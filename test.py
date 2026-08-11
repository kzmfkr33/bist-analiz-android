from veri_katmani import fiyat_verisi_getir, temel_veri_getir
from gostergeler import (
    rsi_hesapla, hareketli_ortalama, ema_hesapla, macd_hesapla, bollinger_bantlari,
    stochastic_hesapla, atr_hesapla, obv_hesapla, adx_hesapla, cci_hesapla,
    williams_r_hesapla, roc_hesapla, relative_volume_hesapla, mfi_hesapla,
    cmf_hesapla, keltner_kanali, standart_sapma_hesapla, supertrend_hesapla,
    vwma_hesapla,
)
from sinyal_motoru import sinyal_uret
from temel_analiz import temel_puanla


def analiz_et(sembol, periyot="3mo"):
    """
    Teknik analiz için tüm göstergeleri hesaplar. Varsayılan periyot ekran
    taramaları için hızlı olsun diye "3mo"; Backtest gibi daha uzun geçmiş
    gerektiren modüller periyot="1y" veya "2y" ile çağırabilir.
    """
    veri = fiyat_verisi_getir(sembol, periyot=periyot)
    veri['RSI'] = rsi_hesapla(veri)
    veri['SMA20'] = hareketli_ortalama(veri, 20)
    veri['SMA50'] = hareketli_ortalama(veri, 50)
    veri['EMA20'] = ema_hesapla(veri, 20)
    veri['EMA50'] = ema_hesapla(veri, 50)

    macd_cizgisi, sinyal_cizgisi = macd_hesapla(veri)
    veri['MACD'] = macd_cizgisi
    veri['MACD_Sinyal'] = sinyal_cizgisi

    ust, orta, alt = bollinger_bantlari(veri)
    veri['BB_Ust'] = ust
    veri['BB_Alt'] = alt

    k, d = stochastic_hesapla(veri)
    veri['Stoch_K'] = k
    veri['Stoch_D'] = d

    veri['ATR'] = atr_hesapla(veri)
    veri['OBV'] = obv_hesapla(veri)

    adx, pdi, ndi = adx_hesapla(veri)
    veri['ADX'] = adx
    veri['PDI'] = pdi
    veri['NDI'] = ndi

    veri['CCI'] = cci_hesapla(veri)
    veri['Williams_R'] = williams_r_hesapla(veri)
    veri['ROC'] = roc_hesapla(veri)
    veri['RVOL'] = relative_volume_hesapla(veri)
    veri['MFI'] = mfi_hesapla(veri)
    veri['CMF'] = cmf_hesapla(veri)

    kk_ust, kk_orta, kk_alt = keltner_kanali(veri)
    veri['Keltner_Ust'] = kk_ust
    veri['Keltner_Alt'] = kk_alt
    veri['StdSapma'] = standart_sapma_hesapla(veri)

    st, st_yon = supertrend_hesapla(veri)
    veri['Supertrend'] = st
    veri['Supertrend_Yon'] = st_yon

    veri['VWMA20'] = vwma_hesapla(veri, 20)

    return veri


def tam_analiz_et(sembol):
    """
    Teknik + temel analizi birleştirir. Daha yavaştır (ekstra sorgu
    gerektirir), bu yüzden tüm BIST'i taramak için değil, öne çıkan
    birkaç hisseyi derinlemesine incelemek için kullanılır.
    """
    teknik_veri = analiz_et(sembol)
    teknik_sonuc = sinyal_uret(teknik_veri)

    temel_veri = temel_veri_getir(sembol)
    temel_sonuc = temel_puanla(temel_veri)

    birlesik_puan = teknik_sonuc["puan"] + temel_sonuc["temel_puan"]

    if birlesik_puan >= 4:
        birlesik_genel = "GÜÇLÜ OLUMLU (teknik + temel uyumlu)"
    elif birlesik_puan <= -4:
        birlesik_genel = "GÜÇLÜ OLUMSUZ (teknik + temel uyumlu)"
    else:
        birlesik_genel = "KARIŞIK — teknik ve temel görünüm birbirini tam desteklemiyor olabilir"

    return {
        "sembol": sembol,
        "sirket_adi": temel_veri.get("sirket_adi"),
        "kapanis_fiyati": teknik_sonuc["kapanis_fiyati"],
        "teknik_puan": teknik_sonuc["puan"],
        "teknik_detaylar": teknik_sonuc["detaylar"],
        "temel_puan": temel_sonuc["temel_puan"],
        "temel_detaylar": temel_sonuc["temel_bulgular"],
        "birlesik_puan": birlesik_puan,
        "birlesik_genel": birlesik_genel,
    }


if __name__ == "__main__":
    sembol = "THYAO.IS"
    sonuc = tam_analiz_et(sembol)

    print(f"\n=== {sonuc['sirket_adi']} ({sonuc['sembol']}) TAM ANALİZ ===")
    print(f"Kapanış: {sonuc['kapanis_fiyati']:.2f} TL\n")

    print(f"Teknik puan: {sonuc['teknik_puan']}")
    for d in sonuc['teknik_detaylar']:
        print(f"  - {d}")

    print(f"\nTemel puan: {sonuc['temel_puan']}")
    for d in sonuc['temel_detaylar']:
        print(f"  - {d}")

    print(f"\n>>> BİRLEŞİK DEĞERLENDİRME: {sonuc['birlesik_genel']} (toplam puan: {sonuc['birlesik_puan']})")
