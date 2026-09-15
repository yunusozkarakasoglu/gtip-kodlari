#!/bin/bash
# ============================================================
# guncelle.sh — RESMİ KAYNAKLARI İNDİR (parse/DB kurmaz)
# Kaynaklar: ggm.ticaret.gov.tr (İPGT) + ithalat.ticaret.gov.tr (İGV)
# İndirilen yer: kaynak/
# Kullanım:  bash scripts/guncelle.sh
# Tam iş akışı (indir + parse + DB kur) için: bash scripts/guncelle_ve_kur.sh
# ============================================================
set -e
SCRIPTS="$(cd "$(dirname "$0")" && pwd)"
KOK="$(dirname "$SCRIPTS")"
KAYNAK="$KOK/kaynak"
mkdir -p "$KAYNAK"
cd "$KAYNAK"

echo "📁 Proje kökü: $KOK"
echo "📁 Arşiv:      $KAYNAK"
echo ""

# ---- 1) İPGT (Ticaret Bakanlığı — Türk Gümrük Tarife Cetveli) ----
echo "1️⃣  İPGT 2026 (TGTC) indiriliyor..."
curl -skL -A "Mozilla/5.0" \
  "https://ggm.ticaret.gov.tr/data/6954cea313b8762ee854542c/2026%20TGTC.zip" \
  -o tgtc_2026.zip
unzip -oq tgtc_2026.zip -d tgtc_2026/
echo "   ✅ kaynak/tgtc_2026.zip"

# ---- 2) İGV listeleri (İthalat Genel Müdürlüğü) ----
echo "2️⃣  İGV 2026 listeleri indiriliyor..."
curl -skL -A "Mozilla/5.0" \
  "https://ithalat.ticaret.gov.tr/data/69550ad713b8762ee85456f7/igv%202026.zip" \
  -o igv_2026.zip
unzip -oq igv_2026.zip -d igv_2026/
echo "   ✅ kaynak/igv_2026.zip"

# ---- 3) KDV oranları (GİB resmi PDF) ----
echo "3️⃣  KDV oranları (GİB) indiriliyor..."
curl -skL -A "Mozilla/5.0" \
  "https://cdn.gib.gov.tr/api/gibportal-file/file/getFileResources?objectKey=arsiv/yardim-kaynaklar/yararli-bilgiler/kdv-oranlari.pdf" \
  -o kdv_oranlari_gib.pdf
echo "   ✅ kaynak/kdv_oranlari_gib.pdf"

echo ""
echo "✅ İNDİRME TAMAM (kaynak/)"
echo ""
echo "Bu script yalnız İNDİRİR. Parse + DB kurmak için:"
echo "  bash scripts/guncelle_ve_kur.sh     (yedek + indir + parse + DB + versiyon)"
echo ""
echo "Manuel güncellenmesi gerekenler:"
echo "  • İGV listeleri  → ithalat.ticaret.gov.tr (yıl ortası güncellemeleri)"
echo "  • ÖTV listeleri  → gib.gov.tr"
echo "  • Anti-damping   → ithalat.ticaret.gov.tr (kapsam dışı, TARA teyidi önerilir)"
