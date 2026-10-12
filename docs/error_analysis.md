# ANALISIS KESALAHAN & INTERPRETASI FITUR

**Fase 4, T-4.4 & T-4.5** · Data: scraping Google Play lima tahun (526.322
ulasan, Oktober 2021 – September 2026).

> ## ✅ Pemeriksaan manual selesai
>
> 50 kesalahan diperiksa manusia; kolom `kategori_penyebab` diisi seluruhnya
> pada `docs/tables/error_analysis_50_reviewed.csv`. Distribusi di Bagian 3
> dihitung dari berkas yang dikembalikan itu, bukan dari tebakan agent.
>
> Statistik mekanis (Bagian 2 dan 4) dihitung read-only dengan
> `ml/src/error_analysis.py` (`bangun_berkas_kerja()`, `profil_kesalahan()`,
> `tumpang_tindih_model()`) dari `data/processed/reviews_clean.parquet` dan
> `ml/artifacts/tuned_*.joblib`.

---

## 1. Model yang Diperiksa

Kesalahan yang dianalisis berasal dari **`linear_svc_tuned`** (`C=0.1`,
`class_weight="balanced"`), yaitu peraih macro-F1 tertinggi setelah tuning
(0,9270 pada set `full`).

Model produksi yang kemudian dipilih adalah **LogisticRegression** (`C=1.0`,
`class_weight="balanced"`; lihat `docs/model_decision.md`), bukan model yang
diperiksa di sini. Bagian 4 menunjukkan mengapa hal itu tidak membatalkan hasil
pemeriksaan manual: kesalahan kedua model linear beririsan **0,937** (Jaccard).
Keduanya praktis salah pada baris yang sama. Confusion matrix model produksi ada
di Gambar 6; versi `linear_svc_tuned` yang menjadi sumber sampel ini ada di
`docs/figures/gambar-06b-confusion-matrix-linear-svc.png`.

## 2. Profil Kesalahan — Statistik Mekanis

**6.161 kesalahan dari 100.842 baris test (6,11%).**

| Properti | n | % dari kesalahan | Tingkat kesalahan pada kelompok itu di test set |
|----------|---|------------------|--------------------------------------------------|
| **Arah kesalahan** | | | |
| positif salah ditandai negatif (alarm palsu, FP) | 3.934 | 63,9% | — |
| negatif lolos sebagai positif (keluhan lolos, FN) | 2.227 | 36,1% | — |
| **Panjang teks** | | | |
| ≤2 kata | 865 | 14,0% | 2,08% (dari 41.539) |
| 3–4 kata | 722 | 11,7% | 5,07% (dari 14.234) |
| 5–19 kata | 3.019 | 49,0% | 9,85% (dari 30.637) |
| ≥20 kata | 1.555 | 25,2% | 10,78% (dari 14.432) |
| **Rating asal** | | | |
| 1★ | 1.617 | 26,2% | 6,55% (dari 24.682) |
| 2★ | 610 | 9,9% | 13,55% (dari 4.503) |
| 4★ | 1.410 | 22,9% | **22,68%** (dari 6.217) |
| 5★ | 2.524 | 41,0% | 3,86% (dari 65.440) |
| **Keyakinan model** | | | |
| jarak ke batas keputusan < 0,5 | 3.849 | **62,5%** | — |

Empat hal yang langsung terbaca dari tabel ini:

**(a) Hampir dua pertiga kesalahan adalah alarm palsu, bukan keluhan yang lolos.**
3.934 dari 6.161 kesalahan adalah ulasan positif yang ditandai negatif. Untuk
kasus penggunaan triase keluhan, arah ini jauh lebih murah daripada
kebalikannya: biayanya waktu peninjau, bukan pelanggan yang keluhannya
diabaikan. Bagian 3.1 menunjukkan bahwa sebagian besar "alarm palsu" ini
bahkan bukan kesalahan model.

