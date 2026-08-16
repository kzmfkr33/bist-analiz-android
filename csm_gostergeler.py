"""
BIST Composite Signal Engine — özel gösterge hesaplamaları.
Standart göstergeler (ATR, ADX, EMA, RSI, Bollinger, Keltner, MFI, Supertrend)
zaten gostergeler.py'de var — burada SADECE bu motöre özel, oralarda
bulunmayan göstergeler var: UT Bot Pro, AlphaTrend (Adım A);
QQE MOD, SSL Hybrid, Waddah Attar Explosion, Squeeze Momentum (Adım B'de eklenecek).

Repainting yasağı: tüm hesaplamalar SADECE kapanmış mum verisiyle yapılır,
hiçbir yerde gelecek veriye bakılmaz (lookahead yok).
"""
import numpy as np
import pandas as pd

from gostergeler import atr_hesapla, mfi_hesapla
from csm_config import UT_BOT, ALPHA_TREND


def ut_bot_pro_hesapla(veri, key_value=None, atr_period=None):
    """
    UT Bot Pro — ATR tabanlı iz süren stop (trailing stop) ve yön tespiti.
    Referans: yaygın UT Bot Pro Pine Script mantığı.

    Dönüş: (trailing_stop: Series, yon: Series [1=yükseliş, -1=düşüş])
    """
    key_value = key_value or UT_BOT["key_value"]
    atr_period = atr_period or UT_BOT["atr_period"]

    kapanis = veri["Close"]
    n_loss = key_value * atr_hesapla(veri, atr_period)

    trailing_stop = pd.Series(0.0, index=veri.index)
    yon = pd.Series(1, index=veri.index)

    trailing_stop.iloc[0] = kapanis.iloc[0] - n_loss.iloc[0]

    for i in range(1, len(veri)):
        src = kapanis.iloc[i]
        src_onceki = kapanis.iloc[i - 1]
        stop_onceki = trailing_stop.iloc[i - 1]
        kayip = n_loss.iloc[i]

        if pd.isna(kayip):
            trailing_stop.iloc[i] = stop_onceki
            yon.iloc[i] = yon.iloc[i - 1]
            continue

        if src > stop_onceki and src_onceki > stop_onceki:
            trailing_stop.iloc[i] = max(stop_onceki, src - kayip)
        elif src < stop_onceki and src_onceki < stop_onceki:
            trailing_stop.iloc[i] = min(stop_onceki, src + kayip)
        elif src > stop_onceki:
            trailing_stop.iloc[i] = src - kayip
        else:
            trailing_stop.iloc[i] = src + kayip

        if src_onceki < stop_onceki and src > trailing_stop.iloc[i]:
            yon.iloc[i] = 1
        elif src_onceki > stop_onceki and src < trailing_stop.iloc[i]:
            yon.iloc[i] = -1
        else:
            yon.iloc[i] = yon.iloc[i - 1]

    return trailing_stop, yon


def alpha_trend_hesapla(veri, period=None, coefficient=None):
    """
    AlphaTrend — ATR ve MFI (hacimli momentum) tabanlı ikinci bağımsız trend
    doğrulama çizgisi. Referans: Kıvanç Özbilgiç açık kaynak versiyonu.

    Dönüş: (alpha_trend: Series, yon: Series [1=yükseliş, -1=düşüş])
    """
    period = period or ALPHA_TREND["period"]
    coefficient = coefficient or ALPHA_TREND["coefficient"]

    atr = atr_hesapla(veri, period)
    mfi = mfi_hesapla(veri, period)

    up_t = veri["Low"] - atr * coefficient
    down_t = veri["High"] + atr * coefficient

    alpha_trend = pd.Series(0.0, index=veri.index)
    yon = pd.Series(1, index=veri.index)

    ilk_gecerli = period  # MFI/ATR bu noktadan önce NaN olabilir
    alpha_trend.iloc[:ilk_gecerli] = up_t.iloc[:ilk_gecerli].fillna(method="bfill")

    for i in range(ilk_gecerli, len(veri)):
        onceki = alpha_trend.iloc[i - 1]
        if pd.isna(mfi.iloc[i]):
            alpha_trend.iloc[i] = onceki
            continue

        if mfi.iloc[i] >= 50:
            alpha_trend.iloc[i] = max(up_t.iloc[i], onceki)
        else:
            alpha_trend.iloc[i] = min(down_t.iloc[i], onceki)

        if alpha_trend.iloc[i] > alpha_trend.iloc[i - 1]:
            yon.iloc[i] = 1
        elif alpha_trend.iloc[i] < alpha_trend.iloc[i - 1]:
            yon.iloc[i] = -1
        else:
            yon.iloc[i] = yon.iloc[i - 1]

    return alpha_trend, yon
