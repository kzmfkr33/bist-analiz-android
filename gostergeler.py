import pandas as pd
import numpy as np


# ---------------------------------------------------------------------------
# TREND
# ---------------------------------------------------------------------------

def rsi_hesapla(veri, periyot=14):
    """
    RSI (Relative Strength Index) hesaplar.
    0-100 arası değer döner.
    Genel kural: 70 üstü 'aşırı alım', 30 altı 'aşırı satım' sayılır.
    """
    fark = veri['Close'].diff()
    kazanc = fark.where(fark > 0, 0)
    kayip = -fark.where(fark < 0, 0)

    ort_kazanc = kazanc.rolling(window=periyot).mean()
    ort_kayip = kayip.rolling(window=periyot).mean()

    rs = ort_kazanc / ort_kayip
    rsi = 100 - (100 / (1 + rs))
    return rsi


def hareketli_ortalama(veri, periyot=20):
    """
    Basit hareketli ortalama (SMA - Simple Moving Average).
    Fiyatın son N günlük ortalamasını verir, trend yönünü anlamaya yarar.
    """
    return veri['Close'].rolling(window=periyot).mean()


def ema_hesapla(veri, periyot=20):
    """
    Üstel hareketli ortalama (EMA - Exponential Moving Average).
    SMA'dan farklı olarak son fiyatlara daha fazla ağırlık verir,
    bu yüzden fiyat değişimine daha hızlı tepki verir.
    """
    return veri['Close'].ewm(span=periyot, adjust=False).mean()


def wma_hesapla(veri, periyot=20):
    """
    Ağırlıklı hareketli ortalama (WMA - Weighted Moving Average).
    En yakın güne en yüksek ağırlığı verir (doğrusal azalan ağırlık).
    """
    agirliklar = np.arange(1, periyot + 1)
    return veri['Close'].rolling(periyot).apply(
        lambda pencere: np.dot(pencere, agirliklar) / agirliklar.sum(), raw=True
    )


def hma_hesapla(veri, periyot=20):
    """
    Hull Hareketli Ortalaması (HMA). WMA'ya göre gecikmesi çok daha az,
    yönü daha erken yakalar. Kısa vadeli trend takibinde kullanılır.
    """
    yarim_periyot = int(periyot / 2)
    kok_periyot = int(np.sqrt(periyot))

    wma_yarim = veri['Close'].rolling(yarim_periyot).apply(
        lambda p: np.dot(p, np.arange(1, len(p) + 1)) / np.arange(1, len(p) + 1).sum(), raw=True
    )
    wma_tam = veri['Close'].rolling(periyot).apply(
        lambda p: np.dot(p, np.arange(1, len(p) + 1)) / np.arange(1, len(p) + 1).sum(), raw=True
    )
    fark_serisi = 2 * wma_yarim - wma_tam
    hma = fark_serisi.rolling(kok_periyot).apply(
        lambda p: np.dot(p, np.arange(1, len(p) + 1)) / np.arange(1, len(p) + 1).sum(), raw=True
    )
    return hma


def vwma_hesapla(veri, periyot=20):
    """
    Hacim Ağırlıklı Hareketli Ortalama (VWMA). Yüksek hacimli günlerin
    fiyata etkisini daha fazla yansıtır.
    """
    fiyat_hacim = veri['Close'] * veri['Volume']
    return fiyat_hacim.rolling(periyot).sum() / veri['Volume'].rolling(periyot).sum()


def adx_hesapla(veri, periyot=14):
    """
    ADX (Average Directional Index): trendin GÜCÜNÜ ölçer (yönünü değil).
    25 üstü 'güçlü trend', 20 altı 'trend yok / yatay piyasa' sayılır.
    Dönüş: adx, +DI, -DI (+DI > -DI ise yükseliş trendi baskın demektir).
    """
    yuksek, dusuk, kapanis = veri['High'], veri['Low'], veri['Close']

    ykk = yuksek - dusuk
    yok = (yuksek - kapanis.shift()).abs()
    dok = (dusuk - kapanis.shift()).abs()
    gercek_araligi = pd.concat([ykk, yok, dok], axis=1).max(axis=1)

    yon_yukari = yuksek.diff()
    yon_asagi = -dusuk.diff()
    pdm = np.where((yon_yukari > yon_asagi) & (yon_yukari > 0), yon_yukari, 0.0)
    ndm = np.where((yon_asagi > yon_yukari) & (yon_asagi > 0), yon_asagi, 0.0)

    atr = gercek_araligi.ewm(alpha=1 / periyot, adjust=False).mean()
    pdi = 100 * pd.Series(pdm, index=veri.index).ewm(alpha=1 / periyot, adjust=False).mean() / atr
    ndi = 100 * pd.Series(ndm, index=veri.index).ewm(alpha=1 / periyot, adjust=False).mean() / atr

    dx = 100 * (pdi - ndi).abs() / (pdi + ndi)
    adx = dx.ewm(alpha=1 / periyot, adjust=False).mean()
    return adx, pdi, ndi


