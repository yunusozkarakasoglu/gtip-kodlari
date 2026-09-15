# Tasks.md — Görev Takibi

> Yeni görev önce buraya eklenir, sonra uygulanır. Birleşik işlerde "Ana > Alt" biçimi.
> Onay bekleyenler `[ ]`, tamamlananlar `[x]`.

## Sıradaki görevler

- [ ] **[2026-09-15 09:00] 🔴 YÜKSEK ÖNCELİK: Gümrük vergisi oranı kaynağını doğrula** —
  `urun_kodlari.vergi_haddi`, İPGT'nin **"474 VERGİ HADDİ"** sütunundan gelir (kaynak dosyanın
  kendi açıklaması: *14.05.1964 tarih ve 474 sayılı Kanun ile tespit edilen vergi hadleri*).
  Yani **fiilen uygulanan oran değil, kanuni had**. Dağılım: %50 (2.540), %25 (1.660),
  %100 (1.567), %30 (1.412) …; otomobil/telefonda boş. Karar: (a) fiilen uygulanan oranlar
  İthalat Rejimi Kararı eklerinden çıkarılıp ayrı kolon/tablo olarak mı eklensin
  (PDF'ler taranmış → OCR gerekir), (b) arayüzde uyarı metni mi güncellensin, (c) ikisi?
  Şu an arayüz "Gümrük vergisi %100" gibi kanuni haddi gösteriyor — kullanıcı onayı bekliyor.
- [ ] **[2026-09-15 09:00] cdp aracı: `click` kaydırma yapmıyor** — görünür alan dışındaki
  öğelerde (ör. sayfa altındaki "Sorgula") `cdp click` hedefi bulamayıp html'e tıklıyor;
  `cdp.js` içindeki click ifadesine `el.scrollIntoView({block:'center'})` eklenmeli.
- [ ] **[2026-09-15 09:00] React hata sınırı (error boundary) yok** — herhangi bir render
  hatasında tüm arayüz boşalıyor (`#root` boş kalır). `App.jsx`'e basit bir ErrorBoundary
  eklensin (testte DOM'a elle müdahale sonrası gözlendi).
- [ ] **[2026-09-15 08:45] EN açıklama güncelleyicisi** — `tariffnumber_en.json` statik;
  `guncelle_ve_kur.sh` onu yenilemiyor. Kazıma scripti yazılıp boru hattına eklenmeli.
- [ ] **[2026-09-15 08:45] ÖTV listelerini doldur** — `otv` tablosu kurulu, kayıt yok.
- [ ] **[2026-09-15 08:45] Anti-damping tablosu** — kapsam dışı; TB önlem listesi gerekli.
- [ ] **[2026-09-15 09:00] Arama kalitesi** — "ceviz" sorgusunda ilk aday "Brezilya cevizi /
  Fresh coconut" (080119000000) geliyor; anahtar kelime ağırlıkları (`anahtar_en` +10)
  gözden geçirilmeli. Ayrıca `toLocaleUpperCase` düzeltmesi sonrası reload doğrulandı.

## Tamamlanan görevler

- [x] **[2026-09-01 07:00] Veri altyapısı > İPGT 2026 parse** — 15.718 GTİP (`scripts/ipgt_parse.py`)
- [x] **[2026-09-01 07:23] Veri altyapısı > EN açıklama eşlemesi** — 15.704 kod (%99,9)
- [x] **[2026-09-01 10:28] Veri altyapısı > İGV parse** — EK-1/2/3 → 4.562 kayıt
- [x] **[2026-09-01 10:40] DB > Ana tablo + FTS5** — `scripts/gtip_build_db3.py`
- [x] **[2026-09-01 11:00] DB > Vergi tabloları** — igv, ulke_gruplari, kdv, otv
- [x] **[2026-09-01 11:13] Uygulama > FastAPI + React arayüzü** — port 8899, 4 adımlı akış
- [x] **[2026-09-01 11:48] Dokümantasyon > README + Mega/GitHub dağılımı**
- [x] **[2026-09-15 08:39] Düzen > Klasör yapısı** — `scripts/ veri/ kaynak/ uygulama/ yedekler/`
- [x] **[2026-09-15 08:40] Düzen > Sabit yollar > `scripts/yollar.py`** — 8 dosyadaki
  hardcoded `/home/yunus/...` yolları kaldırıldı
- [x] **[2026-09-15 08:41] Hata > KDV verisi DB'ye yüklenmiyordu** — `gtip_build_vergi.py`
  artık `veri/kdv_oranlari.json`'u `kdv` tablosuna yüklüyor (5.281 → 15.718 kayıt)
- [x] **[2026-09-15 08:41] Hata > `kdv_parse.py` kendi kendine yeterli değildi** — PDF→metin
  çevrimi (`pdftotext -layout`) script içine alındı
- [x] **[2026-09-15 08:42] Düzen > Boru hattı sırası düzeltildi** — `gtip_build_db3` sonrası
  `kdv_parse` → `gtip_build_vergi` (eskiden KDV JSON üretiliyor ama yüklenmiyordu)
- [x] **[2026-09-15 08:43] Temizlik > Kullanılmayan şablon dosyaları silindi**
  (hero.png, react.svg, vite.svg, icons.svg, frontend/README.md)
- [x] **[2026-09-15 08:44] Hafıza > 7 dosya oluşturuldu** — AGENTS, Roadmaps, Project_info,
  Tasks, Mimari, index, README
- [x] **[2026-09-15 08:45] Test > Uçtan uca doğrulama** — parse → DB → KDV → API (durum/ara/
  ulkeler/sorgula) → React bundle (HTTP 200) → yedekle → geri yükle → CLI araçları
- [x] **[2026-09-15 08:52] Çalıştırma > 8899 portu serbest bırakıldı** — 13 Eyl'den kalan
  sahipsiz `python3 -m http.server 8899` (pid 2981626, ebeveyn=init, bağlantı yok) kapatıldı;
  `uygulama/baslat.sh` ile uygulama başlatıldı (pid dosyası yok, setsid ile)
- [x] **[2026-09-15 08:52] Hata > `favicon.svg` 404** — `server.py` yalnız `/assets` mount
  ediyordu; `dist/` tamamı en sonda `/` mount edildi (API uçlarını gölgelemez)
- [x] **[2026-09-15 08:53] Hata > Türkçe büyük harf** — `App.jsx` rozeti "IHRACAT" yazıyordu
  (`toUpperCase()`); `toLocaleUpperCase('tr-TR')` → "İHRACAT", frontend yeniden derlendi
- [x] **[2026-09-15 08:54] Test > Gerçek tarayıcı (CDP) ile 4 adımlı akış** — arama (15 aday),
  seçim, ülke/hareket/CIF, ithalat raporu (piston CN: 7.640 €), ihracat raporu (4 not),
  DE ithalat (kahve: GV %0, KDV %1 → 50 €)
- [x] **[2026-09-15 08:54] Test > Arayüzden "🔄 Güncelle" butonu** — indirme → parse → DB →
  vergi tabloları → KDV → versiyon 2026.2 → **2026.3** (18 sn), sonrasında sayfa otomatik
  yenilendi, sorgular çalıştı, DB sayıları korundu (15.718 / 4.562 / 15.718)
- [x] **[2026-09-15 09:00] İnceleme > `vergi_haddi` semantiği** — kaynağın kendi açıklaması
  bulundu (474 sayılı Kanun kanuni haddi); README'ye uyarı bloğu eklendi, açık iş olarak kayda geçti
