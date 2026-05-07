# Stratoptic

## Proje
TMM tabanlı thin film simülasyon platformu.
Stack: Python 3.14, PyQt6, numpy, matplotlib, tmm
Hedef: Üniversite labları, optik kaplama firmaları

## Roadmap
Her session başında ROADMAP.md dosyasını oku — proje yol haritası ve mevcut durum orada.

## Dosya Yapısı
- main.py            → Ana giriş + orkestrasyon (298 satır)
- motor/engine.py    → TMM core
- motor/rii_db.py    → Refractiveindex.info entegrasyonu
- motor/optimizer.py → Kalınlık optimizasyonu (QThread)
- motor/color.py     → CIE renk hesaplama
- core/state.py      → AppState (henüz entegre değil)
- ui/sidebar.py      → Sidebar widget (layers, materials, conditions)
- ui/ribbon.py       → Ribbon + SummaryBar widget (calc params, show checkboxes)
- ui/plot_area.py    → PlotArea widget (canvasler + tabs + res_table)
- ui/dialogs.py      → Dialog fonksiyonları (export, import, about)
- ui/splash.py       → Splash screen pixmap
- ui/theme.py        → DARK/LIGHT tema
- ui/canvases.py     → 4 canvas sınıfı (ayrılacak — Faz 2)
- data/rii_db/       → RII veritabanı

## Çalışma Kuralları
- Stratoptic projesi. ~/stratoptic/ dizininde çalış, önce `source .venv/bin/activate`.
- Sadece istenen dosyayı değiştir
- Tüm dosyayı değil, sadece değişen fonksiyonu ver
- Mimari değişiklik öncesi onay iste
- Her session başında bu dosyayı oku

## Fizik Kısıtları
- transfer_matrix() complex dtype bekliyor, float verme
- Katman sırası: substrate → film stack → air
- s ve p polarizasyon ayrı hesaplanıyor

## Öncelik Sırası
1. Temizlik: ölü kod, import hack, bare except (Faz 0)
2. Refactor: main.py parçalama + AppState entegrasyonu (Faz 1)
3. Canvas ayırma (Faz 2)
4. Motor iyileştirmeleri + yeni özellikler (Faz 3+)

## Mimari Kararlar
- State model: core/state.py — AppState QObject, tüm uygulama durumu burada tutulur
- UI: sidebar, ribbon, plot_area ayrı widget dosyaları, main_window bunları birleştirir
- Ölü kod silindi: material_db.py (JSON-based statik n/k), visualizer.py (eski plotly/mpl)
- Canvas sınıfları ui/canvases/ altında, her biri kendi dosyasında
- Theme: ui/theme.py — DARK/LIGHT dict + build_style() + helper fonksiyonlar
- Optimizer: motor/optimizer.py — QThread tabanlı, signal ile progress bildirimi

## Geçmiş Hatalar
- material_db.py eski `from tmm import Material` kullanıyordu — rii_db.py ile değiştirildi, dosya silindi
- visualizer.py `from tmm import TMMResult` import'u yanlış — engine.py'deki sınıflar kullanılmalı, dosya silindi
- motor/tests/test_tmm.py eski API kullanıyordu — silindi (Faz 0)
- patch_*.py ve tmm_old.py — silindi (daha önce)
- main.py sys.path.insert(0, 'motor') hack'i vardı — düzeltildi (Faz 0)
- Monolitik main.py (1138 sat) bakım ve test edilebilirliği çok zorlaştırıyor

## Yapılmaması Gerekenler
- numpy.matrix kullanma, array kullan
- QThread'de direkt GUI güncelleme yapma, signal kullan.

## Modül Çıkarma Durumunda:

GÖREV: [Görev ID] — [Görev adı]

KAYNAK: main.py satır [X]-[Y]
HEDEF: [hedef dosya yolu]

KURALLAR:
- Sadece belirtilen satırları taşı, geri kalanına dokunma
- Import'ları düzelt (hem kaynak hem hedef)
- numpy.matrix kullanma
- Mevcut işlevselliği bozma

DOĞRULAMA: `python main.py` çalışmalı + [spesifik test]

Tamamladığında değişen dosyaların diff özetini göster.

## Yeni Özellik Durumunda:

GÖREV: [Görev ID] — [Görev adı]

DOSYALAR: [etkilenen dosyalar listesi]

SPEC:
[Detaylı spesifikasyon — yukarıdaki görev açıklamasından]

KISITLAR:
- TMM hesabı complex dtype bekliyor
- QThread'de direkt GUI güncelleme yapma, signal kullan
- numpy.matrix değil numpy.array kullan

DOĞRULAMA: [test senaryosu]