# DAFTAR KOREKSI UNTUK NASKAH EKSTERNAL

**Fase 9, T-9.4** · Status: siap dipakai · Disusun 19 September 2026

> **Batas peran (H-4):** naskah utama berada **di luar repositori** dan **tidak
> disentuh agent**. Dokumen ini adalah daftar perubahan yang harus dilakukan
> manusia pada naskah, lengkap dengan **kutipan pengganti yang siap tempel**.
> Setiap angka di bawah berasal dari berkas CSV di `docs/tables/` — tidak ada
> yang ditulis dari ingatan.

Cara pakai: kerjakan dari atas ke bawah, centang tiap baris setelah naskah
diperbarui, lalu jalankan pemeriksaan akhir di Bagian 8.

---

## Ringkasan Perubahan

| # | Item | Kondisi sekarang di naskah | Harus menjadi | Prioritas |
|---|------|---------------------------|---------------|-----------|
| 1 | Nama kolom (Temuan 1) | `content`, `at`, `score`, `reviewCreatedVersion`, `thumbsUpCount` | `Ulasan`, `Tanggal`, `Rating`, `Versi App`, `Likes`, `Nama User` | **Kritis** |
| 2 | Jumlah kelas (Temuan 3) | 3 kelas (negatif/netral/positif) | Biner sebagai model utama; 3 kelas sebagai eksperimen pembanding yang gagal | **Kritis** |
| 3 | Jumlah data | "100k+" | 100.000 baris, 21 Mei 2024 – 31 Des 2025 | Sedang |
| 4 | Sumber data | Sitasi Kaggle generik | Provenans lengkap: pengunggah, versi, SHA-256, "tanpa modifikasi" | **Kritis** |
| 5 | Algoritma | Naive Bayes & SVM | Tiga keluarga, empat varian; LogisticRegression model produksi | **Kritis** |
| 6 | Metrik | Akurasi | Recall negatif & macro-F1 utama; akurasi pelengkap dengan baseline 72,3% | **Kritis** |
| 7 | Tabel variabel | Berdasarkan asumsi | Berdasarkan `docs/data_contract.md` | Sedang |

---

## 1. Nama Kolom (Temuan 1) — **Kritis**

- [ ] Ganti seluruh penyebutan nama kolom di Bab 1 dan Bab 3.

**Mengapa:** naskah mengasumsikan konvensi *google-play-scraper*. Berkas aktual
memakai penamaan berbahasa Indonesia dari pengunggah Kaggle. Menyebut nama kolom
yang tidak ada di berkas adalah kesalahan faktual yang mudah diperiksa penguji.

| Naskah (asumsi awal) | Berkas aktual | Tipe |
|----------------------|---------------|------|
| `content` | `Ulasan` | str |
| `score` | `Rating` | int64 |
| `at` | `Tanggal` | str → datetime |
| `reviewCreatedVersion` | `Versi App` | str |
| `thumbsUpCount` | `Likes` | int64 |
| — (tidak disebut) | `Nama User` | str |

**Kutipan pengganti (siap tempel):**

> Dataset terdiri atas enam kolom dengan penamaan berbahasa Indonesia
> sebagaimana disediakan pengunggah: `Nama User`, `Ulasan`, `Rating`,
> `Tanggal`, `Likes`, dan `Versi App`. Penamaan ini berasal dari berkas sumber
> dan tidak diubah oleh peneliti; kolom `Ulasan` dan `Rating` menjadi dasar
> pemodelan, sementara `Nama User` tidak dipakai.

**Catatan penting:** jangan menulis bahwa peneliti me-*rename* kolom dari
konvensi `content`/`at`/`score` — tidak ada langkah transformasi seperti itu.
Sumber: `docs/data_provenance_notes.md`, `docs/data_contract.md`.

---

## 2. Jumlah Kelas (Temuan 3) — **Kritis**

- [ ] Ubah skema utama di Bab 1, Bab 3, dan seluruh rumusan masalah menjadi biner.
- [ ] Tambahkan subbab eksperimen 3 kelas beserta kegagalannya di Bab 4.

**Mengapa:** rating 3★ hanya 3.534 ulasan (3,5%), rasio 1:19 terhadap kelas
positif. Skema 3 kelas tetap dijalankan agar keputusan ini berbasis bukti, bukan
asumsi — dan hasilnya dilaporkan apa adanya.

