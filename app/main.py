import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os
import numpy as np

BASE = os.path.dirname(os.path.abspath(__file__))

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(page_title="FieldRisk", layout="wide")
st.title("🌾 FieldRisk")
st.caption("CDA 2026 — Track 4: Decision Support")

# ── Load data ────────────────────────────────────────────────────────────────
@st.cache_data
def load_data():
    ts = pd.read_csv(os.path.join(BASE, "weather_data/season_ndvi_timeseries.csv"), parse_dates=["date"])
    stress = pd.read_csv(os.path.join(BASE, "weather_data/season_ndvi_stress_events.csv"), parse_dates=["date"])
    pheno = pd.read_csv(os.path.join(BASE, "weather_data/season_ndvi_phenology.csv"))
    forecast = pd.read_csv(os.path.join(BASE, "weather_data/forecast_all.csv"), parse_dates=["date"])
    fields = pd.read_csv(os.path.join(BASE, "g2f_2022_iowa_fields.csv"))
    return ts, stress, pheno, forecast, fields

@st.cache_data
def load_sce_data():
    sce_dir = os.path.join(BASE, "Example SCE outputs")
    trial_info = pd.read_csv(os.path.join(sce_dir, "trial_info.csv"))
    season_info = pd.read_csv(os.path.join(sce_dir, "season_info.csv"))
    daily_outputs = pd.read_csv(os.path.join(sce_dir, "daily_outputs.csv"))
    # Filter to Iowa site
    site_id = "a0I8Y00001AQNyZUAX"
    site_trials = trial_info[trial_info["Site"] == site_id]
    trial_ids = site_trials["id_trial"].unique()
    site_season = season_info[season_info["id_trial"].isin(trial_ids)]
    site_daily = daily_outputs[daily_outputs["id_trial"].isin(trial_ids)]
    return site_trials, site_season, site_daily

ts, stress, pheno, forecast, fields = load_data()
sce_trials, sce_season, sce_daily = load_sce_data()

# ── Sidebar ──────────────────────────────────────────────────────────────────
st.sidebar.header("Field & Year Selection")
sites = sorted(ts["site"].unique()) + ["IAH5"]
selected_site = st.sidebar.selectbox("Field", sites)

is_sce = selected_site == "IAH5"

if is_sce:
    selected_year = 2023
    st.sidebar.markdown("**Year:** 2023")
    st.sidebar.markdown("---")
    st.sidebar.subheader("Field Info")
    st.sidebar.markdown("**Crop:** Soybean (Simulated)")
    st.sidebar.markdown("**Location:** 41.7300, -93.4700")
    st.sidebar.markdown("**Trials:** 26 maturity groups")
    st.sidebar.markdown("**Source:** SCE Model Output")
else:
    years = sorted(ts[ts["site"] == selected_site]["year"].unique())
    selected_year = st.sidebar.selectbox("Year", years, index=len(years) - 1)
    # Field info card
    field_row = fields[fields["Field_Location"] == selected_site]
    if not field_row.empty:
        r = field_row.iloc[0]
        st.sidebar.markdown("---")
        st.sidebar.subheader("Field Info")
        st.sidebar.markdown(f"**Crop:** {r['Crop']}")
        st.sidebar.markdown(f"**Location:** {r['Latitude']:.4f}, {r['Longitude']:.4f}")
        st.sidebar.markdown(f"**Planting Date:** {r['Planting_Date']}")
        st.sidebar.markdown(f"**Maturity (days):** {r['Maturity_Anthesis_days']}")

if is_sce:
    st.info("NDVI/weather sections are not available for the simulated site. See Crop Simulation Results below.")

# ── Feature 1: Decision Recommendations ─────────────────────────────────────
st.header("📋 Decision Recommendations")