def parabolic_sar_hesapla(veri, hizlanma=0.02, maks_hizlanma=0.2):
    """
    Parabolic SAR: fiyatın altında/üstünde noktalar halinde çizilir.
    Nokta fiyatın altındaysa yükseliş trendi, üstündeyse düşüş trendi
    kabul edilir. Trend dönüşlerini yakalamak için kullanılır.
    """
    yuksek, dusuk = veri['High'].values, veri['Low'].values
    n = len(veri)
    sar = np.zeros(n)
    yon_yukselis = True
    af = hizlanma
    ep = yuksek[0]
    sar[0] = dusuk[0]

    for i in range(1, n):
        sar[i] = sar[i - 1] + af * (ep - sar[i - 1])
        if yon_yukselis:
            if dusuk[i] < sar[i]:
                yon_yukselis = False
                sar[i] = ep
                ep = dusuk[i]
                af = hizlanma
            else:
                if yuksek[i] > ep:
                    ep = yuksek[i]
                    af = min(af + hizlanma, maks_hizlanma)
        else:
            if yuksek[i] > sar[i]:
                yon_yukselis = True
                sar[i] = ep
                ep = yuksek[i]
                af = hizlanma
            else:
                if dusuk[i] < ep:
                    ep = dusuk[i]
                    af = min(af + hizlanma, maks_hizlanma)

    return pd.Series(sar, index=veri.index)


def ichimoku_hesapla(veri, tenkan_p=9, kijun_p=26, senkou_b_p=52):
    """
    Ichimoku Bulutu: birden fazla ortalamayı birleştirip trend yönü,
    destek/direnç bulutu ve momentumu tek grafikte gösterir.
    Fiyat bulutun üstündeyse yükseliş, altındaysa düşüş eğilimi sayılır.
    """
    tenkan = (veri['High'].rolling(tenkan_p).max() + veri['Low'].rolling(tenkan_p).min()) / 2
    kijun = (veri['High'].rolling(kijun_p).max() + veri['Low'].rolling(kijun_p).min()) / 2
    senkou_a = ((tenkan + kijun) / 2).shift(kijun_p)
    senkou_b = ((veri['High'].rolling(senkou_b_p).max() + veri['Low'].rolling(senkou_b_p).min()) / 2).shift(kijun_p)
    chikou = veri['Close'].shift(-kijun_p)

    return {
        "tenkan_sen": tenkan, "kijun_sen": kijun,
        "senkou_a": senkou_a, "senkou_b": senkou_b, "chikou_span": chikou,
    }


def supertrend_hesapla(veri, periyot=10, carpan=3):
    """
    Supertrend: ATR tabanlı bir trend takip göstergesi.
    Fiyat çizginin üstündeyse yükseliş, altındaysa düşüş trendi.
    Dönüş: supertrend serisi, yön serisi (1=yükseliş, -1=düşüş).
    """
    atr = atr_hesapla(veri, periyot)
    orta_fiyat = (veri['High'] + veri['Low']) / 2

    ust_bant_temel = orta_fiyat + carpan * atr
    alt_bant_temel = orta_fiyat - carpan * atr

    ust_bant = ust_bant_temel.copy()
    alt_bant = alt_bant_temel.copy()
    yon = pd.Series(1, index=veri.index)
    st = pd.Series(0.0, index=veri.index)

    for i in range(1, len(veri)):
        if veri['Close'].iloc[i - 1] > ust_bant.iloc[i - 1]:
            ust_bant.iloc[i] = ust_bant_temel.iloc[i]
        else:
            ust_bant.iloc[i] = min(ust_bant_temel.iloc[i], ust_bant.iloc[i - 1])

        if veri['Close'].iloc[i - 1] < alt_bant.iloc[i - 1]:
            alt_bant.iloc[i] = alt_bant_temel.iloc[i]
        else:
            alt_bant.iloc[i] = max(alt_bant_temel.iloc[i], alt_bant.iloc[i - 1])

        if veri['Close'].iloc[i] <= ust_bant.iloc[i]:
            yon.iloc[i] = -1
        else:
            yon.iloc[i] = 1

    st = np.where(yon == 1, alt_bant, ust_bant)
    return pd.Series(st, index=veri.index), yon