**Kutipan pengganti (siap tempel):**

> Penelitian ini memakai skema pelabelan **biner**: ulasan berating 1–2 bintang
> dilabeli negatif dan 4–5 bintang dilabeli positif, sementara ulasan 3 bintang
> (3.534 ulasan; 3,5%) dikeluarkan dari pemodelan utama. Keputusan ini tidak
> diambil berdasarkan asumsi bahwa kelas netral terlalu kecil, melainkan diuji:
> skema tiga kelas dijalankan dengan protokol identik dan menghasilkan macro-F1
> 0,6470, turun 28,7 poin dari 0,9341 pada skema biner. Penurunan tersebut
> bersumber dari contoh netral yang tidak terpisahkan secara leksikal dari kelas
> negatif, bukan dari pemilihan *hyperparameter*. Hasil eksperimen tiga kelas
> dilaporkan sebagai temuan pada Subbab [nomor subbab eksperimen 3 kelas].

Sumber angka: `docs/three_class_experiment.md`, Gambar 7.

---

## 3. Jumlah dan Periode Data — Sedang

- [ ] Ganti "100k+" dengan angka pasti di seluruh naskah.

**Kutipan pengganti (siap tempel):**

> Dataset berisi **100.000 ulasan** yang mencakup periode **21 Mei 2024 hingga
> 31 Desember 2025** (20 bulan). Komposisi rating: 1 bintang 23.178 ulasan
> (23,2%), 2 bintang 3.554 (3,6%), 3 bintang 3.534 (3,5%), 4 bintang 5.083
> (5,1%), dan 5 bintang 64.651 (64,7%).

Sumber: `docs/tables/profil_dataset.csv`, `docs/tables/distribusi_rating.csv`.

---

## 4. Sumber & Provenans Data — **Kritis**

- [ ] Ganti sitasi dataset dengan provenans lengkap.
- [ ] Tambahkan tiga keterbatasan data sekunder di bagian Keterbatasan.

**Kutipan pengganti (siap tempel):**

> Data diperoleh dari dataset publik Kaggle "Gojek App Reviews Indonesia —
> Google Play Store" (pengunggah: `pandaa12`, versi 1), diunduh langsung tanpa
> proses transformasi tambahan oleh peneliti. Skema kolom, penamaan, dan isi
> berkas adalah sebagaimana disediakan oleh sumber. Integritas berkas
> diverifikasi dengan SHA-256
> `9b7f8e50737f9f17bce4ab8a44f7d2f8587deea86c6ad175e2579932cc22b524`
> (10.771.654 byte).

**Yang tidak boleh diklaim:**

- ❌ Bahwa peneliti melakukan *scraping* sendiri dengan `google-play-scraper`.
- ❌ Bahwa kolom di-*rename* oleh peneliti.

**Tambahan wajib di bagian Keterbatasan (siap tempel):**

> Karena berkas berasal dari unggahan pihak ketiga, tiga hal tidak dapat
> diverifikasi peneliti: (1) metode pengambilan data oleh pengunggah asli —
> parameter *scraping*, filter bahasa, dan rentang tanggal yang diminta tidak
> terdokumentasi; (2) apakah dataset merupakan sensus atau sampel dari seluruh
> ulasan pada periode tersebut; dan (3) kemungkinan adanya penyaringan oleh
> pengunggah sebelum data diunggah. Ketiganya lazim pada penelitian berbasis
> data sekunder dan tidak membatalkan analisis, sepanjang dinyatakan.

Sumber: `docs/data_provenance_notes.md`.

---

## 5. Algoritma (H-10) — **Kritis**

- [ ] Ganti "Naive Bayes dan SVM" dengan tiga keluarga / empat varian.
- [ ] Nyatakan LogisticRegression sebagai model produksi beserta alasan teknisnya.

**Kutipan pengganti (siap tempel):**

