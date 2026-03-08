import calendar
from pathlib import Path
import numpy as np
from pandas import DataFrame, concat, to_numeric, read_csv
from datetime import datetime


DATA_COLS = ["radn", "maxt", "mint", "rain", "rh", "windspeed"]

# region ---------- Helper Functions ----------


def import_met(input_file: Path) -> DataFrame:
    assert input_file.suffix == ".met", "Can only load .met files"
    with input_file.open("r") as f:
        lines = f.readlines()
        lines = [ln.strip() for ln in lines if ln != ""]

    col_names, data_rows = lines[7].split(), [row.split() for row in lines[9:]]
    df = DataFrame(data_rows, columns=col_names)

    numeric_cols = DATA_COLS + ["year", "day"]
    df[numeric_cols] = df[numeric_cols].apply(to_numeric, errors="coerce")
    return df


def compute_tav_amp(df: DataFrame) -> tuple[float, float]:
    df = df.copy()
    df["tmean"] = (df["maxt"] + df["mint"]) / 2
    tav = df["tmean"].mean()

    mo_means = []
    for m in range(1, 13):
        days_in_months = [calendar.monthrange(2000, mo)[1] for mo in range(1, m + 1)]
        doy_start = sum(days_in_months[:-1]) + 1
        doy_end = sum(days_in_months)
        mo_df = df[(df["day"] >= doy_start) & (df["day"] <= doy_end)]
        if not mo_df.empty:
            mo_means.append(mo_df["tmean"].mean())

    amp = max(mo_means) - min(mo_means) if mo_means else np.nan
    return round(tav, 4), round(amp, 4)


def export_met(df_pred: DataFrame, ref_met: Path, output_file: Path) -> None:
    with ref_met.open("r") as f:
        source_lines = f.readlines()

    important_meta = ("site", "latitude", "longitude")
    keep_lines = [ln.strip() for ln in source_lines if ln.startswith(important_meta)]
    tav, amp = compute_tav_amp(df_pred)

    meta = (
        f"!data from AgData Ninjas Prediction. retrieved: {datetime.today()}\n"
        "[weather.met.weather]\n"
        f"{'\n'.join(keep_lines)}\n"
        f"tav = {tav}\n"
        f"amp = {amp}\n"
        "year day radn maxt mint rain rh windspeed\n"
        "() () (MJ/m2/day) (oC) (oC) (mm) (%) (m/s)\n"
    )

    with output_file.open("w") as f:
        f.write(meta)
        for _, row in df_pred.iterrows():
            vals = [f"{int(row[c])}" for c in ("year", "day")] + [
                f"{round(row[c], 2)}" for c in DATA_COLS
            ]
            f.write(" ".join(vals) + "\n")


# endregion
# region ---------- Business Functions ----------


def predict_met_weighted_sum(df_hist, df_fcast, spikiness=1.0) -> DataFrame:
    curr_year = df_hist["year"].max()
    df_fcast = df_fcast[df_fcast["year"] == curr_year]

    # All data from current year (hist + pred)
    df_current = (
        concat([df_hist[df_hist["year"] == curr_year], df_fcast])
        .drop_duplicates("day")
        .sort_values("day")
        .reset_index(drop=True)
    )
    # Historical Only (before this year)
    df_hist = df_hist[df_hist["year"] < curr_year]

    known_days = df_current["day"].values
    col_stats = {c: (df_hist[c].mean(), df_hist[c].std()) for c in DATA_COLS}

    def normalize(col):
        mu, sig = col_stats[col.name]
        return (col.fillna(mu) - mu) / sig

    def get_normalized_data(df) -> np.ndarray:
        return (
            df.set_index("day")
            .reindex(known_days)[DATA_COLS]
            .apply(normalize)
            .values.flatten()
        )

    # Compute similarities between df_current and each year in df_hist
    curr_vec = get_normalized_data(df_current)
    year_range = range(df_hist["year"].min(), df_hist["year"].max() + 1)
    similarities: dict[int, float] = {}
    for year in year_range:
        df_window = df_hist[df_hist["year"] == year]
        window_vec = get_normalized_data(df_window)

        denom = np.linalg.norm(curr_vec) * np.linalg.norm(window_vec)
        if denom > 0:
            cos_similarity = float(np.dot(curr_vec, window_vec) / denom)
            similarities[year] = cos_similarity**spikiness

    weights = {year: max(similarities.get(year, 0), 0.0) for year in year_range}
    total = sum(weights.values())
    if total > 0:
        weights = {year: w / total for year, w in weights.items()}
    else:
        # Fallback: equal weights when all similarities are zero/negative
        n = len(weights)
        weights = {year: 1.0 / n for year in weights}

    # Compute weighted sum of previous years
    days_this_year = 365 + int(calendar.isleap(curr_year))
    result = DataFrame({"day": range(1, days_this_year + 1)})
    result.insert(0, "year", curr_year)
    for c in DATA_COLS:
        result[c] = 0.0

    for year, w in weights.items():
        df_year = df_hist[df_hist["year"] == year].set_index("day")
        for c in DATA_COLS:
            matched = df_year[c].reindex(result["day"]).fillna(col_stats[c][0]).values
            result[c] += w * matched  # type: ignore

    # Overwrite predicted values for the days we have current data
    for c in DATA_COLS:
        mask = result["day"].isin(known_days)
        known_vals = df_current.set_index("day")[c]
        result.loc[mask, c] = known_vals.reindex(result.loc[mask, "day"]).values

    return result


def generate_met_files(input_path: Path) -> None:
    sites = read_csv(input_path)["Site"].astype(str).tolist()

    hist_dir = Path("/app/data/nasapower")
    pred_dir = Path("/app/data/openmeteo")
    out_dir = Path("/app/simulations/output_files/met")
    for site in sites:
        if not (hist_dir / f"{site}_nasapower.met").exists():
            raise FileNotFoundError(f"{site} Missing Weather History.")
        if not (pred_dir / f"{site}_forecast.met").exists():
            raise FileNotFoundError(f"{site} Missing Weather Forecast.")

    # load files, run prediction, output mets.
    for i, site in enumerate(sites):
        df_hist = import_met(hist_dir / f"{site}_nasapower.met")
        df_fore = import_met(pred_dir / f"{site}_forecast.met")

        df_pred = predict_met_weighted_sum(df_hist, df_fore, spikiness=10.0)
        export_met(
            df_pred, hist_dir / f"{site}_nasapower.met", out_dir / f"loc_{i + 1}.met"
        )
