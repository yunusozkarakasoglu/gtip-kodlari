# Project_info.md — Proje Künyesi

## Tanım

**gtip_kodlari** — Türkiye ithalat/ihracatı için **GTİP (12 hane) / HS kodu (6 hane) /
CN (8 hane)** bulma ve **ithalat vergisi hesaplama** sistemi. Resmi kaynaklardan
(Ticaret Bakanlığı İPGT 2026, İthalat Genel Müdürlüğü İGV listeleri, GİB KDV oranları)
üretilen yerel bir SQLite veritabanı + tamamen çevrimdışı çalışan FastAPI/React arayüzü.

**Kime hizmet eder:** gümrük müşavirleri, ithalat/ihracat yapan firmalar, muhasebe
programı entegrasyonu (CSV/JSON/SQLite çıktıları).

## Modüller

| Modül | Ne yapar | Nerede |
|---|---|---|
| Veri üretimi | Resmi Excel/PDF → JSON | `scripts/ipgt_parse.py`, `igv_parse.py`, `kdv_parse.py` |
| DB kurulumu | JSON → SQLite + FTS5 + vergi tabloları | `scripts/gtip_build_db3.py`, `gtip_build_vergi.py` |
| Sorgulama çekirdeği | Ürün→aday GTİP, ülke grubu, vergi hesabı | `uygulama/sorgula_modulu.py` |
| API | FastAPI uçları + React statik sunum | `uygulama/server.py` |
| Arayüz | 4 adımlı iş akışı ekranı | `uygulama/frontend/src/App.jsx` |
| Güncelleme | İndir → parse → DB → versiyon | `scripts/guncelle.sh`, `guncelle_ve_kur.sh` |

## Veri hacmi (v2026.2)

| Öğe | Değer |
|---|---|
| Resmi GTİP (12 hane) | 15.718 |
| Fasıl / pozisyon | 97 fasıl |
| Türkçe açıklama kapsamı | %100 |
| İngilizce açıklama kapsamı | 15.704 / 15.718 (%99,9) |
| Vergi haddi (İPGT MFN) dolu | 14.375 / 15.718 (%91) |
| İGV kaydı | 4.562 (EK-1: 4.544, EK-2: 14, EK-3: 4) |
| KDV kaydı | 15.718 (%1: 2.214 · %10: 3.067 · %20: 10.437) |
| Ülke → İGV grubu eşlemesi | 110 ülke (+ bilinmeyen → D.Ü.) |
| ÖTV | tablo hazır, **liste boş** |

## Sayfalar / ekranlar

Tek sayfa (SPA), dört adımlı akış + sistem paneli:

1. **Ürün sorgusu** — metin gir → "🔍 Ara" → alaka skorlu aday GTİP listesi
2. **Ülke + hareket tipi** — menşe/varış ülkesi (ISO), ithalat/ihracat, CIF tutarı (€)
3. **Sorgula** — "🔎 Sorgula"
4. **Rapor** — ithalatta GV + İGV + ÖTV + KDV dökümü ve toplam maliyet;
   ihracatta bilgi notları
5. **Sistem paneli** — 🔄 Güncelle (kaynakları indir + DB kur), 💾 Yedek al,
   ↩ Geri yükle (yedek listesi)

## Uygulama içi akışlar

**Sorgu akışı (ithalat):**
`ürün metni` → `ara_urun()` (FTS5 + LIKE + skorlama) → aday listesi → kullanıcı seçer →
`hesapla_ithalat(gtip, ülke, cif)` → `ulke_grubu()` ile İGV grubu → GV (AB için %0) +
İGV (gruba göre kolon) + KDV (matrah: CIF+GV+İGV+ÖTV) → rapor JSON → arayüz.

**Güncelleme akışı:**
`guncelle_ve_kur.sh` → yedek al → kaynakları `kaynak/`e indir → parse → DB kur →
KDV JSON üret → vergi tablolarını kur → `veri_versiyon.json` sürümünü artır.

**Arama normalizasyonu:** Türkçe karakter katlama (TİŞÖRT→tisort) + 6 karakterlik kök
indirgeme (pistonlar→piston) + İngilizce anahtar kelime ağırlığı.

## Kritik iş kuralları

- **GTİP ≠ HS kodu:** ilk 6 hane uluslararası HS, son 6 hane AB + milli açılım.
- **AB/EFTA/Gümrük Birliği menşeli** sanayi ürünlerinde gümrük vergisi ve İGV %0.
- **Karar 3351 md. 2/2:** A.TR'li ithalatta eşya AB/Türk menşeli değilse **D.Ü. oranı**
  uygulanır (A.TR tek başına %0 sağlamaz).
- **KDV matrahı** = CIF + gümrük vergisi + İGV + ÖTV.
- **Karar md.1/3:** I sayılı listedeki gıda maddesinden ÖTV'ye tabi olanlar → KDV %10.
- Hesaplama **ÖTV, anti-damping, ilave mali yükümlülük ve korunma önlemlerini kapsamaz**
  → gümrük müşaviri / TARA teyidi gerekir (arayüzde uyarı olarak gösterilir).
- **`vergi_haddi` = 474 sayılı Kanun (14.05.1964) kanuni haddi**, fiilen uygulanan gümrük
  vergisi oranı DEĞİLDİR (İPGT dosyasının kendi açıklaması). Uygulanan oranlar İthalat
  Rejimi Kararı ekleriyle yıllık belirlenir; arayüzdeki "Gümrük vergisi %X" bu nedenle
  üst sınır/kanuni had olarak okunmalıdır. (Açık iş — `Tasks.md`.)

## Yasal dayanak

- İthalat Rejimi Kararı **10781** (30.12.2025, RG 33123 Mükerrer)
- İGV Kararı **3351** + **10791** (31.12.2025, RG 33124 3. Mükerrer)
- KDV: Karar 2007/13033 + değişiklikleri (GİB konsolide "KDV Oranları" PDF'i)
