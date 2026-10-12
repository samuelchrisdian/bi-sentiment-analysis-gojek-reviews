# TEMUAN EKSTRAKSI TOPIK — FASE 5 (T-5.1 s/d T-5.3)

Seluruh angka berasal dari `ml/src/topics.py` dan `ml/src/topic_assign.py` yang
dijalankan pada data scraping Google Play lima tahun (526.322 ulasan), bukan
estimasi. Berkas: `docs/tables/ngram_negatif.csv`, `docs/tables/lda_coherence.csv`,
`docs/tables/lda_clusters_for_labeling.csv`, Gambar 8 dan 8b. Angka yang
ditandai "diukur ulang" dihitung read-only dari `data/processed/*.parquet` dan
`data/processed/lda_doc_topic.npy`.

> **Status:** Lengkap. Kelima kategori sudah dinamai penulis (nama final di
> `docs/tables/lda_clusters_for_labeling_reviewed.csv`) dan divalidasi silang
> oleh penilai independen (§11). Aturan penamaan: `docs/topic_labeling_rules.md`.

## 1. Korpus Topik

| Properti | Nilai |
|----------|-------|
| Ulasan negatif (rating 1–2, label 0) | 145.924 |
| **Korpus topik** (`word_count` ≥ 5) | **125.834** |
| Dibuang karena terlalu pendek | 20.090 (13,77%) |
| Duplikat teks di korpus topik | 484 (0,38%) |
| Rata-rata panjang | 23,43 kata |
| Kamus setelah `filter_extremes` | 5.399 token |

<!-- src: diukur ulang dari data/processed/reviews_clean.parquet dan ml/artifacts/lda_dictionary.gensim -->

**Ambang `word_count >= 5` berlaku untuk seluruh grafik dan tabel topik** dan
dinyatakan di keterangan masing-masing.

Pemilihan korpus negatif terbukti menguntungkan: duplikasi teks hanya
**0,38%** di sini, berbanding 50,6% pada ulasan positif, dan ulasan negatif
jauh lebih panjang (rata-rata 20,3 kata untuk rating 1, berbanding 4,3 kata untuk
rating 5). LDA memperoleh materi yang layak, bukan pengulangan pujian dua kata.
<!-- src: facts.yaml asimetri_panjang.pct_duplikat_positif, rata_kata_per_rating -->

Korpus ini memuat 6.601 ulasan (5,25%) hasil terjemahan mesin dari ulasan yang
dominan berbahasa Inggris (diukur ulang dengan mencocokkan teks terhadap
`data/interim/terjemahan_inggris.csv`). Pengaruhnya pada klaster dibahas di §4.

## 2. Frekuensi N-gram (T-5.2)

Dikerjakan sebelum LDA, sehingga berfungsi sebagai temuan mandiri sekaligus
rujukan manusia saat menamai klaster.
`CountVectorizer(ngram_range=(1,2), min_df=10)`, dihitung pada `ulasan_clean`.

### 2.1 Unigram teratas

| # | Term | Frekuensi | % dokumen |
|---|------|-----------|-----------|
| 1 | tidak | 122.019 | 60,17% |
| 2 | pengemudi | 56.289 | 28,24% |
| 3 | aplikasi | 44.096 | 27,52% |
| 4 | bisa | 43.518 | 26,52% |
| 5 | gojek | 38.783 | 23,46% |
| 6 | ada | 37.225 | 23,16% |
| 7 | nya | 32.275 | 18,80% |
| 8 | mau | 23.267 | 15,70% |
| 9 | pakai | 23.267 | 14,80% |
| 10 | dapat | 22.692 | 13,83% |

**`tidak` muncul di 60% ulasan negatif dan `pengemudi` di 28%.** Kedua angka itu
sendiri sudah merupakan temuan: keluhan pada aplikasi ini dominan berbentuk
*ketiadaan layanan* atau *kegagalan fungsi*, dan mitra driver adalah entitas
yang paling sering disebut.

**Catatan yang harus menyertai tabel ini:** `ada`, `bisa`, `dapat`, `mau`
bertahan karena **sengaja dipertahankan** di `NEGATION_KEEP` (keputusan saat
verifikasi pra-pemrosesan). Membuangnya menghancurkan struktur negasi; dengan
daftar ini frasa "tidak bisa" bertahan utuh di 33.766 dokumen (lihat
`docs/preprocessing_validation.md` §2). Kehadirannya di peringkat atas adalah
konsekuensi yang diketahui dan diterima, bukan kebocoran stopword.

Konsekuensinya, **unigram kurang informatif untuk penamaan topik** dan bigram
harus menjadi rujukan utama.

### 2.2 Bigram teratas — jauh lebih informatif

| # | Term | Frekuensi | % dokumen |
|---|------|-----------|-----------|
| 1 | tidak bisa | 29.812 | 19,97% |
| 2 | tidak ada | 18.252 | 12,66% |
| 3 | **dapat pengemudi** | 8.862 | 6,11% |
| 4 | tidak jelas | 6.413 | 4,73% |
| 5 | **layan pelanggan** | 6.231 | 4,16% |
| 6 | **ongkos kirim** | 5.477 | 3,36% |
| 7 | tiba tiba | 5.230 | 3,91% |
| 8 | tidak dapat | 5.221 | 3,81% |
| 9 | **pengemudi tidak** | 4.360 | 3,26% |
| 10 | pengemudi nya | 4.041 | 2,86% |
| 11 | **cari pengemudi** | 4.029 | 3,02% |
| 12 | tidak pernah | 3.886 | 2,90% |
| 13 | bisa pakai | 3.717 | 2,68% |
| 14 | aplikasi gojek | 3.704 | 2,73% |
| 15 | aplikasi tidak | 3.663 | 2,83% |
| 16 | tidak mau | 3.476 | 2,52% |
| 17 | **top up** | 3.471 | 2,38% |
| 18 | **tidak masuk** | 3.318 | 2,48% |
| 22 | **bisa batal** | 2.827 | 2,01% |
| 25 | **tunggu lama** | 2.544 | 1,91% |
| 29 | **tunggu jam** | 2.277 | 1,70% |

