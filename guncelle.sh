#!/bin/bash
# ============================================================
# GTİP / Vergi Veritabanı GÜNCELLEME SCRIPTİ
# Resmi kaynaklardan 2026 verilerini yeniden indirip DB'yi yeniler.
# Kullanım:  bash guncelle.sh
# ============================================================
set -e
cd "$(dirname "$0")"
KLASOR="$(pwd)"
echo "📁 Klasör: $KLASOR"
echo ""

# ---- 1) İPGT (Ticaret Bakanlığı — Türk Gümrük Tarife Cetveli) ----
echo "1️⃣  İPGT 2026 (TGTC) indiriliyor..."
curl -skL -A "Mozilla/5.0" \
  "https://ggm.ticaret.gov.tr/data/6954cea313b8762ee854542c/2026%20TGTC.zip" \
  -o tgtc_2026.zip
unzip -oq tgtc_2026.zip -d tgtc_2026/
echo "   ✅ tgtc_2026.zip"

# ---- 2) İGV listeleri (İthalat Genel Müdürlüğü) ----
echo "2️⃣  İGV 2026 listeleri indiriliyor..."
curl -skL -A "Mozilla/5.0" \
  "https://ithalat.ticaret.gov.tr/data/69550ad713b8762ee85456f7/igv%202026.zip" \
  -o igv_2026.zip
unzip -oq igv_2026.zip -d igv_2026/
echo "   ✅ igv_2026.zip"

# ---- 3) İthalat Rejimi Kararı (Resmî Gazete arşiv) ----
echo "3️⃣  İthalat Rejimi Kararı 10781 indiriliyor (referans)..."
curl -skL -A "Mozilla/5.0" \
  "https://www.resmigazete.gov.tr/eskiler/2025/12/20251230M1-2.pdf" \
  -o ithalat_rejimi_10781.pdf
echo "   ✅ ithalat_rejimi_10781.pdf"

echo ""
echo "✅ İNDİRME TAMAM"
echo ""
echo "NOT: Aşağıdaki dosyaları yıl bazlı güncellemeniz gerekir:"
echo "  • İGV listeleri  → ithalat.ticaret.gov.tr → duyurular (yıl ortası güncellemeleri)"
echo "  • KDV/ÖTV listeleri → gib.gov.tr (indirimli oranlar)"
echo "  • Anti-damping   → ithalat.ticaret.gov.tr → anti-damping önlemleri"
echo ""
echo "DB'yi yeniden inşa etmek için (mevcut verilerden):"
echo "  python3 ipgt_parse.py  (İPGT Excel → JSON)"
echo "  python3 igv_parse.py   (İGV Excel → JSON)"
echo "  python3 gtip_build_db3.py + gtip_build_vergi.py (JSON → SQLite)"
