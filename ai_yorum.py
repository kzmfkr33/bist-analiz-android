"""
Google Gemini API ile hisse analizine dair kısa, doğal dilde yorum üretir — plan madde 18.

AI'nın görevi TAHMİN üretmek değil, hesaplama motorlarının (hisse skoru,
teknik sinyal merkezi, destek/direnç, sektöre göre değerleme, fırsat
tarayıcı) ürettiği rakamları yorumlamaktır. Tüm sayılar önceden
hesaplanmış motorlardan gelir ve prompt içinde AI'ya olduğu gibi verilir
— AI hiçbir rakamı kendisi üretmez, sadece anlaşılır Türkçeye çevirir.
Bu sayede kaynak/hesaplama mantığı her zaman izlenebilir kalır.
"""
import requests

from test import analiz_et
from veri_katmani import temel_veri_getir
from hisse_skoru import hisse_skoru_hesapla
from teknik_sinyal_merkezi import teknik_gorunum_uret
from destek_direnc import destek_direnc_bul
from firsat_tarayici import firsatlari_tespit_et
from relative_guc import relative_strength_hesapla, bist100_getir
from temel_analiz import sektore_gore_degerleme

_GEMINI_MODEL = "gemini-flash-latest"
_GEMINI_URL = (
    f"https://generativelanguage.googleapis.com/v1beta/models/"
    f"{_GEMINI_MODEL}:generateContent"
)


class AIYorumHatasi(Exception):
    pass


def zengin_analiz_verisi_olustur(sembol, sektordeki_diger_hisseler=None):
    """
    Bir hisse için AI yorumunun dayanacağı TÜM ham veriyi tek yerde toplar.
    Döndürülen sözlükteki her rakam ayrı bir hesaplama motorundan gelir
    (tahmin değil, gerçek hesaplama) — AI sadece bunu yorumlar.

    sektordeki_diger_hisseler: (opsiyonel) aynı sektördeki diğer hisselerin
        temel_veri_getir() çıktıları — verilirse "değerleme" bölümüne
        sektöre göre iskonto/prim bilgisi eklenir. UI adımında bunu
        tarayici.py'nin zaten topladığı sonuçlardan sektöre göre
        filtreleyerek vereceğiz (tekrar API çağrısı yapmadan).
    """
    veri = analiz_et(sembol)
    temel = temel_veri_getir(sembol)
    skor = hisse_skoru_hesapla(veri, temel)
    teknik_gorunum = teknik_gorunum_uret(veri.iloc[-1])
    seviyeler = destek_direnc_bul(veri)
    firsatlar = firsatlari_tespit_et(veri)

    try:
        rs = relative_strength_hesapla(veri, bist100_getir())
    except Exception:
        rs = {}

    degerleme_karsilastirma = None
    if sektordeki_diger_hisseler:
        degerleme_karsilastirma = sektore_gore_degerleme(temel, sektordeki_diger_hisseler)

    return {
        "sembol": sembol,
        "sirket_adi": temel.get("sirket_adi") or sembol,
        "kapanis_fiyati": round(float(veri["Close"].iloc[-1]), 2),
        "skor": skor,
        "teknik_gorunum": teknik_gorunum,
        "destek_direnc": seviyeler,
        "firsatlar": firsatlar,
        "relative_strength": rs,
        "degerleme_karsilastirma": degerleme_karsilastirma,
    }


def _bilesen_ozeti(bilesenler):
    """Bir alt skorun bileşenlerini 'isim: ham_deger' satırlarına çevirir (prompt için)."""
    return "\n".join(f"  - {isim}: {ham}" for isim, ham, _puan, _agirlik in bilesenler)


