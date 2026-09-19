# ATURAN PELABELAN TOPIK

**Fase 5, T-5.4** · Sumber klaster: `docs/tables/lda_clusters_for_labeling.csv`

> ## ✅ GERBANG H-8 DILEWATI — 17 September 2026
>
> Pemetaan 9 topik → 9 kategori lengkap dan dipakai di seluruh keluaran Fase 5.
> Pelabel: **Samuel Chrisdian** (pemilik proyek). Usulan awal per klaster
> disusun dengan bantuan model bahasa, lalu dinilai dan diadopsi pelabel —
> termasuk keputusan memecah kategori hipotesis (Bagian 2.1).

---

## 1. Yang Sudah Dikerjakan Agent

| Langkah | Hasil |
|---------|-------|
| Korpus topik | 23.232 ulasan negatif (`word_count` ≥ 5), dari 26.732 |
| Frekuensi n-gram | `docs/tables/ngram_negatif.csv` — top-30 unigram + top-30 bigram |
| LDA | k = 5…12, `random_state=42`, `passes=10`, `alpha="auto"` |
| Pemilihan k | **k = 9** (puncak c_v 0,5763) — `docs/tables/lda_coherence.csv`, Gambar 8 |
| Berkas pelabelan | `docs/tables/lda_clusters_for_labeling.csv` — 9 baris |

Kolom berkas pelabelan: `topic_id`, `n_dokumen_dominan`,
`pangsa_dokumen_dominan`, `top_terms` (20 kata), `top_terms_bobot`,
`contoh_prob_1..5` (+`prob_*`), `contoh_tipikal_1..5` (+`prob_tipikal_*`),
lalu **`kategori_usulan` dan `alasan` yang kosong.**

Bacalah `contoh_tipikal_*` lebih dulu: contoh berprobabilitas tertinggi bias ke
ulasan pendek berulang (lihat `docs/topic_extraction_findings.md` §4).

## 2. Pemetaan Topik → Kategori (hasil H-8)

Sumber: `docs/tables/lda_clusters_for_labeling_reviewed.csv` — kolom
`kategori_usulan` dan `alasan` terisi untuk kesembilan baris.

| topic_id | pangsa | Kategori | Dasar penamaan (ringkas) |
|---|---|---|---|
| 2 | 28,85% | **Pesanan GoFood & Pembatalan** | pesanan makanan lama, sulit dapat driver, menunggu ±1 jam, pembatalan terlambat/tidak tersedia |
| 0 | 16,46% | **Ketersediaan & Respons Mitra Driver** | sulit mendapat driver, driver menolak/mengabaikan order, lokasi jauh, tidak bergerak |
| 4 | 12,03% | **Tarif, Ongkir & Promo** | ongkir/harga mahal, perbandingan biaya, diskon & voucher tidak memadai |
| 7 | 10,18% | **GoPayLater, GoPinjam & Penagihan** | pemblokiran meski bayar tepat waktu, penolakan pengajuan, denda, penagihan |
| 5 | 8,88% | **Performa & Gangguan Aplikasi** | lemot/loading, error koneksi, aplikasi tidak bisa dibuka, masalah setelah pembaruan |
| 6 | 6,87% | **Akurasi Lokasi & Rute** | titik/alamat tidak sesuai, perbedaan dengan Google Maps, salah tujuan |
| 8 | 6,70% | **Akun, Login & Verifikasi** | OTP, login, verifikasi wajah, email/nomor ponsel, ganti data akun |
| 1 | 5,99% | **Layanan Pelanggan & Penanganan Keluhan** | customer service & chat bantuan lambat/tanpa respons, masalah tidak selesai |
| 3 | 4,05% | **Transaksi & Saldo GoPay** | saldo hilang/terpotong, top up tidak masuk, transfer gagal |

### 2.1 Penyimpangan dari enam kategori hipotesis

Hipotesis awal `config.yaml` memuat enam kategori; hasilnya sembilan. Tiga
perubahan substantif:

| Hipotesis awal | Menjadi | Alasan |
|----------------|---------|--------|
| **Pembayaran** (satu kategori) | **Transaksi & Saldo GoPay** + **GoPayLater, GoPinjam & Penagihan** | Dua tema berbeda secara substantif: kegagalan transaksi dompet digital versus kredit, denda, dan perilaku penagihan. LDA memisahkannya sebagai topik 3 dan 7 tanpa diarahkan. |
| **Mitra Driver** (satu kategori) | **Ketersediaan & Respons Mitra Driver** + **Akurasi Lokasi & Rute** + sebagian **Pesanan GoFood & Pembatalan** | Isu driver tidak dijadikan satu keranjang: ketersediaan/respons berbeda dari akurasi titik jemput, dan berbeda lagi dari operasional pemenuhan pesanan GoFood. |
| **Performa Aplikasi** | **Performa & Gangguan Aplikasi** + **Akun, Login & Verifikasi** | Gangguan teknis umum terpisah dari friksi autentikasi, yang membentuk klaster sendiri (topik 8). |

