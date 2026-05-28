import pandas as pd
from sklearn.preprocessing import MinMaxScaler
from pathlib import Path

# Define relative paths based on script location so it runs from anywhere
BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / 'data'

# 1. Load Data
df = pd.read_csv(DATA_DIR / 'recipes_processed.csv')

# --- OUTLIER FILTERING ---
# Fiyatı çok saçma olanları (5 TL altı ve 150 TL üstü) ve kalorisi anlamsız yüksek/düşük olanları filtreliyoruz.
df = df[(df['price_try'] > 20) & (df['price_try'] < 300)]
df = df[(df['calories_kcal'] > 50) & (df['calories_kcal'] < 800)]
df = df[(df['protein_g'] > 0) & (df['protein_g'] < 65)]
# Filtreleme sonrası indexleri sıfırlayalım (menü eşleştirmelerinde kayma olmasın diye)
df = df.reset_index(drop=True)
# Veriyi tekrar kaydediyoruz ki, clustering sonrası menü üretimi (menu_generator) de bu temizlenmiş veriyi baz alsın
df.to_csv(DATA_DIR / 'recipes_processed.csv', index=False)

# 2. One-Hot Encoding
categorical_cols = ['meal_role', 'main_ingredient']
df_processed = pd.get_dummies(df, columns=categorical_cols)

# Prepare the matrix for training the model
cols_to_drop = ['recipe_name', 'recipe_link', 'is_vegetarian', 'is_diabetic_friendly']
X_train = df_processed.drop(columns=cols_to_drop)

# Impute missing values with 0
X_train = X_train.fillna(0)

# 3. Scaling
scaler = MinMaxScaler()
numerical_cols = ['calories_kcal', 'protein_g', 'carbohydrates_g', 'fat_g', 'fiber_g', 'sodium_mg', 'potassium_mg', 'iron_mg', 'vitamin_c_mg', 'cholesterol_mg', 'calcium_mg', 'vitamin_a_iu', 'price_try', 'protein_calorie_ratio', 'protein_price_ratio', 'carb_fiber_ratio']

X_train[numerical_cols] = scaler.fit_transform(X_train[numerical_cols])

# 4. Save to CSV directly in the data folder
out_path = DATA_DIR / 'processed_X_train.csv'
X_train.to_csv(out_path, index=False)
print(f'preprocessing.py completed. Data saved as {out_path}')
