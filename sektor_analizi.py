"""
Sektör Analizi — plan madde 12.
tarayici.tum_hisseleri_tara() çıktısını sektörlere göre gruplar ve her
sektöre Trend Score (ADX ortalaması), Momentum Score (haftalık getiri
ortalaması) ve Hacim Score (RVOL ortalaması) verir.
"""

from collections import defaultdict


def _ortalama(degerler):
    gecerli = [d for d in degerler if d is not None and d == d]  # d==d -> NaN eler
    return sum(gecerli) / len(gecerli) if gecerli else None


def sektor_performansi_hesapla(sonuclar):
    """
    sonuclar: tarayici.tum_hisseleri_tara() çıktısı — her elemanda 'sektor'
    alanının dolu olması için taramanın bist_evreni sembolleriyle ya da
    temel_dahil_et=True ile yapılmış olması gerekir.

    Dönüş: sektöre göre büyükten küçüğe (haftalık performansa göre)
    sıralanmış {sektor_adi: {...}} sözlüğü.
    """
    sektorlere_gore = defaultdict(list)
    for s in sonuclar:
        sektor = s.get("sektor") or "Diğer"
        sektorlere_gore[sektor].append(s)

    sonuc = {}
    for sektor, hisseler in sektorlere_gore.items():
        adx_degerleri = [h.get("gostergeler", {}).get("ADX") for h in hisseler]
        rvol_degerleri = [h.get("gostergeler", {}).get("RVOL") for h in hisseler]
        degisim_1g = [h.get("degisim_yuzde_1g") for h in hisseler]
        degisim_1h = [h.get("degisim_yuzde_1h") for h in hisseler]
        puanlar = [h.get("puan") for h in hisseler]

        siralanmis = sorted(
            [h for h in hisseler if h.get("puan") is not None],
            key=lambda h: h["puan"], reverse=True
        )

        trend_score = _ortalama(adx_degerleri)
        momentum_score = _ortalama(degisim_1h)
        hacim_score = _ortalama(rvol_degerleri)
        ort_1g = _ortalama(degisim_1g)
        ort_puan = _ortalama(puanlar)

        sonuc[sektor] = {
            "hisse_sayisi": len(hisseler),
            "trend_score": round(trend_score, 1) if trend_score is not None else None,
            "momentum_score": round(momentum_score, 2) if momentum_score is not None else None,
            "hacim_score": round(hacim_score, 2) if hacim_score is not None else None,
            "ortalama_puan": round(ort_puan, 2) if ort_puan is not None else None,
            "ortalama_degisim_1g": round(ort_1g, 2) if ort_1g is not None else None,
            "ortalama_degisim_1h": round(momentum_score, 2) if momentum_score is not None else None,
            "en_iyi_hisse": siralanmis[0]["sembol"] if siralanmis else None,
            "en_kotu_hisse": siralanmis[-1]["sembol"] if siralanmis else None,
        }

    return dict(sorted(
        sonuc.items(),
        key=lambda kv: kv[1]["ortalama_degisim_1h"] if kv[1]["ortalama_degisim_1h"] is not None else -999,
        reverse=True,
    ))


if __name__ == "__main__":
    from tarayici import tum_hisseleri_tara

    sonuclar = tum_hisseleri_tara()
    sektorler = sektor_performansi_hesapla(sonuclar)

    print("\n=== SEKTÖR PERFORMANSI (haftalık getiriye göre sıralı) ===")
    for sektor, veri in sektorler.items():
        print(f"\n{sektor} ({veri['hisse_sayisi']} hisse)")
        print(f"  Trend Score (ADX ort.): {veri['trend_score']}")
        print(f"  Momentum Score (1h %): {veri['momentum_score']}")
        print(f"  Hacim Score (RVOL ort.): {veri['hacim_score']}")
        print(f"  En iyi: {veri['en_iyi_hisse']}  |  En kötü: {veri['en_kotu_hisse']}")