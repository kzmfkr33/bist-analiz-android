import json
import os

from log_ayarlari import logger_al

log = logger_al(__name__)

KRITER_DOSYASI = "kayitli_kriterler.json"

# Kriterlerde kullanılabilecek alanlar ve operatörler
KULLANILABILIR_ALANLAR = [
    "puan", "kapanis_fiyati", "degisim_yuzde_1g", "degisim_yuzde_1h",
    "RSI", "SMA20", "SMA50", "EMA20", "EMA50", "MACD", "MACD_Sinyal",
    "Stoch_K", "ATR_Yuzde", "OBV_Yonu", "ADX", "CCI", "Williams_R", "ROC",
    "RVOL", "MFI", "CMF", "Supertrend_Yon",
    "fk_orani", "pd_dd_orani", "roe", "temettu_verimi",
]
KULLANILABILIR_OPERATORLER = ["<", "<=", ">", ">=", "=="]


def _deger_getir(sonuc, alan):
    """Bir sonuç kaydından (üst seviye veya gostergeler içinden) değeri çeker."""
    if alan in sonuc:
        return sonuc[alan]
    return sonuc.get("gostergeler", {}).get(alan)


def kriter_uygula(sonuc, kriter):
    """
    Tek bir kriteri ({"alan": "RSI", "operator": "<", "deger": 30})
    bir hisse sonucuna uygular, True/False döner.
    """
    deger = _deger_getir(sonuc, kriter["alan"])
    if deger is None:
        return False

    op = kriter["operator"]
    hedef = kriter["deger"]

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


def kriterlere_gore_filtrele(sonuclar, kriterler):
    """
    Bir sonuç listesini, verilen TÜM kriterleri (VE mantığıyla) sağlayanlara indirger.
    kriterler boşsa hiçbir filtre uygulanmaz, tüm sonuçlar döner.
    """
    if not kriterler:
        return sonuclar

    filtrelenmis = []
    for sonuc in sonuclar:
        if all(kriter_uygula(sonuc, k) for k in kriterler):
            filtrelenmis.append(sonuc)
    return filtrelenmis


def sablon_kaydet(isim, kriterler):
    """Bir kriter setini isimle diske kaydeder."""
    tumu = _tum_sablonlari_oku()
    tumu[isim] = kriterler
    with open(KRITER_DOSYASI, "w", encoding="utf-8") as f:
        json.dump(tumu, f, ensure_ascii=False, indent=2)


def sablon_yukle(isim):
    """Kaydedilmiş bir kriter setini isimle geri getirir."""
    tumu = _tum_sablonlari_oku()
    return tumu.get(isim, [])


def sablonlari_listele():
    """Kaydedilmiş tüm şablon isimlerini döner."""
    return list(_tum_sablonlari_oku().keys())


def _tum_sablonlari_oku():
    if not os.path.exists(KRITER_DOSYASI):
        return {}
    try:
        with open(KRITER_DOSYASI, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError as hata:
        log.error(f"{KRITER_DOSYASI} bozuk görünüyor, boş şablon listesiyle devam ediliyor: {hata}")
        return {}