Kategori **Lainnya** tidak digunakan: kesembilan klaster dinilai memiliki tema
substantif yang stabil.

## 3. Empat Aturan Pelabelan (hasil H-8)

**3.1 Dasar pemetaan satu topik LDA ke satu kategori.**

Keduanya dipakai, dengan urutan prioritas tegas:

1. `contoh_tipikal_1..5` sebagai bukti utama;
2. `top_terms` + bobot sebagai penguat konsistensi;
3. contoh berprobabilitas tertinggi hanya sebagai pemeriksaan tambahan, karena
   bias terhadap ulasan pendek/berulang.

Bila contoh tipikal dan kata dominan bertentangan, **contoh tipikal menang**
apabila **≥3 dari 5** menunjukkan tema yang sama secara jelas. Kata dominan
tidak boleh sendirian menentukan nama kategori.

**3.2 Bila satu topik memuat dua kategori.**

**Tidak menggunakan label ganda.** Dipilih tema dominan berdasarkan mayoritas
contoh tipikal, dan tema sekundernya dicatat di kolom `alasan`. Bila tidak ada
tema yang benar-benar dominan, digunakan kategori baru yang lebih luas —
tidak memaksakan ke kategori hipotesis lama demi mempertahankan enam kategori.

> Diterapkan pada topik 6: contoh sekunder memuat perilaku driver, tetapi tema
> dominannya akurasi titik/alamat. Dicatat di `alasan`, bukan dijadikan label ganda.

**3.3 Bila tidak masuk kategori yang sudah ada.**

**Tambah kategori baru** bila contoh tipikal dan top terms menunjukkan pola
koheren. `Lainnya` hanya untuk klaster residual yang benar-benar heterogen.
Pada 9 klaster ini, `Lainnya` dinilai tidak diperlukan.

**3.4 Pelabel dan tanggal.**

Pelabel: **Samuel Chrisdian** (pemilik proyek), 17 September 2026. Usulan awal
per klaster disusun dengan bantuan model bahasa; penilaian, revisi, dan adopsi
akhir — termasuk pemecahan kategori hipotesis di Bagian 2.1 — dilakukan
pelabel.

> **Catatan penting tentang label ganda.** Aturan 3.2 melarang label ganda pada
> level **topik LDA**, dan itu dipatuhi: setiap topik memetakan ke tepat satu
> kategori. Ini berbeda dari penetapan pada level **ulasan**, tempat satu
> ulasan memang boleh memperoleh lebih dari satu kategori (rata-rata 2,26) —
> hal yang secara eksplisit diizinkan T-5.5 dan dinyatakan di keterangan tabel.

## 4. Validasi Silang (H-9)

Berkas: `docs/tables/cross_validation_sample_50.csv` — 50 ulasan negatif acak
(`random_state=42`), **berisi teks ulasan asli saja**: tanpa label, tanpa
kategori, tanpa skor topik. Lembar definisi kategori disediakan terpisah di
`docs/tables/cross_validation_definisi_kategori.csv`.

**Rancangan pembandingnya:** label manusia dibandingkan dengan **hasil
penetapan otomatis** pendekatan A (berbasis kata kunci) pada 50 ulasan yang
sama. Ini yang benar-benar perlu divalidasi — apakah kategorisasi otomatis yang
masuk ke `review_topics`, dashboard, dan Tabel 3 sesuai penilaian manusia.
Membandingkannya dengan skema H-8 saja hanya menguji konsistensi penamaan,
bukan kualitas penetapannya.

### 4.1 Cara mengisi berkas penilai

| Kolom | Wajib? | Isi |
|-------|--------|-----|
| `kategori_penilai_1` | **Ya — 50 baris** | Kategori **utama**, yaitu tema paling dominan pada ulasan itu |
| `kategori_penilai_2` | Tidak | Hanya bila ada tema kedua yang jelas; dikosongkan bila tidak ada |
| `catatan` | Tidak | Bebas |

Bila satu ulasan memuat dua tema, **yang dominan masuk kolom 1** — Cohen's κ
dihitung dari kolom itu. Gunakan `TIDAK ADA YANG COCOK` bila ulasan tidak masuk
kategori mana pun (mis. "bosok", "Mampersulit...").

### 4.2 Tiga angka yang dilaporkan

Tidak satu pun memadai sendirian, karena penetapan otomatis boleh memberi lebih
dari satu kategori per ulasan (rata-rata 2,26):

| Ukuran | Membandingkan | Kegunaan |
|--------|---------------|----------|
| **Cohen's κ** | kolom 1 vs kategori otomatis berbobot tertinggi | **Angka utama.** Mengoreksi kesepakatan yang terjadi karena kebetulan — penting karena dua kategori teratas saja menguasai dua pertiga korpus |
| **Kesepakatan longgar** | kolom 1 ada di dalam himpunan kategori otomatis | Tidak menghukum penetapan multi-kategori secara tidak adil |
| **Jaccard rerata** | {kolom 1, kolom 2} vs seluruh himpunan otomatis | Satu-satunya yang memakai kolom 2, dan satu-satunya yang menilai penetapan multi-kategori sebagaimana ia dipakai sistem |

