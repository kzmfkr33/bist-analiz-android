"""
Screener, sıralamalar ve sektör analizinin tarayacağı BIST hisse evreni.
Bu liste elle derlenmiştir (canlı bir kaynaktan otomatik çekilmez) — bu
yüzden zamanla borsadan çıkan/yeni eklenen hisselerle güncel tutulması
gerekebilir. Bir sembol artık geçerli değilse, tarama onu sessizce atlar
(hata vermez), sadece sonuç listesinde görünmez.
"""

BIST_HISSELERI = {
    # Bankacılık
    "AKBNK.IS": "Bankacılık", "GARAN.IS": "Bankacılık", "ISCTR.IS": "Bankacılık",
    "YKBNK.IS": "Bankacılık", "VAKBN.IS": "Bankacılık", "HALKB.IS": "Bankacılık",
    "SKBNK.IS": "Bankacılık", "TSKB.IS": "Bankacılık", "ICBCT.IS": "Bankacılık",
    "QNBFB.IS": "Bankacılık", "ALBRK.IS": "Bankacılık",

    # Holding
    "KCHOL.IS": "Holding", "SAHOL.IS": "Holding", "SISE.IS": "Holding",
    "DOAS.IS": "Holding", "ALARK.IS": "Holding", "AGHOL.IS": "Holding",
    "TAVHL.IS": "Holding", "ENKAI.IS": "Holding", "GLYHO.IS": "Holding",
    "GSDHO.IS": "Holding", "DOHOL.IS": "Holding", "KOZAA.IS": "Holding",
    "NTHOL.IS": "Holding", "POLHO.IS": "Holding", "VERUS.IS": "Holding",
    "YAZIC.IS": "Holding", "ALCAR.IS": "Holding", "AKFYE.IS": "Holding",

    # Demir-Çelik / Metal
    "EREGL.IS": "Demir-Çelik", "KRDMD.IS": "Demir-Çelik", "KRDMA.IS": "Demir-Çelik",
    "KRDMB.IS": "Demir-Çelik", "ISDMR.IS": "Demir-Çelik", "CEMTS.IS": "Demir-Çelik",
    "BURCE.IS": "Demir-Çelik", "SARKY.IS": "Metal", "CELHA.IS": "Metal",
    "IZMDC.IS": "Metal", "SAFKR.IS": "Metal",

    # Otomotiv
    "TOASO.IS": "Otomotiv", "FROTO.IS": "Otomotiv", "TTRAK.IS": "Otomotiv",
    "OTKAR.IS": "Otomotiv", "KARSN.IS": "Otomotiv", "ASUZU.IS": "Otomotiv",
    "TMSN.IS": "Otomotiv", "BFREN.IS": "Otomotiv", "FMIZP.IS": "Otomotiv",
    "PARSN.IS": "Otomotiv", "EGEEN.IS": "Otomotiv", "DITAS.IS": "Otomotiv",

    # Savunma
    "ASELS.IS": "Savunma", "OTKAR.IS": "Savunma",

    # Petrokimya / Enerji Üretimi
    "TUPRS.IS": "Petrokimya", "PETKM.IS": "Petrokimya", "AYGAZ.IS": "Petrokimya",
    "GUBRF.IS": "Kimya", "SODA.IS": "Kimya", "BAGFS.IS": "Kimya",
    "HEKTS.IS": "Kimya", "ALKIM.IS": "Kimya", "EGGUB.IS": "Kimya",

    # GYO (Gayrimenkul Yatırım Ortaklığı)
    "EKGYO.IS": "GYO", "ISGYO.IS": "GYO", "TRGYO.IS": "GYO", "SNGYO.IS": "GYO",
    "HLGYO.IS": "GYO", "AKFGY.IS": "GYO", "AGYO.IS": "GYO", "VKGYO.IS": "GYO",
    "OZKGY.IS": "GYO", "PEGYO.IS": "GYO", "KLGYO.IS": "GYO", "RYGYO.IS": "GYO",

    # Madencilik
    "KOZAL.IS": "Madencilik", "KOZAA.IS": "Madencilik", "IPEKE.IS": "Madencilik",
    "PRKME.IS": "Madencilik",

    # Perakende
    "BIMAS.IS": "Perakende", "MGROS.IS": "Perakende", "SOKM.IS": "Perakende",
    "BIZIM.IS": "Perakende", "VAKKO.IS": "Perakende", "MAVI.IS": "Perakende",

    # Gıda / İçecek
    "ULKER.IS": "Gıda", "CCOLA.IS": "Gıda", "AEFES.IS": "Gıda", "TATGD.IS": "Gıda",
    "PNSUT.IS": "Gıda", "BANVT.IS": "Gıda", "KENT.IS": "Gıda", "OYLUM.IS": "Gıda",
    "FRIGO.IS": "Gıda", "KRVGD.IS": "Gıda", "SELGD.IS": "Gıda",

    # Havacılık / Ulaştırma
    "THYAO.IS": "Havacılık", "PGSUS.IS": "Havacılık", "CLEBI.IS": "Ulaştırma",
    "RYSAS.IS": "Ulaştırma", "GESAN.IS": "Ulaştırma",

    # Telekom
    "TCELL.IS": "Telekom", "TTKOM.IS": "Telekom",

    # Teknoloji / Yazılım
    "LOGO.IS": "Teknoloji", "NETAS.IS": "Teknoloji", "KAREL.IS": "Teknoloji",
    "ARDYZ.IS": "Teknoloji", "LINK.IS": "Teknoloji", "SMART.IS": "Teknoloji",
    "ALCTL.IS": "Teknoloji", "INDES.IS": "Teknoloji", "DESPC.IS": "Teknoloji",
    "PENTA.IS": "Teknoloji", "FONET.IS": "Teknoloji",

    # Sanayi (genel)
    "ASTOR.IS": "Sanayi", "ARCLK.IS": "Dayanıklı Tüketim", "VESTL.IS": "Dayanıklı Tüketim",
    "VESBE.IS": "Dayanıklı Tüketim", "BSHEV.IS": "Dayanıklı Tüketim",

    # Sigorta
    "TURSG.IS": "Sigorta", "ANSGR.IS": "Sigorta", "AGESA.IS": "Sigorta",
    "ANHYT.IS": "Sigorta", "RAYSG.IS": "Sigorta",

    # Enerji / Elektrik
    "AKSEN.IS": "Enerji", "AKSA.IS": "Enerji", "ENJSA.IS": "Enerji",
    "ZOREN.IS": "Enerji", "ODAS.IS": "Enerji", "AYEN.IS": "Enerji",
    "AKFYE.IS": "Enerji", "AKENR.IS": "Enerji", "CANTE.IS": "Enerji",
    "NATEN.IS": "Enerji", "MAGEN.IS": "Enerji", "BIOEN.IS": "Enerji",

    # Çimento
    "CIMSA.IS": "Çimento", "OYAKC.IS": "Çimento", "AKCNS.IS": "Çimento",
    "KONYA.IS": "Çimento", "BTCIM.IS": "Çimento", "GOLTS.IS": "Çimento",
    "NUHCM.IS": "Çimento", "CMENT.IS": "Çimento", "ADANA.IS": "Çimento",

    # Tekstil / Deri
    "KORDS.IS": "Tekstil", "YUNSA.IS": "Tekstil", "SKTAS.IS": "Tekstil",
    "DERIM.IS": "Tekstil", "BRKO.IS": "Tekstil", "MNDRS.IS": "Tekstil",

    # Kâğıt / Ambalaj
    "OZKGY.IS": "Kâğıt", "MEPET.IS": "Kâğıt", "DGGYO.IS": "Kâğıt",
    "SASA.IS": "Kimya", "AKPLP.IS": "Ambalaj",

    # Sağlık / İlaç
    "DEVA.IS": "Sağlık", "SELEC.IS": "Sağlık", "ECILC.IS": "Sağlık",
    "MPARK.IS": "Sağlık", "LKMNH.IS": "Sağlık",

    # İnşaat / Taahhüt
    "ENKAI.IS": "İnşaat", "TKFEN.IS": "İnşaat", "YYAPI.IS": "İnşaat",
    "OZGYO.IS": "İnşaat",

    # Turizm / Otelcilik
    "MAALT.IS": "Turizm", "AYCES.IS": "Turizm", "TEKTU.IS": "Turizm",
    "ETILR.IS": "Turizm",

    # Aracı Kurum / Finans
    "GARFA.IS": "Finans", "ISFIN.IS": "Finans", "SEKFK.IS": "Finans",
    "GLRYH.IS": "Finans", "OYAYO.IS": "Finans",

    # Medya / İletişim
    "IHLAS.IS": "Medya", "DOAS.IS": "Medya",

    # Liman / Lojistik / Denizcilik
    "RYSAS.IS": "Lojistik", "CLEBI.IS": "Lojistik", "GSDDE.IS": "Denizcilik",

    # Cam / Seramik
    "TRCAS.IS": "Cam-Seramik", "KLMSN.IS": "Cam-Seramik", "USAK.IS": "Cam-Seramik",
    "EGSER.IS": "Cam-Seramik", "SISE.IS": "Cam-Seramik",

    # Mobilya
    "GENTS.IS": "Mobilya", "YATAS.IS": "Mobilya", "KLKIM.IS": "Mobilya",

    # Diğer Sanayi
    "TATEN.IS": "Enerji", "CWENE.IS": "Enerji", "BRSAN.IS": "Sanayi",
    "BRYAT.IS": "Sanayi", "EUPWR.IS": "Sanayi", "ALFAS.IS": "Sanayi",
    "SUWEN.IS": "Perakende", "TABGD.IS": "Madencilik", "REEDR.IS": "Sanayi",
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