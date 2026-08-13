import os
import sys
import threading
import traceback

print("CHECKPOINT 1: basic imports done", flush=True)

from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.metrics import dp
from kivy.uix.behaviors import ButtonBehavior
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

print("CHECKPOINT 2: kivy imports done", flush=True)

if platform == "android":
    from android.storage import app_storage_path
    _VERI_DIZINI = app_storage_path()
else:
    _VERI_DIZINI = os.path.join(os.path.expanduser("~"), ".bist_analiz_merkezi")

print("CHECKPOINT 3: storage path resolved: " + str(_VERI_DIZINI), flush=True)

os.makedirs(_VERI_DIZINI, exist_ok=True)
os.chdir(_VERI_DIZINI)

print("CHECKPOINT 4: chdir done", flush=True)

try:
    from veri_katmani import endeks_verisi_getir, doviz_altin_emtia_getir, temel_veri_getir  # noqa: E402
    print("CHECKPOINT 5: veri_katmani imported", flush=True)
    from tarayici import (  # noqa: E402
        tum_hisseleri_tara, en_guclu_20, en_ucuz_20, en_hizli_yukselen_20,
        hacmi_en_cok_artan_20, teknik_en_guclu_20, asiri_satilan_20, asiri_alinan_20,
    )
    print("CHECKPOINT 6: tarayici imported", flush=True)
    import ayarlar  # noqa: E402
    print("CHECKPOINT 7: ayarlar imported", flush=True)
    from test import analiz_et  # noqa: E402
    from hisse_skoru import hisse_skoru_hesapla  # noqa: E402
    from teknik_sinyal_merkezi import teknik_gorunum_uret  # noqa: E402
    from destek_direnc import destek_direnc_bul  # noqa: E402
    from firsat_tarayici import firsatlari_tespit_et  # noqa: E402
    from ai_yorum import hisse_yorumu_uret, AIYorumHatasi  # noqa: E402
    print("CHECKPOINT 7b: detail-screen modules imported", flush=True)
except Exception:
    print("CHECKPOINT FAILED during project imports:", flush=True)
    print(traceback.format_exc(), flush=True)
    sys.stdout.flush()
    raise

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


class TiklanabilirKart(ButtonBehavior, KartKutu):
    """KartKutu ile aynı görünümde ama dokunulabilir (Hisseler listesindeki satırlar için)."""
    pass


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
            mesaj = f"Endeks/döviz verisi alınamadı: {hata}"
            Clock.schedule_once(lambda dt, m=mesaj: self._hata_goster(m))
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
            mesaj = f"Piyasa nabzı taranamadı: {hata}"
            Clock.schedule_once(lambda dt, m=mesaj: self._hata_goster(m))

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


