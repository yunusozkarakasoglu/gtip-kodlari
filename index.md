# index.md — Pusula (görev öncesi 2. sırada okunur)

> Amaç: **nereye bakacağımı** söylemek. Dosya envanteri değildir — canlı envanter ve
> "kim çağırır / etkisi ne" soruları `codebase-memory` grafiğinin işi (bu proje indeksli:
> 204 düğüm / 588 kenar). Burada niyet, komut ve tuzaklar var.

## Çalıştırma komutları

```bash
# --- Uygulama (arayüz + API, tek port) ---
cd uygulama && ./baslat.sh            # → http://127.0.0.1:8899
cd uygulama && ./baslat.sh --build    # frontend'i zorla yeniden derle
# eşdeğeri: python3 -m uvicorn server:app --host 127.0.0.1 --port 8899

# --- Sorgulama (arayüzsüz) ---
python3 uygulama/sorgula_modulu.py 'gemi motoru parçaları' CN ithalat 10000
python3 scripts/vergi_hesapla.py 840999000012 CN 10000     # GTİP + menşe + CIF

# --- Veri güncelleme ---
bash scripts/guncelle.sh              # sadece resmi kaynakları indir → kaynak/
bash scripts/guncelle_ve_kur.sh       # yedek + indir + parse + DB kur + versiyon

# --- Boru hattı parça parça (guncelle_ve_kur.sh ile aynı sıra) ---
python3 scripts/ipgt_parse.py         # kaynak/*.xls  → veri/ipgt_2026.json
python3 scripts/igv_parse.py          # kaynak/igv_2026/*.xlsx → veri/igv_2026.json
python3 scripts/gtip_build_db3.py     # JSON → veri/gtip_kodlari.db (DB'yi SİLER!)
python3 scripts/kdv_parse.py          # DB + kaynak/kdv_oranlari_gib.pdf → veri/kdv_oranlari.json
python3 scripts/gtip_build_vergi.py   # igv + ulke_gruplari + kdv + otv tabloları

# --- Frontend (ayrı çalıştırmak istersen) ---
cd uygulama/frontend && npm run dev    # Vite dev sunucusu
cd uygulama/frontend && npm run build  # dist/ üretir (FastAPI bunu sunar)

# --- Arama testi (DB doğrudan) ---
python3 - <<'PY'
import sqlite3
c = sqlite3.connect("veri/gtip_kodlari.db")
print(c.execute("SELECT gtip_12, aciklama_tr FROM urun_kodlari WHERE aranacak_tr LIKE '%piston%' LIMIT 3").fetchall())
print(c.execute("SELECT oran FROM kdv WHERE gtip_12='610910000000'").fetchone())
PY
```

## "X özelliği → şu dosyalar" haritası

| İstediğim şey | Bakılacak yer |
|---|---|
| Ürün adından GTİP adayı bulmak (skorlama, eşanlamlı) | `uygulama/sorgula_modulu.py` → `ara_urun()` |
| Vergi hesabı (GV + İGV + KDV) | `uygulama/sorgula_modulu.py` → `hesapla_ithalat()` |
| Menşe ülke → İGV grubu (ab/diger/kos/sng/...) | `uygulama/sorgula_modulu.py` → `ulke_grubu()`; tablo `ulke_gruplari` |
| İhracat akışı (vergi yok, notlar) | `uygulama/sorgula_modulu.py` → `hesapla_ihracat()` |
| API uçları / statik React sunumu | `uygulama/server.py` |
| Arayüz ekranı, 4 adımlı akış, sistem paneli | `uygulama/frontend/src/App.jsx` (+ `App.css`) |
| Arama normalizasyonu / kök indirgeme | `uygulama/sorgula_modulu.py` (`normalize`, `_kok`) ve `scripts/gtip_build_db3.py` (`normalize`) |
| **Gümrük vergisi oranı (474 sayılı Kanun haddi!)** | `urun_kodlari.vergi_haddi` ← `scripts/ipgt_parse.py`; uyarı: `README.md` "⚠️ `vergi_haddi` sütunu neyi gösterir?" |
| İPGT Excel → JSON | `scripts/ipgt_parse.py` |
| İGV Excel → JSON | `scripts/igv_parse.py` |
| KDV oranları (GİB PDF) | `scripts/kdv_parse.py` |
| Ana DB + FTS5 kurulumu | `scripts/gtip_build_db3.py` |
| İGV/ülke/KDV/ÖTV tabloları | `scripts/gtip_build_vergi.py` |
| Yedekle / geri yükle | `uygulama/server.py` (`/api/yedekle`, `/api/geri_yukle/{isim}`) |
| Tüm dosya yolları (tek kaynak) | `scripts/yollar.py` |
| Kaynakları yeniden indirme | `scripts/guncelle.sh`, `scripts/guncelle_ve_kur.sh` |

