**Precision Digital Agriculture Hackathon 2026 -- Track 4: Analytics & Decision Support**

## 1. The Problem

Farmers often detect crop stress too late in the growing season, when yield losses have already occurred. Environmental stressors such as drought, cold freezes, heat stress, nutrient deficiency, and disease risk can develop rapidly and are difficult to monitor consistently across large fields.

Farmers have access to weather forecasts, crop simulation outputs, and satellite imagery, but these data sources are often fragmented and difficult to interpret together. As a result, producers frequently rely on manual scouting or delayed field observations, making it difficult to detect early warning signs and determine when to act. This gap between data availability and practical usability leads to reactive rather than proactive decision making. FieldRisk addresses this challenge by integrating multiple data streams into a unified dashboard that synthesizes information and provides clear, actionable management recommendations.

### Who Is Affected

- Farmers and crop producers managing large acreage
- Agronomists/ Extension personnel
- Farm managers who make operational decisions

### What Decisions?

When to irrigate, when to scout for stress, which maturity group to plant, and weather conditions require interventions.

### Why It Matters

Early detection of stress can enable timely management actions that protect crop yield and reduce unnecessary input costs.

If stress conditions are detected earlier, farmers can:

- Apply irrigation at the optimal time
- Adjust fertilizer applications
- Prioritize scouting in high risk areas
- Intervene quickly to control pests or diseases

Failure to detect stress early can lead to:

- Reduced yields
- Higher input application costs
- Inefficient farm management

## 2. Solution Overview

### Data Acquisition / Decision / Action Outputs 
- Weather data (NASA Power, Open Meteo)
- Apsim Simulations

### Outputs ????
- Trend Prediction
- Phenology 

### Decision

- Risk score
- Stress alerts 
- Maturity rankings
- Forecast warnings
- Simulation overlay
- Feedback Loop

### Actions

- Irrigate, Disinfectation, Fertilizer application
- Scout / Monitor
- No action
- Best maturity group selection ???


The dashboard is built in **Streamlit** with **Plotly** visualizations. It serves:

- **Simulated:** 

## Technical Approach

### Baseline

?? 

### Our Approach

### Data Sources

| Source | Description | Sites |
|--------|-------------|-------|
| Sentinel-2 via Google Earth Engine | NDVI at 10m resolution, 2022 growing season | IAH1-4 |
| Open-Meteo API | 16-day weather forecast (temp, rain, radiation) | IAH1-4 |
| G2F 2022 Phenotypic Data | Field metadata (planting date, maturity, coordinates) | IAH1-4 |
| APSIM/SCE Simulation | Soybean trial outputs (26 maturity groups, daily growth, stress, yield) | IAH5 |
| NASA POWER / ERA5 | Historical weather for APSIM .met files | IAH1-4 |

All data is public. No private keys are required.

### Preprocessing Pipeline

| Notebook | Purpose |
|----------|---------|

| `forecast.ipynb` | Fetch and format Open-Meteo 16-day forecast |
| `nasa_power_download.ipynb` | Download NASA POWER weather data for .met files |


## Results


- **Risk score:** 
- **Maturity advisor:** 
- **Decision recommendations:** Banners update dynamically based on site and year selection, producing appropriate urgency levels.

## Run Instructions

### Quick Start (Local)

```bash
pip install streamlit pandas plotly numpy
streamlit run dashboard.py
```

### Docker

```bash
docker build -t fieldrisk .
docker run -p 8501:8501 fieldrisk
```

Then open `http://localhost:8501` in your browser.

### Judge Mode

No external API keys are required. All data is bundled in the repository:

The dashboard runs entirely offline from cached CSV files.???

## Constraints and Limitations