class HisselerEkrani(Screen):
    _SIRALAMA_SECENEKLERI = [
        "Genel Puan", "En Ucuz (F/K)", "En Hızlı Yükselen", "Hacmi En Çok Artan",
        "Teknik En Güçlü", "Aşırı Satılan", "Aşırı Alınan",
    ]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        kok = BoxLayout(orientation="vertical", padding=dp(12), spacing=dp(10))

        ust_satir = BoxLayout(size_hint_y=None, height=dp(46), spacing=dp(8))
        ust_satir.add_widget(baslik_etiketi("Hisseler", 20))
        self.tara_btn = Button(text="Tara", size_hint_x=0.3, background_color=RENK_VURGU)
        self.tara_btn.bind(on_release=self._tarama_baslat)
        ust_satir.add_widget(self.tara_btn)
        kok.add_widget(ust_satir)

        siralama_satiri = BoxLayout(size_hint_y=None, height=dp(42), spacing=dp(8))
        siralama_satiri.add_widget(govde_etiketi("Sırala:"))
        self.siralama_secici = Spinner(
            text="Genel Puan", values=self._SIRALAMA_SECENEKLERI, size_hint_x=0.7,
        )
        self.siralama_secici.bind(text=self._siralama_degisti)
        siralama_satiri.add_widget(self.siralama_secici)
        kok.add_widget(siralama_satiri)

        self.ilerleme = ProgressBar(max=100, value=0, size_hint_y=None, height=dp(8))
        kok.add_widget(self.ilerleme)

        self.durum_etiketi = Label(
            text="Taramak için 'Tara'ya bas (~50 hisse, temel veriler dahil — biraz sürebilir). "
                 "Bir hisseye dokununca detay ekranı açılır.",
            size_hint_y=None, height=dp(50), color=RENK_NOTR,
        )
        self.durum_etiketi.bind(width=lambda i, w: setattr(i, "text_size", (w, None)))
        kok.add_widget(self.durum_etiketi)

        kaydirma = ScrollView()
        self.sonuc_kutusu = BoxLayout(orientation="vertical", spacing=dp(6),
                                       size_hint_y=None, padding=(0, dp(4)))
        self.sonuc_kutusu.bind(minimum_height=self.sonuc_kutusu.setter("height"))
        kaydirma.add_widget(self.sonuc_kutusu)
        kok.add_widget(kaydirma)

        self.add_widget(kok)
        self._son_tarama_sonuclari = []

    def _tarama_baslat(self, *args):
        self.tara_btn.disabled = True
        self.ilerleme.value = 0
        self.durum_etiketi.text = "Hisseler taranıyor..."
        self.sonuc_kutusu.clear_widgets()
        threading.Thread(target=self._tara, daemon=True).start()

    def _ilerleme_callback(self, tamamlanan, toplam, sembol):
        yuzde = (tamamlanan / toplam) * 100 if toplam else 0
        Clock.schedule_once(lambda dt: self._ilerleme_guncelle(yuzde, tamamlanan, toplam, sembol))

    def _ilerleme_guncelle(self, yuzde, tamamlanan, toplam, sembol):
        self.ilerleme.value = yuzde
        self.durum_etiketi.text = f"{tamamlanan}/{toplam} tarandı ({sembol})"

    def _tara(self):
        try:
            sonuclar = tum_hisseleri_tara(
                temel_dahil_et=True, max_paralel_islem=8, ilerleme_callback=self._ilerleme_callback,
            )
            Clock.schedule_once(lambda dt: self._tarama_bitti(sonuclar))
        except Exception as hata:
            mesaj = str(hata)
            Clock.schedule_once(lambda dt, m=mesaj: uyari_goster("Tarama başarısız", m))
            Clock.schedule_once(lambda dt: setattr(self.tara_btn, "disabled", False))

    def _tarama_bitti(self, sonuclar):
        self.tara_btn.disabled = False
        self._son_tarama_sonuclari = sonuclar
        self.durum_etiketi.text = f"{len(sonuclar)} hisse tarandı. Detay için dokun."
        self._listeyi_goster()

    def _siralama_degisti(self, *args):
        if self._son_tarama_sonuclari:
            self._listeyi_goster()

    def _siralanmis_listeyi_getir(self):
        s = self._son_tarama_sonuclari
        secim = self.siralama_secici.text
        eslesme = {
            "Genel Puan": en_guclu_20,
            "En Ucuz (F/K)": en_ucuz_20,
            "En Hızlı Yükselen": en_hizli_yukselen_20,
            "Hacmi En Çok Artan": hacmi_en_cok_artan_20,
            "Teknik En Güçlü": teknik_en_guclu_20,
            "Aşırı Satılan": asiri_satilan_20,
            "Aşırı Alınan": asiri_alinan_20,
        }
        fonksiyon = eslesme.get(secim, en_guclu_20)
        return fonksiyon(s)

    def _listeyi_goster(self):
        self.sonuc_kutusu.clear_widgets()
        liste = self._siralanmis_listeyi_getir()

        if not liste:
            self.sonuc_kutusu.add_widget(govde_etiketi("Sonuç yok."))
            return

        for s in liste:
            kart = TiklanabilirKart()
            kart.bind(on_release=lambda inst, sembol=s["sembol"]: self._hisseye_git(sembol))

            fk = s.get("fk_orani")
            fk_metni = f"F/K {fk:.1f}" if fk is not None else "F/K -"
            degisim = s.get("degisim_yuzde_1g")
            degisim_metni = f"{'+' if (degisim or 0) >= 0 else ''}{degisim:.2f}%" if degisim is not None else "-"
            rsi = s.get("gostergeler", {}).get("RSI")
            rsi_metni = f"{rsi:.1f}" if rsi is not None else "-"
            renk = _puana_gore_renk(s.get("puan"))

            kart.add_widget(baslik_etiketi(
                f"{s['sembol']}  ·  {s['kapanis_fiyati']:.2f} TL  ({degisim_metni})", 15
            ))
            kart.add_widget(govde_etiketi(
                f"Puan: {s.get('puan')}   RSI: {rsi_metni}   {fk_metni}", renk=renk,
            ))
            kart.add_widget(govde_etiketi(s.get("genel_degerlendirme", ""), renk=renk))
            self.sonuc_kutusu.add_widget(kart)

    def _hisseye_git(self, sembol):
        detay_ekrani = self.manager.get_screen("hisse_detay")
        detay_ekrani.hisseyi_yukle(sembol)
        self.manager.transition = SlideTransition(duration=0.15)
        self.manager.current = "hisse_detay"


