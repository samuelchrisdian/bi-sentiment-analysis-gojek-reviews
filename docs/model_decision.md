# KEPUTUSAN MODEL PRODUKSI

**Fase 4, T-4.8** · Kerangka: Bagian 2.5 `tech-architecture-development-plan.md`

> ## ⛔ STATUS: GERBANG H-10 TERBUKA — MENUNGGU KEPUTUSAN MANUSIA
>
> Bagian 5 dokumen ini **sengaja kosong**. Bagian 1–4 berisi seluruh angka yang
> mendasari keputusan, plus rekomendasi agent sebagai bahan pertimbangan —
> bukan sebagai keputusan. `model_final.joblib` belum ditetapkan dan
> `ml/src/finalize.py` belum dijalankan terhadap `ml/artifacts/`.

---

## 1. Kerangka Keputusan dan Apakah Syaratnya Terpenuhi

Bagian 2.5 menetapkan dua cabang:

| Cabang | Syarat | Terpenuhi? |
|--------|--------|------------|
| (a) LinearSVC jadi model produksi + `CalibratedClassifierCV` | LinearSVC unggul macro-F1 **≥2 poin** | ❌ **Tidak.** Unggul **0,03 poin** dari LogisticRegression pada set `full`, dan **kalah 0,05 poin** pada `informative_ge5w`. |
| (b) Pilih ComplementNB atau LogisticRegression — model yang lebih sederhana dan mudah dijelaskan | Selisih **<2 poin** | ✅ **Ya.** Rentang keempat model hanya 1,88 poin (0,9153–0,9341). |

**Cabang (b) yang berlaku.** Syarat cabang (a) meleset dua orde besaran dari
ambangnya; ini bukan kasus batas.

## 2. Angka Lengkap Keempat Kandidat (tuned)

| Model | macro-F1 `full` | macro-F1 `informative` | recall neg `full` | recall neg `informative` | presisi neg `full` | selisih antar-set | n salah | latih |
|-------|-----------------|------------------------|-------------------|--------------------------|--------------------|-------------------|---------|-------|
| LinearSVC | **0,9341** | 0,9066 | 0,9370 | 0,9570 | 0,8769 | 2,75 poin | 1.040 | 1,44 s |
| LogisticRegression | 0,9338 | **0,9071** | 0,9267 | 0,9452 | **0,8845** | 2,67 poin | 1.039 | 1,57 s |
| MultinomialNB | 0,9296 | 0,9016 | 0,9428 | 0,9635 | 0,8610 | 2,80 poin | 1.120 | 1,22 s |
| ComplementNB | 0,9153 | 0,8987 | **0,9553** | **0,9714** | 0,8182 | **1,66 poin** | 1.374 | 1,19 s |
| *baseline mayoritas* | *0,4196* | *0,3173* | *0,0000* | *0,0000* | *0,0000* | — | *5.347* | — |

Sumber: `docs/tables/model_metrics.csv` (baris `*_tuned`), `docs/error_analysis.md` §4.

### 2.1 Bentuk Kesalahannya — yang tidak terlihat dari macro-F1

Jumlah kesalahan yang hampir sama dapat berarti biaya operasional yang sangat
berbeda. Confusion matrix pada set `full` (19.294 baris; 5.347 negatif):

| Model | keluhan **lolos** triase (FN) | alarm **palsu** (FP) | total salah |
|-------|------------------------------|----------------------|-------------|
| LinearSVC | 337 | 703 | 1.040 |
| LogisticRegression | **392** | **647** | 1.039 |
| MultinomialNB | 306 | 814 | 1.120 |
| ComplementNB | **239** | **1.135** | 1.374 |

LinearSVC dan LogisticRegression menghasilkan jumlah kesalahan yang praktis
identik (1.040 vs 1.039) tetapi **komposisi yang berbeda**: LogisticRegression
meloloskan 55 keluhan lebih banyak dan menghasilkan 56 alarm palsu lebih sedikit.
Inilah perbedaan sebenarnya antara keduanya — bukan 0,03 poin macro-F1.

## 3. Tiga Kandidat Nyata dan Biayanya

Perbedaan macro-F1 antara LinearSVC dan LogisticRegression (0,03 poin = 6 baris
dari 19.294) nol untuk tujuan praktis. Yang membedakan ketiga kandidat adalah
hal-hal di luar satu angka itu.

### (a) LogisticRegression — paling sederhana secara operasional

- **Untung:** `predict_proba` **bawaan**. Tidak perlu `CalibratedClassifierCV`,
  tidak perlu `model_calibrated.joblib`, tidak perlu 5× pelatihan ulang, tidak
  ada lapisan tambahan yang harus dijelaskan di bab metodologi. Endpoint
  `/api/predict` mengembalikan probabilitas langsung dari model yang dievaluasi
   — bukan dari pembungkusnya.
- **Untung:** macro-F1 tertinggi pada `informative_ge5w` (0,9071) — set yang
  lebih sulit dan lebih relevan secara operasional, karena di situlah kesalahan
  sebenarnya berada (77% kesalahan terjadi pada ulasan ≥5 kata).
