"""
Algorithm Hyperparameters and Configurations

This module centralizes all tunable parameters for the menu generation algorithm.
Adjust these values to change the AI's behavior, priorities, and strictness.
"""

WEIGHTS = {
    # Controls the trade-off between target matching and menu variety.
    # Range: [0.0 - 1.0]. 
    # Closer to 1.0 -> Prioritizes hitting budget/nutrition targets perfectly. 
    # Closer to 0.0 -> Prioritizes variety (choosing recipes from different clusters).
    'alpha': 0.771,
    
    # Importance of matching the daily budget.
    # Range: [0.0 - 1.0]. Determines the weight of budget suitability in the final score.
    'budget': 0.492,
    
    # Importance of matching the daily protein target.
    # Range: [0.0 - 1.0]. Determines the weight of protein suitability in the final score.
    'protein': 0.813,
    
    # Importance of matching the daily calorie target.
    # Range: [0.0 - 1.0]. Determines the weight of calorie suitability in the final score.
    'calorie': 0.407,
    
    # Impact of the protein-to-price ratio on the final score.
    # Range: [0.0 - 1.0]. Higher values favor cost-effective high-protein meals.
    'economy_multiplier': 0.119,
}

PENALTIES = {
    # Flat score deduction applied when a recipe's price exceeds the remaining budget + flexibility.
    # Range: Negative float (e.g., -1.0 to -10.0). Higher absolute value means stricter budget enforcement.
    'budget_exceeded': -7.896,
    
    # Penalty applied when a recipe belongs to a cluster recently used (reduces repetitiveness).
    # Range: Positive float (e.g., 0.5 to 3.0). Higher values force the algorithm to select from different clusters.
    'similarity': 0.954,
    
    # Multiplier applied to the carbohydrate/fiber ratio to penalize high-carb, low-fiber meals for diabetic profiles.
    # Range: [0.0 - 1.0]. Higher values heavily penalize meals unsuitable for diabetics.
    'diabetic_carb_fiber': 0.05,
}

REWARDS = {
    # Bonus score awarded to recipes specifically labeled as "diabetic friendly" (only active for diabetic users).
    # Range: Positive float (e.g., 0.1 to 2.0).
    'diabetic_friendly': 0.5,
}

CONSTRAINTS = {
    # Maximum acceptable over-budget amount (in TL) for a single recipe before the 'budget_exceeded' penalty applies.
    # Range: Positive integer/float (e.g., 0 to 100). Higher values allow slightly more expensive premium meals despite tight budgets.
    'budget_flexibility': 77,
}
