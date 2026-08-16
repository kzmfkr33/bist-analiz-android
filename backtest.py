import statistics

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


def _profit_factor_hesapla(kazançlar, zararlar):
    """Toplam kazanç / toplam zarar (mutlak). Hiç zarar yoksa None döner (sonsuz demektir)."""
    toplam_kazanc = sum(kazançlar)
    toplam_zarar = abs(sum(zararlar))
    if toplam_zarar == 0:
        return None
    return round(toplam_kazanc / toplam_zarar, 2)


def _sharpe_sortino_hesapla(getiriler):
    """
    İşlem bazlı (günlük değil) basit Sharpe/Sortino yaklaşımı — risksiz
    getiri oranı 0 kabul edilir (basitleştirme). Sortino, sadece negatif
    getirilerin standart sapmasını (downside deviation) kullanır.
    """
    if len(getiriler) < 2:
        return None, None
    ortalama = statistics.mean(getiriler)
    std_sapma = statistics.pstdev(getiriler)
    sharpe = round(ortalama / std_sapma, 2) if std_sapma > 0 else None

    negatifler = [g for g in getiriler if g < 0]
    if len(negatifler) >= 2:
        downside_std = statistics.pstdev(negatifler)
    elif len(negatifler) == 1:
        downside_std = abs(negatifler[0])
    else:
        downside_std = 0
    sortino = round(ortalama / downside_std, 2) if downside_std > 0 else None

    return sharpe, sortino


def _max_ardisik_zarar_hesapla(islemler):
    """En uzun ardışık zararlı işlem serisi (Maximum Consecutive Loss)."""
    en_uzun = 0
    guncel = 0
    for t in islemler:
        if t["getiri_yuzde"] <= 0:
            guncel += 1
            en_uzun = max(en_uzun, guncel)
        else:
            guncel = 0
    return en_uzun


def _expectancy_hesapla(kazançlar, zararlar, toplam_islem):
    """
    Expectancy: bir işlem başına ortalama beklenen getiri yüzdesi
    (kazanma_oranı × ort_kazanç) + (kaybetme_oranı × ort_zarar).
    """
    if toplam_islem == 0:
        return None
    kazanma_orani = len(kazançlar) / toplam_islem
    kaybetme_orani = len(zararlar) / toplam_islem
    ort_kazanc = sum(kazançlar) / len(kazançlar) if kazançlar else 0
    ort_zarar = sum(zararlar) / len(zararlar) if zararlar else 0
    return round(kazanma_orani * ort_kazanc + kaybetme_orani * ort_zarar, 2)


def backtest_calistir(sembol, al_kosullari, sat_kosullari=None, stop_yuzdesi=None,
                       kar_al_yuzdesi=None, periyot="1y", baslangic_sermaye=100000,
                       komisyon_yuzdesi=0.0, slippage_yuzdesi=0.0):
    """
    komisyon_yuzdesi: her işlem (giriş + çıkış toplamda 2 kez) için maliyet
        yüzdesi (örn. 0.1 = binde 1). Varsayılan 0 — belirtmezsen komisyonsuz test edilir.
    slippage_yuzdesi: kayma payı, komisyonla aynı mantıkta uygulanır.
    """
    veri = analiz_et(sembol, periyot=periyot)
    islem_maliyeti_yuzde = 2 * (komisyon_yuzdesi + slippage_yuzdesi)

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
                net_getiri_yuzde = degisim_yuzde - islem_maliyeti_yuzde
                equity *= (1 + net_getiri_yuzde / 100)
                equity_egrisi.append(equity)
                islemler.append({
                    "giris_tarihi": str(giris_tarihi.date()),
                    "cikis_tarihi": str(veri.index[i].date()),
                    "giris_fiyati": round(float(giris_fiyati), 2),
                    "cikis_fiyati": round(float(satir["Close"]), 2),
                    "getiri_yuzde": round(net_getiri_yuzde, 2),
                })
                pozisyonda = False
                giris_fiyati = None

    if pozisyonda:
        son_fiyat = veri["Close"].iloc[-1]
        degisim_yuzde = 100 * (son_fiyat - giris_fiyati) / giris_fiyati
        net_getiri_yuzde = degisim_yuzde - islem_maliyeti_yuzde
        equity *= (1 + net_getiri_yuzde / 100)
        equity_egrisi.append(equity)
        islemler.append({
            "giris_tarihi": str(giris_tarihi.date()),
            "cikis_tarihi": str(veri.index[-1].date()) + " (açık pozisyon, test sonunda kapatıldı)",
            "giris_fiyati": round(float(giris_fiyati), 2),
            "cikis_fiyati": round(float(son_fiyat), 2),
            "getiri_yuzde": round(net_getiri_yuzde, 2),
        })

    kazançlar = [t["getiri_yuzde"] for t in islemler if t["getiri_yuzde"] > 0]
    zararlar = [t["getiri_yuzde"] for t in islemler if t["getiri_yuzde"] <= 0]
    tum_getiriler = [t["getiri_yuzde"] for t in islemler]

    toplam_getiri_yuzde = round(100 * (equity - baslangic_sermaye) / baslangic_sermaye, 2)
    kazancli_islem_yuzdesi = round(100 * len(kazançlar) / len(islemler), 1) if islemler else None

    sharpe, sortino = _sharpe_sortino_hesapla(tum_getiriler)

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
        "profit_factor": _profit_factor_hesapla(kazançlar, zararlar),
        "sharpe_ratio": sharpe,
        "sortino_ratio": sortino,
        "expectancy_yuzde": _expectancy_hesapla(kazançlar, zararlar, len(islemler)),
        "maksimum_ardisik_zarar": _max_ardisik_zarar_hesapla(islemler),
        "bist100_getiri_yuzde": bist100_getiri_yuzde,
        "islemler": islemler,
    }