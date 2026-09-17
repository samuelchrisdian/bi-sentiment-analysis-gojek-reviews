# KEPUTUSAN MODEL PRODUKSI

**Fase 4, T-4.8** · Kerangka: Bagian 2.5 `tech-architecture-development-plan.md`

> ## ✅ GERBANG H-10 DILEWATI — 17 September 2026
>
> Model produksi: **LogisticRegression** (`C=1.0, class_weight="balanced"`),
> dinyatakan pemilik proyek. Artefak sudah ditetapkan di `ml/artifacts/`.
> Keputusan lengkap beserta konsekuensinya ada di Bagian 5.

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
| *LogisticRegression `C=1.0` (model final, §5.2)* | *366* | *678* | *1.044* |

LinearSVC dan LogisticRegression menghasilkan jumlah kesalahan yang praktis
identik (1.040 vs 1.039) tetapi **komposisi yang berbeda**: LogisticRegression
meloloskan 55 keluhan lebih banyak dan menghasilkan 56 alarm palsu lebih sedikit.
Inilah perbedaan sebenarnya antara keduanya — bukan 0,03 poin macro-F1.

### 2.2 Koreksi dari H-7: dua pertiga "alarm palsu" ternyata prediksi yang benar

Tabel 2.1 memperlakukan setiap FP sebagai biaya dan setiap FN sebagai kerugian.
Pemeriksaan manual H-7 menunjukkan asumsi itu salah, dan salahnya tidak simetris
(`docs/error_analysis.md` §3.1–3.2, sampel 50 kesalahan `linear_svc_tuned`):

| Arah kesalahan | n sampel | di antaranya label keliru pengguna | artinya |
|----------------|----------|-----------------------------------|---------|
| Alarm palsu (FP) | 34 | **22 (64,7%)** | prediksi model **benar**; bintang 4–5★ yang keliru |
| Keluhan lolos (FN) | 16 | 2 (12,5%) | hampir seluruhnya kesalahan model yang sebenarnya |

**Dua pertiga "alarm palsu" adalah ulasan berisi keluhan yang diberi bintang
4–5★ oleh penulisnya.** Untuk triase keluhan, baris-baris itu justru temuan yang
diinginkan — bukan gangguan. Sebaliknya, keluhan yang lolos hampir seluruhnya
kesalahan model sungguhan.

Konsekuensinya, pertukaran ComplementNB vs LogisticRegression di Bagian 4 perlu
dihitung ulang dengan proporsi ini:

| Besaran | Hitungan naif | Setelah koreksi H-7 |
|---------|---------------|---------------------|
| Keluhan tambahan tertangkap | 153 | ≈134 *(88% dari 153 adalah keluhan sungguhan)* |
| Alarm palsu tambahan | 488 | **≈172** *(hanya 35% dari 488 benar-benar palsu)* |
| **Rasio pertukaran** | 1 : 3,2 | **≈1 : 1,3** |

**Peringatan atas angka ini.** Proporsi 64,7% dan 12,5% diukur pada sampel 50
kesalahan **`linear_svc_tuned`**, lalu diterapkan ke selisih ComplementNB —
model yang kesalahannya hanya beririsan 0,524 (Jaccard) dengan LinearSVC.
Selang kepercayaannya juga lebar (FP: 47,9%–78,5%; FN: 3,5%–36,0%), sehingga
rasio 1:1,3 sebenarnya sebuah rentang kira-kira **0,7–2,6**. Yang dapat
dinyatakan dengan aman bukan angka pastinya, melainkan **arahnya**: biaya
sebenarnya dari recall negatif yang tinggi jauh lebih rendah daripada yang
tampak pada confusion matrix mentah.


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

*(Rekomendasi ini tetap setelah H-7, tetapi marginnya menyempit — lihat
kualifikasi di akhir bagian.)*

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

Setelah koreksi H-7 (Bagian 2.2), rasio itu turun menjadi **≈1 keluhan per 1,3
alarm palsu sungguhan** — jauh lebih murah daripada yang tampak semula, karena
dua pertiga "alarm palsu" ternyata keluhan asli yang diberi bintang 4–5★.