if is_sce:
    # SCE-based recommendations: best maturity group advice
    harv_trials = sce_trials[sce_trials["Result"].str.contains("Harvested", case=False, na=False)]
    fail_trials = sce_trials[~sce_trials["Result"].str.contains("Harvested", case=False, na=False)]
    if not harv_trials.empty:
        best = harv_trials.loc[harv_trials["Yield_Sim"].idxmax()]
        st.success(f"**Recommended maturity group: {best['Mat']}** — highest simulated yield at {best['Yield_Sim']:.0f} kg/ha.")
    if not fail_trials.empty:
        fail_mats = ", ".join(fail_trials.drop_duplicates("Mat")["Mat"].tolist())
        st.error(f"**Avoid these maturity groups:** {fail_mats} — failed to reach harvest maturity.")
    if harv_trials.empty and fail_trials.empty:
        st.info("No trial data available for recommendations.")
else:
    # NDVI-based recommendations: MACD + forecast synthesis
    ts_rec = ts[(ts["site"] == selected_site) & (ts["year"] == selected_year)].sort_values("date")
    fc_rec = forecast[forecast["site"] == selected_site].sort_values("date").head(16)

    # Assess MACD status
    macd_status = "stable"
    if not ts_rec.empty:
        last_hist = ts_rec["histogram"].iloc[-1] if len(ts_rec) > 0 else 0
        recent_stress = ts_rec.tail(10)["is_macd_stress"].sum()
        if last_hist < -0.01 or recent_stress >= 3:
            macd_status = "declining"
        elif last_hist > 0.01:
            macd_status = "improving"

    # Assess forecast risks
    heat_risk = not fc_rec.empty and (fc_rec["maxt"] > 35).any()
    cold_risk = not fc_rec.empty and (fc_rec["mint"] < 0).any()
    rain_risk = not fc_rec.empty and fc_rec["rain"].mean() < 1

    # Generate recommendation
    if macd_status == "declining" and heat_risk:
        days_to_heat = int((fc_rec[fc_rec["maxt"] > 35]["date"].iloc[0] - fc_rec["date"].iloc[0]).days) + 1 if (fc_rec["maxt"] > 35).any() else 0
        st.error(f"**Urgent: Heat stress incoming in {days_to_heat} days while vegetation is declining.** Consider irrigation and shade management.")
    elif macd_status == "declining" and rain_risk:
        st.warning("**Monitor closely:** Vegetation declining and low rainfall forecast. Consider supplemental irrigation within 5 days.")
    elif macd_status == "declining":
        st.warning("**Vegetation declining** (MACD negative). Monitor for continued stress and plan intervention.")
    elif cold_risk:
        days_to_cold = int((fc_rec[fc_rec["mint"] < 0]["date"].iloc[0] - fc_rec["date"].iloc[0]).days) + 1
        st.warning(f"**Frost risk in {days_to_cold} days.** Consider protective measures for sensitive growth stages.")
    elif heat_risk:
        days_to_heat = int((fc_rec[fc_rec["maxt"] > 35]["date"].iloc[0] - fc_rec["date"].iloc[0]).days) + 1
        st.warning(f"**Heat stress expected in {days_to_heat} days.** Plan irrigation to mitigate impact.")
    elif macd_status == "improving":
        st.success("**No action needed.** Vegetation is recovering and no extreme weather forecast.")
    else:
        st.success("**No action needed.** Conditions are stable with no forecast risks.")

