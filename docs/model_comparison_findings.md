# TEMUAN FASE 3 — BASELINE & KOMPARASI MODEL

Seluruh angka berasal dari `ml/src/train.py` yang dijalankan, bukan estimasi.
Data: scraping Google Play lima tahun (526.322 ulasan, Oktober 2021 –
September 2026). Konfigurasi: TF-IDF unigram+bigram, `min_df=3`,
`max_features=30.000`, `sublinear_tf=True`, `random_state=42`, split stratified
80:20. Parameter default: ComplementNB dan MultinomialNB `alpha=1.0`; LinearSVC
dan LogisticRegression `C=1.0, class_weight="balanced"`.

Sumber: `docs/tables/model_metrics.csv` (baris tanpa akhiran, `dedup_training=True`),
`docs/tables/dedup_impact.csv`, Gambar 10–12. Hasil setelah tuning ada di
`docs/tuning_results.md`; keputusan model produksi di `docs/model_decision.md`.

## 1. Komposisi Data

| Properti | Nilai |
|----------|-------|
| Data berlabel | 504.208 (526.322 − 22.114 ulasan bintang 3) |
| Train / test | 403.366 / 100.842 |
| Train setelah deduplikasi | 222.308 (181.058 dibuang) |
| Komposisi train setelah deduplikasi | 109.501 negatif (49,3%) / 112.807 positif |
| Komposisi test | 29.185 negatif (28,9%) / 71.657 positif |
| Fitur TF-IDF | 30.000 |
| Subset `informative_ge5w` di test | 45.069 dari 100.842 (25.178 negatif, 19.891 positif) |

Deduplikasi hanya diterapkan pada data latih. Data uji dibiarkan apa adanya,
termasuk duplikatnya, agar tetap mewakili distribusi nyata.

## 2. Hasil — 4 Model × 2 Set Evaluasi

Diurutkan menurut macro-F1 pada set `full`.

| Model | Set | macro-F1 | recall neg | F1 neg | accuracy | latih (s) |
|-------|-----|----------|-----------|--------|----------|-----------|
| **LogisticRegression** | full | **0,9261** | 0,9192 | 0,8961 | 0,9383 | 2,448 |
| | informative_ge5w | **0,8951** | 0,9442 | 0,9116 | 0,8977 | |
| **LinearSVC** | full | 0,9228 | 0,9071 | 0,8910 | 0,9358 | 4,371 |
| | informative_ge5w | 0,8890 | 0,9299 | 0,9054 | 0,8914 | |
| **MultinomialNB** | full | 0,9183 | 0,9337 | 0,8864 | 0,9307 | 0,050 |
| | informative_ge5w | 0,8836 | 0,9584 | 0,9049 | 0,8875 | |
| **ComplementNB** | full | 0,9036 | **0,9409** | 0,8677 | 0,9170 | 0,049 |
| | informative_ge5w | 0,8831 | **0,9598** | 0,9048 | 0,8872 | |
| *majority_baseline* | full | *0,4154* | *0,0000* | *0,0000* | *0,7106* | — |
| *majority_baseline* | informative_ge5w | *0,3062* | *0,0000* | *0,0000* | *0,4413* | — |

**Seluruh model mengungguli baseline** pada macro-F1 dengan selisih 48,8–51,1
poin pada set `full`. Gambar 10 menyajikan perbandingan ini.

## 3. Temuan Metodologis — Selisih `full` vs `informative_ge5w`

Inilah pertanyaan yang dirancang untuk dijawab protokol evaluasi ganda: berapa
besar porsi "keberhasilan" model yang bertumpu pada kata pujian pendek berulang,
mengingat 40,6% ulasan hanya berisi ≤2 kata dan hampir seluruhnya positif.

| Model | full | informative_ge5w | Penurunan |
|-------|------|------------------|-----------|
| ComplementNB | 0,9036 | 0,8831 | **2,05 poin** |
| LogisticRegression | 0,9261 | 0,8951 | 3,10 poin |
| LinearSVC | 0,9228 | 0,8890 | 3,37 poin |
| MultinomialNB | 0,9183 | 0,8836 | 3,47 poin |

(Gambar 11.)

**Penurunannya moderat, bukan runtuh.** Ini temuan positif yang harus dinyatakan
apa adanya: kinerja model tetap di kisaran macro-F1 0,88–0,90 pada ulasan
bermakna. Kekhawatiran bahwa akurasi tinggi seluruhnya merupakan artefak panjang
teks tidak terbukti. Namun artefak itu tetap nyata dalam derajat 2,0–3,5 poin,
dan angka itu hanya terlihat karena evaluasi ganda dijalankan.

Perbandingannya jauh lebih tajam pada baseline. macro-F1 baseline jatuh dari
0,4154 ke 0,3062, dan akurasinya dari 0,7106 ke 0,4413. Pada subset informatif,
kelas negatif justru menjadi mayoritas (25.178 dari 45.069, atau 55,9%),
sehingga tebakan "selalu positif" salah pada lebih dari separuh baris. Set
`informative_ge5w` jadi bukan hanya lebih sulit, tetapi juga berbalik
komposisinya, dan model mempertahankan kinerjanya di sana.