**(b) Kesalahan terkonsentrasi pada ulasan panjang, bukan pendek.** 74,2%
kesalahan terjadi pada ulasan ≥5 kata, padahal subset itu hanya 44,7% dari test
set. Tingkat kesalahannya naik monoton menurut panjang: 2,08% pada ulasan ≤2
kata hingga 10,78% pada ulasan ≥20 kata. Ulasan sangat pendek ("bagus", "oke")
hampir selalu benar. Temuan ini melengkapi evaluasi ganda: set `informative_ge5w`
memang lebih sulit, dan di situlah kesalahan sebenarnya berada. Polanya terlihat
pula di Gambar 6. Pada model produksi, recall kelas positif turun dari 0,946
(`full`) ke 0,839 (`informative_ge5w`), sedangkan recall kelas negatif justru
naik dari 0,919 ke 0,944. Polanya sama pada `linear_svc_tuned` (0,945 → 0,835
dan 0,924 → 0,948).

**(c) Ulasan bintang 4 paling sering salah: 22,68%**, enam kali tingkat kesalahan
ulasan bintang 5 (3,86%). Ulasan bintang 4 adalah tempat pengguna yang puas
secara umum menulis satu keluhan spesifik. Isinya menyerupai keluhan, labelnya
positif. Bagian 3.1 mengonfirmasi pola ini pada tingkat ulasan.

**(d) 62,5% kesalahan terjadi di dekat batas keputusan** (jarak < 0,5). Umumnya
model ragu, bukan "yakin dan salah". Proporsinya berbeda menurut arah: 71,7%
keluhan yang lolos (1.596 dari 2.227) berada di dekat batas, sedangkan pada
alarm palsu hanya 57,3% (2.253 dari 3.934). Alarm palsu lebih sering berupa
kesalahan berkeyakinan tinggi, yang merupakan kandidat paling mungkin untuk
kategori "label keliru dari pengguna". Itulah yang diuji pemeriksaan manual di
Bagian 3.

## 3. Distribusi Kategori Penyebab (diisi manusia)

Sumber: `docs/tables/error_analysis_50_reviewed.csv`, 50 baris acak dari 6.161
kesalahan `linear_svc_tuned` (`random_state=42`); seluruh kolom
`kategori_penyebab` terisi dan sah menurut taksonomi. Selang kepercayaan Wilson
95% dihitung dari n = 50.

| Kategori | n | % | Wilson 95% | FP | FN |
|----------|---|---|-----------|----|----|
| **Label keliru dari pengguna** | **25** | **50,0%** | 36,6%–63,4% | 23 | 2 |
| Negasi kompleks / polaritas campuran | 10 | 20,0% | 11,2%–33,0% | 4 | 6 |
| Terlalu pendek / ambigu | 7 | 14,0% | | 1 | 6 |
| Topik netral / off-topic | 3 | 6,0% | | 1 | 2 |
| Sarkasme / ironi | 2 | 4,0% | 1,1%–13,5% | 0 | 2 |
| Campur kode | 2 | 4,0% | | 0 | 2 |
| Kegagalan preprocessing | 1 | 2,0% | | 1 | 0 |
| **Total** | **50** | | | **30** | **20** |

### 3.1 Temuan utama: separuh "kesalahan" bukan kesalahan model

**50% kesalahan adalah label yang keliru dari pengguna**, yaitu bintang yang
diberikan bertentangan dengan isi tulisannya. Arahnya sangat timpang:

| Bentuk salah-label | n | Contoh dari sampel |
|--------------------|---|--------------------|
| Rating 4–5★, isi berupa keluhan | 23 (10 × 4★, 13 × 5★) | 5★ "Upgradenya lama"; 5★ "Knp y setiap isi saldo gk masuk!!!!!!!!!!"; 4★ "Harganya semakin Mahal, aplikasi sebelah lebih murah"; 4★ "Buruk" |
| Rating 1★, isi positif | 2 | 1★ "Bagus"; 1★ "Dangat membantu" |

Dilihat menurut arah kesalahan, temuannya lebih tajam lagi:

| Arah kesalahan | n sampel | label keliru pengguna | Wilson 95% |
|----------------|----------|-----------------------|-----------|
| Alarm palsu (FP) | 30 | **23 (76,7%)** | 59,1%–88,2% |
| Keluhan lolos (FN) | 20 | 2 (10,0%) | 2,8%–30,1% |

