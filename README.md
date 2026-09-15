# GTİP / HS Kod Kütüphanesi + Vergi Hesaplama Sistemi

**Türk Gümrük Tarife Cetveli (İPGT 2026) + AB Kombine Nomenklatürü + İGV + KDV veritabanı**

İthalat ve ihracatta uluslararası ürün dolaşım kodlarının (GTİP / HS Code / CN / TARIC) Türkçe ve İngilizce açıklamalarıyla birlikte aranabilir listesi. **Türkiye ithalatı için tam vergi hesaplama** (gümrük vergisi + İGV + KDV) desteği. Muhasebe programı entegrasyonu ve gümrük beyanı hazırlığı için SQLite + CSV + JSON formatlarında hazırlanmıştır.

---

## 📦 Dosya Dağılımı: GitHub ↔ Mega

| Depo | İçerik |
|---|---|
| **GitHub** — `github.com/yunusozkarakasoglu/gtip-kodlari` | Kod, scriptler, React uygulaması, README, küçük veri (JSON <2MB) |
| **Mega** — `/gtip-kodları/` (yunusozkarakasoglu@gmail.com hesabı) | Büyük veri: `gtip_kodlari.db` (49MB), CSV/JSON çıktılar, resmi arşiv PDF'leri, ZIP'ler, yedekler |

**Mega klasör yapısı:**
```
Mega/
└── gtip-kodları/
    ├── veri/            ← gtip_kodlari.db, urun_kodlari.csv/.json, ipgt_2026.json,
    │   │                  igv_2026.json, kdv_oranlari.json, tariffnumber_en.json,
    │   │                  tim_ham.json
    │   └── yedekler/    ← versiyonlu tar.gz yedekler
    └── arsiv/           ← resmi belgeler: İthalat Rejimi Kararları, İGV/KDV Kararları,
                           tgtc_2026.zip, igv_2026.zip
```

**Neden bölünmüş?** GitHub 100MB dosya limiti uygular; 49MB DB + 130MB arşiv repo'yu şişirir.
Büyük dosyaların TAMAMI scriptlerle yeniden üretilebilir:
```bash
bash scripts/guncelle_ve_kur.sh   # kaynakları indir → parse → DB kur (büyük dosyaları yeniden oluşturur)
```
Mega'daki dosyalar arşiv/kopya amaçlıdır; çalışmak için GitHub klonuna + `scripts/guncelle_ve_kur.sh` yeterlidir.

---

## ⚙️ Kurulum / Bağımlılıklar

```bash
# Sistem araçları: python3 (3.12), node (22), curl, unzip, tar, poppler-utils (pdftotext)
sudo apt install poppler-utils unzip curl

# Python
pip install fastapi uvicorn pydantic xlrd openpyxl

# Arayüz (tek seferlik)
cd uygulama/frontend && npm install

# Çalıştırma (arayüz + API, tek port)
cd uygulama && ./baslat.sh            # → http://127.0.0.1:8899
```

---

## 📊 Veri Özeti

