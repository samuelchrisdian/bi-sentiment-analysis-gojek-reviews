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

## 5. Gerbang H-6 — Tiga Putaran Pemeriksaan

| Putaran | Sampel | Masalah sistemik ditemukan | Dampak terukur |
|---------|--------|---------------------------|----------------|
| 1 | 100 | Stemming merusak entitas domain · emoji hilang | 15% korpus · 1.237 dok |
| 2 | 97 | Struktur negasi hancur · negasi palsu dari stemming | ~10.000 dok · 213 dok |
| 3 | 78 | **Nol** — seluruhnya token individual | — |

Pola konvergensinya jelas: dua putaran pertama menemukan cacat yang mengubah
makna pada puluhan ribu dokumen; putaran ketiga hanya menemukan typo satuan.

### Rekapitulasi perbaikan

| Aspek | Akhir |
|-------|-------|
| `SLANG_DICT` | 572 entri (45 multi-kata) |
| `STEM_OVERRIDE` | 45 pengecualian |
| `NEGATION_KEEP` | 24 kata (dari 11 semula) |
| Normalisasi frasa | 13 pola |
| Pemetaan emoji | 45 emoji, hanya pada ulasan ≤3 kata |
| Teks kosong | 1.308 → **237** (1,3% → 0,2%) |

### Struktur negasi — sebelum dan sesudah

| Frasa | Ada | Bertahan (awal) | Bertahan (akhir) |
|-------|-----|-----------------|------------------|
| `tidak bisa` | 4.849 | 3 | **4.849** |
| `tidak ada` | 4.017 | 9 | **4.017** |
| `tidak dapat` | 1.168 | 69 | **1.168** |

## 6. Residu yang Diketahui dan Alasan Tidak Dikejar Lebih Jauh

Putaran 3 menyisakan sejumlah typo satuan yang tidak dipetakan. Keputusan untuk
menghentikan iterasi didasarkan pada bukti, bukan kelelahan:

**70% token unik (14.857 dari 21.302) memiliki document frequency di bawah 3**,
sehingga `TfidfVectorizer(min_df=3)` membuangnya sebelum model melihatnya.
Diperiksa satu per satu, mayoritas typo sisa memang tidak akan pernah mencapai
model: `jahatt` (df=0), `diskonanya` (df=0), `mantapz` (df=0), `nyiapin` (df=0),
`padahan` (df=0), `isrewel` (df=1).

Yang masih lolos ke model dan layak dipertimbangkan di iterasi berikutnya:
`onlinenya` (df=51), `mna` (df=47), `turunin` (df=45), `gomartnya` (df=12),
`utamain` (df=5), `kbm` (df=4).

Tiga keterbatasan struktural yang tidak diselesaikan dan dinyatakan apa adanya:

1. **Angka dibuang secara global.** Aturan sempit ditambahkan untuk
   `bintang 1..5` dan `tiba2`, tetapi nominal harga, jam, dan kuantitas lain
   tetap hilang. Mengaktifkan angka secara global akan memasukkan ribuan nominal
   sebagai fitur.
2. **Normalisasi frasa bersifat kuratif, bukan umum.** 13 pola ditangani
   eksplisit; penggabungan token terpisah lain (`di batalkan`, `ke lamaan`)
   tidak tertangani.
3. **Umpatan tersamar** hanya ditangani untuk satu pola (`b#ngasd`).

**Umpan balik yang dijadwalkan:** Fase 4 (T-4.5) mengekstrak 20 fitur berbobot
tertinggi per kelas dan mewajibkan pertanyaan "apakah ini istilah domain atau
artefak preprocessing?" dijawab tertulis. Bila artefak muncul di daftar itu,
iterasi kembali ke fase ini dengan bukti kuantitatif, bukan dugaan.

## 7. Status Gerbang

- **H-5 (kamus slang)** — ✅ lolos. 500/500 token diputuskan manusia.
- **H-6 (verifikasi sampel)** — ✅ lolos setelah 3 putaran, 275 sampel diperiksa.
