def sinyal_uret(veri):
    """
    En son satırdaki gösterge değerlerine bakıp kural tabanlı bir
    değerlendirme metni üretir. Bu KESİN bir alım-satım tavsiyesi değildir,
    sadece göstergelerin ne söylediğinin özetidir.
    """
    son = veri.iloc[-1]
    bulgular = []
    puan = 0

    if son['RSI'] < 30:
        bulgular.append(f"RSI {son['RSI']:.1f} — aşırı satım bölgesinde (olası tepki alımı)")
        puan += 1
    elif son['RSI'] > 70:
        bulgular.append(f"RSI {son['RSI']:.1f} — aşırı alım bölgesinde (olası kâr satışı riski)")
        puan -= 1
    else:
        bulgular.append(f"RSI {son['RSI']:.1f} — nötr bölgede")

    if son['SMA20'] > son['SMA50']:
        bulgular.append("Kısa vadeli ortalama uzun vadeli ortalamanın üzerinde — yükseliş trendi")
        puan += 1
    else:
        bulgular.append("Kısa vadeli ortalama uzun vadeli ortalamanın altında — düşüş trendi")
        puan -= 1

    if son['MACD'] > son['MACD_Sinyal']:
        bulgular.append("MACD sinyal çizgisinin üzerinde — momentum olumlu")
        puan += 1
    else:
        bulgular.append("MACD sinyal çizgisinin altında — momentum olumsuz")
        puan -= 1

    if son['Close'] >= son['BB_Ust']:
        bulgular.append("Fiyat üst Bollinger bandına yakın/üzerinde — aşırı hareket olabilir")
    elif son['Close'] <= son['BB_Alt']:
        bulgular.append("Fiyat alt Bollinger bandına yakın/altında — aşırı hareket olabilir")

    if 'Stoch_K' in veri.columns:
        if son['Stoch_K'] < 20:
            bulgular.append(f"Stochastic {son['Stoch_K']:.1f} — aşırı satım bölgesinde")
            puan += 1
        elif son['Stoch_K'] > 80:
            bulgular.append(f"Stochastic {son['Stoch_K']:.1f} — aşırı alım bölgesinde")
            puan -= 1

    obv_yonu = 0
    if 'OBV' in veri.columns and len(veri) > 5:
        fiyat_yonu = son['Close'] - veri['Close'].iloc[-6]
        obv_yonu = son['OBV'] - veri['OBV'].iloc[-6]
        if fiyat_yonu > 0 and obv_yonu > 0:
            bulgular.append("Hacim, yükseliş trendini destekliyor (OBV yükselişte)")
            puan += 1
        elif fiyat_yonu > 0 and obv_yonu < 0:
            bulgular.append("Dikkat: fiyat yükseliyor ama hacim desteklemiyor (uyumsuzluk)")
            puan -= 1
        elif fiyat_yonu < 0 and obv_yonu < 0:
            bulgular.append("Hacim, düşüş trendini destekliyor (OBV düşüşte)")
            puan -= 1

    volatilite_yuzde = None
    if 'ATR' in veri.columns:
        volatilite_yuzde = (son['ATR'] / son['Close']) * 100
        bulgular.append(f"Günlük ortalama oynaklık (ATR): %{volatilite_yuzde:.1f}")

    if puan >= 3:
        genel = "Göstergeler ağırlıklı OLUMLU görünüyor"
    elif puan <= -3:
        genel = "Göstergeler ağırlıklı OLUMSUZ görünüyor"
    else:
        genel = "Göstergeler KARIŞIK/NÖTR — net bir yön yok"

    # Ham gösterge değerleri — tarama kriterlerinde filtrelemek için
    gostergeler = {
        "RSI": son.get('RSI'),
        "SMA20": son.get('SMA20'),
        "SMA50": son.get('SMA50'),
        "MACD": son.get('MACD'),
        "MACD_Sinyal": son.get('MACD_Sinyal'),
        "Stoch_K": son.get('Stoch_K'),
        "ATR_Yuzde": volatilite_yuzde,
        "OBV_Yonu": obv_yonu,
    }

    return {
        "genel_degerlendirme": genel,
        "puan": puan,
        "detaylar": bulgular,
        "kapanis_fiyati": son['Close'],
        "gostergeler": gostergeler,
    }