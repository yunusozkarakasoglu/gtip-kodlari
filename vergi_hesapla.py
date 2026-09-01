#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""vergi_hesapla — GTİP + menşe ülke + CIF → tam vergi dökümü (Türkiye ithalatı).
Kullanım: python3 vergi_hesapla.py 840999000012 CN 10000
"""
import sqlite3, sys, os

DB = "/home/yunus/Masaüstü/gtip_kodlari/gtip_kodlari.db"

def ulke_grubu(cur, kod):
    r = cur.execute("SELECT igv_grup FROM ulke_gruplari WHERE ulke_kod=?", (kod.upper(),)).fetchone()
    return r[0] if r else "diger"

def vergi_hesapla(gtip12, menşe, cif):
    """
    Türkiye ithalatı toplam vergi hesabı.
    Girdi: gtip_12 (12 hane), menşe ülke ISO kodu (örn. CN=Çin, DE=Almanya), CIF değer (EUR)
    Dönüş: sözlük — vergi dökümü
    """
    con = sqlite3.connect(DB)
    cur = con.cursor()

    # 1) Ürün bilgisi
    urun = cur.execute("""SELECT gtip_12, cn_8, hs_6, aciklama_tr, aciklama_tr_4,
                                 aciklama_en, vergi_haddi, birim
                          FROM urun_kodlari WHERE gtip_12=?""", (gtip12,)).fetchone()
    if not urun:
        con.close()
        return {"hata": f"GTİP bulunamadı: {gtip12}"}

    # 2) İGV
    igv = cur.execute("SELECT * FROM igv WHERE gtip_12=?", (gtip12,)).fetchone()
    igv_cols = [d[0] for d in cur.description] if igv else []

    grup = ulke_grubu(cur, menşe)
    igv_oran = None
    if igv:
        col = {"ab":"oran_ab","kos":"oran_kos","sng":"oran_sng","vnz":"oran_vnz",
               "bae":"oran_bae","iran":"oran_iran","diger":"oran_diger"}.get(grup, "oran_diger")
        if col in igv_cols:
            igv_oran = igv[igv_cols.index(col)]
        # spesifik kolon yoksa D.Ü. fallback
        if igv_oran is None:
            igv_oran = igv[igv_cols.index("oran_diger")]

    # 3) Gümrük vergisi — menşeye göre
    # AB/Gümrük Birliği sanayi ürünleri → %0; diğer → İPGT haddi
    gv = 0.0
    gv_aciklama = ""
    try:
        ipgt_haddi = float(urun[6]) if urun[6] and urun[6].strip() else None
    except ValueError:
        ipgt_haddi = None
    if grup == "ab":
        gv = 0.0
        gv_aciklama = "AB/Gümrük Birliği menşeli sanayi ürünü → gümrük vergisi %0"
        if ipgt_haddi and ipgt_haddi > 0:
            gv_aciklama += f" (İPGT MFN haddi %{ipgt_haddi} — menşe kaynaklı muaf)"
    else:
        gv = ipgt_haddi or 0.0
        gv_aciklama = f"İPGT vergi haddi %{gv}" if ipgt_haddi else "İPGT'de vergi haddi belirtilmemiş"

    # 4) ÖTV kontrolü (tablo boşsa yok)
    otv = cur.execute("SELECT liste, oran FROM otv WHERE gtip_12=?", (gtip12,)).fetchone()

    # 5) KDV — genel %20 (indirimli liste eklenmemişse)
    kdv_oran = 0.20
    kdv_row = cur.execute("SELECT oran FROM kdv WHERE gtip_12=?", (gtip12,)).fetchone()
    if kdv_row:
        kdv_oran = kdv_row[0] / 100.0

    # 6) Hesaplar
    gv_tutar = cif * gv / 100.0
    igv_tutar = cif * (igv_oran or 0) / 100.0
    otv_tutar = 0.0
    otv_aciklama = None
    if otv:
        otv_aciklama = f"ÖTV ({otv[0]} sayılı liste): {otv[1]}"
    kdv_matrah = cif + gv_tutar + igv_tutar + otv_tutar
    kdv_tutar = kdv_matrah * kdv_oran
    toplam_vergi = gv_tutar + igv_tutar + otv_tutar + kdv_tutar
    toplam_maliyet = cif + toplam_vergi

    con.close()
    return {
        "gtip_12": gtip12,
        "urun_tr": urun[3],
        "urun_4": urun[4],
        "urun_en": urun[6 - 1],   # aciklama_en index 5
        "menşe": menşe.upper(),
        "igv_grubu": grup,
        "cif": cif,
        "gumruk_vergisi": {"oran": gv, "tutar": round(gv_tutar, 2), "aciklama": gv_aciklama},
        "igv": {"oran": igv_oran or 0, "tutar": round(igv_tutar, 2), "liste": igv[1] if igv else None},
        "otv": otv_aciklama,
        "kdv": {"oran": kdv_oran * 100, "tutar": round(kdv_tutar, 2), "matrah": round(kdv_matrah, 2)},
        "toplam_vergi": round(toplam_vergi, 2),
        "toplam_maliyet": round(toplam_maliyet, 2),
    }

def yazdir(s):
    if "hata" in s:
        print("❌", s["hata"])
        return
    print(f"=== {s['gtip_12']} | {s['urun_tr'][:50]} ===")
    print(f"  4-hane: {s['urun_4'][:70]}")
    print(f"  Menşe: {s['menşe']} → İGV grubu: {s['igv_grubu']}")
    print(f"  CIF: {s['cif']} EUR")
    print(f"  Gümrük vergisi: %{s['gumruk_vergisi']['oran']} → {s['gumruk_vergisi']['tutar']} EUR")
    print(f"  İGV: %{s['igv']['oran']} → {s['igv']['tutar']} EUR  (liste: {s['igv']['liste']})")
    if s["otv"]: print(f"  ÖTV: {s['otv']}")
    print(f"  KDV: %{s['kdv']['oran']} → {s['kdv']['tutar']} EUR (matrah {s['kdv']['matrah']})")
    print(f"  ─────────────────────────────")
    print(f"  TOPLAM VERGİ: {s['toplam_vergi']} EUR | TOPLAM MALİYET: {s['toplam_maliyet']} EUR")

if __name__ == "__main__":
    if len(sys.argv) >= 4:
        g = sys.argv[1]
        m = sys.argv[2]
        c = float(sys.argv[3])
        yazdir(vergi_hesapla(g, m, c))
    else:
        print("Kullanım: python3 vergi_hesapla.py <gtip_12> <menşe_ISO> <CIF_EUR>")
        print("Örnek:    python3 vergi_hesapla.py 840999000012 CN 10000")
