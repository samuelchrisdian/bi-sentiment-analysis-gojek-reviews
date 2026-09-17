# TEMUAN FASE 3 — BASELINE & KOMPARASI MODEL

Seluruh angka berasal dari `ml/src/train.py` yang dijalankan, bukan estimasi.
Konfigurasi: TF-IDF unigram+bigram, `min_df=3`, `max_features=30.000`,
`random_state=42`, split stratified 80:20.

## 1. Komposisi Data

| Properti | Nilai |
|----------|-------|
| Data berlabel | 96.466 (100.000 − 3.534 netral) |
| Train / test | 77.172 / 19.294 |
| Train setelah deduplikasi | 45.614 (31.558 dibuang) |
| Fitur TF-IDF | 30.000 |
| Subset `informative_ge5w` di test | 8.938 dari 19.294 |

## 2. Hasil — 4 Model × 2 Set Evaluasi

Diurutkan menurut macro-F1 pada set `full`.

| Model | Set | macro-F1 | recall neg | F1 neg | accuracy | latih (s) |
|-------|-----|----------|-----------|--------|----------|-----------|
| **LogisticRegression** | full | **0,9336** | 0,9316 | 0,9082 | 0,9459 | 0,328 |
| | informative_ge5w | **0,9078** | 0,9536 | 0,9072 | 0,9089 | |
| **LinearSVC** | full | 0,9301 | 0,9168 | 0,9033 | 0,9433 | 0,427 |
| | informative_ge5w | 0,9000 | 0,9332 | 0,8985 | 0,9010 | |
| **MultinomialNB** | full | 0,9279 | 0,9400 | 0,9013 | 0,9406 | 0,012 |
| | informative_ge5w | 0,8991 | 0,9613 | 0,8985 | 0,9008 | |
| **ComplementNB** | full | 0,9154 | **0,9557** | 0,8862 | 0,9288 | 0,013 |
| | informative_ge5w | 0,8986 | **0,9716** | 0,9010 | 0,9005 | |
| *majority_baseline* | full | *0,4196* | *0,0000* | *0,0000* | *0,7229* | — |
| *majority_baseline* | informative_ge5w | *0,3173* | *0,0000* | *0,0000* | *0,5211* | — |

**Seluruh model mengungguli baseline** pada macro-F1 dengan selisih 50–51 poin.

## 3. Temuan Metodologis — Selisih `full` vs `informative_ge5w`

Inilah pertanyaan yang dirancang untuk dijawab protokol evaluasi ganda: berapa
besar porsi "keberhasilan" model yang bertumpu pada kata pujian pendek berulang,
mengingat 39,9% ulasan hanya berisi ≤2 kata dan hampir seluruhnya positif.

| Model | full | informative_ge5w | Penurunan |
|-------|------|------------------|-----------|
| ComplementNB | 0,9154 | 0,8986 | **1,68 poin** |
| LogisticRegression | 0,9336 | 0,9078 | 2,59 poin |
| MultinomialNB | 0,9279 | 0,8991 | 2,88 poin |
| LinearSVC | 0,9301 | 0,9000 | 3,00 poin |

**Penurunannya moderat, bukan runtuh.** Ini temuan positif yang harus dinyatakan
apa adanya: kinerja model tetap di kisaran macro-F1 0,90 pada ulasan bermakna.
Kekhawatiran bahwa akurasi tinggi seluruhnya merupakan artefak panjang teks
tidak terbukti — tetapi tetap nyata dalam derajat 1,7–3,0 poin, dan angka itu
hanya terlihat karena evaluasi ganda dijalankan.

Perbandingannya jauh lebih tajam pada baseline: macro-F1 baseline jatuh dari
0,4196 ke 0,3173 antara kedua set, karena proporsi kelas pada subset informatif
memang lebih seimbang. Artinya set `informative_ge5w` memang lebih sulit, dan
model mempertahankan kinerjanya di sana.

**ComplementNB paling tahan terhadap artefak ini** — penurunannya terkecil
(1,68 poin) dan recall negatifnya tertinggi pada kedua set (0,9557 dan 0,9716).
Ini konsisten dengan alasan ComplementNB dipilih: ia dirancang untuk data tidak
seimbang.

## 4. Kecepatan

| Model | Latih | Inferensi (19.294 baris) |
|-------|-------|--------------------------|
| MultinomialNB | 0,012 s | 0,0019 s |
| ComplementNB | 0,013 s | 0,0021 s |
| LogisticRegression | 0,328 s | 0,0011 s |
| LinearSVC | 0,427 s | 0,0012 s |

Naive Bayes ±30× lebih cepat dilatih. Pada skala ini seluruhnya praktis, tetapi
selisihnya relevan bila pelatihan ulang menjadi rutin.

## 5. Dampak Deduplikasi Training

Dijalankan dua kali dengan konfigurasi identik, hanya `dedup_training_text`
yang dibedakan. macro-F1 pada set `full`:

| Model | Tanpa dedup | Dengan dedup | Selisih |
|-------|-------------|--------------|---------|
| ComplementNB | 0,9060 | 0,9154 | **+0,0094** |
| LogisticRegression | 0,9283 | 0,9336 | +0,0053 |
| LinearSVC | 0,9291 | 0,9301 | +0,0009 |
| MultinomialNB | 0,9281 | 0,9279 | −0,0002 |

Dampaknya kecil tetapi konsisten positif, kecuali MultinomialNB yang praktis
tidak berubah. ComplementNB paling diuntungkan — masuk akal, karena ia paling
sensitif terhadap distorsi frekuensi kelas, dan 31.558 duplikat yang dibuang
didominasi pujian pendek berulang.

## 6. Arah Awal untuk Fase 4

Kerangka keputusan Bagian 2.5 dokumen arsitektur: bila LinearSVC unggul ≥2 poin
macro-F1, jadikan model produksi; bila selisihnya <2 poin, pilih model yang
lebih sederhana dan mudah dijelaskan.

Pada parameter default, **LinearSVC tidak unggul** — ia justru kalah 0,35 poin
dari LogisticRegression. Selisih antar keempat model hanya 1,82 poin
(0,9154–0,9336). Keputusan final ditunda sampai setelah tuning di Fase 4, dan
merupakan wewenang manusia (gerbang H-10).

Catatan untuk pemilihan: bila prioritas utama adalah **recall kelas negatif**
sebagaimana ditetapkan di Bagian 2.3 — keluhan yang lolos triase adalah
kegagalan bisnis langsung — maka ComplementNB memimpin di kedua set evaluasi
meski macro-F1-nya terendah. Ini persis jenis keputusan yang tidak boleh
diambil hanya dari satu angka.
