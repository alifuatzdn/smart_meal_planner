import numpy as np
from config import WEIGHTS, PENALTIES, REWARDS, CONSTRAINTS

class MealRole:
    SOUP = 'Çorba'
    MAIN_COURSE = 'Ana Yemek'
    SIDE_DISH = 'Yan Yemek'
    SALAD = 'Salata'
    SINGLE_MEAL = 'Tek Öğün'

def _get_config(custom_config):
    """Fallback to main config if a custom one isn't fully provided."""
    weights = custom_config['WEIGHTS'] if custom_config else WEIGHTS
    penalties = custom_config['PENALTIES'] if custom_config else PENALTIES
    rewards = custom_config['REWARDS'] if custom_config else REWARDS
    constraints = custom_config['CONSTRAINTS'] if custom_config else CONSTRAINTS
    return weights, penalties, rewards, constraints

def _generate_meal_structure():
    """Generates the categories of dishes for a given meal."""
    is_single_meal = np.random.choice([True, False])
    
    has_soup = np.random.choice([True, False], p=[0.6, 0.4])
    has_salad = np.random.choice([True, False], p=[0.75, 0.25])

    meal_categories = [MealRole.SINGLE_MEAL] if is_single_meal else [MealRole.MAIN_COURSE, MealRole.SIDE_DISH]

    if has_soup:
        meal_categories.insert(0, MealRole.SOUP)
    if has_salad:
        meal_categories.append(MealRole.SALAD)

    return meal_categories

def _get_candidates(df, meal_type, user_profile, selected_recipe_names):
    """Filters candidate recipes based on meal type, diet, and previously selected recipes."""
    candidates = df[df['meal_role'] == meal_type].copy()
    
    if user_profile.get('diet') == 'vegan' and 'is_vegetarian' in candidates.columns:
        filtered_candidates = candidates[candidates['is_vegetarian'] == 1]
    else:
        filtered_candidates = candidates
        
    filtered_candidates = filtered_candidates[~filtered_candidates['recipe_name'].isin(selected_recipe_names)]
    
    if filtered_candidates.empty:
         candidates = candidates[~candidates['recipe_name'].isin(selected_recipe_names)]
         return candidates
         
    return filtered_candidates

def _calculate_recipe_score(row, remaining_budget, remaining_protein, remaining_calories, remaining_total_dishes, user_profile, past_clusters, weights, penalties, rewards, constraints):
    """Calculates fitness score of a candidate recipe."""
    price = row.get('price_try', 1)
    protein = row.get('protein_g', 1)
    calories = row.get('calories_kcal', 1)

    max_budget = max(1, remaining_budget)
    max_dishes = max(1, remaining_total_dishes)
    max_protein = max(1, protein)
    max_calories = max(1, calories)

    if price > (remaining_budget + constraints['budget_flexibility']):
        budget_suitability = penalties['budget_exceeded']
    else:
        budget_suitability = 1 - (price / max_budget)

    target_protein_threshold = remaining_protein / max_dishes
    protein_diff = abs(target_protein_threshold - protein)
    protein_suitability = 1 - (protein_diff / max_protein)

    target_calorie_threshold = remaining_calories / max_dishes
    calorie_diff = abs(target_calorie_threshold - calories)
    calorie_suitability = 1 - (calorie_diff / max_calories)

    profile_score = 0
    if user_profile.get('diet') == 'diabetic':
        carb_fiber = row.get('carb_fiber_ratio', 5)
        profile_score -= (carb_fiber * penalties['diabetic_carb_fiber'])
        if row.get('is_diabetic_friendly', 0) == 1:
            profile_score += rewards['diabetic_friendly']

    economy_score = row.get('protein_price_ratio', 0) * weights['economy_multiplier']

    target_score = (
        (budget_suitability * weights['budget']) + 
        (protein_suitability * weights['protein']) + 
        (calorie_suitability * weights['calorie']) + 
        profile_score + 
        economy_score
    )

    similarity_penalty = penalties['similarity'] if row.get('cluster_id') in past_clusters[-10:] else 0

    alpha = weights['alpha']
    final_score = (alpha * target_score) - ((1 - alpha) * similarity_penalty)
    final_score += np.random.uniform(-0.15, 0.15)
    
    return final_score

def _select_best_recipe(candidates, remaining_budget, remaining_protein, remaining_calories, remaining_total_dishes, user_profile, past_clusters, weights, penalties, rewards, constraints):
    """Scores candidate recipes and randomly selects one from the top N."""
    scores = [
        _calculate_recipe_score(row, remaining_budget, remaining_protein, remaining_calories, remaining_total_dishes, user_profile, past_clusters, weights, penalties, rewards, constraints)
        for _, row in candidates.iterrows()
    ]
        
    candidates['score'] = scores
    top_n = min(3, len(candidates))
    selected_recipe = candidates.sort_values(by='score', ascending=False).head(top_n).sample(1).iloc[0]
    return selected_recipe

def generate_weekly_menu(df, daily_target_budget, daily_target_protein, daily_target_calories, user_profile, custom_config=None):
    """Generates a personalized weekly menu respecting target nutritional and budget constraints."""
    weights, penalties, rewards, constraints = _get_config(custom_config)

    past_clusters = []
    selected_recipe_names = []
    
    days_of_week = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    meals_of_day = ['Lunch', 'Dinner']

    weekly_menu = {}

    for day in days_of_week:
        remaining_budget = daily_target_budget
        remaining_protein = daily_target_protein
        remaining_calories = daily_target_calories
        
        meals_categories = {meal: _generate_meal_structure() for meal in meals_of_day}
        remaining_total_dishes = sum(len(categories) for categories in meals_categories.values())

        day_menu = {}

        for meal in meals_of_day:
            day_menu[meal] = []
            
            for meal_type in meals_categories[meal]:
                candidates = _get_candidates(df, meal_type, user_profile, selected_recipe_names)

                if candidates.empty:
                    remaining_total_dishes -= 1
                    continue

                selected_recipe = _select_best_recipe(
                    candidates, remaining_budget, remaining_protein, remaining_calories,
                    remaining_total_dishes, user_profile, past_clusters,
                    weights, penalties, rewards, constraints
                )

                selected_recipe_names.append(selected_recipe['recipe_name'])
                past_clusters.append(selected_recipe.get('cluster_id', 0))

                sec_price = selected_recipe.get('price_try', 0)
                sec_protein = selected_recipe.get('protein_g', 0)
                sec_calories = selected_recipe.get('calories_kcal', 0)

                remaining_budget -= sec_price
                remaining_protein -= sec_protein
                remaining_calories -= sec_calories
                remaining_total_dishes -= 1

                day_menu[meal].append({
                    'meal_type': meal_type,
                    'recipe_name': selected_recipe['recipe_name'],
                    'price': sec_price,
                    'protein': sec_protein,
                    'calories': sec_calories,
                    'cluster_id': selected_recipe.get('cluster_id', '-')
                })
        
        weekly_menu[day] = {
            'menu': day_menu,
            'remaining_budget': remaining_budget,
            'remaining_protein': remaining_protein,
            'remaining_calories': remaining_calories
        }

    return weekly_menu