# ---------------------------------------------------------------------------
# MOMENTUM
# ---------------------------------------------------------------------------

def macd_hesapla(veri, hizli=12, yavas=26, sinyal=9):
    """
    MACD (Moving Average Convergence Divergence) hesaplar.
    'macd' çizgisi 'sinyal' çizgisini yukarı keserse -> yükseliş sinyali
    'macd' çizgisi 'sinyal' çizgisini aşağı keserse -> düşüş sinyali
    """
    ema_hizli = veri['Close'].ewm(span=hizli, adjust=False).mean()
    ema_yavas = veri['Close'].ewm(span=yavas, adjust=False).mean()

    macd_cizgisi = ema_hizli - ema_yavas
    sinyal_cizgisi = macd_cizgisi.ewm(span=sinyal, adjust=False).mean()

    return macd_cizgisi, sinyal_cizgisi


def stochastic_hesapla(veri, periyot=14, yavaslatma=3):
    """
    Stochastic Osilatör: fiyatın son N günlük en yüksek-en düşük
    aralığına göre nerede olduğunu 0-100 arası gösterir.
    80 üstü 'aşırı alım', 20 altı 'aşırı satım' sayılır.
    %K: ham değer, %D: %K'nın hareketli ortalaması (daha yumuşak sinyal)
    """
    en_dusuk = veri['Low'].rolling(window=periyot).min()
    en_yuksek = veri['High'].rolling(window=periyot).max()

    k_cizgisi = 100 * (veri['Close'] - en_dusuk) / (en_yuksek - en_dusuk)
    d_cizgisi = k_cizgisi.rolling(window=yavaslatma).mean()

    return k_cizgisi, d_cizgisi


def cci_hesapla(veri, periyot=20):
    """
    CCI (Commodity Channel Index): fiyatın ortalamasından ne kadar
    saptığını ölçer. +100 üstü 'aşırı alım', -100 altı 'aşırı satım'
    sayılır, ayrıca yeni trendlerin başlangıcını erken yakalar.
    """
    tipik_fiyat = (veri['High'] + veri['Low'] + veri['Close']) / 3
    sma = tipik_fiyat.rolling(periyot).mean()
    ort_sapma = tipik_fiyat.rolling(periyot).apply(lambda x: np.abs(x - x.mean()).mean(), raw=True)
    return (tipik_fiyat - sma) / (0.015 * ort_sapma)


def williams_r_hesapla(veri, periyot=14):
    """
    Williams %R: Stochastic'in tersine çevrilmiş hali (-100 ile 0 arası).
    -20 üstü 'aşırı alım', -80 altı 'aşırı satım' sayılır.
    """
    en_yuksek = veri['High'].rolling(periyot).max()
    en_dusuk = veri['Low'].rolling(periyot).min()
    return -100 * (en_yuksek - veri['Close']) / (en_yuksek - en_dusuk)


def roc_hesapla(veri, periyot=12):
    """
    ROC (Rate of Change): fiyatın N gün öncesine göre yüzde değişimi.
    Pozitif ve büyüyen ROC, güçlenen momentumu gösterir.
    """
    return 100 * (veri['Close'] - veri['Close'].shift(periyot)) / veri['Close'].shift(periyot)


def momentum_hesapla(veri, periyot=10):
    """
    Momentum: fiyatın N gün öncesine göre mutlak (TL cinsi) farkı.
    ROC'un yüzdesiz halidir.
    """
    return veri['Close'] - veri['Close'].shift(periyot)


# ---------------------------------------------------------------------------
# VOLATİLİTE
# ---------------------------------------------------------------------------

def bollinger_bantlari(veri, periyot=20, sapma=2):
    """
    Bollinger Bantları: fiyatın 'normal' aralığını gösterir.
    Fiyat üst banda yaklaşırsa 'pahalı', alt banda yaklaşırsa 'ucuz' sayılabilir.
    """
    orta_bant = veri['Close'].rolling(window=periyot).mean()
    std_sapma = veri['Close'].rolling(window=periyot).std()

    ust_bant = orta_bant + (std_sapma * sapma)
    alt_bant = orta_bant - (std_sapma * sapma)

    return ust_bant, orta_bant, alt_bant


