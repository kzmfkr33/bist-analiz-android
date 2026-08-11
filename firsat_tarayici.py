"""
Fırsat Tarayıcı — plan madde 19.
Tek bir hissenin verisinde belirli teknik olayları tespit eder:
yeni yükseliş trendi, hacim patlaması, direnç kırılması, yeni zirve,
RSI dönüşü, MACD kesişimi, Golden Cross, Bollinger breakout, güçlü momentum.

Her fonksiyon bağımsız çalışır ve True/False (veya None — veri yetersizse)
döner; firsatlari_tespit_et() hepsini birleştirip eşleşen etiketleri listeler.
"""

from destek_direnc import destek_direnc_bul


def yeni_yukselis_trendi_mi(veri):
    """Son 3 günde EMA20, EMA50'yi YUKARI kesti mi (yeni trend başlangıcı)."""
    if "EMA20" not in veri.columns or len(veri) < 4:
        return None
    for i in range(-3, 0):
        onceki_fark = veri["EMA20"].iloc[i - 1] - veri["EMA50"].iloc[i - 1]
        simdiki_fark = veri["EMA20"].iloc[i] - veri["EMA50"].iloc[i]
        if onceki_fark <= 0 < simdiki_fark:
            return True
    return False


def hacim_patlamasi_mi(veri, esik=3.0):
    """Bugünkü hacim, ortalamanın 'esik' katından fazla mı (RVOL)."""
    if "RVOL" not in veri.columns:
        return None
    son_rvol = veri["RVOL"].iloc[-1]
    return bool(son_rvol >= esik) if son_rvol == son_rvol else None  # NaN kontrolü


def direnc_kirilmasi_mi(veri):
    """Fiyat, en yakın direnç seviyesini son 2 günde yukarı kırdı mı."""
    if len(veri) < 20:
        return None
    onceki_kapanis = float(veri["Close"].iloc[-2])
    son_kapanis = float(veri["Close"].iloc[-1])

    onceki_seviyeler = destek_direnc_bul(veri.iloc[:-1], guncel_fiyat=onceki_kapanis)
    if not onceki_seviyeler["direncler"]:
        return False
    en_yakin_direnc = onceki_seviyeler["direncler"][0]["seviye"]

    return onceki_kapanis < en_yakin_direnc <= son_kapanis


def yeni_zirve_mi(veri, periyot=63):
    """Son kapanış, son 'periyot' günün en yükseği mi (63 gün ~ 3 ay)."""
    if len(veri) < periyot:
        return None
    son_kapanis = veri["Close"].iloc[-1]
    periyot_yuksegi = veri["High"].iloc[-periyot:].max()
    return bool(son_kapanis >= periyot_yuksegi)


def rsi_donusu_mu(veri):
    """RSI son 3 günde 30 altından yukarı (boğa dönüşü) çıktı mı."""
    if "RSI" not in veri.columns or len(veri) < 4:
        return None
    son_rsi = veri["RSI"].iloc[-4:]
    return bool((son_rsi.iloc[:-1] < 30).any() and son_rsi.iloc[-1] >= 30)


def macd_kesisimi_mi(veri):
    """MACD, sinyal çizgisini son günde YUKARI kesti mi (Golden Cross benzeri, kısa vadeli)."""
    if "MACD" not in veri.columns or len(veri) < 2:
        return None
    onceki_fark = veri["MACD"].iloc[-2] - veri["MACD_Sinyal"].iloc[-2]
    son_fark = veri["MACD"].iloc[-1] - veri["MACD_Sinyal"].iloc[-1]
    return bool(onceki_fark <= 0 < son_fark)


def golden_cross_mu(veri):
    """SMA50, SMA200'ü son 5 günde yukarı kesti mi. En az 200 günlük veri gerekir (1y periyot)."""
    if "SMA50" not in veri.columns or len(veri) < 205:
        return None
    sma200 = veri["Close"].rolling(200).mean()
    for i in range(-5, 0):
        onceki_fark = veri["SMA50"].iloc[i - 1] - sma200.iloc[i - 1]
        simdiki_fark = veri["SMA50"].iloc[i] - sma200.iloc[i]
        if onceki_fark <= 0 < simdiki_fark:
            return True
    return False


def bollinger_breakout_mu(veri):
    """Fiyat üst Bollinger bandını son günde yukarı kırdı mı."""
    if "BB_Ust" not in veri.columns or len(veri) < 2:
        return None
    onceki_alt = veri["Close"].iloc[-2] <= veri["BB_Ust"].iloc[-2]
    son_ust = veri["Close"].iloc[-1] > veri["BB_Ust"].iloc[-1]
    return bool(onceki_alt and son_ust)


def guclu_momentum_mu(veri, esik_roc=5.0):
    """ROC (12 gün) belirli bir eşiğin üzerinde mi — hızlı ve güçlü fiyat hareketi."""
    if "ROC" not in veri.columns:
        return None
    son_roc = veri["ROC"].iloc[-1]
    return bool(son_roc >= esik_roc) if son_roc == son_roc else None


def firsatlari_tespit_et(veri):
    """
    Bir hissenin tüm fırsat türlerini kontrol eder, eşleşenlerin
    isim listesini döner. Veri yetersizse (None dönenler) o tür atlanır.
    """
    kontroller = {
        "Yeni Yükseliş Trendi": yeni_yukselis_trendi_mi(veri),
        "Hacim Patlaması": hacim_patlamasi_mi(veri),
        "Direnç Kırılması": direnc_kirilmasi_mi(veri),
        "Yeni Zirve": yeni_zirve_mi(veri),
        "RSI Dönüşü": rsi_donusu_mu(veri),
        "MACD Kesişimi": macd_kesisimi_mi(veri),
        "Golden Cross": golden_cross_mu(veri),
        "Bollinger Breakout": bollinger_breakout_mu(veri),
        "Güçlü Momentum": guclu_momentum_mu(veri),
    }
    return [isim for isim, sonuc in kontroller.items() if sonuc is True]


if __name__ == "__main__":
    from test import analiz_et

    sembol = "THYAO.IS"
    veri = analiz_et(sembol)
    firsatlar = firsatlari_tespit_et(veri)

    print(f"\n=== {sembol} FIRSAT TARAMASI ===")
    if firsatlar:
        for f in firsatlar:
            print(f"  ✓ {f}")
    else:
        print("  Şu an belirgin bir fırsat sinyali yok.")