> Penelitian membandingkan **tiga keluarga algoritma dalam empat varian**:
> Naive Bayes (ComplementNB dan MultinomialNB), Support Vector Machine
> (LinearSVC), dan regresi logistik (LogisticRegression). ComplementNB
> disertakan karena dirancang untuk distribusi kelas tak seimbang — relevan
> pada data yang 72,3% positif. LinearSVC dipilih menggantikan SVC berkernel
> RBF karena pada representasi TF-IDF berdimensi 30.000 fitur, kernel
> non-linear menambah biaya komputasi satu ordo besaran tanpa keuntungan
> akurasi yang terbukti.
>
> **Model produksi yang dipilih adalah LogisticRegression** (`C=1.0`,
> `class_weight="balanced"`). Pemilihan tidak didasarkan pada skor tertinggi,
> melainkan pada kerangka keputusan yang ditetapkan sebelum evaluasi: bila
> LinearSVC unggul sekurang-kurangnya 2 poin macro-F1, ia menjadi model
> produksi; bila selisihnya di bawah 2 poin, dipilih model yang lebih sederhana
> dan menghasilkan probabilitas secara langsung. Selisih yang teramati hanya
> **0,03 poin** pada set `full` — dan LinearSVC justru **kalah 0,05 poin** pada
> set `informative_ge5w`. LogisticRegression juga menghasilkan 56 alarm palsu
> lebih sedikit dengan presisi kelas negatif tertinggi (0,8845).

Sumber: `docs/model_decision.md`, `docs/tables/model_metrics.csv`.

---

## 6. Metrik Evaluasi — **Kritis**

- [ ] Ganti akurasi sebagai metrik utama.
- [ ] Sertakan baseline 72,3% di **setiap** tabel hasil model.
- [ ] Tambahkan pembahasan selisih `full` vs `informative_ge5w`.

**Mengapa:** pada data yang 72,3% positif, model yang selalu menebak "positif"
sudah mencapai akurasi 72,3% tanpa mempelajari apa pun — macro-F1-nya hanya
0,4196 dan recall negatifnya 0,0000. Akurasi tanpa baseline tidak bermakna.

**Kutipan pengganti (siap tempel):**

> Metrik utama penelitian ini adalah **macro-F1** dan **recall kelas negatif**,
> dengan akurasi sebagai pelengkap. Alasannya melekat pada tujuan: sistem
> ditujukan untuk triase keluhan, sehingga keluhan yang lolos klasifikasi
> berbiaya lebih tinggi daripada alarm palsu. Seluruh angka dibandingkan
> terhadap **baseline mayoritas** yang selalu memprediksi kelas positif —
> akurasi 72,3%, macro-F1 0,4196, dan recall negatif 0,0000. Setiap model
> dilaporkan pada dua set evaluasi: `full` (seluruh test set) dan
> `informative_ge5w` (hanya ulasan ≥5 kata).

**Tabel hasil yang siap tempel** (model *tuned*, latih dengan dedup):

| Model | macro-F1 `full` | macro-F1 `informative` | recall neg `full` | presisi neg `full` | akurasi `full` |
|-------|-----------------|------------------------|-------------------|--------------------|----------------|
| LinearSVC | **0,9341** | 0,9066 | 0,9370 | 0,8769 | 0,9461 |
| **LogisticRegression** (produksi) | 0,9338 | **0,9071** | 0,9267 | **0,8845** | 0,9461 |
| MultinomialNB | 0,9296 | 0,9016 | 0,9428 | 0,8610 | 0,9420 |
| ComplementNB | 0,9153 | 0,8987 | **0,9553** | 0,8182 | 0,9288 |
| *Baseline mayoritas* | *0,4196* | *0,3173* | *0,0000* | *0,0000* | *0,7229* |

Model final yang diterapkan ke seluruh korpus: macro-F1 0,9336 (`full`) dan
0,9078 (`informative_ge5w`); recall negatif 0,9316 dan 0,9536.

**Pembahasan selisih evaluasi (siap tempel):**

> Selisih macro-F1 antara kedua set evaluasi pada model produksi adalah
> **2,59 poin** (0,9336 → 0,9078). Selisih ini merupakan temuan metodologis
> tersendiri, bukan sekadar catatan teknis: 39,9% ulasan dalam korpus hanya
> berisi dua kata atau kurang dan hampir seluruhnya positif, sehingga evaluasi
> pada test set penuh sebagian mengukur kemampuan model mengenali kata seperti
> "bagus" dan "mantap". Angka pada set `informative_ge5w` karena itu merupakan
> ukuran kemampuan yang lebih jujur pada teks yang benar-benar membawa
> informasi.

