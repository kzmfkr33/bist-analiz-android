"""
Watchlist — plan madde 23.
Favori hisseleri saklar; her biri için Fiyat, Değişim %, RSI, Hacim,
Teknik Skor, Temel Skor, Genel Skor tek tabloda gösterilecek şekilde
hazır veri üretir.
"""
import json
import os

from test import analiz_et
from veri_katmani import temel_veri_getir
from hisse_skoru import hisse_skoru_hesapla
from log_ayarlari import logger_al

log = logger_al(__name__)

WATCHLIST_DOSYASI = "watchlist.json"


def watchlist_ekle(sembol):
    semboller = watchlist_getir()
    if sembol not in semboller:
        semboller.append(sembol)
        _watchlist_kaydet(semboller)
    return semboller


def watchlist_cikar(sembol):
    semboller = [s for s in watchlist_getir() if s != sembol]
    _watchlist_kaydet(semboller)
    return semboller


def watchlist_getir():
    if not os.path.exists(WATCHLIST_DOSYASI):
        return []
    try:
        with open(WATCHLIST_DOSYASI, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError as hata:
        log.error(f"{WATCHLIST_DOSYASI} bozuk görünüyor, boş liste ile devam ediliyor: {hata}")
        return []


def _watchlist_kaydet(semboller):
    with open(WATCHLIST_DOSYASI, "w", encoding="utf-8") as f:
        json.dump(semboller, f, ensure_ascii=False, indent=2)


def watchlist_verilerini_getir(semboller=None):
    """
    Watchlist tablosu için hazır veri üretir. semboller verilmezse
    watchlist_getir() kullanılır.

    Dönüş: [{"sembol", "fiyat", "degisim_yuzde", "rsi", "hacim",
             "teknik_skor", "temel_skor", "genel_skor"}, ...]
    Bir hisse için veri çekilemezse o satırda "hata" alanı olur, diğerleri etkilenmez.
    """
    if semboller is None:
        semboller = watchlist_getir()

    sonuclar = []
    for sembol in semboller:
        try:
            veri = analiz_et(sembol)
            temel = temel_veri_getir(sembol)
            skor = hisse_skoru_hesapla(veri, temel)
            son = veri.iloc[-1]

            kapanislar = veri["Close"]
            degisim_yuzde = (
                100 * (kapanislar.iloc[-1] - kapanislar.iloc[-2]) / kapanislar.iloc[-2]
                if len(kapanislar) > 1 else None
            )

            sonuclar.append({
                "sembol": sembol,
                "fiyat": round(float(son["Close"]), 2),
                "degisim_yuzde": round(degisim_yuzde, 2) if degisim_yuzde is not None else None,
                "rsi": round(float(son["RSI"]), 1) if son.get("RSI") == son.get("RSI") else None,
                "hacim": int(son["Volume"]) if son.get("Volume") == son.get("Volume") else None,
                "teknik_skor": skor["teknik"]["puan"],
                "temel_skor": skor["temel"]["puan"],
                "genel_skor": skor["genel"],
            })
        except Exception as hata:
            log.warning(f"{sembol} watchlist verisi alınamadı: {hata}")
            sonuclar.append({"sembol": sembol, "hata": str(hata)})

    return sonuclar


if __name__ == "__main__":
    watchlist_ekle("THYAO.IS")
    watchlist_ekle("ASELS.IS")
    watchlist_ekle("GARAN.IS")

    veriler = watchlist_verilerini_getir()

    print("\n=== WATCHLIST ===")
    print(f"{'Sembol':<10}{'Fiyat':>10}{'Değ.%':>8}{'RSI':>7}{'Teknik':>8}{'Temel':>8}{'Genel':>8}")
    for v in veriler:
        if "hata" in v:
            print(f"{v['sembol']:<10} HATA: {v['hata']}")
            continue
        print(f"{v['sembol']:<10}{v['fiyat']:>10}{v['degisim_yuzde']:>8}{v['rsi']:>7}"
              f"{v['teknik_skor']:>8}{v['temel_skor']:>8}{v['genel_skor']:>8}")