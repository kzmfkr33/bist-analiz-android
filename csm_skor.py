"""
Composite Score — belge Bölüm 3, 4, 5, 8.
5 motorun puanlarını ağırlıklı olarak birleştirir, Market Regime'e göre
ağırlıkları hafifçe ayarlar (Bölüm 6), nihai 0-100 Composite Score'u,
sinyal sınıfını, AL/İZLE/KAÇIN kararını ve güven seviyesini üretir.

Belge Bölüm 5: "Puan tek başına karar vermemeli." — yatay piyasada
(SIDEWAYS) yüksek puanlı sonuçlar bile İZLE'ye düşürülür.
"""
from csm_motorlar import (
    trend_motoru_hesapla, momentum_motoru_hesapla, market_regime_motoru_hesapla,
    volume_motoru_hesapla, breakout_motoru_hesapla,
)
from csm_market_regime import rejim_agirlik_carpani
from csm_config import COMPOSITE_AGIRLIKLAR, SINYAL_SINIFLARI


def _sinif_bul(puan):
    for alt, ust, isim in SINYAL_SINIFLARI:
        if alt <= puan <= ust:
            return isim
    return "NÖTR"


def _guven_seviyesi_hesapla(motor_puanlari, composite_puan):
    """
    5 motorun ne kadar hemfikir olduğuna (dağılım) ve nihai puanın 50'den
    ne kadar uzak (kararlı) olduğuna bakarak güven seviyesi belirler.
    Düşük dağılım + net (50'den uzak) puan = yüksek güven.
    """
    puanlar = list(motor_puanlari.values())
    ortalama = sum(puanlar) / len(puanlar)
    varyans = sum((p - ortalama) ** 2 for p in puanlar) / len(puanlar)
    std_sapma = varyans ** 0.5

    uzaklik = abs(composite_puan - 50)

    if std_sapma <= 12 and uzaklik >= 25:
        return "ÇOK GÜÇLÜ"
    elif std_sapma <= 18 and uzaklik >= 15:
        return "GÜÇLÜ"
    elif std_sapma <= 25:
        return "ORTA"
    else:
        return "ZAYIF"


def composite_skor_hesapla(veri):
    """
    veri: OHLCV DataFrame (EMA200/Market Regime'in anlamlı olması için
    en az ~200+ satır önerilir — periyot="1y" veya "2y" ile çek).

    Dönüş: {
        "composite_score": 0-100,
        "sinyal_sinifi": "ÇOK GÜÇLÜ POZİTİF".."ÇOK GÜÇLÜ NEGATİF",
        "sinyal": "AL"/"İZLE"/"KAÇIN",
        "guven_seviyesi": "ÇOK GÜÇLÜ"/"GÜÇLÜ"/"ORTA"/"ZAYIF",
        "market_regime": str, "aciklama_notu": str veya None,
        "motor_puanlari": {...}, "agirliklar": {...}, "nedenler": {...},
    }
    """
    trend = trend_motoru_hesapla(veri)
    momentum = momentum_motoru_hesapla(veri)
    regime = market_regime_motoru_hesapla(veri)
    volume = volume_motoru_hesapla(veri)
    breakout = breakout_motoru_hesapla(veri)

    carpanlar = rejim_agirlik_carpani(regime["rejim"])

    agirliklar = {
        "trend": COMPOSITE_AGIRLIKLAR["trend"] * carpanlar["trend"],
        "momentum": COMPOSITE_AGIRLIKLAR["momentum"],
        "market_regime": COMPOSITE_AGIRLIKLAR["market_regime"],
        "volume": COMPOSITE_AGIRLIKLAR["volume"],
        "breakout": COMPOSITE_AGIRLIKLAR["breakout"] * carpanlar["breakout"],
    }
    toplam_agirlik = sum(agirliklar.values())
    agirliklar = {k: v / toplam_agirlik for k, v in agirliklar.items()}  # toplam=1 olacak şekilde normalize

    motor_puanlari = {
        "trend": trend["puan"],
        "momentum": momentum["puan"],
        "market_regime": regime["puan"],
        "volume": volume["puan"],
        "breakout": breakout["puan"],
    }

    composite_score = sum(motor_puanlari[k] * agirliklar[k] for k in motor_puanlari)
    composite_score = round(composite_score, 1)

    sinyal_sinifi = _sinif_bul(composite_score)

    if composite_score >= 70:
        sinyal = "AL"
    elif composite_score <= 39:
        sinyal = "KAÇIN"
    else:
        sinyal = "İZLE"

    aciklama_notu = None
    if regime["rejim"] == "SIDEWAYS" and sinyal == "AL":
        sinyal = "İZLE"
        aciklama_notu = "Piyasa yatay (SIDEWAYS) olduğu için sinyal AL'dan İZLE'ye düşürüldü."

    guven_seviyesi = _guven_seviyesi_hesapla(motor_puanlari, composite_score)

    tum_nedenler = {
        "Trend Engine (UT Bot Pro + AlphaTrend)": trend["nedenler"],
        "Momentum Engine (QQE MOD + SSL Hybrid + Waddah Attar)": momentum["nedenler"],
        "Market Regime (SuperTrend + EMA)": regime["nedenler"],
        "Volume Analysis": volume["nedenler"],
        "Squeeze / Breakout Engine": breakout["nedenler"],
    }

    return {
        "composite_score": composite_score,
        "sinyal_sinifi": sinyal_sinifi,
        "sinyal": sinyal,
        "guven_seviyesi": guven_seviyesi,
        "market_regime": regime["rejim"],
        "aciklama_notu": aciklama_notu,
        "motor_puanlari": motor_puanlari,
        "agirliklar": {k: round(v, 3) for k, v in agirliklar.items()},
        "nedenler": tum_nedenler,
    }
