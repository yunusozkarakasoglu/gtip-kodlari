# Mimari.md — Teknik Mimari

> Kavramsal mimari. Dosya envanteri `index.md`'de, canlı ilişki grafiği
> `codebase-memory` MCP'sindedir (proje indeksli: 204 düğüm / 588 kenar).

## Katmanlar

```
┌──────────────────────────────────────────────────────────────┐
│ 1. VERİ ÜRETİM (scripts/, çevrimdışı çalışır, elle tetiklenir)│
│    resmi Excel/PDF → JSON (veri/)                             │
│    ipgt_parse.py · igv_parse.py · kdv_parse.py                │
├──────────────────────────────────────────────────────────────┤
│ 2. VERİ DEPOSU (veri/)                                        │
│    SQLite (gtip_kodlari.db) + CSV + JSON çıktıları            │
│    gtip_build_db3.py (ana tablo + FTS5)                       │
│    gtip_build_vergi.py (igv/ulke_gruplari/kdv/otv)            │
├──────────────────────────────────────────────────────────────┤
│ 3. MANTIK (uygulama/sorgula_modulu.py)                        │
│    ara_urun() · gtip_bilgi() · ulke_grubu()                   │
│    hesapla_ithalat() · hesapla_ihracat() · sorgula()          │
├──────────────────────────────────────────────────────────────┤
│ 4. API (uygulama/server.py — FastAPI + uvicorn, 127.0.0.1:8899)│
│    GET /api/durum · /api/ara · /api/ulkeler · /api/gtip/{kod} │
│    POST /api/sorgula · /api/guncelle · /api/yedekle           │
│    GET /api/yedekler · POST /api/geri_yukle/{isim}            │
├──────────────────────────────────────────────────────────────┤
│ 5. ARAYÜZ (uygulama/frontend/ — React 19 + Vite 8)            │
│    App.jsx (tek sayfa, 4 adımlı akış) + App.css               │
│    dist/ derlenir, FastAPI aynı porttan statik sunar          │
└──────────────────────────────────────────────────────────────┘
```

**Neden tek port:** CORS/port derdi olmasın diye React `dist/` çıktısı FastAPI'den
sunulur; `App.jsx` içindeki `API = http://127.0.0.1:8899` sabiti aynı sunucuya bakar.

## Yol yönetimi (önemli)

`scripts/yollar.py` **tek kaynak**: `KOK`, `VERI`, `KAYNAK`, `YEDEKLER`, `DB` ve
`veri(...)`, `kaynak(...)` yardımcıları. Tüm scriptler buradan import eder; hiçbir
dosyada mutlak yol yoktur. Uygulama tarafı aynı düzeni kendi içinde çözer:
`sorgula_modulu.py` → `KOK/veri/gtip_kodlari.db`, `server.py` → `KOK/veri`,
`KOK/yedekler`, `KOK/scripts/guncelle_ve_kur.sh`.

## Boru hattı (sıra kritik)

```
kaynak/*.xls (İPGT)   ─► ipgt_parse.py   ─► veri/ipgt_2026.json
kaynak/igv_2026/*.xlsx─► igv_parse.py    ─► veri/igv_2026.json
                              │
                              ▼
        gtip_build_db3.py  ← veri/{ipgt_2026, tariffnumber_en, tim_ham}.json
        (DB'yi SİLER ve yeniden kurar: urun_kodlari + fasillar + gtip_fts)
                              │
                              ▼
        kdv_parse.py  (DB'deki 15.718 GTİP'i okur; kaynak/kdv_oranlari_gib.pdf
                       → pdftotext → veri/kdv_oranlari.json)
                              │
                              ▼
        gtip_build_vergi.py  (igv + ulke_gruplari + kdv[← JSON] + otv tabloları)
                              │
                              ▼
        veri/urun_kodlari.csv + veri/urun_kodlari.json (dışa aktarım)
```

`gtip_build_db3.py` DB dosyasını sildiği için **vergi tabloları ve KDV JSON üretimi
ondan sonra** çalışmak zorundadır. `guncelle_ve_kur.sh` bu sırayı uygular.

## Veritabanı şeması (özet)

- **`urun_kodlari`** (PK `gtip_12`) — 16 sütun: `cn_8`, `hs_6`, `poz_4`, `fas_2`,
  `aciklama_tr/_6/_4/_2`, `aciklama_en/_6`, `anahtar_en`, `birim`, `vergi_haddi`,
  `aranacak_tr`, `aranacak_en` (normalize arama metinleri)
