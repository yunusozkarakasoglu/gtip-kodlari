#!/bin/bash
# ============================================================
# baslat.sh — GTİP / Vergi Sorgulama UYGULAMASI (çevrimdışı)
# Backend (FastAPI) + React arayüzü tek portta (8899)
# Aç: http://127.0.0.1:8899
# ============================================================
cd "$(dirname "$0")"

# 1) Frontend build (ilk kurulumda / değişiklik sonrası)
if [ ! -d "frontend/dist" ] || [ "$1" == "--build" ]; then
  echo "📦 Frontend derleniyor..."
  (cd frontend && npm install --silent && npm run build) || { echo "❌ build hatası"; exit 1; }
fi

# 2) Backend başlat (FastAPI + statik sunum)
echo "🚀 Uygulama başlatılıyor: http://127.0.0.1:8899"
pkill -f "uvicorn server:app" 2>/dev/null
sleep 1
exec python3 -m uvicorn server:app --host 127.0.0.1 --port 8899
