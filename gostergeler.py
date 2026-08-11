import pandas as pd
import numpy as np


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


def atr_hesapla(veri, periyot=14):
    """
    ATR (Average True Range): hissenin ne kadar 'oynak' (volatil)
    olduğunu gösterir. Yüksek ATR = büyük fiyat hareketleri.
    İleride stop-loss mesafesini belirlemek için kullanacağız
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