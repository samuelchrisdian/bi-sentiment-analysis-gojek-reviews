# VALIDASI PREPROCESSING — FASE 2

Seluruh angka di bawah berasal dari kode yang dijalankan atas 100.000 ulasan.

## 1. Hasil Pipeline

| Properti | Nilai |
|----------|-------|
| Baris keluaran | 100.000 (12 kolom) |
| `data/processed/reviews_clean.parquet` | 12,1 MB |
| Label: negatif / positif / netral | 26.732 / 69.734 / 3.534 |
| `word_count <= 2` | 39.911 |
| `word_count >= 5` (subset `informative_ge5w`) | 45.925 |
| **Deterministik** | ✅ dua run menghasilkan DataFrame identik |

## 2. Pemeriksaan Kritis: Negasi Bertahan

Tujuan daftar stopword kustom adalah memastikan kata pembawa negasi tidak ikut
terbuang. Terverifikasi pada `ulasan_clean`:

| Kata | Dokumen yang masih memuatnya |
|------|------------------------------|
| `tidak` | 19.297 |
| `jangan` | 1.820 |
| `belum` | 1.658 |
| `bukan` | 979 |

Tanpa penyesuaian ini, "tidak bagus" akan menjadi "bagus" — kebalikan maknanya,
tepat pada kelas yang menjadi fokus penelitian.

## 3. Teks yang Menjadi Kosong — 1.308 (1,3%)

Seluruhnya dapat dijelaskan; tidak ada yang merupakan kegagalan pipeline:

| Sebab | Jumlah | Contoh |
|-------|--------|--------|
| Hanya emoji, angka, atau tanda baca | 1.237 | `👍`, `5`, `...` |
| Hanya stopword | 71 | `saat`, `boleh`, `pasti`, `yah`, `yg pasti pasti saja` |

Keduanya memang tidak membawa sinyal sentimen. Baris tetap disimpan di parquet
(tidak dibuang) agar statistik deskriptif dan dashboard memakai data penuh;
TF-IDF akan mengabaikannya secara alami.

## 4. Catatan Kinerja — Deviasi dari Target DoD

Target DoD Fase 2 adalah "< 5 menit". Hasil terukur:

| Kondisi | Waktu |
|---------|-------|
| Run pertama (cache kosong) | **656 detik (10,9 menit)** — melewati target |
| Run berikutnya (cache terisi) | **1,3 detik** |

Penyebab run pertama: dari 28.297 kata unik, 4.190 sudah ada di kamus dasar
Sastrawi, tetapi 24.107 sisanya berada di luar kamus. Untuk kata di luar kamus,
Sastrawi menjalankan seluruh kaskade aturan afiks sebelum menyerah — terukur
~79 ms per kata, atau ~32 menit pada satu core.

Mitigasi yang diterapkan:

1. **Cache per kata unik**, bukan per dokumen (`stem_cache.json`, 581 KB).
2. **Melewati kata yang sudah bentuk dasar** — 4.190 kata tidak perlu di-stem.
3. **Paralelisasi ke 14 proses** — 32 menit menjadi 10,9 menit.
4. **Penulisan cache berkala** tiap 2.000 kata, sehingga run yang terputus
   tidak kehilangan progres.

Target 5 menit terpenuhi untuk setiap run setelah yang pertama. Karena artefak
ini dibangun sekali dan cache ikut tersimpan, biaya 10,9 menit hanya dibayar
satu kali per mesin.

## 5. Status Gerbang

- **H-5 (kamus slang)** — ✅ lolos. 500/500 token diputuskan manusia.
- **H-6 (verifikasi 100 sampel)** — ⛔ menunggu pemeriksaan manusia.