**Tiga perempat "alarm palsu" adalah ulasan berisi keluhan yang diberi bintang
4–5 oleh penulisnya.** Pada baris-baris itu prediksi model benar; yang keliru
labelnya. Untuk triase keluhan, baris-baris itu justru temuan yang diinginkan.
Sebaliknya, keluhan yang lolos hampir seluruhnya kesalahan model yang
sesungguhnya: negasi kompleks dan ulasan terlalu pendek masing-masing 6 dari 20,
sarkasme, campur kode, dan topik di luar layanan masing-masing 2.
Konsekuensi proporsi ini untuk pemilihan model dibahas di
`docs/model_decision.md` §2.2.

Pola salah-label punya penjelasan perilaku yang masuk akal: bintang diberikan
untuk layanan secara keseluruhan atau sebagai niat baik, sementara kolom teks
dipakai untuk menyampaikan satu keluhan spesifik. Ini sejalan dengan tingkat
kesalahan 22,68% pada ulasan bintang 4 di Bagian 2. Konsekuensinya untuk
penelitian ini langsung: **rating bintang bukan label sentimen teks yang
sempurna, ia hanya proksi.**

### 3.2 Bukti silang: model paling yakin justru ketika labelnya yang salah

Persilangan kategori dengan jarak ke batas keputusan menghasilkan konfirmasi
yang tidak dirancang sebelumnya:

| Kategori | model ragu (<0,5) | model yakin (≥0,5) |
|----------|-------------------|--------------------|
| **Label keliru dari pengguna** | 10 | **15** |
| Negasi kompleks | 8 | 2 |
| Terlalu pendek / ambigu | 4 | 3 |
| Topik netral / off-topic | 2 | 1 |
| Sarkasme / ironi | 1 | 1 |
| Campur kode | 2 | 0 |
| Kegagalan preprocessing | 1 | 0 |
| **Total** | **28** | **22** |

**Dari 22 kesalahan berkeyakinan tinggi, 15 (68,2%; Wilson 47,3%–83,6%) adalah
label keliru.** Ketika model yakin dan "salah", umumnya modelnya yang benar dan
bintangnya yang keliru. Sebaliknya, negasi kompleks, yaitu kesalahan yang
benar-benar sulit, hampir seluruhnya (8 dari 10) terjadi di dekat batas
keputusan, saat model memang ragu.

Tiga dari tujuh kesalahan "terlalu pendek / ambigu" berkeyakinan tinggi, dan
ketiganya ulasan satu kata: "ok" (1★), emoji 👌 yang dinormalisasi menjadi
"oke" (2★), dan "Dihapus" (5★). Pada teks sependek ini model hanya punya satu
token untuk dinilai, dan token itu memang lazim pada kelas yang diprediksinya.

Pola ini tidak dapat dilihat dari metrik agregat mana pun, dan hanya muncul
karena keyakinan model dicatat bersama kategori penyebab.

### 3.3 Batas atas kinerja yang realistis pada dataset ini

Bila 50% dari 6.161 kesalahan adalah label keliru, maka sekitar **3.080 baris
(3,05%) dari 100.842 baris test membawa bintang yang bertentangan dengan
teksnya.** Angka itu menggeser tolok ukurnya:

| Besaran | Nilai |
|---------|-------|
| Estimasi derau label pada test set | 3,05% (Wilson 95%: 2,24%–3,87%) |
| **Plafon akurasi realistis** | **≈0,9695** (rentang 0,9613–0,9776) |
| Akurasi `linear_svc_tuned` (`full`) | 0,9389 → 96,8% dari plafon; sisa ≈3,06 poin |
| Akurasi model produksi LogisticRegression (`full`) | 0,9383 → 96,8% dari plafon; sisa ≈3,12 poin |
| Kesalahan `linear_svc_tuned` yang benar-benar milik model | ≈3.081 baris (3,06% dari test) |

**Akurasi 0,938–0,939 karena itu harus dibaca relatif terhadap ≈0,970, bukan
terhadap 1,000.** Selisih yang tersisa untuk diperbaiki bukan 6,1 poin melainkan
sekitar 3,1 poin. Sebagian darinya terdiri atas negasi kompleks, sarkasme, dan
ulasan satu kata yang tidak terjangkau model *bag-of-words* mana pun.

