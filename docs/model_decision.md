# KEPUTUSAN MODEL PRODUKSI

Kerangka: Bagian 2.5 `tech-architecture-development-plan.md` · Data: scraping
Google Play lima tahun (526.322 ulasan, Oktober 2021 – September 2026).

> ## ✅ Model produksi ditetapkan — 11 Oktober 2026
>
> Model produksi: **LogisticRegression** (`C=1.0, class_weight="balanced"`).
> Keputusan ini mengikuti kerangka keputusan Bagian 2.5 apa adanya dan
> dinyatakan pemilik proyek. Artefaknya ada di `ml/artifacts/`.
>
> Versi berbasis data Kaggle diarsipkan di `archive/kaggle-v1/model_decision.md`.
> Pada data Kaggle, kerangka yang sama menghasilkan model dan parameter yang sama.

---

## 1. Kerangka Keputusan dan Apakah Syaratnya Terpenuhi

Bagian 2.5 menetapkan dua cabang:

| Cabang | Syarat | Terpenuhi? |
|--------|--------|------------|
| (a) LinearSVC jadi model produksi + `CalibratedClassifierCV` | LinearSVC unggul macro-F1 **≥2 poin** | ❌ **Tidak.** Unggul **0,08 poin** dari LogisticRegression pada set `full` (0,9270 vs 0,9261) dan **0,07 poin** pada `informative_ge5w` (0,8958 vs 0,8951). |
| (b) Pilih ComplementNB atau LogisticRegression, yaitu model yang lebih sederhana dan mudah dijelaskan | Selisih **<2 poin** | ✅ **Ya.** |

**Cabang (b) yang berlaku.** Keunggulan LinearSVC 25 kali lebih kecil dari
ambangnya, jadi ini bukan kasus batas.

**Pilihan di dalam cabang (b).** Kerangka menyisakan dua kandidat. Di antara
keduanya, LogisticRegression unggul macro-F1 pada **kedua** set evaluasi:
0,9261 vs 0,9037 pada `full` (+2,24 poin) dan 0,8951 vs 0,8833 pada
`informative_ge5w` (+1,18 poin). Karena itu yang dipilih adalah LogisticRegression.

## 2. Angka Lengkap Keempat Kandidat (tuned)

Data uji `full`: 100.842 ulasan (29.185 negatif, 71.657 positif). Data uji
`informative_ge5w`: 45.069 ulasan dengan `word_count` ≥ 5. Data latih: 222.308
ulasan setelah deduplikasi.

| Model | macro-F1 `full` | macro-F1 `informative` | recall neg `full` | recall neg `informative` | presisi neg `full` | selisih antar-set | n salah | latih |
|-------|-----------------|------------------------|-------------------|--------------------------|--------------------|-------------------|---------|-------|
| LinearSVC | **0,9270** | **0,8958** | 0,9237 | 0,9484 | 0,8727 | 3,12 poin | **6.161** | 9,3 s |
| LogisticRegression | 0,9261 | 0,8951 | 0,9192 | 0,9442 | **0,8742** | 3,10 poin | 6.220 | 4,8 s |
| MultinomialNB | 0,9185 | 0,8838 | 0,9346 | 0,9592 | 0,8434 | 3,47 poin | 6.973 | 6,7 s |
| ComplementNB | 0,9037 | 0,8833 | **0,9414** | **0,9602** | 0,8050 | **2,04 poin** | 8.365 | 6,1 s |
| *baseline mayoritas* | *0,4154* | *0,3062* | *0,0000* | *0,0000* | *0,0000* | — | *29.185* | — |

Sumber: `docs/tables/model_metrics.csv` (baris `*_tuned`, `dedup_training=True`),
`ml/artifacts/reports/*_full.json`.

Rentang macro-F1 keempat varian adalah 2,33 poin (0,9037–0,9270). Tiga model
teratas berada dalam rentang 0,85 poin.

### 2.1 Bentuk kesalahan, yang tidak terlihat dari macro-F1

Jumlah kesalahan yang hampir sama dapat berarti biaya operasional yang berbeda.
Confusion matrix pada set `full`:

| Model | keluhan **lolos** triase (FN) | alarm **palsu** (FP) | total salah |
|-------|------------------------------|----------------------|-------------|
| LinearSVC | 2.227 | 3.934 | 6.161 |
| LogisticRegression | 2.359 | **3.861** | 6.220 |
| MultinomialNB | 1.910 | 5.063 | 6.973 |
| ComplementNB | **1.710** | 6.655 | 8.365 |

LinearSVC dan LogisticRegression hampir identik. Kesalahan keduanya beririsan
0,937 (Jaccard), dan selisih totalnya 59 ulasan dari 100.842.
LogisticRegression meloloskan 132 keluhan lebih banyak, tetapi menghasilkan 73
alarm palsu lebih sedikit.

