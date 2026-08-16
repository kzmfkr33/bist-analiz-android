"""
Market Regime tespiti — belge Bölüm 5, 6.
BULL TREND, BEAR TREND, SIDEWAYS, HIGH VOLATILITY, TRANSITION rejimlerini
EMA20/50/200 dizilimi, SuperTrend yönü, ADX gücü ve ATR/volatilite bazlı
persentil ile tespit eder.

Repainting yasağı: tüm hesaplamalar sadece SON KAPANMIŞ mum (veri.iloc[-1])
üzerinden yapılır, gelecek veri kullanılmaz.
"""
from gostergeler import ema_hesapla, adx_hesapla, supertrend_hesapla, atr_hesapla
from csm_config import EMA_TREND, ADX_CONFIG, SUPERTREND_CONFIG


def market_regime_hesapla(veri):
    """
    veri: OHLCV DataFrame (EMA200'ün anlamlı olması için en az ~200+ satır
    önerilir — periyot="1y" veya "2y" ile çekilmiş veri kullan).

    Dönüş: {"rejim": str, "ema20":, "ema50":, "ema200":, "adx":,
            "supertrend_yon":, "atr_yuzde":, "atr_percentile":}
    """
    ema20 = ema_hesapla(veri, EMA_TREND["kisa"])
    ema50 = ema_hesapla(veri, EMA_TREND["orta"])
    ema200 = ema_hesapla(veri, EMA_TREND["uzun"])
    adx, pdi, ndi = adx_hesapla(veri, ADX_CONFIG["length"])
    st, st_yon = supertrend_hesapla(veri, SUPERTREND_CONFIG["atr_period"], SUPERTREND_CONFIG["carpan"])
    atr = atr_hesapla(veri, 14)
    atr_yuzde = (atr / veri["Close"]) * 100

    son_ema20 = ema20.iloc[-1]
    son_ema50 = ema50.iloc[-1]
    son_ema200 = ema200.iloc[-1] if len(veri) >= 200 else None
    son_adx = adx.iloc[-1]
    son_st_yon = st_yon.iloc[-1]
    son_atr_yuzde = atr_yuzde.iloc[-1]

    # Volatilite persentili — bugünün ATR%'si son 100 günün neresinde
    atr_yuzde_gecmis = atr_yuzde.dropna().iloc[-100:]
    if len(atr_yuzde_gecmis) >= 20:
        atr_percentile = float((atr_yuzde_gecmis < son_atr_yuzde).mean() * 100)
    else:
        atr_percentile = None

    adx_guclu = son_adx >= ADX_CONFIG["guclu_esik"]

    if son_ema200 is not None:
        bull_dizilim = son_ema20 > son_ema50 > son_ema200
        bear_dizilim = son_ema20 < son_ema50 < son_ema200
    else:
        # EMA200 için yeterli veri yoksa sadece EMA20/50'ye bak (daha zayıf teyit)
        bull_dizilim = son_ema20 > son_ema50
        bear_dizilim = son_ema20 < son_ema50

    ema_sikisik = abs(son_ema20 - son_ema50) / son_ema50 * 100 < 1.0
    yuksek_volatilite = atr_percentile is not None and atr_percentile >= 85

    if yuksek_volatilite:
        rejim = "HIGH VOLATILITY"
    elif bull_dizilim and son_st_yon == 1 and adx_guclu:
        rejim = "BULL TREND"
    elif bear_dizilim and son_st_yon == -1 and adx_guclu:
        rejim = "BEAR TREND"
    elif ema_sikisik and not adx_guclu:
        rejim = "SIDEWAYS"
    else:
        rejim = "TRANSITION"

    return {
        "rejim": rejim,
        "ema20": round(float(son_ema20), 2),
        "ema50": round(float(son_ema50), 2),
        "ema200": round(float(son_ema200), 2) if son_ema200 is not None else None,
        "adx": round(float(son_adx), 1) if son_adx == son_adx else None,
        "supertrend_yon": int(son_st_yon),
        "atr_yuzde": round(float(son_atr_yuzde), 2) if son_atr_yuzde == son_atr_yuzde else None,
        "atr_percentile": round(atr_percentile, 1) if atr_percentile is not None else None,
    }


def rejim_agirlik_carpani(rejim):
    """
    Belge Bölüm 6: 'Market Regime, diğer sinyallerin ağırlığını
    etkileyebilmelidir.' Trend ve Breakout motorlarının ağırlığına
    rejime göre hafif bir çarpan uygular (yatay piyasada trend motorları
    zayıflatılır, breakout motoru güçlendirilir, vb.).
    """
    carpanlar = {
        "BULL TREND": {"trend": 1.15, "breakout": 0.90},
        "BEAR TREND": {"trend": 1.15, "breakout": 0.90},
        "SIDEWAYS": {"trend": 0.75, "breakout": 1.20},
        "HIGH VOLATILITY": {"trend": 0.85, "breakout": 1.10},
        "TRANSITION": {"trend": 0.85, "breakout": 1.00},
    }
    return carpanlar.get(rejim, {"trend": 1.0, "breakout": 1.0})