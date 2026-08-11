"""
Alarm Sistemi — plan madde 22.
Fiyat, RSI, MACD kesişimi, hacim (RVOL), destek/direnç kırılması, teknik
skor ve genel skor alarmlarını tanımlamayı ve kontrol etmeyi sağlar.

Bu modül ağa bağlanmaz — kontrol edilecek veriyi (fiyat/gösterge/skor)
çağıran taraf (main.py) zaten elinde tutuyor olmalı (tarama sırasında
veya watchlist güncellenirken). Böylece alarm kontrolü hızlı çalışır ve
gereksiz API çağrısı yapmaz.
"""
import json
import os
import uuid
from datetime import datetime

from log_ayarlari import logger_al

log = logger_al(__name__)

ALARM_DOSYASI = "kayitli_alarmlar.json"

ALARM_TURLERI = [
    "fiyat", "rsi", "macd_kesisim_yukari", "macd_kesisim_asagi",
    "hacim", "destek_kirilma", "direnc_kirilma", "teknik_skor", "genel_skor",
]


def alarm_olustur(sembol, tur, deger=None, yon=">"):
    """
    Yeni bir alarm tanımı oluşturur ve diske kaydeder.

    sembol: "THYAO.IS"
    tur: ALARM_TURLERI içinden biri
    deger: eşik değeri (fiyat/rsi/teknik_skor/genel_skor/hacim(RVOL) türleri için gerekli)
    yon: ">" (deger üstüne çıkınca tetikle) veya "<" (altına inince tetikle)
        — macd_kesisim ve destek/direnç_kirilma türlerinde kullanılmaz.
    """
    if tur not in ALARM_TURLERI:
        raise ValueError(f"Geçersiz alarm türü: {tur}. Geçerli türler: {ALARM_TURLERI}")

    alarm = {
        "id": str(uuid.uuid4())[:8],
        "sembol": sembol,
        "tur": tur,
        "deger": deger,
        "yon": yon,
        "aktif": True,
        "tetiklendi": False,
        "olusturma_tarihi": datetime.now().isoformat(timespec="seconds"),
    }

    tumu = _tum_alarmlari_oku()
    tumu.append(alarm)
    _alarmlari_kaydet(tumu)
    return alarm


def alarm_sil(alarm_id):
    tumu = [a for a in _tum_alarmlari_oku() if a["id"] != alarm_id]
    _alarmlari_kaydet(tumu)


def alarmlari_listele(sadece_aktif=True):
    tumu = _tum_alarmlari_oku()
    return [a for a in tumu if a["aktif"]] if sadece_aktif else tumu


def _esik_kontrol(deger, yon, esik):
    if deger is None or deger != deger or esik is None:
        return None
    return bool(deger > esik) if yon == ">" else bool(deger < esik)


def _tek_alarmi_kontrol_et(alarm, veri, skor=None, seviyeler=None):
    """
    Tek bir alarmı, o hisseye ait güncel veriyle kontrol eder.
    veri: test.py -> analiz_et(sembol) çıktısı (DataFrame)
    skor: (opsiyonel) hisse_skoru.hisse_skoru_hesapla() çıktısı
    seviyeler: (opsiyonel) destek_direnc.destek_direnc_bul() çıktısı

    Dönüş: True (tetiklendi) / False (tetiklenmedi) / None (gerekli veri eksik)
    """
    son = veri.iloc[-1]
    tur, yon, deger = alarm["tur"], alarm["yon"], alarm["deger"]

    if tur == "fiyat":
        return _esik_kontrol(son.get("Close"), yon, deger)
    if tur == "rsi":
        return _esik_kontrol(son.get("RSI"), yon, deger)
    if tur == "hacim":
        return _esik_kontrol(son.get("RVOL"), yon, deger)

    if tur == "macd_kesisim_yukari" and len(veri) >= 2:
        onceki = veri.iloc[-2]
        return bool(onceki["MACD"] <= onceki["MACD_Sinyal"] and son["MACD"] > son["MACD_Sinyal"])
    if tur == "macd_kesisim_asagi" and len(veri) >= 2:
        onceki = veri.iloc[-2]
        return bool(onceki["MACD"] >= onceki["MACD_Sinyal"] and son["MACD"] < son["MACD_Sinyal"])

    if tur == "teknik_skor" and skor is not None:
        return _esik_kontrol(skor.get("teknik", {}).get("puan"), yon, deger)
    if tur == "genel_skor" and skor is not None:
        return _esik_kontrol(skor.get("genel"), yon, deger)

    if tur == "destek_kirilma" and seviyeler is not None and seviyeler.get("destekler"):
        return bool(son["Close"] < seviyeler["destekler"][0]["seviye"])
    if tur == "direnc_kirilma" and seviyeler is not None and seviyeler.get("direncler"):
        return bool(son["Close"] > seviyeler["direncler"][0]["seviye"])

    return None  # gerekli ek veri (skor/seviyeler) sağlanmadı


