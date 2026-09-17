# ANALISIS KESALAHAN & INTERPRETASI FITUR

**Fase 4, T-4.4 & T-4.5**

> ## ⛔ STATUS: GERBANG H-7 TERBUKA — MENUNGGU PEMERIKSAAN MANUSIA
>
> Bagian 5 dokumen ini (distribusi kategori penyebab) **sengaja kosong**.
> Berkas kerja `docs/tables/error_analysis_50.csv` sudah dihasilkan dengan kolom
> `kategori_penyebab` kosong dan menunggu diisi manusia. Bagian 1–4 dan 6 sudah
> lengkap karena seluruhnya dapat dihitung secara mekanis.

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

## 3. Distribusi Kategori Penyebab — ⛔ MENUNGGU H-7

*(Bagian ini diisi setelah `docs/tables/error_analysis_50.csv` dikembalikan
dengan kolom `kategori_penyebab` terisi manusia. Agent tidak mengisinya sendiri:
menilai sarkasme dan menilai apakah bintang yang diberikan bertentangan dengan
isi tulisan adalah penilaian bahasa dan konteks, bukan sesuatu yang dapat
disimpulkan agent dari teks.)*

Taksonomi yang tersedia (nilai sah untuk kolom tersebut):

| Nilai kolom | Kategori | Contoh |
|-------------|----------|--------|
| `sarkasme_ironi` | Sarkasme / ironi | "mantap banget, 2 jam nggak dapet driver" |
| `negasi_kompleks` | Negasi kompleks | "bukan berarti tidak bagus, tapi..." |
| `campur_kode` | Campur kode | "app nya so bad, please fix lah" |
| `label_keliru_pengguna` | Label keliru dari pengguna | Rating 5 tapi isinya keluhan |
| `terlalu_pendek_ambigu` | Terlalu pendek / ambigu | "ok" pada rating 1 |
| `topik_netral_offtopic` | Topik netral / off-topic | "test", "belum coba" |
| `kegagalan_preprocessing` | Kegagalan preprocessing | kata kunci hilang karena stemming/stopword |

Dua hal yang harus dijawab begitu distribusinya tersedia:

1. **Bila `label_keliru_pengguna` dominan** → batas atas kinerja yang realistis
   pada dataset ini lebih rendah dari 100%, dan angka itu harus dinyatakan di
   pembahasan. macro-F1 0,93 kemudian perlu dibaca relatif terhadap batas itu,
   bukan relatif terhadap kesempurnaan.
2. **Bila `kegagalan_preprocessing` signifikan** → kategori ini *actionable*:
   kembali ke Fase 2, perbaiki, jalankan ulang Fase 3–4. Ini umpan balik yang
   sah dan sudah dianggarkan satu iterasi dalam rencana.

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

*Satu-satunya jalur yang masih dapat memicu perbaikan Fase 2 adalah kategori
`kegagalan_preprocessing` pada pemeriksaan manual H-7 (Bagian 3).* Pemeriksaan
top-feature hanya melihat kata yang **bertahan** melewati pipeline; ia secara
struktural tidak dapat memperlihatkan kata kunci yang **hilang** karena stemming
atau stopword. Hanya pembacaan manual atas ulasan asli yang dapat menemukan itu,
dan itulah salah satu alasan gerbang H-7 ada.
