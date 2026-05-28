import requests
from bs4 import BeautifulSoup
import csv
import time
from pathlib import Path
import re

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
}

CSV_QUOTE_ALL = csv.QUOTE_ALL
MAX_FILE_OPEN_ATTEMPTS = 5
FILE_OPEN_WAIT_SEC = 2


def safe_file_open(path, mode):
    for attempt in range(1, MAX_FILE_OPEN_ATTEMPTS + 1):
        try:
            return open(path, mode=mode, encoding='utf-8-sig', newline='')
        except PermissionError:
            if attempt == MAX_FILE_OPEN_ATTEMPTS:
                raise
            print(
                f"[WARNING] File '{path}' is open in another program (like Excel). "
                f"Retrying in {FILE_OPEN_WAIT_SEC} seconds ({attempt}/{MAX_FILE_OPEN_ATTEMPTS})."
            )
            time.sleep(FILE_OPEN_WAIT_SEC)
    raise PermissionError(path)


def clean_recipe_name(value):
    original = (value or "").strip()
    if not original:
        return original

    cleaned = re.sub(r"\([^)]*\)", " ", original)
    cleaned = re.sub(
        r"\b(?:yap[ıi]l[ıi][şs][ıi]?|tarif[ıi]?|video(?:lu|su)?|video['’]su|nas[ıi]l\s+yap[ıi]l[ıi]r\b\??)",
        " ",
        cleaned,
        flags=re.IGNORECASE,
    )

    cleaned = re.sub(r"\s+", " ", cleaned)
    cleaned = cleaned.strip(" -–—:|,.;?!")
    cleaned = re.sub(r"\s+", " ", cleaned).strip()

    return cleaned if cleaned else original

pages_to_scrape = 20
meal_type_fixed = 'Salata/Meze'
collected_links = []

print("STAGE 1: Collecting recipe links from category pages...")

for page_no in range(1, pages_to_scrape + 1):

    if page_no == 1:
        category_url = "https://www.nefisyemektarifleri.com/kategori/tarifler/salata-meze-kanepe/meze-tarifleri/?nytorderby=archive-populer"
    else:
        category_url = f"https://www.nefisyemektarifleri.com/kategori/tarifler/salata-meze-kanepe/meze-tarifleri/page/{page_no}/?nytorderby=archive-populer"

    print(f"Scanning [Page {page_no}]: {category_url}")

    try:
        response = requests.get(category_url, headers=headers)
        soup = BeautifulSoup(response.content, 'html.parser')

        figure_tags = soup.find_all('figure', class_='recipe-image')

        for figure in figure_tags:
            a_tag = figure.find('a')
            if a_tag and a_tag.has_attr('href'):
                href_value = a_tag.get('href')
                if isinstance(href_value, list):
                    if len(href_value) == 0:
                        continue
                    href_value = href_value[0]
                if not href_value:
                    continue
                link = str(href_value)
                if not link.startswith('http'):
                    link = "https://www.nefisyemektarifleri.com" + link
                if link not in collected_links:
                    collected_links.append(link)

    except Exception as e:
        print(f"Error ({category_url}): {e}")

    time.sleep(2)

print("\nGreat! A total of {len(collected_links)} recipe links were found.\n")

# ---------------------------------------------------------

print("STAGE 2: Fetching data from the found links and writing to columns...")

BASE_DIR = Path(__file__).resolve().parent.parent.parent
csv_file = BASE_DIR / 'data' / 'recipes.csv'
nutrition_headers = [
    'calories_kcal', 'carbohydrates_g', 'protein_g', 'fat_g',
    'fiber_g', 'cholesterol_mg', 'sodium_mg', 'potassium_mg',
    'calcium_mg', 'vitamin_a_iu', 'vitamin_c_mg', 'iron_mg'
]
headers_list = ['recipe_name', 'recipe_link', 'meal_role'] + nutrition_headers + [f'ingredient_{i}' for i in range(1, 31)]

existing_links = set()
file_exists = csv_file.exists()
file_is_empty = (not file_exists) or csv_file.stat().st_size == 0

