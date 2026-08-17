"""
Screener, sıralamalar ve sektör analizinin tarayacağı BIST hisse evreni.
Bu liste, KAP/BIST'in resmi şirket listesinden (kullanıcı tarafından PDF
olarak sağlandı) üretilmiştir; sektör ataması şirket unvanındaki anahtar
kelimelere göre otomatik/sezgisel yapılmıştır — bazı atamalar (özellikle
"Diğer" sektöründekiler veya çok amaçlı holdingler) tam isabetli olmayabilir.
Bir sembol artık geçerli değilse tarama onu sessizce atlar (hata vermez).
"""

BIST_HISSELERI = {
    # Bankacılık
    "ADBNK.IS": "Bankacılık", "AKTIF.IS": "Bankacılık", "ALBRK.IS": "Bankacılık",
    "GARAN.IS": "Bankacılık", "HALKB.IS": "Bankacılık", "ICBCT.IS": "Bankacılık",
    "ISCTR.IS": "Bankacılık", "TSKB.IS": "Bankacılık", "VAKBN.IS": "Bankacılık",
    "YKBNK.IS": "Bankacılık",
    # Cam-Seramik
    "EGSER.IS": "Cam-Seramik", "FORMT.IS": "Cam-Seramik", "KLSER.IS": "Cam-Seramik",
    "KUTPO.IS": "Cam-Seramik", "SERNT.IS": "Cam-Seramik", "SISE.IS": "Cam-Seramik",
    "USAK.IS": "Cam-Seramik",
    # Dayanıklı Tüketim
    "VESBE.IS": "Dayanıklı Tüketim",
    # Demir-Çelik
    "AYES.IS": "Demir-Çelik", "BMSCH.IS": "Demir-Çelik", "BURCE.IS": "Demir-Çelik",
    "CEMTS.IS": "Demir-Çelik", "EREGL.IS": "Demir-Çelik", "ISDMR.IS": "Demir-Çelik",
    "IZMDC.IS": "Demir-Çelik", "KCAER.IS": "Demir-Çelik",
    # Diğer
    "ACSEL.IS": "Diğer", "ADEL.IS": "Diğer", "ADESE.IS": "Diğer", "AKBNK.IS": "Diğer",
    "AKCVR.IS": "Diğer", "ALCAR.IS": "Diğer", "ALVES.IS": "Diğer", "ARCLK.IS": "Diğer",
    "ARTMS.IS": "Diğer", "ARZUM.IS": "Diğer", "AYGAZ.IS": "Diğer", "BIMAS.IS": "Diğer",
    "BLCYT.IS": "Diğer", "BORSK.IS": "Diğer", "BOSSA.IS": "Diğer", "BRKSN.IS": "Diğer",
    "BRLSM.IS": "Diğer", "BRSAN.IS": "Diğer", "BRYAT.IS": "Diğer", "BTCIM.IS": "Diğer",
    "BURVA.IS": "Diğer", "BVSAN.IS": "Diğer", "BYDNR.IS": "Diğer", "CANTE.IS": "Diğer",
    "CELHA.IS": "Diğer", "CEMAS.IS": "Diğer", "CLKMT.IS": "Diğer", "CMSAN.IS": "Diğer",
    "CRFSA.IS": "Diğer", "DESA.IS": "Diğer", "DITAS.IS": "Diğer", "DMSAS.IS": "Diğer",
    "DOKTA.IS": "Diğer", "DYOBY.IS": "Diğer", "EGEEN.IS": "Diğer", "EGPRO.IS": "Diğer",
    "ERBOS.IS": "Diğer", "FBBNK.IS": "Diğer", "FMIZP.IS": "Diğer", "GENTS.IS": "Diğer",
    "GEREL.IS": "Diğer", "HEKTS.IS": "Diğer", "JANTS.IS": "Diğer", "KARTN.IS": "Diğer",
    "KATMR.IS": "Diğer", "KLKIM.IS": "Diğer", "KLMSN.IS": "Diğer", "KUYAS.IS": "Diğer",
    "LUKSK.IS": "Diğer", "MGROS.IS": "Diğer", "NTGAZ.IS": "Diğer", "ORMA.IS": "Diğer",
    "OSTIM.IS": "Diğer", "OYLUM.IS": "Diğer", "QUAGR.IS": "Diğer", "RGYAS.IS": "Diğer",
    "SAFKR.IS": "Diğer", "SANKO.IS": "Diğer", "SARKY.IS": "Diğer", "SASA.IS": "Diğer",
    "SKBNK.IS": "Diğer", "TIMUR.IS": "Diğer", "TKNSA.IS": "Diğer", "TV8TV.IS": "Diğer",
    "YATAS.IS": "Diğer",
    # Enerji
    "A1YEN.IS": "Enerji", "AHGAZ.IS": "Enerji", "AKENR.IS": "Enerji", "AKFYE.IS": "Enerji",
    "AKSEN.IS": "Enerji", "AKSUE.IS": "Enerji", "ALFAS.IS": "Enerji", "ARFYE.IS": "Enerji",
    "ASTOR.IS": "Enerji", "AYDEM.IS": "Enerji", "AYEN.IS": "Enerji", "BIOEN.IS": "Enerji",
    "CATES.IS": "Enerji", "CONSE.IS": "Enerji", "CWENE.IS": "Enerji", "ENJSA.IS": "Enerji",
    "EUPWR.IS": "Enerji", "GWIND.IS": "Enerji", "IZENR.IS": "Enerji", "KONTR.IS": "Enerji",
    "MAGEN.IS": "Enerji", "NATEN.IS": "Enerji", "ODAS.IS": "Enerji", "ORGE.IS": "Enerji",
    "SMRTG.IS": "Enerji", "TATEN.IS": "Enerji", "YEOTK.IS": "Enerji", "ZOREN.IS": "Enerji",
    # Finans
    "A1CAP.IS": "Finans", "ADLVY.IS": "Finans", "AKDFA.IS": "Finans", "AKFK.IS": "Finans",
    "AKMEN.IS": "Finans", "AKSFA.IS": "Finans", "AKTVK.IS": "Finans", "ALJF.IS": "Finans",
    "ALNUS.IS": "Finans", "ARSVY.IS": "Finans", "ATAVK.IS": "Finans", "ATAYM.IS": "Finans",
    "ATLAS.IS": "Finans", "ATLFA.IS": "Finans", "BLSMD.IS": "Finans", "BRKT.IS": "Finans",
    "BRKVY.IS": "Finans", "BULGS.IS": "Finans", "CAGFA.IS": "Finans", "EUKYO.IS": "Finans",
    "GARFA.IS": "Finans", "GEDIK.IS": "Finans", "GOZDE.IS": "Finans", "HUBVC.IS": "Finans",
    "INFO.IS": "Finans", "ISFAK.IS": "Finans", "ISGSY.IS": "Finans", "ISMEN.IS": "Finans",
    "ISYAT.IS": "Finans", "LIDFA.IS": "Finans", "MDASM.IS": "Finans", "MTRYO.IS": "Finans",
    "OYAYO.IS": "Finans", "QNBFF.IS": "Finans", "SEKFK.IS": "Finans", "SKYMD.IS": "Finans",
    "TCRYT.IS": "Finans", "TERA.IS": "Finans", "ULUFA.IS": "Finans", "YKFKT.IS": "Finans",
    # GYO
    "AAGYO.IS": "GYO", "ADGYO.IS": "GYO", "AGYO.IS": "GYO", "AHSGY.IS": "GYO",
    "AKFGY.IS": "GYO", "AKMGY.IS": "GYO", "AKSGY.IS": "GYO", "ALGYO.IS": "GYO",
    "ASGYO.IS": "GYO", "ATAGY.IS": "GYO", "AVGYO.IS": "GYO", "AVPGY.IS": "GYO",
    "BASGZ.IS": "GYO", "BEGYO.IS": "GYO", "DGGYO.IS": "GYO", "DZGYO.IS": "GYO",
    "EKGYO.IS": "GYO", "HLGYO.IS": "GYO", "ISGYO.IS": "GYO", "KGYO.IS": "GYO",
    "KLGYO.IS": "GYO", "KRGYO.IS": "GYO", "MHRGY.IS": "GYO", "MRGYO.IS": "GYO",
    "MSGYO.IS": "GYO", "NUGYO.IS": "GYO", "OZGYO.IS": "GYO", "OZKGY.IS": "GYO",
    "PAGYO.IS": "GYO", "PEKGY.IS": "GYO", "RYGYO.IS": "GYO", "SEGYO.IS": "GYO",
    "SNGYO.IS": "GYO", "SRVGY.IS": "GYO", "SURGY.IS": "GYO", "TRGYO.IS": "GYO",
    "TSGYO.IS": "GYO", "VKGYO.IS": "GYO",
    # Gıda
    "AEFES.IS": "Gıda", "AKHAN.IS": "Gıda", "ALKLC.IS": "Gıda", "ARMGD.IS": "Gıda",
    "ATAKP.IS": "Gıda", "AVOD.IS": "Gıda", "BALSU.IS": "Gıda", "BANVT.IS": "Gıda",
    "BESLR.IS": "Gıda", "CCOLA.IS": "Gıda", "DARDL.IS": "Gıda", "DIMES.IS": "Gıda",
    "ERSU.IS": "Gıda", "ETILR.IS": "Gıda", "FRIGO.IS": "Gıda", "KAYSE.IS": "Gıda",
    "KENT.IS": "Gıda", "KRSTL.IS": "Gıda", "KRVGD.IS": "Gıda", "KTSKR.IS": "Gıda",
    "MERKO.IS": "Gıda", "MOPAS.IS": "Gıda", "PENGD.IS": "Gıda", "PETUN.IS": "Gıda",
    "PINSU.IS": "Gıda", "PNSUT.IS": "Gıda", "TABGD.IS": "Gıda", "TATGD.IS": "Gıda",
    "TBORG.IS": "Gıda", "TUKAS.IS": "Gıda", "ULKER.IS": "Gıda", "YYLGD.IS": "Gıda",
    # Havacılık
    "CLEBI.IS": "Havacılık", "PGSUS.IS": "Havacılık", "TAVHL.IS": "Havacılık",
    "THYAO.IS": "Havacılık",
    # Holding
    "AGHOL.IS": "Holding", "AKYHO.IS": "Holding", "ALARK.IS": "Holding",
    "ARSAN.IS": "Holding", "ATSYH.IS": "Holding", "AVHOL.IS": "Holding", "BERA.IS": "Holding",
    "COSMO.IS": "Holding", "DENGE.IS": "Holding", "DEVA.IS": "Holding", "DOHOL.IS": "Holding",
    "EUHOL.IS": "Holding", "GLRYH.IS": "Holding", "GLYHO.IS": "Holding",
    "GSDHO.IS": "Holding", "HEDEF.IS": "Holding", "ISBIR.IS": "Holding",
    "IZINV.IS": "Holding", "KCHOL.IS": "Holding", "KLRHO.IS": "Holding",
    "MARKA.IS": "Holding", "METRO.IS": "Holding", "NTHOL.IS": "Holding",
    "POLHO.IS": "Holding", "SAHOL.IS": "Holding", "TKFEN.IS": "Holding",
    "TRCAS.IS": "Holding", "TRHOL.IS": "Holding", "UNLU.IS": "Holding", "VERUS.IS": "Holding",
    "YESIL.IS": "Holding",
    # Kimya
    "AKSA.IS": "Kimya", "ALKIM.IS": "Kimya", "AVTUR.IS": "Kimya", "BAGFS.IS": "Kimya",
    "EGGUB.IS": "Kimya", "GUBRF.IS": "Kimya", "MEPET.IS": "Kimya", "MRSHL.IS": "Kimya",
    "PETKM.IS": "Kimya", "TUPRS.IS": "Kimya",
    # Kâğıt-Ambalaj
    "ALKA.IS": "Kâğıt-Ambalaj", "BAKAB.IS": "Kâğıt-Ambalaj", "BNTAS.IS": "Kâğıt-Ambalaj",
    "DURDO.IS": "Kâğıt-Ambalaj", "HURGZ.IS": "Kâğıt-Ambalaj", "KRPLS.IS": "Kâğıt-Ambalaj",
    "PRZMA.IS": "Kâğıt-Ambalaj", "VKING.IS": "Kâğıt-Ambalaj",
    # Lojistik
    "HOROZ.IS": "Lojistik", "RYSAS.IS": "Lojistik",
    # Madencilik
    "ATATR.IS": "Madencilik", "CVKMD.IS": "Madencilik", "PRKME.IS": "Madencilik",
    # Makine
    "MAKTK.IS": "Makine", "MEKAG.IS": "Makine", "PARSN.IS": "Makine",
    # Metal
    "BMSTL.IS": "Metal", "CUSAN.IS": "Metal",
    # Mobilya
    "KLSYN.IS": "Mobilya", "YONGA.IS": "Mobilya",
    # Otomotiv
    "ASUZU.IS": "Otomotiv", "BEYAZ.IS": "Otomotiv", "BFREN.IS": "Otomotiv",
    "BRISA.IS": "Otomotiv", "DOAS.IS": "Otomotiv", "EPLAS.IS": "Otomotiv",
    "ESCAR.IS": "Otomotiv", "FROTO.IS": "Otomotiv", "GOODY.IS": "Otomotiv",
    "KARSN.IS": "Otomotiv", "OTKAR.IS": "Otomotiv", "PKART.IS": "Otomotiv",
    "TMSN.IS": "Otomotiv", "TOASO.IS": "Otomotiv", "TTRAK.IS": "Otomotiv",
    # Perakende
    "BIZIM.IS": "Perakende", "EBEBK.IS": "Perakende", "SOKM.IS": "Perakende",
    # Sağlık
    "ECILC.IS": "Sağlık", "ECZYT.IS": "Sağlık", "GENIL.IS": "Sağlık", "LKMNH.IS": "Sağlık",
    "MEDTR.IS": "Sağlık", "MPARK.IS": "Sağlık", "SELEC.IS": "Sağlık",
    # Sigorta
    "AGESA.IS": "Sigorta", "AKGRT.IS": "Sigorta", "ANHYT.IS": "Sigorta",
    "ANSGR.IS": "Sigorta", "RAYSG.IS": "Sigorta", "TURSG.IS": "Sigorta",
    # Spor
    "BJKAS.IS": "Spor", "FENER.IS": "Spor", "GSRAY.IS": "Spor", "TSPOR.IS": "Spor",
    # Teknoloji
    "AGROT.IS": "Teknoloji", "ALTNY.IS": "Teknoloji", "ANGEN.IS": "Teknoloji",
    "ARDYZ.IS": "Teknoloji", "ARENA.IS": "Teknoloji", "ASELS.IS": "Teknoloji",
    "ATATP.IS": "Teknoloji", "AZTEK.IS": "Teknoloji", "BLKOM.IS": "Teknoloji",
    "DESPC.IS": "Teknoloji", "DGATE.IS": "Teknoloji", "FONET.IS": "Teknoloji",
    "HTTBT.IS": "Teknoloji", "INDES.IS": "Teknoloji", "KLYPV.IS": "Teknoloji",
    "KRONT.IS": "Teknoloji", "LOGO.IS": "Teknoloji", "MTRKS.IS": "Teknoloji",
    "PENTA.IS": "Teknoloji", "REEDR.IS": "Teknoloji", "SDTTR.IS": "Teknoloji",
    "SMART.IS": "Teknoloji", "VESTL.IS": "Teknoloji",
    # Tekstil
    "ATEKS.IS": "Tekstil", "BRKO.IS": "Tekstil", "BRMEN.IS": "Tekstil", "DAGI.IS": "Tekstil",
    "DERIM.IS": "Tekstil", "HATEK.IS": "Tekstil", "KORDS.IS": "Tekstil",
    "KOTON.IS": "Tekstil", "MAVI.IS": "Tekstil", "MNDRS.IS": "Tekstil", "SKTAS.IS": "Tekstil",
    "SUNTK.IS": "Tekstil", "SUWEN.IS": "Tekstil", "VAKKO.IS": "Tekstil",
    "YUNSA.IS": "Tekstil",
    # Telekom
    "ALCTL.IS": "Telekom", "MOBTL.IS": "Telekom", "NETAS.IS": "Telekom",
    "TCELL.IS": "Telekom", "TTKOM.IS": "Telekom",
    # Turizm
    "AYCES.IS": "Turizm", "KSTUR.IS": "Turizm", "MAALT.IS": "Turizm", "MARTI.IS": "Turizm",
    "MERIT.IS": "Turizm",
    # Çimento
    "AFYON.IS": "Çimento", "AKCNS.IS": "Çimento", "BASCM.IS": "Çimento",
    "BSOKE.IS": "Çimento", "BUCIM.IS": "Çimento", "CIMSA.IS": "Çimento",
    "CMENT.IS": "Çimento", "GOLTS.IS": "Çimento", "KONYA.IS": "Çimento",
    "NUHCM.IS": "Çimento", "OYAKC.IS": "Çimento",
    # İnşaat
    "AKFIS.IS": "İnşaat", "ALBTN.IS": "İnşaat", "ANELE.IS": "İnşaat", "BIENY.IS": "İnşaat",
    "BOBET.IS": "İnşaat", "ENKAI.IS": "İnşaat", "GESAN.IS": "İnşaat", "GSDDE.IS": "İnşaat",
    "INTEM.IS": "İnşaat", "TEKTU.IS": "İnşaat", "ULUSE.IS": "İnşaat", "YYAPI.IS": "İnşaat",
}


def hisse_listesi():
    """Tüm BIST sembollerinin düz, tekrarsız listesi (screener taraması için)."""
    return list(BIST_HISSELERI.keys())


def sektor_getir(sembol):
    """Bir sembolün sektörünü döner, tanımlı değilse None döner."""
    return BIST_HISSELERI.get(sembol)


def sektorler_listesi():
    """Tanımlı tüm sektörlerin tekrarsız listesi."""
    return sorted(set(BIST_HISSELERI.values()))
