import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

import pandas as pd

from test import analiz_et
from sinyal_motoru import sinyal_uret
from tarama_kriterleri import kriterlere_gore_filtrele
from log_ayarlari import logger_al

log = logger_al(__name__)

WIKI_URL = "https://tr.wikipedia.org/wiki/Borsa_İstanbul'da_işlem_gören_şirketler_listesi"
LISTE_DOSYASI = "bist_hisseleri.csv"

# Wikipedia'ya hiç ulaşılamazsa ve elde hiç yerel liste yoksa kullanılacak
# küçük bir "tohum" listesi — en likit/bilinen BIST hisselerinden oluşur.
# Bu bir YEDEK'tir, tam BIST listesinin yerini tutmaz.
YEDEK_LISTE = [
    "THYAO.IS", "ASELS.IS", "GARAN.IS", "AKBNK.IS", "ISCTR.IS", "YKBNK.IS",
    "SISE.IS", "KCHOL.IS", "SAHOL.IS", "EREGL.IS", "TUPRS.IS", "BIMAS.IS",
    "PGSUS.IS", "FROTO.IS", "TCELL.IS", "TTKOM.IS", "ARCLK.IS", "TOASO.IS",
    "KOZAL.IS", "PETKM.IS",
]


def tum_bist_kodlarini_getir(yeniden_indir=False):
    """
    BIST hisse kodlarını döner. Öncelik sırası:
      1) Yerel CSV varsa ve yeniden_indir=False ise onu kullan (hızlı).
      2) Wikipedia'dan indirmeyi dene, başarılıysa CSV'ye kaydet.
      3) Wikipedia da başarısız olursa: eski CSV varsa onu kullan (bayat da olsa
         hiç liste olmamasından iyidir), yoksa küçük YEDEK_LISTE'yi kullan.
    """
    if os.path.exists(LISTE_DOSYASI) and not yeniden_indir:
        df = pd.read_csv(LISTE_DOSYASI)
        log.info(f"BIST listesi yerel dosyadan okundu ({len(df)} hisse).")
        return df["Sembol"].tolist()

    log.info("BIST hisse listesi Wikipedia'dan indiriliyor...")
    try:
        tablolar = pd.read_html(WIKI_URL)

        hedef_tablo = None
        for t in tablolar:
            if "Kod" in t.columns:
                hedef_tablo = t
                break

        if hedef_tablo is None:
            raise ValueError("Wikipedia sayfasında 'Kod' kolonlu tablo bulunamadı.")

        kodlar = hedef_tablo["Kod"].dropna().unique().tolist()
        semboller = [f"{kod.strip()}.IS" for kod in kodlar if isinstance(kod, str)]

        if len(semboller) < 50:
            # Sayfa yapısı bozulmuş ama hata da fırlatmamış olabilir — çok az
            # sonuç şüphelidir, bunu bayat/yedek listeye düşmek için hataya çevir.
            raise ValueError(f"Sadece {len(semboller)} hisse bulundu, bu şüpheli derecede az.")

        pd.DataFrame({"Sembol": semboller}).to_csv(LISTE_DOSYASI, index=False)
        log.info(f"{len(semboller)} hisse bulundu, {LISTE_DOSYASI} dosyasına kaydedildi.")
        return semboller

    except Exception as hata:
        log.warning(f"Wikipedia'dan liste alınamadı: {hata}")

        if os.path.exists(LISTE_DOSYASI):
            df = pd.read_csv(LISTE_DOSYASI)
            log.warning(f"Bayat yerel liste kullanılıyor ({len(df)} hisse). "
                        "Güncel olmayabilir.")
            return df["Sembol"].tolist()

        log.warning(f"Hiç liste kaynağı yok — {len(YEDEK_LISTE)} hisselik küçük "
                    "yedek listeye düşülüyor. Tam BIST taraması için Wikipedia "
                    "bağlantısını kontrol et.")
        return YEDEK_LISTE


def _tek_hisseyi_analiz_et(sembol):
    """Tek bir hisseyi analiz eder, hata durumunda None döner (paralel çalışmaya uygun)."""
    try:
        veri = analiz_et(sembol)
        degerlendirme = sinyal_uret(veri)
        degerlendirme["sembol"] = sembol
        return degerlendirme
    except Exception as hata:
        log.warning(f"{sembol} analiz edilemedi: {hata}")
        return None


def tum_hisseleri_tara(hisse_listesi, max_paralel_islem=10, ilerleme_callback=None):
    """
    Listedeki tüm hisseleri PARALEL olarak analiz eder, her biri için sinyal üretir.

    max_paralel_islem: aynı anda kaç hissenin sorgulanacağı. Çok yüksek tutmak
        yfinance'ı rate-limit'e sokabilir; 10 makul bir varsayılan.
    ilerleme_callback: (tamamlanan_sayi, toplam_sayi, son_sembol) -> None
        şeklinde bir fonksiyon; Streamlit ilerleme çubuğunu güncellemek için
        kullanılabilir. Verilmezse sadece loglanır.
    """
    sonuclar = []
    toplam = len(hisse_listesi)
    tamamlanan = 0

    baslangic = time.time()
    log.info(f"Paralel tarama başlıyor: {toplam} hisse, {max_paralel_islem} eşzamanlı işlem.")

    with ThreadPoolExecutor(max_workers=max_paralel_islem) as havuz:
        gorev_haritasi = {havuz.submit(_tek_hisseyi_analiz_et, s): s for s in hisse_listesi}

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
    """
    Sonuçları puana göre sıralar. kriterler verilirse önce onlara göre filtreler.
    """
    if kriterler:
        sonuclar = kriterlere_gore_filtrele(sonuclar, kriterler)
        print(f"\n({len(sonuclar)} hisse kriterlere uydu)")

    siralanmis = sorted(sonuclar, key=lambda x: x["puan"], reverse=True)

    print("\n" + "=" * 50)
    print("TARAMA SONUÇLARI (En olumludan en olumsuza)")
    print("=" * 50)

    for s in siralanmis:
        print(f"\n{s['sembol']} — {s['genel_degerlendirme']} (puan: {s['puan']})")
        print(f"  Kapanış: {s['kapanis_fiyati']:.2f} TL")
        for d in s["detaylar"]:
            print(f"  - {d}")


if __name__ == "__main__":
    hisse_listesi = tum_bist_kodlarini_getir()
    print(f"Toplam {len(hisse_listesi)} hisse taranacak.\n")

    sonuclar = tum_hisseleri_tara(hisse_listesi)

    ornek_kriterler = [
        {"alan": "RSI", "operator": "<", "deger": 35},
        {"alan": "puan", "operator": ">=", "deger": 1},
    ]
    dikkat_cekenleri_listele(sonuclar, kriterler=ornek_kriterler)
