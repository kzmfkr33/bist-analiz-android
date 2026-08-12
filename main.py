"""
BIST Analiz Merkezi - Android (Kivy) sürümü.

Ağ çağrıları (fiyat verisi çekme, tarama) UI'yi kilitlememesi için
arka plan thread'lerinde çalışır, sonuçlar Clock.schedule_once ile
ana thread'e (UI thread) geri taşınır.
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
from kivy.uix.screenmanager import Screen, ScreenManager, SlideTransition
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput
from kivy.utils import platform

# ---------------------------------------------------------------------------
# Uygulama verilerinin (JSON/log dosyaları) yazılacağı klasörü, içe
# aktarmalardan ÖNCE ayarlıyoruz — ayarlar.py, log_ayarlari.py, alarm_sistemi.py,
# watchlist.py, strateji_olusturucu.py gibi modüller dosyaları geçerli
# çalışma dizinine göre (göreli yol) açıyor.
# ---------------------------------------------------------------------------
if platform == "android":
    from android.storage import app_storage_path
    _VERI_DIZINI = app_storage_path()
else:
    _VERI_DIZINI = os.path.join(os.path.expanduser("~"), ".bist_analiz_merkezi")

os.makedirs(_VERI_DIZINI, exist_ok=True)
os.chdir(_VERI_DIZINI)

from veri_katmani import endeks_verisi_getir, doviz_altin_emtia_getir  # noqa: E402
from tarayici import tum_hisseleri_tara                                # noqa: E402
import ayarlar                                                         # noqa: E402

RENK_ARKAPLAN = (0.07, 0.09, 0.13, 1)
RENK_KART = (0.12, 0.15, 0.20, 1)
RENK_OLUMLU = (0.20, 0.75, 0.45, 1)
RENK_OLUMSUZ = (0.85, 0.30, 0.30, 1)
RENK_NOTR = (0.85, 0.70, 0.20, 1)
RENK_METIN = (0.92, 0.94, 0.96, 1)
RENK_VURGU = (0.20, 0.55, 0.95, 1)

Window.clearcolor = RENK_ARKAPLAN


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
# EKRAN: Piyasa (Ana Ekran) — plan madde 1
# ---------------------------------------------------------------------------
class PiyasaEkrani(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        kok = BoxLayout(orientation="vertical", padding=dp(12), spacing=dp(10))

        ust_satir = BoxLayout(size_hint_y=None, height=dp(46), spacing=dp(8))
        ust_satir.add_widget(baslik_etiketi("Piyasa", 20))
        self.yenile_btn = Button(text="Yenile", size_hint_x=0.35, background_color=RENK_VURGU)
        self.yenile_btn.bind(on_release=self._yenile)
        ust_satir.add_widget(self.yenile_btn)
        kok.add_widget(ust_satir)

        self.durum_etiketi = Label(text="", size_hint_y=None, height=dp(22), color=RENK_NOTR)
        kok.add_widget(self.durum_etiketi)

        kaydirma = ScrollView()
        self.icerik_kutusu = BoxLayout(orientation="vertical", spacing=dp(10),
                                        size_hint_y=None, padding=(0, dp(4)))
        self.icerik_kutusu.bind(minimum_height=self.icerik_kutusu.setter("height"))
        kaydirma.add_widget(self.icerik_kutusu)
        kok.add_widget(kaydirma)

        self.add_widget(kok)
        self._ilk_yukleme_yapildi = False

    def on_enter(self, *args):
        if not self._ilk_yukleme_yapildi:
            self._ilk_yukleme_yapildi = True
            self._yenile()

    def _yenile(self, *args):
        self.yenile_btn.disabled = True
        self.durum_etiketi.text = "Piyasa verisi yükleniyor..."
        self.icerik_kutusu.clear_widgets()
        threading.Thread(target=self._veriyi_getir, daemon=True).start()

    def _veriyi_getir(self):
        try:
            endeksler = endeks_verisi_getir()
            emtialar = doviz_altin_emtia_getir()
            Clock.schedule_once(lambda dt: self._ust_kartlari_goster(endeksler, emtialar))
        except Exception as hata:
            Clock.schedule_once(lambda dt: self._hata_goster(f"Endeks/döviz verisi alınamadı: {hata}"))
            return

        self._nabiz_taramasi_yap()

    def _ust_kartlari_goster(self, endeksler, emtialar):
        self.durum_etiketi.text = "Piyasa nabzı taranıyor (BIST evreni)..."

        endeks_kart = KartKutu()
        endeks_kart.add_widget(baslik_etiketi("Endeksler", 16))
        izgara = GridLayout(cols=2, size_hint_y=None, spacing=dp(6))
        izgara.bind(minimum_height=izgara.setter("height"))
        for isim, df in endeksler.items():
            metin, renk = self._degisim_metni(df)
            izgara.add_widget(govde_etiketi(f"{isim}\n{metin}", renk=renk))
        endeks_kart.add_widget(izgara)
        self.icerik_kutusu.add_widget(endeks_kart)

        emtia_kart = KartKutu()
        emtia_kart.add_widget(baslik_etiketi("Döviz / Emtia", 16))
        izgara2 = GridLayout(cols=2, size_hint_y=None, spacing=dp(6))
        izgara2.bind(minimum_height=izgara2.setter("height"))
        for isim, df in emtialar.items():
            metin, renk = self._degisim_metni(df)
            izgara2.add_widget(govde_etiketi(f"{isim}\n{metin}", renk=renk))
        emtia_kart.add_widget(izgara2)
        self.icerik_kutusu.add_widget(emtia_kart)

    def _degisim_metni(self, df):
        if df is None or len(df) < 2:
            return "veri yok", RENK_NOTR
        son = float(df["Close"].iloc[-1])
        onceki = float(df["Close"].iloc[-2])
        degisim = 100 * (son - onceki) / onceki
        isaret = "+" if degisim >= 0 else ""
        renk = RENK_OLUMLU if degisim >= 0 else RENK_OLUMSUZ
        return f"{son:.2f}  ({isaret}{degisim:.2f}%)", renk

    def _nabiz_taramasi_yap(self):
        try:
            sonuclar = tum_hisseleri_tara(temel_dahil_et=False, max_paralel_islem=10)
            Clock.schedule_once(lambda dt: self._nabzi_goster(sonuclar))
        except Exception as hata:
            Clock.schedule_once(lambda dt: self._hata_goster(f"Piyasa nabzı taranamadı: {hata}"))

    def _nabzi_goster(self, sonuclar):
        self.yenile_btn.disabled = False
        self.durum_etiketi.text = f"{len(sonuclar)} hisse tarandı."

        yukselen = [s for s in sonuclar if (s.get("degisim_yuzde_1g") or 0) > 0]
        dusen = [s for s in sonuclar if (s.get("degisim_yuzde_1g") or 0) < 0]
        yatay = [s for s in sonuclar if (s.get("degisim_yuzde_1g") or 0) == 0]

        sayim_kart = KartKutu()
        sayim_kart.add_widget(baslik_etiketi("Piyasa Nabzı", 16))
        sayim_kart.add_widget(govde_etiketi(
            f"Yükselen: {len(yukselen)}   Düşen: {len(dusen)}   Yatay: {len(yatay)}"
        ))
        yeni_zirve = [s for s in sonuclar if s.get("periyot_zirvesi_mi")]
        yeni_dip = [s for s in sonuclar if s.get("periyot_dibi_mi")]
        sayim_kart.add_widget(govde_etiketi(
            f"Yeni zirve yapan: {len(yeni_zirve)}   Yeni dip yapan: {len(yeni_dip)}"
        ))
        self.icerik_kutusu.add_widget(sayim_kart)

        en_cok_yukselen = sorted(yukselen, key=lambda s: s["degisim_yuzde_1g"], reverse=True)[:5]
        en_cok_dusen = sorted(dusen, key=lambda s: s["degisim_yuzde_1g"])[:5]
        en_yuksek_hacimli = sorted(
            [s for s in sonuclar if s.get("gostergeler", {}).get("RVOL") is not None],
            key=lambda s: s["gostergeler"]["RVOL"], reverse=True
        )[:5]

        self.icerik_kutusu.add_widget(
            self._liste_karti("En Çok Yükselenler", en_cok_yukselen, "degisim_yuzde_1g", "%")
        )
        self.icerik_kutusu.add_widget(
            self._liste_karti("En Çok Düşenler", en_cok_dusen, "degisim_yuzde_1g", "%")
        )
        self.icerik_kutusu.add_widget(
            self._liste_karti("Hacmi En Çok Artanlar (RVOL)", en_yuksek_hacimli, None, "x", ozel_alan="RVOL")
        )

    def _liste_karti(self, baslik, hisseler, alan, birim, ozel_alan=None):
        kart = KartKutu()
        kart.add_widget(baslik_etiketi(baslik, 16))
        if not hisseler:
            kart.add_widget(govde_etiketi("Veri yok."))
            return kart
        for s in hisseler:
            if ozel_alan:
                deger = s.get("gostergeler", {}).get(ozel_alan)
                metin = f"{s['sembol']}: {deger:.2f}{birim}" if deger is not None else f"{s['sembol']}: -"
            else:
                deger = s.get(alan)
                isaret = "+" if (deger or 0) >= 0 else ""
                metin = f"{s['sembol']}: {isaret}{deger:.2f}{birim}" if deger is not None else f"{s['sembol']}: -"
            renk = RENK_OLUMLU if (deger or 0) >= 0 else RENK_OLUMSUZ
            kart.add_widget(govde_etiketi(metin, renk=renk))
        return kart

    def _hata_goster(self, mesaj):
        self.yenile_btn.disabled = False
        self.durum_etiketi.text = ""
        uyari_goster("Veri alınamadı", mesaj)


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

        kok.add_widget(govde_etiketi("Google Gemini API Key (opsiyonel, AI yorumlar için)"))
        kok.add_widget(govde_etiketi(
            "Ücretsiz anahtar: aistudio.google.com/app/apikey", renk=RENK_NOTR
        ))
        self.api_key_girisi = TextInput(text=mevcut["gemini_api_key"],
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
            "gemini_api_key": self.api_key_girisi.text.strip(),
        })
        self.durum_etiketi.text = "Kaydedildi."


# ---------------------------------------------------------------------------
# Alt gezinme çubuğu + ana uygulama
# ---------------------------------------------------------------------------
class AltMenu(BoxLayout):
    def __init__(self, sm, **kwargs):
        super().__init__(orientation="horizontal", size_hint_y=None, height=dp(56), **kwargs)
        self.sm = sm
        # Not: sıradaki adımlarda buraya Hisseler, Watchlist, Strateji gibi
        # sekmeler eklenecek — şimdilik iskelet + Piyasa ekranı hazır.
        sekmeler = [("Piyasa", "piyasa"), ("Ayarlar", "ayarlar")]
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
        sm.add_widget(PiyasaEkrani(name="piyasa"))
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