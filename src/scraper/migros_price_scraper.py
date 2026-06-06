"""
Migros Fiyat Kazıyıcı ve CSV Oluşturucu (Birleştirilmiş Versiyon)
===================================================
pip install selenium pandas openpyxl
python migros_scraper_csv.py
"""

import time, re, csv
from datetime import datetime

import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

# ──────────────────────────────────────────────────────────────────────────────
# ÜRÜN VERİSİ
# ──────────────────────────────────────────────────────────────────────────────
data = [
    # ── Sebze ────────────────────────────────────────────────────────────────────
    {"Isim": "Mor Lahana 1 Kg",          "Kategori": "Sebze",               "Etiket_Fiyati": 45.0,   "Birim_Tipi": "kg"},
    {"Isim": "Kırmızı Pancar 1 Kg",      "Kategori": "Sebze",               "Etiket_Fiyati": 40.0,   "Birim_Tipi": "kg"},
    {"Isim": "Yaprak Marul 1 Adet",      "Kategori": "Sebze",               "Etiket_Fiyati": 25.0,   "Birim_Tipi": "adet"},
    {"Isim": "Taze Reyhan 1 Demet",      "Kategori": "Sebze",               "Etiket_Fiyati": 20.0,   "Birim_Tipi": "adet"},

    # ── Et ───────────────────────────────────────────────────────────────────────
    {"Isim": "Dana Eti 1 Kg",            "Kategori": "Et ve Tavuk",         "Etiket_Fiyati": 650.0,  "Birim_Tipi": "kg"},
    {"Isim": "Levrek Fileto 1 Kg",       "Kategori": "Et ve Tavuk",         "Etiket_Fiyati": 320.0,  "Birim_Tipi": "kg"},

    # ── Baharat ve Sos ───────────────────────────────────────────────────────────
    {"Isim": "Muskat 30 G",              "Kategori": "Baharat ve Sos",      "Etiket_Fiyati": 55.0,   "Birim_Tipi": "kg"},
    {"Isim": "Köri 50 G",                "Kategori": "Baharat ve Sos",      "Etiket_Fiyati": 60.0,   "Birim_Tipi": "kg"},
    {"Isim": "Köfte Baharatı 50 G",      "Kategori": "Baharat ve Sos",      "Etiket_Fiyati": 45.0,   "Birim_Tipi": "kg"},
    {"Isim": "Karbonat 200 G",           "Kategori": "Temel Gıda",          "Etiket_Fiyati": 25.0,   "Birim_Tipi": "kg"},
    {"Isim": "Beşamel Sos 400 G",        "Kategori": "Baharat ve Sos",      "Etiket_Fiyati": 55.0,   "Birim_Tipi": "kg"},

    # ── Bakliyat / Makarna ───────────────────────────────────────────────────────
    {"Isim": "Yüksük Makarna 500 G",     "Kategori": "Bakliyat",            "Etiket_Fiyati": 25.0,   "Birim_Tipi": "kg"},
    {"Isim": "Lazanya 500 G",            "Kategori": "Bakliyat",            "Etiket_Fiyati": 35.0,   "Birim_Tipi": "kg"},
    {"Isim": "Yıldız Şehriye 500 G",     "Kategori": "Bakliyat",            "Etiket_Fiyati": 30.0,   "Birim_Tipi": "kg"},
    {"Isim": "Kuskus 500 G",             "Kategori": "Bakliyat",            "Etiket_Fiyati": 45.0,   "Birim_Tipi": "kg"},
    {"Isim": "Konserve Mısır 285 G",     "Kategori": "Bakliyat",            "Etiket_Fiyati": 35.0,   "Birim_Tipi": "kg"},

    # ── Süt Ürünleri ─────────────────────────────────────────────────────────────
    {"Isim": "Parmesan Peyniri 150 G",   "Kategori": "Süt ve Süt Ürünleri", "Etiket_Fiyati": 280.0,  "Birim_Tipi": "kg"},

    # ── Diğer ────────────────────────────────────────────────────────────────────
    {"Isim": "Kornişon Turşu 720 G",     "Kategori": "Diğer",               "Etiket_Fiyati": 75.0,   "Birim_Tipi": "kg"},
    {"Isim": "Yufka 10'lu",              "Kategori": "Diğer",               "Etiket_Fiyati": 45.0,   "Birim_Tipi": "adet"},
    {"Isim": "Ekmek 350 G",              "Kategori": "Diğer",               "Etiket_Fiyati": 15.0,   "Birim_Tipi": "kg"},
    {"Isim": "Dolmalık Fıstık 100 G",    "Kategori": "Kuruyemiş",           "Etiket_Fiyati": 120.0,  "Birim_Tipi": "kg"},
    {"Isim": "Kuş Üzümü 100 G",          "Kategori": "Kuruyemiş",           "Etiket_Fiyati": 90.0,   "Birim_Tipi": "kg"},
]


