"""
Kod Yazmadan Strateji Oluşturucu — plan madde 21.
Koşul tabanlı bir arayüz için gereken kural motoru. Örnek:
  RSI < 30 AND EMA20 > EMA50 AND RVOL > 2  →  AL

Bir koşul iki şekilde yazılabilir:
  {"gosterge": "RSI", "operator": "<", "deger": 30}
      -> göstergeyi sabit bir sayıyla kıyaslar
  {"gosterge": "EMA20", "operator": ">", "referans_gosterge": "EMA50"}
      -> iki göstergeyi birbiriyle kıyaslar

"Hacim > Ortalama × 2" gibi bir koşul için RVOL (Relative Volume)
göstergesi zaten "hacim / ortalama hacim" oranı olduğundan
{"gosterge": "RVOL", "operator": ">", "deger": 2} yeterlidir.

Kullanılabilecek operatörler: <, <=, >, >=, ==
Bir koşul listesindeki tüm koşullar VE (AND) mantığıyla birleştirilir.
"""
import json
import os

from log_ayarlari import logger_al

log = logger_al(__name__)

STRATEJI_DOSYASI = "kayitli_stratejiler.json"

KULLANILABILIR_GOSTERGELER = [
    "RSI", "SMA20", "SMA50", "EMA20", "EMA50", "MACD", "MACD_Sinyal",
    "Stoch_K", "Stoch_D", "ADX", "PDI", "NDI", "CCI", "Williams_R", "ROC",
    "RVOL", "MFI", "CMF", "ATR", "Close", "BB_Ust", "BB_Alt", "Supertrend",
    "Supertrend_Yon", "VWMA20",
]
KULLANILABILIR_OPERATORLER = ["<", "<=", ">", ">=", "=="]


def _kiyasla(deger, op, hedef):
    if op == "<":
        return deger < hedef
    elif op == "<=":
        return deger <= hedef
    elif op == ">":
        return deger > hedef
    elif op == ">=":
        return deger >= hedef
    elif op == "==":
        return deger == hedef
    return False


def kosul_uygula(satir, kosul):
    """
    'satir': DataFrame'in tek bir satırı (bir günün gösterge değerleri).
    'kosul': yukarıdaki iki formattan biri.
    Değer eksikse (NaN/None) koşul sağlanmamış sayılır (backtest'in ilk
    günlerinde göstergeler henüz oluşmamış olabilir — bu normaldir).
    """
    deger = satir.get(kosul["gosterge"])
    if deger is None or deger != deger:
        return False

    if "referans_gosterge" in kosul:
        hedef = satir.get(kosul["referans_gosterge"])
        if hedef is None or hedef != hedef:
            return False
    else:
        hedef = kosul["deger"]

    return _kiyasla(deger, kosul["operator"], hedef)


def kosullari_uygula(satir, kosullar):
    """Bir koşul listesinin TÜMÜNÜN (AND) sağlanıp sağlanmadığını kontrol eder."""
    if not kosullar:
        return False
    return all(kosul_uygula(satir, k) for k in kosullar)


def strateji_kaydet(isim, al_kosullari, sat_kosullari=None, stop_yuzdesi=None, kar_al_yuzdesi=None):
    """Bir stratejiyi (AL koşulları + opsiyonel SAT koşulları/stop/kâr-al) diske kaydeder."""
    tumu = _tum_stratejileri_oku()
    tumu[isim] = {
        "al_kosullari": al_kosullari,
        "sat_kosullari": sat_kosullari or [],
        "stop_yuzdesi": stop_yuzdesi,
        "kar_al_yuzdesi": kar_al_yuzdesi,
    }
    with open(STRATEJI_DOSYASI, "w", encoding="utf-8") as f:
        json.dump(tumu, f, ensure_ascii=False, indent=2)


def strateji_yukle(isim):
    """Kaydedilmiş bir stratejiyi isimle geri getirir (yoksa None döner)."""
    return _tum_stratejileri_oku().get(isim)


def stratejileri_listele():
    """Kaydedilmiş tüm strateji isimlerinin listesi."""
    return list(_tum_stratejileri_oku().keys())


def _tum_stratejileri_oku():
    if not os.path.exists(STRATEJI_DOSYASI):
        return {}
    try:
        with open(STRATEJI_DOSYASI, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError as hata:
        log.error(f"{STRATEJI_DOSYASI} bozuk görünüyor, boş liste ile devam ediliyor: {hata}")
        return {}