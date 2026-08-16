"""
BIST Composite Signal Engine — parametre config'i.
Belgedeki referans TradingView parametreleri; ilk sürümde DEĞİŞTİRİLMEDEN
kullanılır. BIST backtest sonuçlarına göre buradan optimize edilebilir.
"""

UT_BOT = {
    "key_value": 1.0,      # Sensitivity
    "atr_period": 10,
}

ALPHA_TREND = {
    "period": 14,           # AP / Length
    "coefficient": 1.0,
}

EMA_TREND = {
    "kisa": 20,
    "orta": 50,
    "uzun": 200,
}

ADX_CONFIG = {
    "length": 14,
    "guclu_esik": 25,
}

RELATIVE_VOLUME = {
    "lookback": 20,
}

SUPERTREND_CONFIG = {
    "atr_period": 10,
    "carpan": 3.0,
}

QQE_MOD = {
    "primary_rsi_length": 6,
    "primary_rsi_smoothing": 5,
    "primary_qqe_factor": 3.0,
    "primary_threshold": 3.0,
    "secondary_rsi_length": 6,
    "secondary_rsi_smoothing": 5,
    "secondary_qqe_factor": 1.61,
    "secondary_threshold": 3.0,
    "bollinger_length": 50,
    "bollinger_carpan": 0.35,
}

SSL_HYBRID = {
    "atr_period": 14,
    "atr_multi": 1.0,
    "baseline_length": 60,   # HMA
    "ssl2_length": 5,        # JMA yerine EMA yaklaşımı kullanılacak (not: aşağıda açıklandı)
    "exit_length": 15,       # HMA
    "kanal_carpani": 0.2,
}

WADDAH_ATTAR = {
    "sensitivity": 150,
    "macd_hizli": 20,
    "macd_yavas": 40,
    "macd_sinyal": 9,
    "bb_length": 20,
    "bb_carpan": 2.0,
    "dead_zone_atr_length": 100,
    "dead_zone_carpani": 3.7,
}

SQUEEZE_MOMENTUM = {
    "bb_length": 20,
    "bb_carpan": 2.0,
    "kc_length": 20,
    "kc_carpan": 1.5,
    "momentum_length": 12,
}

# Composite Score ağırlıkları — belge Bölüm 4
COMPOSITE_AGIRLIKLAR = {
    "trend": 0.30,
    "momentum": 0.25,
    "market_regime": 0.20,
    "volume": 0.15,
    "breakout": 0.10,
}

# Sinyal sınıfları — belge Bölüm 5
SINYAL_SINIFLARI = [
    (85, 100, "ÇOK GÜÇLÜ POZİTİF"),
    (70, 84, "POZİTİF"),
    (55, 69, "İZLE"),
    (40, 54, "NÖTR"),
    (25, 39, "NEGATİF"),
    (0, 24, "ÇOK GÜÇLÜ NEGATİF"),
]