- **Untung:** presisi negatif tertinggi (0,8845) → alarm palsu paling sedikit.
- **Rugi:** recall negatif terendah di antara keempatnya (0,9267 `full`).
  **Ini biaya yang nyata:** 392 keluhan lolos triase versus 337 pada LinearSVC
  dan 239 pada ComplementNB.
- **Catatan parameter:** `GridSearchCV` memilih `C=5.0`, tetapi unggulnya hanya
  0,00015 dari `C=1.0` — jauh di dalam satu simpangan baku (0,0030) — sedangkan
  `C=1.0` punya selisih train−test setengahnya (0,022 vs 0,050). Bila kandidat
  ini dipilih, **`C=1.0` lebih dapat dipertahankan** (lihat `docs/tuning_results.md` §3).

### (b) ComplementNB — paling aman untuk triase keluhan

- **Untung:** recall negatif tertinggi di **kedua** set (0,9553 / 0,9714).
  Bagian 2.3 menetapkan recall negatif sebagai prioritas karena keluhan yang
  lolos triase adalah kegagalan bisnis langsung. Pada kriteria itu, ComplementNB
  menang telak.
- **Untung:** paling tahan artefak panjang teks — selisih antar-set terkecil
  (1,66 poin vs 2,67–2,80 poin model lain).
- **Untung:** `predict_proba` bawaan, pelatihan tercepat, model paling sederhana
  yang dapat dijelaskan (log-ratio per kata, tanpa optimisasi iteratif).
- **Rugi:** macro-F1 terendah (0,9153) dan presisi negatif 0,8182 →
  **1.374 kesalahan, 32% lebih banyak** dari LinearSVC, hampir seluruhnya berupa
  ulasan positif yang ditandai sebagai keluhan. Beban peninjauan manual naik
  sebanding.

### (c) LinearSVC — unggul tipis pada satu angka, termahal secara operasional

- **Untung:** macro-F1 `full` tertinggi (0,9341), dan model yang paling diuntungkan
  tuning (+0,40 poin `full`, +2,02 poin recall negatif).
- **Rugi:** **tidak punya `predict_proba`.** Membutuhkan `CalibratedClassifierCV`
  (5× pelatihan ulang, artefak tambahan 1,2 MB), sehingga yang dipakai di
  produksi bukan persis model yang metriknya dilaporkan di tabel — nuansa yang
  harus dijelaskan di laporan.
- **Rugi:** keunggulannya 0,03 poin, dan hilang pada set yang lebih sulit.
  Membayar kompleksitas kalibrasi untuk selisih sebesar itu sulit dibenarkan.

## 4. Rekomendasi Agent (bahan pertimbangan, bukan keputusan)

**LogisticRegression dengan `C=1.0, class_weight="balanced"`** — dengan syarat
prioritas recall negatif diterima apa adanya pada 0,9267.

Alasannya, berurutan:

1. Cabang (b) kerangka 2.5 berlaku, dan cabang itu secara eksplisit meminta
   model yang lebih sederhana dan lebih mudah dijelaskan.
2. Probabilitas bawaan menghapus seluruh lapisan kalibrasi dari arsitektur.
   Model yang dilaporkan dan model yang dilayankan menjadi objek yang sama.
3. Ia unggul justru pada set evaluasi yang lebih sulit (`informative_ge5w`),
   dan di situlah kesalahan nyata berada.
4. Koefisien per kata dapat ditampilkan langsung — mendukung kebutuhan
   interpretabilitas Fase 4 tanpa perkakas tambahan.

**Alasan sah untuk memutuskan lain:** bila triase keluhan dinilai lebih penting
daripada beban alarm palsu, **ComplementNB** adalah pilihan yang benar, dan
argumennya kuat. Dibanding LogisticRegression, ia menangkap **153 keluhan lebih
banyak** (FN 392 → 239) dengan biaya **488 alarm palsu tambahan** (FP 647 →
1.135) — rasio pertukaran **1 keluhan terselamatkan per 3,2 alarm palsu
tambahan**.

Apakah pertukaran itu layak bergantung pada angka yang tidak ada di data ini:
berapa biaya satu keluhan pelanggan yang terlewat dibanding satu menit waktu
peninjau. Itu pertimbangan operasional, bukan statistik — dan karena itu bukan
keputusan agent.

## 5. Keputusan — ⛔ MENUNGGU H-10

**Model produksi terpilih:** *(diisi manusia)*

**Parameter:** *(diisi manusia)*

**Alasan keputusan:** *(diisi manusia — termasuk bila berbeda dari rekomendasi
Bagian 4, dan terutama bila berbeda)*

**Diputuskan oleh / tanggal:** *(diisi manusia)*

Setelah bagian ini terisi, jalankan:

```bash
python -m ml.src.finalize <nama_model>     # linear_svc | logistic_regression | complement_nb | multinomial_nb
```

Script itu menulis `vectorizer.joblib`, `model_final.joblib`,
`label_encoder.joblib`, `MANIFEST.json` (+ `model_calibrated.joblib` bila model
terpilih adalah LinearSVC) ke `ml/artifacts/`, lalu memverifikasi muat ulang di
proses baru pada 10 sampel uji. Jalur ini sudah diuji lewat `--dry-run`.
