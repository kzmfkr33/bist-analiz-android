"""
Hisse Skoru Motoru — plan madde 5.

Her hisseye 0-100 arasında bir GENEL skor verir. Bu skor altı alt
skordan oluşur: Trend, Momentum, Teknik, Hacim, Temel, Değerleme.

Şeffaflık ilkesi: her alt skorun hangi bileşenlerden, hangi ham
değerlerden ve ne kadar katkıyla oluştuğu 'bilesenler' listesinde
açıkça tutulur — arayüzde kullanıcıya "neden bu puan" sorusunun
cevabı olarak gösterilebilir.

Girdi olarak test.py -> analiz_et(sembol) çıktısı olan 'veri' DataFrame'i
(son satırı kullanılır) ve opsiyonel olarak veri_katmani.temel_veri_getir()
çıktısı beklenir. Temel veri verilmezse Temel ve Değerleme alt skorları
None döner (genel skor, mevcut alt skorların ağırlıklı ortalaması alınarak
hesaplanır — eksik veri genel skoru sıfırlamaz, sadece o kısmı devre dışı bırakır).
"""

import numpy as np

# Genel skor hesaplanırken her alt skorun ağırlığı (toplamı 1.0)
AGIRLIKLAR = {
    "trend": 0.20,
    "momentum": 0.20,
    "teknik": 0.15,
    "hacim": 0.15,
    "temel": 0.15,
    "degerleme": 0.15,
}


def _sayi_mi(deger):
    return deger is not None and not (isinstance(deger, float) and np.isnan(deger))


def _olcekle(deger, alt_sinir, ust_sinir):
    """
    Bir ham değeri [alt_sinir, ust_sinir] aralığından 0-100 aralığına
    doğrusal olarak taşır; aralık dışını 0 veya 100'e kırpar.
    alt_sinir > ust_sinir verilirse (örn. F/K gibi 'düşük=iyi' metrikler
    için) ölçek otomatik ters çevrilir.
    """
    if not _sayi_mi(deger):
        return None
    if ust_sinir == alt_sinir:
        return 50.0
    oran = (deger - alt_sinir) / (ust_sinir - alt_sinir)
    return float(np.clip(oran, 0, 1) * 100)


def _agirlikli_ortalama(bilesenler):
    """
    bilesenler: [(isim, ham_deger, puan_0_100, agirlik), ...]
    Sadece puanı None olmayan bileşenleri kullanarak ağırlıklı ortalama alır.
    Hiçbiri yoksa None döner.
    """
    gecerli = [(p, a) for (_, _, p, a) in bilesenler if p is not None]
    if not gecerli:
        return None
    toplam_agirlik = sum(a for _, a in gecerli)
    if toplam_agirlik == 0:
        return None
    return sum(p * a for p, a in gecerli) / toplam_agirlik


# ---------------------------------------------------------------------------
# ALT SKORLAR
# ---------------------------------------------------------------------------