def _prompt_olustur(veri_paketi):
    skor = veri_paketi["skor"]
    teknik_gorunum = veri_paketi["teknik_gorunum"]
    seviyeler = veri_paketi["destek_direnc"]
    firsatlar = veri_paketi["firsatlar"]
    rs = veri_paketi.get("relative_strength") or {}
    degerleme = veri_paketi.get("degerleme_karsilastirma")

    direnc_metni = ", ".join(
        f"{d['seviye']} TL (güç {d['guc']}/5)" for d in seviyeler["direncler"]
    ) or "tespit edilemedi"
    destek_metni = ", ".join(
        f"{d['seviye']} TL (güç {d['guc']}/5)" for d in seviyeler["destekler"]
    ) or "tespit edilemedi"
    firsat_metni = ", ".join(firsatlar) if firsatlar else "belirgin bir fırsat sinyali yok"

    degerleme_metni = "Sektör kıyaslaması yapılamadı (veri yok)"
    if degerleme:
        parcalar = []
        for anahtar, baslik in [("fk", "F/K"), ("pd_dd", "PD/DD"), ("fd_favok", "FD/FAVÖK")]:
            d = degerleme.get(anahtar)
            if d:
                parcalar.append(
                    f"{baslik}: şirket {d['sirket_degeri']}, sektör ort. "
                    f"{d['sektor_ortalamasi']} ({d['yorum']})"
                )
        degerleme_metni = "; ".join(parcalar) if parcalar else degerleme_metni

    return (
        "Aşağıda bir BIST hissesi için birden fazla hesaplama motorunun "
        "(hisse skoru, teknik sinyal merkezi, destek/direnç, sektöre göre "
        "değerleme) ürettiği RAKAMSAL bulgular var. Bunları bir yatırımcının "
        "kolayca anlayacağı şekilde 5-7 cümlelik doğal, akıcı bir Türkçe "
        "özete çevir. Şu başlıkları kısaca kapsa: genel görünüm, teknik "
        "durum, momentum, hacim, temel görünüm, değerleme, risk. Sayıları "
        "olduğu gibi tekrarlama, ne anlama geldiklerini açıkla. HİÇBİR "
        "rakamı kendin üretme veya tahmin etme — sadece sana verilenleri "
        "yorumla. Kesinlikle 'al', 'sat' gibi kesin bir yatırım tavsiyesi "
        "verme; görünümü tarafsızca özetle ve sonunda kısaca bunun yatırım "
        "tavsiyesi olmadığını hatırlat.\n\n"
        f"Şirket: {veri_paketi['sirket_adi']} ({veri_paketi['sembol']})\n"
        f"Kapanış fiyatı: {veri_paketi['kapanis_fiyati']} TL\n\n"
        f"GENEL SKOR: {skor['genel']}/100\n"
        f"  Trend: {skor['trend']['puan']}/100\n{_bilesen_ozeti(skor['trend']['bilesenler'])}\n"
        f"  Momentum: {skor['momentum']['puan']}/100\n{_bilesen_ozeti(skor['momentum']['bilesenler'])}\n"
        f"  Teknik: {skor['teknik']['puan']}/100\n{_bilesen_ozeti(skor['teknik']['bilesenler'])}\n"
        f"  Hacim: {skor['hacim']['puan']}/100\n{_bilesen_ozeti(skor['hacim']['bilesenler'])}\n"
        f"  Temel: {skor['temel']['puan']}/100\n{_bilesen_ozeti(skor['temel']['bilesenler'])}\n"
        f"  Değerleme: {skor['degerleme']['puan']}/100\n{_bilesen_ozeti(skor['degerleme']['bilesenler'])}\n\n"
        f"TEKNİK SİNYAL MERKEZİ: {teknik_gorunum['etiket']} (puan: {teknik_gorunum['puan']})\n\n"
        f"DESTEK SEVİYELERİ: {destek_metni}\n"
        f"DİRENÇ SEVİYELERİ: {direnc_metni}\n\n"
        f"SEKTÖRE GÖRE DEĞERLEME: {degerleme_metni}\n\n"
        f"RELATIVE STRENGTH (BIST 100'e göre, 1 hafta): {rs.get('1h', 'veri yok')}\n\n"
        f"FIRSAT SİNYALLERİ: {firsat_metni}"
    )


def hisse_yorumu_uret(sembol, api_key, sektordeki_diger_hisseler=None):
    """
    `sembol`: analiz edilecek hisse (örn. "THYAO.IS").
    `api_key`: Ayarlar ekranından girilen Gemini API anahtarı.
    `sektordeki_diger_hisseler`: (opsiyonel) sektöre göre değerleme için.

    Başarılıysa üretilen yorum metnini (str) döner.
    Hata durumunda AIYorumHatasi fırlatır (çağıran taraf mesajı UI'da gösterir).
    """
    if not api_key:
        raise AIYorumHatasi(
            "Gemini API anahtarı girilmemiş. Ayarlar ekranından ücretsiz "
            "bir anahtar ekleyebilirsin (aistudio.google.com/app/apikey)."
        )

    try:
        veri_paketi = zengin_analiz_verisi_olustur(sembol, sektordeki_diger_hisseler)
    except Exception as e:
        raise AIYorumHatasi(f"Analiz verisi hazırlanırken hata oluştu: {e}") from e

    govde = {
        "contents": [
            {"parts": [{"text": _prompt_olustur(veri_paketi)}]}
        ],
        "generationConfig": {
            "temperature": 0.4,
            "maxOutputTokens": 500,
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


if __name__ == "__main__":
    import sys
    api_key = sys.argv[1] if len(sys.argv) > 1 else None
    if not api_key:
        print("Kullanım: python ai_yorum.py <GEMINI_API_KEY>")
    else:
        yorum = hisse_yorumu_uret("THYAO.IS", api_key)
        print(yorum)