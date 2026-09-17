# ATURAN PELABELAN TOPIK

**Fase 5, T-5.4** · Sumber klaster: `docs/tables/lda_clusters_for_labeling.csv`

> ## ⛔ STATUS: GERBANG H-8 TERBUKA — MENUNGGU PENAMAAN OLEH MANUSIA
>
> Bagian 2–4 dokumen ini **sengaja kosong**. Agent melakukan klastering; manusia
> menamai. Nama kategori yang ditebak agent akan mengalir ke tabel `topics`, ke
> dashboard, dan ke Tabel 3 laporan sekaligus — menjadi klaim tanpa dasar di
> tiga tempat.
>
> Gerbang berikutnya (**H-9**, validasi silang) baru dapat disiapkan setelah
> kategori final diketahui, karena penilai membutuhkan lembar definisi kategori.

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

## 2. Pemetaan Topik → Kategori — ⛔ MENUNGGU H-8

*(Diisi dari jawaban manusia. Agent yang menuliskan, bukan yang memutuskan.)*

| topic_id | pangsa | kategori (diisi manusia) | alasan (diisi manusia) |
|----------|--------|--------------------------|------------------------|
| 2 | 28,85% | | |
| 0 | 16,46% | | |
| 4 | 12,03% | | |
| 7 | 10,18% | | |
| 5 | 8,88% | | |
| 6 | 6,87% | | |
| 8 | 6,70% | | |
| 1 | 5,99% | | |
| 3 | 4,05% | | |

Enam kategori di `ml/config.yaml` — Pembayaran, Mitra Driver, Performa Aplikasi,
Tarif & Promo, Layanan Pelanggan, Akurasi Lokasi — adalah **hipotesis awal,
bukan kebenaran.** Menambah, menggabung, memecah, atau mengganti seluruhnya
adalah hak manusia, dan LDA menghasilkan 9 klaster untuk 6 hipotesis kategori,
sehingga pemetaannya memang tidak satu-ke-satu.

## 3. Empat Aturan yang Wajib Ditetapkan — ⛔ MENUNGGU H-8

*(Pertanyaannya ditulis agent; jawabannya milik manusia.)*

**3.1 Dasar pemetaan satu topik LDA ke satu kategori.**
Kata dominan, dokumen contoh, atau keduanya? Bila keduanya dan bertentangan,
mana yang menang?

> *(jawaban)*

**3.2 Bila satu topik LDA mencakup dua kategori.**
Dipecah, dipilih yang dominan, atau diberi label ganda? Ini bukan pertanyaan
hipotetis — beberapa klaster memuat kata dari lebih dari satu kategori
hipotesis.

> *(jawaban)*

**3.3 Bila ada topik yang tidak masuk kategori mana pun.**
Tambah kategori baru, atau beri label "Lainnya"? Keduanya sah asalkan
konsisten dan dinyatakan.

> *(jawaban)*

**3.4 Siapa yang melabeli dan kapan.**
Nama/peran pelabel dan tanggal, untuk dicantumkan di bab metodologi.

> *(jawaban)*

## 4. Validasi Silang (H-9) — ⛔ BELUM DISIAPKAN

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