# ---------------------------------------------------------------------------
# QQE MOD — Momentum motoru bileşeni
# Not: Topluluk QQE MOD sürümlerinin birebir aynısı değildir; standart QQE
# mantığı (RSI + Wilders ATR bantları) referans alınarak uygulanmıştır.
# ---------------------------------------------------------------------------
def _qqe_cizgisi(rsi, rsi_smoothing, qqe_factor):
    rsi_ma = rsi.ewm(span=rsi_smoothing, adjust=False).mean()
    atr_rsi = (rsi_ma - rsi_ma.shift(1)).abs()
    wilders_periyot = rsi_smoothing * 2 - 1
    ma_atr_rsi = atr_rsi.ewm(alpha=1 / wilders_periyot, adjust=False).mean()
    dar = ma_atr_rsi.ewm(alpha=1 / wilders_periyot, adjust=False).mean() * qqe_factor

    longband = pd.Series(0.0, index=rsi.index)
    shortband = pd.Series(0.0, index=rsi.index)
    trend = pd.Series(1, index=rsi.index)

    for i in range(1, len(rsi)):
        yeni_short = rsi_ma.iloc[i] + dar.iloc[i]
        yeni_long = rsi_ma.iloc[i] - dar.iloc[i]

        if rsi_ma.iloc[i - 1] > longband.iloc[i - 1] and rsi_ma.iloc[i] > longband.iloc[i - 1]:
            longband.iloc[i] = max(longband.iloc[i - 1], yeni_long)
        else:
            longband.iloc[i] = yeni_long

        if rsi_ma.iloc[i - 1] < shortband.iloc[i - 1] and rsi_ma.iloc[i] < shortband.iloc[i - 1]:
            shortband.iloc[i] = min(shortband.iloc[i - 1], yeni_short)
        else:
            shortband.iloc[i] = yeni_short

        if rsi_ma.iloc[i] > shortband.iloc[i - 1]:
            trend.iloc[i] = 1
        elif rsi_ma.iloc[i] < longband.iloc[i - 1]:
            trend.iloc[i] = -1
        else:
            trend.iloc[i] = trend.iloc[i - 1]

    qqe_cizgisi = pd.Series(np.where(trend == 1, longband, shortband), index=rsi.index)
    return qqe_cizgisi, rsi_ma, trend


def qqe_mod_hesapla(veri, config=None):
    from csm_config import QQE_MOD
    cfg = config or QQE_MOD

    rsi_birincil = rsi_hesapla_yerel(veri, cfg["primary_rsi_length"])
    qqe1, rsi_ma1, trend1 = _qqe_cizgisi(
        rsi_birincil, cfg["primary_rsi_smoothing"], cfg["primary_qqe_factor"]
    )

    rsi_ikincil = rsi_hesapla_yerel(veri, cfg["secondary_rsi_length"])
    qqe2, rsi_ma2, trend2 = _qqe_cizgisi(
        rsi_ikincil, cfg["secondary_rsi_smoothing"], cfg["secondary_qqe_factor"]
    )

    histogram = rsi_ma1 - 50
    bb_orta = histogram.rolling(cfg["bollinger_length"]).mean()
    bb_std = histogram.rolling(cfg["bollinger_length"]).std()
    bb_ust = bb_orta + bb_std * cfg["bollinger_carpan"]
    bb_alt = bb_orta - bb_std * cfg["bollinger_carpan"]

    return {
        "histogram": histogram,
        "trend_birincil": trend1,
        "trend_ikincil": trend2,
        "bb_ust": bb_ust,
        "bb_alt": bb_alt,
    }


def rsi_hesapla_yerel(veri, periyot):
    """gostergeler.rsi_hesapla ile aynı formül — QQE'nin farklı periyotlarla
    birden çok kez çağırabilmesi için burada tekrar tanımlandı."""
    fark = veri["Close"].diff()
    kazanc = fark.where(fark > 0, 0)
    kayip = -fark.where(fark < 0, 0)
    ort_kazanc = kazanc.rolling(window=periyot).mean()
    ort_kayip = kayip.rolling(window=periyot).mean()
    rs = ort_kazanc / ort_kayip
    return 100 - (100 / (1 + rs))


