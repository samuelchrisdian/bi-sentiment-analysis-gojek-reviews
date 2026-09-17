# ATURAN PELABELAN TOPIK

**Fase 5, T-5.4** · Sumber klaster: `docs/tables/lda_clusters_for_labeling.csv`

> ## ⚠️ STATUS: H-8 TERISI — TETAPI **BELUM DIADOPSI MANUSIA**
>
> Pemetaan 9 topik → 9 kategori sudah lengkap dan dipakai di seluruh keluaran
> Fase 5. Namun pelabelnya **bukan manusia** (lihat Bagian 5), sehingga syarat
> metodologis gerbang H-8 — "manusia menamai" — **belum terpenuhi.**
>
> **Gerbang H-9 ditahan** sampai seorang reviewer manusia mengadopsi atau
> merevisi pemetaan ini dan namanya dicatat sebagai pelabel final.

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

**3.4 Pelabel dan tanggal.** — lihat Bagian 5.

> **Catatan penting tentang label ganda.** Aturan 3.2 melarang label ganda pada
> level **topik LDA**, dan itu dipatuhi: setiap topik memetakan ke tepat satu
> kategori. Ini berbeda dari penetapan pada level **ulasan**, tempat satu
> ulasan memang boleh memperoleh lebih dari satu kategori (rata-rata 2,26) —
> hal yang secara eksplisit diizinkan T-5.5 dan dinyatakan di keterangan tabel.

## 4. Validasi Silang (H-9) — ⛔ DITAHAN

**Alasan penahanan bukan teknis melainkan metodologis:** pemetaan pada Bagian 2
belum diadopsi manusia (Bagian 5). Menyerahkan sampel validasi silang sekarang
akan menghasilkan angka kesepakatan terhadap skema yang pelabelnya sendiri belum
sah menurut protokol H-8.

Setelah Bagian 2 dan 3 terisi, agent menyiapkan
`docs/tables/cross_validation_sample_50.csv`: 50 ulasan negatif acak
(`random_state=42`), **berisi teks ulasan asli saja** — tanpa label, tanpa
kategori hasil H-8, tanpa skor topik — disertai lembar definisi kategori
terpisah.

Berkas itu diserahkan ke rekan penilai untuk dilabeli secara independen. Setelah
kembali, agent menghitung persentase kesepakatan dan Cohen's κ, lalu
melaporkannya apa adanya termasuk bila rendah.

Angka kesepakatan akan diisikan di sini.

| Metrik | Nilai |
|--------|-------|
| Jumlah sampel | 50 |
| Kesepakatan (%) | *(menunggu H-9)* |
| Cohen's κ | *(menunggu H-9)* |
| Penilai | *(menunggu H-9)* |
| Tanggal | *(menunggu H-9)* |

---

## 5. Provenans Pelabelan — ⚠️ HARUS DINYATAKAN DI BAB METODOLOGI

| Properti | Nilai |
|----------|-------|
| **Pelabel ronde ini** | **ChatGPT (GPT-5.6 Sol)**, bertindak sebagai reviewer H-8 |
| Tanggal | 17 September 2026 |
| Diminta oleh | Pemilik proyek |
| **Status adopsi manusia** | **BELUM** |
| Pelabel final | *(menunggu adopsi manusia)* |

Gerbang H-8 ada justru untuk mencegah nama kategori berasal dari model bahasa.
Alasannya dinyatakan di rencana Fase 5: label kategori mengalir ke tabel
`topics`, ke dashboard, dan ke Tabel 3 laporan sekaligus — sehingga label yang
tidak dipertanggungjawabkan manusia menjadi klaim tanpa dasar di tiga tempat.

Pada ronde ini gerbang tersebut diisi oleh model bahasa lain, bukan manusia.
Kualitas pemetaannya baik dan alasannya terdokumentasi per klaster, sehingga
**dipakai sebagai masukan kerja** untuk T-5.5–T-5.8. Tetapi klaim metodologis
"kategori dinamai manusia" **belum dapat ditulis** di laporan.

### 5.1 Dua jalur penyelesaian

**(A) Adopsi manusia — mempertahankan klaim rencana.** Seorang reviewer manusia
membaca `lda_clusters_for_labeling_reviewed.csv`, menyetujui atau merevisi
kesembilan nama, lalu namanya dicatat sebagai pelabel final di tabel Bagian 5.
Bab metodologi kemudian menyatakan: *pelabelan kategori dilakukan oleh
[nama], dengan bantuan model bahasa sebagai penyusun usulan awal.* Ini
pengungkapan yang lazim dan memadai.

**(B) Ubah klaim metodologis.** Bila tidak ada reviewer manusia, bab metodologi
harus menyatakan apa adanya bahwa pelabelan kategori dilakukan model bahasa,
dan **H-9 berubah peran**: dari sekadar validasi silang menjadi **satu-satunya
lapisan validasi manusia** atas skema kategori. Konsekuensinya H-9 menjadi lebih
penting, bukan kurang, dan angka kesepakatannya menjadi bukti utama bahwa skema
itu dapat direproduksi manusia.

Keduanya sah secara akademik asalkan dinyatakan. Yang tidak sah adalah menulis
"manusia menamai" tanpa manusia yang menamai.
