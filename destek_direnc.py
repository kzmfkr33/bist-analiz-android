"""
Destek ve Direnç Tespiti — plan madde 9.
Fiyat grafiğindeki yerel tepe/dip noktalarını (swing high/low) bularak
birbirine yakın seviyeleri kümeler; bir seviyeye kaç kez dokunulduysa
o kadar 'güçlü' kabul eder (fiyat o seviyeden kaç kez tepki verdiyse
piyasanın o seviyeye verdiği önem o kadar fazladır).
"""


def _swing_noktalarini_bul(veri, kenar=5):
    """
    Solundaki VE sağındaki 'kenar' kadar mumdan daha yüksek/düşük olan
    noktaları swing high/low olarak işaretler (fraktal mantığı).
    """
    yuksekler, dusukler = [], []

    for i in range(kenar, len(veri) - kenar):
        pencere_yuksek = veri['High'].iloc[i - kenar:i + kenar + 1]
        if veri['High'].iloc[i] == pencere_yuksek.max():
            yuksekler.append(float(veri['High'].iloc[i]))

        pencere_dusuk = veri['Low'].iloc[i - kenar:i + kenar + 1]
        if veri['Low'].iloc[i] == pencere_dusuk.min():
            dusukler.append(float(veri['Low'].iloc[i]))

    return yuksekler, dusukler


def _seviyeleri_kumele(noktalar, tolerans_yuzde=1.5):
    """
    Birbirine tolerans_yuzde kadar yakın fiyat noktalarını tek bir
    seviyede birleştirir. Bir kümedeki nokta sayısı = o seviyenin gücü.
    Dönüş: [{"seviye": ortalama_fiyat, "guc": dokunma_sayisi}, ...]
    """
    if not noktalar:
        return []

    noktalar = sorted(noktalar)
    kumeler = [[noktalar[0]]]

    for nokta in noktalar[1:]:
        son_kume_ortalamasi = sum(kumeler[-1]) / len(kumeler[-1])
        if abs(nokta - son_kume_ortalamasi) / son_kume_ortalamasi * 100 <= tolerans_yuzde:
            kumeler[-1].append(nokta)
        else:
            kumeler.append([nokta])

    return [
        {"seviye": round(sum(k) / len(k), 2), "guc": min(len(k), 5)}
        for k in kumeler
    ]


def destek_direnc_bul(veri, guncel_fiyat=None, kenar=5, tolerans_yuzde=1.5, maks_seviye=5):
    """
    Güncel fiyata göre en yakın 'maks_seviye' destek ve direnç seviyesini döner.
    'guc' alanı 1-5 arası: kaç kez o seviyeden tepki geldiğini gösterir
    (5 = en güçlü/en çok test edilmiş seviye).
    """
    if guncel_fiyat is None:
        guncel_fiyat = float(veri['Close'].iloc[-1])

    yuksekler, dusukler = _swing_noktalarini_bul(veri, kenar)

    direnc_kumeleri = [
        s for s in _seviyeleri_kumele(yuksekler, tolerans_yuzde) if s["seviye"] > guncel_fiyat
    ]
    destek_kumeleri = [
        s for s in _seviyeleri_kumele(dusukler, tolerans_yuzde) if s["seviye"] < guncel_fiyat
    ]

    direnc_kumeleri.sort(key=lambda s: s["seviye"])            # fiyata en yakın direnç önce
    destek_kumeleri.sort(key=lambda s: s["seviye"], reverse=True)  # fiyata en yakın destek önce

    return {
        "guncel_fiyat": round(guncel_fiyat, 2),
        "direncler": direnc_kumeleri[:maks_seviye],
        "destekler": destek_kumeleri[:maks_seviye],
    }


if __name__ == "__main__":
    from test import analiz_et

    sembol = "THYAO.IS"
    veri = analiz_et(sembol)
    sonuc = destek_direnc_bul(veri)

    print(f"\n=== {sembol} DESTEK / DİRENÇ ===")
    print(f"Güncel fiyat: {sonuc['guncel_fiyat']} TL\n")

    print("DİRENÇLER (fiyata yakından uzağa):")
    for d in sonuc["direncler"]:
        print(f"  {d['seviye']} TL — güç: {'★' * d['guc']}")

    print("\nDESTEKLER (fiyata yakından uzağa):")
    for d in sonuc["destekler"]:
        print(f"  {d['seviye']} TL — güç: {'★' * d['guc']}")