- **`fasillar`** — 97 fasıl (TR adı TİM verisinden, EN adı tariffnumber'dan)
- **`gtip_fts`** — FTS5 sanal tablo (`tokenize='ascii'`, önek araması `kelime*`)
- **`igv`** — menşe grubuna göre oran kolonları (`oran_ab`, `oran_diger`, `oran_kos`,
  `oran_sng`, `oran_vnz`, `oran_bae`, `oran_iran`, `oran_gts`, `oran_kol2/3`) + `liste`, `dipnot`
- **`ulke_gruplari`** — `ulke_kod` → `igv_grup` (ab / kos / sng / vnz / bae / iran / diger)
- **`kdv`** — `gtip_12`, `oran` (1/10/20), `kaynak`
- **`otv`** — kurulu, **boş** (liste oran / maktu)
- Index'ler: `cn_8`, `hs_6`, `poz_4`, `fas_2`, `gtip_12`, `aciklama_en`; `PRAGMA journal_mode=WAL`

## Arama motoru mantığı

1. **Normalizasyon** — Türkçe harf katlama (İ/I→i, ş→s, ö→o...) + noktalama temizliği
2. **Kök indirgeme** — 5 karakterden uzun kelimelerde ilk 6 harf (`pistonlar`→`piston`)
3. **Eşanlamlı genişletme** — `ES_ANLAM` sözlüğü (gemi→deniz ...)
4. **Aday toplama** — önce FTS5 (`bm25` sıralı, 200 kayıt), boşsa `LIKE` yedeği
5. **Alaka skoru** — `anahtar_en` +10, `aciklama_tr` +8, `aciklama_tr_6` +5,
   `aciklama_en` +4, `aciklama_tr_4` +2 (kelime öneki eşleşmesi)
6. **Seçim** — `sorgula()` sorgu kelimelerini en çok eşleştiren adayı varsayılan seçer

> Türkçe kök indirgeme bilinçli olarak **kaba** (ilk 6 harf): ek kütüphanesi yok,
> çevrimdışı ve hızlı. Yanlış eşleşme şikâyeti gelirse `ES_ANLAM`/skor ağırlıkları ayarlanır.

## Bağımlılıklar

| Taraf | Paketler |
|---|---|
| Veri işleme | `xlrd` (İPGT `.xls`), `openpyxl` (İGV `.xlsx`), `pdftotext` (poppler-utils, KDV PDF) |
| API | `fastapi`, `uvicorn`, `pydantic` |
| Arayüz | `react`, `react-dom`; dev: `vite`, `@vitejs/plugin-react`, `oxlint` |
| Sistem | Python 3.12, Node 22, `curl`, `unzip`, `tar` |

## Kodlama kuralları (bu projede)

- Python: 4 boşluk, `snake_case`, fonksiyonlar kısa; SQL doğrudan `sqlite3` ile (ORM yok)
- Bağlantı: `_baglan()` (uygulama) / doğrudan `sqlite3.connect(DB)` (scriptler);
  `row_factory = sqlite3.Row` uygulama tarafında
- Transaction: `cur.execute("BEGIN")` … `con.execute("COMMIT")` (Python 3.12'de
  `executemany` örtük transaction **açmaz** — bu tuzağa dikkat)
- React: fonksiyon bileşenleri, Türkçe değişken/etiket adları, tek dosyada tek sayfa
- Yeni dosya eklerken `index.md` haritasını güncelle

## Kritik notlar / tuzaklar

1. **KDV zinciri iki adımlı** — `kdv_parse.py` JSON üretir, `gtip_build_vergi.py` yükler.
2. **`gtip_build_db3.py` DB'yi siler** — çalıştırma sırasında API açıksa bağlantı kopar.
   Güncelleme öncesi uygulamayı kapatmak ya da beklemek gerekir.
3. **`pdftotext -layout`** çıktısı `/tmp/kdv_gib.txt`'ye yazılır; script her çalıştırmada
   `rm -f` ile tazeler (eski metin yanlış parse'a yol açmasın).
4. **`tim_ham.json`** arşiv verisidir (2024 kaynaklı, TİM) — yalnız fasıl **adları** için
   kullanılır, GTİP listesi için değil.
5. **`tariffnumber_en.json`** statik anlık görüntü; boru hattında yenileyicisi yok.
6. WAL modu etkin — DB'yi elle kopyalarken `-wal`/`-shm` dosyalarına dikkat.
7. `eksik_cn8.json` — EN açıklaması bulunamayan **215 CN8 kodu**nun araştırma notu
   (12 hane düzeyinde EN kapsamı yine %99,9).
