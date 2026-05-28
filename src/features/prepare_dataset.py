import csv

from pathlib import Path

def parse_float(val):
    try:
        if not val:
            return 0.0
        return float(val.replace(',', '.'))

    except:
        return 0.0

def is_vegetarian(ingredients_text):
    text = ingredients_text.lower()
    non_veg_keywords = [
        'et', 'tavuk', 'kıyma', 'kuzu', 'dana', 'balık',
        'sucuk', 'sosis', 'pastırma', 'kavurma', 'karides',
        'somon', 'levrek', 'hamsi', 'ton', 'hindi'
    ]
    for word in non_veg_keywords:
        if word in text:
            return 0
    return 1

def is_diabetic_friendly(ingredients_text, carb, fiber):
    text = ingredients_text.lower()
    high_sugar_keywords = ['şeker', 'bal', 'pekmez', 'şurup', 'çikolata', 'lokum', 'reçel']
    for word in high_sugar_keywords:
        if word in text:
            return 0

    if carb > 45.0:
        return 0

    ratio = carb / (fiber + 0.1)
    if ratio > 15.0:
        return 0

    return 1

BASE_DIR = Path(__file__).resolve().parent.parent.parent
data_in = BASE_DIR / 'data' / 'recipes.csv'
data_out = BASE_DIR / 'data' / 'recipes_processed.csv'

# Dosya Excel ile açılıp kaydedildiğinde utf-8 formatı bozulup ANSI(windows-1254)'e dönebilir.
# Bu yüzden dosyayı okuyabilmek için otomatik Encoding (Karakter Kodlaması) tespiti yapıyoruz.
working_encoding = 'utf-8-sig'
for enc in ['utf-8-sig', 'windows-1254', 'cp1254', 'iso-8859-9', 'mac_turkish', 'utf-8']:
    try:
        with open(data_in, 'r', encoding=enc) as test_f:
            test_f.read()
        working_encoding = enc
        break
    except UnicodeDecodeError:
        pass

with open(data_in, 'r', encoding=working_encoding, errors='replace') as f_in, open(data_out, 'w', encoding='utf-8-sig', errors='replace', newline='') as f_out:
    reader = csv.DictReader(f_in)
    
    # We want to keep all columns except 'ingredient_' ones, plus our new ones
    base_headers = [h for h in reader.fieldnames if not (h and 'ingredient_' in h)]

    # Derived and newly added columns only
    new_cols = ['is_vegetarian', 'is_diabetic_friendly', 'protein_calorie_ratio', 'carb_fiber_ratio', 'protein_price_ratio']
    out_fieldnames = base_headers + new_cols
    
    writer = csv.DictWriter(f_out, fieldnames=out_fieldnames)
    writer.writeheader()
    
    for row in reader:
        # Keep all original data intact
        out_row = {h: row[h] for h in base_headers}
        
        # Compile all ingredients into a single text for analysis
        ingredients = []
        for key in row.keys():
            if key and 'ingredient_' in key and row[key].strip():
                ingredients.append(row[key].strip())
        ingredients_text = ' '.join(ingredients)
        
        # Parse relevant nutritional values for calculations
        calories = parse_float(row.get('calories_kcal', 0))
        protein = parse_float(row.get('protein_g', 0))
        carbs = parse_float(row.get('carbohydrates_g', 0))
        fat = parse_float(row.get('fat_g', 0))
        fiber = parse_float(row.get('fiber_g', 0))
        price = parse_float(row.get('price_try', 0))

        # Apply strict rules for vegetarian and diabetic friendly labels
        vegetarian = is_vegetarian(ingredients_text)
        diabetic_friendly = is_diabetic_friendly(ingredients_text, carbs, fiber)

        # Calculate derived ratios only
        protein_calorie_ratio = round((protein * 4) / calories, 4) if calories > 0 else 0
        carb_fiber_ratio = round(carbs / (fiber + 0.1), 4)
        protein_price_ratio = round(protein / price, 4) if price > 0 else 0

        # Update output row with new features only
        out_row.update({
            'is_vegetarian': vegetarian,
            'is_diabetic_friendly': diabetic_friendly,
            'protein_calorie_ratio': protein_calorie_ratio,
            'carb_fiber_ratio': carb_fiber_ratio,
            'protein_price_ratio': protein_price_ratio
        })
        
        writer.writerow(out_row)


print("Process completed! The new dataset has been saved as 'recipes_processed.csv' and 'recipes_processed.xlsx'.")