Bigram bertanda tebal membawa isi keluhan yang dapat dipetakan ke kategori
bisnis; unigram tidak. Ini mengonfirmasi perkiraan rencana bahwa bigram lebih
informatif, dan menjadi alasan `ngram_range=(1,2)` dipertahankan.

Empat kelompok terbaca langsung dari bigram saja, **sebelum** LDA dijalankan:
ketersediaan dan penugasan pengemudi (`dapat pengemudi`, `cari pengemudi`,
`tunggu lama`, `tunggu jam`, `bisa batal`), kanal bantuan (`layan pelanggan`),
biaya (`ongkos kirim`), dan transaksi saldo (`top up`, `tidak masuk`). Bigram
`top up` sendiri adalah hasil perbaikan pra-pemrosesan putaran 1; sebelumnya
frasa ini rusak menjadi "bagus up".

## 3. LDA — Pemilihan Jumlah Topik (T-5.3)

Parameter dicatat lengkap karena LDA stokastik dan reprodusibilitasnya
bergantung sepenuhnya padanya:

| Parameter | Nilai |
|-----------|-------|
| `random_state` | 42 |
| `passes` | 10 |
| `iterations` | 100 |
| `alpha` | `"auto"` |
| `filter_extremes` | `no_below=10, no_above=0.5` |
| Rentang k | 5–12 (`topics.lda_n_topics_range` di `config.yaml`) |

### 3.1 Coherence per jumlah topik

| k | c_v | u_mass |
|---|-----|--------|
| **5** | **0,5908** | −2,4495 |
| 6 | 0,5561 | −2,7065 |
| 7 | 0,5837 | −2,8050 |
| 8 | 0,5880 | −3,0186 |
| 9 | 0,5251 | −3,3216 |
| 10 | 0,5541 | −3,6043 |
| 11 | 0,5158 | −3,7259 |
| 12 | 0,5673 | −3,5663 |

<!-- src: docs/tables/lda_coherence.csv; facts.yaml topik.lda_k, topik.coherence_cv -->

**k = 5 terpilih** — puncak c_v (0,5908). Kandidat terdekat adalah k = 8
(0,5880), selisih hanya 0,0028. Aturan "bila ada puncak lain dalam 0,005, pilih
k yang lebih kecil" tidak mengubah pilihan karena puncaknya sendiri sudah k
terkecil. u_mass juga terbaik di k = 5 dan memburuk hampir monoton seiring k.
Gambar 8.

**k = 5 jatuh tepat di batas bawah rentang pemindaian.** Kriteria (a) pada
hipotesis tema keluhan — "nilai k terpilih berada di dalam rentang pemindaian
dan bukan di batasnya" — karenanya **tidak terpenuhi**, dan dilaporkan apa
adanya. Rentang 5–12 ditetapkan di `config.yaml` sebelum hasil dibaca dan
**tidak diubah** sesudahnya; memperluasnya ke bawah setelah melihat hasil akan
menjadikan rentang itu parameter yang disetel pada data uji. Hasil yang sama
(k = 5 di batas bawah) muncul baik pada LDA awal maupun setelah LDA dilatih
ulang pada korpus hasil perbaikan pra-pemrosesan.

Kurvanya tidak monoton (k=6 turun, k=7–8 naik, k=9 anjlok). Ini lazim pada c_v
dan berarti **k = 5 sebaiknya tidak dibaca sebagai "jumlah topik yang benar"**,
melainkan sebagai jumlah yang memberi klaster paling koheren dalam rentang yang
diuji. Fakta bahwa puncaknya di batas bawah juga berarti tidak dapat
disimpulkan apakah k < 5 akan lebih koheren.

### 3.2 Lima klaster — ukuran dan kata kunci

`topic_id` mengikuti LDA final. Nama kategori adalah nama final dari penulis
(§3.3); kata teratas adalah keluaran algoritma:

| Topik | Kategori final | % dokumen dominan | n | 10 kata teratas |
|-------|----------------|-------------------|---|-----------------|
| 3 | Kendala Penggunaan Aplikasi & Akses Akun | **40,16%** | 50.533 | bisa, aplikasi, nya, mau, gojek, pakai, terus, padahal, akun, aja |
| 2 | Pencarian & Penugasan Driver, Waktu Tunggu & Pembatalan Pesanan | 29,24% | 36.788 | pengemudi, dapat, pesan, lama, kalau, batal, order, tunggu, nya, jauh |
| 1 | Layanan Pelanggan & Penanganan Keluhan | 15,20% | 19.126 | ada, gojek, layan, pelanggan, kasih, sangat, aku, guna, bantu, kecewa |
| 4 | Tarif, Ongkir & Promo | 9,55% | 12.018 | makin, kirim, voucher, promo, biaya, mahal, sekarang, ongkos, harga, gojek |
| 0 | Transaksi, Saldo & Pemblokiran GoPay | 5,86% | 7.369 | gopay, saldo, bayar, blokir, masuk, up, uang, transaksi, top, hari |

<!-- src: docs/tables/lda_clusters_for_labeling.csv; docs/tables/lda_clusters_for_labeling_reviewed.csv -->

Distribusinya timpang: topik 3 sendiri menguasai 40,16% dokumen, sementara
topik 0 hanya 5,86% (rasio 6,9×).

