# 🍽️ AI-Powered Weekly Menu Planner

A smart, Python and Streamlit-based application designed to generate optimized weekly meal plans. The algorithm dynamically selects recipes based on a user's budget constraints, nutritional targets (calories, protein), and specific dietary preferences (Standard, Vegan, Diabetic).

## 🚀 Features

- **Nutritional Targeting**: Calculates and balances daily protein and calorie intakes.
- **Budget Optimization**: Ensures the generated daily menu stays within a set budget limit.
- **Dietary Constraints**: Supports specialized diets including Vegan (filters vegetarian/vegan recipes) and Diabetic (minimizes carb-to-fiber ratio and favors diabetic-friendly recipes).
- **Variety Enforcement**: Uses clustering history to penalize repetitive meal structures, ensuring you don't eat similar meals day after day.
- **Interactive UI**: Clean and intuitive Streamlit dashboard to tweak parameters and preview generating menus interactively.

## 📁 Project Structure

```text
.
├── data/
│   ├── clustered_data.csv       # Preprocessed and clustered recipes dataset
│   ├── processed_X_train.csv    # Transformed data mapped for ML clustering
│   ├── recipes_processed.csv    # Intermediate dataset
│   └── recipes.csv              # Raw scraped recipes
├── src/
│   ├── app.py                   # Main Streamlit application and UI
│   ├── config.py                # Hyperparameters and algorithm weights
│   ├── features/
│   │   ├── menu_generator.py    # Core generation algorithm
│   │   ├── prepare_dataset.py   # Dataset preparation scripts
│   │   └── preprocessing.py     # Data cleaning scripts
│   ├── models/
│   │   ├── clustering.py        # ML clustering models for recipe variety
│   │   └── hyperparameter_tuning.py # Optuna/Grid search scripts
│   └── scraper/
│       └── recipe_scrapper.py   # Web scraper for recipe data
├── .gitignore                   # Ignored files and folders
└── README.md                    # Project documentation
```

## 🛠️ Installation & Setup

1. **Clone the repository / Open the folder**
2. **Create and Activate a Virtual Environment**
   ```bash
   python -m venv .venv
   ```
   # For Windows
   ```bash
   .\.venv\Scripts\activate
   ```
   # For Mac/Linux
   ```bash
   source .venv/bin/activate
   ```
4. **Install Dependencies**
   ```bash
   pip install pandas numpy streamlit scikit-learn matplotlib seaborn beautifulsoup4 requests
   ```
5. **Prepare the Data**
   *(Ensure you run the scraper, preprocessor, and clustering algorithms first to generate clustered_data.csv and processed_X_train.csv)*
   ```bash
   python src/features/preprocessing.py
   python src/models/clustering.py
   ```

## 💻 Usage

To launch the Streamlit interface, run the following command from the root directory:

```bash
streamlit run src/app.py
```

The application will open in your default web browser where you can set your target limits and generate the weekly plans.

## 🧠 How the Algorithm Works

The menu_generator.py uses a weighted scoring algorithm to rank candidate recipes based on target nutritional gap closures, price, diet types and clustering distance for varied meals. You can tune these weights in src/config.py!
