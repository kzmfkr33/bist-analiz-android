"""
Patlama Potansiyeli Skoru — henüz kırılmamış ama kırılıma hazırlanan teknik
kurulumları tarar (Minervini/O'Neil "Volatility Contraction Pattern"
metodolojisine dayalı). Amaç: fiyat zaten patladıktan (tavan yaptıktan)
SONRA değil, ÖNCE tespit etmek.

ÖNEMLİ — DÜRÜSTLÜK NOTU: Bu skor bir OLASILIK göstergesidir, kesinlik
değil. Hiçbir teknik gösterge kombinasyonu bir hissenin yükseleceğini
garanti edemez — haberler, bilanço açıklamaları, büyük yatırımcı
hareketleri gibi teknik analizin göremediği faktörler her zaman devrede.
Bu ekran riski azaltmaya yardımcı olur, ortadan kaldırmaz. Stop-loss
kullanmadan işlem yapma.
"""
from concurrent.futures import ThreadPoolExecutor, as_completed

from gostergeler import bollinger_bantlari, keltner_kanali, ema_hesapla, rsi_hesapla, cmf_hesapla
from veri_katmani import fiyat_verisi_getir
from relative_guc import relative_strength_hesapla, bist100_getir
from bist_evreni import hisse_listesi
from log_ayarlari import logger_al

log = logger_al(__name__)


def _olcekle(deger, alt, ust):
    if deger is None or deger != deger:
        return None
    oran = (deger - alt) / (ust - alt)
    return max(0.0, min(100.0, oran * 100))


def _squeeze_serisi_hesapla(veri):
    bb_ust, bb_orta, bb_alt = bollinger_bantlari(veri, 20, 2)
    kc_ust, kc_orta, kc_alt = keltner_kanali(veri, 20, 1.5)
    return (bb_alt > kc_alt) & (bb_ust < kc_ust)


