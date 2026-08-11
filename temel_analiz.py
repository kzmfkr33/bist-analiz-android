"""
Temel Analiz — plan madde 15, 16, 17.
Değerleme (F/K, PD/DD, FD/FAVÖK), kârlılık (ROE, net kâr marjı), borç
oranları, büyüme (CAGR) ve sektöre göre göreceli değerleme burada.
"""


def temel_puanla(temel_veri):
    """
    F/K, PD/DD, ROE, borç/özsermaye, temettü verimi gibi temel verilere
    bakıp basit bir puanlama ve yorum listesi üretir. Sektöre göre 'normal'
    değerler değişir, bu yüzden burada genel/kaba eşikler kullanılıyor —
    kesin doğru değil, yönlendirici bir fikir. Sektörle kıyaslamak için
    sektore_gore_degerleme() fonksiyonunu kullan.
    """
    bulgular = []
    puan = 0

    fk = temel_veri.get("fk_orani")
    if fk is not None:
        if fk < 0:
            bulgular.append(f"F/K oranı negatif ({fk:.1f}) — şirket zarar ediyor olabilir")
            puan -= 1
        elif fk < 10:
            bulgular.append(f"F/K oranı düşük ({fk:.1f}) — piyasaya göre ucuz görünüyor")
            puan += 1
        elif fk > 30:
            bulgular.append(f"F/K oranı yüksek ({fk:.1f}) — piyasaya göre pahalı görünüyor")
            puan -= 1
        else:
            bulgular.append(f"F/K oranı normal aralıkta ({fk:.1f})")
    else:
        bulgular.append("F/K oranı verisi bulunamadı")

    pd_dd = temel_veri.get("pd_dd_orani")
    if pd_dd is not None:
        if pd_dd < 1:
            bulgular.append(f"PD/DD oranı 1'in altında ({pd_dd:.2f}) — defter değerinin altında işlem görüyor")
            puan += 1
        elif pd_dd > 5:
            bulgular.append(f"PD/DD oranı yüksek ({pd_dd:.2f}) — defter değerine göre pahalı")
            puan -= 1
        else:
            bulgular.append(f"PD/DD oranı normal aralıkta ({pd_dd:.2f})")
    else:
        bulgular.append("PD/DD oranı verisi bulunamadı")

    roe = temel_veri.get("roe")
    if roe is not None:
        if roe > 0.20:
            bulgular.append(f"ROE %{roe * 100:.1f} — güçlü özsermaye kârlılığı")
            puan += 1
        elif roe < 0.05:
            bulgular.append(f"ROE %{roe * 100:.1f} — zayıf özsermaye kârlılığı")
            puan -= 1
        else:
            bulgular.append(f"ROE %{roe * 100:.1f} — normal aralıkta")

    borc_ozsermaye = temel_veri.get("borc_ozsermaye")
    if borc_ozsermaye is not None:
        if borc_ozsermaye > 150:
            bulgular.append(f"Borç/Özsermaye yüksek ({borc_ozsermaye:.0f}) — kaldıraç riski dikkat gerektirir")
            puan -= 1
        elif borc_ozsermaye < 50:
            bulgular.append(f"Borç/Özsermaye düşük ({borc_ozsermaye:.0f}) — sağlam bilanço")
            puan += 1

    gelir_buyume = temel_veri.get("gelir_buyume")
    if gelir_buyume is not None:
        if gelir_buyume > 0.15:
            bulgular.append(f"Gelir büyümesi %{gelir_buyume * 100:.1f} — güçlü büyüme")
            puan += 1
        elif gelir_buyume < 0:
            bulgular.append(f"Gelir büyümesi negatif (%{gelir_buyume * 100:.1f}) — daralma")
            puan -= 1

    temettu = temel_veri.get("temettu_verimi")
    if temettu is not None and temettu > 0:
        bulgular.append(f"Temettü verimi %{temettu * 100:.1f} — düzenli getiri sağlıyor olabilir")
        puan += 1

    yuksek_52 = temel_veri.get("52_hafta_yuksek")
    dusuk_52 = temel_veri.get("52_hafta_dusuk")

    if puan >= 3:
        genel = "Temel görünüm OLUMLU"
    elif puan <= -3:
        genel = "Temel görünüm OLUMSUZ"
    else:
        genel = "Temel görünüm NÖTR/KARIŞIK"

    return {
        "temel_puan": puan,
        "temel_genel": genel,
        "temel_bulgular": bulgular,
        "52_hafta_araligi": f"{dusuk_52} - {yuksek_52}" if yuksek_52 and dusuk_52 else "Veri yok",
    }