# ──────────────────────────────────────────────────────────────────────────────
# YARDIMCI FONKSİYONLAR
# ──────────────────────────────────────────────────────────────────────────────

def str_to_float(metin: str) -> float | None:
    try:
        temiz = re.sub(r"[^\d,.]", "", metin.strip())
        temiz = temiz.replace(".", "").replace(",", ".")
        val = float(temiz)
        return val if 0.5 <= val <= 50000 else None
    except (ValueError, AttributeError):
        return None


def gramaj_esles(hedef_isim: str, migros_adi: str | None) -> bool:
    if not migros_adi:
        return True

    hedef_m = re.search(
        r"(\d+[\.,]?\d*)\s*(kg|g|gr|l|lt|litre|ml)\b",
        hedef_isim, re.IGNORECASE
    )
    if not hedef_m:
        return True

    hedef_sayi = float(hedef_m.group(1).replace(",", "."))
    hedef_birim = hedef_m.group(2).lower()

    migros_m = re.search(
        r"(\d+[\.,]?\d*)\s*(kg|g|gr|l|lt|litre|ml)\b",
        migros_adi, re.IGNORECASE
    )
    if not migros_m:
        return True

    migros_sayi = float(migros_m.group(1).replace(",", "."))
    migros_birim = migros_m.group(2).lower()

    def normalize(sayi, birim):
        birim = birim.replace("litre", "l").replace("lt", "l").replace("gr", "g")
        if birim == "kg":  return sayi * 1000, "g"
        if birim == "l":   return sayi * 1000, "ml"
        return sayi, birim

    h_s, h_b = normalize(hedef_sayi, hedef_birim)
    m_s, m_b = normalize(migros_sayi, migros_birim)

    if h_b != m_b:
        return True

    return abs(h_s - m_s) / max(h_s, 1) <= 0.20


def arama_terimi(isim: str) -> str:
    temiz = re.sub(
        r"\s+\d+[\.,]?\d*\s*(adet|demet|'lu|'li|'lü|'lu)\s*$",
        "", isim, flags=re.IGNORECASE
    ).strip()
    return temiz or isim


# ──────────────────────────────────────────────────────────────────────────────
# TARAYICI
# ──────────────────────────────────────────────────────────────────────────────

def tarayici_baslat(gorunmez: bool = True) -> webdriver.Chrome:
    opts = Options()
    if gorunmez:
        opts.add_argument("--headless=new")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--disable-blink-features=AutomationControlled")
    opts.add_argument("--window-size=1920,1080")
    opts.add_argument("--lang=tr-TR")
    opts.add_experimental_option("excludeSwitches", ["enable-automation"])
    opts.add_experimental_option("useAutomationExtension", False)
    opts.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )
    driver = webdriver.Chrome(options=opts)
    driver.execute_script(
        "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
    )
    return driver


# ──────────────────────────────────────────────────────────────────────────────
# FİYAT ÇEKME
# ──────────────────────────────────────────────────────────────────────────────

def kart_fiyat_al(kart_el) -> float | None:
    try:
        price_el = kart_el.find_element(By.CSS_SELECTOR, "fe-product-price#price-no-discount")
        span = price_el.find_element(By.CSS_SELECTOR, "div.price span")
        full = span.text.strip()
        try:
            cur = span.find_element(By.CSS_SELECTOR, "span.currency").text.strip()
            sayi_str = full.replace(cur, "").strip()
        except NoSuchElementException:
            sayi_str = full
        val = str_to_float(sayi_str)
        if val: return val
    except NoSuchElementException: pass

    try:
        span = kart_el.find_element(By.CSS_SELECTOR, "fe-product-price span.single-price-amount")
        full = span.text.strip()
        try:
            cur = span.find_element(By.CSS_SELECTOR, "span.currency").text.strip()
            sayi_str = full.replace(cur, "").strip()
        except NoSuchElementException:
            sayi_str = full
        val = str_to_float(sayi_str)
        if val: return val
    except NoSuchElementException: pass

    try:
        for price_el in kart_el.find_elements(By.CSS_SELECTOR, "fe-product-price"):
            for sp in price_el.find_elements(By.CSS_SELECTOR, "span"):
                txt = sp.text.strip()
                if not txt or re.search(r"TL\s*/|₺\s*/|\(", txt): continue
                sayi_str = re.sub(r"[TL₺\s]", "", txt).strip()
                val = str_to_float(sayi_str)
                if val and 1 <= val <= 10000: return val
    except Exception: pass

    return None

