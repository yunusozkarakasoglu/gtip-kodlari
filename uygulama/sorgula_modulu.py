#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""sorgula_modulu.py — GÖREV AKIŞI ÇEKİRDEĞİ
1) ürün sorgusu → GTİP adayları
2) ülke seçimi (ISO)
3) hareket tipi: ithalat / ihracat
4) sorgula → tam rapor (tamamen çevrimdışı, yerel SQLite)
"""
import sqlite3, os, json, unicodedata, re

DB = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "gtip_kodlari.db")

def _baglan():
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    return con

def normalize(s):
    """Türkçe arama normalizasyonu: TİŞÖRTLER → tisortler"""
    if not s:
        return ""
    s = s.replace("İ", "i").replace("I", "i")
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode("ascii").lower()
    for a, b in [("ı","i"),("ş","s"),("ö","o"),("ü","u"),("ç","c"),("ğ","g"),("â","a"),("î","i"),("û","u")]:
        s = s.replace(a, b)
    for ch in "'\"·;,.():/\\-_=<>!?+*%#@[]{}|~&":
        s = s.replace(ch, " ")
    return " ".join(s.split())

def _kok(kelime):
    """Türkçe çekim eki toleransı: parcalari → parca, motoru → motor"""
    if len(kelime) <= 5:
        return kelime
    # uzun kelimelerde ilk 6 karakter (parca, tisort, kavrulmus...)
    return kelime[:6]

# Eşanlamlı genişletme: gemi motoru = deniz motoru vb.
ES_ANLAM = {
    "gemi": ["deniz"],
    "araba": ["tasi", "otomobil"],
    "cep telefonu": ["telefon"],
}

def ara_urun(sorgu, limit=15):
    """Adım 1 — ürün adından GTİP adayları (alaka skorlu, çevrimdışı)."""
    q = normalize(sorgu)
    kelimeler = [k for k in q.split() if len(k) >= 2]
    if not kelimeler:
        return []
    # eşanlamlı genişletme
    for kelime in list(kelimeler):
        for es in ES_ANLAM.get(kelime, []):
            if es not in kelimeler:
                kelimeler.append(es)
    kokler = list(dict.fromkeys(_kok(k) for k in kelimeler))
    con = _baglan()
    cur = con.cursor()

    # Aday toplama: FTS5 bm25 (kelime önekli, alaka sıralı) + LIKE fallback
    satirlar = []
    try:
        fts_q = " AND ".join(f'"{k}"*' for k in kokler[:4])
        satirlar = cur.execute(f"""
            SELECT u.gtip_12, u.cn_8, u.hs_6, u.poz_4, u.fas_2, u.aciklama_tr, u.aciklama_tr_6,
                   u.aciklama_tr_4, u.aciklama_en, u.anahtar_en, u.vergi_haddi, u.birim,
                   u.aranacak_tr, u.aranacak_en
            FROM gtip_fts f JOIN urun_kodlari u ON u.gtip_12 = f.gtip_12
            WHERE gtip_fts MATCH ?
            ORDER BY bm25(gtip_fts) LIMIT 200""", (fts_q,)).fetchall()
    except Exception:
        pass
    if not satirlar:
        # LIKE fallback (kelime öneki, geniş limit)
        kosullar = " OR ".join(
            f"(aranacak_tr LIKE '%{k}%' OR aranacak_en LIKE '%{k}%' OR anahtar_en LIKE '%{k}%')" for k in kokler)
        try:
            satirlar = cur.execute(f"""
                SELECT gtip_12, cn_8, hs_6, poz_4, fas_2, aciklama_tr, aciklama_tr_6, aciklama_tr_4,
                       aciklama_en, anahtar_en, vergi_haddi, birim, aranacak_tr, aranacak_en
                FROM urun_kodlari WHERE {kosullar} LIMIT 3000""").fetchall()
        except Exception:
            satirlar = []

    # Alaka skoru — seviye + anahtar kelime ağırlıklı, kelime-öneki (piston→pistonlar)
    def kelime_eslesme(metin, k):
        """Kelime başında/ortasında önek eşleşmesi (Türkçe normalize + harf duyarsız):
        piston → Piston, pistonlar, pistonlu | tisort → Tişört, tişörtler"""
        if not metin:
            return False
        m = normalize(metin)
        return re.search(rf"(^|[^a-z0-9çğıöşü]){re.escape(k)}", m) is not None

    def skor(r):
        s = 0
        r = dict(r)
        for k in kokler:
            if kelime_eslesme(r.get("anahtar_en"), k):
                s += 10          # ürünün gerçek adı (tariffnumber anahtar kelimeleri)
            if kelime_eslesme(r.get("aciklama_tr"), k):
                s += 8
            if kelime_eslesme(r.get("aciklama_tr_6"), k):
                s += 5
            if kelime_eslesme(r.get("aciklama_en"), k):
                s += 4
            if kelime_eslesme(r.get("aciklama_tr_4"), k):
                s += 2
        return s

    skorlu = [(skor(r), r) for r in satirlar]
    skorlu = [(s, r) for s, r in skorlu if s > 0]
    skorlu.sort(key=lambda x: (-x[0], x[1]["gtip_12"]))
    sonuc = []
    for s, r in skorlu[:limit]:
        d = dict(r)
        d["_skor"] = s
        sonuc.append(d)
    con.close()
    return sonuc

def gtip_bilgi(gtip12):
    """GTİP kodu → ürün bilgisi (çevrimdışı)."""
    con = _baglan()
    cur = con.cursor()
    r = cur.execute("""SELECT * FROM urun_kodlari WHERE gtip_12=?""", (gtip12,)).fetchone()
    con.close()
    return dict(r) if r else None

def ulke_listesi():
    """Tüm ülke grubu eşlemeleri + örnek ülkeler."""
    con = _baglan()
    cur = con.cursor()
    ulkeler = cur.execute("SELECT ulke_kod, ulke_adi, igv_grup FROM ulke_gruplari ORDER BY ulke_adi").fetchall()
    con.close()
    return [dict(r) for r in ulkeler]

def ulke_grubu(kod):
    con = _baglan()
    cur = con.cursor()
    r = cur.execute("SELECT igv_grup FROM ulke_gruplari WHERE ulke_kod=?", (kod.upper(),)).fetchone()
    con.close()
    return r["igv_grup"] if r else "diger"

# ================= HESAPLAMA =================

def hesapla_ithalat(gtip12, menşe, cif):
    """Adım 4a — İTHALAT raporu: gümrük vergisi + İGV + KDV + ÖTV"""
    urun = gtip_bilgi(gtip12)
    if not urun:
        return {"hata": f"GTİP bulunamadı: {gtip12}"}
    con = _baglan()
    cur = con.cursor()

    grup = ulke_grubu(menşe)
    igv = cur.execute("SELECT * FROM igv WHERE gtip_12=?", (gtip12,)).fetchone()
    igv_cols = [d[0] for d in cur.description] if igv else []

    # Gümrük vergisi
    ipgt = urun["vergi_haddi"]
    try:
        ipgt_haddi = float(ipgt) if ipgt and ipgt.strip() else None
    except ValueError:
        ipgt_haddi = None
    if grup == "ab":
        gv_oran = 0.0
        gv_not = "AB/EFTA/Gümrük Birliği menşeli → gümrük vergisi %0"
    else:
        gv_oran = ipgt_haddi or 0.0
        gv_not = "İPGT vergi haddi" if ipgt_haddi is not None else "İPGT'de haddi boş (özel muamele olabilir)"

    # İGV
    igv_oran = None
    igv_liste = None
    igv_d = dict(igv) if igv else {}
    if igv_d:
        col = {"ab":"oran_ab","kos":"oran_kos","sng":"oran_sng","vnz":"oran_vnz",
               "bae":"oran_bae","iran":"oran_iran"}.get(grup, "oran_diger")
        if col in igv_cols and igv_d.get(col) is not None:
            igv_oran = igv_d.get(col)
        elif "oran_diger" in igv_cols:
            igv_oran = igv_d.get("oran_diger")
        igv_liste = igv_d.get("liste")
        igv_dipnot = igv_d.get("dipnot")

    # ÖTV
    otv = cur.execute("SELECT liste, oran FROM otv WHERE gtip_12=?", (gtip12,)).fetchone()

    # KDV
    kdv_oran = 0.20
    kdv_r = cur.execute("SELECT oran FROM kdv WHERE gtip_12=?", (gtip12,)).fetchone()
    if kdv_r:
        kdv_oran = kdv_r["oran"] / 100.0

    con.close()

    gv_t = cif * gv_oran / 100
    igv_t = cif * (igv_oran or 0) / 100
    otv_t = 0.0
    otv_not = None
    if otv:
        otv_not = f"ÖTV uygulanır ({otv['liste']} sayılı liste, {otv['oran']}) — tutar ayrıca hesaplanmalı"
    kdv_matrah = cif + gv_t + igv_t + otv_t
    kdv_t = kdv_matrah * kdv_oran
    toplam = gv_t + igv_t + otv_t + kdv_t

    return {
        "gtip_12": gtip12, "menşe": menşe.upper(), "igv_grubu": grup,
        "urun": urun,
        "cif": cif,
        "kalemler": [
            {"ad": "Gümrük vergisi", "oran": gv_oran, "tutar": round(gv_t,2), "not": gv_not},
            {"ad": "İlave Gümrük Vergisi (İGV)", "oran": igv_oran or 0, "tutar": round(igv_t,2),
             "not": f"Liste: {igv_liste}" + (f", dipnot: {igv_dipnot}" if igv_d.get('dipnot') else "")},
            {"ad": "ÖTV", "oran": None, "tutar": 0, "not": otv_not or "Uygulanmıyor (ÖTV listelerinde yok)"},
            {"ad": "KDV", "oran": kdv_oran*100, "tutar": round(kdv_t,2), "not": f"Matrah: CIF+GV+İGV+ÖTV = {round(kdv_matrah,2)} €"},
        ],
        "toplam_vergi": round(toplam, 2),
        "toplam_maliyet": round(cif + toplam, 2),
        "uyari": "Anti-damping, ilave mali yükümlülük ve korunma önlemleri kapsam dışıdır — gümrük müşaviri/TARA teyidi önerilir."
    }

def hesapla_ihracat(gtip12, varış):
    """Adım 4b — İHRACAT raporu: ihracatta vergi olmaz; ürün bilgisi + notlar."""
    urun = gtip_bilgi(gtip12)
    if not urun:
        return {"hata": f"GTİP bulunamadı: {gtip12}"}
    return {
        "gtip_12": gtip12, "varış": varış.upper(),
        "urun": urun,
        "notlar": [
            "Türkiye'den ihracatta gümrük vergisi/İGV/ÖTV uygulanmaz.",
            "İhracat teslimleri KDV'den istisnadır (KDVK md. 11).",
            "GTİP, hedef ülkenin gümrük tarifesindeki kodla aynıdır (HS 6 hane) — hedef ülke vergileri için o ülkenin tarifesine bakılmalıdır.",
            "Bazı ürünlerde ihracat kayıt/izin/denetim (tarife dışı önlem) gerekebilir — bu veritabanının kapsamı dışındadır.",
        ],
        "uyari": "Hedef ülkedeki ithalat vergileri (gümrük vergisi, KDV/KDV benzeri, anti-damping) ayrıca araştırılmalıdır."
    }

def sorgula(urun_sorgu, ulke, hareket, cif=10000):
    """GÖREV AKIŞI: 1) ürün → 2) ülke → 3) hareket → 4) sorgula → rapor"""
    adaylar = ara_urun(urun_sorgu)
    if not adaylar:
        return {"hata": f"'{urun_sorgu}' için sonuç bulunamadı. Farklı kelimeler deneyin (örn. 'piston', 'enjektör')."}
    # varsayılan seçim: orijinal sorgu kelimelerinin en çoğunu eşleştiren
    q_kelimeler = [k for k in normalize(urun_sorgu).split() if len(k) >= 2]
    for a in adaylar:
        atr, aen = a.get("aranacak_tr", ""), a.get("aranacak_en", "")
        a["_kelime"] = sum(1 for k in q_kelimeler if k in atr or k in aen)
    adaylar.sort(key=lambda x: (-x.get("_kelime", 0), -x["_skor"]))
    secim = adaylar[0]
    if hareket.lower() in ("ithalat", "import", "i"):
        rapor = hesapla_ithalat(secim["gtip_12"], ulke, cif)
    elif hareket.lower() in ("ihracat", "export", "e"):
        rapor = hesapla_ihracat(secim["gtip_12"], ulke)
    else:
        return {"hata": "hareket tipi 'ithalat' veya 'ihracat' olmalı"}
    return {"adaylar": adaylar, "secim": secim, "rapor": rapor}

if __name__ == "__main__":
    import sys
    if len(sys.argv) >= 4:
        sonuc = sorgula(sys.argv[1], sys.argv[2], sys.argv[3], float(sys.argv[4]) if len(sys.argv) > 4 else 10000)
        print(json.dumps(sonuc, ensure_ascii=False, indent=1)[:3000])
    else:
        print("Kullanım: python3 sorgula_modulu.py '<ürün>' <ülke_ISO> ithalat|ihracat [CIF]")
        print("Örnek:    python3 sorgula_modulu.py 'gemi motoru parçaları' CN ithalat 10000")
