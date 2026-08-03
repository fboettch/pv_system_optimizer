import streamlit as st
from streamlit_echarts import st_echarts
from pyecharts.commons.utils import JsCode
import xml.etree.ElementTree as ET
import numpy as np
import pandas as pd
import requests
from energy_flow_graphic import make_figure


st.set_page_config(layout="wide")
st.title("☀️ Pauli's PV System Optimizer")
st.info("Configure the system parameters in the sidebar and click 'Run Simulation'.", icon="ℹ️")

# ------------------------
# PRESETS
# ------------------------
st.sidebar.subheader("Presets")

preset = st.sidebar.selectbox(
    "Scenario",
    ["Custom", "Typical German household", "Heat pump home", "EV household"],
    help="Select a preset scenario to automatically fill in typical values for electricity consumption, battery size, and heat pump usage.")

annual_consumption = 13000
battery_kwh = 20
battery_eff = 90
use_hp = False
hp_annual_heat = 12000

if preset == "Heat pump home":
    annual_consumption = 4500
    battery_kwh = 8
    use_hp = True
elif preset == "EV household":
    annual_consumption = 6000
    battery_kwh = 10

# ------------------------
# INPUTS
# ------------------------
st.sidebar.header("Input parameters")

lat = st.sidebar.number_input("Latitude", value=48.14, help="Latitude of the location in decimal degrees (e.g., 48.14 for Munich, Germany).")
lon = st.sidebar.number_input("Longitude", value=11.58, help="Longitude of the location in decimal degrees (e.g., 11.58 for Munich, Germany).")

battery_kwh = st.sidebar.number_input("Battery (kWh)", value=battery_kwh, help="Capacity of the battery in kilowatt-hours.")
battery_eff = st.sidebar.number_input("Storage efficiency (%)", value=battery_eff, help="Round-trip efficiency of the battery in percent.")

price_buy = st.sidebar.number_input("Electricity price", value=0.30, help="Price of electricity from the grid in euros per kilowatt-hour.")
price_sell = st.sidebar.number_input("Feed-in tariff", value=0.08, help="Tariff for feeding excess electricity into the grid in euros per kilowatt-hour.")

weather_data = st.sidebar.selectbox("Weather Data",
                                    ["Typical Meteorological Year",
                                     "Real Historical Year"], 
                                     help="Select the type of weather data to use for the simulation. 'Typical Meteorological Year' uses averaged data, while 'Real Historical Year' uses actual historical data for a specific year.")

if weather_data == "Real Historical Year":
    ref_year = st.sidebar.slider("Reference year", 2015, 2023, 2020, 1)
else:
    ref_year = 2026


# ------------------------
# ROOF CONFIG
# ------------------------
st.sidebar.subheader("Roof configuration")

num_roofs = st.sidebar.slider("Number of roof surfaces", 1, 3, 1, 
                              help="Select the number of roof surfaces to model. Each roof can have its own PV size, tilt, and azimuth angle.")

roof_configs = []

for i in range(num_roofs):
    st.sidebar.markdown(f"### Roof {i+1}")

    size = st.sidebar.number_input(f"PV Size kWp (Roof {i+1})", value=20, key=f"size_{i}", 
                                   help="Peak power of the PV system on this roof in kilowatt.")
    tilt = st.sidebar.slider(f"Tilt ° (Roof {i+1})", 0, 90, 30, key=f"tilt_{i}", 
                             help="Inclination of the PV system on this roof in degrees. 0° is flat, 90° is vertical.")
    azimuth = st.sidebar.slider(f"Azimuth ° (Roof {i+1})", -180, 180, i * 90, key=f"az_{i}", 
                                help="Orientation of the PV system on this roof in degrees. 0° is south, -90° is east, 90° is west.")

    roof_configs.append({
        "size": size,
        "tilt": tilt,
        "azimuth": azimuth
    })

# =====================================================
# CONSUMPTION
# =====================================================

st.sidebar.header("Consumption")

annual_consumption = st.sidebar.number_input(
    "Annual Electricity Consumption (kWh)",
    value=annual_consumption,
    help="Total annual electricity consumption in kilowatt-hours (kWh). This includes all household electricity usage, such as lighting, appliances, and electronics.")

use_hp = st.sidebar.checkbox(
    "Include Heat Pump",
    value=use_hp,
    help="Check to include a heat pump in the demand simulation.")
