"""
AL/SAT Sinyal Takip Motoru — çoklu teyit (confluence) prensibiyle kurulmuştur.
Tek bir göstergeye güvenmek yanlış sinyale (whipsaw) çok açık olduğu için,
AL sinyali ancak birden fazla bağımsız gösterge AYNI ANDA hizalandığında
tetiklenir. SAT sinyali ise riski erken kesmek için daha gevşek kurallarla,
bağımsız tetikleyicilerin HERHANGİ BİRİYLE çalışır.

Repainting yasağı: tüm hesaplamalar sadece kapanmış mumlarla (veri.iloc[-1])
yapılır. Sadece günlük zaman dilimi destekleniyor (ilk sürüm).

Bu modül her hissenin pozisyon durumunu (izlemede mi, pozisyonda mı, hangi
fiyattan girildi) diske kaydeder — böylece "zaten AL durumundayken tekrar
tekrar AL" demek yerine, sadece durum DEĞİŞTİĞİNDE (yeni bir AL/SAT anı)
bildirim üretir.
"""
import json
import os

from gostergeler import ema_hesapla, macd_hesapla, rsi_hesapla, adx_hesapla, relative_volume_hesapla
from veri_katmani import fiyat_verisi_getir
from log_ayarlari import logger_al

log = logger_al(__name__)

TAKIP_DOSYASI = "sinyal_takip_listesi.json"
STOP_YUZDESI_VARSAYILAN = 5.0


def sinyal_hesapla(veri):
    """
    Bir hissenin son kapanmış mumu için ham AL/SAT tetikleyicilerini hesaplar.

    AL — hepsi birden sağlanmalı:
      Trend filtresi (EMA20>EMA50) + MACD yukarı kesişim + RSI 45-70 +
      ADX>=20 + RVOL>=1.2

    SAT — herhangi biri yeterli:
      MACD aşağı kesişim VEYA RSI>=75 VEYA fiyat EMA20 altına düştü
      (stop-loss ayrıca hisseyi_kontrol_et'te uygulanıyor)
    """
    if len(veri) < 60:
        return {"al_tetik": False, "sat_tetik": False, "al_kosullari": {}, "sat_kosullari": {},
                "son_fiyat": None, "son_tarih": None, "hata": "Yetersiz veri (en az 60 gün gerekli)"}

    ema20 = ema_hesapla(veri, 20)
    ema50 = ema_hesapla(veri, 50)
    macd, macd_sinyal = macd_hesapla(veri)
    rsi = rsi_hesapla(veri)
    adx, pdi, ndi = adx_hesapla(veri)
    rvol = relative_volume_hesapla(veri, 20)

    son, onceki = -1, -2

    macd_yukari_kesti = bool(macd.iloc[onceki] <= macd_sinyal.iloc[onceki] and macd.iloc[son] > macd_sinyal.iloc[son])
    macd_asagi_kesti = bool(macd.iloc[onceki] >= macd_sinyal.iloc[onceki] and macd.iloc[son] < macd_sinyal.iloc[son])

    trend_yukselis = bool(ema20.iloc[son] > ema50.iloc[son])
    rsi_son = rsi.iloc[son]
    rsi_saglikli = bool(45 <= rsi_son <= 70) if rsi_son == rsi_son else False
    rsi_asiri_alim = bool(rsi_son >= 75) if rsi_son == rsi_son else False
    adx_son = adx.iloc[son]
    adx_guclu = bool(adx_son >= 20) if adx_son == adx_son else False
    rvol_son = rvol.iloc[son]
    hacim_teyit = bool(rvol_son >= 1.2) if rvol_son == rvol_son else False
    fiyat_ema20_altinda = bool(veri["Close"].iloc[son] < ema20.iloc[son])

    al_kosullari = {
        "Trend filtresi (EMA20 > EMA50)": trend_yukselis,
        "MACD yukarı kesişim": macd_yukari_kesti,
        "RSI sağlıklı bölgede (45-70)": rsi_saglikli,
        "ADX güçlü (>=20)": adx_guclu,
        "Hacim teyidi (RVOL >= 1.2)": hacim_teyit,
    }
    sat_kosullari = {
        "MACD aşağı kesişim": macd_asagi_kesti,
        "RSI aşırı alım (>=75)": rsi_asiri_alim,
        "Fiyat EMA20 altına düştü": fiyat_ema20_altinda,
    }

    return {
        "al_tetik": all(al_kosullari.values()),
        "al_kosullari": al_kosullari,
        "sat_tetik": any(sat_kosullari.values()),
        "sat_kosullari": sat_kosullari,
        "son_fiyat": float(veri["Close"].iloc[son]),
        "son_tarih": str(veri.index[son].date()),
    }


