# HASIL TUNING — FASE 4 (T-4.1 & T-4.2)

Seluruh angka berasal dari `ml/src/tune.py` yang dijalankan, bukan estimasi.
Data: scraping Google Play lima tahun (526.322 ulasan, Oktober 2021 –
September 2026). Berkas mentah: `docs/tables/gridsearch_results.csv`
(24 kombinasi), `ml/artifacts/best_params.json`, baris `*_tuned` di
`docs/tables/model_metrics.csv`.

## 1. Protokol

`GridSearchCV` dengan `scoring="f1_macro"`, bukan `accuracy`. Baseline kelas
mayoritas sudah memperoleh accuracy 0,711 tanpa mempelajari apa pun, sehingga
mengoptimalkan accuracy berarti mengoptimalkan ke arah yang salah.

Validasi: `StratifiedKFold(n_splits=5, shuffle=True, random_state=42)` pada
222.308 baris training hasil deduplikasi. Total 120 *fit* untuk empat model.

**Vectorizer berada di dalam `Pipeline`.** Ini diverifikasi di kode
([ml/src/tune.py:61-64](../ml/src/tune.py#L61-L64)): TF-IDF di-*fit* ulang pada
4/5 data di setiap *fold*. Mem-*fit* TF-IDF sekali di luar CV akan membuat
vocabulary dan bobot IDF ikut dipelajari dari fold validasi. Itu kebocoran yang
menaikkan skor CV tanpa menaikkan kinerja sebenarnya, dan sering terlewat karena
tidak menimbulkan error apa pun.

Grid sengaja kecil (4–8 kombinasi per model):

| Model | Grid | Waktu grid search |
|-------|------|-------------------|
| ComplementNB | `alpha` ∈ {0,1; 0,5; 1,0; 2,0} | 38,0 s |
| MultinomialNB | `alpha` ∈ {0,1; 0,5; 1,0; 2,0} | 34,3 s |
| LinearSVC | `C` ∈ {0,1; 0,5; 1,0; 5,0} × `class_weight` ∈ {None, balanced} | 78,1 s |
| LogisticRegression | `C` ∈ {0,1; 0,5; 1,0; 5,0} × `class_weight` ∈ {None, balanced} | 62,8 s |

Seluruh proses selesai dalam 213,1 detik (`n_jobs=-1`).

## 2. Parameter Terpilih

| Model | Grid | Terpilih (grid) | macro-F1 CV | std | selisih train−test |
|-------|------|-----------------|-------------|-----|--------------------|
| LinearSVC | C × class_weight (8) | `C=0.1, class_weight="balanced"` | 0,9004 | 0,0009 | 0,0147 |
| LogisticRegression | C × class_weight (8) | `C=1.0, class_weight="balanced"` | 0,8992 | 0,0008 | 0,0146 |
| MultinomialNB | alpha (4) | `alpha=0.5` | 0,8885 | 0,0016 | 0,0079 |
| ComplementNB | alpha (4) | `alpha=0.5` | 0,8761 | 0,0017 | 0,0081 |

Skor CV (≈0,90) lebih rendah daripada macro-F1 pada test `full` (0,93; Bagian
4). Ini sesuai dengan cara data dibagi. CV berjalan pada data latih yang sudah
dideduplikasi, yang hampir seimbang (49,3% negatif) dan tidak lagi memuat
ribuan pujian pendek berulang. Test `full` memuat duplikat itu, dan duplikat itu
mudah ditebak. Skor CV karena itu lebih dekat ke set `informative_ge5w`
(0,8951–0,8958 untuk model linear) daripada ke set `full`.

## 3. Temuan Utama Tuning — Kurva Regularisasi Model Linear

Kolom `mean_train_score` bukan pelengkap. Ia yang menjelaskan mengapa LinearSVC
naik setelah tuning:

**LinearSVC** (`class_weight="balanced"`):

| C | train | test (CV) | selisih |
|---|-------|-----------|---------|
| 0,1 | 0,9151 | **0,9004** | **0,015** |
| 0,5 | 0,9277 | 0,8969 | 0,031 |
| 1,0 | 0,9322 | 0,8923 | 0,040 |
| 5,0 | 0,9405 | 0,8781 | **0,062** |

**LogisticRegression** (`class_weight="balanced"`):

| C | train | test (CV) | selisih |
|---|-------|-----------|---------|
| 0,1 | 0,8925 | 0,8887 | 0,004 |
| 0,5 | 0,9073 | 0,8975 | 0,010 |
| 1,0 | 0,9138 | **0,8992** | 0,015 |
| 5,0 | 0,9273 | 0,8968 | 0,030 |

Pada LinearSVC, setiap pelemahan regularisasi menaikkan skor train dan
menurunkan skor CV. Pada `C=5` selisihnya 6,2 poin. Nilai default Fase 3
adalah `C=1.0`, yang sudah berada di sisi *overfitting* dengan selisih 4,0 poin.
Tuning memindahkannya ke `C=0.1`, yaitu regularisasi **sepuluh kali lebih kuat**
dari default, dengan selisih 1,5 poin.

LogisticRegression berperilaku lain: puncak CV-nya tepat di `C=1.0`, nilai
default. Regularisasi lebih kuat (`C=0.1`) menurunkan skor CV 1,0 poin
(*underfitting*), dan regularisasi lebih lemah (`C=5.0`) menggandakan selisih
train−test tanpa menaikkan skor CV.

Titik optimum `C` kedua model berbeda, sehingga satu nilai default yang sama
tidak bisa dianggap netral untuk keduanya. Yang penting untuk laporan adalah
hasil empirisnya: pada 222.308 dokumen dan 30.000 fitur, jarak *overfitting*
moderat (paling besar 6,2 poin), tetapi cukup untuk membuat default LinearSVC
bukan titik terbaiknya.

**`class_weight` praktis tidak berpengaruh.** Pada LinearSVC `C=0.1`, selisih
CV antara `balanced` dan `None` hanya 0,00004; pada LogisticRegression `C=1.0`,
0,0003. Keduanya jauh di dalam satu simpangan baku. Ini sejalan dengan data
latih yang setelah deduplikasi sudah hampir seimbang (49,3% negatif), sehingga
pembobotan kelas hampir tidak mengubah apa pun.

**`alpha` Naive Bayes juga praktis tidak berpengaruh.** Rentang skor CV keempat
nilai `alpha` hanya 0,0006 (ComplementNB) dan 0,0007 (MultinomialNB), lebih
kecil dari simpangan baku masing-masing (0,0017 dan 0,0016).

### 3.1 Aturan Satu Simpangan Baku (*one-standard-error rule*)

`GridSearchCV` memilih skor CV tertinggi tanpa memperhitungkan bahwa skor itu
sendiri punya ragam. Aturan 1-SE (Breiman et al., 1984) memilih model **paling
sederhana** yang skornya masih berada dalam satu simpangan baku dari yang
terbaik. Pada model linear, paling sederhana berarti regularisasi terkuat; pada
Naive Bayes, *smoothing* terkuat.

Diterapkan pada keempat model (`ml/src/tune.py::pilih_1se()`, hasil tersimpan di
`ml/artifacts/best_params.json` kunci `seleksi_1se`):

| Model | Pemenang grid | Pilihan 1-SE | Ambang 1-SE | Kandidat dalam ambang | Selisih train−test |
|-------|---------------|--------------|-------------|-----------------------|--------------------|
| LinearSVC | `C=0.1, balanced` | `C=0.1, balanced` *(sama)* | 0,8995 | 2 | 0,0147 → 0,0147 |
| **LogisticRegression** | `C=1.0, balanced` | **`C=1.0, balanced`** *(sama)* | 0,8984 | 2 | 0,0146 → 0,0146 |
| ComplementNB | `alpha=0.5` | `alpha=2.0` | 0,8744 | 4 | 0,0081 → 0,0065 |
| MultinomialNB | `alpha=0.5` | `alpha=2.0` | 0,8869 | 4 | 0,0079 → 0,0065 |

Pada kedua model linear, aturan 1-SE **mengonfirmasi** pemenang grid. Kandidat
dalam ambang hanya dua, yaitu `C` terbaik dengan dan tanpa
`class_weight="balanced"`, dan keduanya memiliki `C` yang sama. Aturan ini
karena itu bukan mekanisme yang selalu menggeser hasil.

Pada kedua Naive Bayes, keempat nilai `alpha` berada di dalam ambang, sehingga
aturan 1-SE memilih *smoothing* terkuat (`alpha=2.0`) dan menurunkan selisih
train−test dari ±0,008 ke 0,0065. Pilihan ini tidak dievaluasi pada test set.
Baris `*_tuned` untuk Naive Bayes memakai pemenang grid (`alpha=0.5`), dan
model produksi bukan Naive Bayes, sehingga pilihan 1-SE untuk Naive Bayes tidak
dipakai di tahap mana pun.

**Konsekuensi yang paling layak dilaporkan:** model produksi LogisticRegression
memakai `C=1.0, class_weight="balanced"` (`docs/model_decision.md` §4.2). Pemenang
grid search dan hasil aturan 1-SE sama, dan keduanya adalah **persis
konfigurasi default Fase 3**. Untuk LogisticRegression, seluruh proses tuning
berakhir kembali di titik awalnya. Ini bukan karena tuning gagal dijalankan,
melainkan karena pada TF-IDF dengan data sebesar ini *hyperparameter* memang
bukan faktor penentu. Itu temuan, bukan kekosongan. Baris
`logistic_regression`, `logistic_regression_tuned`, dan
`logistic_regression_final` di `model_metrics.csv` karenanya identik.

## 4. Default vs Tuned pada Test Set

Baris Fase 3 tidak ditimpa; keduanya hidup berdampingan di `model_metrics.csv`.

### Set `full` (100.842 baris)

| Model | macro-F1 default | macro-F1 tuned | Δ | recall neg default | recall neg tuned | Δ |
|-------|------------------|----------------|---|--------------------|------------------|---|
| LinearSVC | 0,9228 | **0,9270** | **+0,0042** | 0,9071 | **0,9237** | **+0,0166** |
| LogisticRegression | 0,9261 | 0,9261 | 0,0000 | 0,9192 | 0,9192 | 0,0000 |
| MultinomialNB | 0,9183 | 0,9185 | +0,0002 | 0,9337 | 0,9346 | +0,0008 |
| ComplementNB | 0,9036 | 0,9037 | +0,0001 | 0,9409 | 0,9414 | +0,0005 |

### Set `informative_ge5w` (45.069 baris)

| Model | macro-F1 default | macro-F1 tuned | Δ | recall neg tuned |
|-------|------------------|----------------|---|------------------|
| LinearSVC | 0,8890 | **0,8958** | **+0,0068** | 0,9484 |
| LogisticRegression | 0,8951 | 0,8951 | 0,0000 | 0,9442 |
| MultinomialNB | 0,8836 | 0,8838 | +0,0002 | 0,9592 |
| ComplementNB | 0,8831 | 0,8833 | +0,0001 | **0,9602** |

**Tuning hanya berarti untuk satu model.** LinearSVC naik 0,42 poin (`full`) dan
0,68 poin (`informative_ge5w`), dan recall negatifnya naik 1,66 poin. Tiga model
lainnya bergerak ≤0,02 poin, yaitu di dalam derau. LogisticRegression tidak
bergerak sama sekali karena parameter terpilihnya sama dengan default. Ini hasil
yang wajar dan harus dinyatakan apa adanya: pada TF-IDF dengan data sebesar ini,
pilihan *hyperparameter* bukan faktor penentu, kecuali ketika parameter default
kebetulan berada di sisi *overfitting*, yang persis terjadi pada LinearSVC.

## 5. Posisi Akhir Keempat Model (tuned)

| Model | macro-F1 `full` | macro-F1 `informative` | recall neg `full` | recall neg `informative` | presisi neg `full` | selisih set |
|-------|-----------------|------------------------|-------------------|--------------------------|--------------------|-------------|
| LinearSVC | **0,9270** | **0,8958** | 0,9237 | 0,9484 | 0,8727 | 3,12 poin |
| LogisticRegression | 0,9261 | 0,8951 | 0,9192 | 0,9442 | **0,8742** | 3,10 poin |
| MultinomialNB | 0,9185 | 0,8838 | 0,9346 | 0,9592 | 0,8434 | 3,47 poin |
| ComplementNB | 0,9037 | 0,8833 | **0,9414** | **0,9602** | 0,8050 | **2,04 poin** |

Selisih LinearSVC dengan LogisticRegression adalah **0,08 poin** pada `full`
dan 0,07 poin pada `informative_ge5w`. Kedua angka itu nol untuk tujuan
praktis.

**Konsekuensi untuk kerangka keputusan Bagian 2.5:** syarat "LinearSVC unggul
macro-F1 ≥2 poin" **tidak terpenuhi**. Selisihnya 0,08 poin, 25 kali lebih kecil
dari ambang. Cabang kedua yang berlaku: pilih model yang lebih sederhana dan
lebih mudah dijelaskan. Di antara dua kandidat cabang itu, LogisticRegression
mengungguli ComplementNB pada kedua set (+2,24 poin `full`, +1,18 poin
`informative_ge5w`). Model produksi yang ditetapkan adalah
**LogisticRegression `C=1.0, class_weight="balanced"`**; keputusan dan
alasannya ditulis di `docs/model_decision.md`.

Bahan pertimbangan yang tetap dicatat: bila prioritas adalah **recall kelas
negatif** sebagaimana ditetapkan Bagian 2.3, ComplementNB memimpin di kedua set
(0,9414 / 0,9602) meski macro-F1-nya terendah, dan penurunan antar-set miliknya
terkecil (2,04 poin). Yang dikorbankan adalah presisi negatif (0,8050 vs 0,8742
LogisticRegression), artinya lebih banyak ulasan positif ikut tertandai sebagai
keluhan. Analisis kesalahan manual menunjukkan sebagian besar "alarm palsu" itu
sebenarnya keluhan yang diberi bintang 4–5 (`docs/error_analysis.md` §3.1), jadi
biaya sebenarnya dari recall tinggi lebih rendah daripada yang tampak. Keduanya
tetap biaya nyata dengan arah berlawanan, dan tidak ada angka tunggal yang
menyelesaikannya (`docs/model_decision.md` §2.2).