def patlama_potansiyeli_hesapla(veri, endeks_veri=None):
    """
    veri: en az ~65 günlük OHLCV DataFrame.
    endeks_veri: (opsiyonel) BIST 100 verisi — relative strength için.

    Dönüş: {"skor": 0-100 veya None, "bilesenler": [(isim, ham_deger, puan, agirlik), ...]}
    """
    if len(veri) < 65:
        return {"skor": None, "bilesenler": [("Yetersiz veri (en az 65 gün gerekli)", None, None, 1.0)]}

    bilesenler = []

    # 1) Volatilite sıkışması + süresi
    sikisma_serisi = _squeeze_serisi_hesapla(veri)
    son_sikisik = bool(sikisma_serisi.iloc[-1])
    sikisma_suresi = 0
    for deger in reversed(sikisma_serisi.tolist()):
        if deger:
            sikisma_suresi += 1
        else:
            break
    if son_sikisik:
        p = _olcekle(sikisma_suresi, 3, 20)
        bilesenler.append(("Volatilite Sıkışması", f"{sikisma_suresi} gündür sıkışık", p, 0.20))
    else:
        bilesenler.append(("Volatilite Sıkışması", "Şu an sıkışık değil", 15.0, 0.20))

    # 2) Baz sıkılığı (son 15 gün fiyat aralığı, ortalama fiyata oranla)
    son_15 = veri.iloc[-15:]
    baz_araligi_yuzde = float((son_15["High"].max() - son_15["Low"].min()) / son_15["Close"].mean() * 100)
    p = _olcekle(baz_araligi_yuzde, 25, 5)
    bilesenler.append(("Baz Sıkılığı (15 gün)", f"%{baz_araligi_yuzde:.1f}", p, 0.15))

    # 3) Dirence yakınlık (son 60 gün zirvesine göre)
    zirve_60 = float(veri["High"].iloc[-60:].max())
    guncel_fiyat = float(veri["Close"].iloc[-1])
    zirveye_uzaklik_yuzde = (zirve_60 - guncel_fiyat) / zirve_60 * 100
    if 0 <= zirveye_uzaklik_yuzde <= 8:
        p = 100 - (zirveye_uzaklik_yuzde / 8 * 30)
    elif zirveye_uzaklik_yuzde < 0:
        p = 45.0  # zaten zirveyi geçmiş (yeni zirve) — iyi ama bu ekranın asıl hedefi değil
    else:
        p = _olcekle(zirveye_uzaklik_yuzde, 25, 8)
    bilesenler.append(("Dirence Yakınlık", f"%{zirveye_uzaklik_yuzde:.1f} uzaklıkta", p, 0.15))

    # 4) Hacim imzası: kuruma sonrası hafif erken artış (aşırı patlama değil)
    hacim_son5 = float(veri["Volume"].iloc[-5:].mean())
    hacim_onceki15 = float(veri["Volume"].iloc[-20:-5].mean())
    if hacim_onceki15 > 0:
        hacim_orani = hacim_son5 / hacim_onceki15
        p = _olcekle(hacim_orani, 0.7, 2.0) if hacim_orani <= 2.5 else 35.0
        bilesenler.append(("Hacim İmzası (erken ilgi)", f"{hacim_orani:.2f}x", p, 0.15))

    # 5) Göreceli güç (BIST 100'e göre, 1 ay)
    if endeks_veri is not None:
        try:
            rs = relative_strength_hesapla(veri, endeks_veri)
            rs_1a = rs.get("1a")
            if rs_1a is not None:
                p = _olcekle(rs_1a, -5, 10)
                bilesenler.append(("Göreceli Güç (BIST 100'e göre, 1 ay)", f"%{rs_1a:+.1f}", p, 0.15))
        except Exception:
            pass

    # 6) Trend kalitesi (EMA20 > EMA50 — genel yükseliş yapısı)
    ema20 = ema_hesapla(veri, 20).iloc[-1]
    ema50 = ema_hesapla(veri, 50).iloc[-1]
    trend_iyi = bool(ema20 > ema50)
    bilesenler.append(("Trend Yapısı (EMA20 > EMA50)", "Olumlu" if trend_iyi else "Olumsuz",
                        75.0 if trend_iyi else 20.0, 0.10))

    # 7) Henüz aşırı alım değil (RSI < 65 — zaten patlamışsa bu düşer)
    rsi_son = rsi_hesapla(veri).iloc[-1]
    if rsi_son == rsi_son:
        if rsi_son >= 70:
            p = 10.0  # zaten aşırı alımda — bu ekranın aradığı şey değil
        else:
            p = _olcekle(rsi_son, 40, 65)
        bilesenler.append(("Aşırı Alım Değil (RSI)", f"{rsi_son:.1f}", p, 0.05))

    # 8) Gizli birikim (CMF pozitif mi — para girişi)
    cmf_son = cmf_hesapla(veri, 20).iloc[-1]
    if cmf_son == cmf_son:
        p = _olcekle(cmf_son, -0.15, 0.15)
        bilesenler.append(("Gizli Birikim (CMF)", f"{cmf_son:.3f}", p, 0.05))

    gecerli = [(p, a) for (_, _, p, a) in bilesenler if p is not None]
    toplam_agirlik = sum(a for _, a in gecerli)
    skor = sum(p * a for p, a in gecerli) / toplam_agirlik if toplam_agirlik else None

    return {"skor": round(skor, 1) if skor is not None else None, "bilesenler": bilesenler}


def _tek_hisse_hesapla(sembol, endeks_veri):
    try:
        veri = fiyat_verisi_getir(sembol, periyot="6mo")
        sonuc = patlama_potansiyeli_hesapla(veri, endeks_veri)
        if sonuc["skor"] is None:
            return None
        sonuc["sembol"] = sembol
        sonuc["son_fiyat"] = float(veri["Close"].iloc[-1])
        return sonuc
    except Exception as hata:
        log.warning(f"{sembol} patlama potansiyeli hesaplanamadı: {hata}")
        return None


def patlama_taramasi_yap(semboller=None, max_paralel_islem=6, ilerleme_callback=None):
    """
    Verilen (veya bist_evreni'ndeki tüm) hisseleri paralel olarak Patlama
    Potansiyeli skoruna göre tarar. Ağır bir işlemdir — yüzlerce hisse için
    birkaç dakika sürebilir.
    """
    if semboller is None:
        semboller = hisse_listesi()

    try:
        endeks_veri = bist100_getir(periyot="6mo")
    except Exception as hata:
        log.warning(f"BIST 100 verisi alınamadı, göreceli güç hesaplanamayacak: {hata}")
        endeks_veri = None

    sonuclar = []
    toplam = len(semboller)
    tamamlanan = 0

    with ThreadPoolExecutor(max_workers=max_paralel_islem) as havuz:
        gorev_haritasi = {
            havuz.submit(_tek_hisse_hesapla, s, endeks_veri): s for s in semboller
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


def en_yuksek_patlama_potansiyeli_10(sonuclar, adet=10):
    """Patlama Potansiyeli skoruna göre en yüksek N hisseyi döner (varsayılan 10)."""
    return sorted(sonuclar, key=lambda s: s["skor"], reverse=True)[:adet]