# ---------------------------------------------------------------------------
# Otomatik Tarama — tüm BIST evrenini Composite Signal Engine ile puanlar
# ---------------------------------------------------------------------------
from concurrent.futures import ThreadPoolExecutor, as_completed
from veri_katmani import fiyat_verisi_getir
from bist_evreni import hisse_listesi
from log_ayarlari import logger_al

log = logger_al(__name__)


def _tek_hisse_composite_hesapla(sembol, periyot="1y"):
    try:
        veri = fiyat_verisi_getir(sembol, periyot=periyot)
        sonuc = composite_skor_hesapla(veri)
        sonuc["sembol"] = sembol
        return sonuc
    except Exception as hata:
        log.warning(f"{sembol} composite skor hesaplanamadı: {hata}")
        return None


def composite_taramasi_yap(semboller=None, periyot="1y", max_paralel_islem=6, ilerleme_callback=None):
    """
    Verilen (veya bist_evreni'ndeki tüm) hisseleri paralel olarak Composite
    Signal Engine ile puanlar. Ağır bir işlemdir (her hisse için 1 yıllık
    veri + 5 motor hesaplanır) — yüzlerce hisse için birkaç dakika sürebilir.
    """
    if semboller is None:
        semboller = hisse_listesi()

    sonuclar = []
    toplam = len(semboller)
    tamamlanan = 0

    with ThreadPoolExecutor(max_workers=max_paralel_islem) as havuz:
        gorev_haritasi = {
            havuz.submit(_tek_hisse_composite_hesapla, s, periyot): s for s in semboller
        }
        for gorev in as_completed(gorev_haritasi):
            sembol = gorev_haritasi[gorev]
            tamamlanan += 1
            sonuc = gorev.result()
            if sonuc is not None:
                sonuclar.append(sonuc)
            if ilerleme_callback:
                ilerleme_callback(tamamlanan, toplam, sembol)

    return sonuclar


def en_yuksek_composite_20(sonuclar, adet=10):
    """Composite Score'a göre en yüksek puanlı N hisseyi döner (varsayılan 10)."""
    return sorted(sonuclar, key=lambda s: s["composite_score"], reverse=True)[:adet]