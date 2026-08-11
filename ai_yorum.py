"""
Google Gemini API ile hisse analizine dair kısa, doğal dilde yorum üretir.

Neden Gemini?
  - Ücretsiz katmanı var (kredi kartı istemiyor, süresi dolmuyor).
  - Kişisel/hobi ölçekli kullanım (günde birkaç istek) için bu katman
    fazlasıyla yeterli.
  - Tek bir HTTPS isteği (requests) ile çalışıyor; ekstra ağır bir SDK
    kurmaya gerek yok, bu da Android derlemesini (buildozer/p4a) daha
    sağlam tutar.

Ücretsiz API anahtarı almak için: https://aistudio.google.com/app/apikey

NOT: Burada üretilen metin yatırım tavsiyesi değildir; sadece uygulamanın
kendi kural tabanlı puanlamasının (teknik + temel) doğal dile çevrilmiş,
kısa bir özetidir.
"""
import requests

_GEMINI_MODEL = "gemini-2.5-flash"
_GEMINI_URL = (
    f"https://generativelanguage.googleapis.com/v1beta/models/"
    f"{_GEMINI_MODEL}:generateContent"
)


class AIYorumHatasi(Exception):
    pass


def _prompt_olustur(sonuc):
    teknik_satirlar = "\n".join(f"- {d}" for d in sonuc.get("teknik_detaylar", []))
    temel_satirlar = "\n".join(f"- {d}" for d in sonuc.get("temel_detaylar", []))

    return (
        "Aşağıda bir hisse senedi için kural tabanlı (teknik + temel) bir "
        "analiz motorunun ürettiği bulgular var. Bunları, bir yatırımcının "
        "kolayca anlayacağı şekilde 3-5 cümlelik doğal, akıcı bir Türkçe "
        "özete çevir. Sayıları tekrarlamak yerine ne anlama geldiklerini "
        "açıkla. Kesinlikle 'al', 'sat' gibi kesin bir yatırım tavsiyesi "
        "verme; bunun yerine görünümü tarafsızca özetle ve sonunda kısaca "
        "bunun yatırım tavsiyesi olmadığını hatırlat.\n\n"
        f"Şirket: {sonuc.get('sirket_adi') or sonuc.get('sembol')} "
        f"({sonuc.get('sembol')})\n"
        f"Kapanış fiyatı: {sonuc.get('kapanis_fiyati')} TL\n\n"
        f"Teknik analiz (puan: {sonuc.get('teknik_puan')}):\n{teknik_satirlar}\n\n"
        f"Temel analiz (puan: {sonuc.get('temel_puan')}):\n{temel_satirlar}\n\n"
        f"Birleşik değerlendirme: {sonuc.get('birlesik_genel')} "
        f"(toplam puan: {sonuc.get('birlesik_puan')})"
    )


def hisse_yorumu_uret(sonuc, api_key):
    """
    `sonuc`: test.py -> tam_analiz_et() çıktısı (dict).
    `api_key`: Ayarlar ekranından girilen Gemini API anahtarı.

    Başarılıysa üretilen yorum metnini (str) döner.
    Hata durumunda AIYorumHatasi fırlatır (çağıran taraf mesajı UI'da gösterir).
    """
    if not api_key:
        raise AIYorumHatasi(
            "Gemini API anahtarı girilmemiş. Ayarlar ekranından ücretsiz "
            "bir anahtar ekleyebilirsin (aistudio.google.com/app/apikey)."
        )

    govde = {
        "contents": [
            {"parts": [{"text": _prompt_olustur(sonuc)}]}
        ],
        "generationConfig": {
            "temperature": 0.4,
            "maxOutputTokens": 400,
        },
    }

    try:
        yanit = requests.post(
            _GEMINI_URL,
            params={"key": api_key},
            json=govde,
            timeout=30,
        )
    except requests.RequestException as e:
        raise AIYorumHatasi(f"Gemini API'ye ulaşılamadı: {e}") from e

    if yanit.status_code == 429:
        raise AIYorumHatasi(
            "Gemini ücretsiz katman istek limitine ulaşıldı (dakikada/günde "
            "sınırlı istek). Birkaç dakika sonra tekrar dene."
        )
    if yanit.status_code == 400:
        raise AIYorumHatasi(
            "Gemini API anahtarı geçersiz görünüyor. Ayarlar ekranından "
            "kontrol et."
        )
    if not yanit.ok:
        raise AIYorumHatasi(f"Gemini API hatası (kod {yanit.status_code}): {yanit.text[:200]}")

    veri = yanit.json()
    try:
        adaylar = veri["candidates"]
        if not adaylar:
            raise AIYorumHatasi("Gemini boş yanıt döndürdü.")
        parcalar = adaylar[0]["content"]["parts"]
        metin = "".join(p.get("text", "") for p in parcalar).strip()
        if not metin:
            raise AIYorumHatasi("Gemini boş bir yorum döndürdü.")
        return metin
    except (KeyError, IndexError) as e:
        raise AIYorumHatasi(f"Gemini yanıtı beklenmeyen formatta: {e}") from e