**Kualifikasi jujur atas rekomendasi Bagian 4:** bukti H-7 memperkuat posisi
ComplementNB dan memperkecil jarak antara kedua pilihan. Yang masih memihak
LogisticRegression adalah macro-F1 1,9 poin lebih tinggi — metrik utama yang
akan menjadi angka judul di laporan — serta keunggulannya pada set evaluasi yang
lebih sulit. Yang memihak ComplementNB adalah tujuan operasional sistem ini:
menemukan keluhan. Ini kini **keputusan yang sungguh-sungguh berimbang**, bukan
pilihan dengan satu jawaban yang jelas lebih baik.

Apakah pertukaran itu layak bergantung pada angka yang tidak ada di data ini:
berapa biaya satu keluhan pelanggan yang terlewat dibanding satu menit waktu
peninjau. Itu pertimbangan operasional, bukan statistik — dan karena itu bukan
keputusan agent.

## 5. Keputusan (H-10)

**Model produksi terpilih:** **LogisticRegression**

**Parameter:** `C=1.0, class_weight="balanced"`, TF-IDF unigram+bigram
(`min_df=3`, `max_features=30000`, `sublinear_tf=True`), `solver="liblinear"`,
`random_state=42`.

**Diputuskan oleh / tanggal:** pemilik proyek, 17 September 2026.

### 5.1 Alasan keputusan

Sesuai cabang (b) kerangka Bagian 2.5 — syarat "LinearSVC unggul ≥2 poin" tidak
terpenuhi (unggul 0,03 poin pada `full`, kalah 0,05 poin pada
`informative_ge5w`), sehingga yang berlaku adalah "pilih model yang lebih
sederhana dan lebih mudah dijelaskan".

Empat alasan, berurutan:

1. **`predict_proba` bawaan.** Tidak ada `CalibratedClassifierCV`, tidak ada
   `model_calibrated.joblib`, tidak ada pelatihan ulang 5×. Model yang
   metriknya dilaporkan di tabel adalah objek yang persis sama dengan yang
   melayani `/api/predict` — tanpa lapisan perantara yang perlu dijelaskan
   terpisah di bab metodologi.
2. **Unggul pada set evaluasi yang lebih sulit.** macro-F1 0,9078 pada
   `informative_ge5w`, tertinggi di antara keempat model, dan di situlah 77%
   kesalahan sebenarnya berada.
3. **Presisi negatif tertinggi** (0,8802 pada `full`) → beban alarm palsu
   paling ringan.
4. **Koefisien = log-odds per kata**, dapat ditampilkan langsung tanpa perkakas
   tambahan.

**Biaya yang diterima secara sadar:** recall negatif 0,9315 pada `full` — yang
terendah di antara keempat kandidat. Dibanding ComplementNB (0,9553),
**127 keluhan lebih banyak lolos triase** (FN 239 → 366) dari 5.347 ulasan
negatif di test set, ditukar dengan **457 alarm palsu lebih sedikit**
(FP 1.135 → 678). Setelah koreksi H-7 (Bagian 2.2), pertukaran sebenarnya
≈111 keluhan sungguhan versus ≈161 alarm palsu sungguhan, yaitu **1 : 1,5**.
Konsekuensi ini diterima, bukan diabaikan.

### 5.2 Parameter: mengapa `C=1.0` dan bukan `C=5.0` pemenang GridSearch

`GridSearchCV` memilih `C=5.0` (CV macro-F1 0,908486). Parameter produksi
justru `C=1.0` (CV 0,908341) berdasarkan **aturan satu simpangan baku**
(*one-standard-error rule*, Breiman et al., 1984): dipilih model paling
sederhana — pada model linear berarti regularisasi terkuat — yang skornya masih
berada dalam satu simpangan baku dari yang terbaik.

