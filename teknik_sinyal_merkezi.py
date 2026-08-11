"""
Teknik Sinyal Merkezi — plan madde 8.
EMA yapısı, MACD, RSI, ADX, Supertrend ve VWMA (VWAP yerine) göstergelerini
birleştirerek tek bir teknik görünüm üretir:
Güçlü Yükseliş / Yükseliş / Nötr / Düşüş / Güçlü Düşüş.
"""


def teknik_gorunum_uret(son):
    """
    'son': analiz_et(sembol) çıktısı olan DataFrame'in son satırı (veri.iloc[-1]).
    Dönüş: {"etiket": ..., "puan": ..., "bilesenler": [(isim, katki), ...]}
    """
    bilesenler = []
    puan = 0

    # EMA yapısı — en güçlü ağırlığa sahip (trendin omurgası)
    ema20, ema50, kapanis = son.get("EMA20"), son.get("EMA50"), son.get("Close")
    if ema20 is not None and ema50 is not None and kapanis is not None:
        if ema20 > ema50 and kapanis > ema20:
            bilesenler.append(("EMA yapısı: fiyat > EMA20 > EMA50 (güçlü yükseliş dizilimi)", 2))
            puan += 2
        elif ema20 > ema50:
            bilesenler.append(("EMA yapısı: EMA20 > EMA50 ama fiyat EMA20 altında (zayıflayan yükseliş)", 1))
            puan += 1
        elif ema20 < ema50 and kapanis < ema20:
            bilesenler.append(("EMA yapısı: fiyat < EMA20 < EMA50 (güçlü düşüş dizilimi)", -2))
            puan -= 2
        else:
            bilesenler.append(("EMA yapısı: EMA20 < EMA50 ama fiyat EMA20 üzerinde (zayıflayan düşüş)", -1))
            puan -= 1

    # MACD
    macd, macd_sinyal = son.get("MACD"), son.get("MACD_Sinyal")
    if macd is not None and macd_sinyal is not None:
        if macd > macd_sinyal:
            bilesenler.append(("MACD sinyal üzerinde", 1))
            puan += 1
        else:
            bilesenler.append(("MACD sinyal altında", -1))
            puan -= 1

    # RSI
    rsi = son.get("RSI")
    if rsi is not None:
        if 50 < rsi < 70:
            bilesenler.append((f"RSI {rsi:.1f} — sağlıklı yükseliş bölgesi", 1))
            puan += 1
        elif 30 < rsi <= 50:
            bilesenler.append((f"RSI {rsi:.1f} — sağlıklı düşüş bölgesi", -1))
            puan -= 1
        elif rsi >= 70:
            bilesenler.append((f"RSI {rsi:.1f} — aşırı alım (risk, katkı yok)", 0))
        elif rsi <= 30:
            bilesenler.append((f"RSI {rsi:.1f} — aşırı satım (risk, katkı yok)", 0))

    # ADX + yön (en güçlü ikinci ağırlık — trend gücünü teyit eder)
    adx, pdi, ndi = son.get("ADX"), son.get("PDI"), son.get("NDI")
    if adx is not None and pdi is not None and ndi is not None:
        if adx >= 25:
            if pdi > ndi:
                bilesenler.append((f"ADX {adx:.1f} — güçlü yükseliş trendi teyidi", 2))
                puan += 2
            else:
                bilesenler.append((f"ADX {adx:.1f} — güçlü düşüş trendi teyidi", -2))
                puan -= 2
        else:
            bilesenler.append((f"ADX {adx:.1f} — trend zayıf/yatay, teyit yok", 0))

    # Supertrend
    supertrend_yon = son.get("Supertrend_Yon")
    if supertrend_yon is not None:
        if supertrend_yon == 1:
            bilesenler.append(("Supertrend: yükseliş yönlü", 2))
            puan += 2
        else:
            bilesenler.append(("Supertrend: düşüş yönlü", -2))
            puan -= 2

    # VWMA20 (VWAP yerine) — fiyatın hacim ağırlıklı ortalamaya göre konumu
    vwma20 = son.get("VWMA20")
    if vwma20 is not None and kapanis is not None:
        if kapanis > vwma20:
            bilesenler.append(("Fiyat hacim ağırlıklı ortalamanın (VWMA20) üzerinde — alıcılar kontrolde", 1))
            puan += 1
        else:
            bilesenler.append(("Fiyat hacim ağırlıklı ortalamanın (VWMA20) altında — satıcılar kontrolde", -1))
            puan -= 1

    if puan >= 6:
        etiket = "Güçlü Yükseliş"
    elif puan >= 2:
        etiket = "Yükseliş"
    elif puan <= -6:
        etiket = "Güçlü Düşüş"
    elif puan <= -2:
        etiket = "Düşüş"
    else:
        etiket = "Nötr"

    return {"etiket": etiket, "puan": puan, "bilesenler": bilesenler}