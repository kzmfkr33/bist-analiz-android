"""
Android derlemesini basitleştirmek için yfinance yerine doğrudan Yahoo
Finance'in genel JSON uçlarına 'requests' ile istek atıyoruz. yfinance'ın
kendisi de arka planda aynı uçları kullanır; burada sadece lxml/peewee gibi
python-for-android'de sorun çıkarabilecek ek bağımlılıkları elimine ediyoruz.

Not: Yahoo, temel veri (F/K, PD/DD vb.) döndüren 'quoteSummary' uçlarını bir
süredir bir 'crumb' güvenlik token'ı olmadan reddediyor (401 Unauthorized).
Bu yüzden bir requests.Session ile önce çerez + crumb alıyor, sonra bunu
temel veri isteklerine ekliyoruz. Fiyat/grafik verisi ('chart' ucu) bundan
etkilenmiyor, crumb gerektirmiyor.
"""
import time

import pandas as pd
import requests

from log_ayarlari import logger_al

log = logger_al(__name__)

_HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
_PERIYOT_GUN = {
    "1mo": 31, "2mo": 62, "3mo": 93, "6mo": 186, "1y": 372, "2y": 744, "5y": 1860,
}

ENDEKS_SEMBOLLERI = {
    "BIST 100": "XU100.IS",
    "BIST 30": "XU030.IS",
    "BIST Banka": "XBANK.IS",
    "BIST Sınai": "XUSIN.IS",
    "BIST Hizmet": "XUHIZ.IS",
}

EMTIA_DOVIZ_SEMBOLLERI = {
    "USD/TRY": "USDTRY=X",
    "EUR/TRY": "EURTRY=X",
    "Altın (Ons)": "GC=F",
    "Brent Petrol": "BZ=F",
}

_oturum = requests.Session()
_oturum.headers.update(_HEADERS)
_crumb_onbellek = {"crumb": None}


def _crumb_al():
    """
    Yahoo'nun temel veri uçları için gerektirdiği 'crumb' token'ını alır.
    Bir kere alınıp bellekte tutulur (her istekte yeniden almaya gerek yok).
    Alınamazsa None döner — çağıran taraf bu durumda crumb'sız dener.
    """
    if _crumb_onbellek["crumb"]:
        return _crumb_onbellek["crumb"]

    try:
        _oturum.get("https://fc.yahoo.com", timeout=10)
        yanit = _oturum.get("https://query2.finance.yahoo.com/v1/test/getcrumb", timeout=10)
        yanit.raise_for_status()
        crumb = yanit.text.strip()
        if crumb and "<html" not in crumb.lower():
            _crumb_onbellek["crumb"] = crumb
            return crumb
    except Exception as hata:
        log.warning(f"Crumb alınamadı: {hata}")

    return None


def fiyat_verisi_getir(sembol, periyot="3mo", interval="1d", deneme_sayisi=3):
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{sembol}"
    params = {"range": periyot, "interval": interval}

    for deneme in range(deneme_sayisi):
        try:
            yanit = _oturum.get(url, params=params, timeout=15)
            yanit.raise_for_status()
            veri_json = yanit.json()

            sonuc = veri_json.get("chart", {}).get("result")
            if not sonuc:
                hata_msg = veri_json.get("chart", {}).get("error")
                raise ValueError(f"{sembol} için veri boş döndü ({hata_msg})")

            r = sonuc[0]
            zaman_damgalari = r.get("timestamp")
            if not zaman_damgalari:
                raise ValueError(f"{sembol} için veri boş döndü")

            fiyatlar = r["indicators"]["quote"][0]
            df = pd.DataFrame({
                "Open": fiyatlar.get("open"),
                "High": fiyatlar.get("high"),
                "Low": fiyatlar.get("low"),
                "Close": fiyatlar.get("close"),
                "Volume": fiyatlar.get("volume"),
            }, index=pd.to_datetime(zaman_damgalari, unit="s"))

            df = df.dropna(subset=["Close"])
            if df.empty:
                raise ValueError(f"{sembol} için veri boş döndü")

            return df

        except Exception as hata:
            if deneme < deneme_sayisi - 1:
                bekleme = 2 ** deneme
                log.warning(f"{sembol} verisi alınamadı ({hata}), {bekleme}sn sonra tekrar deneniyor...")
                time.sleep(bekleme)
            else:
                log.error(f"{sembol} verisi {deneme_sayisi} denemeden sonra da alınamadı: {hata}")
                raise


