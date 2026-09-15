# AGENTS.md — Proje Kuralları (gtip_kodlari)

> Bu dosya pi tarafından otomatik yüklenir. Göreve başlarken **önce burayı**, sonra
> `index.md`'yi oku. Kurallar global `~/.pi/agent/AGENTS.md` ile birlikte geçerlidir
> (görev akışı, kod mimarisi, arama protokolü, hafıza dosyaları orada tanımlıdır).

## Bu proje nedir (tek cümle)

GTİP / HS kodu **bulma + Türkiye ithalat vergisi hesaplama** uygulaması: resmi İPGT 2026
Excel'lerinden SQLite veritabanı üretir, FastAPI + React arayüzüyle çevrimdışı sorgular.

## Göreve başlarken okuma sırası

1. **AGENTS.md** (bu dosya) — kurallar
2. **index.md** — hangi özellik hangi dosyada, çalıştırma komutları, tuzaklar
3. İhtiyaca göre: `Tasks.md` (bekleyen işler) → `Roadmaps.md` (sprint) → `Project_info.md`
   (ne yapar, hangi sayfalar/akışlar) → `Mimari.md` (katmanlar, şema, bağımlılıklar)

## Projeye özel kurallar

- **Veriye dokunmadan önce yedek al.** `veri/gtip_kodlari.db` 49 MB ve scriptlerle
  yeniden üretilebilir; ama üretim ~2-3 dakika sürer. Test öncesi:
  `tar czf /tmp/gtip_yedek.tar.gz -C veri .`
- **Scriptler `veri/` klasörünü tek kaynaktan okur** — yollar `scripts/yollar.py`'de
  tanımlıdır. Sabit (hardcoded) mutlak yol **ekleme**; `yollar.py`'den import et.
- **Boru hattı sırası bozulmaz:** `ipgt_parse → igv_parse → gtip_build_db3 →
  kdv_parse → gtip_build_vergi`. `gtip_build_db3.py` DB'yi **siler ve yeniden kurar**;
  `vergi` tabloları (igv/kdv/ulke_gruplari/otv) ondan **sonra** kurulur. Sıra atlanırsa
  KDV/İGV verisi kaybolur.
- **KDV zinciri:** `kdv_parse.py` DB'deki GTİP listesini okuyup `veri/kdv_oranlari.json`
  üretir; `gtip_build_vergi.py` bu JSON'u `kdv` tablosuna **yükler**. İkisi ayrı adımdır.
- **Ağ erişimi** yalnız `guncelle*.sh` ve `tariffnumber_en.json` yenilemesinde gerekir;
  uygulama ve sorgulama tamamen çevrimdışıdır.
- **Vergi sonucu hukuki beyan değildir.** ÖTV/anti-damping/ilave mali yükümlülük kapsam
  dışıdır; arayüzde uyarı zorunludur (`uyari` alanı korunmalı).
- **Dosya boyutu:** bileşen/script ~200-300 satırı geçerse böl (`sorgula_modulu.py`
  şu an 265 satır — yeni özellik eklenirse önce bölme planı yap).
- Büyük dosyalar (DB, CSV, PDF, ZIP) **git'e girmez** — `.gitignore` + Mega dağılımı:
  README.md → "📦 Dosya Dağılımı". GitHub'a yalnız kod + küçük JSON gider.

## Hafıza dosyaları (bu klasörde)

`AGENTS.md` · `Roadmaps.md` · `Project_info.md` · `Tasks.md` · `Mimari.md` · `index.md` ·
`README.md` (dış okuyucuya proje tanıtımı — ayrı bir `Readme.md` yoktur).

Görev sonunda: kullanıcı **"tamam"** dedikten sonra `Tasks.md → Roadmaps.md → index.md →
diğerleri` sırasıyla güncelle, sonra commit + push.