if use_hp:
    hp_annual_heat = st.sidebar.number_input(
        "Annual heat demand (kWh thermal)", value=12000, help="Total annual heat demand in kilowatt-hours (kWh thermal) for the heat pump. This represents the amount of heat energy required for space heating and hot water.")

    indoor_temp = st.sidebar.number_input(
        "Indoor temperature (°C)", value=21, help="Required indoor temperature in degrees Celsius.")

run = st.button("Run simulation")

# ------------------------
# FINANCIALS
# ------------------------

st.sidebar.subheader("Financial parameters")
                     
pv_cost_per_kwp = st.sidebar.number_input("PV cost €/kWp", value=1200, help="Cost of the PV system per kilowatt peak in euros (including wiring, mounting, installation, etc.).")
battery_cost_per_kwh = st.sidebar.number_input("Battery cost €/kWh", value=600, help="Cost of the battery per kilowatt-hour in euros (including wiring, mounting, installation, etc.).")

lifetime = st.sidebar.slider("System lifetime (years)", 5, 30, 20, help="Expected lifetime of the system in years.")
discount_rate = st.sidebar.slider("Discount rate (%)", 0.0, 10.0, 3.0, help="Discount rate for NPV calculation in percent.")
discount_rate = discount_rate / 100 

# ------------------------
# OPTIMIZER
# ------------------------

st.sidebar.subheader("Optimizer")

run_optimization = st.sidebar.checkbox("Run optimizer", value=False, help="Enable to run the optimization over a range of PV and battery sizes.")
pv_range = st.sidebar.slider("PV power range", 1, 20, 5, help="Range of PV power (kWp) to explore around the current configuration for optimization.")
bat_range = st.sidebar.slider("Battery capacity range", 0, 20, 5, help="Range of battery capacity (kWh) to explore around the current configuration for optimization.")

objective = st.sidebar.selectbox(
    "Optimization target",
    ["Net Present Value", "Internal Rate of Return", "Payback"],
    help="Select the objective for optimization. 'Net Present Value' maximizes the total value of the system, 'Internal Rate of Return' maximizes the percentage return, and 'Payback' minimizes the time to recover the investment."
)

# set min max
pv_size = sum([r['size'] for r in roof_configs])
pv_min = max(0, int(pv_size - pv_range))
pv_max = int(pv_size + pv_range)
bat_min = max(0, int(battery_kwh - bat_range))
bat_max = int(battery_kwh + bat_range)

# ------------------------
# WEATHER (PVGIS)
# ------------------------

@st.cache_data(ttl=86400)
def load_weather(lat, lon, y):
    url = "https://re.jrc.ec.europa.eu/api/v5_2/seriescalc"
    params = {
        "lat": lat,
        "lon": lon,
        "outputformat": "json",
        "pvcalculation": 0,
        "startyear": y,
        "endyear": y
    }
    data = requests.get(url, params=params).json()
    df = pd.DataFrame(data["outputs"]["hourly"])
    df["irradiance"] = df["G(i)"]
    df["temperature"] = df["T2m"]
    return df

@st.cache_data(ttl=86400)
def load_weather_tmy(latitude, longitude):
    url = "https://re.jrc.ec.europa.eu/api/v5_2/tmy"
    parameters = {
        "lat": latitude,
        "lon": longitude,
        "outputformat": "json"
    }
    response = requests.get(url, params=parameters, timeout=30)
    response.raise_for_status()
    data = response.json()
    df = pd.DataFrame(data["outputs"]["tmy_hourly"])
    df["irradiance"] = df["G(h)"]
    df["temperature"] = df["T2m"]
    return df

# ------------------------
# SIMULATION
# ------------------------

def compute_pv_power(df, roof):
    pv_efficiency = 0.18
    system_loss = 0.14
    area_per_kwp = 5.0

    pv_area = roof["size"] * area_per_kwp

    # Compute constants once
    azimuth_rad = np.radians(roof["azimuth"])
    tilt_rad = np.radians(roof["tilt"])

    orientation_factor = (
        np.cos(tilt_rad) * 0.8 +
        np.cos(azimuth_rad) * 0.2)
    orientation_factor = max(0.0, orientation_factor)

    # Extract columns as NumPy arrays
    G = df["irradiance"].to_numpy()
    T = df["temperature"].to_numpy()
    temp_loss = 1 - 0.004 * (T - 25)

    power = (
        pv_area
        * pv_efficiency
        * G / 1000.0
        * orientation_factor
        * temp_loss
        * (1 - system_loss))
    return np.maximum(power, 0.0)


