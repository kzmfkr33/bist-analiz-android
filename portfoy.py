import json
import os
from datetime import date

from veri_katmani import fiyat_verisi_getir
from log_ayarlari import logger_al

log = logger_al(__name__)

PORTFOY_DOSYASI = "portfoyum.json"
GECMIS_DOSYASI = "islem_gecmisi.json"


# ---------------------------------------------------------------------------
# Açık pozisyonlar (portfoyum.json)
# ---------------------------------------------------------------------------

def _portfoyu_oku():
    if not os.path.exists(PORTFOY_DOSYASI):
        return []
    with open(PORTFOY_DOSYASI, "r", encoding="utf-8") as f:
        return json.load(f)


def _portfoyu_kaydet(pozisyonlar):
    with open(PORTFOY_DOSYASI, "w", encoding="utf-8") as f:
        json.dump(pozisyonlar, f, ensure_ascii=False, indent=2)


def pozisyon_ekle(sembol, adet, maliyet_fiyati, tarih=None):
    """Portföye yeni bir alım ekler (aynı hisseden zaten varsa ayrı satır olarak eklenir)."""
    pozisyonlar = _portfoyu_oku()
    pozisyonlar.append({
        "sembol": sembol,
        "adet": adet,
        "maliyet_fiyati": maliyet_fiyati,
        "tarih": tarih or str(date.today()),
    })
    _portfoyu_kaydet(pozisyonlar)
    log.info(f"Pozisyon eklendi: {sembol} x{adet} @ {maliyet_fiyati} TL")


def pozisyon_sil(sembol, tarih):
    """Belirli bir sembol+tarih kombinasyonundaki pozisyonu TAMAMEN siler.
    Kısmi satış için pozisyon_kismi_sat() kullan."""
    pozisyonlar = _portfoyu_oku()
    pozisyonlar = [p for p in pozisyonlar if not (p["sembol"] == sembol and p["tarih"] == tarih)]
    _portfoyu_kaydet(pozisyonlar)


def pozisyon_kismi_sat(sembol, adet, satis_fiyati, tarih=None):
    """
    Bir hisseden kısmi (veya tam) satış yapar. FIFO mantığı kullanılır:
    en eski alım kayıtlarından başlayarak satılan adet düşülür — bu, gerçek
    borsa muhasebesinde de en yaygın kullanılan yöntemdir.

    Gerçekleşen kâr/zararı hesaplar, islem_gecmisi.json'a kaydeder ve
    tutarını geri döner.

    Hata fırlatır: elinde satılacak kadar adet yoksa (ValueError).
    """
    pozisyonlar = _portfoyu_oku()

    ilgili = sorted(
        [p for p in pozisyonlar if p["sembol"] == sembol],
        key=lambda p: p["tarih"],
    )
    diger_semboller = [p for p in pozisyonlar if p["sembol"] != sembol]

    mevcut_toplam = sum(p["adet"] for p in ilgili)
    if adet > mevcut_toplam:
        raise ValueError(
            f"{sembol} için satılmak istenen adet ({adet}), elindeki adetten "
            f"({mevcut_toplam}) fazla."
        )

    kalan_satis_adedi = adet
    guncellenmis_pozisyonlar = []
    gerceklesen_kar_zarar = 0.0
    kullanilan_maliyet_toplami = 0.0

    for p in ilgili:
        if kalan_satis_adedi <= 0:
            guncellenmis_pozisyonlar.append(p)
            continue

        if p["adet"] <= kalan_satis_adedi:
            # Bu alım kaydının tamamı satılıyor
            gerceklesen_kar_zarar += p["adet"] * (satis_fiyati - p["maliyet_fiyati"])
            kullanilan_maliyet_toplami += p["adet"] * p["maliyet_fiyati"]
            kalan_satis_adedi -= p["adet"]
            # bu kayıt tamamen düştüğü için guncellenmis_pozisyonlar'a eklenmiyor
        else:
            # Bu alım kaydının bir kısmı satılıyor
            gerceklesen_kar_zarar += kalan_satis_adedi * (satis_fiyati - p["maliyet_fiyati"])
            kullanilan_maliyet_toplami += kalan_satis_adedi * p["maliyet_fiyati"]
            p = dict(p)
            p["adet"] -= kalan_satis_adedi
            kalan_satis_adedi = 0
            guncellenmis_pozisyonlar.append(p)

    _portfoyu_kaydet(diger_semboller + guncellenmis_pozisyonlar)

    gerceklesen_kar_zarar = round(gerceklesen_kar_zarar, 2)
    gerceklesen_yuzde = (
        round((gerceklesen_kar_zarar / kullanilan_maliyet_toplami) * 100, 2)
        if kullanilan_maliyet_toplami else 0
    )

    _gecmise_kaydet({
        "sembol": sembol,
        "adet": adet,
        "satis_fiyati": satis_fiyati,
        "tarih": tarih or str(date.today()),
        "gerceklesen_kar_zarar": gerceklesen_kar_zarar,
        "gerceklesen_kar_zarar_yuzde": gerceklesen_yuzde,
    })

    log.info(f"Kısmi/tam satış: {sembol} x{adet} @ {satis_fiyati} TL "
              f"(gerçekleşen K/Z: {gerceklesen_kar_zarar} TL)")

    return gerceklesen_kar_zarar