def cagr_hesapla(baslangic_degeri, bitis_degeri, yil_sayisi):
    """
    CAGR (Compound Annual Growth Rate — Bileşik Yıllık Büyüme Oranı) hesaplar.
    Örn: 4 yılda satışlar 100'den 180'e çıktıysa, yıllık ortalama büyüme oranı.
    Başlangıç değeri negatif/sıfırsa (zarar/gelir yoksa) None döner.
    """
    if not baslangic_degeri or baslangic_degeri <= 0 or yil_sayisi <= 0:
        return None
    oran = (bitis_degeri / baslangic_degeri) ** (1 / yil_sayisi) - 1
    return round(oran * 100, 1)


def buyume_analizi_hesapla(gecmis_veriler):
    """
    veri_katmani.gecmis_finansal_veriler_getir() çıktısını alır (yıla göre
    sıralı liste), satış ve net kâr için CAGR hesaplar.

    Dönüş: {"satis_cagr": ..., "net_kar_cagr": ..., "yil_araligi": "2021-2024",
            "yillik_veriler": [...]}  (yıllık_veriler tabloda/grafikte gösterilebilir)
    """
    if not gecmis_veriler or len(gecmis_veriler) < 2:
        return {"satis_cagr": None, "net_kar_cagr": None, "yil_araligi": None,
                "yillik_veriler": gecmis_veriler or []}

    ilk, son = gecmis_veriler[0], gecmis_veriler[-1]
    yil_farki = len(gecmis_veriler) - 1

    satis_cagr = cagr_hesapla(ilk.get("satis"), son.get("satis"), yil_farki)
    net_kar_cagr = cagr_hesapla(ilk.get("net_kar"), son.get("net_kar"), yil_farki)

    return {
        "satis_cagr": satis_cagr,
        "net_kar_cagr": net_kar_cagr,
        "yil_araligi": f"{ilk.get('yil')}-{son.get('yil')}",
        "yillik_veriler": gecmis_veriler,
    }


def sektore_gore_degerleme(sirket_temel_verisi, sektordeki_diger_hisseler):
    """
    Şirketin F/K, PD/DD ve FD/FAVÖK çarpanlarını, aynı sektördeki diğer
    hisselerin ortalamasıyla kıyaslar. Örnek çıktı: "F/K 7,2, sektör
    ortalaması 11,5 — sektöre göre yaklaşık %37 iskontolu."

    sirket_temel_verisi: veri_katmani.temel_veri_getir() çıktısı
    sektordeki_diger_hisseler: aynı sektördeki diğer hisselerin
        temel_veri_getir() çıktılarının listesi (kendisi hariç)

    Dönüş: {"fk": {...}, "pd_dd": {...}, "fd_favok": {...}} — her biri
    None olabilir (veri yoksa).
    """

    def _karsilastir(alan):
        sirket_degeri = sirket_temel_verisi.get(alan)
        sektor_degerleri = [
            h.get(alan) for h in sektordeki_diger_hisseler
            if h.get(alan) is not None and h[alan] > 0
        ]
        if not sirket_degeri or sirket_degeri <= 0 or not sektor_degerleri:
            return None

        sektor_ortalamasi = sum(sektor_degerleri) / len(sektor_degerleri)
        fark_yuzde = 100 * (sirket_degeri - sektor_ortalamasi) / sektor_ortalamasi

        if fark_yuzde < 0:
            yorum = f"Sektöre göre yaklaşık %{abs(fark_yuzde):.0f} iskontolu"
        else:
            yorum = f"Sektöre göre yaklaşık %{fark_yuzde:.0f} primli"

        return {
            "sirket_degeri": round(sirket_degeri, 2),
            "sektor_ortalamasi": round(sektor_ortalamasi, 2),
            "fark_yuzde": round(fark_yuzde, 1),
            "yorum": yorum,
        }

    return {
        "fk": _karsilastir("fk_orani"),
        "pd_dd": _karsilastir("pd_dd_orani"),
        "fd_favok": _karsilastir("fd_favok"),
    }


if __name__ == "__main__":
    from veri_katmani import temel_veri_getir, gecmis_finansal_veriler_getir

    sembol = "THYAO.IS"
    temel = temel_veri_getir(sembol)

    sonuc = temel_puanla(temel)
    print(f"\n=== {sembol} TEMEL ANALİZ ===")
    print(f"Puan: {sonuc['temel_puan']} — {sonuc['temel_genel']}")
    for b in sonuc["temel_bulgular"]:
        print(f"  - {b}")

    gecmis = gecmis_finansal_veriler_getir(sembol)
    buyume = buyume_analizi_hesapla(gecmis)
    print(f"\n=== BÜYÜME ({buyume['yil_araligi']}) ===")
    print(f"Satış CAGR: %{buyume['satis_cagr']}")
    print(f"Net Kâr CAGR: %{buyume['net_kar_cagr']}")
    for yil_verisi in buyume["yillik_veriler"]:
        print(f"  {yil_verisi}")