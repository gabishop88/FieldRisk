from pathlib import Path
import subprocess
import numpy as np
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import folium
from streamlit_folium import st_folium

from weather.request import fetch_weather_data
from weather.predict import generate_met_files


BASE = Path("/app")
INPUT_PATH = BASE / "simulations/input/input.csv"
OUTPUT_PATH = BASE / "simulations/output_files/results/daily_sim_outputs.csv"

LINE_VARS = {
    "Max Temp (°C)": "MaxT",
    "Min Temp (°C)": "MinT",
    "Solar Radiation": "Radn",
    "Accumulated Thermal Time": "AccEmTT",
    "Rainfall (mm)": "Rain",
    "Accumulated Rainfall (mm)": "AccRain",
    "Plant Avaiable Water (mm)": "PAWmm",
}
STRESS_VARS = {
    "Water Stress": "WaterStress",
    "Temp Stress": "TempStress",
    # "Nutrient Stress": "NutrientStress",
}
STRESS_COLORS = ["Reds", "Blues", "Greens"]

EMPTY_SITE = {
    "Site": "",
    "Crop": "Maize",
    "Planting": "",
    "Genetics": "",
    "Latitude": 0.0,
    "Longitude": 0.0,
}


# ── Data helpers ──────────────────────────────────────────────────────────────
@st.cache_data
def load_input():
    return (
        pd.read_csv(INPUT_PATH) if INPUT_PATH.exists() else pd.DataFrame([EMPTY_SITE])
    )


@st.cache_data
def load_output():
    return pd.read_csv(OUTPUT_PATH) if OUTPUT_PATH.exists() else None


def save_input(df):
    df.to_csv(INPUT_PATH, index=False)
    st.cache_data.clear()


def run_simulation():
    with st.status("Running Simulation"):
        st.session_state.simulating = True
        st.write("Copying input data")
        save_input(pd.DataFrame(st.session_state.sites))
        st.write("Requesting weather data")
        fetch_weather_data(BASE / "data")
        st.write("Predicting future weather data")
        generate_met_files(INPUT_PATH)
        st.write("Simulating crop growth")
        result = subprocess.run(
            ["Rscript", str(BASE / "simulations/simulation_script.R")],
            capture_output=True,
        )
        if result.returncode:
            st.write("Simulation Failed - Failed to connect to APSIM.")
        st.session_state.simulating = False
        st.cache_data.clear()
        st.write("Cleared cache, Simulation Complete.")


# ── Session state init ────────────────────────────────────────────────────────
input_df = load_input()
if "sites" not in st.session_state:
    st.session_state.sites = input_df.to_dict("records")
if "selected_idx" not in st.session_state:
    st.session_state.selected_idx = 0
if "simulating" not in st.session_state:
    st.session_state.simulating = False


# ── Page ──────────────────────────────────────────────────────────────────────
st.set_page_config(page_title="Field Risk Dashboard", layout="wide")
st.title("Field Risk Dashboard")
st.caption("CDA 2026 Hackathon — Track 4: Decision Support")


# ── Sidebar ───────────────────────────────────────────────────────────────────
st.sidebar.header("Selected Site")

sites = st.session_state.sites
site_names = [s["Site"] or f"Unnamed Site {i + 1}" for i, s in enumerate(sites)]

# Site selector row with +/- buttons
col_sel, col_add, col_del = st.sidebar.columns([5, 1, 1])
with col_sel:
    idx = st.selectbox(
        "Site",
        range(len(site_names)),
        format_func=lambda i: site_names[i],
        index=st.session_state.selected_idx,
        label_visibility="collapsed",
    )
    st.session_state.selected_idx = idx
with col_add:
    if st.button("+"):
        st.session_state.sites.append(EMPTY_SITE.copy())  # type: ignore
        st.session_state.selected_idx = len(st.session_state.sites) - 1
        st.rerun()
