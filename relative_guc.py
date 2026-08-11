"""
Relative Strength — plan madde 13.
Bir hissenin BIST 100 endeksine göre göreceli performansını ölçer.
Pozitif değer = hisse endeksten daha güçlü; negatif = endeksten zayıf.
Bu, piyasanın genelinden daha güçlü hisseleri otomatik bulmak için kullanılır.
"""

from veri_katmani import fiyat_verisi_getir, ENDEKS_SEMBOLLERI


def _getiri_yuzde(kapanislar, gun):
    if len(kapanislar) <= gun:
        return None
    return 100 * (kapanislar.iloc[-1] - kapanislar.iloc[-1 - gun]) / kapanislar.iloc[-1 - gun]


def relative_strength_hesapla(hisse_veri, endeks_veri):
    """
    hisse_veri, endeks_veri: fiyat_verisi_getir() çıktısı DataFrame'ler
    (anlamlı bir kıyas için aynı periyotla çekilmiş olmaları gerekir).

    Dönüş: {"1g": ..., "1h": ..., "1a": ..., "genel_rs": ...}
    Değerler yüzde PUAN farkı cinsindendir (hisse getirisi - endeks getirisi).
    """
    periyotlar = {"1g": 1, "1h": 5, "1a": 21}
    sonuc = {}

    for etiket, gun in periyotlar.items():
        hisse_getiri = _getiri_yuzde(hisse_veri["Close"], gun)
        endeks_getiri = _getiri_yuzde(endeks_veri["Close"], gun)
        if hisse_getiri is not None and endeks_getiri is not None:
            sonuc[etiket] = round(hisse_getiri - endeks_getiri, 2)
        else:
            sonuc[etiket] = None

    gecerli = [v for v in sonuc.values() if v is not None]
    sonuc["genel_rs"] = round(sum(gecerli) / len(gecerli), 2) if gecerli else None

    return sonuc


def bist100_getir(periyot="3mo"):
    """Kısayol: BIST 100 endeks verisini çeker (relative strength hesapları için)."""
    return fiyat_verisi_getir(ENDEKS_SEMBOLLERI["BIST 100"], periyot=periyot)


if __name__ == "__main__":
    from test import analiz_et

    sembol = "THYAO.IS"
    hisse_veri = analiz_et(sembol)
    endeks_veri = bist100_getir()

    rs = relative_strength_hesapla(hisse_veri, endeks_veri)
    print(f"\n=== {sembol} RELATIVE STRENGTH (BIST 100'e göre) ===")
    for k, v in rs.items():
        isaret = "+" if (v is not None and v > 0) else ""
        print(f"  {k}: {isaret}{v}")