### 2.2 Koreksi dari analisis kesalahan manual: sebagian besar "alarm palsu" ternyata prediksi yang benar

Tabel 2.1 memperlakukan setiap FP sebagai biaya dan setiap FN sebagai kerugian.
Pemeriksaan manual atas 50 kesalahan `linear_svc_tuned`
(`docs/tables/error_analysis_50_reviewed.csv`) menunjukkan asumsi itu tidak
simetris:

| Arah kesalahan | n sampel | di antaranya label keliru pengguna | artinya |
|----------------|----------|-----------------------------------|---------|
| Alarm palsu (FP) | 30 | **23 (76,7%)** | prediksi model **benar**; yang keliru adalah bintang 4–5 dari pengguna |
| Keluhan lolos (FN) | 20 | 2 (10,0%) | hampir seluruhnya kesalahan model yang sebenarnya |

**Tiga perempat "alarm palsu" adalah ulasan berisi keluhan yang diberi bintang
4–5 oleh penulisnya.** Untuk triase keluhan, baris-baris itu justru temuan yang
diinginkan. Sebaliknya, keluhan yang lolos hampir seluruhnya kesalahan model
sungguhan.

Pertukaran ComplementNB vs LogisticRegression, dihitung ulang dengan proporsi ini:

| Besaran | Hitungan naif | Setelah koreksi |
|---------|---------------|-----------------|
| Keluhan tambahan yang tertangkap ComplementNB | 649 | ≈584 *(90% dari 649 adalah keluhan sungguhan)* |
| Alarm palsu tambahan ComplementNB | 2.794 | **≈651** *(hanya 23,3% dari 2.794 benar-benar palsu)* |
| **Rasio pertukaran** | 1 : 4,3 | **≈1 : 1,1** |

**Peringatan atas angka ini.** Proporsi 76,7% dan 10,0% diukur pada sampel
kesalahan **`linear_svc_tuned`**, lalu diterapkan ke selisih ComplementNB. Model
ComplementNB kesalahannya hanya beririsan 0,520 (Jaccard) dengan LinearSVC.
Selang kepercayaan Wilson 95% juga lebar: FP 59,1%–88,2%, FN 2,8%–30,1%. Yang
dapat dinyatakan dengan aman adalah **arahnya**: biaya sebenarnya dari recall
negatif yang tinggi jauh lebih rendah daripada yang tampak pada confusion matrix
mentah. Angka pastinya tidak dapat dinyatakan dengan aman.

## 3. Ciri Ketiga Kandidat Utama

Selisih macro-F1 LinearSVC dan LogisticRegression (0,08 poin) nol untuk tujuan
praktis. Yang membedakan ketiga kandidat adalah hal-hal di luar angka itu.

### (a) LogisticRegression — paling sederhana secara operasional

- **Untung:** `predict_proba` **bawaan**. Tidak perlu `CalibratedClassifierCV`,
  pelatihan ulang 5×, atau artefak tambahan. Endpoint `/api/predict`
  mengembalikan probabilitas langsung dari model yang dievaluasi.
- **Untung:** presisi negatif tertinggi (0,8742), sehingga alarm palsunya paling sedikit.
- **Untung:** koefisien = log-odds per kata, dapat ditampilkan langsung.
- **Rugi:** recall negatif terendah di antara keempatnya (0,9192 `full`).
  Ini biaya nyata: 2.359 keluhan lolos triase, dibanding 2.227 pada LinearSVC
  dan 1.710 pada ComplementNB.

### (b) ComplementNB — paling aman untuk triase keluhan

- **Untung:** recall negatif tertinggi di **kedua** set (0,9414 / 0,9602).
- **Untung:** paling tahan artefak panjang teks, dengan selisih antar-set terkecil
  (2,04 poin vs 3,10–3,47 poin pada model lain).
- **Rugi:** macro-F1 terendah (0,9037) dan presisi negatif 0,8050, yaitu
  **8.365 kesalahan, 36% lebih banyak** dari LinearSVC. Hampir seluruhnya berupa
  ulasan positif yang ditandai sebagai keluhan.

### (c) LinearSVC — unggul tipis pada satu angka, termahal secara operasional

- **Untung:** macro-F1 tertinggi pada kedua set, dengan selisih 0,07–0,08 poin.
- **Rugi:** **tidak punya `predict_proba`.** Membutuhkan `CalibratedClassifierCV`,
  sehingga yang dipakai di produksi bukan persis model yang metriknya dilaporkan.

## 4. Keputusan

**Model produksi:** **LogisticRegression**

**Parameter:** `C=1.0, class_weight="balanced"`, TF-IDF unigram+bigram
(`min_df=3`, `max_features=30000`, `sublinear_tf=True`), `solver="liblinear"`,
`random_state=42`.

**Dasar keputusan:** kerangka Bagian 2.5 diterapkan apa adanya. Keputusan
diambil di dalam cabang (b): dari dua kandidat cabang itu, model dengan
macro-F1 tertinggi pada kedua set evaluasi.

