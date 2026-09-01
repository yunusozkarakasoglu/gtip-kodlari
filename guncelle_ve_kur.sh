#!/bin/bash
# ============================================================
# guncelle_ve_kur.sh — TAM GÜNCELLEME + YENİDEN KURMA
# 1) Yedek al (mevcut veri korunur)
# 2) Resmi kaynakları yeniden indir (İPGT + İGV + Kararlar)
# 3) Excel'leri parse et → JSON
# 4) SQLite DB'yi yeniden kur (urun_kodlari + igv + ulke_gruplari)
# 5) CSV/JSON dışa aktar + versiyon güncelle
# ============================================================
set -e
cd "$(dirname "$0")"
KLASOR="$(pwd)"
LOG="guncelleme_log.txt"

log() { echo "$1" | tee -a "$LOG"; }
log "=============================================="
log "GÜNCELLEME BAŞLADI: $(date '+%Y-%m-%d %H:%M:%S')"

# ---- 0) Yedek ----
log "[1/7] Mevcut veri yedekleniyor..."
mkdir -p yedekler
DAMGA=$(date '+%Y%m%d_%H%M%S')
ESKI_VERSIYON=$(python3 -c "import json;print(json.load(open('veri_versiyon.json'))['versiyon'])" 2>/dev/null || echo "x")
tar czf "yedekler/veri_${ESKI_VERSIYON}_${DAMGA}.tar.gz" \
  gtip_kodlari.db urun_kodlari.csv urun_kodlari.json ipgt_2026.json igv_2026.json veri_versiyon.json 2>/dev/null || true
log "    Yedek: yedekler/veri_${ESKI_VERSIYON}_${DAMGA}.tar.gz"

# ---- 1) İPGT ----
log "[2/7] İPGT 2026 indiriliyor..."
curl -skL -A "Mozilla/5.0" \
  "https://ggm.ticaret.gov.tr/data/6954cea313b8762ee854542c/2026%20TGTC.zip" \
  -o tgtc_2026.zip
unzip -oq tgtc_2026.zip -d tgtc_2026/ 2>/dev/null || true

# ---- 2) İGV ----
log "[3/7] İGV 2026 indiriliyor..."
curl -skL -A "Mozilla/5.0" \
  "https://ithalat.ticaret.gov.tr/data/69550ad713b8762ee85456f7/igv%202026.zip" \
  -o igv_2026.zip
unzip -oq igv_2026.zip -d igv_2026/ 2>/dev/null || true

# ---- 3) Parse ----
log "[4/7] Excel → JSON parse..."
python3 ipgt_parse.py >> "$LOG" 2>&1
python3 igv_parse.py >> "$LOG" 2>&1

# ---- 3.5) KDV oranları (GİB) ----
log "[4/7] KDV oranları indiriliyor (GİB)..."
curl -skL -A "Mozilla/5.0" \
  "https://cdn.gib.gov.tr/api/gibportal-file/file/getFileResources?objectKey=arsiv/yardim-kaynaklar/yararli-bilgiler/kdv-oranlari.pdf" \
  -o kdv_oranlari_gib.pdf
python3 kdv_parse.py >> "$LOG" 2>&1

# ---- 4) DB kur ----
log "[5/7] SQLite veritabanı kuruluyor..."
python3 gtip_build_db3.py >> "$LOG" 2>&1
python3 gtip_build_vergi.py >> "$LOG" 2>&1

# ---- 5) Versiyon ----
log "[6/7] Versiyon güncelleniyor..."
YIL=$(date '+%Y')
python3 - "$YIL" <<'PY' >> "$LOG" 2>&1
import json, sys, time
v = json.load(open("veri_versiyon.json"))
yil = sys.argv[1]
# yıl değiştiyse versiyon artır
if str(v.get("yil")) != str(yil):
    base = v["versiyon"].split(".")[0]
    v["versiyon"] = f"{yil}.1"
    v["yil"] = int(yil)
else:
    parca = v["versiyon"].split(".")
    v["versiyon"] = f"{parca[0]}.{int(parca[1])+1}"
v["guncellenme"] = time.strftime("%Y-%m-%d %H:%M")
json.dump(v, open("veri_versiyon.json", "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print(f"Yeni versiyon: {v['versiyon']}")
PY

log "[7/7] TAMAM: $(date '+%H:%M:%S') — veri güncel ✓"
