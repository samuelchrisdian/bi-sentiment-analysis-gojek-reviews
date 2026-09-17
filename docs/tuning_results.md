# HASIL TUNING — FASE 4 (T-4.1 & T-4.2)

Seluruh angka berasal dari `ml/src/tune.py` yang dijalankan, bukan estimasi.
Berkas mentah: `docs/tables/gridsearch_results.csv` (24 kombinasi),
`ml/artifacts/best_params.json`, baris `*_tuned` di `docs/tables/model_metrics.csv`.

## 1. Protokol

`GridSearchCV` dengan `scoring="f1_macro"` — bukan `accuracy`. Baseline kelas
mayoritas sudah memperoleh accuracy 0,723 tanpa mempelajari apa pun, sehingga
mengoptimalkan accuracy berarti mengoptimalkan ke arah yang salah.

Validasi: `StratifiedKFold(n_splits=5, shuffle=True, random_state=42)` pada
45.614 baris training hasil deduplikasi. Total 120 *fit* untuk empat model.

**Vectorizer berada di dalam `Pipeline`.** Ini diverifikasi di kode
([ml/src/tune.py:61-64](../ml/src/tune.py#L61-L64)): TF-IDF di-*fit* ulang pada
4/5 data di setiap *fold*. Mem-*fit* TF-IDF sekali di luar CV akan membuat
vocabulary dan bobot IDF ikut dipelajari dari fold validasi — kebocoran yang
menaikkan skor CV tanpa menaikkan kinerja sebenarnya, dan yang sering terlewat
karena tidak menimbulkan error apa pun.

Grid sengaja kecil (4–8 kombinasi per model). Seluruh proses selesai dalam
50 detik pada 16 inti.

## 2. Parameter Terpilih

| Model | Grid | Terpilih | macro-F1 CV | std | selisih train−test |
|-------|------|----------|-------------|-----|--------------------|
| LinearSVC | C × class_weight (8) | `C=0.1, class_weight="balanced"` | 0,9099 | 0,0022 | 0,0226 |
| LogisticRegression | C × class_weight (8) | `C=5.0, class_weight="balanced"` | 0,9085 | 0,0030 | 0,0499 |
| MultinomialNB | alpha (4) | `alpha=0.5` | 0,9057 | 0,0025 | 0,0205 |
| ComplementNB | alpha (4) | `alpha=0.5` | 0,8919 | 0,0016 | 0,0204 |

## 3. Temuan Utama Tuning — Kurva Regularisasi LinearSVC

Kolom `mean_train_score` bukan pelengkap. Ia yang menjelaskan mengapa LinearSVC
naik setelah tuning:

| C | class_weight | train | test (CV) | selisih |
|---|--------------|-------|-----------|---------|
| 0,1 | balanced | 0,9325 | **0,9099** | **0,023** |
| 0,5 | balanced | 0,9611 | 0,9090 | 0,052 |
| 1,0 | balanced | 0,9744 | 0,9040 | 0,070 |
| 5,0 | balanced | 0,9932 | 0,8879 | **0,105** |

Pada `C=5` model menghafal training set (macro-F1 0,993) dan kehilangan 10,5
poin saat digeneralisasi. Nilai default Fase 3 adalah `C=1.0` — sudah berada di
wilayah *overfitting*, dengan selisih 7,0 poin. Tuning memindahkannya ke `C=0.1`,
yaitu regularisasi **sepuluh kali lebih kuat** dari default.

Ini temuan yang layak dibahas: pada TF-IDF 30.000 fitur dengan 45.614 dokumen,
jumlah fitur mendekati jumlah contoh per kelas, sehingga model linear dengan
regularisasi lemah dapat memisahkan training set hampir sempurna tanpa
mempelajari pola yang berlaku umum.

**Catatan kejujuran pada LogisticRegression:** parameter terpilih `C=5.0`
(CV 0,90849) hanya unggul **0,00015** dari `C=1.0` (CV 0,90834) — jauh di dalam
satu simpangan baku (0,0030). Pemilihan itu praktis hasil derau, sementara
`C=1.0` memiliki selisih train−test setengahnya (0,022 vs 0,050). Bila
LogisticRegression dipilih sebagai model produksi di H-10, `C=1.0` adalah
pilihan yang lebih dapat dipertahankan meski bukan peringkat 1 versi
`GridSearchCV`. Angka ini dilaporkan, bukan dibulatkan menjadi "tuning berhasil".

## 4. Default vs Tuned pada Test Set

Baris Fase 3 tidak ditimpa; keduanya hidup berdampingan di `model_metrics.csv`.

### Set `full` (19.294 baris)

| Model | macro-F1 default | macro-F1 tuned | Δ | recall neg default | recall neg tuned | Δ |
|-------|------------------|----------------|---|--------------------|------------------|---|
| LinearSVC | 0,9301 | **0,9341** | **+0,0040** | 0,9168 | **0,9370** | **+0,0202** |
| LogisticRegression | 0,9336 | 0,9338 | +0,0001 | 0,9316 | 0,9267 | −0,0049 |
| MultinomialNB | 0,9279 | 0,9296 | +0,0017 | 0,9400 | 0,9428 | +0,0028 |
| ComplementNB | 0,9154 | 0,9153 | −0,0001 | 0,9557 | 0,9553 | −0,0004 |

### Set `informative_ge5w` (8.696 baris)

| Model | macro-F1 default | macro-F1 tuned | Δ | recall neg tuned |
|-------|------------------|----------------|---|------------------|
| LogisticRegression | 0,9078 | 0,9071 | −0,0006 | 0,9452 |
| LinearSVC | 0,9000 | **0,9066** | **+0,0066** | 0,9570 |
| MultinomialNB | 0,8991 | 0,9016 | +0,0025 | 0,9635 |
| ComplementNB | 0,8986 | 0,8987 | +0,0001 | **0,9714** |

**Tuning hanya berarti untuk satu model.** LinearSVC naik 0,40 poin (`full`) dan
0,66 poin (`informative_ge5w`); tiga model lainnya bergerak ≤0,25 poin, yaitu
di dalam derau. Ini hasil yang wajar dan harus dinyatakan apa adanya: pada TF-IDF
dengan data sebesar ini, pilihan *hyperparameter* bukan faktor penentu — kecuali
ketika parameter default kebetulan berada di wilayah *overfitting*, yang persis
terjadi pada LinearSVC.

## 5. Posisi Akhir Keempat Model (tuned)

| Model | macro-F1 `full` | macro-F1 `informative` | recall neg `full` | recall neg `informative` | selisih set |
|-------|-----------------|------------------------|-------------------|--------------------------|-------------|
| LinearSVC | **0,9341** | 0,9066 | 0,9370 | 0,9570 | 2,75 poin |
| LogisticRegression | 0,9338 | **0,9071** | 0,9267 | 0,9452 | 2,67 poin |
| MultinomialNB | 0,9296 | 0,9016 | 0,9428 | 0,9635 | 2,80 poin |
| ComplementNB | 0,9153 | 0,8987 | **0,9553** | **0,9714** | **1,66 poin** |

Selisih LinearSVC dengan LogisticRegression adalah **0,03 poin** pada `full`,
dan LogisticRegression justru unggul 0,05 poin pada `informative_ge5w`. Kedua
angka itu nol untuk tujuan praktis.

**Konsekuensi untuk kerangka keputusan Bagian 2.5:** syarat "LinearSVC unggul
macro-F1 ≥2 poin" **tidak terpenuhi** — selisihnya 0,03 poin, dua orde besaran
di bawah ambang. Cabang kedua yang berlaku: pilih model yang lebih sederhana dan
lebih mudah dijelaskan. Keputusannya tetap wewenang manusia (gerbang H-10) dan
ditulis di `docs/model_decision.md`.

Bahan tambahan untuk keputusan itu: bila prioritas adalah **recall kelas
negatif** sebagaimana ditetapkan Bagian 2.3, ComplementNB tetap memimpin di
kedua set (0,9553 / 0,9714) meski macro-F1-nya terendah, dan penurunan antar-set
miliknya terkecil (1,66 poin). Yang dikorbankan adalah presisi negatif (0,818
vs 0,877 LinearSVC) — artinya lebih banyak ulasan positif ikut tertandai sebagai
keluhan. Keduanya adalah biaya nyata dengan arah berlawanan; tidak ada angka
tunggal yang menyelesaikannya.
