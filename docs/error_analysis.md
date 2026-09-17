# ANALISIS KESALAHAN & INTERPRETASI FITUR

**Fase 4, T-4.4 & T-4.5**

> ## ✅ GERBANG H-7 DILEWATI
>
> 50 kesalahan diperiksa manusia; kolom `kategori_penyebab` diisi seluruhnya
> pada `docs/tables/error_analysis_50_reviewed.csv`. Distribusi di Bagian 3
> dihitung dari berkas yang dikembalikan itu, bukan dari tebakan agent.

---

## 1. Model yang Diperiksa

Kesalahan yang dianalisis berasal dari **`linear_svc_tuned`** (`C=0.1`,
`class_weight="balanced"`) — peraih macro-F1 tertinggi setelah tuning (0,9341
pada set `full`).

Keputusan model produksi belum diambil (gerbang H-10). Bagian 4 menunjukkan
bahwa pemilihan model di H-10 tidak akan membatalkan hasil pemeriksaan manual
ini, karena kesalahan keempat model sebagian besar bertumpuk pada baris yang sama.

## 2. Profil Kesalahan — Statistik Mekanis

1.040 kesalahan dari 19.294 baris test (**5,39%**).

| Properti | n | Keterangan |
|----------|---|------------|
| **Arah kesalahan** | | |
| positif salah ditandai negatif | 703 | 67,6% |
| negatif lolos sebagai positif | 337 | 32,4% |
| **Panjang teks** | | |
| ≤2 kata | 133 | 12,8% |
| 3–4 kata | 106 | 10,2% |
| 5–19 kata | 488 | 46,9% |
| ≥20 kata | 313 | 30,1% |
| **Rating asal** | | |
| 1★ | 268 | 25,8% |
| 2★ | 69 | 6,6% |
| 4★ | 267 | 25,7% |
| 5★ | 436 | 41,9% |
| **Keyakinan model** | | |
| jarak ke batas keputusan < 0,5 | 696 | **66,9%** |

Tiga hal yang langsung terbaca dari tabel ini:

**(a) Dua pertiga kesalahan adalah alarm palsu, bukan keluhan yang lolos.**
703 dari 1.040 kesalahan adalah ulasan positif yang ditandai negatif. Untuk
kasus penggunaan triase keluhan, arah ini jauh lebih murah daripada
kebalikannya: biayanya waktu peninjau, bukan pelanggan yang keluhannya
diabaikan. Ini konsisten dengan `class_weight="balanced"` yang memang menggeser
ambang ke arah kelas negatif.

**(b) Kesalahan terkonsentrasi pada ulasan panjang, bukan pendek.** 77% kesalahan
terjadi pada ulasan ≥5 kata, padahal subset itu hanya 45% dari test set. Ulasan
sangat pendek ("bagus", "oke") justru hampir selalu benar. Temuan ini melengkapi
temuan Fase 3: set `informative_ge5w` memang lebih sulit, dan di situlah
kesalahan sebenarnya berada. Terlihat pula di Gambar 6 — recall kelas positif
turun dari 0,950 (`full`) ke 0,851 (`informative_ge5w`), sedangkan recall kelas
negatif justru naik dari 0,937 ke 0,957.

**(c) 67% kesalahan terjadi di dekat batas keputusan** (jarak < 0,5). Model tidak
"yakin dan salah"; ia ragu. Sepertiga sisanya — kesalahan berkeyakinan tinggi —
adalah kandidat paling mungkin untuk kategori "label keliru dari pengguna", dan
itulah yang akan diuji pemeriksaan manual di Bagian 5.

## 3. Distribusi Kategori Penyebab (H-7 — diisi manusia)

Sumber: `docs/tables/error_analysis_50_reviewed.csv`, 50 baris, seluruh kolom
`kategori_penyebab` terisi dan sah menurut taksonomi.

| Kategori | n | % |
|----------|---|---|
| **Label keliru dari pengguna** | **24** | **48,0%** |
| Negasi kompleks | 10 | 20,0% |
| Kegagalan preprocessing | 8 | 16,0% |
| Terlalu pendek / ambigu | 3 | 6,0% |
| Sarkasme / ironi | 2 | 4,0% |
| Topik netral / off-topic | 2 | 4,0% |
| Campur kode | 1 | 2,0% |

### 3.1 Temuan utama: hampir separuh "kesalahan" bukan kesalahan model