**Pemeriksaan kepekaan.** Estimasi di atas menerapkan proporsi gabungan 50%
pada seluruh kesalahan. Bila dihitung per arah, yaitu 76,7% × 3.934 FP + 10,0% ×
2.227 FN, hasilnya ≈3.239 baris (3,21%). Angka ini sedikit lebih tinggi karena
porsi FP di populasi kesalahan (63,9%) sedikit lebih besar daripada di sampel
(60%), dan tetap berada di dalam selang di atas.

**Tiga kualifikasi yang harus menyertai angka ini, bukan disembunyikan:**

1. Estimasi berasal dari sampel 50 baris. Selang kepercayaannya lebar
   (36,6%–63,4% untuk proporsi salah-label), sehingga plafonnya pun sebuah
   rentang, bukan satu angka.
2. Sampel diambil **hanya dari baris yang salah diklasifikasikan**. Baris yang
   salah label tetapi kebetulan diprediksi sesuai labelnya tidak terwakili,
   sehingga 3,05% adalah **batas bawah** derau label pada test set.
3. Penilaian "label keliru" adalah penilaian manusia atas teks, dan pada
   beberapa kasus berbatasan dengan kategori "negasi kompleks", yaitu ulasan
   berpolaritas campuran seperti 4★ "Saya pengguna gojek ... Memuaskan:) Hanya
   saja sedikit kecewa dengan goride". Batas antar keduanya tidak tajam.

### 3.4 Kegagalan preprocessing (2%): tidak menghasilkan iterasi

Hanya satu kasus: 5★ "Plis lah ya km mey" menjadi `lah kilometer mey`. Token
`km` di sini singkatan "kamu", tetapi kamus normalisasi memetakannya ke satuan
`kilometer`. Pada korpus, `km` sebagai kata utuh muncul di 812 ulasan dan
seluruhnya dipetakan ke `kilometer`. Sebagian memang berarti satuan jarak
(angkanya sudah dibuang), sebagian berarti "kamu". Ambiguitas ini tidak dapat
diselesaikan kamus yang bekerja per token tanpa konteks, dan sudah tercatat
sebagai keterbatasan pra-pemrosesan.

Angka 1 dari 50 sejalan dengan verifikasi manual pra-pemrosesan empat putaran
(400 sampel) yang mendahului pemodelan: masalah sistemik sudah ditangani di
sana. Salah ketik idiosinkratik masih ada di teks, misalnya "Dangat membantu"
dan "semakin paya(h)", tetapi pada sampel ini keduanya bukan penyebab
kesalahan. Kasus pertama salah karena labelnya, kasus kedua karena ironinya.

Satu pemeriksaan tambahan menunjukkan mengapa ekor panjang salah ketik
pengaruhnya kecil: dari 61.543 token unik pada `ulasan_clean` di seluruh korpus,
**44.035 (71,6%) muncul di kurang dari 3 dokumen**. Dengan `min_df=3`, token
seperti itu tidak pernah menjadi fitur TF-IDF. Sebagian besar salah ketik
perorangan tidak masuk matriks fitur sejak awal.

**Keputusan: tidak ada iterasi kembali ke pra-pemrosesan.** Yang dicatat
sebagai keterbatasan: normalisasi slang menangani variasi **yang umum**, bukan
singkatan ambigu yang maknanya bergantung pada konteks.

### 3.5 Yang diperkirakan besar tetapi ternyata kecil: sarkasme

Taksonomi menempatkan sarkasme di urutan pertama, dan literatur analisis
sentimen umumnya memperlakukannya sebagai penyebab utama. Pada sampel ini
**sarkasme hanya 2 dari 50 (4%; Wilson 1,1%–13,5%)**: "PINnya gapernah berubah
tpi salah mulu, mantap" dan "tetap semangat 💪💪..meskipun semakin paya".
Campur kode juga 2 kasus: "Cool artwork, lazy costumer service." dan "To much
updates....". Keduanya ulasan pendek yang memuat kurang dari dua kata fungsi
bahasa Inggris, sehingga tidak terdeteksi sebagai ulasan dominan bahasa Inggris
(`ml/src/language_filter.py`) dan tidak diterjemahkan. Teksnya tetap berbahasa
Inggris atau hanya sebagian ternormalisasi (`costumer service` →
`pelanggan layan`).

