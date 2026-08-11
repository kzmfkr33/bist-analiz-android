"""
BIST Analiz Merkezi - Android (Kivy) sürümü.

Orijinal Streamlit arayüzü yerine, aynı analiz/tarama/portföy motorunu
(gostergeler.py, sinyal_motoru.py, temel_analiz.py, tarayici.py, portfoy.py...)
kullanan native bir Kivy arayüzü. Ağ çağrıları (fiyat verisi çekme, tarama)
UI'yi kilitlememesi için arka plan thread'lerinde çalışır.
"""
import os
import threading

from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.progressbar import ProgressBar
from kivy.uix.screenmanager import Screen, ScreenManager, SlideTransition
from kivy.uix.scrollview import ScrollView
from kivy.uix.spinner import Spinner
from kivy.uix.textinput import TextInput
from kivy.utils import platform

# ---------------------------------------------------------------------------
# Uygulama verilerinin (JSON/CSV/log dosyaları) yazılacağı klasörü,
# içe aktarmalardan ÖNCE ayarlıyoruz — portfoy.py, tarama_kriterleri.py,
# log_ayarlari.py gibi modüller dosyaları geçerli çalışma dizinine göre
# (göreli yol) açıyor.
# ---------------------------------------------------------------------------
if platform == "android":
    from android.storage import app_storage_path
    _VERI_DIZINI = app_storage_path()
else:
    _VERI_DIZINI = os.path.join(os.path.expanduser("~"), ".bist_analiz_merkezi")

os.makedirs(_VERI_DIZINI, exist_ok=True)
os.chdir(_VERI_DIZINI)

from test import tam_analiz_et                                  # noqa: E402
from tarayici import tum_bist_kodlarini_getir, tum_hisseleri_tara, YEDEK_LISTE  # noqa: E402
from tarama_kriterleri import kriterlere_gore_filtrele          # noqa: E402
from risk_yonetimi import atr_ile_stop_onerisi, pozisyon_buyuklugu_hesapla  # noqa: E402
from portfoy import pozisyon_ekle, portfoy_ozeti                # noqa: E402
import ayarlar                                                  # noqa: E402

RENK_ARKAPLAN = (0.07, 0.09, 0.13, 1)
RENK_KART = (0.12, 0.15, 0.20, 1)
RENK_OLUMLU = (0.20, 0.75, 0.45, 1)
RENK_OLUMSUZ = (0.85, 0.30, 0.30, 1)
RENK_NOTR = (0.85, 0.70, 0.20, 1)
RENK_METIN = (0.92, 0.94, 0.96, 1)
RENK_VURGU = (0.20, 0.55, 0.95, 1)

Window.clearcolor = RENK_ARKAPLAN


def _puana_gore_renk(puan):
    if puan is None:
        return RENK_NOTR
    if puan >= 2:
        return RENK_OLUMLU
    if puan <= -2:
        return RENK_OLUMSUZ
    return RENK_NOTR


def baslik_etiketi(metin, boyut=20):
    return Label(
        text=metin, font_size=dp(boyut), bold=True, color=RENK_METIN,
        size_hint_y=None, height=dp(boyut + 20), halign="left", valign="middle",
    )


def govde_etiketi(metin, renk=RENK_METIN):
    lbl = Label(
        text=metin, font_size=dp(14), color=renk, size_hint_y=None,
        halign="left", valign="top",
    )
    lbl.bind(width=lambda i, w: setattr(i, "text_size", (w, None)))
    lbl.bind(texture_size=lambda i, ts: setattr(i, "height", ts[1]))
    return lbl


def uyari_goster(baslik, mesaj):
    icerik = BoxLayout(orientation="vertical", padding=dp(15), spacing=dp(10))
    icerik.add_widget(govde_etiketi(mesaj))
    kapat = Button(text="Tamam", size_hint_y=None, height=dp(45))
    icerik.add_widget(kapat)
    pop = Popup(title=baslik, content=icerik, size_hint=(0.85, 0.4))
    kapat.bind(on_release=pop.dismiss)
    pop.open()


