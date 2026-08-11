# BIST Analiz Merkezi — Android (APK) Sürümü

## Bu klasörde ne var?

Orijinal Streamlit uygulamasının analiz motoru (göstergeler, sinyal üretimi,
temel analiz, tarama, portföy, risk yönetimi) korunarak, arayüz **Kivy** ile
native bir Android uygulamasına dönüştürüldü.

- `main.py` — Android arayüzü (4 sekme: Analiz, Tarama, Portföy, Ayarlar)
- `veri_katmani.py` — yfinance yerine `requests` ile Yahoo Finance'e doğrudan
  bağlanan, Android derlemesi için sadeleştirilmiş veri katmanı
- `gostergeler.py`, `sinyal_motoru.py`, `temel_analiz.py`, `tarayici.py`,
  `tarama_kriterleri.py`, `risk_yonetimi.py`, `portfoy.py`, `test.py`,
  `log_ayarlari.py` — orijinal analiz mantığı (değiştirilmedi)
- `ayarlar.py` — **değiştirildi**: eski dosyada Telegram bot token'ı doğrudan
  koda yazılmıştı, bunu kaldırdım. API anahtarları artık uygulama içindeki
  Ayarlar ekranından girilip cihazda ayrı bir dosyada saklanıyor — APK'yı
  paylaşırsan anahtarın da gitmesin diye.
- `buildozer.spec` — APK derleme yapılandırması
- `.github/workflows/build-apk.yml` — GitHub Actions ile otomatik derleme

## Neden APK'yı ben derlemedim?

Bu ortamda internet erişimim kapalı. APK derlemek Android SDK/NDK indirmeyi,
Gradle bağımlılıklarını çekmeyi gerektiriyor — bunları buradan yapamıyorum.
Bunun yerine **GitHub Actions** üzerinden internetli bir ortamda, sizin için
otomatik derlensin diye workflow dosyasını hazırladım.

## APK'yı nasıl alırsınız (yaklaşık 10-15 dakika, ücretsiz)

1. GitHub'da yeni bir repo oluşturun (public ya da private, fark etmez).
2. Bu klasördeki (`bist_analiz_apk`) TÜM dosyaları o repoya push edin:
   ```
   git init
   git add .
   git commit -m "ilk surum"
   git branch -M main
   git remote add origin https://github.com/KULLANICI_ADIN/REPO_ADIN.git
   git push -u origin main
   ```
3. Push işleminden sonra GitHub otomatik olarak "Actions" sekmesinde
   "APK Derle" workflow'unu başlatır. İlk derleme Android SDK/NDK indireceği
   için **15-25 dakika** sürebilir.
4. Derleme bitince Actions sayfasındaki ilgili çalıştırmanın altında
   "Artifacts" bölümünden `bist-analiz-apk` adlı zip'i indirin — içinde
   `.apk` dosyanız olacak.
5. APK'yı telefonunuza aktarıp kurun (Android "bilinmeyen kaynaklardan
   yükleme" iznini isteyebilir — bu normal, Play Store dışı APK'lar için
   standart bir uyarıdır).

Elle/lokal derlemek isterseniz (Linux/WSL üzerinde):
```
pip install buildozer cython==0.29.36
buildozer android debug
```

## Bilinmesi gerekenler / riskler

- **Kod boyutu**: Orijinal uygulamada AI asistan (Anthropic API), Telegram
  bildirimleri ve otomatik zamanlayıcı (arka planda periyodik tarama) da
  vardı. Bunları bu ilk sürüme **eklemedim** — kapsam çok büyüyüp derleme
  riskini artırıyordu. İstersen bir sonraki adımda bunları da native
  arayüze bağlayabilirim.
- **Wikipedia'dan tam BIST listesi**: `pd.read_html` için gereken `lxml`
  kütüphanesini bilinçli olarak derlemeye dahil etmedim (Android'de sık
  hata veren bir bağımlılık). Bu yüzden tam liste çekilemezse uygulama
  otomatik olarak ~20 hisselik bilinen bir yedek listeye düşer. Tam BIST
  taraması istersen bunu ayrıca ele almamız gerekir (örn. listeyi CSV
  olarak uygulamaya gömmek).
- **Yahoo Finance erişimi**: Veri katmanı yfinance yerine doğrudan Yahoo'nun
  genel JSON uçlarını kullanıyor; bu bazen (özellikle Yahoo API'de değişiklik
  olursa) çalışmayabilir. Bir sorun yaşarsan bana haber ver, uyarlarım.
- **İlk GitHub Actions derlemesi bazen ilk seferde ortam kaynaklı hata
  verebilir** (buildozer/p4a projelerinde sık rastlanan bir durumdur) —
  böyle olursa hata logunu bana yapıştır, düzeltip tekrar deneriz.
