#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""yollar.py — Proje klasör yolları (TEK KAYNAK).

Klasör yapısı:
    <kök>/
      scripts/    bu dosya + parse/build scriptleri + güncelleme scriptleri
      veri/       JSON / CSV / SQLite çıktıları (guncelle_*.sh ile üretilir)
      kaynak/     resmi arşiv: PDF, ZIP, açılmış Excel klasörleri
      uygulama/   FastAPI + React arayüzü
      yedekler/   versiyonlu tar.gz anlık görüntüler

Kullanım (scriptler scripts/ içinden çalıştırıldığından sys.path'te hazırdır):
    from yollar import KOK, VERI, KAYNAK, YEDEKLER, DB, veri, kaynak
"""
import os

KOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VERI = os.path.join(KOK, "veri")
KAYNAK = os.path.join(KOK, "kaynak")
YEDEKLER = os.path.join(KOK, "yedekler")
DB = os.path.join(VERI, "gtip_kodlari.db")


def veri(*parcalar):
    """veri/ altındaki dosya yolu: veri('ipgt_2026.json')"""
    return os.path.join(VERI, *parcalar)


def kaynak(*parcalar):
    """kaynak/ altındaki dosya yolu: kaynak('tgtc_2026')"""
    return os.path.join(KAYNAK, *parcalar)
