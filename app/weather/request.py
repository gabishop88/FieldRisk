"""
Weather API requests for FieldRisk.

Two sources, all free and keyless:
  1. NASA POWER   — historical daily weather (2016–present, ~2 day lag)
  2. Open-Meteo    — 16-day daily forecast

All return a DataFrame with columns:
  date, year, day, radn, maxt, mint, rain, rh, windspeed
"""

import numpy as np
import pandas as pd
import requests
from datetime import datetime
from pathlib import Path

INPUT_CSV = Path(__file__).resolve().parents[2] / "simulations" / "input" / "input.csv"
NASAPOWER_DIR = Path(__file__).resolve().parents[1] / "data" / "nasapower"
OPENMETEO_DIR = Path(__file__).resolve().parents[1] / "data" / "openmeteo"

DATA_COLS = ["radn", "maxt", "mint", "rain", "rh", "windspeed"]


# ── Helpers ──────────────────────────────────────────────────────────────────

def load_sites() -> pd.DataFrame:
    """Load site list from simulations/input/input.csv."""
    return pd.read_csv(INPUT_CSV)


def _add_time_cols(df: pd.DataFrame) -> pd.DataFrame:
    """Ensure year and day-of-year columns exist."""
    df["year"] = df["date"].dt.year
    df["day"] = df["date"].dt.dayofyear
    return df


# ── 1. NASA POWER (historical) ──────────────────────────────────────────────

def fetch_nasapower(lat: float, lon: float,
                    start: str = "20160101",
                    end: str | None = None) -> pd.DataFrame:
    """
    Fetch daily weather from NASA POWER API.

    Parameters
    ----------
    lat, lon : float
    start, end : str  YYYYMMDD format. end defaults to today.

    Returns
    -------
    DataFrame with columns: date, radn, maxt, mint, rain, rh, windspeed, year, day
    """
    if end is None:
        end = datetime.today().strftime("%Y%m%d")

    url = "https://power.larc.nasa.gov/api/temporal/daily/point"
    params = {
        "parameters": "ALLSKY_SFC_SW_DWN,T2M_MAX,T2M_MIN,PRECTOTCORR,RH2M,WS2M",
        "community": "AG",
        "longitude": lon,
        "latitude": lat,
        "start": start,
        "end": end,
        "format": "JSON",
    }
    resp = requests.get(url, params=params, timeout=120)
    resp.raise_for_status()
    records = resp.json()["properties"]["parameter"]

    df = pd.DataFrame({
        "date": pd.to_datetime(list(records["T2M_MAX"].keys()), format="%Y%m%d"),
        "radn": list(records["ALLSKY_SFC_SW_DWN"].values()),
        "maxt": list(records["T2M_MAX"].values()),
        "mint": list(records["T2M_MIN"].values()),
        "rain": list(records["PRECTOTCORR"].values()),
        "rh": list(records["RH2M"].values()),
        "windspeed": list(records["WS2M"].values()),
    })

    df.replace(-999.0, np.nan, inplace=True)
    df.interpolate(method="linear", inplace=True)
    df.bfill(inplace=True)
    df.ffill(inplace=True)
    df = _add_time_cols(df)

    # Save to data/nasapower/
    NASAPOWER_DIR.mkdir(parents=True, exist_ok=True)
    df.to_csv(NASAPOWER_DIR / f"{lat}_{lon}.csv", index=False)
    return df


# ── 2. Open-Meteo forecast (16-day) ─────────────────────────────────────────

def fetch_forecast(lat: float, lon: float,
                   forecast_days: int = 16) -> pd.DataFrame:
    """
    Fetch daily forecast from Open-Meteo API (GFS + ECMWF blend).

    Parameters
    ----------
    lat, lon : float
    forecast_days : int  (max 16)

    Returns
    -------
    DataFrame with columns: date, radn, maxt, mint, rain, rh, windspeed, year, day
    """
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lon,
        "daily": ",".join([
            "temperature_2m_max", "temperature_2m_min",
            "precipitation_sum", "shortwave_radiation_sum",
            "relative_humidity_2m_mean", "windspeed_10m_max",
        ]),
        "forecast_days": forecast_days,
        "timezone": "auto",
    }
    resp = requests.get(url, params=params, timeout=60)
    resp.raise_for_status()
    data = resp.json()["daily"]

    df = pd.DataFrame({
        "date": pd.to_datetime(data["time"]),
        "radn": np.array(data["shortwave_radiation_sum"], dtype=float),
        "maxt": data["temperature_2m_max"],
        "mint": data["temperature_2m_min"],
        "rain": data["precipitation_sum"],
        "rh": data["relative_humidity_2m_mean"],
        "windspeed": np.array(data["windspeed_10m_max"], dtype=float) / 3.6,
    })

    df.replace([None], np.nan, inplace=True)
    df.ffill(inplace=True)
    df.bfill(inplace=True)
    df = _add_time_cols(df)

    # Save to data/openmeteo/
    OPENMETEO_DIR.mkdir(parents=True, exist_ok=True)
    df.to_csv(OPENMETEO_DIR / f"{lat}_{lon}.csv", index=False)
    return df


# ── .met file writer ────────────────────────────────────────────────────────

def write_met(df: pd.DataFrame, lat: float, lon: float,
              site: str, filepath: str, source: str = "FieldRisk") -> None:
    """Write a DataFrame to APSIM .met format."""
    tavg = (df["maxt"] + df["mint"]) / 2.0
    monthly = df.copy()
    monthly["month"] = df["date"].dt.month
    monthly["tavg"] = tavg
    mo_means = monthly.groupby("month")["tavg"].mean()
    tav = round(mo_means.mean(), 4)
    amp = round(mo_means.max() - mo_means.min(), 4)

    with open(filepath, "w") as f:
        f.write(f"!data from {source}. retrieved: {datetime.now()}\n")
        f.write("[weather.met.weather]\n")
        f.write(f"site = {site}\n")
        f.write(f"latitude = {lat}\n")
        f.write(f"longitude = {lon}\n")
        f.write(f"tav = {tav}\n")
        f.write(f"amp = {amp}\n")
        f.write("year day radn maxt mint rain rh windspeed\n")
        f.write("() () (MJ/m2/day) (oC) (oC) (mm) (%) (m/s)\n")
        for _, row in df.iterrows():
            f.write(
                f"{int(row['year'])} {int(row['day'])} "
                f"{row['radn']:.2f} {row['maxt']:.2f} {row['mint']:.2f} "
                f"{row['rain']:.2f} {row['rh']:.2f} {row['windspeed']:.2f}\n"
            )


# ── Convenience: fetch all sources for all sites ────────────────────────────

def fetch_all_for_site(site: str, lat: float, lon: float,
                       output_dir: str) -> dict[str, pd.DataFrame]:
    """
    Fetch NASA POWER + forecast for one site. Save .met files.

    Returns dict with keys 'nasapower', 'forecast'.
    """
    results = {}
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    # NASA POWER
    df_nasa = fetch_nasapower(lat, lon)
    write_met(df_nasa, lat, lon, site,
              str(Path(output_dir) / f"{site}_nasapower.met"), "NASA POWER API")
    results["nasapower"] = df_nasa

    # Forecast
    df_fc = fetch_forecast(lat, lon)
    write_met(df_fc, lat, lon, site,
              str(Path(output_dir) / f"{site}_forecast.met"), "Open-Meteo Forecast")
    results["forecast"] = df_fc

    return results
