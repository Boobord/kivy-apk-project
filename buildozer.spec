[app]
#android.gradle_repositories = mavenCentral(),google()
#android.gradle_dependencies = com.android.tools.build:gradle:7.4.2

title = InvoiceApp
package.name = invoiceapp
package.domain = org.reyhan
source.dir = .
source.main = kivy01.py

requirements = kivy,xhtml2pdf,arabic_reshaper,python-bidi,jdatetime


icon.filename = %(source.dir)s/logo.png
orientation = portrait
fullscreen = 1
android.archs = arm64-v8a
android.minapi = 21
android.api = 33
android.ndk_api = 21
android.permissions = WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE
android.entrypoint = org.kivy.android.PythonActivity
android.theme = @android:style/Theme.NoTitleBar
android.copy_libs = 1
version = 1.0.0
android.version_code = 1
android.add_assets = ./fonts/Vazirmatn-Medium.ttf, ./logo.png

[buildozer]
log_level = 2
num_jobs = 4