with col_del:
    if st.button("-") and len(sites) > 1:
        st.session_state.sites.pop(idx)
        st.session_state.selected_idx = max(0, idx - 1)
        st.rerun()

st.sidebar.divider()

# Edit current site
planting_help = "If a planting date is not available, input the current year and a date will be recommended based on weather predictions."

s = st.session_state.sites[idx]
s["Site"] = st.sidebar.text_input("Site Name", value=s["Site"])
s["Crop"] = st.sidebar.selectbox("Crop", ["Maize"])
s["Genetics"] = st.sidebar.text_input("Genetics", value=s["Genetics"])
s["Planting"] = st.sidebar.text_input(
    "Planting Date (YYYY-MM-DD)", value=s["Planting"], help=planting_help
)
lat = float(s["Latitude"]) or 41.5
lon = float(s["Longitude"]) or -93.0

m = folium.Map(location=[lat, lon], zoom_start=8, tiles="CartoDB dark_matter")

# Other sites in gray
for i, other in enumerate(sites):
    if i != idx and float(other["Latitude"]) and float(other["Longitude"]):
        folium.Marker(
            [float(other["Latitude"]), float(other["Longitude"])],
            popup=other["Site"],
            icon=folium.Icon(color="gray"),
        ).add_to(m)

# Current site in red
folium.Marker([lat, lon], popup=s["Site"], icon=folium.Icon(color="red")).add_to(m)

st.sidebar.caption(f"📍 {s['Latitude']}, {s['Longitude']}")

with st.sidebar:
    map_data = st_folium(m, height=250, width=305, key=f"map_{idx}")

if map_data["last_clicked"]:
    s["Latitude"] = round(map_data["last_clicked"]["lat"], 4)
    s["Longitude"] = round(map_data["last_clicked"]["lng"], 4)

st.session_state.sites[idx] = s

# Simulate button — grey out if unchanged or currently running
saved = input_df.to_dict("records")
all_complete = all(all(str(v) for v in site.values()) for site in sites)


def normalize_sites(sites):
    return [{k: str(v).strip() for k, v in s.items()} for s in sites]


is_dirty = normalize_sites(st.session_state.sites) != normalize_sites(
    input_df.to_dict("records")
)


st.sidebar.divider()
simulate_disabled = not is_dirty or not all_complete or st.session_state.simulating
st.sidebar.button(
    "Simulating..." if st.session_state.simulating else "▶ Simulate",
    disabled=simulate_disabled,
    on_click=run_simulation,
    type="primary",
    use_container_width=True,
)
if not all_complete:
    st.sidebar.caption("Fill in all fields to enable simulation.")
elif not is_dirty:
    st.sidebar.caption("No changes from last simulation.")


# ── Main — Chart ──────────────────────────────────────────────────────────────
st.header("Simulation Results - Environment and Risk Timeline")

output_df = load_output()
if output_df is None:
    st.warning("No simulation output found.")
    st.stop()

# Filter to selected site
current_site = st.session_state.sites[idx]["Site"]
df = (
    output_df[output_df["ID"] == idx + 1].copy()
    if "ID" in output_df.columns
    else output_df.copy()
)
if df.empty:
    st.info(
        f"No output data for site '{current_site['Site']}' yet. Run a simulation first."
    )
    st.stop()
today = pd.Timestamp.today().normalize()

selected_lines = st.multiselect(
    "Line Charts", list(LINE_VARS), default=["Max Temp (°C)"]
)
selected_stresses = st.multiselect(
    "Stress Types", list(STRESS_VARS), default=["Temp Stress"]
)