# ── Sections 1-4: NDVI / Weather (hidden for SCE site) ──────────────────────
if not is_sce:
    # Pre-compute NDVI selection for use across sections
    ts_sel = ts[(ts["site"] == selected_site) & (ts["year"] == selected_year)].sort_values("date")

    # ── Section 1: Forecast ─────────────────────────────────────────────────
    st.header("📡 16-Day Weather Forecast")

    fc = forecast[forecast["site"] == selected_site].sort_values("date").head(16)

    if fc.empty:
        st.info("No forecast data available for this field.")
    else:
        risks = []
        if fc["maxt"].max() > 35:
            risks.append("🔴 **High heat risk** — max temperature exceeds 35 °C")
        if fc["rain"].max() > 25:
            risks.append("🔵 **Heavy rain warning** — single-day rainfall > 25 mm")
        if fc["mint"].min() < 0:
            risks.append("🥶 **Frost risk** — min temperature below 0 °C")
        if risks:
            for r in risks:
                st.warning(r)
        else:
            st.success("No extreme weather risks in the forecast period.")

        st.subheader("Next 7 Days")
        cols = st.columns(min(7, len(fc)))
        for i, (_, row) in enumerate(fc.head(7).iterrows()):
            with cols[i]:
                dt = row["date"]
                label = dt.strftime("%a %b %d") if hasattr(dt, "strftime") else str(dt)
                st.markdown(f"**{label}**")
                st.metric("Max °C", f"{row['maxt']:.1f}")
                st.metric("Min °C", f"{row['mint']:.1f}")
                rain_val = row["rain"]
                rain_color = "🔵" if rain_val > 10 else ""
                st.metric("Rain mm", f"{rain_val:.1f} {rain_color}")

        with st.expander("Full 16-day forecast chart"):
            fig_fc = make_subplots(specs=[[{"secondary_y": True}]])
            fig_fc.add_trace(go.Scatter(x=fc["date"], y=fc["maxt"], name="Max Temp", line=dict(color="red")), secondary_y=False)
            fig_fc.add_trace(go.Scatter(x=fc["date"], y=fc["mint"], name="Min Temp", line=dict(color="blue")), secondary_y=False)
            fig_fc.add_trace(go.Bar(x=fc["date"], y=fc["rain"], name="Rain (mm)", marker_color="rgba(0,120,255,0.4)"), secondary_y=True)
            fig_fc.update_yaxes(title_text="Temperature (°C)", secondary_y=False)
            fig_fc.update_yaxes(title_text="Rainfall (mm)", secondary_y=True)
            fig_fc.update_layout(height=350, margin=dict(t=30, b=30))
            st.plotly_chart(fig_fc, use_container_width=True)

        # --- Feature 2: Forecast Stress Predictor ---
        st.subheader("🔮 Forecast Stress Predictor")

        # Flag stress days
        stress_days = []
        for idx, row in fc.iterrows():
            day_num = (row["date"] - fc["date"].iloc[0]).days + 1
            if row["maxt"] > 35:
                stress_days.append(f"Day {day_num} ({row['date'].strftime('%b %d')}): heat stress likely (max {row['maxt']:.1f}°C)")
            if row["mint"] < 0:
                stress_days.append(f"Day {day_num} ({row['date'].strftime('%b %d')}): frost stress likely (min {row['mint']:.1f}°C)")

        if stress_days:
            for s in stress_days:
                st.warning(s)
        else:
            st.success("No temperature stress days in forecast window.")

        # MACD histogram projection
        if not ts_sel.empty and "histogram" in ts_sel.columns:
            hist_vals = ts_sel["histogram"].dropna().values
            if len(hist_vals) >= 5:
                # Linear trend from last 10 observations
                n_pts = min(10, len(hist_vals))
                recent_hist = hist_vals[-n_pts:]
                x_obs = np.arange(n_pts)
                slope, intercept = np.polyfit(x_obs, recent_hist, 1)

                # Project 16 steps forward
                x_proj = np.arange(n_pts, n_pts + 16)
                projected = slope * x_proj + intercept

                fig_proj = go.Figure()
                fig_proj.add_trace(go.Bar(
                    x=list(range(n_pts)), y=recent_hist.tolist(),
                    name="Observed Histogram",
                    marker_color=["red" if v < 0 else "green" for v in recent_hist],
                ))
                fig_proj.add_trace(go.Scatter(
                    x=list(range(n_pts, n_pts + 16)), y=projected.tolist(),
                    mode="lines+markers", name="Projected (16 days)",
                    line=dict(color="red", dash="dash", width=2),
                    marker=dict(size=5),
                ))
                fig_proj.add_hline(y=0, line_dash="solid", line_color="black", line_width=1)
                fig_proj.update_layout(
                    xaxis_title="Observation Index (recent → projected)",
                    yaxis_title="MACD Histogram",
                    height=320, margin=dict(t=30, b=30),
                    legend=dict(orientation="h", y=-0.25),
                )
                st.plotly_chart(fig_proj, use_container_width=True)

                if projected[-1] < 0 and slope < 0:
                    st.warning("MACD histogram trending negative — vegetation stress may intensify.")
                elif projected[-1] > 0 and slope > 0:
                    st.success("MACD histogram trending positive — recovery expected.")

    # ── Section 2: NDVI & MACD ──────────────────────────────────────────────
    st.header("📈 NDVI & MACD Analysis")

    if ts_sel.empty:
        st.info("No NDVI data for this field/year combination.")
    else:
        col_left, col_right = st.columns(2)

        with col_left:
            st.subheader("NDVI Time Series")
            fig_ndvi = go.Figure()
            fig_ndvi.add_trace(go.Scatter(x=ts_sel["date"], y=ts_sel["ndvi"], mode="markers+lines", name="NDVI", marker=dict(size=5), line=dict(color="green", width=1)))
            fig_ndvi.add_trace(go.Scatter(x=ts_sel["date"], y=ts_sel["ema_fast"], name="EMA Fast", line=dict(color="orange", dash="dash")))
            fig_ndvi.add_trace(go.Scatter(x=ts_sel["date"], y=ts_sel["ema_slow"], name="EMA Slow", line=dict(color="purple", dash="dash")))
            fig_ndvi.add_trace(go.Scatter(x=ts_sel["date"], y=ts_sel["ndvi_fitted"], name="Fitted Curve", line=dict(color="gray", dash="dot")))
            fig_ndvi.update_layout(yaxis_title="NDVI", height=400, margin=dict(t=30, b=30), legend=dict(orientation="h", y=-0.2))
            st.plotly_chart(fig_ndvi, use_container_width=True)

        with col_right:
            st.subheader("MACD Indicator")
            fig_macd = go.Figure()
            fig_macd.add_trace(go.Scatter(x=ts_sel["date"], y=ts_sel["macd"], name="MACD", line=dict(color="blue")))
            fig_macd.add_trace(go.Scatter(x=ts_sel["date"], y=ts_sel["signal_line"], name="Signal", line=dict(color="orange")))
            colors = ["red" if v < 0 else "green" for v in ts_sel["histogram"]]
            fig_macd.add_trace(go.Bar(x=ts_sel["date"], y=ts_sel["histogram"], name="Histogram", marker_color=colors))
            stress_pts = ts_sel[ts_sel["is_macd_stress"] == True]
            if not stress_pts.empty:
                fig_macd.add_trace(go.Scatter(x=stress_pts["date"], y=stress_pts["macd"], mode="markers", name="Stress", marker=dict(color="red", size=10, symbol="x")))
            fig_macd.update_layout(yaxis_title="MACD", height=400, margin=dict(t=30, b=30), legend=dict(orientation="h", y=-0.2))
            st.plotly_chart(fig_macd, use_container_width=True)

    # ── Section 3: Stress Alerts ────────────────────────────────────────────
    st.header("⚠️ Stress Alerts")

    stress_sel = stress[(stress["site"] == selected_site) & (stress["year"] == selected_year)].copy()

    if stress_sel.empty:
        st.success(f"No stress events detected for {selected_site} in {selected_year}.")
    else:
        def style_stress(row):
            cmap = {
                "macd_crossover": "background-color: #fff3cd",
                "below_phenology": "background-color: #f8d7da",
            }
            color = cmap.get(row["stress_type"], "")
            return [color] * len(row)

        display_cols = ["date", "doy", "ndvi", "macd", "signal_line", "histogram", "residual", "stress_type"]
        available = [c for c in display_cols if c in stress_sel.columns]
        styled = stress_sel[available].style.apply(style_stress, axis=1).format({
            "ndvi": "{:.4f}", "macd": "{:.4f}", "signal_line": "{:.4f}",
            "histogram": "{:.4f}", "residual": "{:.4f}"
        }, subset=[c for c in ["ndvi", "macd", "signal_line", "histogram", "residual"] if c in available])
        st.dataframe(styled, use_container_width=True, hide_index=True)

    # ── Section 4: Phenology Summary ────────────────────────────────────────
    st.header("🌱 Phenology Summary")

    pheno_site = pheno[pheno["site"] == selected_site].sort_values("year")
    pheno_row = pheno_site[pheno_site["year"] == selected_year]

    if pheno_row.empty:
        st.info("No phenology data for this selection.")
    else:
        pr = pheno_row.iloc[0]
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Green-up DOY", int(pr["greenup_doy"]))
        c2.metric("Senescence DOY", int(pr["senescence_doy"]))
        c3.metric("Peak NDVI", f"{pr['ndvi_max']:.3f}")
        c4.metric("Stress Events", int(pr["n_macd_stress"] + pr["n_residual_stress"]))

    if not pheno_site.empty:
        st.subheader("Year-over-Year Comparison")
        yoy_cols = ["year", "n_obs", "ndvi_mean", "ndvi_max", "ndvi_min",
                    "n_macd_stress", "n_residual_stress", "greenup_doy", "senescence_doy"]
        available_yoy = [c for c in yoy_cols if c in pheno_site.columns]
        st.dataframe(
            pheno_site[available_yoy].style.format({
                "ndvi_mean": "{:.3f}", "ndvi_max": "{:.3f}", "ndvi_min": "{:.3f}"
            }, subset=[c for c in ["ndvi_mean", "ndvi_max", "ndvi_min"] if c in available_yoy]),
            use_container_width=True, hide_index=True
        )

    # ── Feature 5: Composite Risk Score ────────────────────────────────────
    st.header("🎯 Composite Risk Score")

    # Component 1: MACD trend (40%) — ratio of negative histogram values in last 30 days
    if not ts_sel.empty:
        recent = ts_sel.tail(30)
        neg_ratio = (recent["histogram"] < 0).sum() / max(len(recent), 1)
        macd_score = neg_ratio * 100
    else:
        macd_score = 50

    # Component 2: Forecast heat/cold (25%)
    fc_risk = forecast[forecast["site"] == selected_site].sort_values("date").head(16)
    if not fc_risk.empty:
        heat_days = (fc_risk["maxt"] > 35).sum()
        cold_days = (fc_risk["mint"] < 0).sum()
        weather_score = min((heat_days + cold_days) / 16 * 100 * 3, 100)
    else:
        weather_score = 0

    # Component 3: Forecast rain deficit (15%)
    if not fc_risk.empty:
        avg_rain = fc_risk["rain"].mean()
        rain_score = max(0, min(100, (1 - avg_rain / 5) * 100)) if avg_rain < 5 else 0
    else:
        rain_score = 0

    # Component 4: Phenology residual stress (20%)
    if not pheno_row.empty:
        pr_risk = pheno_row.iloc[0]
        total_stress = int(pr_risk["n_macd_stress"] + pr_risk["n_residual_stress"])
        pheno_score = min(total_stress * 15, 100)
    else:
        pheno_score = 50

    composite = (macd_score * 0.40 + weather_score * 0.25 +
                 rain_score * 0.15 + pheno_score * 0.20)

    col_gauge, col_breakdown = st.columns([1, 1])

    with col_gauge:
        fig_gauge = go.Figure(go.Indicator(
            mode="gauge+number",
            value=composite,
            title={"text": "Overall Risk"},
            gauge={
                "axis": {"range": [0, 100]},
                "bar": {"color": "darkblue"},
                "steps": [
                    {"range": [0, 30], "color": "#2ecc71"},
                    {"range": [30, 60], "color": "#f1c40f"},
                    {"range": [60, 100], "color": "#e74c3c"},
                ],
                "threshold": {
                    "line": {"color": "black", "width": 3},
                    "thickness": 0.8,
                    "value": composite,
                },
            },
        ))
        fig_gauge.update_layout(height=300, margin=dict(t=60, b=20))
        st.plotly_chart(fig_gauge, use_container_width=True)

    with col_breakdown:
        st.markdown("**Risk Components**")
        components = [
            ("MACD Trend (40%)", macd_score),
            ("Heat/Cold Stress (25%)", weather_score),
            ("Rain Deficit (15%)", rain_score),
            ("Phenology Stress (20%)", pheno_score),
        ]
        for label, val in components:
            color = "#2ecc71" if val < 30 else "#f1c40f" if val < 60 else "#e74c3c"
            st.markdown(f"**{label}:** {val:.0f}/100")
            st.progress(min(val / 100, 1.0))