**Dinyatakan oleh / tanggal:** pemilik proyek, 11 Oktober 2026.

### 4.1 Alasan

1. **Syarat cabang (a) tidak terpenuhi.** LinearSVC hanya unggul 0,08 poin, jauh
   di bawah ambang 2 poin.
2. **LogisticRegression mengungguli ComplementNB pada kedua set evaluasi**, dengan
   selisih +2,24 poin (`full`) dan +1,18 poin (`informative_ge5w`).
3. **`predict_proba` bawaan.** Model yang metriknya dilaporkan adalah objek yang
   sama dengan yang melayani `/api/predict`.
4. **Koefisien per kata dapat ditafsirkan langsung**, sehingga mendukung
   interpretasi fitur tanpa perkakas tambahan.

**Biaya yang diterima secara sadar:** recall negatif 0,9192 pada `full`, yang
terendah di antara keempat kandidat. Dibanding ComplementNB, **649 keluhan lebih
banyak lolos triase** (FN 1.710 → 2.359), ditukar dengan **2.794 alarm palsu
lebih sedikit** (FP 6.655 → 3.861). Setelah koreksi Bagian 2.2, pertukaran
sebenarnya ≈584 keluhan sungguhan versus ≈651 alarm palsu sungguhan, kira-kira
**1 : 1,1**. Konsekuensi ini dicatat sebagai keterbatasan, bukan diabaikan.

### 4.2 Parameter: aturan satu simpangan baku

Parameter dipilih dengan **aturan satu simpangan baku** (*one-standard-error
rule*, Breiman et al., 1984). Aturan ini memilih model paling sederhana, yaitu
regularisasi terkuat pada model linear, yang skornya masih berada dalam satu
simpangan baku dari yang terbaik.

Pada data scraping, pemenang `GridSearchCV` dan hasil aturan 1-SE **sama**,
yaitu `C=1.0, class_weight="balanced"`:

| Besaran | Nilai |
|---------|-------|
| CV macro-F1 (5-fold) | 0,8992 |
| Simpangan baku CV | 0,0008 |
| Ambang 1-SE | 0,8984 |
| Kandidat dalam ambang 1-SE | 2 (`C=1.0` dengan dan tanpa `class_weight="balanced"`) |
| Selisih train−test CV | 0,0146 |
| macro-F1 test `full` / `informative_ge5w` | 0,9261 / 0,8951 |

`C=1.0, class_weight="balanced"` adalah **konfigurasi default Fase 3**. Untuk
LogisticRegression, seluruh proses tuning berakhir kembali di titik awalnya,
sama seperti pada data Kaggle. Ini bukti kuantitatif bahwa pada TF-IDF dengan
data sebesar ini, *hyperparameter* bukan faktor penentu kinerja. Baris
`logistic_regression`, `logistic_regression_tuned`, dan
`logistic_regression_final` di `model_metrics.csv` karenanya identik.

Implementasi: `ml/src/tune.py::pilih_1se()`. Hasilnya tersimpan di
`ml/artifacts/best_params.json` pada kunci `seleksi_1se` dan dipakai
`ml/src/finalize.py` secara default (`--seleksi 1se`).

### 4.3 Konsekuensi untuk rumusan masalah

Perbandingan dalam RM1 mencakup **tiga keluarga algoritma dengan empat varian**:
Naive Bayes (ComplementNB, MultinomialNB), SVM (LinearSVC), dan Logistic
Regression. Penyebutan di laporan harus presisi, yaitu "tiga keluarga algoritma
dengan empat varian", bukan "tiga model", karena tabel hasil memuat empat baris.

Temuan untuk RM1: **tiga varian teratas berada dalam rentang 0,85 poin** dan
model paling sederhana setara dengan yang paling kompleks. Ini ditulis sebagai
temuan yang sah, bukan kegagalan eksperimen. Sesuai arahan dosen, perbandingan
model **tidak** dijadikan kebaruan penelitian.

### 4.4 Artefak

Dijalankan `python -m ml.src.finalize logistic_regression` (seleksi 1-SE):

| Artefak | Ukuran | Catatan |
|---------|--------|---------|
| `ml/artifacts/vectorizer.joblib` | 1,2 MB | TF-IDF ter-fit pada 222.308 baris latih |
| `ml/artifacts/model_final.joblib` | 235 KB | LogisticRegression `C=1.0` |
| `ml/artifacts/label_encoder.joblib` | 383 B | 0=negatif, 1=positif |
| `ml/artifacts/MANIFEST.json` | 4,6 KB | hash data, snapshot config, versi pustaka, seluruh metrik, `random_state` |

**`model_calibrated.joblib` tidak dibuat**, karena tidak diperlukan.

Uji muat ulang di proses terpisah pada 10 sampel (`ml/artifacts/_uji_muat_ulang.json`)
lolos dengan prediksi identik.