**48% kesalahan adalah label yang keliru dari pengguna** — bintang yang
diberikan bertentangan dengan isi tulisannya. Arahnya sangat timpang:

| Bentuk salah-label | n | Contoh dari sampel |
|--------------------|---|--------------------|
| Rating 4–5★, isi berupa keluhan | 22 | 5★ "aplikasinya sering lemot"; 5★ "saya udah tf ke gopay teman saldo berkurang tapi uang ke teman saya gak masuk"; 4★ "Kok setiap verifikasi wajah gagal terus ya?" |
| Rating 1★, isi positif/netral | 2 | 1★ "Tarifnya murah murah sekali siip terima kasih gojek.. semangat" |

Dua puluh dua dari 24 kasus adalah pengguna yang memberi bintang tinggi sambil
menulis keluhan. Pola ini punya penjelasan perilaku yang masuk akal: bintang
diberikan untuk layanan secara keseluruhan atau sebagai niat baik, sementara
kolom teks dipakai untuk menyampaikan satu keluhan spesifik. Konsekuensinya
untuk penelitian ini langsung: **rating bintang bukan label sentimen teks yang
sempurna, ia hanya proksi.**

### 3.2 Bukti silang: model paling yakin justru ketika labelnya yang salah

Persilangan kategori dengan jarak ke batas keputusan menghasilkan konfirmasi
yang tidak dirancang sebelumnya:

| Kategori | model ragu (<0,5) | model yakin (≥0,5) |
|----------|-------------------|--------------------|
| **Label keliru dari pengguna** | 8 | **16** |
| Negasi kompleks | 9 | 1 |
| Kegagalan preprocessing | 7 | 1 |
| Terlalu pendek / ambigu | 0 | 3 |
| Sarkasme / ironi | 2 | 0 |
| Topik netral / off-topic | 1 | 1 |
| Campur kode | 1 | 0 |
| **Total** | **28** | **22** |

**Dari 22 kesalahan berkeyakinan tinggi, 16 (72,7%) adalah label keliru.**
Ketika model yakin dan "salah", umumnya modelnya yang benar dan bintangnya yang
keliru. Sebaliknya, kesalahan yang benar-benar sulit — negasi kompleks (9 dari
10) dan kegagalan preprocessing (7 dari 8) — hampir seluruhnya terjadi di dekat
batas keputusan, yaitu model memang ragu.

Ini pola yang tidak dapat dilihat dari metrik agregat mana pun, dan hanya muncul
karena keyakinan model dicatat bersama kategori penyebab.

### 3.3 Batas atas kinerja yang realistis pada dataset ini

Bila 48% dari 1.040 kesalahan adalah label keliru, maka sekitar **499 baris
(2,59%) dari 19.294 baris test membawa bintang yang bertentangan dengan
teksnya.** Angka itu menggeser tolok ukurnya:

| Besaran | Nilai |
|---------|-------|
| Akurasi `linear_svc_tuned` (`full`) | 0,9461 |
| Estimasi derau label pada test set | 2,59% (95% CI Wilson: 1,88%–3,31%) |
| **Plafon akurasi realistis** | **≈0,9741** (CI 0,9669–0,9812) |
| Porsi plafon yang tercapai | **97,1%** |
| Kesalahan yang benar-benar milik model | ≈541 baris (2,80% dari test) |

**Angka 0,9461 karena itu harus dibaca relatif terhadap ≈0,974, bukan terhadap
1,000.** Selisih yang tersisa untuk diperbaiki bukan 5,4 poin melainkan sekitar
2,8 poin — dan sebagian darinya terdiri atas negasi kompleks dan sarkasme yang
tidak terjangkau model *bag-of-words* mana pun.

**Tiga kualifikasi yang harus menyertai angka ini, bukan disembunyikan:**

1. Estimasi berasal dari sampel 50 baris. Selang kepercayaannya lebar
   (34,8%–61,5% untuk proporsi salah-label), sehingga plafonnya pun sebuah
   rentang, bukan satu angka.
2. Sampel diambil **hanya dari baris yang salah diklasifikasikan**. Baris yang
   salah label tetapi kebetulan diprediksi sesuai labelnya tidak terwakili,
   sehingga 2,59% adalah **batas bawah** derau label pada test set.
