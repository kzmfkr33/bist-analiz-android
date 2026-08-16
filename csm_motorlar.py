"""
BIST Composite Signal Engine — 5 ana motor (belge Bölüm 2, 4).
Her motor kendi 0-100 puanını ve puana katkı yapan gerekçelerini üretir
(belge Bölüm 7 — "Sinyalin Nedenleri"). Puanlar daha sonra csm_skor.py'de
ağırlıklı olarak Composite Score'a dönüştürülür.

Repainting yasağı: tüm motorlar SADECE son kapanmış mumu (veri.iloc[-1])
kullanır, gelecek veriye bakmaz.
"""
from gostergeler import rsi_hesapla, relative_volume_hesapla, adx_hesapla
from csm_gostergeler import (
    ut_bot_pro_hesapla, alpha_trend_hesapla, qqe_mod_hesapla,
    ssl_hybrid_hesapla, waddah_attar_hesapla, squeeze_momentum_hesapla,
)
from csm_market_regime import market_regime_hesapla
from csm_config import RELATIVE_VOLUME


def _olcekle(deger, alt, ust):
    if deger is None or deger != deger:
        return None
    oran = (deger - alt) / (ust - alt)
    return max(0.0, min(100.0, oran * 100))


# ---------------------------------------------------------------------------
# 1. Trend Engine — belge Bölüm 2.1 (UT Bot Pro) + 2.2 (AlphaTrend)
# ---------------------------------------------------------------------------
def trend_motoru_hesapla(veri):
    nedenler = []
    puan_bilesenleri = []

    _, ut_yon = ut_bot_pro_hesapla(veri)
    son_ut_yon = ut_yon.iloc[-1]
    if son_ut_yon == 1:
        nedenler.append("UT Bot Pro: yükseliş yönlü")
        puan_bilesenleri.append((70, 0.4))
    else:
        nedenler.append("UT Bot Pro: düşüş yönlü")
        puan_bilesenleri.append((30, 0.4))

    _, at_yon = alpha_trend_hesapla(veri)
    son_at_yon = at_yon.iloc[-1]
    if son_at_yon == 1:
        nedenler.append("AlphaTrend: yükseliş yönlü")
        puan_bilesenleri.append((70, 0.4))
    else:
        nedenler.append("AlphaTrend: düşüş yönlü")
        puan_bilesenleri.append((30, 0.4))

    adx, pdi, ndi = adx_hesapla(veri)
    son_adx, son_pdi, son_ndi = adx.iloc[-1], pdi.iloc[-1], ndi.iloc[-1]
    if son_adx == son_adx:
        if son_adx >= 25:
            yon_teyit = 70 if son_pdi > son_ndi else 30
            nedenler.append(
                f"ADX {son_adx:.1f} — güçlü trend teyidi "
                f"({'yükseliş' if son_pdi > son_ndi else 'düşüş'})"
            )
        else:
            yon_teyit = 50
            nedenler.append(f"ADX {son_adx:.1f} — trend zayıf, teyit yok")
        puan_bilesenleri.append((yon_teyit, 0.2))

    toplam_agirlik = sum(a for _, a in puan_bilesenleri)
    puan = sum(p * a for p, a in puan_bilesenleri) / toplam_agirlik if toplam_agirlik else 50

    return {"puan": round(puan, 1), "nedenler": nedenler}


# ---------------------------------------------------------------------------
# 2. Momentum Engine — belge Bölüm 2.4
# ---------------------------------------------------------------------------
def momentum_motoru_hesapla(veri):
    nedenler = []
    puan_bilesenleri = []

    qqe = qqe_mod_hesapla(veri)
    son_hist = qqe["histogram"].iloc[-1]
    son_bb_ust = qqe["bb_ust"].iloc[-1]
    son_bb_alt = qqe["bb_alt"].iloc[-1]
    if son_hist == son_hist:
        if son_hist > 0:
            nedenler.append("QQE MOD: pozitif momentum")
            puan_bilesenleri.append((65 if son_hist < son_bb_ust else 80, 0.30))
        else:
            nedenler.append("QQE MOD: negatif momentum")
            puan_bilesenleri.append((35 if son_hist > son_bb_alt else 20, 0.30))

    ssl = ssl_hybrid_hesapla(veri)
    son_ssl_yon = ssl["yon"].iloc[-1]
    if son_ssl_yon == 1:
        nedenler.append("SSL Hybrid: yükseliş yönlü trend yapısı")
        puan_bilesenleri.append((65, 0.25))
    elif son_ssl_yon == -1:
        nedenler.append("SSL Hybrid: düşüş yönlü trend yapısı")
        puan_bilesenleri.append((35, 0.25))
    else:
        nedenler.append("SSL Hybrid: nötr/karışık")
        puan_bilesenleri.append((50, 0.25))

    wae = waddah_attar_hesapla(veri)
    son_tp = wae["trend_power"].iloc[-1]
    son_dz = wae["dead_zone_line"].iloc[-1]
    if son_tp == son_tp and son_dz == son_dz:
        if abs(son_tp) > son_dz:
            yon_metni = "yükseliş" if son_tp > 0 else "düşüş"
            nedenler.append(f"Waddah Attar: dead zone üzerinde güçlü {yon_metni} enerjisi")
            puan_bilesenleri.append((75 if son_tp > 0 else 25, 0.25))
        else:
            nedenler.append("Waddah Attar: dead zone içinde, momentum zayıf")
            puan_bilesenleri.append((50, 0.25))

    rsi = rsi_hesapla(veri).iloc[-1]
    if rsi == rsi:
        if rsi > 50:
            nedenler.append(f"RSI {rsi:.1f} — 50 üzerinde")
        else:
            nedenler.append(f"RSI {rsi:.1f} — 50 altında")
        puan_bilesenleri.append((_olcekle(rsi, 30, 70), 0.20))

    gecerli = [(p, a) for p, a in puan_bilesenleri if p is not None]
    toplam_agirlik = sum(a for _, a in gecerli)
    puan = sum(p * a for p, a in gecerli) / toplam_agirlik if toplam_agirlik else 50

    return {"puan": round(puan, 1), "nedenler": nedenler}