def temel_veri_getir(sembol):
    url = f"https://query1.finance.yahoo.com/v10/finance/quoteSummary/{sembol}"
    params = {"modules": "summaryDetail,defaultKeyStatistics,price,assetProfile,financialData"}

    crumb = _crumb_al()
    if crumb:
        params["crumb"] = crumb

    try:
        yanit = _oturum.get(url, params=params, timeout=15)
        yanit.raise_for_status()
        sonuc = yanit.json()["quoteSummary"]["result"][0]

        ozet = sonuc.get("summaryDetail", {})
        istat = sonuc.get("defaultKeyStatistics", {})
        fiyat = sonuc.get("price", {})
        profil = sonuc.get("assetProfile", {})
        finansal = sonuc.get("financialData", {})

        def _ham(alan_sozlugu, anahtar):
            return alan_sozlugu.get(anahtar, {}).get("raw") if alan_sozlugu.get(anahtar) else None

        return {
            "sembol": sembol,
            "sirket_adi": fiyat.get("longName"),
            "sektor": profil.get("sector"),
            "fk_orani": _ham(ozet, "trailingPE") or _ham(istat, "trailingPE"),
            "pd_dd_orani": _ham(istat, "priceToBook"),
            "piyasa_degeri": _ham(fiyat, "marketCap") or _ham(ozet, "marketCap"),
            "temettu_verimi": _ham(ozet, "dividendYield"),
            "52_hafta_yuksek": _ham(ozet, "fiftyTwoWeekHigh"),
            "52_hafta_dusuk": _ham(ozet, "fiftyTwoWeekLow"),
            "roe": _ham(finansal, "returnOnEquity"),
            "net_kar_marji": _ham(finansal, "profitMargins"),
            "borc_ozsermaye": _ham(finansal, "debtToEquity"),
            "gelir_buyume": _ham(finansal, "revenueGrowth"),
            "fd_favok": _ham(istat, "enterpriseToEbitda"),
        }
    except Exception as hata:
        log.warning(f"{sembol} temel verisi alınamadı: {hata}")
        return {"sembol": sembol}


def endeks_verisi_getir(periyot="3mo"):
    sonuclar = {}
    for isim, sembol in ENDEKS_SEMBOLLERI.items():
        try:
            sonuclar[isim] = fiyat_verisi_getir(sembol, periyot=periyot, deneme_sayisi=2)
        except Exception as hata:
            log.warning(f"{isim} ({sembol}) endeks verisi alınamadı: {hata}")
    return sonuclar


def doviz_altin_emtia_getir(periyot="1mo"):
    sonuclar = {}
    for isim, sembol in EMTIA_DOVIZ_SEMBOLLERI.items():
        try:
            sonuclar[isim] = fiyat_verisi_getir(sembol, periyot=periyot, deneme_sayisi=2)
        except Exception as hata:
            log.warning(f"{isim} ({sembol}) verisi alınamadı: {hata}")
    return sonuclar


def gecmis_finansal_veriler_getir(sembol, yil_sayisi=4):
    url = f"https://query1.finance.yahoo.com/v10/finance/quoteSummary/{sembol}"
    params = {"modules": "incomeStatementHistory"}

    crumb = _crumb_al()
    if crumb:
        params["crumb"] = crumb

    try:
        yanit = _oturum.get(url, params=params, timeout=15)
        yanit.raise_for_status()
        sonuc = yanit.json()["quoteSummary"]["result"][0]
        yillik_kayitlar = sonuc.get("incomeStatementHistory", {}).get("incomeStatementHistory", [])

        def _ham(kayit, anahtar):
            return kayit.get(anahtar, {}).get("raw") if kayit.get(anahtar) else None

        veriler = []
        for kayit in yillik_kayitlar[:yil_sayisi]:
            veriler.append({
                "yil": kayit.get("endDate", {}).get("fmt", "")[:4],
                "satis": _ham(kayit, "totalRevenue"),
                "net_kar": _ham(kayit, "netIncome"),
                "favok_yaklasik": _ham(kayit, "ebit"),
            })

        veriler.sort(key=lambda v: v["yil"])
        return veriler

    except Exception as hata:
        log.warning(f"{sembol} geçmiş finansal verisi alınamadı: {hata}")
        return []
def saatlik_veri_getir(sembol, periyot="60d"):
    """
    Saatlik mum verisi getirir (Yahoo Finance'in 60m interval'ı — gerçek
    60 dakikalık verinin en yakın karşılığı). Yahoo saatlik veriyi
    yaklaşık 730 güne kadar destekler, ama biz 60 günle sınırlı tutuyoruz
    (çoklu zaman dilimi teyidi için bu kadarı yeterli).
    """
    return fiyat_verisi_getir(sembol, periyot=periyot, interval="60m")


def dortsaatlik_veri_getir(sembol, periyot="60d"):
    """
    Yahoo'da doğrudan 4 saatlik interval yok — saatlik veriyi çekip
    4'erli gruplar halinde yeniden örnekliyoruz (resample).
    """
    saatlik = saatlik_veri_getir(sembol, periyot=periyot)
    dortsaatlik = saatlik.resample("4h").agg({
        "Open": "first", "High": "max", "Low": "min", "Close": "last", "Volume": "sum",
    }).dropna()
    return dortsaatlik