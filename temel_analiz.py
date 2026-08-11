def temel_puanla(temel_veri):
    """
    F/K, PD/DD, temettü verimi gibi temel verilere bakıp basit bir
    puanlama ve yorum listesi üretir. Sektöre göre 'normal' F/K değişir,
    bu yüzden burada genel/kaba eşikler kullanıyoruz — kesin doğru değil,
    yönlendirici bir fikir.
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

    temettu = temel_veri.get("temettu_verimi")
    if temettu is not None and temettu > 0:
        bulgular.append(f"Temettü verimi %{temettu * 100:.1f} — düzenli getiri sağlıyor olabilir")
        puan += 1

    yuksek_52 = temel_veri.get("52_hafta_yuksek")
    dusuk_52 = temel_veri.get("52_hafta_dusuk")

    if puan >= 2:
        genel = "Temel görünüm OLUMLU"
    elif puan <= -2:
        genel = "Temel görünüm OLUMSUZ"
    else:
        genel = "Temel görünüm NÖTR/KARIŞIK"

    return {
        "temel_puan": puan,
        "temel_genel": genel,
        "temel_bulgular": bulgular,
        "52_hafta_araligi": f"{dusuk_52} - {yuksek_52}" if yuksek_52 and dusuk_52 else "Veri yok",
    }