def _tum_kayitlari_oku():
    if not os.path.exists(TAKIP_DOSYASI):
        return []
    try:
        with open(TAKIP_DOSYASI, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError as hata:
        log.error(f"{TAKIP_DOSYASI} bozuk görünüyor: {hata}")
        return []


def _kayitlari_yaz(liste):
    with open(TAKIP_DOSYASI, "w", encoding="utf-8") as f:
        json.dump(liste, f, ensure_ascii=False, indent=2)


def takip_listesi_getir():
    return _tum_kayitlari_oku()


def takibe_ekle(sembol, stop_yuzdesi=STOP_YUZDESI_VARSAYILAN):
    liste = _tum_kayitlari_oku()
    if any(k["sembol"] == sembol for k in liste):
        return liste
    liste.append({
        "sembol": sembol, "stop_yuzdesi": stop_yuzdesi,
        "pozisyonda": False, "giris_fiyati": None, "giris_tarihi": None,
        "son_fiyat": None, "son_kontrol": None, "gecmis": [],
    })
    _kayitlari_yaz(liste)
    return liste


def takipten_cikar(sembol):
    liste = [k for k in _tum_kayitlari_oku() if k["sembol"] != sembol]
    _kayitlari_yaz(liste)
    return liste


def hisseyi_kontrol_et(sembol, periyot="1y"):
    """
    Bir hissenin güncel verisini çeker, sinyal hesaplar, kayıtlı durumla
    kıyaslar ve DURUM DEĞİŞTİYSE (yeni AL ya da SAT anı) bunu döner.
    Durum değişmediyse (örn. zaten pozisyondaysan ve sinyal hâlâ AL) None
    dönmez ama "yeni_sinyal" alanı None olur — spam önlenir.
    """
    veri = fiyat_verisi_getir(sembol, periyot=periyot)
    sonuc = sinyal_hesapla(veri)

    liste = _tum_kayitlari_oku()
    kayit = next((k for k in liste if k["sembol"] == sembol), None)
    if kayit is None:
        return None

    yeni_sinyal = None

    if sonuc.get("son_fiyat") is None:
        return {"kayit": kayit, "yeni_sinyal": None, "canli": sonuc}

    if not kayit["pozisyonda"]:
        if sonuc["al_tetik"]:
            kayit["pozisyonda"] = True
            kayit["giris_fiyati"] = sonuc["son_fiyat"]
            kayit["giris_tarihi"] = sonuc["son_tarih"]
            yeni_sinyal = {
                "tur": "AL", "fiyat": sonuc["son_fiyat"], "tarih": sonuc["son_tarih"],
                "nedenler": sonuc["al_kosullari"],
            }
    else:
        degisim_yuzde = 100 * (sonuc["son_fiyat"] - kayit["giris_fiyati"]) / kayit["giris_fiyati"]
        stop_tetiklendi = degisim_yuzde <= -abs(kayit.get("stop_yuzdesi", STOP_YUZDESI_VARSAYILAN))

        if sonuc["sat_tetik"] or stop_tetiklendi:
            yeni_sinyal = {
                "tur": "SAT", "fiyat": sonuc["son_fiyat"], "tarih": sonuc["son_tarih"],
                "getiri_yuzde": round(degisim_yuzde, 2),
                "neden": "Stop-loss" if (stop_tetiklendi and not sonuc["sat_tetik"]) else "Teknik sinyal",
                "nedenler": sonuc["sat_kosullari"],
            }
            kayit["pozisyonda"] = False
            kayit["giris_fiyati"] = None
            kayit["giris_tarihi"] = None

    kayit["son_fiyat"] = sonuc["son_fiyat"]
    kayit["son_kontrol"] = sonuc["son_tarih"]
    if yeni_sinyal:
        kayit.setdefault("gecmis", []).insert(0, yeni_sinyal)
        kayit["gecmis"] = kayit["gecmis"][:20]

    _kayitlari_yaz(liste)
    return {"kayit": kayit, "yeni_sinyal": yeni_sinyal, "canli": sonuc}


def tum_takipleri_kontrol_et():
    """Takip listesindeki tüm hisseleri kontrol eder, yeni tetiklenen sinyalleri döner."""
    liste = _tum_kayitlari_oku()
    tetiklenenler = []
    for kayit in liste:
        try:
            sonuc = hisseyi_kontrol_et(kayit["sembol"])
            if sonuc and sonuc["yeni_sinyal"]:
                tetiklenenler.append({"sembol": kayit["sembol"], **sonuc["yeni_sinyal"]})
        except Exception as hata:
            log.warning(f"{kayit['sembol']} kontrol edilemedi: {hata}")
            continue
    return tetiklenenler