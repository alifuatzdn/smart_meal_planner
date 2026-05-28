import pandas as pd
import optuna
from pathlib import Path
import sys

BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(BASE_DIR / 'src'))

from features.menu_generator import generate_weekly_menu

# --- 1. GROUND TRUTH (e.g., School Cafeteria Actual Data) ---
# Using the weekly average values of the school menu as a reference
GROUND_TRUTH = {
    'avg_weekly_cost': 300 * 7,      # 2100 TL based on daily 300 TL
    'avg_weekly_protein': 80 * 7,    # 560g protein based on daily 80g
    'avg_weekly_calories': 2200 * 7  # 15400 kcal based on daily 2200 kcal
}

# --- 2. LOAD DATA ---
df = pd.read_csv(BASE_DIR / 'data' / 'clustered_data.csv')

def objective(trial):
    # --- 3. HYPERPARAMETERS TO TEST WITH OPTUNA (Search Space) ---
    custom_config = {
        'WEIGHTS': {
            'alpha': trial.suggest_float('alpha', 0.1, 0.9),
            'budget': trial.suggest_float('wt_budget', 0.1, 0.9),
            'protein': trial.suggest_float('wt_protein', 0.1, 0.9),
            'calorie': trial.suggest_float('wt_calorie', 0.1, 0.9),
            'economy_multiplier': trial.suggest_float('wt_eco', 0.05, 0.9)
        },
        'PENALTIES': {
            'budget_exceeded': trial.suggest_float('pen_budget', -9.0, -1.0),
            'similarity': trial.suggest_float('pen_sim', 0.5, 3.0),
            'diabetic_carb_fiber': 0.05
        },
        'REWARDS': {'diabetic_friendly': 0.5},
        'CONSTRAINTS': {'budget_flexibility': trial.suggest_int('flex', 10, 100)}
    }

    # Targets matches 4-course meal layout x 2 times a day
    daily_budget = 300
    daily_protein = 80
    daily_calories = 2200
    user_profile = {'diet': 'standard'}

    # Generate the menu using these weights (selected by optuna)
    weekly_menu = generate_weekly_menu(df, daily_budget, daily_protein, daily_calories, user_profile, custom_config)

    # --- 4. EVALUATE RESULTS (FITNESS / LOSS CALCULATION) ---
    actual_cost = 0
    actual_protein = 0
    actual_calories = 0
    clusters_used = []

    for day, data in weekly_menu.items():
        actual_cost += (daily_budget - data['remaining_budget'])
        actual_protein += (daily_protein - data['remaining_protein'])
        actual_calories += (daily_calories - data['remaining_calories'])
        
        for meal in ['Lunch', 'Dinner']:
            for item in data['menu'][meal]:
                clusters_used.append(item['cluster_id'])

    # Variety Score (Ratio of unique clusters to total meals)
    actual_variety = len(set(clusters_used)) / len(clusters_used) if clusters_used else 0

    # Calculate differences (How much did we deviate from the Ground Truth?)
    # Creating a setup similar to Mean Absolute Percentage Error
    error_cost = abs(GROUND_TRUTH['avg_weekly_cost'] - actual_cost) / max(1, GROUND_TRUTH['avg_weekly_cost'])
    error_protein = abs(GROUND_TRUTH['avg_weekly_protein'] - actual_protein) / max(1, GROUND_TRUTH['avg_weekly_protein'])
    error_calories = abs(GROUND_TRUTH['avg_weekly_calories'] - actual_calories) / max(1, GROUND_TRUTH['avg_weekly_calories'])

    # Instead of comparing to a strict ground truth variety, we just penalize if variety is too low (e.g., below 60%)
    variety_penalty = max(0, 0.6 - actual_variety)

    # We add weights to the loss function to heavily penalize missing protein and calories
    # Total Penalty (Loss/Error) : We will try to MINIMIZE this
    total_loss = error_cost + (error_protein * 3.0) + (error_calories * 3.0) + variety_penalty

    return total_loss

if __name__ == "__main__":
    print("Optuna Optimization Starting...")
    # Our goal is to minimize the Error Rate (Loss)
    study = optuna.create_study(direction="minimize")
    
    # Try 500 different combinations
    study.optimize(objective, n_trials=1000)

    print("\n===============================")
    print("OPTIMIZATION COMPLETED!")
    print(f"Lowest Error Score: {study.best_value:.4f}")
    print("BEST PARAMETERS (CLOSEST TO THE SCHOOL MENU):")
    for key, value in study.best_params.items():
        print(f"  {key}: {value:.3f}")
    print("===============================\n")

    print("\nCopying the best parameters to 'src/config.py'...")
    
    import re
    config_path = BASE_DIR / 'src' / 'config.py'
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config_content = f.read()
            
        best = study.best_params
        
        # Update WEIGHTS
        config_content = re.sub(r"('alpha':\s*)[0-9.-]+", f"\\g<1>{best['alpha']:.3f}", config_content)
        config_content = re.sub(r"('budget':\s*)[0-9.-]+", f"\\g<1>{best['wt_budget']:.3f}", config_content)
        config_content = re.sub(r"('protein':\s*)[0-9.-]+", f"\\g<1>{best['wt_protein']:.3f}", config_content)
        config_content = re.sub(r"('calorie':\s*)[0-9.-]+", f"\\g<1>{best['wt_calorie']:.3f}", config_content)
        config_content = re.sub(r"('economy_multiplier':\s*)[0-9.-]+", f"\\g<1>{best['wt_eco']:.3f}", config_content)
        
        # Update PENALTIES
        config_content = re.sub(r"('budget_exceeded':\s*)[0-9.-]+", f"\\g<1>{best['pen_budget']:.3f}", config_content)
        config_content = re.sub(r"('similarity':\s*)[0-9.-]+", f"\\g<1>{best['pen_sim']:.3f}", config_content)
        
        # Update CONSTRAINTS (integer)
        config_content = re.sub(r"('budget_flexibility':\s*)[0-9.-]+", f"\\g<1>{int(best['flex'])}", config_content)
        
        with open(config_path, 'w', encoding='utf-8') as f:
            f.write(config_content)
            
        print("✅ SUCCESS: All weights and penalties have been automatically added to config.py without altering English comments!")
    except Exception as e:
        print(f"❌ ERROR: An issue occurred while updating config.py: {e}")