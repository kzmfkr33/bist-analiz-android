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