def trend_skoru_hesapla(son):
    """
    Trend alt skoru: EMA yapısı + fiyatın EMA50'ye göre konumu + ADX gücü/yönü.
    'son': veri DataFrame'inin son satırı (veri.iloc[-1]).
    """
    bilesenler = []

    # EMA20 / EMA50 ilişkisi — kısa vade uzun vadenin üstündeyse yükseliş trendi
    ema20, ema50 = son.get("EMA20"), son.get("EMA50")
    if _sayi_mi(ema20) and _sayi_mi(ema50) and ema50 != 0:
        ema_farki_yuzde = 100 * (ema20 - ema50) / ema50
        p = _olcekle(ema_farki_yuzde, -5, 5)  # +-%5 aralığında 0-100'e yay
        bilesenler.append(("EMA20 vs EMA50 (%)", round(ema_farki_yuzde, 2), p, 0.35))

    # Fiyatın EMA50'ye göre konumu
    kapanis, ema50_ = son.get("Close"), son.get("EMA50")
    if _sayi_mi(kapanis) and _sayi_mi(ema50_) and ema50_ != 0:
        fiyat_farki_yuzde = 100 * (kapanis - ema50_) / ema50_
        p = _olcekle(fiyat_farki_yuzde, -8, 8)
        bilesenler.append(("Fiyat vs EMA50 (%)", round(fiyat_farki_yuzde, 2), p, 0.25))

    # ADX gücü + yönü (PDI > NDI ise yükseliş yönlü güç, aksi halde düşüş yönlü)
    adx, pdi, ndi = son.get("ADX"), son.get("PDI"), son.get("NDI")
    if _sayi_mi(adx) and _sayi_mi(pdi) and _sayi_mi(ndi):
        guc = _olcekle(adx, 10, 40)  # ADX 10-40 arası "zayıf -> çok güçlü" kabul edilir
        if pdi < ndi:
            guc = 100 - guc if guc is not None else None  # yön düşüşse skoru tersine çevir
        bilesenler.append((f"ADX gücü ({'yükseliş' if pdi > ndi else 'düşüş'} yönlü)", round(adx, 1), guc, 0.40))

    return {"puan": _agirlikli_ortalama(bilesenler), "bilesenler": bilesenler}


def momentum_skoru_hesapla(veri):
    """
    Momentum alt skoru: RSI konumu + ROC + MACD histogramı + mevcut olan
    çoklu periyot getiriler (1g, 1h, 1a, veri yeterliyse 3a/6a).
    'veri': tam DataFrame (çoklu periyot getirisi için geçmişe bakılıyor).
    """
    son = veri.iloc[-1]
    bilesenler = []

    rsi = son.get("RSI")
    if _sayi_mi(rsi):
        p = _olcekle(rsi, 30, 70)  # RSI 30-70 aralığı "zayıf -> güçlü momentum" kabul edilir
        bilesenler.append(("RSI", round(rsi, 1), p, 0.25))

    roc = son.get("ROC")
    if _sayi_mi(roc):
        p = _olcekle(roc, -10, 10)
        bilesenler.append(("ROC (12 gün, %)", round(roc, 2), p, 0.20))

    macd, macd_sinyal = son.get("MACD"), son.get("MACD_Sinyal")
    kapanis = son.get("Close")
    if _sayi_mi(macd) and _sayi_mi(macd_sinyal) and _sayi_mi(kapanis) and kapanis != 0:
        histogram_yuzde = 100 * (macd - macd_sinyal) / kapanis
        p = _olcekle(histogram_yuzde, -1, 1)
        bilesenler.append(("MACD histogramı (%)", round(histogram_yuzde, 3), p, 0.20))

    # Çoklu periyot getiriler: veride kaç gün varsa o kadarını kullan (esnek)
    kapanislar = veri["Close"]
    periyotlar = [("1 gün", 1, 0.05), ("1 hafta", 5, 0.10), ("1 ay", 21, 0.10),
                  ("3 ay", 63, 0.05), ("6 ay", 126, 0.05)]
    for isim, gun, agirlik in periyotlar:
        if len(kapanislar) > gun:
            getiri_yuzde = 100 * (kapanislar.iloc[-1] - kapanislar.iloc[-1 - gun]) / kapanislar.iloc[-1 - gun]
            p = _olcekle(getiri_yuzde, -15, 15)
            bilesenler.append((f"Getiri ({isim}, %)", round(getiri_yuzde, 2), p, agirlik))

    return {"puan": _agirlikli_ortalama(bilesenler), "bilesenler": bilesenler}