def portfoy_ozeti():
    """
    Portföydeki tüm pozisyonların güncel fiyatlarla kâr/zararını hesaplar.
    Aynı sembolden birden fazla alım varsa birleştirip ağırlıklı ortalama maliyet çıkarır.
    """
    pozisyonlar = _portfoyu_oku()
    if not pozisyonlar:
        return {"mesaj": "Portföyde pozisyon yok.", "pozisyonlar": [], "toplam_deger": 0, "toplam_kar_zarar": 0}

    semboller = {}
    for p in pozisyonlar:
        s = p["sembol"]
        if s not in semboller:
            semboller[s] = {"toplam_adet": 0, "toplam_maliyet": 0}
        semboller[s]["toplam_adet"] += p["adet"]
        semboller[s]["toplam_maliyet"] += p["adet"] * p["maliyet_fiyati"]

    sonuc_listesi = []
    toplam_deger = 0
    toplam_maliyet_genel = 0

    for sembol, bilgi in semboller.items():
        try:
            guncel_veri = fiyat_verisi_getir(sembol, periyot="5d")
            guncel_fiyat = guncel_veri['Close'].iloc[-1]
        except Exception as hata:
            log.warning(f"{sembol} güncel fiyatı alınamadı: {hata}")
            guncel_fiyat = None

        adet = bilgi["toplam_adet"]
        ort_maliyet = bilgi["toplam_maliyet"] / adet

        if guncel_fiyat is not None:
            guncel_deger = adet * guncel_fiyat
            kar_zarar = guncel_deger - bilgi["toplam_maliyet"]
            kar_zarar_yuzde = (kar_zarar / bilgi["toplam_maliyet"]) * 100
            toplam_deger += guncel_deger
        else:
            guncel_deger = None
            kar_zarar = None
            kar_zarar_yuzde = None

        toplam_maliyet_genel += bilgi["toplam_maliyet"]

        sonuc_listesi.append({
            "sembol": sembol,
            "adet": adet,
            "ortalama_maliyet": round(ort_maliyet, 2),
            "guncel_fiyat": round(guncel_fiyat, 2) if guncel_fiyat else None,
            "guncel_deger": round(guncel_deger, 2) if guncel_deger else None,
            "kar_zarar": round(kar_zarar, 2) if kar_zarar is not None else None,
            "kar_zarar_yuzde": round(kar_zarar_yuzde, 2) if kar_zarar_yuzde is not None else None,
        })

    toplam_kar_zarar = toplam_deger - toplam_maliyet_genel

    return {
        "pozisyonlar": sonuc_listesi,
        "toplam_maliyet": round(toplam_maliyet_genel, 2),
        "toplam_deger": round(toplam_deger, 2),
        "toplam_kar_zarar": round(toplam_kar_zarar, 2),
        "toplam_kar_zarar_yuzde": round((toplam_kar_zarar / toplam_maliyet_genel) * 100, 2) if toplam_maliyet_genel else 0,
    }


# ---------------------------------------------------------------------------
# Gerçekleşen (satılmış) işlem geçmişi (islem_gecmisi.json)
# ---------------------------------------------------------------------------

def _gecmisi_oku():
    if not os.path.exists(GECMIS_DOSYASI):
        return []
    with open(GECMIS_DOSYASI, "r", encoding="utf-8") as f:
        return json.load(f)


def _gecmise_kaydet(islem):
    gecmis = _gecmisi_oku()
    gecmis.append(islem)
    with open(GECMIS_DOSYASI, "w", encoding="utf-8") as f:
        json.dump(gecmis, f, ensure_ascii=False, indent=2)


def gerceklesen_kar_zarar_ozeti():
    """Tüm satış geçmişini ve toplam gerçekleşen kâr/zararı döner."""
    gecmis = _gecmisi_oku()
    toplam = sum(g["gerceklesen_kar_zarar"] for g in gecmis)
    return {
        "islemler": sorted(gecmis, key=lambda g: g["tarih"], reverse=True),
        "toplam_gerceklesen_kar_zarar": round(toplam, 2),
        "islem_sayisi": len(gecmis),
    }


if __name__ == "__main__":
    # Örnek kullanım — kendi pozisyonlarını eklemek için bu satırları düzenle
    # pozisyon_ekle("THYAO.IS", adet=50, maliyet_fiyati=280.5)
    # pozisyon_ekle("ASELS.IS", adet=100, maliyet_fiyati=65.2)
    # pozisyon_kismi_sat("THYAO.IS", adet=20, satis_fiyati=310.0)  # 20 adetini sat

    ozet = portfoy_ozeti()

    if not ozet["pozisyonlar"]:
        print(ozet["mesaj"])
        print("\nPozisyon eklemek için dosyanın en altındaki örnek satırların başındaki # işaretini kaldır.")
    else:
        print("=== PORTFÖY ÖZETİ (açık pozisyonlar) ===\n")
        for p in ozet["pozisyonlar"]:
            print(f"{p['sembol']}: {p['adet']} adet, ort. maliyet {p['ortalama_maliyet']} TL")
            print(f"  Güncel: {p['guncel_fiyat']} TL | Değer: {p['guncel_deger']} TL | K/Z: {p['kar_zarar']} TL (%{p['kar_zarar_yuzde']})\n")

        print(f"TOPLAM DEĞER: {ozet['toplam_deger']} TL")
        print(f"TOPLAM K/Z (henüz satılmamış): {ozet['toplam_kar_zarar']} TL (%{ozet['toplam_kar_zarar_yuzde']})")

    gerceklesen = gerceklesen_kar_zarar_ozeti()
    if gerceklesen["islem_sayisi"]:
        print(f"\n=== GERÇEKLEŞEN K/Z (satılmış işlemler) ===")
        print(f"Toplam {gerceklesen['islem_sayisi']} satış, toplam gerçekleşen K/Z: "
              f"{gerceklesen['toplam_gerceklesen_kar_zarar']} TL")