# ---------------------------------------------------------------------------
# SSL Hybrid — Momentum motoru bileşeni
# Not: SSL2 bileşeni orijinal script'te JMA (Jurik Moving Average) kullanır.
# JMA kapalı/patentli bir formüldür, halka açık değildir. Burada SSL2 için
# EMA tabanlı bir yaklaşım kullanılmıştır — yönü/davranışı benzer olur ama
# TradingView'deki JMA sürümüyle birebir aynı sayısal sonucu vermez.
# ---------------------------------------------------------------------------
def ssl_hybrid_hesapla(veri, config=None):
    from csm_config import SSL_HYBRID
    from gostergeler import hma_hesapla, atr_hesapla
    cfg = config or SSL_HYBRID

    baseline = hma_hesapla(veri, cfg["baseline_length"])
    ssl2 = veri["Close"].ewm(span=cfg["ssl2_length"], adjust=False).mean()  # JMA yaklaşıklığı
    exit_line = hma_hesapla(veri, cfg["exit_length"])

    atr = atr_hesapla(veri, cfg["atr_period"])
    atr_wma = atr.rolling(cfg["atr_period"]).mean() * cfg["atr_multi"]
    kanal_genisligi = atr_wma * cfg["kanal_carpani"]
    ust_kanal = baseline + kanal_genisligi
    alt_kanal = baseline - kanal_genisligi

    yon = pd.Series(
        np.where(
            (veri["Close"] > baseline) & (ssl2 > baseline), 1,
            np.where((veri["Close"] < baseline) & (ssl2 < baseline), -1, 0)
        ),
        index=veri.index,
    )

    return {
        "baseline": baseline, "ssl2": ssl2, "exit_line": exit_line,
        "ust_kanal": ust_kanal, "alt_kanal": alt_kanal, "yon": yon,
    }


# ---------------------------------------------------------------------------
# Waddah Attar Explosion — Momentum motoru bileşeni
# ---------------------------------------------------------------------------
def waddah_attar_hesapla(veri, config=None):
    from csm_config import WADDAH_ATTAR
    cfg = config or WADDAH_ATTAR

    ema_hizli = veri["Close"].ewm(span=cfg["macd_hizli"], adjust=False).mean()
    ema_yavas = veri["Close"].ewm(span=cfg["macd_yavas"], adjust=False).mean()
    t1 = ema_hizli - ema_yavas
    trend_power = (t1 - t1.shift(1)) * cfg["sensitivity"]

    bb_orta = veri["Close"].rolling(cfg["bb_length"]).mean()
    bb_std = veri["Close"].rolling(cfg["bb_length"]).std()
    explosion_line = (bb_std * cfg["bb_carpan"] * 2)

    onceki_kapanis = veri["Close"].shift(1)
    tr = pd.concat([
        veri["High"] - veri["Low"],
        (veri["High"] - onceki_kapanis).abs(),
        (veri["Low"] - onceki_kapanis).abs(),
    ], axis=1).max(axis=1)
    dead_zone_line = tr.ewm(alpha=1 / cfg["dead_zone_atr_length"], adjust=False).mean() * cfg["dead_zone_carpani"]

    return {
        "trend_power": trend_power,
        "explosion_line": explosion_line,
        "dead_zone_line": dead_zone_line,
    }


# ---------------------------------------------------------------------------
# Squeeze Momentum — Breakout motoru bileşeni
# ---------------------------------------------------------------------------
def squeeze_momentum_hesapla(veri, config=None):
    from csm_config import SQUEEZE_MOMENTUM
    from gostergeler import bollinger_bantlari, keltner_kanali
    cfg = config or SQUEEZE_MOMENTUM

    bb_ust, bb_orta, bb_alt = bollinger_bantlari(veri, cfg["bb_length"], cfg["bb_carpan"])
    kc_ust, kc_orta, kc_alt = keltner_kanali(veri, cfg["kc_length"], cfg["kc_carpan"])

    sikisma_var = (bb_alt > kc_alt) & (bb_ust < kc_ust)
    sikisma_bitti = (bb_alt < kc_alt) & (bb_ust > kc_ust)

    orta_seviye = (
        veri["High"].rolling(cfg["momentum_length"]).max() +
        veri["Low"].rolling(cfg["momentum_length"]).min()
    ) / 2
    sma_kapanis = veri["Close"].rolling(cfg["momentum_length"]).mean()
    referans = (orta_seviye + sma_kapanis) / 2
    momentum = veri["Close"] - referans

    return {
        "sikisma_var": sikisma_var,
        "sikisma_bitti": sikisma_bitti,
        "momentum": momentum,
    }