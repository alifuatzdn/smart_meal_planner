import pandas as pd
import numpy as np
import re

# Standart ölçü birimlerinin yaklaşık gram/mililitre karşılıkları
OLCU_SAYISAL = {
    "yarım": 0.5,
    "çeyrek": 0.25,
    "bir buçuk": 1.5,
    "iki buçuk": 2.5
}

BIRIM_CEVRIM = {
    "su bardağı": 200,
    "çay bardağı": 100,
    "kahve fincanı": 70,
    "çorba kaşığı": 15,   # BUG FIX: "çorba kaşığı" eklendi (yemek kaşığı ile aynı)
    "yemek kaşığı": 15,
    "tatlı kaşığı": 5,
    "çay kaşığı": 2.5,
    "litre": 1000,
    "lt": 1000,
    "kg": 1000,
    "kilo": 1000,
    "gram": 1,
    "gr": 1,
    "g": 1,
    "ml": 1,
    "adet": 1,
    "tane": 1,
    "paket": 1,
    "diş": 5,      # BUG FIX: 1 diş sarımsak ~5g (önceki 3g biraz düşüktü)
    "demet": 1,
    "tutam": 2,
    "damla": 0.05,
    "dilim": 20
}

STOP_WORDS = [
    "haşlanmış", "rendelenmiş", "sıcak", "soğuk", "ılık", "tepeleme", "silme",
    "doğranmış", "kıyılmış", "iri", "ufak", "küp", "orta boy", "küçük boy", "büyük boy",
    "kadar", "yakın", "isteğe bağlı", "taze", "kuru", "hazır", "közlenmiş",
    "ezilmiş", "rendelenmiş", "dövülmüş", "kabuklu", "kabuğu soyulmuş"
]

