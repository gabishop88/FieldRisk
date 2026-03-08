from pathlib import Path
import subprocess
import time
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from weather.predict import generate_met_files


BASE = Path("/app")
INPUT_PATH = BASE / "simulations/input/input.csv"
OUTPUT_PATH = BASE / "simulations/output_files/results/daily_sim_outputs.csv"

LINE_VARS = {
    "Max Temp (°C)": "MaxT",
    "Min Temp (°C)": "MinT",
    "Rainfall (mm)": "Rain",
    "Solar Radiation": "Radn",
    "PAW (mm)": "PAWmm",
}
STRESS_VARS = {
    "Water Stress": "WaterStress",
    "Temp Stress": "TempStress",
    "Nutrient Stress": "NutrientStress",
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
        # TODO: Emine's function
        st.write("Predicting future weather data")
        generate_met_files(INPUT_PATH)

        st.write("Simulating crop growth")
        time.sleep(5)
        # result = subprocess.run(["Rscript", str(BASE / "simulations/simulation_script.R")], capture_output=True)
        st.write("Validating output...")
        st.session_state.simulating = False
        st.cache_data.clear()
        st.write("Completed!")


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
s = st.session_state.sites[idx]
s["Site"] = st.sidebar.text_input("Site Name", value=s["Site"])
s["Crop"] = st.sidebar.selectbox("Crop", ["Maize"])
s["Genetics"] = st.sidebar.text_input("Genetics", value=s["Genetics"])
s["Planting"] = st.sidebar.text_input("Planting Date (YYYY-MM-DD)", value=s["Planting"])
s["Latitude"] = st.sidebar.number_input(
    "Latitude", value=float(s["Latitude"]), format="%.4f"
)
s["Longitude"] = st.sidebar.number_input(
    "Longitude", value=float(s["Longitude"]), format="%.4f"
)
st.session_state.sites[idx] = s

# Simulate button — grey out if unchanged or currently running
saved = input_df.to_dict("records")
all_complete = all(all(str(v) for v in site.values()) for site in sites)
def normalize_sites(sites):
    return [{k: str(v).strip() for k, v in s.items()} for s in sites]

is_dirty = normalize_sites(st.session_state.sites) != normalize_sites(input_df.to_dict("records"))


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
st.header("📊 Seasonal Risk Timeline")

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
    st.info(f"No output data for site '{current_site["Site"]}' yet. Run a simulation first.")
    st.stop()

selected_lines = st.multiselect(
    "Line Charts", list(LINE_VARS), default=["Max Temp (°C)"]
)
selected_stresses = st.multiselect(
    "Stress Types", list(STRESS_VARS), default=["Temp Stress"]
)


def build_fig(df, selected_lines, selected_stresses):
    n_stress = len(selected_stresses)
    row_heights = [0.7] + [0.3 / max(n_stress, 1)] * n_stress if n_stress else [1.0]
    fig = make_subplots(
        rows=1 + max(n_stress, 0),
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
            x0=grp["DOY"].min(),
            x1=grp["DOY"].max(),
            fillcolor=stage_colors.get(stage, "#aaaaaa"),
            opacity=0.12,
            line_width=0,
            annotation_text=stage,
            annotation_position="top left",
            annotation_font_size=9,
        )

    colors = ["#4cc9f0", "#f72585", "#7209b7", "#3a86ff", "#fb8500", "#06d6a0"]
    for i, label in enumerate(selected_lines):
        fig.add_trace(
            go.Scatter(
                x=df["DOY"],
                y=df[LINE_VARS[label]],
                name=label,
                line=dict(color=colors[i % len(colors)], width=1.5),
            ),
            row=1,
            col=1,
        )

    for r, (label, cmap) in enumerate(zip(selected_stresses, STRESS_COLORS), start=2):
        fig.add_trace(
            go.Heatmap(
                x=df["DOY"],
                z=[df[STRESS_VARS[label]].values],
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

    fig.update_xaxes(title_text="Day of Year", row=1 + max(n_stress, 0), col=1)
    fig.update_layout(
        height=420 + 80 * n_stress,
        margin=dict(t=20, b=40),
        legend=dict(orientation="h", y=1.05),
    )
    return fig


st.plotly_chart(
    build_fig(df, selected_lines, selected_stresses), use_container_width=True
)