**Klaster terbesar bersifat umum.** Kata teratas topik 3 hampir seluruhnya kata
fungsi dan kata umum (`bisa`, `aplikasi`, `nya`, `mau`, `padahal`); hanya
`akun` yang spesifik. Contoh tipikalnya mencakup aplikasi tidak bisa dibuka,
verifikasi wajah gagal, keluar sendiri, dan permintaan pembaruan. **Jangan
menafsirkan 40,16% sebagai proporsi masalah akun atau login** — penetapan
berbasis kata kunci (§7) hanya menempatkan 12,56% ulasan negatif ke kategori
ini.

### 3.3 Penamaan kategori dan pelatihan ulang LDA

Penamaan dilakukan penulis atas dasar kata teratas dan contoh tipikal tiap
klaster; usulan awal berbantuan model bahasa dinilai dan direvisi penulis.
Riwayatnya tercatat di kolom `status_pelabelan` dan `catatan_perubahan` pada
`lda_clusters_for_labeling_reviewed.csv`:

| Topik final | Topik LDA awal | Nama awal | Nama final | Alasan perubahan |
|-------------|----------------|-----------|------------|------------------|
| 2 | 2 | Ketersediaan Driver, Waktu Tunggu & Pembatalan Pesanan | Pencarian & Penugasan Driver, Waktu Tunggu & Pembatalan Pesanan | "Ketersediaan" menyiratkan stok driver kosong; beberapa contoh justru menyebut driver dekat tersedia tetapi sistem menugaskan driver yang jauh |
| 3 | 1 | Akun, Login & Pembaruan Aplikasi | Kendala Penggunaan Aplikasi & Akses Akun | Nama awal terlalu sempit untuk klaster terbesar yang heterogen |
| 1 | 4 | Layanan Pelanggan & Pemblokiran Akun | Layanan Pelanggan & Penanganan Keluhan | Setelah LDA dilatih ulang, `blokir` berpindah ke klaster GoPay; kata kunci klaster ini murni layanan pelanggan (`layan`, `pelanggan`, `bantu`, `masalah`, `mohon`, `selesai masalah`) |
| 0 | 0 | Transaksi & Saldo GoPay | Transaksi, Saldo & Pemblokiran GoPay | `blokir` kini kata kunci klaster ini (bersama `gopay`, `saldo`, `bayar`, `top up`, `denda`) |
| 4 | 3 | Tarif, Ongkir & Promo | (tidak berubah) | — |

**LDA dilatih ulang setelah perbaikan pra-pemrosesan putaran 1–3**, karena
`ulasan_clean` berubah (misalnya "top up" tidak lagi menjadi "bagus up").
Penamaan tidak diulang dari nol: kelima topik LDA baru cocok satu-satu dengan
lima topik yang sudah dinamai penulis — 83,6% dokumen korpus topik tetap
berada di topik dominan yang sama — sehingga nama dipetakan ke `topic_id` baru
dan nomor semula disimpan di kolom `topic_id_lda_awal`.
<!-- src: pesan commit 8058d1e; docs/tables/lda_clusters_for_labeling_reviewed.csv (topic_id_lda_awal). Model LDA awal tidak disimpan, sehingga 83,6% tidak dapat dihitung ulang dari artefak saat ini. -->

Satu pergeseran berdampak pada nama: kata `blokir` berpindah dari klaster
layanan pelanggan ke klaster GoPay. Karena itu dua nama direvisi atas
persetujuan penulis (11 Oktober 2026) — "Layanan Pelanggan & Pemblokiran Akun"
menjadi **Layanan Pelanggan & Penanganan Keluhan**, dan "Transaksi & Saldo
GoPay" menjadi **Transaksi, Saldo & Pemblokiran GoPay**. Pangsa klaster
terbesar juga bergeser dari 44,03% (LDA awal, angka yang masih disebut di
`catatan_perubahan` topik 3) menjadi 40,16%.

## 4. Catatan Metodologis untuk Pembaca Berkas Klaster

**Contoh berprobabilitas tertinggi tidak mewakili klaster.** Pada data ini
penyebabnya bukan lagi ulasan berisi pengulangan satu kata: sejak emoji identik
berurutan dihitung sekali (perbaikan pra-pemrosesan putaran 1), hanya 3 dari
125.834 dokumen korpus topik yang terdiri dari satu token unik. Penyebabnya
kini **teks terjemahan mesin** (diukur ulang):