def atr_hesapla(veri, periyot=14):
    """
    ATR (Average True Range): hissenin ne kadar 'oynak' (volatil)
    olduğunu gösterir. Yüksek ATR = büyük fiyat hareketleri.
    Stop-loss mesafesini belirlemek için kullanılır
    (örn. stop-loss = güncel fiyat - 2*ATR gibi).
    """
    yuksek_dusuk = veri['High'] - veri['Low']
    yuksek_onceki_kapanis = (veri['High'] - veri['Close'].shift()).abs()
    dusuk_onceki_kapanis = (veri['Low'] - veri['Close'].shift()).abs()

    gercek_araligi = pd.concat(
        [yuksek_dusuk, yuksek_onceki_kapanis, dusuk_onceki_kapanis], axis=1
    ).max(axis=1)

    atr = gercek_araligi.rolling(window=periyot).mean()
    return atr


def keltner_kanali(veri, periyot=20, carpan=2):
    """
    Keltner Kanalı: Bollinger'a benzer ama standart sapma yerine ATR
    kullanır, bu yüzden ani hacim/volatilite patlamalarında daha
    'sakin' kalır. Bollinger ile birlikte 'squeeze' (sıkışma) tespiti
    için kullanılabilir.
    """
    orta_hat = veri['Close'].ewm(span=periyot, adjust=False).mean()
    atr = atr_hesapla(veri, periyot)
    ust_kanal = orta_hat + carpan * atr
    alt_kanal = orta_hat - carpan * atr
    return ust_kanal, orta_hat, alt_kanal


def standart_sapma_hesapla(veri, periyot=20):
    """
    Standart Sapma: fiyatın son N günde ortalamadan ne kadar saptığının
    ham istatistiksel ölçüsü. Yükselen std sapma = artan volatilite.
    """
    return veri['Close'].rolling(periyot).std()


# ---------------------------------------------------------------------------
# HACİM
# ---------------------------------------------------------------------------

def obv_hesapla(veri):
    """
    OBV (On-Balance Volume): fiyat ve hacmi birleştirerek trendin
    hacimle 'desteklenip desteklenmediğini' gösterir.
    Fiyat yükselirken OBV de yükseliyorsa trend güçlü sayılır.
    Fiyat yükselirken OBV düşüyorsa trend zayıf/şüpheli sayılır (uyumsuzluk).
    """
    yon = np.sign(veri['Close'].diff()).fillna(0)
    obv = (yon * veri['Volume']).cumsum()
    return obv


def relative_volume_hesapla(veri, periyot=20):
    """
    Relative Volume (RVOL): bugünkü hacmin, son N günlük ortalama hacme
    oranı. 1'in üstü normalden fazla, 3+ genelde 'olağandışı hacim'
    sayılır (Hacim Anomalisi modülünde kullanılacak).
    """
    ortalama_hacim = veri['Volume'].rolling(periyot).mean()
    return veri['Volume'] / ortalama_hacim


def mfi_hesapla(veri, periyot=14):
    """
    MFI (Money Flow Index): RSI'nin hacim ağırlıklı versiyonu, bazen
    'hacimli RSI' diye anılır. 80 üstü aşırı alım, 20 altı aşırı satım.
    """
    tipik_fiyat = (veri['High'] + veri['Low'] + veri['Close']) / 3
    para_akisi = tipik_fiyat * veri['Volume']

    yon = tipik_fiyat.diff()
    pozitif_akis = para_akisi.where(yon > 0, 0).rolling(periyot).sum()
    negatif_akis = para_akisi.where(yon < 0, 0).rolling(periyot).sum()

    para_orani = pozitif_akis / negatif_akis
    return 100 - (100 / (1 + para_orani))


def cmf_hesapla(veri, periyot=20):
    """
    CMF (Chaikin Money Flow): fiyatın gün içindeki kapanış konumunu
    hacimle ağırlıklandırarak alım/satım baskısını ölçer.
    Pozitif = alım baskısı, negatif = satım baskısı.
    """
    payda = (veri['High'] - veri['Low']).replace(0, np.nan)
    mfm = ((veri['Close'] - veri['Low']) - (veri['High'] - veri['Close'])) / payda
    mfv = mfm * veri['Volume']
    return mfv.rolling(periyot).sum() / veri['Volume'].rolling(periyot).sum()


def vwap_hesapla(veri):
    """
    VWAP (Volume Weighted Average Price): günün/periyodun hacim
    ağırlıklı ortalama fiyatı. Fiyat VWAP üstündeyse alıcılar,
    altındaysa satıcılar kontrolde sayılır. Kümülatif hesaplanır,
    bu yüzden gün içi (intraday) veride en anlamlısıdır.
    """
    tipik_fiyat = (veri['High'] + veri['Low'] + veri['Close']) / 3
    return (tipik_fiyat * veri['Volume']).cumsum() / veri['Volume'].cumsum()
