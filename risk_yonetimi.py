from veri_katmani import fiyat_verisi_getir
from gostergeler import atr_hesapla


def pozisyon_buyuklugu_hesapla(toplam_sermaye, risk_yuzdesi, giris_fiyati, stop_fiyati):
    """
    'Bu işlemde en fazla ne kadar kaybetmeyi göze alıyorum' mantığıyla
    kaç adet hisse alman gerektiğini hesaplar.

    toplam_sermaye: elindeki toplam yatırım parası (TL)
    risk_yuzdesi: bu TEK işlemde riske atmayı kabul ettiğin yüzde (örn. 2)
    giris_fiyati: almayı düşündüğün fiyat
    stop_fiyati: stop-loss koyacağın fiyat (giriş fiyatının altında)
    """
    if stop_fiyati >= giris_fiyati:
        raise ValueError("Stop fiyatı giriş fiyatından düşük olmalı (uzun pozisyon için)")

    riske_edilecek_tutar = toplam_sermaye * (risk_yuzdesi / 100)
    hisse_basi_risk = giris_fiyati - stop_fiyati
    adet = int(riske_edilecek_tutar / hisse_basi_risk)

    toplam_maliyet = adet * giris_fiyati

    return {
        "onerilen_adet": adet,
        "toplam_maliyet": round(toplam_maliyet, 2),
        "riske_edilecek_tutar": round(riske_edilecek_tutar, 2),
        "sermayeye_orani_yuzde": round((toplam_maliyet / toplam_sermaye) * 100, 1) if toplam_sermaye else 0,
    }


def atr_ile_stop_onerisi(sembol, giris_fiyati=None, atr_carpani=2):
    """
    ATR (ortalama günlük oynaklık) baz alınarak makul bir stop-loss
    seviyesi önerir. Mantık: hissenin normal günlük hareketinin
    'atr_carpani' katı kadar altına stop koy — çok yakın stop koyup
    normal dalgalanmada elenmeyi önler.
    """
    veri = fiyat_verisi_getir(sembol, periyot="2mo")
    veri['ATR'] = atr_hesapla(veri)
    son_atr = veri['ATR'].iloc[-1]
    guncel_fiyat = veri['Close'].iloc[-1]

    if giris_fiyati is None:
        giris_fiyati = guncel_fiyat

    onerilen_stop = giris_fiyati - (son_atr * atr_carpani)
    risk_yuzdesi = ((giris_fiyati - onerilen_stop) / giris_fiyati) * 100

    return {
        "sembol": sembol,
        "guncel_fiyat": round(guncel_fiyat, 2),
        "atr": round(son_atr, 2),
        "onerilen_giris": round(giris_fiyati, 2),
        "onerilen_stop": round(onerilen_stop, 2),
        "stop_mesafesi_yuzde": round(risk_yuzdesi, 2),
    }


if __name__ == "__main__":
    sembol = "THYAO.IS"

    stop_onerisi = atr_ile_stop_onerisi(sembol)
    print(f"--- {sembol} Stop-Loss Önerisi ---")
    for k, v in stop_onerisi.items():
        print(f"{k}: {v}")

    print("\n--- Pozisyon Büyüklüğü Örneği ---")
    sonuc = pozisyon_buyuklugu_hesapla(
        toplam_sermaye=100000,
        risk_yuzdesi=2,
        giris_fiyati=stop_onerisi["onerilen_giris"],
        stop_fiyati=stop_onerisi["onerilen_stop"],
    )
    for k, v in sonuc.items():
        print(f"{k}: {v}")