[app]
title = BIST Analiz Merkezi
package.name = bistanaliz
package.domain = org.bistanaliz

source.dir = .
source.include_exts = py,png,jpg,kv,atlas,json

version = 1.0

requirements = python3,kivy==2.3.0,pandas,numpy,requests,certifi

orientation = portrait
fullscreen = 0

icon.filename = %(source.dir)s/icon.png

android.permissions = INTERNET
android.api = 34
android.minapi = 24
android.ndk = 28c
android.archs = arm64-v8a,armeabi-v7a
android.allow_backup = True

[buildozer]
log_level = 2
warn_on_root = 1