| Besaran | `C=5.0` (pemenang grid) | `C=1.0` (1-SE) |
|---------|-------------------------|----------------|
| CV macro-F1 | 0,908486 | 0,908341 |
| Simpangan baku CV | 0,003017 | 0,001703 |
| **Selisih train−test** | **0,0499** | **0,0221** |
| macro-F1 test `full` | 0,9338 | 0,9336 |
| macro-F1 test `informative_ge5w` | 0,9071 | **0,9078** |
| recall neg `full` | 0,9267 | **0,9315** |

Keunggulan `C=5.0` di CV adalah **0,00015** — dua puluh kali lebih kecil dari
simpangan bakunya sendiri, yaitu derau. Sebagai gantinya ia menanggung selisih
train−test lebih dari dua kali lipat. Pada test set, `C=1.0` justru lebih baik
pada tiga dari empat angka utama.

Implementasi: `ml/src/tune.py::pilih_1se()`, hasilnya tersimpan di
`ml/artifacts/best_params.json` pada kunci `seleksi_1se`, dan dipakai
`ml/src/finalize.py` secara default (`--seleksi 1se`).

**Catatan yang layak masuk laporan:** `C=1.0, class_weight="balanced"` adalah
**persis konfigurasi default yang dipakai di Fase 3**. Untuk LogisticRegression,
seluruh proses tuning berakhir kembali di titik awalnya. Ini bukan tuning yang
gagal — ini bukti kuantitatif bahwa pada TF-IDF dengan data sebesar ini,
*hyperparameter* bukan faktor penentu kinerja. Baris `logistic_regression`
(Fase 3) dan `logistic_regression_final` (Fase 4) di `model_metrics.csv`
karenanya identik, dan keduanya sengaja dipertahankan sebagai bukti.

### 5.3 Konsekuensi untuk rumusan masalah

Keputusan menyertakan perubahan framing: **LogisticRegression naik dari
"pembanding" menjadi model penuh dalam RM1**, sehingga perbandingannya menjadi
**tiga keluarga algoritma** — Naive Bayes, SVM, dan Logistic Regression —
dengan **empat varian** terlatih (ComplementNB, MultinomialNB, LinearSVC,
LogisticRegression).

Dasarnya sudah disiapkan dokumen arsitektur sendiri di §2.1(c): *"Perbandingan
tiga model juga lebih kuat secara akademik daripada dua."* Seluruh bahannya
sudah tersedia — keempat varian menjalani `GridSearchCV`, evaluasi ganda,
confusion matrix, dan ekstraksi fitur dengan protokol identik.

Penyebutan di laporan harus presisi: **"tiga keluarga algoritma dengan empat
varian"**, bukan "tiga model" — karena tabel hasil memuat empat baris.

Temuan yang menjadi inti jawaban RM1: **rentang macro-F1 keempat varian hanya
1,88 poin (0,9153–0,9341)**. Model paling sederhana setara dengan yang paling
kompleks. Sesuai ketentuan Fase 10, itu ditulis sebagai temuan yang sah, bukan
sebagai kegagalan eksperimen.

### 5.4 Artefak yang dihasilkan

Dijalankan `python -m ml.src.finalize logistic_regression` (seleksi 1-SE):

| Artefak | Ukuran | Catatan |
|---------|--------|---------|
| `ml/artifacts/vectorizer.joblib` | 1,2 MB | TF-IDF ter-fit pada 45.614 baris train |
| `ml/artifacts/model_final.joblib` | 235 KB | LogisticRegression `C=1.0` |
| `ml/artifacts/label_encoder.joblib` | 383 B | 0=negatif, 1=positif |
| `ml/artifacts/MANIFEST.json` | 3,8 KB | hash data, snapshot config, versi pustaka, seluruh metrik, `random_state` |

**`model_calibrated.joblib` tidak dibuat** — tidak diperlukan, karena inilah
keuntungan utama yang mendasari pilihan ini.

Uji muat ulang di proses terpisah pada 10 sampel: **LOLOS** (prediksi identik).
Probabilitas terverifikasi berfungsi tanpa lapisan kalibrasi.