def calculate_load_profile(annual_consumption, hours, time_index):
    avg_hourly = annual_consumption / hours
    load = []

    for t in range(hours):
        ts = time_index[t]

        hour = ts.hour
        day = ts.dayofyear
        weekday = ts.weekday()

        # Daily profile
        if 0 <= hour < 5:
            f_day = 0.5
        elif 5 <= hour < 8:
            f_day = 1.2
        elif 8 <= hour < 16:
            f_day = 0.8
        elif 16 <= hour < 22:
            f_day = 1.5
        else:
            f_day = 0.7

        # Seasonal factor
        f_season = 1.2 - 0.4 * np.cos(2 * np.pi * day / 365)

        # Weekend
        f_week = 1.1 if weekday >= 5 else 1.0

        load.append(avg_hourly * f_day * f_season * f_week)

    load = np.array(load)
    load *= annual_consumption / load.sum()  # Normalize exactly

    return load


def calculate_heat_pump_load(load, temp, indoor_temp, hp_annual_heat):
    hours = len(load)
    heat_load = []

    for t in range(hours):
        T_out = temp[t]

        # Heating demand (only below indoor temp)
        deltaT = max(0, indoor_temp - T_out)

        # Thermal demand proportional to deltaT
        heat = deltaT

        # COP model (clamped)
        cop = max(2.0, 3.0 - 0.05 * (indoor_temp - T_out))

        # Electricity consumption
        elec = heat / cop

        heat_load.append(elec)

    heat_load = np.array(heat_load)
    heat_load *= hp_annual_heat / heat_load.sum()  # Normalize to annual heat demand

    return load + heat_load  # Add to base load


def calculate_battery_simulation(df, load, battery_kwh, eff=95):

    eff = eff/100
    pv = df["P_kW"].to_numpy()
    load = np.asarray(load)

    n = len(pv)

    soc = 0.0
    grid_import = 0.0
    grid_export = 0.0
    direct_pv_consumption = 0.0
    battery_to_load = 0.0
    pv_to_battery = 0.0

    soc_trace = np.empty(n, dtype=np.float64)

    inv_eff = 1.0 / eff

    for t in range(n):
        pv_t = pv[t]
        demand = load[t]

        direct = pv_t if pv_t < demand else demand
        direct_pv_consumption += direct

        surplus = pv_t - direct
        deficit = demand - direct

        if surplus > 0.0:
            available_capacity = battery_kwh - soc
            charge = min(surplus * eff, available_capacity)

            soc += charge
            surplus -= charge * inv_eff

            if surplus * eff < available_capacity:
                pv_to_battery += charge * inv_eff

        if deficit > 0.0:
            discharge = min(deficit * inv_eff, soc)

            supplied = discharge * eff
            battery_to_load += supplied

            soc -= discharge
            deficit -= supplied

        if surplus > 0.0:
            grid_export += surplus

        if deficit > 0.0:
            grid_import += deficit

        soc_trace[t] = soc

    return {
        "soc_trace": soc_trace,
        "grid_import": grid_import,
        "grid_export": grid_export,
        "direct_pv_consumption": direct_pv_consumption,
        "battery_to_load": battery_to_load,
        "pv_to_battery":  pv_to_battery,
        "total_self_consumption": direct_pv_consumption + battery_to_load,
    }


def irr(cashflows, guess=0.1, tol=1e-7, max_iter=1000):
    """
    Calculate the Internal Rate of Return (IRR).

    Parameters
    ----------
    cashflows : list or iterable
        Cash flows where cashflows[0] is the initial investment
        (typically negative) and subsequent values are future cash flows.
    guess : float
        Initial rate guess.
    tol : float
        Convergence tolerance.
    max_iter : int
        Maximum number of iterations.

    Returns
    -------
    float
        IRR as a decimal (e.g. 0.15 = 15%).

    Raises
    ------
    ValueError
        If the algorithm does not converge.
    """

    rate = guess

    for _ in range(max_iter):
        # NPV
        npv = sum(cf / (1 + rate) ** t for t, cf in enumerate(cashflows))

        # Derivative of NPV with respect to rate
        d_npv = sum(
            -t * cf / (1 + rate) ** (t + 1)
            for t, cf in enumerate(cashflows)
            if t > 0
        )
        new_rate = rate - npv / d_npv

        if abs(new_rate - rate) < tol:
            return new_rate

        rate = new_rate
    return None


def scale_to_range(values, min_range, max_range):
    min_val = min(values)
    max_val = max(values)

    if max_val == min_val:
        return [min_range] * len(values)

    return [
        min_range + (v - min_val) * (max_range - min_range) / (max_val - min_val)
        for v in values
    ]


