# Stratoptic

## Proje
TMM tabanlı thin film simülasyon platformu.
Stack: Python 3.11, PyQt6, numpy, matplotlib
Hedef: Üniversite labları, optik kaplama firmaları

## Dosya Yapısı
- main.py          → Ana giriş + UI (refactor bekliyor)
- motor/engine.py  → TMM core
- motor/rii_db.py  → Refractiveindex.info entegrasyonu
- motor/tmm_old.py → Eski TMM — audit et, muhtemelen sil
- patch_*.py       → Audit et, aktif mi dead code mu belli değil
- data/materials/  → Lokal malzeme JSON
- data/rii_db/     → RII veritabanı

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
1. Audit: patch_*.py ve tmm_old.py temizliği
2. Refactor: UI'ı main.py'dan ayır
3. Feature: Kalınlık optimizasyonu

## Mimari Kararlar
- State model: core/state.py — AppState QObject, tüm uygulama durumu burada tutulur
- UI: sidebar, ribbon, plot_area ayrı widget dosyaları, main_window bunları birleştirir
- Ölü kod silindi: material_db.py (JSON-based statik n/k), visualizer.py (eski plotly/mpl)
- Canvas sınıfları ui/canvases/ altında, her biri kendi dosyasında
- Theme: ui/theme.py — DARK/LIGHT dict + build_style() + helper fonksiyonlar
- Optimizer: motor/optimizer.py — QThread tabanlı, signal ile progress bildirimi

## Geçmiş Hatalar
- material_db.py eski `from tmm import Material` kullanıyordu — rii_db.py ile değiştirildi
- visualizer.py `from tmm import TMMResult` import'u yanlış — engine.py'deki sınıflar kullanılmalı
- Monolitik main.py (1370 sat) bakım ve test edilebilirliği çok zorlaştırıyordu

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