def build_fig(df, selected_lines, selected_stresses, today):
    n_stress = len(selected_stresses)
    n_rows = 1 + n_stress + 1  # main + stress + stage
    row_heights = [0.82] + [0.09 / max(n_stress, 1)] * n_stress + [0.09]

    fig = make_subplots(
        rows=n_rows,
        cols=1,
        shared_xaxes=True,
        row_heights=row_heights,
        vertical_spacing=0.02,
    )

    stage_colors = {
        "Germination": "#2d6a4f",
        "Vegetative": "#52b788",
        "Flowering": "#f4a261",
        "Grain Fill": "#e76f51",
        "Maturity": "#9b2226",
    }
    for stage, grp in df.groupby("StageName"):
        fig.add_vrect(
            x0=grp["Date"].min(),
            x1=grp["Date"].max(),
            fillcolor=stage_colors.get(stage, "#aaaaaa"),
            opacity=0.12,
            line_width=0,
            annotation_text=stage,
            annotation_position="top left",
            annotation_font_size=9,
        )
    for r in range(1, n_rows + 1):
        fig.add_vline(
            x=today.timestamp() * 1000,  # plotly needs ms epoch for dates
            line=dict(color="white", width=1, dash="dash"),
            opacity=0.5,
            row=r, col=1,
        )

    colors = ["#4cc9f0", "#f72585", "#7209b7", "#3a86ff", "#fb8500", "#06d6a0"]
    for i, label in enumerate(selected_lines):
        fig.add_trace(
            go.Scatter(
                x=df["Date"],
                y=df[LINE_VARS[label]],
                name=label,
                line=dict(color=colors[i % len(colors)], width=1.5),
            ),
            row=1,
            col=1,
        )

    for r, (label, cmap) in enumerate(zip(selected_stresses, STRESS_COLORS), start=2):
        vals = np.log1p(df[STRESS_VARS[label]].values)
        fig.add_trace(
            go.Heatmap(
                x=df["Date"],
                z=[vals],
                colorscale=cmap,
                showscale=False,
                name=label,
            ),
            row=r,
            col=1,
        )
        fig.update_yaxes(
            showticklabels=False, title_text=label, title_font_size=9, row=r, col=1
        )

    customdata = [list(zip(df["Stage"].values, df["StageName"].values))]
    colorscale = [
        [0.0,   "#1a1a2e"],   # 1  — NA / pre-season (dark, invisible)
        [0.09,  "#1a1a2e"],   # 1  — NA / pre-season
        [0.09,  "#4a7c3f"],   # 1  — Germinating (deep green)
        [0.18,  "#6aad44"],   # 2  — Emerging
        [0.27,  "#8db84a"],   # 3  — Juvenile
        [0.45,  "#b5c832"],   # 5  — LeafAppearance
        [0.54,  "#d4c020"],   # 6  — FlagLeaf/Flowering
        [0.63,  "#e8a020"],   # 7  — FloweringToGrainFilling
        [0.72,  "#d4782a"],   # 8  — GrainFilling
        [0.90,  "#a04020"],   # 10 — MaturityToHarvestRipe
        [1.0,   "#7a3010"],   # 11 — ReadyForHarvesting
    ]
    # Growth stage strip
    fig.add_trace(
        go.Heatmap(
            x=df["Date"],
            z=[df["Stage"].values],
            colorscale=colorscale,
            zmin=1,
            zmax=11,
            showscale=False,
            name="Growth Stage",
            customdata=customdata,
            hovertemplate="Date: %{x}<br>Stage: %{customdata[0]:.1f}<br>%{customdata[1]}<extra></extra>",
        ),
        row=n_rows,
        col=1,
    )
    fig.update_yaxes(
        showticklabels=False, title_text="Stage", title_font_size=9, row=n_rows, col=1
    )

    # fig.update_xaxes(title_text="Day of Year", row=n_rows, col=1)
    fig.update_xaxes(title_text="Date", tickformat="%b %d", row=n_rows, col=1)
    fig.update_layout(
        height=420 + 40 * n_stress,
        margin=dict(t=20, b=40),
        legend=dict(orientation="h", y=1.05),
    )
    return fig


st.plotly_chart(build_fig(df, selected_lines, selected_stresses, today), use_container_width=True)