def simulate_system(pv_size, battery_kwh, roof_configs, load):
    # Scale roof sizes proportionally
    total_roof = sum(r["size"] for r in roof_configs)

    scaled_roofs = []
    for r in roof_configs:
        scaled_roofs.append({
            "size": pv_size * (r["size"] / total_roof),
            "tilt": r["tilt"],
            "azimuth": r["azimuth"]
        })

    # PV generation
    pv_total = np.zeros(len(df))
    for roof in scaled_roofs:
        pv_total += compute_pv_power(df, roof)
    df["P_kW"] = pv_total

    # Battery simulation
    bat = calculate_battery_simulation(df, load, battery_kwh, eff=battery_eff)

    # Economics
    savings = bat["total_self_consumption"] * price_buy
    revenue = bat["grid_export"] * price_sell
    costs = bat["grid_import"] * price_buy

    annual_benefit = savings + revenue - costs
    total_investment = (pv_size * pv_cost_per_kwp +
                        battery_kwh * battery_cost_per_kwh)

    # calculate npv
    npv = sum([annual_benefit / ((1 + discount_rate)**t)
               for t in range(1, lifetime + 1)]) - total_investment

    # Payback
    payback = total_investment / annual_benefit if annual_benefit > 0 else 999

    # calculate irr
    basic_cashflows = [annual_benefit for _ in range(lifetime)]
    basic_cashflows.insert(0, -total_investment)
    irr_res = irr(basic_cashflows)
    return {
        "npv": npv,
        "irr": irr_res,
        "payback": payback,
        "pv": pv_size,
        "battery": battery_kwh
    }


def make_donut_chart(label_value_color: dict, autarky):

    options = {
        "tooltip": {"trigger": "item"},
        #"legend": {"top": "5%", "left": "center"},
        "series": [
            {
                "name": "Share in %",
                "type": "pie",
                "radius": ["40%", "70%"],
                "avoidLabelOverlap": False,
                "padAngle": 5,
                "itemStyle": {
                    "borderRadius": 10,
                    "borderColor": "#fff",
                    "borderWidth": 2,
                },
                "label": {
                    "show": True,
                    "position": "center",
                    "formatter": f"{round(autarky,1)}%",
                    "fontSize": 24,
                    "fontWeight": "bold",
                },
                "emphasis": {
                    "label": {"show": False}
                },
                "data": [{"value": value, "name": label, "itemStyle": {"color": color}}
                          for label, (value, color) in label_value_color.items()
                ],
            }
        ],
    }
    return options


def make_line_chart(years, grid_only_costs, pv_costs, c_grid, c_pv):
    """Create ECharts line chart for cost comparison.
    
    Args:
        years: Array of years.
        grid_only_costs: Array of cumulative costs for grid-only scenario.
        pv_costs: Array of cumulative costs for PV system scenario.
    
    Returns:
        dict: ECharts options object.
    """
    option = {
        "tooltip": {
            "trigger": "axis",
            "formatter": JsCode("""function(params) {
                if (!params.length) return '';
                let result = 'Year: ' + params[0].axisValue + '<br>';
                for (let i = 0; i < params.length; i++) {
                    result += params[i].marker + params[i].seriesName + ': ' + Math.round(params[i].value) + ' €<br>';
                }
                return result;
            }""").js_code
        },
        "legend": {"data": ["Grid Electricity Only", "Photovoltaic System"], "top": "5%"},
        "xAxis": {
            "type": "category",
            "data": years.tolist(),
            "name": "Years",
            "nameLocation": "middle",
            "nameGap": 30,
        },
        "yAxis": {
            "type": "value",
            "name": "Cumulative Cost (€)",
            "nameLocation": "middle",
            "nameGap": 40,
        },
        "grid": {"left": 80, "right": 80, "bottom": 60, "top": 80},
        "series": [
            {
                "name": "Grid Electricity Only",
                "type": "line",
                "data": grid_only_costs.tolist() if hasattr(grid_only_costs, 'tolist') else grid_only_costs,
                "lineStyle": {"width": 4, "color": c_grid},
                "itemStyle": {"color": c_grid},
                "symbol": "circle",
                "symbolSize": 8,
                "emphasis": {"focus": "series"},
            },
            {
                "name": "Photovoltaic System",
                "type": "line",
                "data": pv_costs.tolist() if hasattr(pv_costs, 'tolist') else pv_costs,
                "lineStyle": {"width": 4, "color": c_pv},
                "itemStyle": {"color": c_pv},
                "symbol": "circle",
                "symbolSize": 8,
                "emphasis": {"focus": "series"},
            },
        ],
    }
    return option