def migros_fiyat_al(driver: webdriver.Chrome, sorgu: str, hedef_isim: str) -> tuple:
    url = f"https://www.migros.com.tr/arama?q={sorgu.replace(' ', '+')}"
    driver.get(url)

    try:
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "fe-product-card"))
        )
    except TimeoutException:
        return None, None, url

    time.sleep(1.5)

    try:
        kartlar = driver.find_elements(By.CSS_SELECTOR, "fe-product-card")
        if not kartlar: return None, None, url

        for kart in kartlar[:6]:
            try:
                m_adi = kart.find_element(By.CSS_SELECTOR, "fe-product-name a").text.strip()
            except NoSuchElementException:
                m_adi = None

            fiyat = kart_fiyat_al(kart)
            if fiyat is None: continue

            if gramaj_esles(hedef_isim, m_adi):
                return m_adi, fiyat, url
            else:
                print(f"\n    ↷ gramaj uyuşmadı: '{m_adi}' → sonraki kart...", end="")

        try:
            ilk_adi = kartlar[0].find_element(By.CSS_SELECTOR, "fe-product-name a").text.strip()
        except Exception:
            ilk_adi = None
        return ilk_adi, kart_fiyat_al(kartlar[0]), url

    except Exception as e:
        print(f"  [hata: {e}]", end=" ")
        return None, None, url


# ──────────────────────────────────────────────────────────────────────────────
# ANA DÖNGÜ VE VERİ İŞLEME
# ──────────────────────────────────────────────────────────────────────────────

def main():
    print("Chrome başlatılıyor...")
    driver = tarayici_baslat(gorunmez=True)

    sonuclar = []
    toplam = len(data)

    try:
        for i, urun in enumerate(data, 1):
            sorgu = arama_terimi(urun["Isim"])
            print(f"[{i:>3}/{toplam}] {urun['Isim']:<44}", end=" ", flush=True)

            try:
                m_adi, m_fiyat, m_url = migros_fiyat_al(driver, sorgu, urun["Isim"])
            except Exception as e:
                print(f"→ HATA: {e}")
                m_adi, m_fiyat, m_url = None, None, None

            if m_fiyat:
                fark = round(m_fiyat - urun["Etiket_Fiyati"], 2)
                print(f"→ {m_fiyat:>8.2f} ₺   (fark: {fark:+.2f} ₺)")
            else:
                print("→ bulunamadı")

            sonuclar.append({
                **urun,
                "Migros_Adi":    m_adi,
                "Migros_Fiyati": m_fiyat,
                "Migros_URL":    m_url,
                "Fark":          round(m_fiyat - urun["Etiket_Fiyati"], 2) if m_fiyat else None,
                "Durum":         "bulundu" if m_fiyat else "bulunamadı",
            })

            time.sleep(1.5)

    finally:
        driver.quit()

    # ── CSV Oluşturma Aşaması (Ayrı JSON Kullanmadan) ──
    print("\nVeriler CSV formatında işleniyor...")
    
    processed_data = []
    pattern = re.compile(r'^(.*?)\s+(\d+(?:[.,]\d+)?\s*[a-zA-Z]+)$')

    for item in sonuclar:
        raw_isim = item.get("Isim", "")
        
        # Regexten eşleşme kontrolü
        match = pattern.match(raw_isim)
        if match:
            isim = match.group(1).strip()
            birim = match.group(2).strip()
        else:
            isim = raw_isim.strip()
            birim = ""

        processed_data.append({
            "İsim": isim,
            "Kategori": item.get("Kategori", ""),
            "Birim Tipi": item.get("Birim_Tipi", ""),
            "Migros Fiyatı": item.get("Migros_Fiyati", ""),
            "Birim": birim
        })

    # CSV Kaydetme
    import os
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    output_file = os.path.join(BASE_DIR, 'data', 'migros_price_data.csv')
    fieldnames = ["İsim", "Kategori", "Birim Tipi", "Migros Fiyatı", "Birim"]
    
    try:
        # utf-8-sig ile Excel'de Türkçe karakter sorununu çözer, ; delimiter ile kolonları böler
        with open(output_file, 'w', encoding='utf-8-sig', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter=';')
            writer.writeheader()
            writer.writerows(processed_data)
        
        print(f"✓ Başarılı! Veriler doğrudan '{output_file}' dosyasına kaydedildi.")
    except Exception as e:
        print(f"Hata oluştu: {e}")

    # İsteğe bağlı olarak kazımanın detaylı halini hala Excel'e kaydetmek istersen diye açık bıraktım:
    df = pd.DataFrame(sonuclar)
    df.to_excel("migros_fiyatlari.xlsx", index=False)

    bulunan     = df[df["Durum"] == "bulundu"]
    bulunamayan = df[df["Durum"] == "bulunamadı"]

    print(f"\n{'─'*60}")
    print(f"Bulunan: {len(bulunan)}/{toplam}   Bulunamayan: {len(bulunamayan)}")
    if len(bulunan):
        print(f"Ort. fark : {bulunan['Fark'].mean():+.2f} ₺")
        print(f"En büyük  : {bulunan['Fark'].max():+.2f} ₺")
        print(f"En küçük  : {bulunan['Fark'].min():+.2f} ₺")
    if len(bulunamayan):
        print("Bulunamayanlar: " + ", ".join(bulunamayan["Isim"].tolist()))
    print("─"*60)


if __name__ == "__main__":
    main()