- **Topik 0 (GoPay):** kelima `contoh_prob_*` adalah ulasan **berbahasa
  Vietnam** yang ikut terdeteksi sebagai "dominan Inggris" lalu diterjemahkan
  MarianMT menjadi teks rusak (misalnya "Quo coi théng khách hàng. Akun vác xác
  théc…"). Dari 20 dokumen berprobabilitas tertinggi topik ini, 19 bertipe sama.
  Korpus topik memuat 140 dokumen semacam ini (≥15% hurufnya huruf Latin
  ber-diakritik), 138 di antaranya dominan di topik 0. Di seluruh berkas
  terjemahan, 153 dari 14.671 teks asli memuat ≥3 huruf khas Vietnam.
- **Topik 1 (Layanan Pelanggan):** 4 dari 5 `contoh_prob_*` adalah terjemahan
  mesin berbahasa baku-kaku ("Imo, fitur peringkat kostum sangat
  menjengkelkan…"). Terjemahan menyusun 21,15% dokumen dominan topik 1,
  berbanding 5,25% di seluruh korpus topik — kemungkinan karena terjemahan
  memakai kosakata baku seperti "layanan pelanggan" dan "bantuan"
  (dugaan, belum diuji).
- Topik 2, 3, dan 4 tidak memuat terjemahan maupun teks Vietnam di 20 contoh
  berprobabilitas tertingginya.

Jumlahnya kecil terhadap korpus (140 dokumen = 0,11%), jadi bukan cacat yang
mengubah peringkat kategori, tetapi cukup untuk menyesatkan bila klaster
dinilai hanya dari peringkat teratas.

Karena itu `lda_clusters_for_labeling.csv` memuat **dua jenis contoh**:

- `contoh_prob_1..5` — probabilitas topik tertinggi
- `contoh_tipikal_1..5` — **acak** dari dokumen yang topik ini dominan dan
  panjangnya 10–60 kata, yaitu yang benar-benar mewakili klaster

Gunakan kolom `contoh_tipikal_*` sebagai dasar penilaian utama.

## 5. Catatan Perkakas

Rencana menyebut *word cloud* sebagai gambar pelengkap dengan catatan eksplisit
"jangan jadikan ini bukti utama; tabel frekuensi lebih bisa
dipertanggungjawabkan". Pustaka `wordcloud` tidak termasuk dependensi yang
dikunci, dan tidak dipasang hanya untuk gambar pelengkap.

Gantinya Gambar 8b: batang berurut untuk 20 unigram dan 20 bigram teratas.
Panjang batang dapat dibaca sebagai angka, sedangkan ukuran huruf pada word
cloud tidak — sehingga substansi yang diminta tetap terpenuhi, bahkan lebih
dapat dipertanggungjawabkan. Bila *word cloud* tetap dikehendaki untuk laporan,
pemasangan `wordcloud` adalah perubahan satu baris di daftar dependensi dan
merupakan keputusan pemilik proyek.

---

# BAGIAN II — PENETAPAN TOPIK & PERINGKAT (T-5.5 s/d T-5.8)

Sumber: `ml/src/topic_assign.py`. Nama kategori dibaca dari
`docs/tables/lda_clusters_for_labeling_reviewed.csv`; aturan pelabelan dan
pelabelnya di `docs/topic_labeling_rules.md`.

## 6. Pemilihan Kata Kunci per Kategori

Kata kunci tidak diketik manual. Ia diturunkan dari model dengan tiga saringan
berurutan, sehingga dapat direproduksi dan diaudit.

**(a) Relevance** (Sievert & Shirley, 2014 — ukuran yang sama dipakai pyLDAvis),
λ = 0,6:

> relevance(w,t) = λ·log p(w|t) + (1−λ)·log( p(w|t) / p(w) )

Suku kedua menghukum kata yang sering di seluruh korpus. Tanpa itu setiap
kategori memperoleh kata kunci `gojek`, `aplikasi`, `nya`, `ada` — benar secara
probabilitas, tidak membedakan apa pun.

**(b) `MAX_DF_KORPUS = 0,15`.** Kata yang muncul di >15% korpus topik dibuang.
Tanpa ini `bisa` (26,52% dokumen) dan `aplikasi` (27,52%) — dua kata teratas
klaster terbesar — menjadi kata kunci "Kendala Penggunaan Aplikasi & Akses
Akun" dan mencocoki lebih dari seperempat korpus.

**(c) `MIN_LIFT = 2,0`.** Kata harus ≥2× lebih terkonsentrasi pada dokumen
dominan topiknya dibanding pangsa topik itu. Ambang **rasio**, bukan mutlak,
agar tidak berat sebelah terhadap topik besar. Pada data ini efeknya justru
berbalik untuk klaster terbesar: dengan pangsa 40,16%, sebuah kata harus
≥80,3% kemunculannya berada di topik 3 agar lolos (lihat §11.2).

Bigram ditetapkan dengan prinsip yang sama: sebuah bigram (frekuensi ≥150)
masuk kategori tempat ≥35% kemunculannya terkonsentrasi, dibatasi 15 teratas
per kategori. Tanpa batas itu sebarannya sangat timpang (diukur ulang): Kendala
Aplikasi menarik 591 bigram dan Pencarian Driver 507, sementara GoPay hanya 28.

**Hasil: 125 kata kunci (50 unigram + 75 bigram), tepat 25 per kategori**
(10 unigram dari batas `N_KATA_KUNCI = 10`, 15 bigram). DoD menuntut ≥5 per
kategori — terpenuhi seluruhnya. Berkas: `docs/tables/topic_keywords.csv`
(memuat kolom `lift` dan `df_korpus`, sehingga kata kunci lemah terlihat, bukan
tersembunyi).

### 6.1 Tabrakan kata kunci

Satu kata kunci hanya boleh milik satu kategori; bila sebuah kata lolos di dua
kategori, **lift tertinggi menang** (`buang_tabrakan()`). Pada data ini **tidak
ada tabrakan**: hanya ada satu kategori pembayaran, sehingga `gopay` (lift
4,36) hanya muncul di "Transaksi, Saldo & Pemblokiran GoPay".

### 6.2 Kata kunci yang perlu dibaca hati-hati

- **`sen`** (Pencarian Driver, lift 2,20) adalah artefak stemming: ragam
  informal `pesen`/`pesenan` belum ada di kamus slang dan di-stem menjadi
  `sen`. Maknanya tetap "pesan", sehingga penempatannya di kategori pemesanan
  masuk akal (lihat `docs/preprocessing_validation.md` §6).
- **`up`** dan **`top`** (GoPay) berasal dari "top up", tetapi `up` juga
  mencocoki kata Inggris pada ulasan pendek yang tidak diterjemahkan (contoh
  pada validasi silang: "Driver rarely picks up" masuk kategori GoPay).
- **`makin`** (Tarif, lift 3,49), **`daftar`** dan **`buka`** (Kendala
  Aplikasi), serta **`guna`** dan **`masalah`** (Layanan Pelanggan) khas secara
  statistik tetapi bermakna umum; sebagian contoh Tabel 3 masuk kategorinya
  hanya karena kata ini (§10).

## 7. Penetapan Topik per Ulasan (T-5.5)

### 7.1 Pendekatan A — berbasis kata kunci (RESMI)

Dijalankan pada **seluruh 145.924 ulasan negatif**, bukan hanya korpus LDA:
pencocokan kata kunci tidak menuntut panjang minimum, dan DoD meminta proporsi
ulasan negatif yang memperoleh ≥1 topik.

Pencocokan unigram dilakukan pada level **token**, bukan substring. Ini penting:
`bayar` sebagai substring juga cocok dengan `pembayaran` dan `membayarkan`,
yang membuat cakupan tampak lebih tinggi daripada sebenarnya.

| Metrik | Nilai |
|--------|-------|
| Ulasan dengan ≥1 kategori | **112.724 / 145.924 = 77,25%** (DoD: ≥60%) |
| Tanpa kategori | 33.200 (22,75%) |
| Rata-rata kategori per ulasan berkategori | 1,63 |
| Baris `review_topics` | 183.542 |

<!-- src: facts.yaml topik.n_penetapan_kategori; diukur ulang dari data/processed/topics.parquet -->

Sebaran jumlah kategori per ulasan berkategori: 1 kategori 60.678 ulasan,
2 kategori 36.199, 3 kategori 13.067, 4 kategori 2.635, 5 kategori 145.

**Kategori tidak saling eksklusif.** Satu ulasan boleh masuk lebih dari satu
kategori — diizinkan eksplisit oleh rencana, dan wajar karena satu keluhan
sering menyinggung beberapa hal sekaligus. Konsekuensinya jumlah seluruh
penetapan (183.542) melebihi jumlah ulasan berkategori (112.724), dan itu
**bukan kesalahan penghitungan**. Keterangan ini wajib menyertai setiap tabel
peringkat.

### 7.2 Pendekatan B — berbasis LDA (pembanding)

Topik dominan dengan ambang probabilitas ≥ 0,3; di bawah ambang tidak diberi
topik. Hanya terdefinisi pada korpus LDA (125.834 ulasan).

| Metrik | Nilai |
|--------|-------|
| Memperoleh topik (prob ≥ 0,3) | 121.140 / 125.834 = 96,27% |
| **Kesesuaian dengan A** (kategori B termasuk himpunan kategori A) | **61,50%** |

<!-- src: diukur ulang dari data/processed/lda_doc_topic.npy dan topics.parquet; sama dengan keluaran topic_assign.jalankan() -->

Kesesuaian keseluruhan hanya 61,50%, tetapi angka itu didominasi satu topik.
Diurai per topik B:

| Topik B (LDA) | Ulasan | Sesuai dengan A | Tanpa kategori A |
|---------------|--------|-----------------|------------------|
| Transaksi, Saldo & Pemblokiran GoPay | 6.814 | 88,4% | 8,1% |
| Tarif, Ongkir & Promo | 11.206 | 88,0% | 6,9% |
| Pencarian & Penugasan Driver, … | 35.866 | 85,5% | 9,2% |
| Layanan Pelanggan & Penanganan Keluhan | 18.148 | 72,1% | 13,2% |
| **Kendala Penggunaan Aplikasi & Akses Akun** | **49.106** | **30,3%** | 22,1% |

Di luar topik 3, kesesuaiannya 82,8%: untuk empat kategori yang klasternya
tajam, kata kunci benar-benar mewakili klaster LDA. Kesesuaian yang rendah
terkonsentrasi pada klaster umum yang kata kuncinya sempit (§3.2, §11.2).
Kesesuaian sebesar apa pun **bukan bukti kebenaran kategori** — keduanya
diturunkan dari model yang sama — tetapi pola ini menunjukkan di mana
penetapan berbasis kata kunci kehilangan cakupan.

A dipakai sebagai penetapan resmi sesuai rencana: alasannya dapat dijelaskan ke
pemangku kepentingan dan dapat diaudit sampai ke kata pemicunya.

### 7.3 Satu baris per (ulasan, kategori) — bukan per kata kunci

`review_topics` merujuk baris `topics`, yaitu pasangan (kategori, keyword). Bila
satu ulasan ditautkan ke tiga baris keyword dari kategori yang sama, maka
`COUNT(*) GROUP BY kategori` menghitungnya **tiga kali** dan peringkatnya salah.

Karena itu setiap (ulasan, kategori) hanya menyimpan **satu kata kunci pemicu**
— yang berlift tertinggi di antara yang cocok. Hitungan tetap benar, dan
penetapan tetap dapat diaudit: terlihat kata mana yang memicunya.

## 8. Peringkat Topik (T-5.6) — Gambar 9

Dua lensa **terpisah**, tidak digabung menjadi skor komposit. Batasan masalah
membatasi prioritas hanya berbasis frekuensi; Likes hadir sebagai lensa
tambahan. Menggabung keduanya menyelundupkan pembobotan yang tidak diizinkan
batasan itu.

| # | Kategori | Ulasan | % negatif | Total Likes | Rata Likes | #Frek | #Total Likes |
|---|----------|--------|-----------|-------------|------------|-------|--------------|
| 1 | Pencarian & Penugasan Driver, Waktu Tunggu & Pembatalan Pesanan | 55.745 | 38,20% | 144.538 | 2,59 | 1 | 2 |
| 2 | Layanan Pelanggan & Penanganan Keluhan | 41.154 | 28,20% | **148.724** | **3,61** | 2 | **1** |
| 3 | Tarif, Ongkir & Promo | 36.061 | 24,71% | 91.095 | 2,53 | 3 | 3 |
| 4 | Transaksi, Saldo & Pemblokiran GoPay | 32.251 | 22,10% | 73.579 | **2,28** | 4 | 4 |
| 5 | Kendala Penggunaan Aplikasi & Akses Akun | 18.331 | 12,56% | 47.601 | 2,60 | 5 | 5 |

*Persentase dihitung terhadap 145.924 ulasan negatif. Kategori tidak saling
eksklusif sehingga totalnya melebihi 100%. Penetapan berbasis kata kunci
mencakup 77,25% ulasan negatif.*
<!-- src: docs/tables/topics_ranked.csv; facts.yaml topik.peringkat -->

### 8.1 Jawaban RM2

**Tema keluhan dominan adalah pencarian dan penugasan driver, waktu tunggu,
dan pembatalan pesanan (38,20% ulasan negatif), disusul layanan pelanggan dan
penanganan keluhan (28,20%).** Karena kategori tidak eksklusif, keduanya tidak
dapat dijumlahkan; gabungan keduanya (ulasan yang masuk sedikitnya salah satu)
mencakup 77.979 ulasan, atau 53,44% korpus keluhan (diukur ulang).

Ini konsisten dengan analisis n-gram yang dikerjakan sebelum LDA: `pengemudi`
muncul di 28,24% korpus topik, dan bigram `dapat pengemudi` di 6,11% dokumen.
Dua metode yang berbeda menunjuk ke tempat yang sama.

Urutan ini **tidak** sama dengan urutan ukuran klaster LDA: klaster terbesar
(Kendala Aplikasi, 40,16% dokumen dominan) justru menjadi kategori terkecil
(12,56%) setelah penetapan berbasis kata kunci, karena klasternya umum dan kata
kuncinya sempit (§3.2, §11.2). Peringkat RM2 berasal dari penetapan berbasis
kata kunci, bukan dari ukuran klaster.

### 8.2 Peringkat frekuensi ≠ peringkat resonansi

Rencana menyebut: "bila peringkatnya berbeda antara dua kolom, itu sendiri
temuan menarik." Perbedaannya ada, tetapi lebih kecil daripada pada data
sebelumnya:

- **Layanan Pelanggan & Penanganan Keluhan naik ke #1 menurut total Likes**
  (148.724, melampaui kategori driver meski frekuensinya #2) dan memiliki
  rata-rata Likes tertinggi (3,61). Keluhan tentang tanggapan CS yang tidak
  solutif adalah pengalaman yang segera dikenali banyak pengguna — kutipan
  ber-likes tertinggi di Tabel 3 (1.386) berasal dari kategori ini.
- **Transaksi, Saldo & Pemblokiran GoPay punya rata-rata Likes terendah
  (2,28).** Masalah saldo banyak dilaporkan tetapi paling sedikit diamini
  pengguna lain. Penjelasan yang masuk akal: kegagalan transaksi bersifat
  personal — pembaca lain tidak mengalaminya, sehingga tidak menekan tombol
  *like*.
- Tiga kategori lain berperingkat sama di kedua lensa.

Implikasi praktisnya: **frekuensi mengukur berapa banyak yang mengeluh,
Likes mengukur berapa banyak yang merasakan hal yang sama.** Keduanya sah, dan
justru karena dapat berbeda maka tidak boleh digabung menjadi satu angka.

## 9. Tren Bulanan (T-5.8)

`docs/tables/topic_trend_monthly.csv` — 300 baris, 60 bulan (Oktober 2021 –
September 2026), 5 kategori. Seluruh 60 bulan adalah bulan penuh, sehingga
kolom `periode_parsial` bernilai `false` di setiap baris.

Jumlah absolut setiap kategori turun dari bulan pertama ke bulan terakhir
(misalnya Kendala Aplikasi 1.225 → 87, Transaksi GoPay 1.394 → 216), tetapi
sebagian besar penurunan itu mengikuti volume ulasan negatif yang juga turun
(4.843 pada Oktober 2021, 1.577 pada September 2026). Puncak absolut terjadi
**November 2021** (Pencarian Driver 2.124), bulan dengan volume ulasan
tertinggi (24.424 ulasan).
<!-- src: facts.yaml tren; volume negatif bulanan diukur ulang dari reviews_clean.parquet -->

Yang lebih informatif adalah **pangsa** tiap kategori terhadap ulasan negatif
bulan yang sama (diukur ulang), dibandingkan 12 bulan pertama (Okt 2021 – Sep
2022) dengan 12 bulan terakhir (Okt 2025 – Sep 2026):

| Kategori | 12 bulan pertama | 12 bulan terakhir |
|----------|------------------|-------------------|
| Pencarian & Penugasan Driver, Waktu Tunggu & Pembatalan Pesanan | 30,9% | **56,5%** |
| Layanan Pelanggan & Penanganan Keluhan | 27,6% | 29,2% |
| Tarif, Ongkir & Promo | 23,9% | 23,1% |
| Transaksi, Saldo & Pemblokiran GoPay | 23,5% | 14,4% |
| Kendala Penggunaan Aplikasi & Akses Akun | 18,4% | 6,4% |

Keluhan pencarian dan penugasan driver hampir dua kali lipat pangsanya dan
kini muncul di lebih dari separuh ulasan negatif, sementara keluhan aplikasi
dan akses akun serta keluhan GoPay menyusut. Layanan pelanggan dan tarif
relatif stabil. Menghubungkan pergeseran ini dengan rilis versi aplikasi
adalah bahan analisis RM3 (`facts.yaml` `pola_sentimen_rm3`).

## 10. Tabel 3 Storytelling

`docs/tables/tabel3_storytelling_topik.csv` — kategori, jumlah, persen, total
Likes, kedua peringkat, dan **3 contoh ulasan nyata (teks asli, bukan hasil
pra-pemrosesan)** per kategori. Seluruh 15 kutipan unik.

Contoh dipilih dengan dua kriteria berurutan:

1. **Eksklusif** — hanya masuk satu kategori. Tanpa syarat ini, satu ulasan
   ber-likes tinggi yang menyinggung ongkir, pembatalan, dan layanan pelanggan
   akan muncul sebagai contoh ketiganya sekaligus, dan tidak mengilustrasikan
   satu pun dengan baik.
2. **Likes tertinggi** di antara yang eksklusif, panjang 40–300 karakter agar
   dapat dikutip utuh.

**Kelemahan yang terlihat pada data final:** syarat eksklusif cenderung
memilih ulasan yang cocok dengan satu kategori **hanya karena satu kata kunci
umum**. Ditelusuri ke kata pemicunya di `topics.parquet`, sedikitnya enam dari
15 kutipan lebih tepat mengilustrasikan kategori lain:

| Kategori | Kutipan (dipotong) | Pemicu | Isi sebenarnya |
|----------|--------------------|--------|----------------|
| Pencarian Driver | "Lagi laper mau pesen makan malah error' … server sedang sibuk" | `sen` | Gangguan aplikasi |
| Layanan Pelanggan | "perbaiki lagi sistem aplikatornya. titik lokasi terkadang mental…" | `masalah` | Lokasi/aplikasi |
| Layanan Pelanggan | "Kenapa setiap sedang searching … aplikasinya selalu suka ngebug??" | `guna` | Gangguan aplikasi |
| Tarif, Ongkir & Promo | "Setiap ada perubahan bukannya makin bagus … tujuan pengiriman…" | `kirim` | Perubahan tampilan |
| Tarif, Ongkir & Promo | "Parah makin jelek aj aplikasi ini..bnyk kecewa" | `makin` | Keluhan umum |
| Kendala Aplikasi | "Jangan daftar GoPayLater atau Anda masuk perangkap riba." | `daftar` | GoPayLater |

Kutipan Tabel 3 karenanya **perlu dipilih ulang secara manual oleh penulis**
(misalnya dari ulasan eksklusif yang memuat ≥2 kata kunci kategorinya) sebelum
dipakai di naskah. Sebagian kutipan di atas juga tercantum di `facts.yaml`
`topik.kutipan`.

## 11. Validasi Silang oleh Penilai Independen

Berkas: `docs/tables/cross_validation_sample_50_reviewed.csv` (lembar penilai)
dan `docs/tables/h9_hasil_kesepakatan.csv` (hasil per ulasan; nama berkas
berasal dari penamaan tahap lama). Penilai independen (identitas dan
kualifikasinya **[DIISI PENULIS]**) melabeli 50 ulasan negatif acak
(`random_state=42`) hanya dari teks ulasan dan lembar definisi kategori
(`cross_validation_definisi_kategori.csv`), tanpa melihat keluaran pipeline.

Yang dibandingkan adalah **hasil penetapan otomatis** pendekatan A — bukan skema
penamaan di atas kertas. Ini pilihan yang disengaja: yang perlu divalidasi
adalah kategorisasi yang benar-benar masuk `review_topics`, dashboard, dan
Tabel 3.

**Penilai memakai nama dan definisi kategori versi awal** (sebelum revisi
akibat pelatihan ulang LDA). Labelnya dipetakan satu-satu ke nama final; label
asli disimpan di kolom `kategori_penilai_1_asli`.

| Metrik | Nilai | Membandingkan |
|--------|-------|---------------|
| **Cohen's κ** | **0,543** — moderat | kategori utama penilai vs kategori otomatis berbobot tertinggi |
| Kesepakatan longgar | 78% | kategori utama penilai ada di dalam himpunan otomatis |
| Kesepakatan ketat | 62% | kecocokan persis label tunggal |
| Jaccard rerata | 0,615 | {kolom 1, kolom 2} vs seluruh himpunan otomatis |

<!-- src: facts.yaml validasi_silang; dihitung ulang dari docs/tables/h9_hasil_kesepakatan.csv -->

κ = 0,543 berada di rentang *moderate* menurut Landis & Koch (1977), **bukan
tinggi.** Angka itu dilaporkan apa adanya. Yang mengubah pelabelan dari
"subjektif" menjadi "subjektif tetapi terukur" bukan besar angkanya, melainkan
keberadaannya.

**Uji sensitivitas definisi.** Dua ulasan tentang GoPayLater yang diblokir
("Gopaylater di blokir tanpa sebab…", "…limit sudah full malah akunnya di
blokir…") dilabeli penilai "Layanan Pelanggan & Pemblokiran Akun" — label yang
benar menurut definisi versi awal, tetapi menurut definisi final keduanya
masuk "Transaksi, Saldo & Pemblokiran GoPay", sama dengan penetapan otomatis.
Bila keduanya dibaca menurut definisi final, **κ = 0,591** (kesepakatan ketat
66%); kesimpulan "moderat" tidak berubah. Angka resmi tetap 0,543; alternatifnya
adalah meminta penilai menilai ulang dengan lembar definisi final.

### 11.1 Kesepakatan per kategori

Dikelompokkan menurut label penilai:

| Kategori (label penilai) | n | Ketat | Longgar | Jaccard |
|--------------------------|---|-------|---------|---------|
| Pencarian & Penugasan Driver, … | 14 | 7 | 11 | 0,643 |
| TIDAK ADA YANG COCOK | 11 | 8 | 8 | 0,727 |
| Tarif, Ongkir & Promo | 9 | 7 | 9 | 0,731 |
| **Kendala Penggunaan Aplikasi & Akses Akun** | 8 | **3** | **5** | **0,417** |
| Layanan Pelanggan & Penanganan Keluhan | 5 | 3 | 3 | 0,500 |
| Transaksi, Saldo & Pemblokiran GoPay | 3 | 3 | 3 | 0,444 |

Sebelas ulasan tidak disepakati bahkan secara longgar. Polanya:

- **Empat ulasan tidak memperoleh kategori otomatis apa pun** padahal jelas
  bertema: "Kebanyakan animasi, jd lemot" dan "aplikasi apaan eror mulu"
  (Kendala Aplikasi), serta dua keluhan antre dan sulit mendapat driver
  (Pencarian Driver).
- **Dua ulasan GoPayLater diblokir** — perbedaan definisi, dibahas di atas.
- **Tiga ulasan dinilai penilai tidak masuk kategori mana pun**, tetapi diberi
  kategori otomatis (misalnya keluhan *spam* telepon penagih GoPayLater masuk
  GoPay; keluhan fitur penilaian makanan masuk Layanan Pelanggan).
- **"Driver rarely picks up"** — ulasan Inggris pendek yang tidak diterjemahkan;
  token `up` mencocoki kata kunci GoPay.
- Satu keluhan ganti nomor telepon akun dilabeli penilai Kendala Aplikasi,
  otomatis Layanan Pelanggan.

### 11.2 Validasi menemukan cacat nyata — dan itu memang gunanya

Kategori terlemah adalah **Kendala Penggunaan Aplikasi & Akses Akun**
(kesepakatan ketat 3 dari 8, Jaccard 0,417). Penyebabnya terdiagnosis sampai
akar, bukan diduga. Sepuluh kata kunci unigramnya — `buka, ponsel, upgrade,
ktp, daftar, login, unduh, kode, instal, otp` — seluruhnya tentang akses dan
instalasi. Kosakata **gangguan kinerja aplikasi** tidak ada sama sekali,
padahal kosakata itu terkonsentrasi kuat di klaster yang sama (diukur ulang
pada korpus topik):

| Istilah | % dokumen korpus topik | Kemunculan di topik 3 | Lift | Lolos `MIN_LIFT = 2,0`? |
|---------|------------------------|-----------------------|------|-------------------------|
| `error` | 3,06% | 76,0% | 1,89 | ❌ |
| `lemot` | 1,14% | 75,2% | 1,87 | ❌ |
| `crash` | 0,28% | 71,2% | 1,77 | ❌ |
| `login` (pembanding) | 1,81% | 95,1% | 2,37 | ✅ |

Yang menyingkirkannya adalah `MIN_LIFT = 2,0` itu sendiri. Ambang rasio
dirancang agar adil bagi topik besar, tetapi untuk topik berpangsa 40,16% ia
menuntut ≥80,3% kemunculan sebuah kata berada di topik itu — hanya kata yang
sangat spesifik (login, OTP, KTP) yang lolos.

Dampaknya di tingkat korpus (seluruh 145.924 ulasan negatif, diukur ulang):

| Istilah | Ulasan negatif yang memuatnya | Di antaranya **tanpa kategori apa pun** |
|---------|-------------------------------|-----------------------------------------|
| `error` | 4.513 | 1.538 (34,1%) |
| `lemot` | 1.962 | 822 (41,9%) |

Cacat ini juga menjelaskan dua temuan agregat yang sebelumnya tampak
terpisah: klaster terbesar (40,16%) menjadi kategori terkecil (12,56%), dan
kesesuaian A vs B hanya 30,3% pada topik itu (§7.2). Tetapi tidak satu pun
metrik agregat dapat menunjukkan **kosakata apa** yang hilang, karena semuanya
dihitung dari pipeline yang sama yang mengandung cacatnya. Penilaian manusia
independen yang menunjukkannya.

### 11.3 Mengapa cacat ini tidak diperbaiki di tahap ini

Memperbaiki kata kunci berdasarkan temuan di atas **membatalkan κ = 0,543
sebagai validasi versi yang diperbaiki** — parameternya akan disetel memakai
sampel yang sama yang dipakai mengukurnya. Perbaikan yang sah (misalnya
melonggarkan `MIN_LIFT` untuk topik besar, atau menambah kata kunci gangguan
aplikasi) menuntut sampel validasi baru dengan `random_state` berbeda, dan
akan mengubah peringkat kategori.

Keputusan yang berlaku: **laporkan apa adanya.** κ = 0,543 sah sebagai
validasi versi pipeline yang benar-benar diuji. Perbaikannya tercatat sebagai
rekomendasi dan keputusan penulis, bukan dieksekusi diam-diam.

> ### 📌 Catatan untuk `docs/limitations.md`
>
> Butir dari tahap ini yang masuk bab Keterbatasan:
>
> 1. **Kesepakatan penilai moderat (κ = 0,543; 0,591 bila dua ulasan
>    GoPayLater dibaca menurut definisi final), bukan tinggi**, dari satu
>    penilai independen yang memakai definisi kategori versi awal.
> 2. **k = 5 berada di batas bawah rentang pemindaian**, sehingga kriteria (a)
>    hipotesis tema keluhan tidak terpenuhi.
> 3. **Kategori "Kendala Penggunaan Aplikasi & Akses Akun" kehilangan kosakata
>    gangguan kinerja** (`error`, `lemot`, `crash`) akibat `MIN_LIFT = 2,0`
>    pada topik berpangsa 40,16%. Terukur: 1.538 ulasan ber-`error` dan 822
>    ulasan ber-`lemot` tidak terkategorikan. Akibatnya pangsa kategori ini
>    (12,56%) kemungkinan terlalu rendah.
> 4. **22,75% ulasan negatif tidak memperoleh kategori apa pun** (33.200 dari
>    145.924), sebagian karena terlalu pendek, sebagian karena kosakata di luar
>    daftar kata kunci (butir 3).
> 5. **Kutipan Tabel 3 perlu dipilih ulang manual** (§10).