def is_optimum_in_interior(df_opt, objective_id, pv_min, pv_max, bat_min, bat_max):
    """Determine if the global optimum is within the optimization range (not at boundaries).
    
    Args:
        df_opt: DataFrame containing optimization results with pv, battery, npv, irr, payback columns.
        objective_id: ID of the objective column ("npv", "irr", or "payback").
        pv_min: Minimum PV capacity in optimization range.
        pv_max: Maximum PV capacity in optimization range.
        bat_min: Minimum battery capacity in optimization range.
        bat_max: Maximum battery capacity in optimization range.
    
    Returns:
        bool: True if optimum is in interior (global optimum reached), False if at boundary.
    """
    if objective_id == "payback":
        # For payback, we want the minimum
        best_idx = df_opt[objective_id].idxmin()
    else:
        # For NPV and IRR, we want the maximum
        best_idx = df_opt[objective_id].idxmax()
    
    best = df_opt.loc[best_idx]
    best_pv = best["pv"]
    best_bat = best["battery"]
    
    # Check if at boundary
    at_pv_boundary = (best_pv == pv_min) or (best_pv == pv_max)
    at_bat_boundary = (best_bat == bat_min) or (best_bat == bat_max)
    
    # Global optimum is in interior if NOT at any boundary
    return not (at_pv_boundary or at_bat_boundary)


def make_heat_map(df_opt, objective_name, objective_id):
    """Create a heatmap showing optimization results across PV and Battery capacity.
    
    Args:
        df_opt: DataFrame containing optimization results with pv, battery, npv, irr, payback columns.
        objective_name: Name of the objective (string for legend title).
        objective_id: ID of the objective column ("npv", "irr", or "payback").
    
    Returns:
        dict: ECharts heatmap options object.
    """
    pv_values = df_opt["pv"]
    battery_values = df_opt["battery"]
    objective_values = df_opt[objective_id]
    
    # Get unique sorted values
    pv_unique = sorted(pv_values.unique())
    battery_unique = sorted(battery_values.unique())
    
    # Create data points for the heatmap using objective values
    data = []
    obj_min = objective_values.min()
    obj_max = objective_values.max()
    
    for i, pv in enumerate(pv_unique):
        for j, bat in enumerate(battery_unique):
            mask = (pv_values == pv) & (battery_values == bat)
            if mask.any():
                idx = mask.idxmax()
                row = df_opt.loc[idx]
                value = row[objective_id]
                # Store metrics for tooltip, with objective value as last element for color mapping
                data.append([j, i, row['npv'], row['irr'], row['payback'], value])
    
    option = {
        "tooltip": {
            "position": "top",
            "formatter": JsCode("""function(params) {
                if (!params.value) return '';
                let result = 'Objective: """ + objective_name + """<br>';
                result += 'NPV: ' + Math.round(params.value[2]) + ' €<br>';
                result += 'IRR: ' + (Math.round(params.value[3] * 1000) / 10) + ' %<br>';
                result += 'Payback: ' + (Math.round(params.value[4] * 10) / 10) + ' years';
                return result;
            }""").js_code
        },
        "grid": {"height": "90%", "top": "5%", "left": "8%", "right": "15%", "bottom": "5%"},
        "xAxis": {
            "type": "category",
            "data": [str(int(b)) for b in battery_unique],
            "name": "Battery (kWh)",
            "nameLocation": "middle",
            "nameGap": 30,
            "axisLabel": {"fontSize": 16},
            "splitArea": {"show": True}
        },
        "yAxis": {
            "type": "category",
            "data": [str(int(p)) for p in pv_unique],
            "name": "PV (kWp)",
            "nameLocation": "middle",
            "nameGap": 40,
            "axisLabel": {"fontSize": 16},
            "splitArea": {"show": True}
        },
        "visualMap": {
            "min": obj_min,
            "max": obj_max,
            "calculable": True,
            "orient": "vertical",
            "right": "2%",
            "top": "center",
            "textStyle": {"color": "#000", "fontSize": 16},
            "inRange": {"color": ["#313695", "#4575b4", "#74add1", "#abd9e9", 
                                  "#e0f3f8", "#ffffbf", "#fee090", "#fdae61", 
                                  "#f46d43", "#d73027", "#a50026"]},
        },
        "series": [
            {
                "name": objective_name,
                "type": "heatmap",
                "data": data,
                "emphasis": {
                    "itemStyle": {"shadowBlur": 10, "shadowColor": "rgba(0, 0, 0, 0.5)"}
                },
            }
        ],
    }
    return option


