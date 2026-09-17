# TEMUAN EKSTRAKSI TOPIK — FASE 5 (T-5.1 s/d T-5.3)

Seluruh angka berasal dari `ml/src/topics.py` yang dijalankan, bukan estimasi.
Berkas: `docs/tables/ngram_negatif.csv`, `docs/tables/lda_coherence.csv`,
Gambar 8 dan 8b.

> **Status:** Bagian 1–4 lengkap. Penamaan kategori bisnis menunggu
> **gerbang H-8** — lihat `docs/topic_labeling_rules.md`.

## 1. Korpus Topik

| Properti | Nilai |
|----------|-------|
| Ulasan negatif (label 0) | 26.732 |
| **Korpus topik** (`word_count` ≥ 5) | **23.232** |
| Dibuang karena terlalu pendek | 3.500 (13,09%) |
| Duplikat teks di korpus topik | 20 (0,09%) |
| Rata-rata panjang | 23,86 kata |
| Kamus setelah `filter_extremes` | 2.041 token |

**Ambang `word_count >= 5` berlaku untuk seluruh grafik dan tabel topik** dan
dinyatakan di keterangan masing-masing.

Pemilihan korpus negatif terbukti menguntungkan sebagaimana diperkirakan
(Temuan 2): duplikasi teks hanya **0,09%** di sini, berbanding 32% pada korpus
positif, dan rata-rata panjangnya 23,86 kata berbanding ±4,9 kata pada ulasan
positif. LDA memperoleh materi yang layak, bukan pengulangan pujian dua kata.

## 2. Frekuensi N-gram (T-5.2)

Dikerjakan sebelum LDA, sehingga berfungsi sebagai temuan mandiri sekaligus
rujukan manusia saat menamai klaster di H-8.
`CountVectorizer(ngram_range=(1,2), min_df=10)`.

### 2.1 Unigram teratas

| # | Term | Frekuensi | % dokumen |
|---|------|-----------|-----------|
| 1 | tidak | 22.681 | 59,0% |
| 2 | pengemudi | 14.031 | 38,0% |
| 3 | aplikasi | 7.592 | 26,2% |
| 4 | gojek | 7.342 | 23,9% |
| 5 | nya | 7.190 | 22,1% |
| 6 | ada | 7.033 | 23,8% |
| 7 | bisa | 6.694 | 22,4% |
| 8 | batal | 5.356 | 17,4% |
| 9 | dapat | 4.689 | 15,7% |
| 10 | mau | 4.549 | 16,4% |

**`tidak` muncul di 59% ulasan negatif dan `pengemudi` di 38%.** Kedua angka itu
sendiri sudah merupakan temuan: keluhan pada aplikasi ini dominan berbentuk
*ketiadaan layanan* dan berpusat pada mitra driver.

**Catatan yang harus menyertai tabel ini:** `ada`, `bisa`, `dapat`, `mau`
bertahan karena **sengaja dipertahankan** di `NEGATION_KEEP` (keputusan Fase 2
gerbang H-6 putaran 2). Membuangnya menghancurkan struktur negasi — "tidak bisa"
menyusut dari 4.834 dokumen menjadi 3. Kehadirannya di peringkat atas adalah
konsekuensi yang diketahui dan diterima, bukan kebocoran stopword.

Konsekuensinya, **unigram kurang informatif untuk penamaan topik** dan bigram
harus menjadi rujukan utama.

### 2.2 Bigram teratas — jauh lebih informatif

| # | Term | Frekuensi | % dokumen |
|---|------|-----------|-----------|
| 1 | tidak bisa | 4.292 | 15,7% |
| 2 | tidak ada | 3.496 | 13,1% |
| 3 | **dapat pengemudi** | 2.415 | 8,8% |
| 4 | tidak jelas | 1.345 | 5,4% |
| 5 | **ongkos kirim** | 1.141 | 3,8% |
| 6 | pengemudi nya | 1.099 | 4,2% |
| 7 | **layan pelanggan** | 1.098 | 4,0% |
| 8 | tidak dapat | 1.078 | 4,3% |
| 9 | **pengemudi tidak** | 1.054 | 4,3% |
| 10 | **cari pengemudi** | 1.005 | 4,1% |
| 11 | **bisa batal** | 920 | 3,6% |
| 12 | tidak mau | 904 | 3,5% |
| 13 | tiba tiba | 852 | 3,4% |
| 14 | **tunggu jam** | 778 | 3,1% |
| 15 | **tunggu lama** | 712 | 2,8% |

Bigram bertanda tebal membawa isi keluhan yang dapat dipetakan ke kategori
bisnis; unigram tidak. Ini mengonfirmasi perkiraan rencana Fase 5 bahwa bigram
lebih informatif, dan menjadi alasan `ngram_range=(1,2)` dipertahankan.

Tiga kelompok terbaca langsung dari bigram saja, **sebelum** LDA dijalankan:
ketersediaan pengemudi (`dapat pengemudi`, `cari pengemudi`, `tunggu jam`,
`tunggu lama`), biaya (`ongkos kirim`), dan kanal bantuan (`layan pelanggan`).

## 3. LDA — Pemilihan Jumlah Topik (T-5.3)

Parameter dicatat lengkap karena LDA stokastik dan reprodusibilitasnya
bergantung sepenuhnya pada ketiganya:

