#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""kdv_parse.py — GİB resmi KDV Oranları PDF'inden (I)/(II) sayılı listeleri parse eder.
Her maddenin GTİP referanslarını (fasıl/pozisyon/12-hane) + hariçleri çıkarır,
veritabanındaki her GTİP için KDV oranını belirler: %1 (I), %10 (II), %20 (genel).
Çıktı: Masaüstü/gtip_kodlari/kdv_oranlari.json  (liste: [ {gtip_12, oran, kaynak} ])
"""
import re, json, os, sqlite3

OUT = "/home/yunus/Masaüstü/gtip_kodlari"
PDF_TXT = "/tmp/kdv_gib.txt"

def madde_bol(metin):
    """Numaralı maddeleri (1-, 2-, ...) ayır. Ayrıca a), b), c) alt maddeleri içeride kalır."""
    maddeler = re.split(r'\n\s*(\d{1,2})-\s*', metin)
    sonuc = []
    # maddeler[0] = ön kısım; sonra (no, metin) çiftleri
    for i in range(1, len(maddeler), 2):
        if i + 1 < len(maddeler):
            sonuc.append((int(maddeler[i]), maddeler[i+1]))
    return sonuc

def kod_referanslari(metin):
    """Bir madde metninden GTİP referanslarını çıkar.
    Dönüş: {ekle: [ (tip, kod) ], haric: [kod12], haric_poz: [poz4], kismi: bool}
    """
    ekle, haric, haric_poz, kismi = [], [], [], False
    parantezler = re.findall(r'\((.*?)\)', metin)
    kismi = ('yalnız' in metin or 'yaln\u0131z' in metin or 'sadece' in metin
             or 'kullanılmış' in metin or 'kullanilmis' in metin)

    # 12 haneli kodlar (ana metinde, hariç parantezleri hariç)
    ana_metin = re.sub(r'\([^)]*\)', ' ', metin)
    for m in re.finditer(r'(\d{2})\.(\d{2})\.(\d{2})\.(\d{2})\.(\d{2})\.(\d{2})', ana_metin):
        ekle.append(('kod', m.group(1)+m.group(2)+m.group(3)+m.group(4)+m.group(5)+m.group(6)))

    # hariç parantezlerindeki 12 haneli kodlar → hariç
    for p in parantezler:
        for m in re.finditer(r'(\d{2})\.(\d{2})\.(\d{2})\.(\d{2})\.(\d{2})\.(\d{2})', p):
            haric.append(m.group(1)+m.group(2)+m.group(3)+m.group(4)+m.group(5)+m.group(6))
        # hariç parantezindeki pozisyonlar: "85.17 pozisyonunda yer alan mallar hariç"
        for m in re.finditer(r'(\d{2})\.(\d{2}) pozisyon', p):
            haric_poz.append(m.group(1)+m.group(2))

    # pozisyonlar (ana metin, hariç kısmı hariç)
    for m in re.finditer(r'(\d{2})\.(\d{2}) pozisyon', ana_metin):
        ekle.append(('pozisyon', m.group(1)+m.group(2)))
    # virgülle ayrılmış pozisyon listeleri
    for m in re.finditer(r'((?:\d{2}\.\d{2},?\s*)+)pozisyonlar', ana_metin):
        for p in re.finditer(r'(\d{2})\.(\d{2})', m.group(1)):
            ekle.append(('pozisyon', p.group(1)+p.group(2)))

    # fasıllar
    for m in re.finditer(r'(\d{1,2}) no\.lu fasl[ıi](?:nd[ıa])?', ana_metin):
        ekle.append(('fasil', f"{int(m.group(1)):02d}"))

    return {"ekle": ekle, "haric": haric, "haric_poz": haric_poz, "kismi": kismi}

def main():
    txt = open(PDF_TXT, encoding='utf-8', errors='ignore').read()
    i1 = txt.find('(I) SAYILI LİSTE')
    i2 = txt.find('(II) SAYILI LİSTE')
    i3 = txt.find('(II) SAYILI LİSTE', i2 + 1)
    liste1_txt = txt[i1:i2]
    liste2_txt = txt[i2:(i3 if i3 > i2 else len(txt))]

    # II sayılı TANIMLAYICI maddelerin fasıl eşlemeleri (GTİP referansı vermeyenler)
    # [3] iplikler → 50-56, [4] mensucat → 50-60, [5] giyim → 61-63, [7] ayakkabı → 64,
    # [6] deri → 41-43, [8] çanta → 4202, [9] halı → 57, [13] kağıt → 4801-4802, [14] kitap → 49
    II_FASILLAR = [41, 42, 43, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64]
    # hariç tutulacak spesifik kodlar (ör. "hariç" geçen tanımlayıcı maddelerdeki istisnalar)

    # DB'deki tüm GTİP'ler
    con = sqlite3.connect(f"{OUT}/gtip_kodlari.db")
    gtipler = [r[0] for r in con.execute("SELECT gtip_12 FROM urun_kodlari")]
    con.close()

    oranlar = {}
    kismi_kayitlar = {}

    def uygula(maddeler, oran, fasil_ekle=None):
        for no, metin in maddeler:
            ref = kod_referanslari(metin)
            haric_set = set(ref['haric'])
            haric_poz_set = set(ref['haric_poz'])
            for tip, kod in ref['ekle']:
                if tip == 'fasil':
                    aday = [g for g in gtipler if g.startswith(kod)]
                elif tip == 'pozisyon':
                    if kod in haric_poz_set:
                        continue
                    aday = [g for g in gtipler if g.startswith(kod)]
                else:
                    aday = [kod] if kod in gtipler else []
                for g in aday:
                    if g in haric_set:
                        continue
                    if ref['kismi']:
                        kismi_kayitlar[g] = kismi_kayitlar.get(g, set()) | {no}
                    oranlar[g] = oran
            # tanımlayıcı madde için fasıl eklemesi
            if fasil_ekle and no in fasil_ekle and not ref['kismi']:
                for f in fasil_ekle[no]:
                    for g in [x for x in gtipler if x.startswith(f"{f:02d}")]:
                        if g not in haric_set:
                            oranlar[g] = oran

    uygula(madde_bol(liste1_txt), 1)
    uygula(madde_bol(liste2_txt), 10, fasil_ekle={
        3: II_FASILLAR,          # iplikler
        4: II_FASILLAR,          # mensucat
        5: [61, 62, 63],         # giyim eşyası (tekstil)
        6: [41, 42, 43],         # deri ve giyim
        7: [64],                 # ayakkabı
        9: [57],                 # halılar
        13: [48],                # gazete/baskı kağıdı
        14: [49],                # kitap
    })
    # 4202 (çanta/bavul) ve 9603.21 (diş fırçası) — pozisyon bazlı eklemeler
    for g in gtipler:
        if g.startswith('4202') and 8 in [m[0] for m in madde_bol(liste2_txt)]:
            oranlar[g] = 10
        if g.startswith('960321'):
            oranlar[g] = 10

    # MADDE 1(3) kuralı: I sayılı GIDA maddelerinden ÖTV'ye tabi olanlar → %10
    # (alkol 22, tütün 24, akaryakıt 27, taşıt 87 — ÖTV kapsamı)
    for g in gtipler:
        if oranlar.get(g) == 1 and g[:2] in ('22', '24', '27', '87'):
            oranlar[g] = 10
            kismi_kayitlar[g] = kismi_kayitlar.get(g, set()) | {999}

    # sonuçları kaydet
    sonuc = []
    for g in gtipler:
        o = oranlar.get(g, 20)
        k = sorted(kismi_kayitlar.get(g, []))
        sonuc.append({"gtip_12": g, "oran": o,
                      "kismi": k if k else None,
                      "kaynak": "I sayılı (GİB)" if o == 1 else ("II sayılı (GİB)" if o == 10 else "genel %20")})
    with open(f"{OUT}/kdv_oranlari.json", "w", encoding="utf-8") as f:
        json.dump(sonuc, f, ensure_ascii=False, indent=1)

    # istatistik
    from collections import Counter
    c = Counter(x['oran'] for x in sonuc)
    kismi_sayi = sum(1 for x in sonuc if x['kismi'])
    print(f"✅ {len(sonuc)} GTİP")
    print(f"   %1: {c.get(1,0)} | %10: {c.get(10,0)} | %20: {c.get(20,0)}")
    print(f"   kısmi (yalnız/sadece) işaretli: {kismi_sayi}")
    # örnekler
    for g in ['040120110000', '610910000000', '090121000000', '840999000012']:
        for x in sonuc:
            if x['gtip_12'] == g:
                print(f"   örnek {g}: %{x['oran']} {x['kaynak']}")
                break
    print(f"📄 {OUT}/kdv_oranlari.json")

if __name__ == "__main__":
    main()