3. Penilaian "label keliru" adalah penilaian manusia atas teks, dan pada
   beberapa kasus berbatasan dengan kategori "negasi kompleks" (ulasan
   berpolaritas campuran seperti "Overall baik, saran hapus saja sistem order
   gabungan"). Batas antar keduanya tidak tajam.

### 3.4 Kegagalan preprocessing (16%) — kategori *actionable*, tetapi tidak menghasilkan iterasi

Delapan kasus, dan rencana Fase 4 menetapkan kategori ini memicu kembali ke
Fase 2 "bila jumlahnya signifikan". 16% terdengar signifikan, sehingga
klaimnya diuji sebelum diputuskan.

Token yang gagal dinormalisasi pada kedelapan kasus, beserta frekuensinya di
seluruh 100.000 ulasan:

| Token gagal | Seharusnya | Frekuensi korpus |
|-------------|-----------|------------------|
| `jngn` | jangan | 42 |
| `gda` | tidak ada | 34 |
| `mslh` | masalah | 16 |
| `nggu` | tunggu | 15 |
| `cba` | coba | 10 |
| `agr` | agar | 4 |
| `dzholim` | zalim | 1 |
| `jaur` | jalur | 1 |
| `yangBermamfaat` | yang bermanfaat | 1 |

**Seluruhnya berjumlah ±124 kemunculan, yaitu 0,12% korpus.** Tidak ada satu
pun pola bersama: setiap kasus adalah singkatan atau salah ketik idiosinkratik
yang berbeda. Memperbaikinya berarti memperluas kamus slang satu entri per
kasus, tanpa batas yang jelas kapan berhenti.

Dua pemeriksaan tambahan menguatkan kesimpulan yang sama:

- **`min_df=3` sudah menyaringnya lebih dulu.** Dari 21.302 token unik pada
  `ulasan_clean`, **14.624 (68,7%) muncul di bawah 3 dokumen** dan karena itu
  tidak pernah menjadi fitur. Sebagian besar salah ketik ini tidak pernah masuk
  matriks TF-IDF sejak awal — pengaruhnya terhadap model sudah nol sebelum
  diperbaiki.
- **Pola `camelCase` tergabung bukan masalah sistematis.** Hanya 109 ulasan
  (0,11%) mengandung pola itu, dan hampir seluruhnya berupa kapitalisasi acak
  (`setiAp`, `keadaAn`, `mAhaL`) yang sudah tertangani *case-folding*. Kasus
  kata benar-benar tergabung seperti `yangBermamfaat` langka.

**Keputusan: tidak ada iterasi Fase 2 → Fase 4.** Kriteria "signifikan" tidak
terpenuhi ketika diukur di tingkat korpus, dan bukan hanya di tingkat sampel
50 baris. Yang dicatat sebagai keterbatasan: normalisasi slang menangani variasi
**yang umum**, bukan ekor panjang salah ketik perorangan — dan satu kasus di
antaranya (`jngn` → `jangan`) menghilangkan token negasi, sehingga jenis
kegagalan ini dapat membalik polaritas, bukan sekadar melemahkannya.

### 3.5 Yang diperkirakan besar tetapi ternyata kecil: sarkasme

Taksonomi menempatkan sarkasme di urutan pertama, dan literatur analisis
sentimen umumnya memperlakukannya sebagai penyebab utama. Pada sampel ini
**sarkasme hanya 2 dari 50 (4%)** — "Anda semua adalah sapi perah kami" dan
"Senang banget kasih driver jauh2". Campur kode bahkan lebih kecil lagi, 1 kasus.

Yang justru dominan adalah dua hal yang jarang dibahas: derau label dari
pengguna (48%) dan polaritas campuran dalam satu ulasan (20%). Pada ulasan
aplikasi berbahasa Indonesia, **"bagus tapi..." jauh lebih sering menjadi
sumber kesalahan daripada ironi.** Ini layak dinyatakan di pembahasan sebagai
temuan tersendiri, karena ia bertentangan dengan dugaan awal yang membentuk
taksonominya.

## 4. Apakah Taksonomi Ini Berlaku Lintas Model?

Indeks Jaccard antar himpunan kesalahan keempat model tuned (irisan ÷ gabungan):

| | linear_svc | logistic_reg | complement_nb | multinomial_nb | n salah |
|---|---|---|---|---|---|
| **linear_svc** | 1,000 | **0,783** | 0,524 | 0,644 | 1.040 |
| **logistic_regression** | 0,783 | 1,000 | 0,479 | 0,596 | 1.039 |
| **complement_nb** | 0,524 | 0,479 | 1,000 | 0,731 | 1.374 |
| **multinomial_nb** | 0,644 | 0,596 | 0,731 | 1,000 | 1.120 |

Dua model linear salah pada 78% baris yang sama; dua Naive Bayes pada 73% baris
yang sama. Lintas keluarga, tumpang tindihnya 48–64% — lebih rendah, tetapi
tetap mayoritas.

**Konsekuensi praktis:** taksonomi penyebab yang disusun dari kesalahan
`linear_svc_tuned` berlaku juga untuk kandidat lain di H-10. Yang berbeda antar
model bukan *jenis* kasus yang sulit, melainkan *berapa banyak* yang terjaring.
ComplementNB salah pada 1.374 baris — 32% lebih banyak dari LinearSVC — yang
sepenuhnya konsisten dengan presisi negatifnya yang lebih rendah (0,818 vs 0,877):
ia menandai lebih banyak ulasan sebagai keluhan, sehingga menghasilkan lebih
banyak alarm palsu.

## 5. Fitur Paling Berpengaruh (T-4.5)

Berkas lengkap: `docs/tables/top_features.csv` (4 model × 2 kelas × 20 fitur).

### LinearSVC (tuned)

| Kelas | 20 fitur teratas |
|-------|------------------|
| **Negatif** | tidak, buruk, jelek, malah, iklan, parah, batal, padahal, jam, pengemudi, tolol, mahal, susah, lambat, ganggu, lama, tolak, bintang satu, hilang, sampah |
| **Positif** | bagus, mantap, mudah, bantu, cepat, oke, baik, terbaik, sangat bantu, tidak ribet, keren, ramah, moga, pernah kecewa, terima kasih, kadang, tidak kecewa, banyak promo, senang, puas |

### LogisticRegression (tuned)

| Kelas | 20 fitur teratas |
|-------|------------------|
| **Negatif** | tidak, buruk, jelek, tolol, parah, batal, sampah, tidak ramah, iklan, malah, jam, gila, kurang bagus, tidak sopan, tidak bantu, kacau, bintang satu, bangkrut, tolak, blokir |
| **Positif** | bagus, mantap, mudah, bantu, sangat bantu, keren, tidak ribet, oke, terbaik, cepat, pernah kecewa, baik, ramah, moga, banyak promo, terima kasih, tidak kecewa, alhamdulillah, permudah, senang |

### ComplementNB & MultinomialNB (tuned)

| Kelas | 20 fitur teratas |
|-------|------------------|
| **Negatif** | sampah, tolol, aplikasi tolol, aplikasi sampah, anjing, busuk, sangat buruk, makin buruk, najis, satu jam, jam tidak, jelek banget, jelek sangat, sial, ampas, buruk, hampir jam, tidak jelas, aplikasi buruk, makan jam |
| **Positif** | bantu sekali, sangat bantu, sangat puas, mudah guna, oke banget, the terbaik, pengemudi ramah, mantap, moga makin, bagus bagus, keren, bantu jalan, terbaik, sukses selalu, cepat aman, jadi mudah, gojek mantap, mudah cepat, bantu banget, sangat baik

**Catatan metodologis:** daftar ComplementNB dan MultinomialNB identik. Ini bukan
kekeliruan ekstraksi melainkan konsekuensi matematis dari kasus dua kelas:
komplemen kelas 0 *adalah* kelas 1, sehingga peringkat log-ratio kedua model
sama persis meski bobot mentahnya berbeda. Perbedaan keduanya terletak pada
normalisasi bobot saat prediksi, bukan pada urutan fitur. Karena itu Bagian ini
efektif menyajikan tiga daftar berbeda, bukan empat.

Bobot antar keluarga model **tidak boleh dibandingkan angkanya** — koefisien
model linear dan log-ratio Naive Bayes berada pada skala berbeda. Yang
dibandingkan adalah daftar katanya.

### 5.1 Jawaban Eksplisit: Masuk Akal Secara Domain, atau Artefak?

**Jawabannya: masuk akal secara domain. Tidak ditemukan artefak preprocessing
pada 160 fitur teratas.**

Audit mekanis (`ml/src/interpret.py`, fungsi `audit_artefak`) atas seluruh 160
fitur: **0** mengandung angka, **0** mengandung sisa tanda baca, **0**
mengandung token satu huruf. Tidak ada nama orang, tidak ada URL, tidak ada
stopword yang lolos.

Yang muncul justru kosakata domain yang diharapkan:

- **Kegagalan layanan:** `batal`, `tolak`, `gagal`*, `hilang`, `blokir`, `kacau`
- **Waktu tunggu:** `jam`, `lama`, `lambat`, `satu jam`, `hampir jam`, `makan jam`
  — kelompok yang sangat menonjol pada Naive Bayes dan cocok dengan keluhan
  pencarian driver
- **Biaya:** `mahal`, `banyak promo`
- **Mitra driver:** `pengemudi`, `pengemudi ramah`, `tidak ramah`, `tidak sopan`
- **Pengalaman aplikasi:** `iklan`, `ganggu`, `susah`, `mudah`, `mudah guna`,
  `tidak ribet`, `permudah`

Tiga pengamatan tambahan yang layak masuk pembahasan:

**(1) Bigram membayar dirinya sendiri untuk menangani negasi.** Unigram `tidak`
adalah fitur negatif terkuat pada kedua model linear — masuk akal, tetapi
berbahaya bila berdiri sendiri. Yang menyelamatkannya: bigram `tidak ribet`,
`tidak kecewa`, dan `pernah kecewa` (dari "tidak pernah kecewa") muncul di
20 besar kelas **positif**, sementara `tidak ramah`, `tidak sopan`, `tidak bantu`
muncul di kelas **negatif**. Model membedakan arah negasi dari konteksnya. Ini
pembenaran empiris langsung untuk keputusan `ngram_range=(1,2)` di Fase 3, dan
sebaiknya dilaporkan sebagai bukti, bukan sebagai asumsi.

**(2) `bintang satu` sebagai fitur negatif adalah bahasa meta-ulasan.** Pengguna
menulis "saya kasih bintang satu karena..." di dalam teks. Modelnya benar, tetapi
sinyal ini datang dari kebiasaan menulis ulasan, bukan dari sentimen terhadap
layanan. Perlu disebut sebagai keterbatasan generalisasi: ia tidak akan tersedia
pada teks keluhan di kanal lain (surel, chat CS).

**(3) `the terbaik` — hibrida campur kode dari normalisasi slang.** Kamus slang
Fase 2 memetakan `best → terbaik` ([ml/src/slang_dict.py:68](../ml/src/slang_dict.py#L68)),
sehingga "gojek is the best" menjadi "gojek is the terbaik". Bigram ini muncul
538 kali, 523 di antaranya berating 5★ — **sinyalnya benar dan kuat**, sehingga
ini bukan kegagalan. Yang ditunjukkannya: normalisasi slang berjalan tanpa
penjaga bahasa, dan menghasilkan token hibrida. Pada kasus ini tidak merugikan;
pada korpus dengan porsi bahasa Inggris lebih besar, perilaku ini perlu ditinjau.

**Satu fitur yang lemah, dilaporkan apa adanya:** `kadang` menempati peringkat 16
kelas positif pada LinearSVC, padahal distribusi ratingnya di korpus praktis
merata (1★:239, 2★:94, 3★:135, 4★:198, 5★:240). Ia kemungkinan besar derau
peringkat, bukan sinyal. Satu fitur lemah dari 40 bukan alasan mengubah
pipeline, tetapi menyembunyikannya juga tidak benar.

**Kesimpulan untuk umpan balik ke Fase 2: tidak diperlukan.** Kriteria
pemicunya — "yang muncul artefak (nama orang, tanda baca, stopword yang lolos)"
— tidak terpenuhi. Pipeline Fase 2 lulus uji interpretabilitas ini.

Pemeriksaan top-feature hanya melihat kata yang **bertahan** melewati pipeline;
ia secara struktural tidak dapat memperlihatkan kata kunci yang **hilang**
karena stemming atau salah ketik. Jalur kedua itu ditutup oleh pemeriksaan
manual H-7, dan hasilnya sejalan: kegagalan preprocessing memang ada (16% dari
kesalahan) tetapi berupa ekor panjang salah ketik perorangan dengan jangkauan
korpus 0,12%, bukan cacat sistematis — lihat Bagian 3.4. Kedua jalur pemeriksaan
menyimpulkan hal yang sama, dan keduanya diperlukan untuk sampai ke sana.