def teknik_skoru_hesapla(son):
    """
    Teknik alt skoru: osilatörlerin 'sağlıklı' bölgede olup olmadığına bakar
    (aşırı uçlar yerine dengeli-güçlü konumu ödüllendirir).
    Stochastic, CCI, Williams %R, Supertrend yönü ve VWAP'a göre fiyat konumunu kullanır.
    """
    bilesenler = []

    stoch_k = son.get("Stoch_K")
    if _sayi_mi(stoch_k):
        p = _olcekle(stoch_k, 20, 80)
        bilesenler.append(("Stochastic %K", round(stoch_k, 1), p, 0.25))

    cci = son.get("CCI")
    if _sayi_mi(cci):
        p = _olcekle(cci, -100, 100)
        bilesenler.append(("CCI", round(cci, 1), p, 0.20))

    williams = son.get("Williams_R")
    if _sayi_mi(williams):
        p = _olcekle(williams, -80, -20)
        bilesenler.append(("Williams %R", round(williams, 1), p, 0.20))

    supertrend_yon = son.get("Supertrend_Yon")
    if _sayi_mi(supertrend_yon):
        p = 100.0 if supertrend_yon == 1 else 0.0
        bilesenler.append(("Supertrend yönü", "Yükseliş" if supertrend_yon == 1 else "Düşüş", p, 0.35))

    return {"puan": _agirlikli_ortalama(bilesenler), "bilesenler": bilesenler}


def hacim_skoru_hesapla(son):
    """
    Hacim alt skoru: Relative Volume, MFI (hacimli RSI), CMF (para akışı)
    ve OBV yönünü birleştirir.
    """
    bilesenler = []

    rvol = son.get("RVOL")
    if _sayi_mi(rvol):
        p = _olcekle(rvol, 0.5, 3)
        bilesenler.append(("Relative Volume", round(rvol, 2), p, 0.30))

    mfi = son.get("MFI")
    if _sayi_mi(mfi):
        p = _olcekle(mfi, 20, 80)
        bilesenler.append(("MFI", round(mfi, 1), p, 0.30))

    cmf = son.get("CMF")
    if _sayi_mi(cmf):
        p = _olcekle(cmf, -0.2, 0.2)
        bilesenler.append(("CMF", round(cmf, 3), p, 0.40))

    return {"puan": _agirlikli_ortalama(bilesenler), "bilesenler": bilesenler}


def temel_skoru_hesapla(temel_veri):
    """
    Temel alt skoru: ROE, net kâr marjı, borç/özsermaye, gelir büyümesi,
    temettü verimi. temel_veri, veri_katmani.temel_veri_getir()'in çıktısıdır.
    """
    if not temel_veri:
        return {"puan": None, "bilesenler": []}

    bilesenler = []

    roe = temel_veri.get("roe")
    if _sayi_mi(roe):
        p = _olcekle(roe * 100, 0, 30)  # yfinance oranı ondalık (0.15 = %15) döner
        bilesenler.append(("ROE (%)", round(roe * 100, 1), p, 0.30))

    net_kar_marji = temel_veri.get("net_kar_marji")
    if _sayi_mi(net_kar_marji):
        p = _olcekle(net_kar_marji * 100, 0, 25)
        bilesenler.append(("Net kâr marjı (%)", round(net_kar_marji * 100, 1), p, 0.25))

    gelir_buyume = temel_veri.get("gelir_buyume")
    if _sayi_mi(gelir_buyume):
        p = _olcekle(gelir_buyume * 100, -10, 30)
        bilesenler.append(("Gelir büyümesi (%)", round(gelir_buyume * 100, 1), p, 0.25))

    borc_ozsermaye = temel_veri.get("borc_ozsermaye")
    if _sayi_mi(borc_ozsermaye):
        p = _olcekle(borc_ozsermaye, 150, 0)  # düşük borç iyi, ölçek tersine çevrilmiş
        bilesenler.append(("Borç/Özsermaye", round(borc_ozsermaye, 1), p, 0.20))

    return {"puan": _agirlikli_ortalama(bilesenler), "bilesenler": bilesenler}