# BUG FIX: Eksik mappingler eklendi (zeytinyağı, domates, kıyma, biber vb.)
SOZLUK = {
    # Yumurta
    "yumurta sarısı": "Yumurta 30'lu",
    "yumurta akı": "Yumurta 30'lu",
    "yumurta": "Yumurta 30'lu",

    # Yağlar
    "sıvı yağ": "Ayçiçek Yağı",
    "sıvıyağ": "Ayçiçek Yağı",
    "çiçek yağı": "Ayçiçek Yağı",
    "ayçiçek yağı": "Ayçiçek Yağı",
    "zeytinyağı": "Riviera Zeytinyağı",   # BUG FIX: eklendi
    "zeytinyağ": "Riviera Zeytinyağı",    # BUG FIX: eklendi
    "zeytin yağı": "Riviera Zeytinyağı",  # BUG FIX: eklendi
    "tereyağ": "Tereyağı",
    "tereyağı": "Tereyağı",
    "margarin": "Tereyağı",               # BUG FIX: eklendi, tereyağı ile eşle

    # Sebzeler
    "kuru soğan": "Kuru Soğan",
    "soğan": "Kuru Soğan",
    "sarımsak": "İPTAL",                  # Migros'ta sarımsak yok -> atla
    "domates": "Salkım Domates",          # BUG FIX: eklendi
    "domates rendesi": "Salkım Domates",  # BUG FIX: eklendi
    "yeşil biber": "Yeşil Sivri Biber",   # BUG FIX: eklendi
    "sivri biber": "Yeşil Sivri Biber",   # BUG FIX: eklendi
    "kapya biber": "Kırmızı Kapya Biber", # BUG FIX: eklendi
    "kırmızı biber": "Kırmızı Kapya Biber", # BUG FIX: eklendi
    "dolmalık biber": "Dolmalık Biber",   # BUG FIX: eklendi
    "biber": "Yeşil Sivri Biber",         # BUG FIX: eklendi (genel biber)
    "havuç": "Havuç",
    "patates": "Patates",
    "brokoli": "Brokoli",
    "mantar": "Kültür Mantarı",
    "kabak": "Kabak",                     # BUG FIX: eklendi (migros'ta var)
    "limon": "Limon",
    "limon suyu": "Limon",
    "ıspanak": "İspanak",                 # BUG FIX: eklendi

    # BUG FIX: Migros'ta "1 Demet" ile satılan otlar - adet olarak sayılınca
    # fiyat patlıyor (22 adet maydanoz = 22 demet gibi). Bunları İPTAL et.
    "maydanoz": "İPTAL",
    "dereotu": "İPTAL",
    "fesleğen": "İPTAL",
    "roka": "İPTAL",
    "yeşil soğan": "İPTAL",  # BUG FIX: kuru soğana eşlenmemeli
    "taze soğan": "İPTAL",   # BUG FIX: aynı sorun
    "arpacık soğan": "İPTAL", # BUG FIX: adet başı gram tahmini zor

    # BUG FIX: Mısır eşleştirme - tariflerde "mısır" = konserve/hazır mısır tane,
    # Migros'ta "Mısır" = koçan mısır (adet, 52.9 TL/adet). Gram bazlı kullanım için
    # "Haşlanmış Mısır Konservesi"ne (425g, 115.5 TL) eşlemek daha doğru.
    # "su bardağı mısır", "kutu mısır", "haşlanmış mısır" hepsi aynı şey.
    "haşlanmış mısır": "Haşlanmış Mısır Konservesi",
    "kutu mısır": "Haşlanmış Mısır Konservesi",
    "konserve mısır": "Haşlanmış Mısır Konservesi",
    "tane mısır": "Haşlanmış Mısır Konservesi",
    "mısır": "Haşlanmış Mısır Konservesi",   # BUG FIX: genel "mısır" -> konserve (gram bazlı)
    "mısır unu": "İPTAL",    # Migros'ta mısır unu yok -> atla
    "mısır nişastası": "İPTAL",  # Migros'ta yok -> atla

    # Baharatlar
    "tuz": "Sofra Tuzu",
    "karabiber": "Karabiber",
    "toz kırmızı biber": "Tatlı Toz Biber",
    "kırmızı toz biber": "Tatlı Toz Biber",
    "toz biber": "Tatlı Toz Biber",
    "pul biber": "Pul Biber",
    "pulbiber": "Pul Biber",
    "isot": "Pul Biber",                  # BUG FIX: isot ~ pul biber
    "nane": "Kuru Nane",
    "kuru nane": "Kuru Nane",
    "taze nane": "Taze Nane",
    "kekik": "İPTAL",                     # Migros'ta standart kekik yok -> atla

    # Salçalar
    "biber salçası": "Biber Salçası",
    "domates salçası": "Domates Salçası",
    "salça": "Domates Salçası",

    # Tahıllar
    "un": "Buğday Unu",
    "galeta unu": "Galeta Unu",           # BUG FIX: eklendi
    "şeker": "Toz Şeker",
    "toz şeker": "Toz Şeker",
    "pirinç": "Osmancık Pirinç",
    "baldo pirinç": "Baldo Pirinç",
    "kırmızı mercimek": "Kırmızı Mercimek",
    "yeşil mercimek": "Yeşil Mercimek",
    "tel şehriye": "Tel Şehriye",
    "arpa şehriye": "Arpa Şehriye",
    "bulgur": "Pilavlık Bulgur",
    "nohut": "Koçbaşı Nohut",            # BUG FIX: eklendi
    "makarna": "Kalem Makarna",           # BUG FIX: eklendi
    "erişte": "Kalem Makarna",
    "spagetti": "Spagetti Makarna",       # BUG FIX: eklendi
    "penne": "Kalem Makarna",             # BUG FIX: eklendi (Migros'ta penne yok, kalem = penne)

    # Süt ürünleri
    "süt": "Yarım Yağlı Süt",
    "yoğurt": "Tam Yağlı Yoğurt",
    "süt kreması": "Yağlı Krema",
    "krema": "Yağlı Krema",
    "nişasta": "İPTAL",                   # Migros'ta yok -> atla

    # Et
    "tavuk göğsü": "Piliç Göğüs Fileto",
    "tavuk but": "Piliç But",             # BUG FIX: eklendi
    "tavuk": "Bütün Piliç",
    "kıyma": "Dana Kıyma",               # BUG FIX: eklendi
    "dana kıyma": "Dana Kıyma",          # BUG FIX: eklendi
    "kuşbaşı": "Dana Kuşbaşı",           # BUG FIX: eklendi
    "biftek": "Dana Biftek",              # BUG FIX: eklendi (pahalı et, doğru fiyat)
    "dana biftek": "Dana Biftek",         # BUG FIX: eklendi

    # İptal (fiyatlandırılamaz)
    "kemik suyu": "İPTAL",
    "tavuk suyu": "İPTAL",
    "et suyu": "İPTAL",
    "su": "İPTAL",
    "defne yaprağı": "İPTAL",
    "sirke": "İPTAL",
}


MIGROS_ADET_GRAMAJLARI = {
    'Beyaz Lahana': 2000,
    'Kırmızı Lahana': 1000,
    'Karnabahar': 1500,
    'Enginar': 250,
    'Kıvırcık Marul': 500,
    'Göbek Marul': 500,
    'Yaprak Marul': 400,
}

