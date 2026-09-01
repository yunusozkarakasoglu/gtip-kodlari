#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""SQLite veritabanı v3 — İPGT 2026 (resmi) + tariffnumber EN açıklamalar.
Kaynaklar:
  - ipgt_2026.json      : Ticaret Bakanlığı resmi TGTC 2026 (15.718 GTİP)
  - tariffnumber_en.json: EN açıklama + anahtar kelimeler (2026 CN)
  - tim_ham.json        : fasıl adları (TR) — İPGT ile aynı köken
"""
import json, sqlite3, os, csv, unicodedata

OUT = "/home/yunus/Masaüstü/gtip_kodlari"
DB = f"{OUT}/gtip_kodlari.db"

def normalize(s):
    if not s:
        return ""
    s = s.replace("İ", "i").replace("I", "i")
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode("ascii")
    s = s.lower()
    s = s.replace("ı", "i").replace("ş", "s").replace("ö", "o").replace("ü", "u") \
         .replace("ç", "c").replace("ğ", "g").replace("â", "a").replace("î", "i").replace("û", "u")
    for ch in "'\"·;,.():/\\-_=<>!?+*%#@[]{}|~&":
        s = s.replace(ch, " ")
    return " ".join(s.split())

def yukle():
    ipgt = json.load(open(f"{OUT}/ipgt_2026.json", encoding="utf-8"))
    tn = json.load(open(f"{OUT}/tariffnumber_en.json", encoding="utf-8"))
    tim = json.load(open(f"{OUT}/tim_ham.json", encoding="utf-8"))
    return ipgt, tn, tim

def en(tn, kod):
    r = tn.get(kod)
    return r["ad"] if r else None

def kur(ipgt, tn, tim):
    if os.path.exists(DB):
        os.remove(DB)
    con = sqlite3.connect(DB)
    cur = con.cursor()

    cur.executescript("""
    PRAGMA journal_mode=WAL;
    CREATE TABLE fasillar (
        fas_2   TEXT PRIMARY KEY,
        ad_tr   TEXT,
        ad_en   TEXT
    );
    CREATE TABLE urun_kodlari (
        gtip_12        TEXT PRIMARY KEY,   -- resmi 12 haneli GTİP (İPGT 2026)
        cn_8           TEXT NOT NULL,      -- AB Kombine Nomenklatür (8 hane)
        hs_6           TEXT NOT NULL,      -- HS kodu (6 hane, uluslararası)
        poz_4          TEXT NOT NULL,      -- pozisyon (4 hane)
        fas_2          TEXT NOT NULL,      -- fasıl (2 hane)
        aciklama_tr    TEXT,               -- İPGT tanımı (12 hane seviyesi)
        aciklama_tr_6  TEXT,               -- İPGT tanımı (6 hane seviyesi)
        aciklama_tr_4  TEXT,               -- İPGT tanımı (4 hane seviyesi)
        aciklama_tr_2  TEXT,               -- fasıl adı (TR)
        aciklama_en    TEXT,               -- EN açıklama (8 hane, tariffnumber)
        aciklama_en_6  TEXT,               -- EN açıklama (6 hane)
        anahtar_en     TEXT,               -- EN anahtar kelimeler
        birim          TEXT,               -- ölçü birimi (İPGT)
        vergi_haddi    TEXT,               -- vergi haddi % (İPGT)
        aranacak_tr    TEXT,               -- normalize TR (arama)
        aranacak_en    TEXT                -- normalize EN (arama)
    );
    CREATE INDEX idx_cn8  ON urun_kodlari(cn_8);
    CREATE INDEX idx_hs6  ON urun_kodlari(hs_6);
    CREATE INDEX idx_poz4 ON urun_kodlari(poz_4);
    CREATE INDEX idx_fas2 ON urun_kodlari(fas_2);
    CREATE INDEX idx_en   ON urun_kodlari(aciklama_en);
    CREATE VIRTUAL TABLE gtip_fts USING fts5(
        gtip_12, cn_8, hs_6, poz_4, fas_2,
        aranacak_tr, aranacak_en,
        tokenize = 'ascii'
    );
    """)

    # fasıl adları: TİM (TR) + tariffnumber (EN)
    fas_tr = {}
    for x in tim:
        fas_tr[x["gtip2"]] = x["gtip2desc"]
    fasillar = []
    for kod in sorted(fas_tr):
        ad_en = en(tn, kod)
        fasillar.append((kod, fas_tr[kod], ad_en))
    con.execute("BEGIN")
    cur.executemany("INSERT OR REPLACE INTO fasillar VALUES (?,?,?)", fasillar)

    satirlar, fts = [], []
    for x in ipgt:
        g = x["gtip"]
        cn8, hs6, poz4, fas2 = g[:8], g[:6], g[:4], g[:2]
        ad_en = en(tn, cn8) or en(tn, hs6) or en(tn, poz4) or en(tn, fas2)
        ad_en_6 = en(tn, hs6)
        anahtar = ""
        r8 = tn.get(cn8)
        if r8 and r8.get("anahtar"):
            anahtar = r8["anahtar"].replace("&#039;", "'").replace("·", " ")
        fas_adi = fas_tr.get(fas2, "")
        ar_tr = normalize(" ".join(filter(None, [fas_adi, x["aciklama_tr_4"], x["aciklama_tr_6"], x["aciklama_tr"]])))
        ar_en = normalize(" ".join(filter(None, [ad_en, ad_en_6, anahtar])))
        satirlar.append((g, cn8, hs6, poz4, fas2,
                         x["aciklama_tr"], x["aciklama_tr_6"], x["aciklama_tr_4"], fas_adi,
                         ad_en, ad_en_6, anahtar, x["birim"], x["vergi_haddi"], ar_tr, ar_en))
        fts.append((g, cn8, hs6, poz4, fas2, ar_tr, ar_en))

    cur.executemany("INSERT INTO urun_kodlari VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", satirlar)
    cur.executemany("INSERT INTO gtip_fts VALUES (?,?,?,?,?,?,?)", fts)
    con.execute("COMMIT")
    return con, cur

def export(con):
    cur = con.cursor()
    cols = ["gtip_12","cn_8","hs_6","poz_4","fas_2","aciklama_tr","aciklama_tr_6","aciklama_tr_4",
            "aciklama_tr_2","aciklama_en","aciklama_en_6","anahtar_en","birim","vergi_haddi"]
    with open(f"{OUT}/urun_kodlari.csv", "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(cols)
        for r in cur.execute("SELECT " + ",".join(cols) + " FROM urun_kodlari ORDER BY gtip_12"):
            w.writerow(r)
    with open(f"{OUT}/urun_kodlari.json", "w", encoding="utf-8") as f:
        rows = [dict(zip(cols, r)) for r in cur.execute("SELECT " + ",".join(cols) + " FROM urun_kodlari ORDER BY gtip_12")]
        json.dump(rows, f, ensure_ascii=False)

def test(con):
    cur = con.cursor()
    print("=== TESTLER (İPGT 2026) ===")
    print("1) Kod→ürün (hs_6 LIKE '6109%'):")
    for r in cur.execute("SELECT gtip_12, cn_8, aciklama_tr, aciklama_en FROM urun_kodlari WHERE hs_6 LIKE '6109%' LIMIT 2"):
        print("  ", r)
    print("2) Ürün→kod TR ('pamuk tişört'):")
    for r in cur.execute("""SELECT gtip_12, hs_6, aciklama_tr_4 FROM urun_kodlari 
                            WHERE aranacak_tr LIKE '%pamuk%' AND aranacak_tr LIKE '%tisort%' LIMIT 2"""):
        print("  ", r)
    print("3) Ürün→kod EN ('leather jacket'):")
    for r in cur.execute("""SELECT gtip_12, cn_8, aciklama_en FROM urun_kodlari 
                            WHERE aranacak_en LIKE '%leather%' AND aranacak_en LIKE '%jacket%' LIMIT 2"""):
        print("  ", r)
    print("4) Vergi + birim (01012910):")
    for r in cur.execute("SELECT gtip_12, aciklama_tr, birim, vergi_haddi FROM urun_kodlari WHERE gtip_12 LIKE '01012910%'"):
        print("  ", r)
    print("5) Yeni kod kontrolü (03028115 — İPGT 2026'da var):")
    for r in cur.execute("SELECT gtip_12, aciklama_tr, aciklama_en FROM urun_kodlari WHERE gtip_12 LIKE '03028115%'"):
        print("  ", r)
    print("6) FTS5 ('tisort'):")
    for r in cur.execute("SELECT gtip_12 FROM gtip_fts WHERE gtip_fts MATCH 'tisort' LIMIT 3"):
        print("  ", r)

def main():
    ipgt, tn, tim = yukle()
    print(f"Yüklendi: İPGT={len(ipgt)}, tariffnumber={len(tn)}")
    con, cur = kur(ipgt, tn, tim)
    n = cur.execute("SELECT COUNT(*) FROM urun_kodlari").fetchone()[0]
    nf = cur.execute("SELECT COUNT(*) FROM fasillar").fetchone()[0]
    en_var = cur.execute("SELECT COUNT(*) FROM urun_kodlari WHERE aciklama_en IS NOT NULL AND aciklama_en != ''").fetchone()[0]
    vergi_var = cur.execute("SELECT COUNT(*) FROM urun_kodlari WHERE vergi_haddi != ''").fetchone()[0]
    print(f"✅ DB: {n} GTİP | fasillar={nf} | EN'li={en_var} | vergi'li={vergi_var}")
    export(con)
    print("✅ CSV + JSON export")
    test(con)
    con.close()

if __name__ == "__main__":
    main()
