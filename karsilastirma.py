"""
Hisse Karşılaştırma — plan madde 14.
İki veya daha fazla hisseyi getiri, RSI, volatilite, F/K, PD/DD, ROE,
hacim, teknik/temel/genel skor ve relative strength açısından yan yana
karşılaştırır.
"""

from test import analiz_et
from veri_katmani import temel_veri_getir
from hisse_skoru import hisse_skoru_hesapla
from relative_guc import relative_strength_hesapla, bist100_getir


def hisseleri_karsilastir(semboller):
    """
    semboller: ["THYAO.IS", "ASELS.IS", ...] (2 veya daha fazla)
    Dönüş: {sembol: {...karşılaştırma alanları...}} — bir alan çekilemezse
    o hisse için sadece "hata" anahtarı döner, diğer hisseler etkilenmez.
    """
    endeks_veri = bist100_getir()
    sonuc = {}

    for sembol in semboller:
        try:
            veri = analiz_et(sembol)
            temel = temel_veri_getir(sembol)
            skor = hisse_skoru_hesapla(veri, temel)
            rs = relative_strength_hesapla(veri, endeks_veri)
            son = veri.iloc[-1]

            kapanislar = veri["Close"]
            degisim_1h = (
                100 * (kapanislar.iloc[-1] - kapanislar.iloc[-6]) / kapanislar.iloc[-6]
                if len(kapanislar) > 6 else None
            )

            sonuc[sembol] = {
                "sirket_adi": temel.get("sirket_adi"),
                "kapanis": round(float(son["Close"]), 2),
                "degisim_1h_yuzde": round(degisim_1h, 2) if degisim_1h is not None else None,
                "rsi": round(float(son["RSI"]), 1) if son.get("RSI") == son.get("RSI") else None,
                "atr_yuzde": round(float(son["ATR"] / son["Close"] * 100), 2)
                             if son.get("ATR") == son.get("ATR") else None,
                "fk_orani": temel.get("fk_orani"),
                "pd_dd_orani": temel.get("pd_dd_orani"),
                "roe": temel.get("roe"),
                "gunluk_hacim": int(son["Volume"]) if son.get("Volume") == son.get("Volume") else None,
                "teknik_skor": skor["teknik"]["puan"],
                "temel_skor": skor["temel"]["puan"],
                "genel_skor": skor["genel"],
                "relative_strength_1h": rs.get("1h"),
            }
        except Exception as hata:
            sonuc[sembol] = {"hata": str(hata)}

    return sonuc


if __name__ == "__main__":
    karsilastirma = hisseleri_karsilastir(["THYAO.IS", "PGSUS.IS", "TAVHL.IS"])

    print("\n=== HİSSE KARŞILAŞTIRMA ===")
    for sembol, veri in karsilastirma.items():
        print(f"\n{sembol}:")
        for alan, deger in veri.items():
            print(f"  {alan}: {deger}")