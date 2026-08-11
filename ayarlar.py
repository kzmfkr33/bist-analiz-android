import json
import os

# GÜVENLİK NOTU: Telegram/Gemini gibi API anahtarlarını asla doğrudan bu
# dosyaya (ve dolayısıyla APK'nın içine) yazma — APK'yı paylaşırsan anahtarın
# da dağılır. Bunun yerine uygulama içindeki "Ayarlar" ekranından gireriz;
# değerler cihazdaki ayarlar.json dosyasında (APK dışında) saklanır.

_AYAR_DOSYASI = "ayarlar.json"

VARSAYILAN_AYARLAR = {
    "toplam_sermaye": 100000,
    "telegram_bot_token": "",
    "telegram_chat_id": "",
    "gemini_api_key": "",
}


def ayarlari_oku():
    if not os.path.exists(_AYAR_DOSYASI):
        return dict(VARSAYILAN_AYARLAR)
    try:
        with open(_AYAR_DOSYASI, "r", encoding="utf-8") as f:
            kayitli = json.load(f)
        birlesik = dict(VARSAYILAN_AYARLAR)
        birlesik.update(kayitli)
        return birlesik
    except Exception:
        return dict(VARSAYILAN_AYARLAR)


def ayarlari_kaydet(yeni_ayarlar):
    mevcut = ayarlari_oku()
    mevcut.update(yeni_ayarlar)
    with open(_AYAR_DOSYASI, "w", encoding="utf-8") as f:
        json.dump(mevcut, f, ensure_ascii=False, indent=2)
    return mevcut


# Diğer modüllerin `from ayarlar import TOPLAM_SERMAYE` gibi kullanımlarıyla
# geriye dönük uyumluluk için:
_ayarlar = ayarlari_oku()
TOPLAM_SERMAYE = _ayarlar["toplam_sermaye"]
GEMINI_API_KEY = _ayarlar["gemini_api_key"]
