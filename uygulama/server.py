#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""server.py — GTİP / Vergi Sorgulama API'si (FastAPI, tamamen çevrimdışı).
Çalıştırma:  cd uygulama && uvicorn server:app --port 8899
"""
import os, sys, json, subprocess, shutil, time, glob
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sorgula_modulu import (ara_urun, gtip_bilgi, ulke_listesi, ulke_grubu,
                            hesapla_ithalat, hesapla_ihracat, sorgula)

KLASOR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VERSIYON_DOSYA = os.path.join(KLASOR, "veri_versiyon.json")

app = FastAPI(title="GTİP / Vergi Sorgulama", version="1.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# React build çıktısını statik sun (index.html fallback)
ON = os.path.dirname(os.path.abspath(__file__))
DIST = os.path.join(ON, "frontend", "dist")
if os.path.exists(os.path.join(DIST, "index.html")):
    app.mount("/assets", StaticFiles(directory=os.path.join(DIST, "assets")), name="assets")
    @app.get("/")
    def anasayfa():
        from fastapi.responses import HTMLResponse
        return HTMLResponse(open(os.path.join(DIST, "index.html"), encoding="utf-8").read())

# ---------- Modeller ----------
class SorguIstek(BaseModel):
    urun: str
    ulke: str
    hareket: str          # ithalat / ihracat
    cif: float = 10000
    gtip_12: Optional[str] = None   # kullanıcı aday seçerse

# ---------- Yardımcılar ----------
def versiyon_oku():
    if os.path.exists(VERSIYON_DOSYA):
        try:
            return json.load(open(VERSIYON_DOSYA, encoding="utf-8"))
        except Exception:
            pass
    return {"versiyon": "bilinmiyor", "kaynaklar": {}}

# ---------- API ----------
@app.get("/api/durum")
def durum():
    v = versiyon_oku()
    db = os.path.join(KLASOR, "gtip_kodlari.db")
    import sqlite3
    con = sqlite3.connect(db)
    n = con.execute("SELECT COUNT(*) FROM urun_kodlari").fetchone()[0]
    igv = con.execute("SELECT COUNT(*) FROM igv").fetchone()[0]
    con.close()
    return {
        "cevrimdisi": True,
        "veri_yolu": KLASOR,
        "urun_kodlari": n, "igv": igv,
        "versiyon": v,
    }

@app.get("/api/ara")
def ara(q: str, limit: int = 15):
    return {"sonuclar": ara_urun(q, limit=limit)}

@app.get("/api/ulkeler")
def ulkeler():
    return {"ulkeler": ulke_listesi()}

@app.get("/api/gtip/{kod}")
def gtip(kod: str):
    u = gtip_bilgi(kod)
    if not u:
        return {"hata": f"GTİP bulunamadı: {kod}"}
    return u

@app.post("/api/sorgula")
def is_akisi(istek: SorguIstek):
    """GÖREV AKIŞI: ürün → ülke → hareket → sorgula → rapor"""
    if istek.gtip_12:
        # kullanıcı aday seçti — doğrudan hesapla
        if istek.hareket.lower() in ("ithalat", "i"):
            r = hesapla_ithalat(istek.gtip_12, istek.ulke, istek.cif)
        else:
            r = hesapla_ihracat(istek.gtip_12, istek.ulke)
        return {"adaylar": [], "secim": gtip_bilgi(istek.gtip_12), "rapor": r}
    return sorgula(istek.urun, istek.ulke, istek.hareket, istek.cif)

# ---------- Güncelleme / Versiyonlama ----------
@app.post("/api/guncelle")
def guncelle():
    """Kaynakları yeniden indirip DB'yi yeniden kurar (arka planda script)."""
    script = os.path.join(KLASOR, "guncelle_ve_kur.sh")
    log = os.path.join(KLASOR, "guncelleme_log.txt")
    subprocess.Popen(["bash", script], stdout=open(log, "w"), stderr=subprocess.STDOUT)
    return {"durum": "basladi", "log": log}

@app.get("/api/guncelle/durum")
def guncelle_durum():
    log = os.path.join(KLASOR, "guncelleme_log.txt")
    son = ""
    if os.path.exists(log):
        son = open(log, encoding="utf-8", errors="ignore").read()[-1500:]
    v = versiyon_oku()
    return {"log": son, "versiyon": v}

@app.post("/api/yedekle")
def yedekle():
    """Mevcut veriyi versiyonlu yedek alır."""
    yedek_klasor = os.path.join(KLASOR, "yedekler")
    os.makedirs(yedek_klasor, exist_ok=True)
    v = versiyon_oku()
    damga = time.strftime("%Y%m%d_%H%M%S")
    isim = f"veri_{v.get('versiyon', 'x')}_{damga}.tar.gz"
    hedef = os.path.join(yedek_klasor, isim)
    # kritik dosyalar
    dosyalar = ["gtip_kodlari.db", "urun_kodlari.csv", "urun_kodlari.json",
                "ipgt_2026.json", "igv_2026.json", "veri_versiyon.json"]
    mevcut = [d for d in dosyalar if os.path.exists(os.path.join(KLASOR, d))]
    with tar_open(hedef, "w:gz") as t:
        for d in mevcut:
            t.add(os.path.join(KLASOR, d), arcname=d)
    return {"yedek": hedef, "dosyalar": len(mevcut)}

@app.get("/api/yedekler")
def yedekler_listele():
    yedek_klasor = os.path.join(KLASOR, "yedekler")
    os.makedirs(yedek_klasor, exist_ok=True)
    liste = sorted(glob.glob(os.path.join(yedek_klasor, "*.tar.gz")), reverse=True)
    return {"yedekler": [os.path.basename(p) for p in liste]}

@app.post("/api/geri_yukle/{isim}")
def geri_yukle(isim: str):
    """Belirtilen yedeği geri yükler (DB + JSON + versiyon)."""
    yol = os.path.join(KLASOR, "yedekler", isim)
    if not os.path.exists(yol):
        return {"hata": f"Yedek bulunamadı: {isim}"}
    import tarfile
    with tarfile.open(yol, "r:gz") as t:
        t.extractall(KLASOR)
    return {"durum": "geri yuklendi", "yedek": isim}

def tar_open(*a, **k):
    import tarfile
    return tarfile.open(*a, **k)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8899)
