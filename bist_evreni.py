"""
Screener, sıralamalar ve sektör analizinin tarayacağı BIST hisse evreni.
Sembol -> sektör eşlemesi burada tutulur; yeni hisse eklemek istediğinde
sadece bu sözlüğe satır eklemen yeterli.

Not: Sembollerin sonundaki '.IS' Yahoo Finance'in Borsa İstanbul son ekidir.
"""

BIST_HISSELERI = {
    # Bankacılık
    "AKBNK.IS": "Bankacılık", "GARAN.IS": "Bankacılık", "ISCTR.IS": "Bankacılık",
    "YKBNK.IS": "Bankacılık", "VAKBN.IS": "Bankacılık", "HALKB.IS": "Bankacılık",
    "SKBNK.IS": "Bankacılık", "TSKB.IS": "Bankacılık",
    # Holding
    "KCHOL.IS": "Holding", "SAHOL.IS": "Holding", "SISE.IS": "Holding",
    "DOAS.IS": "Holding", "ALARK.IS": "Holding", "AGHOL.IS": "Holding",
    # Sanayi / Otomotiv / Metal
    "EREGL.IS": "Demir-Çelik", "KRDMD.IS": "Demir-Çelik", "TOASO.IS": "Otomotiv",
    "FROTO.IS": "Otomotiv", "TTRAK.IS": "Otomotiv", "OTKAR.IS": "Otomotiv",
    "ASELS.IS": "Savunma", "TUPRS.IS": "Petrokimya", "PETKM.IS": "Petrokimya",
    "EKGYO.IS": "GYO", "KOZAL.IS": "Madencilik", "KOZAA.IS": "Madencilik",
    # Perakende / Gıda / Tüketim
    "BIMAS.IS": "Perakende", "MGROS.IS": "Perakende", "SOKM.IS": "Perakende",
    "ULKER.IS": "Gıda", "CCOLA.IS": "Gıda", "AEFES.IS": "Gıda",
    # Havacılık / Ulaştırma
    "THYAO.IS": "Havacılık", "PGSUS.IS": "Havacılık", "TAVHL.IS": "Ulaştırma",
    # Telekom / Teknoloji
    "TCELL.IS": "Telekom", "TTKOM.IS": "Telekom", "LOGO.IS": "Teknoloji",
    "ASTOR.IS": "Sanayi",
    # Sigorta / Finans
    "TURSG.IS": "Sigorta", "ANSGR.IS": "Sigorta", "AGESA.IS": "Sigorta",
    # Enerji
    "AKSEN.IS": "Enerji", "AKSA.IS": "Enerji", "ENJSA.IS": "Enerji",
    "ZOREN.IS": "Enerji", "ODAS.IS": "Enerji",
    # Diğer sanayi
    "ARCLK.IS": "Dayanıklı Tüketim", "VESTL.IS": "Dayanıklı Tüketim",
    "CIMSA.IS": "Çimento", "OYAKC.IS": "Çimento", "AKCNS.IS": "Çimento",
    "KONYA.IS": "Çimento", "ISDMR.IS": "Demir-Çelik",
}


def hisse_listesi():
    """Tüm BIST sembollerinin düz listesi (screener taraması için)."""
    return list(BIST_HISSELERI.keys())


def sektor_getir(sembol):
    """Bir sembolün sektörünü döner, tanımlı değilse None döner."""
    return BIST_HISSELERI.get(sembol)


def sektorler_listesi():
    """Tanımlı tüm sektörlerin tekrarsız listesi."""
    return sorted(set(BIST_HISSELERI.values()))
