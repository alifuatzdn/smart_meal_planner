import streamlit as st
import pandas as pd
from pathlib import Path
from features.menu_generator import generate_weekly_menu

# UI Settings
st.set_page_config(page_title="AI Menu Planner", page_icon="🍽️", layout="wide")
st.title("🤖 AI-Powered Weekly Menu Planner")
st.markdown("Generate your optimized weekly meal menu based on daily goals and diet types.")

# 1. Load Clustered Data
@st.cache_data
def load_data():
    try:
        BASE_DIR = Path(__file__).resolve().parent.parent
        filepath = BASE_DIR / 'data' / 'clustered_data.csv'
        return pd.read_csv(filepath)
    except Exception as e:
        return None

df = load_data()

if df is None:
    st.error("⚠️ Dataset not found. Please run clustering.py to generate 'data/clustered_data.csv' first.")
    st.stop()

# --- LEFT PANEL: User Inputs ---
st.sidebar.header("🎯 Daily Targets")
daily_target_budget = st.sidebar.number_input("Daily Budget (TL)", min_value=10.0, max_value=2000.0, value=300.0, step=50.0)
daily_target_protein = st.sidebar.number_input("Daily Protein (g)", min_value=20.0, max_value=300.0, value=80.0, step=10.0)
daily_target_calories = st.sidebar.number_input("Daily Calories (kcal)", min_value=1000.0, max_value=5000.0, value=2200.0, step=100.0)

st.sidebar.markdown("---")
st.sidebar.header("👤 User Profile")
diet_type = st.sidebar.selectbox("Diet Type", ["General/Standard", "Diabetic", "Vegan"])
diet_mapping = {"General/Standard": "standard", "Diabetic": "diabetic", "Vegan": "vegan"}

# Generate Button
generate_btn = st.sidebar.button("Generate Menu 🚀", type="primary")

# --- RIGHT PANEL: Algorithm & Output ---
if generate_btn:
    user_profile = {'diet': diet_mapping[diet_type]}

    st.markdown("### 📅 Your Menu For This Week")

    weekly_menu = generate_weekly_menu(df, daily_target_budget, daily_target_protein, daily_target_calories, user_profile)

    days = list(weekly_menu.keys())
    tabs = st.tabs(days)

    weekly_actual_budget = 0
    weekly_actual_protein = 0
    weekly_actual_calories = 0

    for i, day in enumerate(days):
        with tabs[i]:
            day_data = weekly_menu[day]
            col1, col2 = st.columns(2)
            columns_layout = {'Lunch': col1, 'Dinner': col2}

            for m_idx, meal in enumerate(['Lunch', 'Dinner']):
                with columns_layout[meal]:
                    st.subheader(f"🍽️ {meal}")
                    for item in day_data['menu'][meal]:
                        st.markdown(f"**{item['meal_type']}:** {item['recipe_name']}")
                        st.caption(f"💰 {item['price']:.2f} TL | 🥩 {item['protein']}g | 🔥 {item['calories']} kcal")

            st.divider()
            
            # Gerçek harcama = Hedef - Kalan
            actual_budget = daily_target_budget - day_data['remaining_budget']
            actual_protein = daily_target_protein - day_data['remaining_protein']
            actual_calories = daily_target_calories - day_data['remaining_calories']
            
            weekly_actual_budget += actual_budget
            weekly_actual_protein += actual_protein
            weekly_actual_calories += actual_calories

            st.info(f"**End Of Day Status:** Budget: {actual_budget:.1f} / {daily_target_budget:.1f} TL | Protein: {actual_protein:.1f} / {daily_target_protein:.1f}g | Calories: {actual_calories:.1f} / {daily_target_calories:.1f} kcal")

    st.markdown("---")
    st.markdown("### 📊 Weekly Summary")
    
    col_w1, col_w2, col_w3 = st.columns(3)
    
    col_w1.metric(label="Total Budget (TL)", 
                  value=f"{weekly_actual_budget:.1f} / {daily_target_budget*7:.1f}", 
                  delta=f"{weekly_actual_budget - (daily_target_budget*7):.1f} TL", 
                  delta_color="inverse")
                  
    col_w2.metric(label="Total Protein (g)", 
                  value=f"{weekly_actual_protein:.1f} / {daily_target_protein*7:.1f}", 
                  delta=f"{weekly_actual_protein - (daily_target_protein*7):.1f} g")
                  
    col_w3.metric(label="Total Calories (kcal)", 
                  value=f"{weekly_actual_calories:.1f} / {daily_target_calories*7:.1f}", 
                  delta=f"{weekly_actual_calories - (daily_target_calories*7):.1f} kcal")