class KartKutu(BoxLayout):
    """Koyu temalı, köşeleri yuvarlatılmış görünen basit bir 'kart' konteyneri."""

    def __init__(self, **kwargs):
        super().__init__(orientation="vertical", padding=dp(12), spacing=dp(6),
                          size_hint_y=None, **kwargs)
        self.bind(minimum_height=self.setter("height"))
        with self.canvas.before:
            from kivy.graphics import Color, RoundedRectangle
            Color(*RENK_KART)
            self._arkaplan = RoundedRectangle(radius=[dp(10)])
        self.bind(pos=self._guncelle, size=self._guncelle)

    def _guncelle(self, *args):
        self._arkaplan.pos = self.pos
        self._arkaplan.size = self.size


# ---------------------------------------------------------------------------
# EKRAN: Hisse Analizi
# ---------------------------------------------------------------------------
class AnalizEkrani(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        kok = BoxLayout(orientation="vertical", padding=dp(12), spacing=dp(10))

        arama_satiri = BoxLayout(size_hint_y=None, height=dp(46), spacing=dp(8))
        self.sembol_girisi = TextInput(
            hint_text="Örn: THYAO.IS", multiline=False, size_hint_x=0.7,
            font_size=dp(16),
        )
        buton = Button(text="Analiz Et", size_hint_x=0.3, background_color=RENK_VURGU)
        buton.bind(on_release=self._analiz_baslat)
        arama_satiri.add_widget(self.sembol_girisi)
        arama_satiri.add_widget(buton)
        kok.add_widget(arama_satiri)

        self.durum_etiketi = Label(text="", size_hint_y=None, height=dp(24), color=RENK_METIN)
        kok.add_widget(self.durum_etiketi)

        kaydirma = ScrollView()
        self.sonuc_kutusu = BoxLayout(orientation="vertical", spacing=dp(10),
                                       size_hint_y=None, padding=(0, dp(4)))
        self.sonuc_kutusu.bind(minimum_height=self.sonuc_kutusu.setter("height"))
        kaydirma.add_widget(self.sonuc_kutusu)
        kok.add_widget(kaydirma)

        self.add_widget(kok)

    def _analiz_baslat(self, *args):
        sembol = self.sembol_girisi.text.strip().upper()
        if not sembol:
            uyari_goster("Eksik bilgi", "Lütfen bir hisse kodu gir (örn. THYAO.IS).")
            return
        if not sembol.endswith(".IS") and "." not in sembol:
            sembol += ".IS"

        self.durum_etiketi.text = f"{sembol} analiz ediliyor..."
        self.sonuc_kutusu.clear_widgets()
        threading.Thread(target=self._analiz_yap, args=(sembol,), daemon=True).start()

    def _analiz_yap(self, sembol):
        try:
            sonuc = tam_analiz_et(sembol)
            Clock.schedule_once(lambda dt: self._sonucu_goster(sonuc))
        except Exception as hata:
            Clock.schedule_once(lambda dt: self._hata_goster(str(hata)))

    def _hata_goster(self, mesaj):
        self.durum_etiketi.text = ""
        uyari_goster("Analiz başarısız", f"Veri alınamadı: {mesaj}\n\nİnternet bağlantını kontrol et.")

    def _sonucu_goster(self, sonuc):
        self.durum_etiketi.text = ""
        self.sonuc_kutusu.clear_widgets()

        baslik_kart = KartKutu()
        ad = sonuc.get("sirket_adi") or sonuc["sembol"]
        baslik_kart.add_widget(baslik_etiketi(f"{ad} ({sonuc['sembol']})"))
        baslik_kart.add_widget(govde_etiketi(f"Kapanış: {sonuc['kapanis_fiyati']:.2f} TL"))
        renk = _puana_gore_renk(sonuc["birlesik_puan"])
        baslik_kart.add_widget(govde_etiketi(sonuc["birlesik_genel"], renk=renk))
        self.sonuc_kutusu.add_widget(baslik_kart)

        teknik_kart = KartKutu()
        teknik_kart.add_widget(baslik_etiketi(f"Teknik Analiz (puan: {sonuc['teknik_puan']})", 16))
        for d in sonuc["teknik_detaylar"]:
            teknik_kart.add_widget(govde_etiketi(f"• {d}"))
        self.sonuc_kutusu.add_widget(teknik_kart)

        temel_kart = KartKutu()
        temel_kart.add_widget(baslik_etiketi(f"Temel Analiz (puan: {sonuc['temel_puan']})", 16))
        for d in sonuc["temel_detaylar"]:
            temel_kart.add_widget(govde_etiketi(f"• {d}"))
        self.sonuc_kutusu.add_widget(temel_kart)

        risk_kart = KartKutu()
        risk_kart.add_widget(baslik_etiketi("Stop-Loss Önerisi (ATR bazlı)", 16))
        ekle_btn = Button(text="Hesapla", size_hint_y=None, height=dp(40),
                           background_color=RENK_VURGU)
        risk_kutusu = BoxLayout(orientation="vertical", size_hint_y=None, spacing=dp(4))
        risk_kutusu.bind(minimum_height=risk_kutusu.setter("height"))

        def _risk_hesapla(*_a, sembol=sonuc["sembol"], kutu=risk_kutusu):
            kutu.clear_widgets()
            kutu.add_widget(govde_etiketi("Hesaplanıyor..."))

            def _isle():
                try:
                    r = atr_ile_stop_onerisi(sembol)
                    metin = (
                        f"Güncel fiyat: {r['guncel_fiyat']} TL\n"
                        f"Önerilen giriş: {r['onerilen_giris']} TL\n"
                        f"Önerilen stop: {r['onerilen_stop']} TL\n"
                        f"Stop mesafesi: %{r['stop_mesafesi_yuzde']}"
                    )
                    Clock.schedule_once(lambda dt: (kutu.clear_widgets(), kutu.add_widget(govde_etiketi(metin))))
                except Exception as e:
                    Clock.schedule_once(lambda dt: (kutu.clear_widgets(), kutu.add_widget(govde_etiketi(f"Hata: {e}", renk=RENK_OLUMSUZ))))

            threading.Thread(target=_isle, daemon=True).start()

        ekle_btn.bind(on_release=_risk_hesapla)
        risk_kart.add_widget(ekle_btn)
        risk_kart.add_widget(risk_kutusu)
        self.sonuc_kutusu.add_widget(risk_kart)


# ---------------------------------------------------------------------------
# EKRAN: Tarama
# ---------------------------------------------------------------------------
class TaramaEkrani(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        kok = BoxLayout(orientation="vertical", padding=dp(12), spacing=dp(10))

        kok.add_widget(govde_etiketi(
            "Not: Tam BIST listesi Wikipedia'dan indirilemezse, bilinen "
            f"{len(YEDEK_LISTE)} likit hisseden oluşan yedek liste kullanılır."
        ))

        buton_satiri = BoxLayout(size_hint_y=None, height=dp(46), spacing=dp(8))
        self.baslat_btn = Button(text="Taramayı Başlat", background_color=RENK_VURGU)
        self.baslat_btn.bind(on_release=self._tarama_baslat)
        buton_satiri.add_widget(self.baslat_btn)
        kok.add_widget(buton_satiri)

        self.ilerleme = ProgressBar(max=100, value=0, size_hint_y=None, height=dp(10))
        kok.add_widget(self.ilerleme)
        self.durum_etiketi = Label(text="", size_hint_y=None, height=dp(24), color=RENK_METIN)
        kok.add_widget(self.durum_etiketi)

        kaydirma = ScrollView()
        self.sonuc_kutusu = BoxLayout(orientation="vertical", spacing=dp(6),
                                       size_hint_y=None, padding=(0, dp(4)))
        self.sonuc_kutusu.bind(minimum_height=self.sonuc_kutusu.setter("height"))
        kaydirma.add_widget(self.sonuc_kutusu)
        kok.add_widget(kaydirma)

        self.add_widget(kok)

    def _tarama_baslat(self, *args):
        self.baslat_btn.disabled = True
        self.sonuc_kutusu.clear_widgets()
        self.ilerleme.value = 0
        self.durum_etiketi.text = "Hisse listesi hazırlanıyor..."
        threading.Thread(target=self._tara, daemon=True).start()

    def _ilerleme_callback(self, tamamlanan, toplam, sembol):
        yuzde = (tamamlanan / toplam) * 100 if toplam else 0
        Clock.schedule_once(lambda dt: self._ilerleme_guncelle(yuzde, tamamlanan, toplam, sembol))

    def _ilerleme_guncelle(self, yuzde, tamamlanan, toplam, sembol):
        self.ilerleme.value = yuzde
        self.durum_etiketi.text = f"{tamamlanan}/{toplam} tarandı ({sembol})"

    def _tara(self):
        try:
            liste = tum_bist_kodlarini_getir()
            sonuclar = tum_hisseleri_tara(liste, max_paralel_islem=8,
                                           ilerleme_callback=self._ilerleme_callback)
            olumlu_kriter = [{"alan": "puan", "operator": ">=", "deger": 2}]
            filtrelenmis = kriterlere_gore_filtrele(sonuclar, olumlu_kriter)
            filtrelenmis.sort(key=lambda x: x["puan"], reverse=True)
            Clock.schedule_once(lambda dt: self._sonuclari_goster(filtrelenmis, len(sonuclar)))
        except Exception as hata:
            Clock.schedule_once(lambda dt: uyari_goster("Tarama başarısız", str(hata)))
            Clock.schedule_once(lambda dt: setattr(self.baslat_btn, "disabled", False))

    def _sonuclari_goster(self, filtrelenmis, toplam_taranan):
        self.baslat_btn.disabled = False
        self.durum_etiketi.text = f"{toplam_taranan} hisse tarandı, {len(filtrelenmis)} tanesi olumlu (puan >= 2)."
        self.sonuc_kutusu.clear_widgets()

        if not filtrelenmis:
            self.sonuc_kutusu.add_widget(govde_etiketi("Kritere uyan hisse bulunamadı."))
            return

        for s in filtrelenmis:
            kart = KartKutu()
            renk = _puana_gore_renk(s["puan"])
            kart.add_widget(baslik_etiketi(f"{s['sembol']}  ·  puan {s['puan']}  ·  {s['kapanis_fiyati']:.2f} TL", 15))
            kart.add_widget(govde_etiketi(s["genel_degerlendirme"], renk=renk))
            self.sonuc_kutusu.add_widget(kart)


# ---------------------------------------------------------------------------
# EKRAN: Portföy
# ---------------------------------------------------------------------------
class PortfoyEkrani(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        kok = BoxLayout(orientation="vertical", padding=dp(12), spacing=dp(10))

        ekle_kart = KartKutu()
        ekle_kart.add_widget(baslik_etiketi("Pozisyon Ekle", 16))
        satir1 = BoxLayout(size_hint_y=None, height=dp(42), spacing=dp(6))
        self.sembol_girisi = TextInput(hint_text="THYAO.IS", multiline=False)
        self.adet_girisi = TextInput(hint_text="Adet", multiline=False, input_filter="int")
        self.maliyet_girisi = TextInput(hint_text="Maliyet (TL)", multiline=False, input_filter="float")
        satir1.add_widget(self.sembol_girisi)
        satir1.add_widget(self.adet_girisi)
        satir1.add_widget(self.maliyet_girisi)
        ekle_kart.add_widget(satir1)
        ekle_btn = Button(text="Portföye Ekle", size_hint_y=None, height=dp(42),
                           background_color=RENK_VURGU)
        ekle_btn.bind(on_release=self._pozisyon_ekle)
        ekle_kart.add_widget(ekle_btn)
        kok.add_widget(ekle_kart)

        yenile_btn = Button(text="Portföy Özetini Yenile", size_hint_y=None, height=dp(42),
                             background_color=RENK_VURGU)
        yenile_btn.bind(on_release=self._ozet_yenile)
        kok.add_widget(yenile_btn)

        self.durum_etiketi = Label(text="", size_hint_y=None, height=dp(24), color=RENK_METIN)
        kok.add_widget(self.durum_etiketi)

        kaydirma = ScrollView()
        self.ozet_kutusu = BoxLayout(orientation="vertical", spacing=dp(8),
                                      size_hint_y=None, padding=(0, dp(4)))
        self.ozet_kutusu.bind(minimum_height=self.ozet_kutusu.setter("height"))
        kaydirma.add_widget(self.ozet_kutusu)
        kok.add_widget(kaydirma)

        self.add_widget(kok)

    def _pozisyon_ekle(self, *args):
        sembol = self.sembol_girisi.text.strip().upper()
        adet = self.adet_girisi.text.strip()
        maliyet = self.maliyet_girisi.text.strip()
        if not (sembol and adet and maliyet):
            uyari_goster("Eksik bilgi", "Sembol, adet ve maliyet alanlarını doldur.")
            return
        if not sembol.endswith(".IS") and "." not in sembol:
            sembol += ".IS"
        try:
            pozisyon_ekle(sembol, int(adet), float(maliyet))
            self.sembol_girisi.text = ""
            self.adet_girisi.text = ""
            self.maliyet_girisi.text = ""
            uyari_goster("Eklendi", f"{sembol} portföye eklendi.")
        except Exception as hata:
            uyari_goster("Hata", str(hata))

    def _ozet_yenile(self, *args):
        self.durum_etiketi.text = "Güncel fiyatlar alınıyor..."
        self.ozet_kutusu.clear_widgets()
        threading.Thread(target=self._ozet_getir, daemon=True).start()

    def _ozet_getir(self):
        try:
            ozet = portfoy_ozeti()
            Clock.schedule_once(lambda dt: self._ozeti_goster(ozet))
        except Exception as hata:
            Clock.schedule_once(lambda dt: uyari_goster("Hata", str(hata)))
            Clock.schedule_once(lambda dt: setattr(self.durum_etiketi, "text", ""))

    def _ozeti_goster(self, ozet):
        self.durum_etiketi.text = ""
        self.ozet_kutusu.clear_widgets()

        if ozet.get("mesaj"):
            self.ozet_kutusu.add_widget(govde_etiketi(ozet["mesaj"]))
            return

        genel_kart = KartKutu()
        renk = RENK_OLUMLU if ozet["toplam_kar_zarar"] >= 0 else RENK_OLUMSUZ
        genel_kart.add_widget(baslik_etiketi("Portföy Özeti", 16))
        genel_kart.add_widget(govde_etiketi(f"Toplam değer: {ozet['toplam_deger']:.2f} TL"))
        genel_kart.add_widget(govde_etiketi(
            f"Toplam K/Z: {ozet['toplam_kar_zarar']:.2f} TL (%{ozet['toplam_kar_zarar_yuzde']:.1f})",
            renk=renk,
        ))
        self.ozet_kutusu.add_widget(genel_kart)

        for p in ozet["pozisyonlar"]:
            kart = KartKutu()
            kz_renk = RENK_NOTR
            if p["kar_zarar"] is not None:
                kz_renk = RENK_OLUMLU if p["kar_zarar"] >= 0 else RENK_OLUMSUZ
            kart.add_widget(baslik_etiketi(f"{p['sembol']} · {p['adet']} adet", 15))
            kart.add_widget(govde_etiketi(f"Ort. maliyet: {p['ortalama_maliyet']} TL  ·  Güncel: {p['guncel_fiyat']} TL"))
            if p["kar_zarar"] is not None:
                kart.add_widget(govde_etiketi(f"K/Z: {p['kar_zarar']} TL (%{p['kar_zarar_yuzde']})", renk=kz_renk))
            self.ozet_kutusu.add_widget(kart)


# ---------------------------------------------------------------------------
# EKRAN: Ayarlar
# ---------------------------------------------------------------------------
class AyarlarEkrani(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        kok = BoxLayout(orientation="vertical", padding=dp(16), spacing=dp(12))

        kok.add_widget(baslik_etiketi("Ayarlar", 18))
        kok.add_widget(govde_etiketi(
            "API anahtarları bu cihazda, uygulama verisi klasöründeki "
            "ayarlar.json dosyasında saklanır — APK'nın koduna gömülmez."
        ))

        mevcut = ayarlar.ayarlari_oku()

        kok.add_widget(govde_etiketi("Toplam Sermaye (TL)"))
        self.sermaye_girisi = TextInput(text=str(mevcut["toplam_sermaye"]),
                                         multiline=False, input_filter="float",
                                         size_hint_y=None, height=dp(42))
        kok.add_widget(self.sermaye_girisi)

        kok.add_widget(govde_etiketi("Anthropic API Key (opsiyonel, AI yorumlar için)"))
        self.api_key_girisi = TextInput(text=mevcut["anthropic_api_key"],
                                         multiline=False, password=True,
                                         size_hint_y=None, height=dp(42))
        kok.add_widget(self.api_key_girisi)

        kaydet_btn = Button(text="Kaydet", size_hint_y=None, height=dp(46),
                             background_color=RENK_VURGU)
        kaydet_btn.bind(on_release=self._kaydet)
        kok.add_widget(kaydet_btn)

        self.durum_etiketi = Label(text="", size_hint_y=None, height=dp(24), color=RENK_METIN)
        kok.add_widget(self.durum_etiketi)
        kok.add_widget(BoxLayout())  # boşluk doldurucu

        self.add_widget(kok)

    def _kaydet(self, *args):
        try:
            sermaye = float(self.sermaye_girisi.text or 0)
        except ValueError:
            sermaye = 100000
        ayarlar.ayarlari_kaydet({
            "toplam_sermaye": sermaye,
            "anthropic_api_key": self.api_key_girisi.text.strip(),
        })
        self.durum_etiketi.text = "Kaydedildi."


# ---------------------------------------------------------------------------
# Alt gezinme çubuğu + ana uygulama
# ---------------------------------------------------------------------------
class AltMenu(BoxLayout):
    def __init__(self, sm, **kwargs):
        super().__init__(orientation="horizontal", size_hint_y=None, height=dp(56), **kwargs)
        self.sm = sm
        sekmeler = [
            ("Analiz", "analiz"), ("Tarama", "tarama"),
            ("Portföy", "portfoy"), ("Ayarlar", "ayarlar"),
        ]
        for etiket, ekran_adi in sekmeler:
            btn = Button(text=etiket, background_color=(0.10, 0.12, 0.17, 1),
                         color=RENK_METIN)
            btn.bind(on_release=lambda inst, e=ekran_adi: self._gec(e))
            self.add_widget(btn)

    def _gec(self, ekran_adi):
        self.sm.transition = SlideTransition(duration=0.15)
        self.sm.current = ekran_adi


class AnaLayout(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation="vertical", **kwargs)
        sm = ScreenManager()
        sm.add_widget(AnalizEkrani(name="analiz"))
        sm.add_widget(TaramaEkrani(name="tarama"))
        sm.add_widget(PortfoyEkrani(name="portfoy"))
        sm.add_widget(AyarlarEkrani(name="ayarlar"))

        ust_baslik = Label(text="BIST Analiz Merkezi", font_size=dp(20), bold=True,
                            color=RENK_METIN, size_hint_y=None, height=dp(50))

        self.add_widget(ust_baslik)
        self.add_widget(sm)
        self.add_widget(AltMenu(sm))


class BistAnalizApp(App):
    title = "BIST Analiz Merkezi"

    def build(self):
        return AnaLayout()


if __name__ == "__main__":
    BistAnalizApp().run()
