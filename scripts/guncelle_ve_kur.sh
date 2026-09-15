#!/bin/bash
# ============================================================
# guncelle_ve_kur.sh — TAM GÜNCELLEME + YENİDEN KURMA
#   1) Yedek al (mevcut veri korunur)
#   2) Resmi kaynakları indir (kaynak/): İPGT + İGV + KDV PDF
#   3) Excel/PDF → JSON parse (veri/)
#   4) SQLite DB'yi yeniden kur (veri/gtip_kodlari.db)
#   5) Versiyon güncelle (veri/veri_versiyon.json)
# Kullanım:  bash scripts/guncelle_ve_kur.sh
# ============================================================
set -e
SCRIPTS="$(cd "$(dirname "$0")" && pwd)"
KOK="$(dirname "$SCRIPTS")"
KAYNAK="$KOK/kaynak"
VERI="$KOK/veri"
LOG="$KOK/guncelleme_log.txt"
mkdir -p "$KAYNAK" "$VERI" "$KOK/yedekler"

log() { echo "$1" | tee -a "$LOG"; }
log "=============================================="
log "GÜNCELLEME BAŞLADI: $(date '+%Y-%m-%d %H:%M:%S')"

command -v pdftotext >/dev/null || log "⚠ pdftotext yok — KDV PDF metne çevrilemez (sudo apt install poppler-utils)"

# ---- 0) Yedek ----
log "[1/7] Mevcut veri yedekleniyor..."
DAMGA=$(date '+%Y%m%d_%H%M%S')
ESKI_VERSIYON=$(python3 -c "import json;print(json.load(open('$VERI/veri_versiyon.json'))['versiyon'])" 2>/dev/null || echo "x")
tar czf "$KOK/yedekler/veri_${ESKI_VERSIYON}_${DAMGA}.tar.gz" -C "$VERI" \
  gtip_kodlari.db urun_kodlari.csv urun_kodlari.json ipgt_2026.json igv_2026.json veri_versiyon.json 2>/dev/null || true
log "    Yedek: yedekler/veri_${ESKI_VERSIYON}_${DAMGA}.tar.gz"

# ---- 1) İPGT ----
log "[2/7] İPGT 2026 indiriliyor..."
curl -skL -A "Mozilla/5.0" \
  "https://ggm.ticaret.gov.tr/data/6954cea313b8762ee854542c/2026%20TGTC.zip" \
  -o "$KAYNAK/tgtc_2026.zip"
unzip -oq "$KAYNAK/tgtc_2026.zip" -d "$KAYNAK/tgtc_2026/" 2>/dev/null || true

# ---- 2) İGV ----
log "[3/7] İGV 2026 indiriliyor..."
curl -skL -A "Mozilla/5.0" \
  "https://ithalat.ticaret.gov.tr/data/69550ad713b8762ee85456f7/igv%202026.zip" \
  -o "$KAYNAK/igv_2026.zip"
unzip -oq "$KAYNAK/igv_2026.zip" -d "$KAYNAK/igv_2026/" 2>/dev/null || true

# ---- 3) Parse: İPGT + İGV ----
log "[4/7] Excel → JSON parse (İPGT + İGV)..."
python3 "$SCRIPTS/ipgt_parse.py" >> "$LOG" 2>&1
python3 "$SCRIPTS/igv_parse.py"  >> "$LOG" 2>&1

# ---- 4) DB kur ----
log "[5/7] SQLite veritabanı kuruluyor (urun_kodlari + FTS5)..."
python3 "$SCRIPTS/gtip_build_db3.py" >> "$LOG" 2>&1

# ---- 4.5) KDV oranları (GİB PDF → JSON, taze DB'deki GTİP listesine göre) ----
log "[5/7] KDV oranları (GİB PDF) parse ediliyor..."
curl -skL -A "Mozilla/5.0" \
  "https://cdn.gib.gov.tr/api/gibportal-file/file/getFileResources?objectKey=arsiv/yardim-kaynaklar/yararli-bilgiler/kdv-oranlari.pdf" \
  -o "$KAYNAK/kdv_oranlari_gib.pdf"
rm -f /tmp/kdv_gib.txt          # PDF her seferinde yeniden metne çevrilsin
python3 "$SCRIPTS/kdv_parse.py" >> "$LOG" 2>&1

# ---- 4.6) Vergi tabloları (igv + ulke_gruplari + kdv + otv) ----
log "[5/7] Vergi tabloları kuruluyor (igv/ulke_gruplari/kdv/otv)..."
python3 "$SCRIPTS/gtip_build_vergi.py" >> "$LOG" 2>&1

# ---- 5) Versiyon ----
log "[6/7] Versiyon güncelleniyor..."
YIL=$(date '+%Y')
python3 - "$YIL" "$VERI/veri_versiyon.json" <<'PY' >> "$LOG" 2>&1
import json, sys, time
yil, yol = sys.argv[1], sys.argv[2]
v = json.load(open(yol, encoding="utf-8"))
if str(v.get("yil")) != str(yil):
    v["versiyon"] = f"{yil}.1"
    v["yil"] = int(yil)
else:
    parca = v["versiyon"].split(".")
    v["versiyon"] = f"{parca[0]}.{int(parca[1])+1}"
v["guncellenme"] = time.strftime("%Y-%m-%d %H:%M")
json.dump(v, open(yol, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print(f"Yeni versiyon: {v['versiyon']}")
PY

log "[7/7] TAMAM: $(date '+%H:%M:%S') — veri güncel ✓"
