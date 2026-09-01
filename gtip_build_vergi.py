#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Vergi hesaplama sistemi — ülke grupları + İGV + KDV + ÖTV entegrasyonu.
Ana DB'ye tablolar ekler: igv, ulke_gruplari, kdv, otv
"""
import json, sqlite3, os

OUT = "/home/yunus/Masaüstü/gtip_kodlari"
DB = f"{OUT}/gtip_kodlari.db"

# ============ ÜLKE GRUPLARI (İGV kolon eşlemesi) ============
# AB grubu: EU27 + EFTA4 + BK + Bosna + Faroe + G.Kore + Malezya + STA ortakları
# (İthalat Rejimi "1. sütun": AB Üyesi, EFTA, STA ortakları — Arnavutluk, Sırbistan, Gürcistan...)
AB_ULKELER = {
    # AB-27
    "AT":"Avusturya","BE":"Belçika","BG":"Bulgaristan","HR":"Hırvatistan","CY":"Güney Kıbrıs",
    "CZ":"Çekya","DK":"Danimarka","EE":"Estonya","FI":"Finlandiya","FR":"Fransa","DE":"Almanya",
    "GR":"Yunanistan","HU":"Macaristan","IE":"İrlanda","IT":"İtalya","LV":"Letonya","LT":"Litvanya",
    "LU":"Lüksemburg","MT":"Malta","NL":"Hollanda","PL":"Polonya","PT":"Portekiz","RO":"Romanya",
    "SK":"Slovakya","SI":"Slovenya","ES":"İspanya","SE":"İsveç",
    # EFTA
    "CH":"İsviçre","NO":"Norveç","IS":"İzlanda","LI":"Lihtenştayn",
    # Gümrük Birliği / STA ortakları
    "GB":"Birleşik Krallık","BA":"Bosna-Hersek","FO":"Faroe Adaları","KR":"Güney Kore",
    "MY":"Malezya","AL":"Arnavutluk","RS":"Sırbistan","GE":"Gürcistan","MK":"Kuzey Makedonya",
    "ME":"Karadağ","EG":"Mısır","MA":"Fas","TN":"Tunus","IL":"İsrail","CL":"Şili",
    "JO":"Ürdün","LB":"Lübnan","PS":"Filistin","AZ":"Azerbaycan","XK":"Kosova",
    # Pan-Avrupa-Akdeniz bölgesi (PEM kümülasyon)
    "MD":"Moldova","UA":"Ukrayna","DZ":"Cezayir",
}
# Spesifik kolonlu ülkeler (EK-2/EK-3'te ayrı sütunları var)
OZEL_ULKELER = {
    "XK": ("kos", "Kosova"),
    "SG": ("sng", "Singapur"),
    "VE": ("vnz", "Venezuela"),
    "AE": ("bae", "Birleşik Arap Emirlikleri"),
    "IR": ("iran", "İran"),
}

# Diğer Ülkeler (D.Ü.) — ana İGV oranı uygulananlar
DIGER_ULKELER = {
    "CN":"Çin","US":"ABD","JP":"Japonya","IN":"Hindistan","RU":"Rusya","BR":"Brezilya",
    "TR":"Türkiye","ID":"Endonezya","TH":"Tayland","VN":"Vietnam","BD":"Bangladeş",
    "PK":"Pakistan","NG":"Nijerya","ZA":"Güney Afrika","MX":"Meksika","AR":"Arjantin",
    "AU":"Avustralya","NZ":"Yeni Zelanda","CA":"Kanada","UA":"Ukrayna",
    "BY":"Belarus","KZ":"Kazakistan","UZ":"Özbekistan","IQ":"Irak","SY":"Suriye",
    "SA":"Suudi Arabistan","QA":"Katar","KW":"Kuveyt","OM":"Umman","BH":"Bahreyn",
    "YE":"Yemen","SD":"Sudan","ET":"Etiyopya","KE":"Kenya","TZ":"Tanzanya","GH":"Gana",
    "CI":"Fildişi Sahili","CM":"Kamerun","SN":"Senegal","ML":"Mali","BF":"Burkina Faso",
    "NE":"Nijer","TD":"Çad","SO":"Somali","AF":"Afganistan","NP":"Nepal","LK":"Sri Lanka",
    "MM":"Myanmar","KH":"Kamboçya","LA":"Laos","PH":"Filipinler","TW":"Tayvan",
    "HK":"Hong Kong",
}

def ulke_grubu(kod):
    """Ülke kodunu İGV grubuna eşler. Bilinmeyen → 'diger' (D.Ü.)."""
    kod = (kod or "").strip().upper()
    if kod in OZEL_ULKELER:
        return OZEL_ULKELER[kod][0]
    if kod in AB_ULKELER:
        return "ab"
    return "diger"

def main():
    con = sqlite3.connect(DB)
    cur = con.cursor()

    # ---- 1) İGV tablosu ----
    cur.executescript("""
    CREATE TABLE IF NOT EXISTS igv (
        gtip_12    TEXT PRIMARY KEY,
        liste      TEXT,            -- EK-1 / EK-2 / EK-3
        dipnot     TEXT,
        oran_ab    REAL,            -- AB+EFTA+STA ortakları
        oran_kol2  REAL,            -- EK-1 sütun 2
        oran_kol3  REAL,            -- EK-1 sütun 3
        oran_gts   REAL,            -- GTS ülkeleri (EK-1)
        oran_kos   REAL,
        oran_sng   REAL,
        oran_vnz   REAL,
        oran_bae   REAL,
        oran_iran  REAL,
        oran_gkore REAL,
        oran_mlz   REAL,
        oran_diger REAL              -- Diğer Ülkeler (D.Ü.)
    );
    CREATE INDEX IF NOT EXISTS idx_igv_gtip ON igv(gtip_12);
    """)

    igv = json.load(open(f"{OUT}/igv_2026.json", encoding="utf-8"))
    satirlar = []
    for x in igv:
        satirlar.append((x["gtip"], x["liste"], x.get("dipnot",""),
            x.get("ab"), x.get("kol2"), x.get("kol3"), x.get("gts"),
            x.get("kos"), x.get("sng"), x.get("vnz"), x.get("bae"),
            x.get("iran"), x.get("g_kore"), x.get("mlz"), x.get("diger")))
    cur.execute("BEGIN")
    cur.executemany("INSERT OR REPLACE INTO igv VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", satirlar)
    con.execute("COMMIT")
    print(f"✅ igv: {len(satirlar)} kayıt")

    # ---- 2) Ülke grupları ----
    cur.execute("""CREATE TABLE IF NOT EXISTS ulke_gruplari (
        ulke_kod   TEXT PRIMARY KEY,
        ulke_adi   TEXT,
        igv_grup   TEXT,   -- ab / kos / sng / vnz / bae / iran / diger
        aciklama   TEXT
    )""")
    ulkeler = []
    for kod, ad in AB_ULKELER.items():
        ulkeler.append((kod, ad, "ab", "AB+EFTA+Gümrük Birliği+STA ortağı — İGV genelde %0"))
    for kod, (grup, ad) in OZEL_ULKELER.items():
        ulkeler.append((kod, ad, grup, f"Spesifik İGV kolonu ({grup})"))
    for kod, ad in DIGER_ULKELER.items():
        ulkeler.append((kod, ad, "diger", "Diğer Ülkeler (D.Ü.) — İGV ana oranı"))
    cur.execute("BEGIN")
    cur.executemany("INSERT OR REPLACE INTO ulke_gruplari VALUES (?,?,?,?)", ulkeler)
    con.execute("COMMIT")
    print(f"✅ ulke_gruplari: {len(ulkeler)} ülke (geri kalan → 'diger' = D.Ü.)")

    # ---- 3) KDV ----
    # Genel %20; indirimli listeler GİB'den eklenebilir (I sayılı %1, II sayılı %10)
    cur.execute("""CREATE TABLE IF NOT EXISTS kdv (
        gtip_12   TEXT PRIMARY KEY,
        oran      REAL,
        kaynak    TEXT
    )""")
    print("✅ kdv tablosu hazır (genel %20 — indirimli GTİP listeleri GİB'den eklenebilir)")

    # ---- 4) ÖTV ----
    cur.execute("""CREATE TABLE IF NOT EXISTS otv (
        gtip_12   TEXT PRIMARY KEY,
        liste     TEXT,   -- I (akaryakıt) / II (taşıt) / III (alkol-tütün) / IV (lüks)
        oran      TEXT,   -- oran veya maktu (TL/kg vb.)
        kaynak    TEXT
    )""")
    print("✅ otv tablosu hazır (listeler GİB'den eklenebilir)")

    con.commit()
    con.close()
    print(f"\n📦 {DB} güncellendi")

if __name__ == "__main__":
    main()
