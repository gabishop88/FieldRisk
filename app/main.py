# project_path = "/content/drive/My Drive/AgDataNinjas/SCE_Files"

# When analysis starts:

# Get Inputs

# Get Weather Data from API

# Make Predictions

# Create MET Files

# Run Simulations

# Get Outputs
from pathlib import Path
import subprocess
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# BASE = Path(__file__).parent
BASE = Path("/app")

# region ---------- Helper Functions ----------


def run_apsim() -> None:
    result = subprocess.run(
        ["Rscript", BASE / "simulations/simulation_script.R"], capture_output=True
    )
    print(result.stdout)
    if result.stderr:
        print(f"APSIM Error: {result.stderr}")


# endregion
# region ---------- Streamlit Dashboard ---------
st.set_page_config(page_title="Field Risk Dashboard", layout="wide")
st.title("Field Risk Dashboard")
st.caption("CDA 2026 Hackathon — Track 4: Decision Support")

# ── Config ────────────────────────────────────────────────────────────────────
LINE_VARS = {
    "Max Temp (°C)": "MaxT", "Min Temp (°C)": "MinT",
    "Rainfall (mm)": "Rain", "Solar Radiation": "Radn", "PAW (mm)": "PAWmm",
}
STRESS_VARS = {
    "Water Stress": "WaterStress", "Temp Stress": "TempStress", "Nutrient Stress": "NutrientStress",
}
STRESS_COLORS = ["Blues", "Reds", "Greens"]

# ── Load data ─────────────────────────────────────────────────────────────────
@st.cache_data
def load_data():
    in_path = Path("/app/simulations/input/input.csv")
    inp = pd.read_csv(in_path) if in_path.exists() else None
    out_path = Path("/app/simulations/output_files/results/daily_sim_outputs.csv")
    out = pd.read_csv(out_path) if out_path.exists() else None
    return inp, out

input_df, output_df = load_data()

# ── Sidebar — Field Inputs ────────────────────────────────────────────────────
st.sidebar.header("Field Configuration")
st.sidebar.info("ℹ️ Input selection coming soon — showing example data below.")

row = input_df.iloc[0]
st.sidebar.text_input("Site Name", value=row.get("Site", ""), disabled=True)
st.sidebar.selectbox("Crop", ["Maize"], disabled=True)
st.sidebar.text_input("Genetics", value=row.get("Genetics", ""), disabled=True)
st.sidebar.date_input("Planting Date", disabled=True)
st.sidebar.number_input("Latitude",  value=float(row.get("Latitude",  0)), disabled=True)
st.sidebar.number_input("Longitude", value=float(row.get("Longitude", 0)), disabled=True)

# ── Main — Chart ──────────────────────────────────────────────────────────────
st.header("📊 Seasonal Risk Timeline")

if output_df is None:
    st.warning("No simulation output found at `simulations/output_files/results/daily_sim_outputs.csv`")
    st.stop()

df = output_df.copy()
selected_lines    = st.multiselect("Overlay variables", list(LINE_VARS),   default=["Max Temp (°C)", "Min Temp (°C)"])
selected_stresses = st.multiselect("Stress indices",    list(STRESS_VARS), default=list(STRESS_VARS))

def build_fig(df, selected_lines, selected_stresses):
    n_stress = len(selected_stresses)
    row_heights = [0.7] + [0.3 / max(n_stress, 1)] * n_stress if n_stress else [1.0]
    fig = make_subplots(rows=1 + max(n_stress, 0), cols=1, shared_xaxes=True,
                        row_heights=row_heights, vertical_spacing=0.02)

    stage_colors = {"Germination": "#2d6a4f", "Vegetative": "#52b788",
                    "Flowering": "#f4a261", "Grain Fill": "#e76f51", "Maturity": "#9b2226"}
    for stage, grp in df.groupby("StageName"):
        fig.add_vrect(x0=grp["DOY"].min(), x1=grp["DOY"].max(),
                      fillcolor=stage_colors.get(stage, "#aaaaaa"), opacity=0.12,
                      line_width=0, annotation_text=stage,
                      annotation_position="top left", annotation_font_size=9)

    colors = ["#4cc9f0","#f72585","#7209b7","#3a86ff","#fb8500","#06d6a0"]
    for i, label in enumerate(selected_lines):
        fig.add_trace(go.Scatter(x=df["DOY"], y=df[LINE_VARS[label]], name=label,
                                 line=dict(color=colors[i % len(colors)], width=1.5)), row=1, col=1)

    for r, (label, cmap) in enumerate(zip(selected_stresses, STRESS_COLORS), start=2):
        fig.add_trace(go.Heatmap(x=df["DOY"], z=[df[STRESS_VARS[label]].values],
                                 colorscale=cmap, showscale=False, name=label), row=r, col=1)
        fig.update_yaxes(showticklabels=False, title_text=label, title_font_size=9, row=r, col=1)

    fig.update_xaxes(title_text="Day of Year", row=1 + max(n_stress, 0), col=1)
    fig.update_layout(height=420 + 80 * n_stress, margin=dict(t=20, b=40),
                      legend=dict(orientation="h", y=1.05))
    return fig

st.plotly_chart(build_fig(df, selected_lines, selected_stresses), use_container_width=True)