# BUG FIX: Birim sütunu NaN veya bozuk olan ürünler için manuel birim tanımları
# (Migros CSV'de Birim sütunu boş kalan ürünlerin doğru birimi buraya yazılır)
MIGROS_MANUEL_BIRIM = {
    "Yumurta 30'lu":              "30 Adet",   # 30'lu paket -> 169.9/30 = ~5.66 TL/adet
    "Haşlanmış Mısır Konservesi": "425 G",     # standart konserve gramajı
    "Yufka 10'lu":                "10 Adet",   # 10'lu paket -> 179/10 = ~17.9 TL/adet
    "Mısır":                      "1 Adet",    # koçan mısır, adet olarak satılıyor
}

def parse_migros_prices(df_migros):
    """Migros tablosundan birim başına (1g, 1ml, 1adet) fiyatı hesaplar."""
    price_dict = {}

    for _, row in df_migros.iterrows():
        name = row['İsim']
        price = float(str(row['Migros Fiyatı']).replace(',', '.'))
        birim_str = str(row['Birim']).lower().strip()

        # BUG FIX: Birim NaN veya bozuksa manuel tablodan al
        if not re.search(r'[a-z]', birim_str) or birim_str in ['nan', '', ' a']:
            if name in MIGROS_MANUEL_BIRIM:
                birim_str = MIGROS_MANUEL_BIRIM[name].lower()
                print(f"  [BİRİM DÜZELTMESİ] '{name}': NaN/bozuk birim -> '{birim_str}' olarak kullanıldı")
            else:
                print(f"  [UYARI] '{name}': Birim sütunu bozuk ('{row['Birim']}'), ürün atlandı")
                continue  # fiyat hesaplanamaz, price_dict'e ekleme

        match = re.match(r"([\d\.,]+)\s*([a-z]+)", birim_str)
        if match:
            miktar = float(match.group(1).replace(',', '.'))
            birim_tipi = match.group(2)

            if birim_tipi in ['kg', 'l', 'lt', 'litre']:
                birim_fiyat = price / (miktar * 1000)
            elif birim_tipi in ['g', 'gr', 'ml', 'gram']:
                birim_fiyat = price / miktar
            elif birim_tipi in ['adet', 'demet', 'paket']:
                if name in MIGROS_ADET_GRAMAJLARI:
                    birim_fiyat = price / (miktar * MIGROS_ADET_GRAMAJLARI[name])
                else:
                    birim_fiyat = price / miktar
            else:
                birim_fiyat = price

            price_dict[name] = birim_fiyat
        else:
            print(f"  [UYARI] '{name}': Birim parse edilemedi ('{birim_str}'), ürün atlandı")

    return price_dict


URUN_GRAM_KARSILIGI = {
    "soğan": 100,
    "kuru soğan": 100,
    "patates": 150,
    "domates": 150,
    "salkım domates": 150,
    "tarla domates": 150,
    "havuç": 100,
    "limon": 100,
    "elma": 150,
    "yumurta": 1,       # Adet
    "yumurta sarısı": 1,
    "yumurta akı": 1,
    "sarımsak": 5,
    "tavuk but": 250,
    "tavuk baget": 150,
    "tavuk kanat": 50,
    "tavuk göğsü": 300,
    "tavuk": 500,
    "kabak": 200,       # BUG FIX: eklendi
    "biber": 100,       # BUG FIX: eklendi
    "yeşil biber": 100,
    "kırmızı biber": 150,
}

