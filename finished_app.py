import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# --- PAGE SETUP ---
st.set_page_config(page_title="Harvest or Hold? Forecaster", layout="wide")
st.title("🌽 Harvest or Hold? Nebraska Corn Market Forecaster")
st.markdown("Enter the current market conditions on the left to predict future price momentum.")

# ==========================================
# 1. THE SIDEBAR (USER INPUTS & LINKS)
# ==========================================
st.sidebar.header("Market Control Panel")

current_week = st.sidebar.slider("Current Week Number", min_value=1, max_value=51, value=6)
target_week = st.sidebar.slider("Target Forecast Week", min_value=current_week+1, max_value=52, value=12)

st.sidebar.markdown("---")
st.sidebar.subheader("Model Settings")
window_size = st.sidebar.number_input("Momentum Window Size (Weeks)", min_value=1, max_value=52, value=4, step=1, help="Must be a whole number between 1 to 52.")

st.sidebar.markdown("---")
st.sidebar.subheader("Seasonal & Price Baseline")
st.sidebar.markdown("*Tip: Refer to the 'Seasonality' column in `Master Sheet for MSEF.csv` for the 10-year baseline average for target week.*")

# Clickable link to your Master Spreadsheet
st.sidebar.markdown("[📊 Master Spreadsheet Reference](https://docs.google.com/spreadsheets/d/1H_GvT5G7hVf1jKdgth3KPQGPs6svWit6x7ozwhnGmMA/edit?usp=sharing)")

current_seasonality = st.sidebar.number_input("Current Seasonality Baseline", value=4.51)

recent_prices_input = st.sidebar.text_input("Recent Prices (comma separated)", "3.78, 3.83, 3.70, 3.84")

st.sidebar.markdown("*Note: Please use the price for **EAST**, as the entire model is based on this region's baseline.*")
st.sidebar.markdown("[📊 Find Latest Prices Here](https://mymarketnews.ams.usda.gov/viewReport/3225)")

st.sidebar.markdown("---")
st.sidebar.subheader("Demand Factors")
demand_ethanol = st.sidebar.number_input("Ethanol Demand (Thousand Barrels/Day)", value=990)
st.sidebar.markdown("[🏭 Latest Ethanol Data: EIA.gov Midwest PADD 2](https://www.eia.gov/dnav/pet/hist/LeafHandler.ashx?n=PET&s=W_EPOOXE_YOP_R20_MBBLD&f=W)")

demand_livestock = st.sidebar.number_input("Livestock Demand (Head)", value=2500000)

# Step-by-Step USDA QuickStats Instructions for Livestock
with st.sidebar.expander("🐄 How to find Livestock Data"):
    st.markdown("""
    1. Go to [USDA QuickStats](https://quickstats.nass.usda.gov/)
    2. **Program:** Survey
    3. **Sector:** Animals & Products
    4. **Group:** Livestock
    5. **Commodity:** Cattle
    6. **Category:** Inventory
    7. **Data Item:** CATTLE, ON FEED - INVENTORY
    8. **Geographic Level:** State -> Nebraska
    9. Click **Get Data** and enter the most recent value!
    """)

st.sidebar.markdown("---")
st.sidebar.subheader("Supply Factors")

# *** NEW: Step-by-Step USDA QuickStats Instructions for Harvest Supply ***
with st.sidebar.expander("🌽 How to calculate Harvest Bushels"):
    st.markdown("""
    **Step 1:** Go to [USDA QuickStats](https://quickstats.nass.usda.gov/)
    
    **Step 2:** Select **Program:** Survey -> **Sector:** Crops -> **Commodity:** Corn -> **Category:** Progress -> **Data Item:** CORN, GRAIN - PROGRESS, MEASURED IN PCT HARVESTED -> **State:** Nebraska.
    
    **Step 3:** Find the percentage harvested for  target week.
    
    **Step 4:** Multiply this percentage (as a decimal) by the newest annual total bushels produced (e.g., 2,027,300,000 bushels for 2025) to get the **Cumulative Harvest**.
    
    **Step 5:** Subtract last week's Cumulative Harvest from this week's to find the **Weekly Bushels Produced**.
    """)

is_harvesting = st.sidebar.number_input("Is it Harvest Season? (1=Yes, 0=No)", min_value=0, max_value=1, value=0, step=1)
weekly_bushels = st.sidebar.number_input("Weekly Bushels Produced", value=0)
cumulative_harvest = st.sidebar.number_input("Cumulative Harvest (Bushels)", value=0)


# ==========================================
# 2. THE MAIN STAGE (THE PREDICTION ENGINE)
# ==========================================
if st.button("🚀 Run Chained Forecast"):
    
    recent_prices = [float(p.strip()) for p in recent_prices_input.split(',')]
    st.subheader(f"Forecasting from Week {current_week + 1} to Week {target_week}...")
    
    forecast_weeks = []
    forecast_prices = []
    
    MAX_WEEKLY_SHIFT = 0.20
    current_confidence = 98.0
    
    for week in range(current_week + 1, target_week + 1):
        moving_avg = np.mean(recent_prices[-window_size:])
        
        future_conditions = pd.DataFrame({
            'Week_Num': [week],
            'Seasonality': [current_seasonality], 
            'Weekly_Bushels_Produced': [weekly_bushels],  
            'Cumulative_Harvest': [cumulative_harvest],       
            'Is_Harvesting': [is_harvesting],            
            'Demand_Ethanol': [demand_ethanol],         
            'Demand_Livestock': [demand_livestock]       
        })

        # --- MOCK PREDICTION STEP ---
        # Note: Replace this with your actual model prediction!
        # future_scaled = scaler.transform(future_conditions)
        # raw_deviation = rf_model.predict(future_scaled)
        raw_deviation = 0.05 # Mocked shift for demonstration
        
        deviation = np.clip(raw_deviation, -MAX_WEEKLY_SHIFT, MAX_WEEKLY_SHIFT)
        predicted_price = moving_avg + deviation
        
        recent_prices.append(predicted_price)
        forecast_weeks.append(week)
        forecast_prices.append(predicted_price)
        
        st.write(f"**Week {week}** | Momentum: ${moving_avg:.2f} | Shift: ${deviation:+.2f} | **PRED PRICE: ${predicted_price:.2f}** | Confidence: {current_confidence:.1f}%")
        current_confidence -= 2.0

    st.success(f"Final Projected Price for Week {target_week}: **${recent_prices[-1]:.2f}**")

    # ==========================================
    # 3. WEB GRAPH GENERATION
    # ==========================================
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(forecast_weeks, forecast_prices, marker='o', color='#DD8452', linestyle='-', linewidth=2)
    ax.set_title("Forecasted Price Trajectory", fontweight='bold')
    ax.set_xlabel("Week Number")
    ax.set_ylabel("Price ($/Bushel)")
    ax.grid(True, linestyle='--', alpha=0.7)
    
    st.pyplot(fig)