Yang justru dominan adalah dua hal yang jarang dibahas: derau label dari
pengguna (50%) dan polaritas campuran dalam satu ulasan (20%). Pada ulasan
aplikasi berbahasa Indonesia, **"bagus tapi..." jauh lebih sering menjadi
sumber kesalahan daripada ironi.** Ini layak dinyatakan di pembahasan sebagai
temuan tersendiri, karena ia bertentangan dengan dugaan awal yang membentuk
taksonominya.

## 4. Apakah Taksonomi Ini Berlaku Lintas Model?

Indeks Jaccard antar himpunan kesalahan keempat model tuned (irisan ÷ gabungan),
dihitung dengan `tumpang_tindih_model()`:

| | linear_svc | logistic_reg | complement_nb | multinomial_nb | n salah |
|---|---|---|---|---|---|
| **linear_svc** | 1,000 | **0,937** | 0,520 | 0,644 | 6.161 |
| **logistic_regression** | 0,937 | 1,000 | 0,511 | 0,632 | 6.220 |
| **complement_nb** | 0,520 | 0,511 | 1,000 | 0,791 | 8.365 |
| **multinomial_nb** | 0,644 | 0,632 | 0,791 | 1,000 | 6.973 |

Dua model linear salah pada 94% baris yang sama, dan dua Naive Bayes pada 79%.
Lintas keluarga, tumpang tindihnya 51–64%: lebih rendah, tetapi tetap
mayoritas.

**Konsekuensi praktis:** taksonomi penyebab yang disusun dari kesalahan
`linear_svc_tuned` berlaku langsung untuk model produksi LogisticRegression,
karena himpunan kesalahannya hampir identik. Untuk Naive Bayes, taksonomi ini
berlaku sebagian. Yang berbeda bukan *jenis* kasus yang sulit, melainkan *berapa
banyak* yang terjaring. ComplementNB salah pada 8.365 baris, 36% lebih banyak
dari LinearSVC. Ini sepenuhnya konsisten dengan presisi negatifnya yang lebih
rendah (0,8050 vs 0,8727): ia menandai lebih banyak ulasan sebagai keluhan,
sehingga menghasilkan lebih banyak alarm palsu. Karena irisannya dengan
LinearSVC hanya 0,520, proporsi label keliru pada Bagian 3.1 tidak dapat
dipindahkan begitu saja ke kesalahan ComplementNB (lihat peringatan di
`docs/model_decision.md` §2.2).

## 5. Fitur Paling Berpengaruh (T-4.5)

Berkas lengkap: `docs/tables/top_features.csv` (4 model × 2 kelas × 20 fitur),
dihasilkan `ml/src/interpret.py`.

### LinearSVC (tuned)

| Kelas | 20 fitur teratas |
|-------|------------------|
| **Negatif** | tidak, buruk, parah, batal, bintang satu, malah, jelek, tolol, padahal, blokir, selamat tinggal, tidak puas, kecewa, bangkrut, iklan, tidak bisa, sampah, tidak ramah, tipu, tidak bantu |
| **Positif** | mantap, tidak ribet, pernah kecewa, bagus, mudah, oke, sangat bantu, tidak kecewa, bantu, terbaik, alhamdulillah, terima kasih, kadang, sejauh, keren, puas, cepat, tidak lama, bintang empat, terkadang |

### LogisticRegression (tuned = model produksi)

| Kelas | 20 fitur teratas |
|-------|------------------|
| **Negatif** | tidak, buruk, parah, batal, tolol, malah, jelek, bintang satu, sampah, padahal, kecewa, blokir, iklan, tidak puas, bangkrut, payah, aneh, tidak bantu, tidak ramah, selamat tinggal |
| **Positif** | mantap, bagus, mudah, sangat bantu, oke, tidak ribet, pernah kecewa, terbaik, bantu, alhamdulillah, terima kasih, keren, tidak kecewa, puas, cepat, sejauh, ramah, kadang, moga, permudah |