def clean_and_parse_ingredient(text):
    """
    Doğal dildeki malzemeden miktarı ve malzeme adını çıkarır.
    """
    if pd.isna(text) or str(text).strip() == "":
        return None, None

    text = str(text).lower().strip()

    # Parantez içlerini sil
    text = re.sub(r"\(.*?\)", "", text).strip()

    # "veya", "ya da", "+" ile iki seçenek varsa ilkini al
    text = re.split(r" veya | ya da |\+", text)[0].strip()

    # BUG FIX: "2-3" gibi aralıkları ortalamayla çevir -> "2.5"
    # Başındaki "N-M" pattern -> (N+M)/2
    range_match = re.match(r"^(\d+)-(\d+)\s+", text)
    if range_match:
        low = float(range_match.group(1))
        high = float(range_match.group(2))
        avg = (low + high) / 2
        text = f"{avg} " + text[range_match.end():]

    # BUG FIX: Başında kalan tire/tire-sayı kalıntılarını temizle
    text = re.sub(r"^-[\d\s]*", "", text).strip()

    # Rakam ve kelimeler bitişik gelirse ayır "200gr tavuk" -> "200 gr tavuk"
    text = re.sub(r"(?<=\d)(?=[a-z])", " ", text)

    amount = 1.0
    base_unit_multiplier = 1.0

    # "yarım", "çeyrek" gibi metinsel sayıları çevir
    for word, val in OLCU_SAYISAL.items():
        if text.startswith(word):
            amount = val
            text = text.replace(word, "", 1).strip()
            break

    # İlk baştaki sayıları al
    match_num = re.match(r"^([\d\.,]+)", text)
    if match_num:
        amount_str = match_num.group(1).replace(',', '.')
        try:
            amount = float(amount_str)
        except ValueError:
            amount = 1.0
        text = text[match_num.end():].strip()

    # BUG FIX: Sayıdan sonra kalan tire/tire-sayı kalıntılarını temizle ("2-3" -> "2" + "-3 biber")
    text = re.sub(r"^-[\d\.]+\s*", "", text).strip()

    # Ölçü birimini saptayıp çarpana ekle
    found_unit = ""
    for unit, mult in BIRIM_CEVRIM.items():
        if text.startswith(unit):
            base_unit_multiplier = mult
            found_unit = unit
            text = text.replace(unit, "", 1).strip()
            break

    # Stop words temizle
    for stop_word in STOP_WORDS:
        text = re.sub(r"\b" + stop_word + r"\b", "", text).strip()

    product_name = text.strip()

    # Adet hesabı gereken sebze/meyveler
    if found_unit in ["adet", "tane"] or (base_unit_multiplier == 1 and found_unit == ""):
        for u_name, u_gram in sorted(URUN_GRAM_KARSILIGI.items(), key=lambda x: len(x[0]), reverse=True):
            if u_name in product_name:
                base_unit_multiplier = u_gram
                break

    final_amount = amount * base_unit_multiplier

    if product_name == "":
        return None, None

    return final_amount, product_name


def map_to_migros(product_name, migros_names):
    """
    Malzeme ismini Migros verisi ile eşler.
    """
    if product_name in SOZLUK:
        return SOZLUK[product_name]

    for key in sorted(SOZLUK.keys(), key=len, reverse=True):
        if key in product_name:
            return SOZLUK[key]

    # Migros isimlerinde partial match
    for k in migros_names:
        if k.lower() in product_name:
            return k

    return None


def main():
    import os
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    migros_data_path = os.path.join(BASE_DIR, 'data', 'migros_price_data.csv')
    df_migros = pd.read_csv(migros_data_path, sep=';')
    price_dict = parse_migros_prices(df_migros)
    migros_names = df_migros['İsim'].unique()

    recipes_data_path = os.path.join(BASE_DIR, 'data', 'recipes.csv')
    df_recipes = pd.read_csv(recipes_data_path)

    toplam_fiyat_liste = []

    # DEBUG: Eşleşmeyen malzemeleri takip et
    unmatched_log = {}

    material_columns = [col for col in df_recipes.columns if "ingredient" in col]

    for idx, row in df_recipes.iterrows():
        total_cost = 0.0
        for col in material_columns:
            val = str(row[col])

            if val.strip().lower() == "nan":
                continue

            sub_items = [v.strip() for v in re.split(r",\s+|\.\s+", val) if v.strip()]

            for item in sub_items:
                amount, p_name = clean_and_parse_ingredient(item)

                if p_name and amount is not None:
                    migros_name = map_to_migros(p_name, migros_names)

                    if migros_name == "İPTAL":
                        continue

                    if migros_name and migros_name in price_dict:
                        total_cost += amount * price_dict[migros_name]
                    elif migros_name is None:
                        unmatched_log[p_name] = unmatched_log.get(p_name, 0) + 1

        toplam_fiyat_liste.append(round(total_cost, 2))

    df_recipes['price_try'] = toplam_fiyat_liste
    df_recipes = df_recipes.drop(columns=material_columns)

    output_path = os.path.join(BASE_DIR, 'data', 'recipes_processed.csv')
    df_recipes.to_csv(output_path, index=False, sep=',')
    print(f"Veri dönüştürme tamamlandı. {output_path} kaydedildi.")

    # Hâlâ eşleşmeyen malzemeleri yazdır
    if unmatched_log:
        print(f"\n[UYARI] {len(unmatched_log)} malzeme hâlâ eşleşmedi (fiyata katılmadı):")
        for name, count in sorted(unmatched_log.items(), key=lambda x: x[1], reverse=True)[:20]:
            safe_name = str(name).encode('ascii', 'replace').decode('ascii')
            print(f"  {count:3d}x  '{safe_name}'")


if __name__ == "__main__":
    main()
