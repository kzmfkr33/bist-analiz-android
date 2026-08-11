import time
from concurrent.futures import ThreadPoolExecutor, as_completed

from test import analiz_et
from sinyal_motoru import sinyal_uret
from tarama_kriterleri import kriterlere_gore_filtrele
from veri_katmani import temel_veri_getir
from bist_evreni import hisse_listesi, sektor_getir
from log_ayarlari import logger_al

log = logger_al(__name__)


def _tek_hisseyi_analiz_et(sembol, temel_dahil_et=True):
    """
    Tek bir hisseyi analiz eder: teknik göstergeler + fiyat değişimleri +
    (istenirse) temel veriler. Hata durumunda None döner (paralel
    tarama sırasında bir hissenin başarısız olması diğerlerini etkilemesin diye).
    """
    try:
        veri = analiz_et(sembol)
        degerlendirme = sinyal_uret(veri)
        degerlendirme["sembol"] = sembol
        degerlendirme["sektor"] = sektor_getir(sembol)

        kapanis = veri['Close']
        degerlendirme["degisim_yuzde_1g"] = (
            100 * (kapanis.iloc[-1] - kapanis.iloc[-2]) / kapanis.iloc[-2]
            if len(kapanis) > 1 else None
        )
        degerlendirme["degisim_yuzde_1h"] = (
            100 * (kapanis.iloc[-1] - kapanis.iloc[-6]) / kapanis.iloc[-6]
            if len(kapanis) > 6 else None
        )
        degerlendirme["gunluk_hacim"] = veri['Volume'].iloc[-1]
        degerlendirme["ortalama_hacim_20g"] = veri['Volume'].rolling(20).mean().iloc[-1]

        if temel_dahil_et:
            temel = temel_veri_getir(sembol)
            degerlendirme["sirket_adi"] = temel.get("sirket_adi")
            degerlendirme["fk_orani"] = temel.get("fk_orani")
            degerlendirme["pd_dd_orani"] = temel.get("pd_dd_orani")
            degerlendirme["roe"] = temel.get("roe")
            degerlendirme["temettu_verimi"] = temel.get("temettu_verimi")
            if not degerlendirme["sektor"]:
                degerlendirme["sektor"] = temel.get("sektor")

        return degerlendirme
    except Exception as hata:
        log.warning(f"{sembol} analiz edilemedi: {hata}")
        return None


def tum_hisseleri_tara(hisseler=None, temel_dahil_et=True, max_paralel_islem=10, ilerleme_callback=None):
    """
    Verilen (veya bist_evreni'ndeki tüm) hisseleri PARALEL olarak analiz eder.

    hisseler: None ise bist_evreni.hisse_listesi() kullanılır.
    temel_dahil_et: F/K, PD/DD gibi temel verileri de çeker (ekstra sorgu,
        taramayı yavaşlatır ama 'en ucuz 20' gibi sıralamalar için gerekli).
    max_paralel_islem: aynı anda kaç hissenin sorgulanacağı.
    ilerleme_callback: (tamamlanan_sayi, toplam_sayi, son_sembol) -> None
    """
    if hisseler is None:
        hisseler = hisse_listesi()

    sonuclar = []
    toplam = len(hisseler)
    tamamlanan = 0

    baslangic = time.time()
    log.info(f"Paralel tarama başlıyor: {toplam} hisse, {max_paralel_islem} eşzamanlı işlem.")

    with ThreadPoolExecutor(max_workers=max_paralel_islem) as havuz:
        gorev_haritasi = {
            havuz.submit(_tek_hisseyi_analiz_et, s, temel_dahil_et): s for s in hisseler
        }

        for gorev in as_completed(gorev_haritasi):
            sembol = gorev_haritasi[gorev]
            tamamlanan += 1
            sonuc = gorev.result()
            if sonuc is not None:
                sonuclar.append(sonuc)

            if ilerleme_callback:
                ilerleme_callback(tamamlanan, toplam, sembol)

    gecen_sure = time.time() - baslangic
    log.info(f"Tarama tamamlandı: {len(sonuclar)}/{toplam} hisse başarıyla analiz edildi "
              f"({gecen_sure:.1f} saniye).")

    return sonuclar


def dikkat_cekenleri_listele(sonuclar, kriterler=None):
    """Sonuçları puana göre sıralar. kriterler verilirse önce onlara göre filtreler."""
    if kriterler:
        sonuclar = kriterlere_gore_filtrele(sonuclar, kriterler)

    return sorted(sonuclar, key=lambda x: x["puan"], reverse=True)


# ---------------------------------------------------------------------------
# BIST SIRALAMALARI (Top 20'ler) — plan madde 11
# ---------------------------------------------------------------------------

def _en_iyi_20(sonuclar, alan, ters=True, none_haric=True):
    """Bir sonuç listesini, verilen alana göre sıralayıp ilk 20'yi döner."""
    veri = sonuclar
    if none_haric:
        veri = [s for s in veri if s.get(alan) is not None]
    return sorted(veri, key=lambda s: s[alan], reverse=ters)[:20]


def en_guclu_20(sonuclar):
    """Genel puana göre en güçlü 20 hisse (teknik+temel karışık sinyal puanı)."""
    return _en_iyi_20(sonuclar, "puan", ters=True)


def en_ucuz_20(sonuclar):
    """F/K oranı en düşük (ama pozitif) 20 hisse."""
    pozitif_fk = [s for s in sonuclar if s.get("fk_orani") is not None and s["fk_orani"] > 0]
    return sorted(pozitif_fk, key=lambda s: s["fk_orani"])[:20]


def en_hizli_yukselen_20(sonuclar):
    """1 haftalık % değişime göre en çok yükselen 20 hisse."""
    return _en_iyi_20(sonuclar, "degisim_yuzde_1h", ters=True)


def hacmi_en_cok_artan_20(sonuclar):
    """Relative Volume'e (RVOL) göre hacmi en çok artan 20 hisse."""
    return sorted(
        [s for s in sonuclar if s.get("gostergeler", {}).get("RVOL") is not None],
        key=lambda s: s["gostergeler"]["RVOL"], reverse=True
    )[:20]


def teknik_en_guclu_20(sonuclar):
    """ADX'e göre trendi en güçlü 20 hisse (yön ayrımı yapmadan güç ölçer)."""
    return sorted(
        [s for s in sonuclar if s.get("gostergeler", {}).get("ADX") is not None],
        key=lambda s: s["gostergeler"]["ADX"], reverse=True
    )[:20]


def asiri_satilan_20(sonuclar):
    """RSI'ye göre en aşırı satılmış (en düşük RSI) 20 hisse."""
    return sorted(
        [s for s in sonuclar if s.get("gostergeler", {}).get("RSI") is not None],
        key=lambda s: s["gostergeler"]["RSI"]
    )[:20]


def asiri_alinan_20(sonuclar):
    """RSI'ye göre en aşırı alınmış (en yüksek RSI) 20 hisse."""
    return sorted(
        [s for s in sonuclar if s.get("gostergeler", {}).get("RSI") is not None],
        key=lambda s: s["gostergeler"]["RSI"], reverse=True
    )[:20]


if __name__ == "__main__":
    sonuclar = tum_hisseleri_tara()
    print(f"\nToplam {len(sonuclar)} hisse başarıyla tarandı.\n")

    print("=== EN GÜÇLÜ 20 ===")
    for s in en_guclu_20(sonuclar):
        print(f"{s['sembol']}: puan {s['puan']} — {s['genel_degerlendirme']}")