### ComplementNB & MultinomialNB (tuned)

| Kelas | 20 fitur teratas |
|-------|------------------|
| **Negatif** | tidak mutu, aplikasi sampah, aplikasi tolol, mending pindah, aplikasi busuk, ampas, buruk sangat, aplikasi tipu, gjls, tolol, aplikasi bodoh, worst, makin kacau, lintah, makin jelek, jam cari, jam malah, mau bangkrut, gaguna, busuk |
| **Positif** | mantap banyak, cepat ramah, gojek terbaik, bantu segala, mantap sangat, sukses selalu, oke banget, jadi mudah, bantu kala, mantap pokok, mantap aplikasi, moga selalu, cepat aman, sangat bantu, selalu bantu, bantu jalan, sukses terus, gojek mantap, mantabs, alhamdulillah sangat |

**Catatan metodologis:** daftar ComplementNB dan MultinomialNB identik. Ini bukan
kekeliruan ekstraksi melainkan konsekuensi matematis dari kasus dua kelas:
komplemen kelas 0 *adalah* kelas 1, sehingga peringkat log-ratio kedua model
sama persis meski bobot mentahnya berbeda. Perbedaan keduanya terletak pada
normalisasi bobot saat prediksi, bukan pada urutan fitur. Karena itu Bagian ini
efektif menyajikan tiga daftar berbeda, bukan empat.