# ------------------------
# WEATHER DATA
# ------------------------
with st.spinner("Fetching solar data...", show_time=True):
    if weather_data == "Real Historical Year":
        df = load_weather(lat, lon, ref_year)
    elif weather_data == "Typical Meteorological Year":
        df = load_weather_tmy(lat, lon)

if run:
    # ------------------------
    # MULTI-ROOF PV MODEL
    # ------------------------

    pv_total = np.zeros(len(df))
    for roof in roof_configs:
        pv_total += compute_pv_power(df, roof)
    df["P_kW"] = pv_total

    # ------------------------
    # LOAD PROFILE (H0 model)
    # ------------------------

    hours = len(df)
    time_index = pd.date_range(f"{ref_year}-01-01", 
                               periods=hours, freq="h")
    load = calculate_load_profile(annual_consumption, hours, time_index)

    if use_hp:
        load = calculate_heat_pump_load(load, df["temperature"].values, 
                                        indoor_temp, hp_annual_heat)

    # ------------------------
    # BATTERY SIMULATION
    # ------------------------
    bat = calculate_battery_simulation(df, load, battery_kwh, eff=battery_eff)

    # ------------------------
    # ECONOMICS
    # ------------------------

    savings = bat["total_self_consumption"] * price_buy
    revenue = bat["grid_export"] * price_sell
    costs = bat["grid_import"] * price_buy

    total_pv_size = sum(r["size"] for r in roof_configs)

    investment_pv = total_pv_size * pv_cost_per_kwp
    investment_battery = battery_kwh * battery_cost_per_kwh
    total_investment = investment_pv + investment_battery

    annual_benefit = savings + revenue - costs
    payback = total_investment / annual_benefit if annual_benefit > 0 else None

    # yearly cost comparison
    annual_grid_only_cost = annual_consumption * price_buy
    annual_cost_with_pv = (bat["grid_import"] * price_buy - revenue)

    # calculate npv
    npv = sum([annual_benefit / ((1 + discount_rate)**t)
               for t in range(1, lifetime + 1)]) - total_investment
    
    # calculate lcoe
    discounted_energy = sum(
        bat["total_self_consumption"]*bat["grid_export"] / (1 + discount_rate) ** year
        for year in range(1, lifetime + 1))
    lcoe_value = -npv/discounted_energy

    # cost comparison
    grid_only_costs = []
    pv_costs = []
    for year in range(0, lifetime + 1):
        # Base case (no PV)
        grid_only_costs.append(annual_grid_only_cost * year)
        # PV case
        pv_costs.append(total_investment + annual_cost_with_pv * year)

    # calculate break even
    break_even_year = None
    for year in range(0, lifetime + 1):
        if pv_costs[year] < grid_only_costs[year]:
            break_even_year = year
            break

    # calculate irr
    basic_cashflows = [annual_benefit for _ in range(lifetime)]
    basic_cashflows.insert(0, -total_investment)
    irr_res = irr(basic_cashflows)

    # ------------------------
    # OUTPUT
    # ------------------------

    st.header("Electricity")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total annual consumption", f"{annual_consumption:.0f} kWh",
                help="Electricity consumed as specified in the input.")
    col2.metric("Total annual production", f"{bat['total_self_consumption'] + bat['grid_export']:.0f} kWh", 
                help="Electricity produced by the PV system, including both self-consumed and exported energy.")
    col3.metric("Total self consumption", f"{bat['total_self_consumption']:.0f} kWh",
                help="Electricity consumed directly from the PV system and battery discharge.")
    col4.metric("Grid export (surplus)", f"{bat['grid_export']:.0f} kWh",
                help="Export to the electricity grid.")

    col1.metric("Direct PV consumption", f"{bat['direct_pv_consumption']:.0f} kWh",
                help="Electricity consumed directly from the PV system without storage.")
    col2.metric("Battery discharge", f"{bat['battery_to_load']:.0f} kWh",
                help="Electricity discharged from the battery is charging reduced by storage efficiency as set in the inputs.")
    col3.metric("Battery charge", f"{bat['pv_to_battery']:.0f} kWh",
                help="Electricity charged from the PV system into the battery.")
    col4.metric("Grid import (deficit)", f"{bat['grid_import']:.0f} kWh",
                help="Electricity imported from the grid to cover the demand in low production periods.")

    widths = scale_to_range([bat['grid_export'], bat['grid_import'], 
                            bat['direct_pv_consumption'], bat['battery_to_load'], 
                            bat['pv_to_battery']], min_range=20, max_range=60)
    svg = make_figure(*widths)

    # scale figure
    factor = 0.5
    svg.set("width", str(float(svg.get("width")) * factor))
    svg.set("height", str(float(svg.get("height")) * factor))

    # Colors
    GREEN = "#7BC000"
    DARK_GREEN = "#3A7E00"
    YELLOW = "#F2B500"
    LIGHT_GRAY = "#BEBEBE"
    DARK_GRAY = "#666666"

    a_label_value_color = {
        "Battery discharge": (round(bat['battery_to_load']/annual_consumption*100,1), DARK_GREEN),
        "Grid import": (round(bat['grid_import']/annual_consumption*100,1), DARK_GRAY),
        "Direct consumption": (round(bat['direct_pv_consumption']/annual_consumption*100,1), YELLOW),
    }
    autark_share = bat['total_self_consumption'] / annual_consumption * 100

    e_label_value_color = {
        "Battery charging": (round(bat['pv_to_battery']/(bat['total_self_consumption'] + bat['grid_export'])*100,1), GREEN),
        "Grid export": (round(bat['grid_export']/(bat['total_self_consumption'] + bat['grid_export'])*100,1), LIGHT_GRAY),
        "Direct consumption": (round(bat['direct_pv_consumption']/(bat['total_self_consumption'] + bat['grid_export'])*100,1), YELLOW),
    }
    eigen_share = bat['total_self_consumption'] / (bat['total_self_consumption'] + bat['grid_export']) * 100

    col1, col2, col3 = st.columns([1, 2, 1], gap="small")
    with col1:
        st.subheader("Self-sufficiency")
        st_echarts(
            options=make_donut_chart(a_label_value_color, autark_share),
            height="400px"
        )

    with col2:
        # Convert SVG element to string for display with responsive scaling
        svg_string = ET.tostring(svg, encoding='unicode')
        html_content = f"""
        <html>
        <body style="display: flex; justify-content: center; align-items: center; margin: 0; padding: 0px;">
            {svg_string}
        </body>
        </html>
        """
        st.iframe(html_content, height="content", width="stretch")

    with col3:
        st.subheader("Self-consumption")
        st_echarts(
            options=make_donut_chart(e_label_value_color, eigen_share),
            height="400px"
        )

    st.header("Finance")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Annual benefit", f"{annual_benefit:.0f} €", 
                help="The net benefit of the PV system. It is calculated as savings + revenue - grid cost.")
    col2.metric("Annual savings", f"{savings:.0f} €", 
                help="The savings from reduced electricity bills.")
    col3.metric("Annual feed-in revenue", f"{revenue:.0f} €", 
                help="The revenue from selling excess electricity to the grid. Is calculated as grid export * feed-in tariff.")
    col4.metric("Annual grid costs", f"{costs:.0f} €", 
                help="The costs of importing electricity from the grid. Is calculated as grid import * electricity price.")

    col1.metric("Initial Investment", f"{total_investment:.0f} €", 
                help="Investment required for the PV + Battery. Is calculated as PV size * PV cost + Battery size * Battery cost.")
    col2.metric("Net Present Value", f"{npv:.0f} €", 
                help="The net present value of the PV system over its lifetime. It is calculated as the sum of discounted annual benefits minus the initial investment.")
    col3.metric("Internal Rate of Return", f"{irr_res*100:.1f} %" if irr_res else "N/A", 
                help="The internal rate of return of the PV system. It is the discount rate that makes the net present value of all cash flows equal to zero.")
    col4.metric("Payback time", f"{payback:.1f} years" if payback else "N/A", 
                help="The time it takes for the PV system to pay for itself. It is calculated as the initial investment divided by the annual benefit.")

    st.subheader("Cost comparison")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Annual electricity cost grid only", f"{annual_grid_only_cost:.0f} €",
                help="Electricity cost without PV system. It is calculated as annual consumption * electricity price.")
    col2.metric("Annual electricity cost with PV", f"{annual_cost_with_pv:.0f} €",
                help="Electricity cost with PV system. It is calculated as grid costs minus revenue.")
    col3.metric("Break-even reached after", f"{break_even_year} years" if break_even_year is not None else "N/A",
                help="The time it takes for the PV system to reach the break-even point. It is the year when the cumulative cost of the PV system becomes lower than the cumulative cost of grid electricity.")
    col4.metric("Levelized cost of energy", f"{lcoe_value:.0f} €/kWh" if lcoe_value > 1 else f"{lcoe_value*100:.0f} ct/kWh",
                help="The levelized cost of energy. It is calculated as the net present value of the PV system divided by the discounted energy.")

    # ------------------------
    # PLOTS
    # ------------------------

    years = np.arange(0, lifetime + 1)
    options = make_line_chart(years, grid_only_costs, pv_costs, DARK_GRAY, YELLOW)
    st_echarts(options=options, height="500px")

    with st.expander("📈 Meteorological Data", expanded=False):
        st.header("Time series (first 3 days)", 
                  help="Winter conditions are shown for the first 72 hours of the year.")
        st.subheader("Electricity consumption, PV generation and battery SOC",
                     help="The PV generation is based on the roof configuration and the weather data. The battery state of charge (SOC) is shown as a percentage of the total battery capacity.")

        plot_df = pd.DataFrame({
            "PV": df["P_kW"][:72].values,
            "Load": load[:72],
            "SOC": bat["soc_trace"][:72]})

        st.line_chart(plot_df, x_label="hours", y_label="kW / kWh")
        
        st.subheader("Irradiance")
        st.line_chart(df["irradiance"][:72], x_label="hours", y_label="W/m²")

        st.subheader("Temperature")
        st.line_chart(df["temperature"][:72], x_label="hours", y_label="°C")

    # ------------------------
    # OPTIMIZATION
    # ------------------------

    if run_optimization:
        st.header(f"System size optimization for {objective}")

        hours = len(df)
        time_index = pd.date_range(f"{ref_year}-01-01", 
                                periods=hours, freq="h")

        load = calculate_load_profile(annual_consumption, hours, time_index)

        if use_hp:
            load = calculate_heat_pump_load(load, df["temperature"].values, 
                                            indoor_temp, hp_annual_heat)

        with st.spinner("Optimization in progress...", show_time=True):
            results = []
            for pv in range(pv_min, pv_max + 1, 1):
                for bat in range(bat_min, bat_max + 1, 1):
                    res = simulate_system(pv, bat, roof_configs, load)
                    results.append(res)
            df_opt = pd.DataFrame(results)

        if objective == "Net Present Value":
            best = df_opt.loc[df_opt["npv"].idxmax()]
            v_id = "npv"
        elif objective == "Internal Rate of Return":
            best = df_opt.loc[df_opt["irr"].idxmax()]
            v_id = "irr"
        elif objective == "Payback":
            best = df_opt.loc[df_opt["payback"].idxmin()]
            v_id = "payback"
        df_opt["opti"] = df_opt[v_id]

        # Determine if global optimum is reached
        optimum_reached = is_optimum_in_interior(df_opt, v_id, pv_min, pv_max, bat_min, bat_max)

        col1, col2, col3 = st.columns(3)
        col1.metric("PV power", f"{best['pv']:.0f} kWp",
                    help="The optimal peak power of the PV system.")
        col2.metric("Battery capacity", f"{best['battery']:.0f} kWh",
                    help="The optimal capacity of the battery system.")
        col3.metric("Global optimum reached", "✅ YES" if optimum_reached else "❌ NO",
                    help="If NOT reached, consider expanding the range for better results or set pv size or battery size to the local optimum and rerun.")

        col1, col2, col3 = st.columns(3)
        col1.metric("Net Present Value", f"{best['npv']:.0f} €", 
                    help="The net present value of the PV system over its lifetime. It is calculated as the sum of discounted annual benefits minus the initial investment.")
        col2.metric("Internal Rate of Return", f"{best['irr']*100:.1f} %",
                    help="The internal rate of return of the PV system. It is the discount rate that makes the net present value of all cash flows equal to zero.")
        col3.metric("Payback", f"{best['payback']:.1f} years",
                    help="The time it takes for the PV system to pay for itself. It is calculated as the initial investment divided by the annual benefit.")

        st.subheader(f"{objective} optimization heatmap")
        options = make_heat_map(df_opt, objective, v_id)
        st_echarts(options=options, height="700px")

        with st.expander("Optimization result values", expanded=False):
            st.subheader(f"Objective Values for {objective}")
            if not optimum_reached:
                st.warning("The global optimum is at the boundary of the optimization range. Consider expanding the range for better results.", icon="⚠️")
            pivot = df_opt.pivot(index="pv", columns="battery", values=v_id)
            st.dataframe(pivot)