if not file_is_empty:
    try:
        with safe_file_open(csv_file, mode='r') as existing_file:
            csv_reader = csv.reader(existing_file)
            for row_no, row_data in enumerate(csv_reader):
                if len(row_data) < 2:
                    continue
                # Do not include the header row in the link set
                if row_no == 0 and row_data[1].strip() == 'recipe_link':
                    continue
                existing_links.add(row_data[1].strip())
    except PermissionError:
        raise SystemExit(
            f"ERROR: Cannot access '{csv_file}'. Please close the file in Excel and try again."
        )

print(f"Found {len(existing_links)} unique links in the existing CSV.")

added_count = 0
skipped_count = 0
missing_kcal_skipped_count = 0

try:
    file_connection = safe_file_open(csv_file, mode='a')
except PermissionError:
    raise SystemExit(
        f"ERROR: Cannot write to '{csv_file}'. Please close the file in Excel and try again."
    )

with file_connection as file:
    csv_writer = csv.writer(
        file,
        delimiter=',',
        quoting=CSV_QUOTE_ALL,   # Quote all cells to reduce shift issues in Excel
        lineterminator='\n'
    )
    # Write header if file is new/empty
    if file_is_empty:
        csv_writer.writerow(headers_list)

    for link in collected_links:
        if link in existing_links:
            skipped_count += 1
            print(f"[SKIPPED] Already saved: {link}")
            continue

        print(f"Fetching data -> {link}")

        try:
            response = requests.get(link, headers=headers)
            soup = BeautifulSoup(response.content, 'html.parser')

            title_tag = soup.find('h1')
            recipe_name = title_tag.text.strip() if title_tag else "Title Not Found"
            recipe_name = clean_recipe_name(recipe_name)

            # --- NUTRITION VALUES EXTRACTION ---
            nutrition_dict = {}

            # Calories
            calories_div = soup.find('div', class_='nutrition-circle-value calories')
            if calories_div:
                nutrition_dict['Kalori'] = calories_div.text.strip()

            if not nutrition_dict.get('Kalori', '').strip():
                missing_kcal_skipped_count += 1
                print(f"[SKIPPED] No kcal info: {link}")
                continue

            nutrition_table = soup.find('table', class_='nutrition-table')
            if nutrition_table:
                for tr in nutrition_table.find_all('tr'):
                    tds = tr.find_all('td')
                    if len(tds) >= 2:
                        name = tds[0].text.strip()  # Karbonhidrat(g)
                        value = tds[1].text.strip() # 17.5
                        nutrition_dict[name] = value

            ordered_nutritions = [
                nutrition_dict.get('Kalori', ''),
                nutrition_dict.get('Karbonhidrat(g)', ''),
                nutrition_dict.get('Protein(g)', ''),
                nutrition_dict.get('Yağ(g)', ''),
                nutrition_dict.get('Lif(g)', ''),
                nutrition_dict.get('Kolesterol(mg)', ''),
                nutrition_dict.get('Sodyum(mg)', ''),
                nutrition_dict.get('Potasyum(mg)', ''),
                nutrition_dict.get('Kalsiyum(mg)', ''),
                nutrition_dict.get('Vitamin A(iu)', ''),
                nutrition_dict.get('Vitamin C(mg)', ''),
                nutrition_dict.get('Demir(mg)', nutrition_dict.get('Demir', ''))
            ]

            ingredients_list = []
            ul_tags = soup.find_all('ul', class_='recipe-materials')

            for ul in ul_tags:
                li_tags = ul.find_all('li', itemprop='recipeIngredient')
                for li in li_tags:
                    ingredient = " ".join(li.get_text(strip=True).split()).replace(',', '.')
                    ingredients_list.append(ingredient)

            if len(ingredients_list) == 0:
                ingredients_list.append("Ingredient Not Found")

            # --- WRITING TO CSV IN SEPARATE COLUMNS ---
            row_data_to_write = [recipe_name, link, meal_type_fixed] + ordered_nutritions + ingredients_list

            csv_writer.writerow(row_data_to_write)
            existing_links.add(link)
            added_count += 1

        except Exception as e:
            print(f"  [-] Error ({link}): {e}")

        time.sleep(2)

print(
    f"\nPROCESS COMPLETED! {added_count} new rows added, {skipped_count} duplicate records skipped, "
    f"{missing_kcal_skipped_count} records skipped due to missing kcal. "
    f"Open '{csv_file}' to see the data in separate columns.")
