# Stratoptic Roadmap
> Sistem audit: 2026-05-07 | Durum: 11/11 test passing

---

## FAZA 0 — Temizlik & Teknik Borc (Oncelik: Yuksek)

### 0.1 Olu Kod Temizligi
- [ ] `motor/tests/test_tmm.py` sil (eski `from tmm import Material, Polarization` — calismaz)
- [ ] `core/state.py` ya entegre et ya da sil (tanimli ama hic kullanilmiyor)

### 0.2 Import Duzeltme
- [ ] `main.py:21` — `sys.path.insert(0, 'motor')` hack'ini kaldir
- [ ] Tum import'lari `from motor.engine import ...` seklinde duzelt
- [ ] `optimizer.py:4` — `from engine import TMMEngine` → `from motor.engine import TMMEngine`

### 0.3 Bare Except Temizligi
- [ ] main.py'deki 6+ `except:` / `except: pass` satirini spesifik exception'larla degistir
- [ ] Minimum: `except Exception as e:` + loglama

### 0.4 Test Iyilestirme
- [ ] `tests/test_engine.py` — conftest.py fixture'larini kullanacak sekilde refactor et
- [ ] `motor/color.py` icin test yaz (spectrum_to_XYZ, XYZ_to_sRGB)
- [ ] `motor/optimizer.py` icin basit unit test yaz

---

## FAZA 1 — UI Refactor: main.py Parcalama (TAMAMLANDI)

### 1.1 Sidebar Cikarimi
- [x] `main.py` _build_sidebar() + iliskili metodlari → `ui/sidebar.py`
- [x] Layer management metodlari (_add_layer, _remove_layer, _swap_rows, vb.)
- [x] Substrate/Incident combo'lari
- [x] Optimization conditions UI

### 1.2 Ribbon Cikarimi
- [x] `main.py` _build_ribbon() → `ui/ribbon.py`
- [x] Calculation parametreleri (wl range, angle, pol)
- [x] Optimization bounds + button

### 1.3 Plot Area Cikarimi
- [x] `main.py` _build_plotarea() → `ui/plot_area.py`
- [x] Tab yonetimi (Spectrum, Stack, Dispersion, E-Field)

### 1.4 Main Window Sadece Orkestrasyon
- [x] `main.py` sadece widget'lari birlestiren ince katman (298 satir)
- [x] Menu + dialog'lar ayri (`ui/dialogs.py`)
- [x] Splash screen ayri (`ui/splash.py`)

### 1.5 AppState Entegrasyonu (TAMAMLANDI)
- [x] `core/state.py` AppState'i aktif kullanima al
- [x] Widget'lar arasi iletisim signal/slot ile AppState uzerinden
- [x] `_last_result`, `_last_structure`, `_overlay_results` → AppState'e tasi

---

## FAZA 2 — Canvas Ayirma (Oncelik: Orta)

### 2.1 Canvas Dosya Yapisi
- [ ] `ui/canvases.py` → `ui/canvases/` dizinine ayir
- [ ] `ui/canvases/__init__.py` — re-export
- [ ] `ui/canvases/spectrum.py` — SpectrumCanvas
- [ ] `ui/canvases/dispersion.py` — DispersionCanvas
- [ ] `ui/canvases/stack.py` — StackCanvas
- [ ] `ui/canvases/efield.py` — EFieldCanvas

---

## FAZA 3 — Motor Iyilestirmeleri (Oncelik: Orta)

### 3.1 Engine Performans
- [ ] `engine.py` _calc_single for-loop'u → vectorize (tmm API'si elverirse)
- [ ] RIIDatabase index'ini pickle cache ile hizlandir (startup suresi)
- [ ] Benchmark: mevcut vs optimize edilmis (benchmark.py zaten var)

### 3.2 Optimizer Gelistirme
- [ ] Coklu algoritma destegi (differential_evolution, scipy.optimize.minimize, basin-hopping)
- [ ] Iterasyon bazli progress signal (mevcut sadece "Optimizing..." gosteriyor)
- [ ] Constraint destegi (min/max R/T belirli wl araliginda)
- [ ] Sonuc gecmisi (onceki optimizasyon sonuclarini karsilastir)

### 3.3 Yeni Hesaplama Ozellikleri
- [ ] Aci taramasi (angular spectrum — tek yapiyi birden fazla acida hesapla)
- [ ] GDD (Group Delay Dispersion) hesaplama
- [ ] Stack peryodu (DBR/Bragg yapilar icin otomatik periyot olusturma)

---

## FAZA 4 — Kullanici Deneyimi (Oncelik: Orta-Dusuk)

### 4.1 Proje Kaydetme/Yukleme
- [ ] Yapilari JSON olarak kaydet/yukle
- [ ] Son kullanilan yapilar gecmisi

### 4.2 Gelismis UI
- [ ] Material veritabani browser dialog (arama + filtreleme + onizleme)
- [ ] Katman tablosunda drag & drop sira degistirme
- [ ] Undo/Redo sistemi

### 4.3 Export Gelistirme
- [ ] PDF rapor olusturma (yapi + grafik + tablo)
- [ ] SVG export
- [ ] Multi-angle karsilastirma grafigu export

---

## FAZA 5 — Ileri Ozellikler (Oncelik: Dusuk)

### 5.1 Inverse Design
- [ ] Hedef spektrum belirleme + otomatik yapi onerisi
- [ ] Genetic algorithm ile cok katmanli optimizasyon

### 5.2 Veritabani Genisletme
- [ ] Kullanici malzeme veritabani persistence (JSON dosyasina kaydet)
- [ ] Malzeme karsilastirma araci (n/k grafiklerini ust uste ciz)

### 5.3 Paketleme & Dagitim
- [ ] pyproject.toml'u tam spec ile doldur (version, dependencies, entry_points)
- [ ] PyInstaller / cx_Freeze ile standalone executable
- [ ] GitHub Actions CI (test + lint)

---

## Oncelik Matrisi

| Faz | Risk | Etki | Tahmini Karmasiklik |
|-----|------|------|---------------------|
| 0 — Temizlik | Dusuk | Yuksek (bakim kolayligi) | Dusuk |
| 1 — UI Refactor | Orta | Cok Yuksek (test edilebilirlik, bakim) | Yuksek |
| 2 — Canvas Ayirma | Dusuk | Orta | Dusuk |
| 3 — Motor | Orta | Yuksek (kullanici degeri) | Orta |
| 4 — UX | Dusuk | Orta | Orta |
| 5 — Ileri | Yuksek | Yuksek | Cok Yuksek |

---

## Baslama Onerisi
**Faz 0 → Faz 1.1** sirasi ile.
Faz 0 yarim gun icinde tamamlanabilir.
Faz 1 buyuk refactor — her adim sonrasi `python main.py` ile dogrulama + testler.