Sumber: `docs/tables/model_metrics.csv`, Gambar 10 dan Gambar 11.

---

## 7. Tabel Variabel Penelitian — Sedang

- [ ] Ganti tabel variabel dengan versi berbasis `docs/data_contract.md`.

**Tabel pengganti (siap tempel):**

| Kolom | Tipe | Nullable | Peran dalam penelitian |
|-------|------|----------|------------------------|
| `Nama User` | str | tidak | Tidak dipakai untuk pemodelan |
| `Ulasan` | str | tidak | **Variabel bebas** — teks mentah, tidak pernah diubah |
| `Rating` | int64 (1–5) | tidak | **Sumber variabel terikat** via pemetaan biner |
| `Tanggal` | datetime | tidak | Analisis tren temporal |
| `Likes` | int64 | tidak | Bobot perhatian; median 0, 83,7% bernilai nol |
| `Versi App` | str | **ya (21,9%)** | Analisis per-versi; **tidak diimputasi** |

Variabel turunan yang dibentuk peneliti:

| Variabel | Definisi |
|----------|----------|
| `sentimen_aktual` | `0` bila `Rating ∈ {1,2}`; `1` bila `Rating ∈ {4,5}`; `NULL` bila `Rating = 3` |
| `word_count` | Jumlah token atas teks ternormalisasi (setelah normalisasi slang, sebelum stemming) |
| `versi_minor` | `Versi App` dipotong dua segmen: `4.93.1` → `4.93` |
| `bulan` | `Tanggal` dipotong ke periode bulanan |

Sumber: `docs/data_contract.md`.

---

## 8. Pemeriksaan Akhir Naskah

Setelah seluruh koreksi di atas diterapkan, periksa hal-hal berikut secara
manual pada naskah:

- [ ] Tidak ada lagi penyebutan `content`, `score`, `at`, `reviewCreatedVersion`,
      atau `thumbsUpCount` di mana pun.
- [ ] Tidak ada lagi klaim skema tiga kelas sebagai model utama.
- [ ] Tidak ada lagi penanda isian yang belum terisi — rujukan berkurung
      siku berawalan huruf A atau T, maupun penanda sementara lain yang
      biasa dipakai saat menyusun draf.
- [ ] Baseline 72,3% muncul di setiap tabel hasil model.
- [ ] Setiap angka dapat ditelusuri ke berkas di `docs/tables/` atau ke sel
      notebook di `ml/notebooks/`.
- [ ] Seluruh gambar diambil dari `docs/figures/final/` (300 dpi), bukan dari
      tangkapan layar notebook.
- [ ] Bagian Keterbatasan memuat ketujuh poin `docs/limitations.md`.
- [ ] Nomor gambar di naskah konsisten dengan penomoran `docs/figures/final/`
      (lihat tabel padanan di bawah).

### Padanan Nomor Gambar

| Berkas di `docs/figures/final/` | Isi |
|--------------------------------|-----|
| `gambar-01-distribusi-rating.png` | Distribusi rating |
| `gambar-02-panjang-per-rating.png` | Rata-rata kata per rating |
| `gambar-03-distribusi-wordcount.png` | Distribusi `word_count` |
| `gambar-04-volume-bulanan.png` | Volume ulasan per bulan |
| `gambar-05-cakupan-versi.png` | Cakupan per ambang versi |
| `gambar-06-confusion-matrix.png` | Confusion matrix model produksi |
| `gambar-06b-confusion-matrix-linear-svc.png` | Confusion matrix LinearSVC (pembanding) |
| `gambar-07-tiga-kelas.png` | Hasil eksperimen tiga kelas |
| `gambar-08-lda-coherence.png` | Coherence vs jumlah topik |
| `gambar-08b-ngram-negatif.png` | N-gram paling menandai kelas negatif |
| `gambar-09-peringkat-topik.png` | Peringkat topik keluhan |
| `gambar-10-perbandingan-model.png` | Perbandingan macro-F1 `full` vs `informative` |
| `gambar-11-selisih-evaluasi.png` | Selisih antar set evaluasi |
| `gambar-12-waktu-latih.png` | Waktu latih per model |
| `gambar-13-dashboard.png` | Tangkapan layar dashboard |