Bobot antar keluarga model **tidak boleh dibandingkan angkanya**, karena
koefisien model linear dan log-ratio Naive Bayes berada pada skala berbeda. Yang
dibandingkan adalah daftar katanya. Kedua model linear hampir sepakat: 18 dari
20 fitur negatif dan 17 dari 20 fitur positif sama. Daftar Naive Bayes berbeda
sifat: didominasi bigram makian dan frasa spesifik ("aplikasi sampah", "mending
pindah"), yaitu kata yang jarang tetapi hampir eksklusif pada satu kelas.

### 5.1 Jawaban Eksplisit: Masuk Akal Secara Domain, atau Artefak?

**Jawabannya: masuk akal secara domain. Tidak ditemukan artefak preprocessing
mekanis pada 160 fitur teratas.**

Audit mekanis (`ml/src/interpret.py`, fungsi `audit_artefak`) atas seluruh 160
fitur: **0** mengandung angka, **0** mengandung sisa tanda baca, **0**
mengandung token satu huruf. Tidak ada nama orang, tidak ada URL, tidak ada
stopword yang lolos.

Yang muncul justru kosakata domain yang diharapkan:

- **Kegagalan layanan:** `batal`, `blokir`, `tipu`, `tidak bisa`, `makin kacau`
- **Waktu tunggu dan pencarian driver:** `jam cari`, `jam malah`, `tidak lama`.
  Kelompok ini menonjol pada Naive Bayes dan cocok dengan keluhan pencarian
  driver.
- **Biaya dan potongan:** `lintah` (dari "lintah darat", dipakai untuk potongan
  aplikasi, biaya, dan pinjaman), `mantap banyak` (umumnya "mantap, banyak
  promo/diskon")
- **Mitra driver:** `tidak ramah`, `ramah`, `cepat ramah`
- **Pengalaman aplikasi:** `iklan`, `mudah`, `tidak ribet`, `permudah`,
  `jadi mudah`
- **Niat berpindah layanan:** `selamat tinggal`, `mending pindah`, `bangkrut`,
  `mau bangkrut`

Empat pengamatan tambahan yang layak masuk pembahasan:

**(1) Bigram membayar dirinya sendiri untuk menangani negasi.** Unigram `tidak`
adalah fitur negatif terkuat pada kedua model linear. Itu masuk akal, tetapi
berbahaya bila berdiri sendiri. Yang menyelamatkannya: bigram `tidak ribet`,
`tidak kecewa`, `tidak lama`, dan `pernah kecewa` (dari "tidak pernah kecewa";
464 dari 511 ulasannya berating 5★) muncul di 20 besar kelas **positif**,
sementara `tidak puas`, `tidak bisa`, `tidak ramah`, dan `tidak bantu` muncul di
kelas **negatif**. Model membedakan arah negasi dari konteksnya. Ini pembenaran
empiris langsung untuk keputusan `ngram_range=(1,2)`, dan sebaiknya dilaporkan
sebagai bukti, bukan sebagai asumsi.

**(2) `bintang satu` dan `bintang empat` adalah bahasa meta-ulasan.** Pengguna
menulis "saya kasih bintang satu karena..." di dalam teks. `bintang satu`
muncul di 2.012 ulasan, 1.785 di antaranya berating 1★. `bintang empat` muncul
di 292 ulasan, 243 di antaranya berating 4★. Modelnya benar, tetapi sinyal ini
datang dari kebiasaan menulis ulasan, bukan dari sentimen terhadap layanan.
Perlu disebut sebagai keterbatasan generalisasi: sinyal ini tidak akan tersedia
pada teks keluhan di kanal lain (surel, chat CS).

**(3) `kadang` dan `terkadang` di kelas positif adalah penanda bintang 4.**
Distribusi rating `kadang` di korpus hampir merata (1★:1.115, 2★:434, 3★:676,
4★:856, 5★:1.074), sehingga sekilas tampak sebagai derau. Namun 20,6% ulasan
yang memuatnya berating 4★, padahal porsi bintang 4 di korpus hanya 5,9%; pada
`terkadang` porsinya 26,2%. Dalam model linear, bobot sebuah kata bersifat
kondisional terhadap kata lain di ulasan yang sama. "Kadang" melunakkan keluhan
("kadang lambat") pada ulasan yang secara keseluruhan positif. Bersama
`sejauh` (dari "sejauh ini"; 1.546 dari 1.967 ulasan berating 5★), ini
kosakata pengguna puas yang menyampaikan catatan kecil. Sinyalnya sah, tetapi
ia juga menjelaskan mengapa ulasan bintang 4 paling sering salah (Bagian 2c):
ulasan bintang 4 tanpa kata pelunak seperti ini tampak sebagai keluhan murni.

**(4) Varian slang dan kata Inggris yang tersisa muncul pada Naive Bayes.**
`gjls` ("gak jelas", 152 ulasan, 131 berating 1★), `gaguna` ("gak guna", 78
ulasan), dan `mantabs` (varian "mantap", 244 ulasan, 237 berating 5★) tidak
tercakup kamus slang. `worst` (80 ulasan, 75 berating 1★) bertahan karena
penerjemahan hanya diterapkan pada ulasan yang dominan berbahasa Inggris;
kata Inggris di dalam ulasan berbahasa Indonesia ("worst banget", "worst
driver") tidak diterjemahkan. Sinyal keempatnya benar dan kuat, jadi ini bukan
artefak yang merusak. Yang ditunjukkannya adalah batas cakupan normalisasi:
varian yang cukup sering untuk lolos `min_df=3` tetapi tidak masuk kamus tetap
menjadi fitur tersendiri, terpisah dari bentuk bakunya.

**Kesimpulan untuk umpan balik ke pra-pemrosesan: tidak diperlukan.** Kriteria
pemicunya, yaitu muncul artefak seperti nama orang, tanda baca, atau stopword
yang lolos, tidak terpenuhi. Pipeline pra-pemrosesan lulus uji
interpretabilitas ini. Varian slang pada pengamatan (4) dicatat sebagai
keterbatasan cakupan kamus, bukan cacat yang mengubah makna.

Pemeriksaan top-feature hanya melihat kata yang **bertahan** melewati pipeline.
Ia secara struktural tidak dapat memperlihatkan kata kunci yang **hilang**
karena stemming atau salah ketik. Jalur kedua itu ditutup oleh pemeriksaan
manual 50 kesalahan, dan hasilnya sejalan: kegagalan preprocessing hanya 1 dari
50 kesalahan, berupa singkatan ambigu (`km`), bukan cacat sistematis (lihat
Bagian 3.4). Kedua jalur pemeriksaan menyimpulkan hal yang sama, dan keduanya
diperlukan untuk sampai ke sana.
