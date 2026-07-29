# ☀️ Pauli's PV System Optimizer

An advanced photovoltaic system optimizer for analyzing and optimizing residential solar installations with battery storage.

## 🌟 Features

### System Configuration
- **Multi-roof support** (1-3 roof surfaces) with independent tilt and azimuth angles
- **Flexible consumption modeling** with built-in load profiles (H0 model)
- **Heat pump integration** for thermal loads with COP calculation
- **Variable battery storage** with configurable efficiency
- **Preset scenarios** (Custom, Typical German household, Heat pump home, EV household)

### Simulation & Analysis
- **Hourly energy simulation** with weather data from PVGIS
- **Battery optimization** (charging/discharging strategy)
- **Self-sufficiency & self-consumption** analysis with visualizations
- **Financial ROI calculations** including NPV, IRR, and payback period
- **Break-even analysis** comparing grid-only vs PV scenarios
- **Energy flow diagrams** showing PV→Load, PV→Battery, and Grid interactions

### Optimization
- **Multi-parameter optimization** across PV size and battery capacity ranges
- **Three optimization targets**: Net Present Value (NPV), Internal Rate of Return (IRR), Payback Period
- **Global optimum detection** (identifies if optimum is at range boundary)
- **Interactive heatmap** visualization with multi-metric tooltips (NPV, IRR, Payback)
- **Objective-value coloring** showing performance across the optimization surface

### Visualization
- Donut charts for self-sufficiency and self-consumption
- Energy flow SVG diagram
- Cost comparison line chart (cumulative costs over system lifetime)
- Time series analysis of generation, consumption, and battery SOC
- Meteorological data (irradiance, temperature, 3-day forecast)

## 📋 Input Parameters

### System Design
- **Latitude/Longitude** for location-based weather data
- **PV size & configuration** (up to 3 roof surfaces with tilt/azimuth)
- **Battery capacity & efficiency** (percentage)
- **Weather data source** (Typical Meteorological Year or Historical Year 2015-2023)

### Financial
- **Electricity prices** (buy price, feed-in tariff)
- **System costs** (€/kWp for PV, €/kWh for battery)
- **Lifetime** (years of system operation)
- **Discount rate** (for NPV calculations)

### Consumption
- **Annual electricity consumption** (kWh)
- **Heat pump mode** with thermal demand (kWh/year) and indoor temperature target
- **Automatic H0 profile** (daily/seasonal/weekend variations)

### Optimization (Optional)
- **PV range** (search range in kWp around base size)
- **Battery range** (search range in kWh around base capacity)
- **Optimization objective** (maximize NPV/IRR or minimize Payback)

## 📊 Output Metrics

### Electricity
- Annual consumption, generation, self-consumption, grid export/import
- Direct PV consumption, battery discharge/charge cycles

### Finance
- Annual benefit, savings, feed-in revenue, grid costs
- Initial investment, NPV, IRR, payback time
- Break-even year, levelized cost of energy (LCOE)

### Optimization Results
- Best system configuration (PV size, battery capacity)
- Global optimum status (✅ YES / ❌ NO)
- Performance metrics (NPV, IRR, Payback) at optimum
- Interactive heatmap with detailed tooltips

## 🚀 Installation & Usage

### Requirements
- Python 3.8+
- See `requirements.txt` for dependencies

### Run locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

Then open your browser to `http://localhost:8501`

### Using the App

1. **Configure System** in the left sidebar:
   - Choose a preset or customize parameters
   - Set roof configurations (tilt, azimuth)
   - Define battery and financial parameters

2. **Run Simulation** by clicking "Run Simulation" button
   - View electricity balance, energy flows, and financial analysis
   - Inspect time series data and meteorological conditions

3. **Optional: Run Optimizer**
   - Enable "Run optimizer" in sidebar
   - Set search ranges and optimization target
   - View heatmap to explore trade-offs across parameter space

## 🔧 Technical Details

### Weather Data
- **Source**: PVGIS API v5.2 (JRC, European Commission)
- **Endpoints**: 
  - Typical Meteorological Year (TMY): Long-term averages
  - Real Historical Year: Year-specific data (2015-2023)

### Simulation Engine
- **PV Model**: Orientation factor, temperature losses, system losses (18% efficiency baseline)
- **Battery**: Hourly state-of-charge tracking with round-trip efficiency
- **Load Profile**: H0 model with hourly, seasonal, and weekend variations
- **Heat Pump**: COP (Coefficient of Performance) scaling with outdoor temperature

### Optimization
- **Algorithm**: Grid search across PV/battery parameter space
- **Boundary Detection**: Identifies if optimum is at search range boundary
- **IRR Calculation**: Newton-Raphson method for cash flow analysis

## 📁 Project Structure

```
pv-optimizer-app/
├── app.py                      # Main Streamlit application
├── energy_flow_graphic.py       # SVG energy flow diagram generation
├── requirements.txt            # Python dependencies
└── README.md                   # This file
```

## 📝 License

MIT

## ⚠️ Disclaimer

This tool is for educational and estimation purposes. Always consult with professional solar installers and financial advisors before making investment decisions.