**ComplementNB paling tahan terhadap artefak ini.** Penurunannya terkecil
(2,05 poin) dan recall negatifnya tertinggi pada kedua set (0,9409 dan 0,9598).
Ini konsisten dengan alasan ComplementNB dipilih: ia dirancang untuk data tidak
seimbang. Harganya presisi negatif terendah (0,8050 pada `full`), sehingga ia
juga paling banyak menandai ulasan positif sebagai keluhan.

## 4. Kecepatan

| Model | Latih | Inferensi (100.842 baris) |
|-------|-------|---------------------------|
| ComplementNB | 0,049 s | 0,0072 s |
| MultinomialNB | 0,050 s | 0,0081 s |
| LogisticRegression | 2,448 s | 0,0040 s |
| LinearSVC | 4,371 s | 0,0054 s |

(Gambar 12, skala log.) Naive Bayes ±50–90× lebih cepat dilatih. Inferensi
seluruh model di bawah 0,01 detik untuk 100.842 baris. Pada skala ini seluruhnya
praktis, tetapi selisih waktu latih relevan bila pelatihan ulang menjadi rutin.

## 5. Dampak Deduplikasi Training

Dijalankan dua kali dengan konfigurasi identik, hanya `dedup_training_text`
yang dibedakan. macro-F1 pada set `full`:

| Model | Tanpa dedup | Dengan dedup | Selisih |
|-------|-------------|--------------|---------|
| ComplementNB | 0,8957 | 0,9036 | **+0,0079** |
| LogisticRegression | 0,9228 | 0,9261 | +0,0033 |
| LinearSVC | 0,9216 | 0,9228 | +0,0012 |
| MultinomialNB | 0,9173 | 0,9183 | +0,0010 |

Dampaknya kecil tetapi **positif pada keempat model**. ComplementNB paling
diuntungkan, karena ia paling sensitif terhadap distorsi frekuensi kelas.

Yang lebih penting dari macro-F1 adalah **pergeseran keseimbangan**. Deduplikasi
membuang 173.820 baris positif (60,6% dari positif latih), tetapi hanya 7.238
baris negatif (6,2%). Komposisi data latih bergeser dari 28,9% negatif menjadi
49,3%. Akibatnya pada data uji `full`:

| Model | recall neg tanpa → dengan dedup | presisi neg tanpa → dengan dedup |
|-------|--------------------------------|----------------------------------|
| ComplementNB | 0,9711 → 0,9409 | 0,7710 → 0,8050 |
| MultinomialNB | 0,9420 → 0,9337 | 0,8354 → 0,8436 |
| LinearSVC | 0,9428 → 0,9071 | 0,8449 → 0,8755 |
| LogisticRegression | 0,9542 → 0,9192 | 0,8398 → 0,8742 |

Pada keempat model, recall negatif turun dan presisi negatif naik. Untuk dua
model linear, mekanismenya langsung: `class_weight="balanced"` menghitung bobot
dari komposisi kelas. Dengan data latih yang hampir seimbang, bobot kelas
negatif turun dari ±1,73 menjadi ±1,02, sehingga model lebih jarang memprediksi
negatif. Untuk Naive Bayes, penjelasan yang paling mungkin adalah bahwa pujian
pendek yang berulang tidak lagi mendominasi distribusi kata kelas positif. Ini
dugaan dan tidak diuji terpisah.

Deduplikasi juga memangkas waktu latih LinearSVC dari 86,7 s menjadi 4,4 s.

## 6. Arah untuk Fase 4 dan Hasil Akhirnya

Kerangka keputusan Bagian 2.5 dokumen arsitektur: bila LinearSVC unggul ≥2 poin
macro-F1, jadikan model produksi; bila selisihnya <2 poin, pilih model yang
lebih sederhana dan mudah dijelaskan.

Pada parameter default, **LinearSVC tidak unggul**. Ia justru kalah 0,33 poin
dari LogisticRegression. Selisih antar keempat model 2,25 poin
(0,9036–0,9261).

Setelah tuning (`docs/tuning_results.md`), LinearSVC naik ke 0,9270 dan unggul
0,08 poin atas LogisticRegression (0,9261), tetap jauh di bawah ambang 2 poin.
Cabang kedua kerangka berlaku. Model produksi yang ditetapkan adalah
**LogisticRegression `C=1.0, class_weight="balanced"`**, persis konfigurasi
default pada tabel di atas (`docs/model_decision.md`).

Catatan untuk pemilihan: bila prioritas utama adalah **recall kelas negatif**
sebagaimana ditetapkan di Bagian 2.3 (keluhan yang lolos triase adalah
kegagalan bisnis langsung), ComplementNB memimpin di kedua set evaluasi meski
macro-F1-nya terendah. Ini persis jenis keputusan yang tidak boleh diambil hanya
dari satu angka. Pertimbangannya, termasuk koreksi dari analisis kesalahan
manual bahwa sebagian besar "alarm palsu" sebenarnya keluhan yang diberi
bintang tinggi, ada di `docs/model_decision.md` §2.2 dan §4.1.