def alarmlari_kontrol_et(sembol_verileri):
    """
    Aktif ve henüz tetiklenmemiş tüm alarmları kontrol eder, tetiklenenleri döner.

    sembol_verileri: {sembol: {"veri": DataFrame, "skor": {...} veya None,
                                "seviyeler": {...} veya None}}
        — hangi semboller için kontrol yapılacağını çağıran taraf belirler
        (genelde watchlist'teki veya alarmı olan semboller).
    """
    tetiklenenler = []
    tumu = _tum_alarmlari_oku()
    degisti = False

    for alarm in tumu:
        if not alarm["aktif"] or alarm["tetiklendi"]:
            continue
        if alarm["sembol"] not in sembol_verileri:
            continue

        paket = sembol_verileri[alarm["sembol"]]
        sonuc = _tek_alarmi_kontrol_et(alarm, paket["veri"], paket.get("skor"), paket.get("seviyeler"))

        if sonuc is True:
            alarm["tetiklendi"] = True
            degisti = True
            mesaj = _alarm_mesaji_olustur(alarm)
            tetiklenenler.append({**alarm, "mesaj": mesaj})
            log.info(f"Alarm tetiklendi: {mesaj}")

    if degisti:
        _alarmlari_kaydet(tumu)

    return tetiklenenler


def _alarm_mesaji_olustur(alarm):
    isimler = {
        "fiyat": "Fiyat", "rsi": "RSI", "hacim": "Hacim (RVOL)",
        "macd_kesisim_yukari": "MACD yukarı kesişim", "macd_kesisim_asagi": "MACD aşağı kesişim",
        "teknik_skor": "Teknik Skor", "genel_skor": "Genel Skor",
        "destek_kirilma": "Destek kırılması", "direnc_kirilma": "Direnç kırılması",
    }
    baslik = isimler.get(alarm["tur"], alarm["tur"])
    if alarm["deger"] is not None:
        return f"{alarm['sembol']}: {baslik} eşiği ({alarm['yon']} {alarm['deger']}) tetiklendi"
    return f"{alarm['sembol']}: {baslik} tetiklendi"


def _tum_alarmlari_oku():
    if not os.path.exists(ALARM_DOSYASI):
        return []
    try:
        with open(ALARM_DOSYASI, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError as hata:
        log.error(f"{ALARM_DOSYASI} bozuk görünüyor, boş liste ile devam ediliyor: {hata}")
        return []


def _alarmlari_kaydet(alarmlar):
    with open(ALARM_DOSYASI, "w", encoding="utf-8") as f:
        json.dump(alarmlar, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    from test import analiz_et

    alarm_olustur("THYAO.IS", "rsi", deger=30, yon="<")
    alarm_olustur("THYAO.IS", "fiyat", deger=300, yon=">")

    veri = analiz_et("THYAO.IS")
    sembol_verileri = {"THYAO.IS": {"veri": veri, "skor": None, "seviyeler": None}}

    tetiklenenler = alarmlari_kontrol_et(sembol_verileri)
    print(f"\n{len(tetiklenenler)} alarm tetiklendi:")
    for t in tetiklenenler:
        print(f"  - {t['mesaj']}")