## Konvansiyonlar ve tuzaklar

- **`vergi_haddi` = 474 sayılı Kanun (1964) kanuni haddi**, fiilen uygulanan gümrük vergisi
  değil (kaynak: `kaynak/tgtc_2026/2026 TGTC/açıklamalar.xls`). Arayüz bu değeri "Gümrük
  vergisi %X" olarak gösteriyor; gerçek oran İthalat Rejimi Kararı eklerindedir (taranmış PDF
  → OCR gerekir). Karar bekleyen açık iş: `Tasks.md`.
- **Sabit mutlak yol yazma** → `scripts/yollar.py` kullan (`from yollar import VERI, DB, kaynak`).
- **Boru hattı sırası:** `ipgt_parse → igv_parse → gtip_build_db3 → kdv_parse →
  gtip_build_vergi`. `gtip_build_db3.py` DB'yi **siler**; vergi tabloları ondan sonra kurulur.
- **KDV iki adımlı:** JSON üretimi (`kdv_parse.py`) ≠ tabloya yükleme (`gtip_build_vergi.py`).
- **Python 3.12:** `executemany` örtük transaction açmaz — `cur.execute("BEGIN")` +
  `con.execute("COMMIT")` kalıbını kullan.
- **Arayüz portu 8899 sabit** (`App.jsx` içinde `const API`). Portu değiştirirsen iki yeri
  (baslat.sh/uvicorn ve App.jsx) birlikte değiştir.
- **KDV PDF'i `/tmp/kdv_gib.txt`'ye çevrilir**; script başına `rm -f` eklendi. Metin eskiyse
  yanlış parse riski var.
- **EN açıklama verisi statik** (`veri/tariffnumber_en.json`) — boru hattında yenileyici yok.
- **`otv` tablosu boş**; arayüzde ÖTV kalemi bu yüzden 0 gösterir (uyarı metni korunur).
- WAL modu açık: DB'yi elle kopyalarken `-wal`/`-shm` dosyalarını da al ya da önce
  bağlantıları kapat.

## Ortam notları (bu makine)

- `codebase-memory-mcp` indeksi hazır (proje kökü: `/home/yunus/Masaüstü/gtip_kodlari`).
- **Uygulama çalışıyor:** `http://127.0.0.1:8899` (2026-09-15'ten itibaren; süreç `setsid` ile
  arka planda, kalıcı systemd servisi **yok** → makine yeniden başlarsa elle başlat).
  Log: `/tmp/gtip_uygulama.log`. Durdurmak için: `pkill -f 'uvicorn server:app'`
  (⚠️ bu komutu içeren kabuk da ölebilir — pid ile öldürmek daha güvenli).
- 8899'u daha önce tutan sahipsiz `python3 -m http.server` (pid 2981626) kapatıldı.
- Büyük veri yerelde `veri/` (~96 MB) ve `kaynak/` (~76 MB); Mega kopyaları README'de.
- **Tarayıcı testi (CDP) tuzağı:** `cdp click "<metin>"` öğeyi görünür alana kaydırmaz;
  sayfa altındaki butonlarda (ör. "Sorgula") başarısız olur, başarılı görünür. Teşhis:
  dinleyici takıp `window.__t` dizisine bakmak. Geçici çözüm:
  `cdp eval "... b.scrollIntoView({block:'center'}); setTimeout(()=>b.click(),150)"`.
  Ayrıca emoji'li etiketlerde ("🔎 Sorgula") eşleşme daha da güvenilmez.

## Son commit'ler

```
83fcc10 gtip-kodlari: klasör düzeni, hafıza dosyaları, KDV boru hattı düzeltmesi ve tarayıcı testi
47f46d1 readme: Mega hesap adresi düzeltildi (gmail)
3e447d0 readme: GitHub-Mega dosya dağılımı belgelendi (büyük veri Mega'da)
b08231f uygulama: frontend bağımlılık kilidi eklendi
f3ceff9 gtip-kodlari: Türkiye ithalat/ihracat GTİP + vergi hesaplama sistemi
```