| Metrik | Değer |
|---|---|
| Resmi GTİP sayısı (12 hane) | **15.718** |
| Fasıl sayısı | 97 (77 ve 98 hariç) |
| Türkçe açıklama kapsamı | %100 |
| İngilizce açıklama kapsamı | %99,9 (15.704 / 15.718) |
| Vergi haddi kapsamı | %91 (14.375 kod) — bkz. ⚠️ aşağıdaki uyarı |
| **İGV (İlave Gümrük Vergisi) kayıtları** | **4.562** (EK-1: 4.544, EK-2: 14, EK-3: 4) |
| **KDV oranı (GİB listelerinden)** | **5.281** (%1: 2.214, %10: 3.067 — gerisi %20) — tabloda 15.718 GTİP'in tamamı için oran vardır |
| Ülke grubu eşlemesi | 110 ülke + varsayılan D.Ü. |
| Yıl | **2026** (1 Ocak 2026'da yürürlüğe girmiştir) |

> ### ⚠️ `vergi_haddi` sütunu neyi gösterir?
>
> İPGT Excel'lerindeki bu sütunun başlığı **"474 VERGİ HADDİ"**'dir ve kaynak dosyanın
> kendi açıklaması (`kaynak/tgtc_2026/2026 TGTC/açıklamalar.xls`) şöyle der:
> *"Bu sütunda, 14.05.1964 tarih ve 474 sayılı Kanun ile tesbit edilen vergi hadleri
> gösterilmiştir."*
>
> Yani bu değer **474 sayılı Kanun'un kanuni haddidir; fiilen uygulanan ithalat vergisi
> oranı değildir.** Uygulanan oranlar her yıl **İthalat Rejimi Kararı** ekleriyle
> belirlenir (ör. Karar 10781). Veri setindeki dağılım bunu doğrular: %50 (2.540 kayıt),
> %25 (1.660), %100 (1.567) ... — otomobil (87.03) ve cep telefonu (8517.12) gibi
> kalemlerde bu sütun **boştur**.
>
> **Pratik sonuç:** Araç, ürünün kanuni haddini gösterir; gümrük beyanındaki gerçek vergi
> için İthalat Rejimi Kararı / TARA teyidi şarttır. (Kaynak PDF'ler taranmış görüntüdür,
> metin katmanı yoktur → uygulanan oranların otomatik çıkarımı OCR gerektirir.)

---

## 🗂️ Proje Yapısı

```
gtip_kodlari/
│
├── AGENTS.md  Roadmaps.md  Project_info.md  Tasks.md  Mimari.md  index.md
├── README.md                 ← bu dosya (Readme.md aynı dosyaya bağdır)
│
├── scripts/                  ← TÜM kod (veri üretimi + güncelleme)
│   ├── yollar.py             ← klasör yolları (tek kaynak: veri/, kaynak/, yedekler/)
│   ├── ipgt_parse.py         ← İPGT Excel → JSON dönüştürücü
│   ├── igv_parse.py          ← İGV Excel → JSON dönüştürücü
│   ├── kdv_parse.py          ← GİB KDV oranları PDF → JSON (pdftotext ile)
│   ├── gtip_build_db3.py     ← JSON → SQLite ana tablo + FTS5 kurucusu (DB'yi yeniden kurar)
│   ├── gtip_build_vergi.py   ← İGV + ülke grupları + KDV + ÖTV tabloları kurucusu
│   ├── vergi_hesapla.py      ← VERGİ HESAPLAMA ARACI (GTİP + menşe + CIF → tam döküm)
│   ├── guncelle.sh           ← resmi kaynakları indirir (parse/DB kurmaz)
│   └── guncelle_ve_kur.sh    ← yedek + indir + parse + DB kur + versiyon (tam akış)
│
├── veri/                     ← ÜRETİLEN VERİ (git'e girmez)
│   ├── gtip_kodlari.db       ← ANA VERİTABANI (SQLite) — muhasebe programı bunu kullanır
│   ├── urun_kodlari.csv      ← Excel'de açılabilir düz tablo (14 sütun × 15.718 satır)
│   ├── urun_kodlari.json     ← API/entegrasyon formatı (JSON)
│   ├── ipgt_2026.json        ← Ham İPGT 2026 verisi (Ticaret Bakanlığı, Türkçe tanımlar)
│   ├── tariffnumber_en.json  ← EN açıklama + anahtar kelimeler (tariffnumber.com)
│   ├── igv_2026.json         ← Ham İGV verisi (EK-1/2/3, menşe bazlı oranlar)
│   ├── kdv_oranlari.json     ← GTİP bazlı KDV oranları (GİB I/II sayılı listeler)
│   ├── tim_ham.json          ← TİM fasıl adları (ARŞİV — 2024 kaynaklı)
│   ├── eksik_cn8.json        ← EN karşılığı bulunamayan CN8 kodları (araştırma notu)
│   └── veri_versiyon.json    ← sürüm + kaynak karar numaraları + güncellik
│
├── kaynak/                   ← RESMİ ARŞİV (git'e girmez, guncelle.sh indirir)
│   ├── tgtc_2026.zip + tgtc_2026/    ← İPGT 2026 Excel'leri (98 fasıl + notlar + kılavuzlar)
│   ├── igv_2026.zip + igv_2026/      ← İGV listeleri (Ek-1.xlsx, Ek-2 Ek-3.xlsx)
│   ├── ithalat_rejimi_10781.pdf      ← İthalat Rejimi Kararı 10781 (Resmî Gazete, 631 s.)
│   ├── ithalat_rejimi_3350.pdf       ← İthalat Rejimi Kararı 3350 (Resmî Gazete, 568 s.)
│   ├── igv_karar_10791.pdf           ← İGV Kararı 10791 (Resmî Gazete, 103 s.)
│   ├── kdv_karar_7346.pdf            ← KDV Kararı 7346
│   └── kdv_oranlari_gib.pdf          ← GİB resmi "KDV Oranları" PDF'i
│
├── uygulama/                 ← ARAYÜZ + API (React + FastAPI)
│   ├── server.py             ← FastAPI uçları + React statik sunumu
│   ├── sorgula_modulu.py     ← sorgulama çekirdeği (arama + vergi hesabı)
│   ├── baslat.sh             ← tek komutla başlatma (build + uvicorn, port 8899)
│   └── frontend/             ← React (Vite) kaynakları + dist/ (git'e girmez)
│
└── yedekler/                 ← versiyonlu tar.gz anlık görüntüler (git'e girmez)
```

---

## 🗃️ Veritabanı Şeması (`veri/gtip_kodlari.db`)

### Tablo: `urun_kodlari` — her satır = 1 resmi 12 haneli GTİP

| Sütun | Örnek | Açıklama |
|---|---|---|
| `gtip_12` | `090121000000` | **Resmi GTİP** (12 hane) — gümrük beyan kodu |
| `cn_8` | `09012100` | AB Kombine Nomenklatür kodu (8 hane) |
| `hs_6` | `090121` | **HS kodu** (6 hane, uluslararası — WCO standardı) |
| `poz_4` | `0901` | Pozisyon / Heading (4 hane) |
| `fas_2` | `09` | Fasıl / Chapter (2 hane) |
| `aciklama_tr` | `Kafeini alınmamış` | Resmi İPGT tanımı (12 hane seviyesi) |
| `aciklama_tr_6` | — | İPGT tanımı (6 hane seviyesi) |
| `aciklama_tr_4` | `Kahve (kavrulmuş veya kafeini alınmış olsun olmasın)...` | İPGT tanımı (4 hane seviyesi) |
| `aciklama_tr_2` | `Kahve, çay, paraguay çayı ve baharat` | Fasıl adı (TR) |
| `aciklama_en` | `Roasted coffee (excl. decaffeinated)` | İngilizce açıklama (8 hane) |
| `aciklama_en_6` | — | İngilizce açıklama (6 hane) |
| `anahtar_en` | `Roasted Coffee · Coffee Beans...` | İngilizce anahtar kelimeler (arama desteği) |
| `birim` | `Baş` | Ölçü birimi |
| `vergi_haddi` | `100` | **474 sayılı Kanun (1964) ile tespit edilen vergi haddi (%)** — fiilen uygulanan oran değildir, aşağıdaki uyarıya bakın |
| `aranacak_tr` | `kahve kavrulmus kafeini alinmamis...` | Normalize TR arama metni (TİŞÖRTLER→tisortler) |
| `aranacak_en` | `roasted coffee decaffeinated...` | Normalize EN arama metni |

### Tablo: `fasillar` — 97 fasıl referansı (fas_2, ad_tr, ad_en)

### Sanal Tablo: `gtip_fts` — FTS5 tam metin arama indeksi

Index'ler: `cn_8`, `hs_6`, `poz_4`, `fas_2`, `gtip_12`, `aciklama_en`

---

## 🧮 Vergi Tabloları

### `igv` — İlave Gümrük Vergisi (4.562 kayıt)
Karar 3351 + 10791 — menşe ülke grubuna göre farklı oranlar:

| Sütun | Ülke grubu | Açıklama |
|---|---|---|
| `oran_ab` | AB+EFTA+STA ortakları | Neredeyse her zaman %0 (Gümrük Birliği) |
| `oran_diger` | **D.Ü. (Diğer Ülkeler)** | Çin, ABD, Japonya... — ana İGV oranı |
| `oran_kos/sng/vnz/bae/iran` | Kosova, Singapur, Venezuela, BAE, İran | EK-2/3'te spesifik kolonlar |
| `oran_gts` | GTS ülkeleri (GYÜ/ÖTDÜ/EAGÜ) | EK-1'de D.Ü. ile eşit |
| `oran_kol2/kol3` | Ara gruplar | EK-1 sütun 2/3 (grup eşlemesi için TB ile teyit önerilir) |

**Kritik kural (Karar 3351 md. 2/2):** A.TR'li ithalatta AB/Türk menşeli olmayan eşya → D.Ü. oranı uygulanır.

### `ulke_gruplari` — ülke → İGV grubu eşlemesi (110 ülke + D.Ü. varsayılan)

### `kdv` — KDV oranları (15.718 kayıt — her GTİP için oran, GİB resmi)
GİB'in resmi **"KDV Oranları"** PDF'inden (konsolide Karar 2007/13033 + değişiklikler) GTİP bazlı oranlar:
- **%1** — I sayılı liste (temel gıda: et, süt, sebze, meyve, un, ekmek, kitap...)
- **%10** — II sayılı liste (tekstil, giyim, deri, ayakkabı, halı, kağıt/kitap...)
- **%20** — genel oran (listelerde olmayanlar, makine, elektronik...)
- Özel kural (Karar md.1/3): I sayılı gıda maddelerinden ÖTV'ye tabi olanlar → %10
- "kısmi" işaretli kayıtlar koşulludur (örn. kullanılmış araç %1, yeni %20)

### `otv` — ÖTV tablosu (iskelet; GİB listeleri eklenebilir)

---

## 🖥️ React Uygulaması (arayüz)

**Başlatma:**
```bash
cd gtip_kodlari/uygulama && ./baslat.sh
# Aç: http://127.0.0.1:8899
```

**Görev akışı (varsayılan):**
1. **Ürün sorgusu** yaz (örn. "gemi motoru parçaları", "piston") → 🔍 Ara
2. Aday GTİP listesinden seç
3. **Ülke** seç (menşe/varış) + **hareket tipi** (ithalat/ihracat) + CIF
4. **Sorgula** → tam vergi raporu (GV + İGV + KDV + toplam)

**Sistem paneli:**
- 🔄 **Güncelle** — kaynakları yeniden indirir + DB'yi yeniden kurar (önce otomatik yedek)
- 💾 **Yedek al** / **Geri yükle** — versiyonlu tar.gz anlık görüntüler

**Mimari:** React (Vite) + FastAPI + SQLite — tamamen çevrimdışı, internet gerekmez.

## 💰 Vergi Hesaplama (komut satırı)

```bash
python3 scripts/vergi_hesapla.py <gtip_12> <menşe_ISO> <CIF_EUR>
```

**Örnek — gemi motoru parçası (piston), Çin menşeli, CIF 10.000 €:**
```
Gümrük vergisi: %40  → 4.000 €   (İPGT haddi)
İGV:            %7   →   700 €   (EK-1, D.Ü.)
KDV:            %20  → 2.940 €   (matrah: CIF+GV+İGV)
─────────────────────────────────
TOPLAM VERGİ: 7.640 € | TOPLAM MALİYET: 17.640 €
```

**Aynı parça Almanya menşeli:** GV %0 + İGV %0 + KDV 2.000 € = **2.000 €** (Gümrük Birliği avantajı)

> ⚠️ Hesaplama **gümrük vergisi + İGV + KDV**'yi içerir. ÖTV, ilave mali yükümlülük, anti-damping ve korunma önlemleri kapsam dışıdır — bu kalemler için gümrük müşaviri / TARA (`uygulama.gtb.gov.tr/TARA`) teyidi gereklidir.
>
> ⚠️ **Gümrük vergisi kalemi, İPGT'deki "474 sayılı Kanun vergi haddi" sütunundan gelir** — fiilen uygulanan oran değildir (yukarıdaki uyarıya bakın). Uygulanan oranlar İthalat Rejimi Kararı eklerindedir.

---

## 🔍 Kullanım (SQL örnekleri)

### 1. Kod → Ürün (gümrük kodunu çöz)
```sql
SELECT gtip_12, aciklama_tr, aciklama_tr_4, aciklama_en, vergi_haddi
FROM urun_kodlari
WHERE gtip_12 = '090121000000';
```

### 2. Ürün → Kod (Türkçe arama — morfoloji toleranslı)
```sql
SELECT gtip_12, hs_6, aciklama_tr, aciklama_tr_4
FROM urun_kodlari
WHERE aranacak_tr LIKE '%pamuk%' AND aranacak_tr LIKE '%tisort%';
-- "pamuk tişört" → 610910000000
```

### 3. Ürün → Kod (İngilizce arama)
```sql
SELECT gtip_12, cn_8, aciklama_en
FROM urun_kodlari
WHERE aranacak_en LIKE '%leather%' AND aranacak_en LIKE '%jacket%';
-- → 420310000012
```

### 4. HS kodu seviyesinde tarama
```sql
SELECT gtip_12, aciklama_tr, aciklama_en, vergi_haddi
FROM urun_kodlari
WHERE hs_6 = '6109';           -- tam eşleşme (index'li, anında)
-- veya önek taraması:
WHERE hs_6 LIKE '6109%';       -- 6109 ile başlayan tüm tişört kodları
```

### 5. Hızlı tam metin arama (FTS5 — önek kullanımı gerekli)
```sql
SELECT gtip_12 FROM gtip_fts WHERE gtip_fts MATCH 'tisort*';
SELECT gtip_12 FROM gtip_fts WHERE gtip_fts MATCH 'walnut';
```

### 6. Fasıl istatistikleri
```sql
SELECT fas_2, COUNT(*) FROM urun_kodlari GROUP BY fas_2 ORDER BY 2 DESC LIMIT 5;
```

---

## 📚 Kod Hiyerarşisi (Bilgi)

| Hane | Ad | Kapsam |
|---|---|---|
| 2 | Fasıl (Chapter) | 🌍 HS |
| 4 | Pozisyon (Heading) | 🌍 HS |
| 6 | Alt Pozisyon = **HS Kodu** | 🌍 HS (WCO, 180+ ülke) |
| 8 | Kombine Nomenklatür (CN) | 🇪🇺 AB (Türkiye Gümrük Birliği gereği uygular) |
| 10 | TARIC | 🇪🇺 AB |
| 12 | **GTİP** | 🇹🇷 Türkiye (İPGT) |

> **Önemli:** GTİP ≠ HS Kodu. GTİP'in ilk 6 hanesi = HS Kodu; son 6 hanesi AB + milli açılım.

---

## 🔄 Güncelleme + Versiyonlama + Yedekleme

| İşlem | Komut / Buton | Ne yapar |
|---|---|---|
| **Güncelle** | `bash scripts/guncelle_ve_kur.sh` veya uygulamada 🔄 | 1) Yedek al → 2) İPGT+İGV+KDV indir → 3) Parse → 4) DB kur → 5) Vergi tabloları + KDV → 6) Versiyon artır (2026.2→2026.3) |
| **Yedek al** | uygulamada 💾 | `yedekler/veri_{versiyon}_{tarih}.tar.gz` oluşturur (DB+JSON+versiyon) |
| **Geri yükle** | uygulamada yedek satırına tıkla | Seçilen yedeği geri yükler |
| **Versiyon takibi** | `veri/veri_versiyon.json` | Kaynak adları + karar numaraları + güncellik durumu |