class HisseDetayEkrani(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        kok = BoxLayout(orientation="vertical", padding=dp(12), spacing=dp(10))

        ust_satir = BoxLayout(size_hint_y=None, height=dp(46), spacing=dp(8))
        self.geri_btn = Button(text="< Geri", size_hint_x=0.3, background_color=(0.10, 0.12, 0.17, 1))
        self.geri_btn.bind(on_release=self._geri_don)
        ust_satir.add_widget(self.geri_btn)
        self.baslik_lbl = baslik_etiketi("Hisse Detay", 18)
        ust_satir.add_widget(self.baslik_lbl)
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
        self.sembol = None
        self.ai_btn = None
        self.ai_sonuc_etiketi = None

    def _geri_don(self, *args):
        self.manager.transition = SlideTransition(duration=0.15)
        self.manager.current = "hisseler"

    def hisseyi_yukle(self, sembol):
        self.sembol = sembol
        self.baslik_lbl.text = sembol
        self.durum_etiketi.text = "Yükleniyor..."
        self.icerik_kutusu.clear_widgets()
        threading.Thread(target=self._veriyi_getir, daemon=True).start()

    def _veriyi_getir(self):
        try:
            veri = analiz_et(self.sembol)
            temel = temel_veri_getir(self.sembol)
            skor = hisse_skoru_hesapla(veri, temel)
            teknik_gorunum = teknik_gorunum_uret(veri.iloc[-1])
            seviyeler = destek_direnc_bul(veri)
            firsatlar = firsatlari_tespit_et(veri)

            paket = {
                "veri": veri, "temel": temel, "skor": skor,
                "teknik_gorunum": teknik_gorunum, "seviyeler": seviyeler,
                "firsatlar": firsatlar,
            }
            Clock.schedule_once(lambda dt: self._goster(paket))
        except Exception as hata:
            mesaj = f"Veri alınamadı: {hata}"
            Clock.schedule_once(lambda dt, m=mesaj: self._hata_goster(m))
    def _goster(self, paket):
        self.durum_etiketi.text = ""
        veri = paket["veri"]
        temel = paket["temel"]
        skor = paket["skor"]
        son = veri.iloc[-1]

        sirket_adi = temel.get("sirket_adi") or self.sembol

        ust_kart = KartKutu()
        ust_kart.add_widget(baslik_etiketi(sirket_adi, 16))
        ust_kart.add_widget(govde_etiketi(f"Kapanış: {son['Close']:.2f} TL"))
        self.icerik_kutusu.add_widget(ust_kart)

        genel_skor = skor.get("genel")
        skor_kart = KartKutu()
        skor_kart.add_widget(baslik_etiketi(
            f"Genel Skor: {genel_skor}/100" if genel_skor is not None else "Genel Skor: -", 16
        ))
        for alan, etiket in [
            ("trend", "Trend"), ("momentum", "Momentum"), ("teknik", "Teknik"),
            ("hacim", "Hacim"), ("temel", "Temel"), ("degerleme", "Değerleme"),
        ]:
            p = skor[alan]["puan"]
            metin = f"{etiket}: {p:.0f}/100" if p is not None else f"{etiket}: veri yok"
            skor_kart.add_widget(govde_etiketi(metin))
        self.icerik_kutusu.add_widget(skor_kart)

        tg = paket["teknik_gorunum"]
        renk = RENK_OLUMLU if tg["puan"] >= 2 else (RENK_OLUMSUZ if tg["puan"] <= -2 else RENK_NOTR)
        sinyal_kart = KartKutu()
        sinyal_kart.add_widget(baslik_etiketi("Teknik Sinyal Merkezi", 16))
        sinyal_kart.add_widget(govde_etiketi(tg["etiket"], renk=renk))
        self.icerik_kutusu.add_widget(sinyal_kart)

        seviyeler = paket["seviyeler"]
        dd_kart = KartKutu()
        dd_kart.add_widget(baslik_etiketi("Destek / Direnç", 16))
        if seviyeler["direncler"]:
            for d in seviyeler["direncler"]:
                dd_kart.add_widget(govde_etiketi(
                    f"Direnç: {d['seviye']} TL  ({'*' * d['guc']})", renk=RENK_OLUMSUZ
                ))
        if seviyeler["destekler"]:
            for d in seviyeler["destekler"]:
                dd_kart.add_widget(govde_etiketi(
                    f"Destek: {d['seviye']} TL  ({'*' * d['guc']})", renk=RENK_OLUMLU
                ))
        if not seviyeler["direncler"] and not seviyeler["destekler"]:
            dd_kart.add_widget(govde_etiketi("Belirgin bir seviye tespit edilemedi."))
        self.icerik_kutusu.add_widget(dd_kart)

        firsatlar = paket["firsatlar"]
        firsat_kart = KartKutu()
        firsat_kart.add_widget(baslik_etiketi("Fırsat Sinyalleri", 16))
        if firsatlar:
            for f in firsatlar:
                firsat_kart.add_widget(govde_etiketi(f"+ {f}", renk=RENK_OLUMLU))
        else:
            firsat_kart.add_widget(govde_etiketi("Belirgin bir fırsat sinyali yok."))
        self.icerik_kutusu.add_widget(firsat_kart)

        ai_kart = KartKutu()
        ai_kart.add_widget(baslik_etiketi("AI Yorum", 16))
        self.ai_sonuc_etiketi = govde_etiketi("Henüz oluşturulmadı.")
        ai_kart.add_widget(self.ai_sonuc_etiketi)
        self.ai_btn = Button(text="AI Yorum Al", size_hint_y=None, height=dp(44), background_color=RENK_VURGU)
        self.ai_btn.bind(on_release=self._ai_yorum_al)
        ai_kart.add_widget(self.ai_btn)
        self.icerik_kutusu.add_widget(ai_kart)

    def _ai_yorum_al(self, *args):
        ayarlar_veri = ayarlar.ayarlari_oku()
        api_key = ayarlar_veri.get("gemini_api_key")
        if not api_key:
            uyari_goster("API anahtarı yok", "Ayarlar ekranından Gemini API anahtarını girmen gerekiyor.")
            return
        self.ai_btn.disabled = True
        self.ai_sonuc_etiketi.text = "AI yorum oluşturuluyor..."
        threading.Thread(target=self._ai_yorum_getir, args=(api_key,), daemon=True).start()

    def _ai_yorum_getir(self, api_key):
        try:
            yorum = hisse_yorumu_uret(self.sembol, api_key)
            Clock.schedule_once(lambda dt: self._ai_yorum_goster(yorum))
        except AIYorumHatasi as hata:
            mesaj = str(hata)
            Clock.schedule_once(lambda dt, m=mesaj: self._ai_yorum_hata(m))
        except Exception as hata:
            mesaj = f"Beklenmeyen hata: {hata}"
            Clock.schedule_once(lambda dt, m=mesaj: self._ai_yorum_hata(m))

    def _metin_ve_yukseklik_guncelle(self, label, yeni_metin):
        """Bir Label'ın metnini değiştirdikten sonra yüksekliğini SENKRON olarak
        yeniden hesaplar — otomatik texture_size bağlantısı uzun/çok satırlı
        metinlerde bazen gecikmeli tetiklenip metni kesilmiş gösterebiliyor.
        Ayrıca iç içe kutuların (kart -> kaydırma alanı) yükseklik zincirinin
        otomatik güncellenmediği durumlar için üst kapsayıcıları elle
        yeniden hizalıyoruz."""
        label.text = yeni_metin
        label.text_size = (label.width, None)
        label.texture_update()
        label.height = label.texture_size[1]

        ust = label.parent
        while ust is not None and hasattr(ust, "do_layout"):
            ust.do_layout()
            ust = ust.parent

    def _ai_yorum_goster(self, yorum):
        self.ai_btn.disabled = False
        self._metin_ve_yukseklik_guncelle(self.ai_sonuc_etiketi, yorum)

    def _ai_yorum_hata(self, mesaj):
        self.ai_btn.disabled = False
        self._metin_ve_yukseklik_guncelle(self.ai_sonuc_etiketi, "Yorum alınamadı.")
        uyari_goster("AI yorum alınamadı", mesaj)
        uyari_goster("AI yorum alınamadı", mesaj)

    def _hata_goster(self, mesaj):
        self.durum_etiketi.text = ""
        uyari_goster("Veri alınamadı", mesaj)


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
        kok.add_widget(BoxLayout())

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


class AltMenu(BoxLayout):
    def __init__(self, sm, **kwargs):
        super().__init__(orientation="horizontal", size_hint_y=None, height=dp(56), **kwargs)
        self.sm = sm
        sekmeler = [("Piyasa", "piyasa"), ("Hisseler", "hisseler"), ("Ayarlar", "ayarlar")]
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
        sm.add_widget(HisselerEkrani(name="hisseler"))
        sm.add_widget(HisseDetayEkrani(name="hisse_detay"))
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
    print("CHECKPOINT 8: entering run()", flush=True)
    try:
        BistAnalizApp().run()
    except Exception:
        print("CHECKPOINT FAILED inside run():", flush=True)
        print(traceback.format_exc(), flush=True)
        sys.stdout.flush()
        raise
    print("CHECKPOINT 9: run() returned normally", flush=True)