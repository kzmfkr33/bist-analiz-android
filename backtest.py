from test import analiz_et
from strateji_olusturucu import kosullari_uygula
from relative_guc import bist100_getir
from log_ayarlari import logger_al

log = logger_al(__name__)


def _maksimum_dusus_hesapla(equity_egrisi):
    tepe = equity_egrisi[0]
    maks_dusus = 0.0
    for deger in equity_egrisi:
        tepe = max(tepe, deger)
        dusus = (deger - tepe) / tepe * 100
        maks_dusus = min(maks_dusus, dusus)
    return round(maks_dusus, 2)


def backtest_calistir(sembol, al_kosullari, sat_kosullari=None, stop_yuzdesi=None,
                       kar_al_yuzdesi=None, periyot="1y", baslangic_sermaye=100000):
    veri = analiz_et(sembol, periyot=periyot)

    islemler = []
    pozisyonda = False
    giris_fiyati = None
    giris_tarihi = None
    equity = baslangic_sermaye
    equity_egrisi = [equity]

    for i in range(len(veri)):
        satir = veri.iloc[i]

        if not pozisyonda:
            if kosullari_uygula(satir, al_kosullari):
                pozisyonda = True
                giris_fiyati = satir["Close"]
                giris_tarihi = veri.index[i]
        else:
            degisim_yuzde = 100 * (satir["Close"] - giris_fiyati) / giris_fiyati
            cik = False

            if sat_kosullari and kosullari_uygula(satir, sat_kosullari):
                cik = True
            elif stop_yuzdesi and degisim_yuzde <= -abs(stop_yuzdesi):
                cik = True
            elif kar_al_yuzdesi and degisim_yuzde >= abs(kar_al_yuzdesi):
                cik = True

            if cik:
                equity *= (1 + degisim_yuzde / 100)
                equity_egrisi.append(equity)
                islemler.append({
                    "giris_tarihi": str(giris_tarihi.date()),
                    "cikis_tarihi": str(veri.index[i].date()),
                    "giris_fiyati": round(float(giris_fiyati), 2),
                    "cikis_fiyati": round(float(satir["Close"]), 2),
                    "getiri_yuzde": round(degisim_yuzde, 2),
                })
                pozisyonda = False
                giris_fiyati = None

    if pozisyonda:
        son_fiyat = veri["Close"].iloc[-1]
        degisim_yuzde = 100 * (son_fiyat - giris_fiyati) / giris_fiyati
        equity *= (1 + degisim_yuzde / 100)
        equity_egrisi.append(equity)
        islemler.append({
            "giris_tarihi": str(giris_tarihi.date()),
            "cikis_tarihi": str(veri.index[-1].date()) + " (açık pozisyon, test sonunda kapatıldı)",
            "giris_fiyati": round(float(giris_fiyati), 2),
            "cikis_fiyati": round(float(son_fiyat), 2),
            "getiri_yuzde": round(degisim_yuzde, 2),
        })

    kazançlar = [t["getiri_yuzde"] for t in islemler if t["getiri_yuzde"] > 0]
    zararlar = [t["getiri_yuzde"] for t in islemler if t["getiri_yuzde"] <= 0]

    toplam_getiri_yuzde = round(100 * (equity - baslangic_sermaye) / baslangic_sermaye, 2)
    kazancli_islem_yuzdesi = round(100 * len(kazançlar) / len(islemler), 1) if islemler else None

    try:
        endeks_veri = bist100_getir(periyot=periyot)
        bist100_getiri_yuzde = round(
            100 * (endeks_veri["Close"].iloc[-1] - endeks_veri["Close"].iloc[0]) / endeks_veri["Close"].iloc[0], 2
        )
    except Exception as hata:
        log.warning(f"BIST 100 karşılaştırması alınamadı: {hata}")
        bist100_getiri_yuzde = None

    return {
        "sembol": sembol,
        "periyot": periyot,
        "toplam_getiri_yuzde": toplam_getiri_yuzde,
        "islem_sayisi": len(islemler),
        "kazancli_islem_yuzdesi": kazancli_islem_yuzdesi,
        "ortalama_kazanc_yuzde": round(sum(kazançlar) / len(kazançlar), 2) if kazançlar else None,
        "ortalama_zarar_yuzde": round(sum(zararlar) / len(zararlar), 2) if zararlar else None,
        "maksimum_dusus_yuzde": _maksimum_dusus_hesapla(equity_egrisi),
        "bist100_getiri_yuzde": bist100_getiri_yuzde,
        "islemler": islemler,
    }