Baris yang mengosongkan kolom 2 diperlakukan sebagai himpunan beranggota satu,
bukan sebagai data hilang.

Ketiganya dilaporkan apa adanya, termasuk bila rendah.

### 4.3 Hasil

| Metrik | Nilai |
|--------|-------|
| Jumlah sampel | 50 |
| **Cohen's κ** | **0,4621** — *moderate* (Landis & Koch, 1977) |
| Kesepakatan longgar | 84,0% |
| Kesepakatan ketat | 52,0% |
| Jaccard rerata | 0,4967 |
| Baris berkategori ganda dari penilai | 17 |
| Baris `TIDAK ADA YANG COCOK` | 4 |
| **Penilai** | **Samuel Chrisdian** (pemilik proyek) |
| Tanggal | 19 September 2026 |

Berkas rinci per baris: `docs/tables/h9_hasil_kesepakatan.csv`.

**κ 0,46 berada di rentang *moderate*, bukan tinggi, dan itu dilaporkan apa
adanya.** Angka ini yang mengubah pelabelan dari "subjektif" menjadi "subjektif
tetapi terukur" — dan nilai sesungguhnya bukan pada angkanya, melainkan pada
apa yang ditemukannya (§4.4).

### 4.4 Ketidaksepakatan terkonsentrasi pada satu kategori

| Kategori (label penilai) | n | Sepakat | % | Jaccard |
|---|---|---|---|---|
| Tarif, Ongkir & Promo | 7 | 7 | **100%** | 0,557 |
| Akun, Login & Verifikasi | 4 | 4 | **100%** | 0,562 |
| GoPayLater, GoPinjam & Penagihan | 4 | 4 | **100%** | 0,354 |
| Ketersediaan & Respons Mitra Driver | 12 | 11 | 91,7% | 0,572 |
| Pesanan GoFood & Pembatalan | 8 | 7 | 87,5% | 0,500 |
| Layanan Pelanggan & Penanganan Keluhan | 5 | 4 | 80,0% | 0,483 |
| TIDAK ADA YANG COCOK | 4 | 3 | 75,0% | 0,750 |
| Performa & Gangguan Aplikasi | 3 | 2 | 66,7% | 0,328 |
| **Akurasi Lokasi & Rute** | **3** | **0** | **0%** | **0,000** |

Kegagalannya tidak merata. Delapan dari sembilan kategori berada di 67–100%;
**Akurasi Lokasi & Rute gagal total (0 dari 3).**

**Penyebabnya terdiagnosis, bukan diduga.** Kata kunci kategori itu adalah
`titik, jalan, alamat, sesuai, motor, tuju, rumah, barang, nyaman, bawa` —
tidak memuat satu pun istilah yang paling jelas menandakannya:

| Istilah | Frekuensi korpus negatif | Jadi kata kunci? |
|---------|--------------------------|------------------|
| `lokasi` | 497 | ❌ |
| `peta` | 265 | ❌ |
| `map` | 254 | ❌ |
| `gps` | 51 | ❌ |

Ketiga ulasan yang tidak disepakati persis bertipe ini: *"Maps tidak akurat"*,
*"Maps ngawur parah."*, *"Gajelas gocek masa maps ga terdetek"* — seluruhnya
**tidak memperoleh kategori apa pun** dari penetapan otomatis.

Ketiga istilah itu **lolos seluruh saringan kualitas** (`MAX_DF_KORPUS`,
`MIN_LIFT`); yang menyingkirkannya adalah batas `N_KATA_KUNCI = 10` semata.
Pada peringkat *relevance* topik 6: `map` #13, `lokasi` #15, `peta` #19 — tepat
di luar sepuluh besar. Angka 10 itu ditetapkan sembarang (DoD hanya menuntut
≥5), dan validasi silang inilah yang menunjukkan bahwa ia terlalu ketat.

Dampak di tingkat korpus lebih kecil daripada yang tampak pada sampel: dari 771
ulasan negatif yang menyebut `peta`/`lokasi`/`gps`, **59 (7,7%)** sama sekali
tidak memperoleh kategori. Sampel 50 kebetulan menarik tiga ulasan pendek yang
hanya berisi kata itu.

### 4.5 Catatan metodologis — mengapa perbaikan menuntut sampel baru

Memperbaiki kata kunci berdasarkan temuan di atas **membatalkan κ = 0,4621
sebagai validasi versi yang diperbaiki**: parameter disetel memakai sampel yang
sama yang dipakai mengukurnya. Setiap perbaikan karena itu menuntut sampel
validasi baru (`random_state` berbeda) bila angkanya ingin tetap bermakna.

Angka 0,4621 sah sebagai validasi **versi pipeline yang benar-benar diuji**, dan
dilaporkan sebagai itu.
