#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""İPGT 2026 (Ticaret Bakanlığı resmi TGTC) parser v2.
- Header/legend satırlarını atlar, devam satırlarını tireleme düzeltmesiyle birleştirir
- Hiyerarşi: fasıl → pozisyon → HS → CN → GTİP (12 hane)
- Açıklamaları temizler (baştaki tireler, fazla boşluklar)
"""
import xlrd, re, json, glob, os

KAYNAK = "/home/yunus/Masaüstü/gtip_kodlari/tgtc_2026/2026 TGTC/2026 TGTC"
OUT = "/home/yunus/Masaüstü/gtip_kodlari"

def temizle(s):
    """Baştaki tireleri/boşlukları temizle, iç boşlukları sadeleştir."""
    if not s:
        return ""
    s = re.sub(r'^[\s\-\u2013\u2014\.]+', '', s)   # baştaki - - . işaretleri
    s = re.sub(r'\s+', ' ', s).strip()
    return s

def vergi_temizle(v):
    """'100.0' → '100', '1.5' → '1.5', 'Oran yok' kalırsa kalsın."""
    v = v.strip()
    if v.endswith('.0') and v.count('.') == 1:
        v = v[:-2]
    return v

def oku_dosya(path):
    wb = xlrd.open_workbook(path)
    sh = wb.sheet_by_index(0)
    satirlar = []
    for r in range(sh.nrows):
        def hucre(c):
            return str(sh.cell_value(r, c)).strip() if c < sh.ncols else ""
        kod_raw, tanim, birim, vergi = hucre(0), hucre(1), hucre(2), hucre(3)
        kod = kod_raw.replace(".", "").replace(" ", "")
        if kod.isdigit() and len(kod) >= 4:
            satirlar.append([kod, [tanim], birim, vergi])
        elif kod.isdigit() and len(kod) <= 2 and r < 6:
            pass  # header/legend satırı (1 2 3.0 4.0)
        elif tanim:
            if satirlar:
                # tireleme düzeltmesi: "ka-" + "buk" → "kabuk"
                onceki = satirlar[-1][1]
                if onceki and onceki[-1].endswith("-") and not onceki[-1].endswith("--"):
                    onceki[-1] = onceki[-1][:-1]
                    onceki.append(tanim)
                else:
                    onceki.append(tanim)
    return satirlar

def main():
    tum = []
    for path in sorted(glob.glob(f"{KAYNAK}/*.xls")):
        satirlar = oku_dosya(path)
        katmanlar = {}
        for (kod, tanimlar, birim, vergi) in satirlar:
            l = len(kod)
            tanim = temizle(" ".join(t for t in tanimlar if t))
            for k in list(katmanlar.keys()):
                if k >= l:
                    del katmanlar[k]
            katmanlar[l] = (kod, tanim)
            if l == 12:
                tum.append({
                    "gtip": kod,
                    "aciklama_tr": tanim,
                    "aciklama_tr_6": katmanlar.get(6, ("", ""))[1],
                    "aciklama_tr_4": katmanlar.get(4, ("", ""))[1],
                    "aciklama_tr_2": katmanlar.get(2, ("", ""))[1],
                    "birim": birim,
                    "vergi_haddi": vergi_temizle(vergi),
                })
        print(f"  {os.path.basename(path)}: {sum(1 for s in satirlar if len(s[0])==12)} GTİP", flush=True)

    tum.sort(key=lambda x: x["gtip"])
    with open(f"{OUT}/ipgt_2026.json", "w", encoding="utf-8") as f:
        json.dump(tum, f, ensure_ascii=False, indent=1)
    print(f"\n✅ TOPLAM: {len(tum)} resmi 12 haneli GTİP (İPGT 2026)")
    print(f"📄 {OUT}/ipgt_2026.json")

if __name__ == "__main__":
    main()