# ---------------------------------------------------------------------------
# 3. Market Regime Engine — belge Bölüm 2.3 (rejimi doğrudan puana çevirir)
# ---------------------------------------------------------------------------
def market_regime_motoru_hesapla(veri):
    regime = market_regime_hesapla(veri)
    rejim = regime["rejim"]

    puan_haritasi = {
        "BULL TREND": 85,
        "BEAR TREND": 15,
        "SIDEWAYS": 50,
        "HIGH VOLATILITY": 50,
        "TRANSITION": 45,
    }
    puan = puan_haritasi.get(rejim, 50)

    nedenler = [f"Market Regime: {rejim}"]
    if regime.get("ema200") is not None:
        nedenler.append(f"EMA20 {regime['ema20']} / EMA50 {regime['ema50']} / EMA200 {regime['ema200']}")
    else:
        nedenler.append(f"EMA20 {regime['ema20']} / EMA50 {regime['ema50']} (EMA200 için yetersiz veri)")
    nedenler.append(f"SuperTrend: {'yükseliş' if regime['supertrend_yon'] == 1 else 'düşüş'} yönlü")
    if regime.get("atr_percentile") is not None:
        nedenler.append(f"Volatilite persentili: %{regime['atr_percentile']:.0f}")

    return {"puan": puan, "nedenler": nedenler, "rejim": rejim, "detay": regime}


# ---------------------------------------------------------------------------
# 4. Volume Analysis
# ---------------------------------------------------------------------------
def volume_motoru_hesapla(veri):
    rvol = relative_volume_hesapla(veri, RELATIVE_VOLUME["lookback"]).iloc[-1]
    nedenler = []

    if rvol != rvol:
        return {"puan": 50, "nedenler": ["Hacim verisi yetersiz"]}

    if rvol >= 2.5:
        nedenler.append(f"Relative Volume {rvol:.2f} — olağandışı yüksek hacim")
        puan = 85
    elif rvol >= 1.3:
        nedenler.append(f"Relative Volume {rvol:.2f} — ortalamanın üzerinde hacim")
        puan = 65
    elif rvol >= 0.7:
        nedenler.append(f"Relative Volume {rvol:.2f} — normal hacim")
        puan = 50
    else:
        nedenler.append(f"Relative Volume {rvol:.2f} — düşük hacim, teyit zayıf")
        puan = 35

    return {"puan": puan, "nedenler": nedenler}


# ---------------------------------------------------------------------------
# 5. Squeeze / Breakout Engine — belge Bölüm 2.5
# ---------------------------------------------------------------------------
def breakout_motoru_hesapla(veri):
    nedenler = []
    puan_bilesenleri = []

    sq = squeeze_momentum_hesapla(veri)
    sikisma_bitti_son = bool(sq["sikisma_bitti"].iloc[-1])
    sikisma_var_son = bool(sq["sikisma_var"].iloc[-1])
    momentum_son = sq["momentum"].iloc[-1]

    if sikisma_bitti_son and momentum_son == momentum_son:
        yon_metni = "yükseliş" if momentum_son > 0 else "düşüş"
        nedenler.append(f"Squeeze serbest kaldı — {yon_metni} yönlü kırılım")
        puan_bilesenleri.append((80 if momentum_son > 0 else 20, 0.5))
    elif sikisma_var_son:
        nedenler.append("Squeeze devam ediyor — kırılım henüz oluşmadı")
        puan_bilesenleri.append((50, 0.5))
    else:
        nedenler.append("Squeeze durumu nötr")
        puan_bilesenleri.append((50, 0.5))

    rvol = relative_volume_hesapla(veri, RELATIVE_VOLUME["lookback"]).iloc[-1]
    if rvol == rvol:
        rvol_puan = _olcekle(rvol, 0.5, 3)
        nedenler.append(f"Relative Volume {rvol:.2f}")
        puan_bilesenleri.append((rvol_puan, 0.3))

    adx, _, _ = adx_hesapla(veri)
    son_adx = adx.iloc[-1]
    if son_adx == son_adx:
        genisleme_puani = _olcekle(son_adx, 15, 35)
        nedenler.append(f"ADX {son_adx:.1f} — trend genişleme gücü")
        puan_bilesenleri.append((genisleme_puani, 0.2))

    gecerli = [(p, a) for p, a in puan_bilesenleri if p is not None]
    toplam_agirlik = sum(a for _, a in gecerli)
    puan = sum(p * a for p, a in gecerli) / toplam_agirlik if toplam_agirlik else 50

    return {"puan": round(puan, 1), "nedenler": nedenler}