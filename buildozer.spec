[app]

title = TVS Unit Tracker
package.name = tvsunittracker
package.domain = org.tvsunit

source.dir = .
source.include_exts = py,kv,png,jpg,jpeg,ttf,atlas

version = 1.0

requirements = python3,kivy

orientation = portrait
fullscreen = 0

# Optional: drop a 512x512 icon.png in this folder and uncomment the line
# below to use it as the app icon.
# icon.filename = %(source.dir)s/icon.png

android.permissions = INTERNET

# Android API / NDK settings (Buildozer will download these automatically
# on first build if they are not already installed).
android.api = 34
android.minapi = 21
android.ndk = 25b
android.archs = arm64-v8a, armeabi-v7a

android.accept_sdk_license = True

[buildozer]
log_level = 2
warn_on_root = 1