**Manuel adımlar (yıllık):**
1. **Resmi İPGT indir:** Gümrükler Genel Müdürlüğü → `ggm.ticaret.gov.tr/duyurular` → "İstatistik Pozisyonlarına Bölünmüş Türk Gümrük Tarife Cetveli" duyurusu → `20XX TGTC.zip`
2. **İGV listeleri:** `ithalat.ticaret.gov.tr/duyurular` → İGV Kararı duyurusu → `igv 20XX.zip` (yıl ortası güncellemelerine dikkat!)
3. **EN açıklamalar:** `tariffnumber.com` fasıl ve heading sayfalarından EN açıklama + anahtar kelimeler
4. **İş akışı:** `scripts/ipgt_parse.py` → `scripts/igv_parse.py` → `scripts/gtip_build_db3.py` → `scripts/kdv_parse.py` → `scripts/gtip_build_vergi.py` → CSV/JSON dışa aktarılır
5. **KDV/ÖTV:** GİB'den indirimli oran listeleri (`kaynak/kdv_oranlari_gib.pdf`) → `scripts/kdv_parse.py` → `kdv` tablosu; ÖTV listeleri henüz eklenmedi (`otv` boş)
6. **Anti-damping:** TB İthalat GM önlem listesi → ayrı tablo (henüz eklenmedi)
