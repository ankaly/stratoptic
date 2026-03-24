# Stratoptic

## Proje
TMM tabanlı thin film simülasyon platformu.
Stack: Python 3.11, PyQt6, numpy, matplotlib
Hedef: Üniversite labları, optik kaplama firmaları

## Dosya Yapısı
- main.py          → Ana giriş + UI (refactor bekliyor)
- motor/engine.py  → TMM core
- motor/material_db.py → Lokal malzeme DB
- motor/rii_db.py  → Refractiveindex.info entegrasyonu
- motor/visualizer.py  → Grafik çizimi
- motor/tmm_old.py → Eski TMM — audit et, muhtemelen sil
- patch_*.py       → Audit et, aktif mi dead code mu belli değil
- data/materials/  → Lokal malzeme JSON
- data/rii_db/     → RII veritabanı

## Çalışma Kuralları
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
[Audit sonrası dolacak]

## Geçmiş Hatalar
[Audit sonrası dolacak]

## Yapılmaması Gerekenler
- numpy.matrix kullanma, array kullan
- QThread'de direkt GUI güncelleme yapma, signal kullan
```