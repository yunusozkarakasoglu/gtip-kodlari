# Roadmaps.md — Global İlerleme (gtip_kodlari)

> Sprint + alt görev takibi. İşaretleme görev sonunda, kullanıcı onayından sonra yapılır.
> Güncel durum: **v2026.3** (İPGT 2026 + İGV Karar 3351/10791 + KDV GİB listeleri)

## Sprint 0 — Temel veri altyapısı ✅ (2026-09-01)

- [x] İPGT 2026 resmi Excel'lerinden 15.718 GTİP çıkarma (`scripts/ipgt_parse.py`)
- [x] EN açıklama + anahtar kelime eşlemesi (`veri/tariffnumber_en.json`)
- [x] SQLite ana tablo + FTS5 arama indeksi (`scripts/gtip_build_db3.py`)
- [x] CSV / JSON dışa aktarım (muhasebe entegrasyonu için)
- [x] Vergi hesaplama çekirdeği (`scripts/vergi_hesapla.py`)

## Sprint 1 — Vergi tabloları ve uygulama ✅ (2026-09-01)

- [x] İGV listeleri (EK-1/2/3) → `igv` tablosu (4.562 kayıt)
- [x] Ülke → İGV grubu eşlemesi (110 ülke + D.Ü. varsayılanı)
- [x] GİB KDV oranları PDF → `kdv` tablosu (I/II sayılı listeler)
- [x] FastAPI sorgulama API'si + React arayüzü (tek port 8899)
- [x] Yedekle / geri yükle / güncelle butonları
- [x] `veri_versiyon.json` ile sürüm takibi

## Sprint 2 — Proje düzeni ve hafıza ✅ (2026-09-15)

- [x] Klasör yapısını `scripts/ veri/ kaynak/ uygulama/ yedekler/` olarak ayır
- [x] Sabit yolları kaldır → `scripts/yollar.py` (tek kaynak)
- [x] 7 hafıza dosyasını oluştur (`AGENTS.md` … `README.md`)
- [x] KDV → DB yükleme adımını boru hattına ekle (**eksik adım bulundu ve düzeltildi**)
- [x] `kdv_parse.py`'yi PDF'ten metne çevirme adımıyla kendi kendine yeterli yap
- [x] Kullanılmayan şablon dosyalarını (hero.png, vite/react svg, icons.svg) temizle
- [x] Tüm boru hattı + API + React build + yedek/geri yükle uçtan uca test

## Sprint 2.5 — Çalışır hâle getirme + tarayıcı testi ✅ (2026-09-15)

- [x] 8899 portunu tutan sahipsiz süreci kapat, uygulamayı başlat
- [x] `favicon.svg` 404 hatasını düzelt (`dist/` mount)
- [x] Türkçe büyük harf hatası (`IHRACAT` → `İHRACAT`)
- [x] Gerçek tarayıcıda (CDP) 4 adımlı akış testi: ithalat + ihracat
- [x] Arayüzden "🔄 Güncelle" butonuyla tam boru hattı testi (versiyon 2026.2 → 2026.3)

## Sprint 3 — Veri doğruluğu ve tazeliği (sıradaki)

- [ ] **🔴 Gümrük vergisi oranı kaynağını doğrula** — `vergi_haddi` şu an İPGT'nin
  "474 sayılı Kanun kanuni haddi" sütunu; fiilen uygulanan oran (İthalat Rejimi Kararı
  ekleri) değil. Gerçek oranların eklenmesi OCR/ayrı veri kaynağı gerektirir. **Karar bekliyor.**

- [ ] **EN açıklama güncelleyici yaz** — `tariffnumber_en.json` statik bir anlık görüntü;
      `guncelle_ve_kur.sh` onu yenilemiyor (tek elle kalan veri parçası)
- [ ] **ÖTV listelerini doldur** — `otv` tablosu kurulu ama boş (GİB listeleri gerekli)
- [ ] **Anti-damping / ilave mali yükümlülük tablosu** — şu an tamamen kapsam dışı
- [ ] **TARIC 10 hane** eşlemesi (AB tarafı için) — isteğe bağlı

## Sprint 4 — Arayüz ve entegrasyon (aday)

- [ ] Toplu sorgu (Excel/CSV yükle → her satıra GTİP önerisi + vergi)
- [ ] Sonuçları PDF/Excel rapor olarak indir
- [ ] Arama kalitesi: eşanlamlı sözlüğünü (`ES_ANLAM` in `uygulama/sorgula_modulu.py`) genişlet
- [ ] React hata sınırı (ErrorBoundary) ekle — render hatasında arayüz boşalmasın
- [ ] `cdp.js` `click` komutuna `scrollIntoView` ekle (görünür alan dışı öğeler)
- [ ] Muhasebe programı için doğrudan DB bağlantı örneği/dokümanı