# ── Section 5: Crop Simulation Results (SCE — IAH5 only) ────────────────────
if is_sce:
    st.header("🧬 Crop Simulation Results (SCE)")

    # --- 5a: Yield by Maturity Group ---
    st.subheader("Yield by Maturity Group")
    yield_df = sce_trials.drop_duplicates(subset=["Mat"])[["Mat", "Yield_Sim", "Result"]].sort_values("Mat")
    color_map = {"Harvested at Maturity.": "#2ecc71", "Dead from Total Senescence.": "#e74c3c"}
    yield_df["color"] = yield_df["Result"].map(color_map).fillna("#95a5a6")
    fig_yield = go.Figure(go.Bar(
        x=yield_df["Mat"], y=yield_df["Yield_Sim"],
        marker_color=yield_df["color"],
        text=yield_df["Result"].str.replace(".", "", regex=False),
        textposition="outside",
    ))
    fig_yield.update_layout(
        xaxis_title="Maturity Group", yaxis_title="Simulated Yield (kg/ha)",
        height=420, margin=dict(t=30, b=30),
    )
    st.plotly_chart(fig_yield, use_container_width=True)

    # --- Feature 3: Observed vs Simulated Overlay ---
    st.subheader("🔬 Observed (IAH4) vs Simulated Growth")

    # IAH4 2022 NDVI as proxy for closest real site
    iah4_ts = ts[(ts["site"] == "IAH4") & (ts["year"] == 2022)].sort_values("doy")
    # Pick first trial for SCE daily growth rate
    first_trial_id = sce_trials.iloc[0]["id_trial"]
    sce_first_daily = sce_daily[sce_daily["id_trial"] == first_trial_id].copy()

    if not iah4_ts.empty and not sce_first_daily.empty:
        # Normalize NDVI to 0-1
        ndvi_min_val, ndvi_max_val = iah4_ts["ndvi"].min(), iah4_ts["ndvi"].max()
        ndvi_range = ndvi_max_val - ndvi_min_val if ndvi_max_val > ndvi_min_val else 1
        iah4_ts = iah4_ts.copy()
        iah4_ts["ndvi_norm"] = (iah4_ts["ndvi"] - ndvi_min_val) / ndvi_range

        fig_overlay = go.Figure()
        fig_overlay.add_trace(go.Scatter(
            x=iah4_ts["doy"], y=iah4_ts["ndvi_norm"],
            mode="lines+markers", name="IAH4 NDVI (normalized)",
            line=dict(color="green", width=2), marker=dict(size=4),
        ))
        fig_overlay.add_trace(go.Scatter(
            x=sce_first_daily["DOY"], y=sce_first_daily["FracGrowthRate"],
            mode="lines", name="SCE FracGrowthRate",
            line=dict(color="orange", width=2, dash="dash"),
        ))
        fig_overlay.update_layout(
            xaxis_title="Day of Year", yaxis_title="Normalized Value (0-1)",
            height=380, margin=dict(t=30, b=30),
            legend=dict(orientation="h", y=-0.2),
        )
        st.plotly_chart(fig_overlay, use_container_width=True)
        st.caption("Compares real satellite observations (IAH4, ~35 km away) with SCE simulation growth rate.")
    else:
        st.info("Insufficient data for observed vs simulated overlay.")

    # --- 5b: Daily Growth Timeline ---
    st.subheader("Daily Growth Timeline")
    mat_options = sorted(sce_trials["Mat"].unique())
    selected_mat = st.selectbox("Select maturity group", mat_options)
    sel_trial_id = sce_trials[sce_trials["Mat"] == selected_mat].iloc[0]["id_trial"]
    trial_daily = sce_daily[sce_daily["id_trial"] == sel_trial_id].copy()
    trial_daily["Date"] = pd.to_datetime(trial_daily["Date"])

    fig_growth = go.Figure()
    # Background stage bands
    stages = trial_daily.groupby("StageName")["Date"].agg(["min", "max"]).reset_index()
    stage_colors = {
        "Germinating": "rgba(139,69,19,0.12)", "Emerging": "rgba(34,139,34,0.12)",
        "Vegetative": "rgba(50,205,50,0.12)", "EarlyFlowering": "rgba(255,215,0,0.15)",
        "EarlyPodDevelopment": "rgba(255,165,0,0.15)",
        "EarlyGrainFilling": "rgba(255,140,0,0.15)",
        "MidGrainFilling": "rgba(210,105,30,0.15)",
        "LateGrainFilling": "rgba(180,90,20,0.15)",
        "Maturing": "rgba(160,82,45,0.15)", "Ripening": "rgba(139,69,19,0.15)",
        "ReadyForHarvesting": "rgba(100,100,100,0.12)",
    }
    for _, s in stages.iterrows():
        fig_growth.add_vrect(
            x0=s["min"], x1=s["max"],
            fillcolor=stage_colors.get(s["StageName"], "rgba(200,200,200,0.1)"),
            layer="below", line_width=0,
            annotation_text=s["StageName"], annotation_position="top left",
            annotation_font_size=9,
        )
    fig_growth.add_trace(go.Scatter(
        x=trial_daily["Date"], y=trial_daily["Yieldkgha"],
        mode="lines", name="Yield (kg/ha)", line=dict(color="#2c3e50", width=2),
    ))
    fig_growth.update_layout(
        yaxis_title="Cumulative Yield (kg/ha)", height=420, margin=dict(t=30, b=30),
    )
    st.plotly_chart(fig_growth, use_container_width=True)

    # --- 5c: Stress Factors Over Time ---
    st.subheader("Stress Factors Over Time")
    fig_stress = make_subplots(specs=[[{"secondary_y": True}]])
    fig_stress.add_trace(go.Scatter(
        x=trial_daily["Date"], y=trial_daily["WaterStress"],
        name="Water Stress", line=dict(color="#3498db", width=2),
    ), secondary_y=False)
    fig_stress.add_trace(go.Scatter(
        x=trial_daily["Date"], y=trial_daily["TempStress"],
        name="Temp Stress", line=dict(color="#e74c3c", width=2),
    ), secondary_y=True)
    fig_stress.update_yaxes(title_text="Water Stress", range=[0, 1.05], secondary_y=False)
    fig_stress.update_yaxes(title_text="Temp Stress", range=[0, 1.05], secondary_y=True)
    fig_stress.update_layout(height=380, margin=dict(t=30, b=30))
    st.plotly_chart(fig_stress, use_container_width=True)

    # --- 5d: Season Summary Table ---
    st.subheader("Season Summary")
    trial_season = sce_season[sce_season["id_trial"] == sel_trial_id].copy()
    display_season_cols = ["Period", "Rain", "MaxT", "MinT", "ThermalTime",
                           "FracGrowthRate", "TempStress", "WaterStress",
                           "Period_Start_Date", "Period_End_Date", "Length"]
    avail = [c for c in display_season_cols if c in trial_season.columns]
    st.dataframe(
        trial_season[avail].style.format({
            "Rain": "{:.1f}", "MaxT": "{:.1f}", "MinT": "{:.1f}",
            "ThermalTime": "{:.1f}", "FracGrowthRate": "{:.3f}",
            "TempStress": "{:.3f}", "WaterStress": "{:.3f}",
        }, subset=[c for c in ["Rain", "MaxT", "MinT", "ThermalTime",
                               "FracGrowthRate", "TempStress", "WaterStress"] if c in avail]),
        use_container_width=True, hide_index=True,
    )

    # --- Feature 4: Maturity Group Advisor ---
    st.subheader("🎯 Maturity Group Advisor")

    adv_df = sce_trials.drop_duplicates(subset=["Mat"])[["Mat", "Yield_Sim", "DTM_Sim", "Result"]].copy()
    adv_df["harvested"] = adv_df["Result"].str.contains("Harvested", case=False, na=False)

    fig_adv = go.Figure()
    harv = adv_df[adv_df["harvested"]]
    fail = adv_df[~adv_df["harvested"]]
    fig_adv.add_trace(go.Scatter(
        x=harv["DTM_Sim"], y=harv["Yield_Sim"], mode="markers+text",
        marker=dict(color="green", size=12, symbol="circle"),
        text=harv["Mat"], textposition="top center", name="Harvested",
    ))
    fig_adv.add_trace(go.Scatter(
        x=fail["DTM_Sim"], y=fail["Yield_Sim"], mode="markers+text",
        marker=dict(color="red", size=12, symbol="x"),
        text=fail["Mat"], textposition="top center", name="Failed",
    ))
    # Optimal zone around best-performing harvested cluster
    if not harv.empty:
        best = harv.nlargest(5, "Yield_Sim")
        fig_adv.add_shape(type="rect",
            x0=best["DTM_Sim"].min() - 3, x1=best["DTM_Sim"].max() + 3,
            y0=best["Yield_Sim"].min() * 0.95, y1=best["Yield_Sim"].max() * 1.05,
            line=dict(color="green", width=2, dash="dash"),
            fillcolor="rgba(46,204,113,0.1)",
        )
        fig_adv.add_annotation(
            x=best["DTM_Sim"].mean(), y=best["Yield_Sim"].max() * 1.06,
            text="Optimal Zone", showarrow=False, font=dict(color="green", size=12),
        )
    fig_adv.update_layout(
        xaxis_title="Days to Maturity", yaxis_title="Simulated Yield (kg/ha)",
        height=420, margin=dict(t=30, b=30),
    )
    st.plotly_chart(fig_adv, use_container_width=True)

    # Recommendation text
    if not harv.empty:
        best_mat = harv.loc[harv["Yield_Sim"].idxmax(), "Mat"]
        best_yield = harv["Yield_Sim"].max()
        avoid_list = ", ".join(fail["Mat"].tolist()) if not fail.empty else "None"
        st.success(f"**Best maturity group:** {best_mat} (yield: {best_yield:.0f} kg/ha)")
        if not fail.empty:
            st.error(f"**Avoid:** {avoid_list} — these failed to reach harvest")

# ── Footer ───────────────────────────────────────────────────────────────────
st.markdown("---")
st.caption("CDA 2026 Hackathon — Crop Stress Decision Support Dashboard | Data: Sentinel-2 NDVI, Open-Meteo Forecast, G2F Metadata, SCE Simulation")