| Parameter | Nilai |
|-----------|-------|
| `random_state` | 42 |
| `passes` | 10 |
| `iterations` | 100 |
| `alpha` | `"auto"` |
| `filter_extremes` | `no_below=10, no_above=0.5` |

### 3.1 Coherence per jumlah topik

| k | c_v | u_mass |
|---|-----|--------|
| 5 | 0,5566 | −2,2511 |
| 6 | 0,5583 | −2,2916 |
| 7 | 0,5648 | −2,5371 |
| 8 | 0,5469 | −2,4602 |
| **9** | **0,5763** | −2,4469 |
| 10 | 0,5293 | −2,5737 |
| 11 | 0,5378 | −2,6103 |
| 12 | 0,5449 | −2,6155 |

**k = 9 terpilih** — puncak c_v yang jelas (0,5763), unggul 1,15 poin dari
kandidat terdekat (k=7, 0,5648). Aturan "bila ada dua puncak berdekatan pilih
yang lebih kecil" tidak terpicu: tidak ada k lebih kecil yang berada dalam 0,005
dari puncak. Gambar 8.

Kurvanya tidak monoton dan berfluktuasi (k=8 turun, k=9 melonjak, k=10 turun
tajam). Ini lazim pada c_v dan berarti **k=9 sebaiknya tidak dibaca sebagai
"jumlah topik yang benar"**, melainkan sebagai jumlah yang memberi klaster
paling koheren dalam rentang yang diuji. Rentangnya sendiri (5–12) adalah
batasan yang ditetapkan `config.yaml`, bukan hasil pencarian tak terbatas.

### 3.2 Sembilan klaster — ukuran dan kata kunci

Kategori bisnis **belum dinamai** (gerbang H-8). Yang disajikan di sini murni
keluaran algoritma:

| Topik | % dokumen dominan | n | 10 kata teratas |
|-------|-------------------|---|-----------------|
| 2 | **28,85%** | 6.702 | pengemudi, batal, pesan, lama, tunggu, jam, makan, bisa, dapat, gofood |
| 0 | 16,46% | 3.823 | pengemudi, dapat, mau, jauh, order, banyak, susah, kalau, ambil, nya |
| 4 | 12,03% | 2.794 | makin, kirim, mahal, ongkos, promo, gojek, harga, nya, iklan, ribu |
| 7 | 10,18% | 2.364 | bayar, gopay, ada, gojek, pakai, hari, bisa, pinjam, blokir, padahal |
| 5 | 8,88% | 2.063 | aplikasi, tiba, bisa, ada, padahal, terus, mau, bagus, jelas, buka |
| 6 | 6,87% | 1.596 | pengemudi, gojek, nya, jalan, titik, sesuai, jadi, sama, alamat, gocar |
| 8 | 6,70% | 1.557 | bisa, mau, pakai, akun, gojek, aja, aplikasi, nomor, masuk, terus |
| 1 | 5,99% | 1.391 | pelanggan, layan, aplikasi, ada, gojek, kasih, sangat, buruk, nya, bintang |
| 3 | 4,05% | 942 | gopay, saldo, masuk, up, uang, potong, ada, kembali, isi, transfer |

Distribusinya timpang: topik 2 sendiri menguasai 28,85% dokumen, sementara
topik 3 hanya 4,05%. Rasio terbesar-terkecil 7,1×.

## 4. Catatan Metodologis untuk Pembaca Berkas H-8

**Contoh berprobabilitas tertinggi bias ke dokumen degenerate.** Ulasan pendek
berisi pengulangan satu kata memperoleh probabilitas topik hampir 1 karena
seluruh isinya satu topik. Contoh nyata: ulasan berisi `👎` berulang, yang
dipetakan Fase 2 menjadi `jelek jelek jelek ...` dan menempati peringkat teratas
topik 1.

Ulasan semacam itu hanya **42 dari 23.232 (0,18%)** — jadi bukan cacat korpus,
tetapi cukup untuk menyesatkan bila klaster dinilai hanya dari peringkat
teratas. Pangsanya per topik: tertinggi di topik 1 (0,65%), terendah di topik 8
(0,06%).

Karena itu `lda_clusters_for_labeling.csv` memuat **dua jenis contoh**:

- `contoh_prob_1..5` — probabilitas topik tertinggi (sesuai rencana)
- `contoh_tipikal_1..5` — **acak** dari dokumen yang topik ini dominan dan
  panjangnya 10–60 kata, yaitu yang benar-benar mewakili klaster

Gunakan kolom `contoh_tipikal_*` sebagai dasar penilaian utama.

## 5. Catatan Perkakas

Rencana menyebut *word cloud* sebagai gambar pelengkap dengan catatan eksplisit
"jangan jadikan ini bukti utama; tabel frekuensi lebih bisa
dipertanggungjawabkan". Pustaka `wordcloud` tidak termasuk dependensi yang
dikunci di Fase 0, dan tidak dipasang hanya untuk gambar pelengkap.

Gantinya Gambar 8b: batang berurut untuk 20 unigram dan 20 bigram teratas.
Panjang batang dapat dibaca sebagai angka, sedangkan ukuran huruf pada word
cloud tidak — sehingga substansi yang diminta tetap terpenuhi, bahkan lebih
dapat dipertanggungjawabkan. Bila *word cloud* tetap dikehendaki untuk laporan,
pemasangan `wordcloud` adalah perubahan satu baris di `requirements.txt` dan
merupakan keputusan pemilik proyek.