def degerleme_skoru_hesapla(temel_veri):
    """
    Değerleme alt skoru: F/K, PD/DD, FD/FAVÖK — düşük çarpanlar daha
    yüksek puan alır (plan madde 17'deki sektör karşılaştırması,
    Adım 7'de sektor_analizi.py ile bu skora eklenecek).
    """
    if not temel_veri:
        return {"puan": None, "bilesenler": []}

    bilesenler = []

    fk = temel_veri.get("fk_orani")
    if _sayi_mi(fk) and fk > 0:
        p = _olcekle(fk, 30, 5)  # düşük F/K iyi, ölçek tersine çevrilmiş
        bilesenler.append(("F/K oranı", round(fk, 1), p, 0.40))

    pd_dd = temel_veri.get("pd_dd_orani")
    if _sayi_mi(pd_dd) and pd_dd > 0:
        p = _olcekle(pd_dd, 5, 0.5)
        bilesenler.append(("PD/DD oranı", round(pd_dd, 2), p, 0.30))

    fd_favok = temel_veri.get("fd_favok")
    if _sayi_mi(fd_favok) and fd_favok > 0:
        p = _olcekle(fd_favok, 15, 3)
        bilesenler.append(("FD/FAVÖK", round(fd_favok, 1), p, 0.30))

    return {"puan": _agirlikli_ortalama(bilesenler), "bilesenler": bilesenler}


# ---------------------------------------------------------------------------
# GENEL SKOR
# ---------------------------------------------------------------------------

def hisse_skoru_hesapla(veri, temel_veri=None):
    """
    Bir hissenin tam skor kartını üretir: 6 alt skor + genel (0-100) skor.

    veri: test.py -> analiz_et(sembol) çıktısı (tüm göstergeleri içeren DataFrame)
    temel_veri: veri_katmani.temel_veri_getir(sembol) çıktısı (opsiyonel;
        verilmezse Temel ve Değerleme skorları None döner ve genel skor
        kalan alt skorların ağırlıklı ortalamasından hesaplanır)

    Dönüş: {
        "genel": 87.3,
        "trend": {"puan": 92.1, "bilesenler": [...]},
        "momentum": {...}, "teknik": {...}, "hacim": {...},
        "temel": {...}, "degerleme": {...},
    }
    """
    son = veri.iloc[-1]

    alt_skorlar = {
        "trend": trend_skoru_hesapla(son),
        "momentum": momentum_skoru_hesapla(veri),
        "teknik": teknik_skoru_hesapla(son),
        "hacim": hacim_skoru_hesapla(son),
        "temel": temel_skoru_hesapla(temel_veri),
        "degerleme": degerleme_skoru_hesapla(temel_veri),
    }

    genel_bilesenler = [
        (isim, None, alt_skorlar[isim]["puan"], AGIRLIKLAR[isim])
        for isim in alt_skorlar
    ]
    genel = _agirlikli_ortalama(genel_bilesenler)

    return {
        "genel": round(genel, 1) if genel is not None else None,
        **{isim: {
            "puan": round(alt_skorlar[isim]["puan"], 1) if alt_skorlar[isim]["puan"] is not None else None,
            "bilesenler": alt_skorlar[isim]["bilesenler"],
        } for isim in alt_skorlar},
    }


if __name__ == "__main__":
    from test import analiz_et
    from veri_katmani import temel_veri_getir

    sembol = "THYAO.IS"
    veri = analiz_et(sembol)
    temel = temel_veri_getir(sembol)

    skor = hisse_skoru_hesapla(veri, temel)

    print(f"\n=== {sembol} HİSSE SKORU ===")
    print(f"GENEL: {skor['genel']} / 100\n")
    for alan in ["trend", "momentum", "teknik", "hacim", "temel", "degerleme"]:
        print(f"{alan.upper()}: {skor[alan]['puan']}")
        for isim, ham, puan, agirlik in skor[alan]["bilesenler"]:
            puan_metni = f"{puan:.1f}" if puan is not None else "yok"
            print(f"    - {isim}: {ham}  ->  {puan_metni} puan (ağırlık {agirlik})")