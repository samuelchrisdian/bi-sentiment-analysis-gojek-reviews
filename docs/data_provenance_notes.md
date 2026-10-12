# CATATAN PROVENANS DATASET

**Status:** ✅ Final · **Tanggal pencatatan:** 11 Oktober 2026
**Sumber data:** scraping Google Play oleh peneliti (bukan dataset pihak ketiga)

Seluruh nilai di dokumen ini berasal dari berkas metadata yang ditulis skrip
pengambilan dan terjemahan, dari `ml/artifacts/MANIFEST.json`, dari
`docs/synthesis/facts.yaml`, atau dihitung *read-only* dari berkas mentah.

---

## Asal Berkas

| Properti | Nilai |
|----------|-------|
| **Kategori provenans** | Data primer: diambil sendiri oleh peneliti dari Google Play Store |
| **Nama berkas** | `gojek_reviews_5Y.csv` |
| **Lokasi di repo** | `data/raw/gojek_reviews_5Y.csv` (tidak masuk git; lihat `.gitignore`) |
| **Ukuran** | 182.360.998 byte (173,9 MiB) |
| **SHA-256** | `51e87f6b44a25c3da0d4529cf7a006b445525a16fe4a7e52569d83049910937f` |
| **Skrip pengambilan** | `data/script-scraping/scrape_5_tahun.py` |
| **Pustaka** | `google-play-scraper` 1.2.7, fungsi `reviews()` |
| **Aplikasi** | `com.gojek.app` |
| **Parameter** | `country="id"`, `sort=Sort.NEWEST`, `count=200` per permintaan, berlanjut dengan *continuation token*; dua putaran `lang="id"` dan `lang="en"` |
| **Rentang tanggal** | 1 Oktober 2021 – 30 September 2026 (60 bulan penuh, tanpa bulan parsial) |
| **Tanggal pengambilan** | 11 Oktober 2026, 02.19–03.01 UTC |
| **Jumlah baris** | 526.329 (tanpa `reviewId` ganda) |
| **Kolom** | 12: sebelas kolom keluaran *scraper* ditambah `lang_query` (penanda putaran) |
| **Modifikasi oleh peneliti** | Tidak ada pada berkas mentah. Penggabungan kedua putaran, pemotongan rentang tanggal, dan penambahan `lang_query` dilakukan skrip pengambilan sebelum berkas ditulis; seluruh transformasi lain terjadi di pipeline. |
| **Metadata** | `data/raw/gojek_reviews_5Y.meta.json` (gabungan), `data/raw/bagian/gojek_reviews_5Y_{id,en}.meta.json` (per putaran) |

<!-- src: data/raw/gojek_reviews_5Y.meta.json; data/raw/bagian/*.meta.json; ml/artifacts/MANIFEST.json data.sha256; facts.yaml dataset.sha256 -->

### Cara pengambilan

Skrip meminta ulasan urutan terbaru halaman demi halaman (200 ulasan per
permintaan) dan berhenti ketika ulasan tertua pada satu halaman sudah lebih tua
dari 1 Oktober 2021. Hasilnya dideduplikasi menurut `reviewId`, dipotong ke
rentang 1 Oktober 2021 00.00 – 30 September 2026 23.59, lalu disimpan apa adanya.
Kegagalan jaringan diulang sampai enam kali dengan jeda yang terus berlipat, dan
progres disimpan berkala ke berkas *checkpoint* agar pengambilan yang terputus
dapat dilanjutkan.

Kedua putaran berhenti karena telah melewati batas awal rentang, bukan karena
layanan berhenti mengembalikan ulasan: ulasan tertua dalam rentang bertanggal
1 Oktober 2021 pada kedua putaran.

### Rincian per putaran

| Putaran | Halaman | Ulasan unik terambil | Dalam rentang | Waktu pengambilan (UTC) | Ulasan tertua / terbaru dalam rentang |
|---------|---------|----------------------|---------------|--------------------------|----------------------------------------|
| `lang="id"` | 2.318 | 463.600 | 462.528 | 02.19.35 – 02.48.57 | 2021-10-01 00.03.12 / 2026-09-30 23.41.10 |
| `lang="en"` | 320 | 64.000 | 63.801 | 02.58.10 – 03.01.21 | 2021-10-01 00.18.34 / 2026-09-30 23.36.02 |
| **Gabungan** | — | — | **526.329** | — | `reviewId` ganda antarputaran: **0** |

<!-- src: data/raw/gojek_reviews_5Y.meta.json per_lang, reviewId_ganda_antar_lang, ulasan_gabungan -->

### Mengapa dua putaran `lang` — temuan empiris

Parameter `lang` pada Google Play **tidak** menyaring ulasan menurut bahasa
teksnya. Data penelitian ini menunjukkan:

1. Kedua putaran **tidak beririsan sama sekali** (0 `reviewId` ganda), padahal
   negara dan rentang tanggalnya sama.
2. Putaran `lang="en"` **sebagian besar tidak berbahasa Inggris**: hanya
   12.834 dari 63.801 ulasan (20,1%) yang terdeteksi dominan berbahasa Inggris
   oleh aturan kata fungsi (`ml/src/language_filter.py`). Sebaliknya, putaran
   `lang="id"` tetap memuat 1.837 ulasan (0,4%) yang dominan berbahasa Inggris.
3. Putaran `lang="en"` **jauh lebih negatif**: 41,0% berating 1–2, dibanding
   25,9% pada putaran `lang="id"`.

Pola ini konsisten dengan pengelompokan ulasan menurut bahasa yang terkait
dengan **penulisnya** (misalnya bahasa perangkat atau akun), bukan bahasa
teksnya. Mekanisme internal Google Play tidak terdokumentasi secara resmi,
sehingga pernyataan ini adalah **temuan empiris penelitian**, bukan spesifikasi
layanan. Konsekuensi praktisnya terukur: mengambil putaran `lang="id"` saja akan
kehilangan 63.801 ulasan (12,1% korpus) yang lebih negatif, sehingga korpus
tampak lebih positif dari kenyataan.

<!-- src: perhitungan read-only atas data/raw/gojek_reviews_5Y.csv (kolom lang_query, score, content) dengan ml/src/language_filter.tandai_inggris dan ml/config.yaml language_filter -->

### Berkas per putaran

Berkas per putaran disimpan terpisah sebelum digabung, sehingga penggabungan
dapat diperiksa ulang.

| Berkas | Baris | SHA-256 |
|--------|-------|---------|
| `data/raw/bagian/gojek_reviews_5Y_id.csv` | 462.528 | `ee2e35df98331493e74913287e4bbc684c4d3fc4288c5f64d19c3a381a5361e0` |
| `data/raw/bagian/gojek_reviews_5Y_en.csv` | 63.801 | `c3f4e20595e4c230cd4e6f763d5376cca8b319fc9b9e8720e8980507f181ce6c` |
| `data/raw/gojek_reviews_5Y.csv` (gabungan) | 526.329 | `51e87f6b44a25c3da0d4529cf7a006b445525a16fe4a7e52569d83049910937f` |

Hanya *hash* berkas gabungan yang diperiksa pipeline (`ml/src/ingest.py`
`sha256_of_raw`, dicatat di `MANIFEST.json`). *Hash* berkas per putaran
dihitung pada 11 Oktober 2026 untuk catatan ini.

---

## Terjemahan Ulasan Berbahasa Inggris

Ulasan yang dominan berbahasa Inggris tidak dibuang, melainkan diterjemahkan ke
bahasa Indonesia; teks aslinya tetap disimpan.

| Properti | Nilai |
|----------|-------|
| **Deteksi** | Aturan kata fungsi `ml/src/language_filter.py`: ≥3 token, ≥2 kata fungsi Inggris, dan kata fungsi Inggris > 2 × kata fungsi Indonesia |
| **Ulasan ditandai** | 14.671 (2,8% dari 526.329): 5.472 berating 1, 1.273 berating 2, 1.019 berating 3, 1.085 berating 4, 5.822 berating 5 |
| **Model** | MarianMT `Helsinki-NLP/opus-mt-en-id` |
| **Revisi model (terkunci)** | `6e4c52d61a6b16fe3509b0267cbfec65011b860b` |
| **Dekode** | *Beam search* 4 berkas, tanpa *sampling*; panjang maksimum 256 token |
| **Satuan terjemahan** | Per kalimat (31.174 kalimat), karena model cenderung menghilangkan kalimat kedua dan seterusnya bila satu masukan memuat beberapa kalimat |
| **Lingkungan** | `transformers` 5.19.0, `torch` 2.14.1+cpu, luring di CPU, lingkungan Python terpisah `.venv-translate` |
| **Skrip** | `ml/src/translate.py` (dijalankan dengan `.venv-translate/bin/python -m ml.src.translate`) |
| **Keluaran** | `data/interim/terjemahan_inggris.csv` (`reviewId`, `content_asli`, `content_terjemahan`, `n_kalimat`); tidak masuk git |
| **SHA-256 keluaran** | `81b128028c88d0b5d5fc79dcb12783fb9aec4c84758ae8451e038240ea4fb735` (dihitung 11 Oktober 2026) |
| **Metadata** | `data/interim/terjemahan_inggris.meta.json` |
| **Penerapan** | `ml/src/ingest.py` mengganti teks ulasan yang ditandai dengan terjemahannya (`ml/config.yaml` `language_filter.mode: translate`) |
| **Audit manual** | 50 ulasan acak: deteksi benar 47 (94%), terjemahan layak 43 (86%) — `docs/tables/audit_terjemahan_sampel_50_reviewed.csv` |

<!-- src: data/interim/terjemahan_inggris.meta.json; ml/config.yaml translation, language_filter; facts.yaml dataset.penanganan_bahasa -->

Pustaka terjemahan dipasang di lingkungan terpisah karena PyTorch dan
`transformers` menuntut NumPy versi 2, sedangkan gensim pada pipeline utama
menuntut NumPy di bawah versi 2.

---

## Dari Berkas Mentah ke Korpus Analisis

| Langkah | Baris | Sumber |
|---------|-------|--------|
| Berkas mentah (dua putaran) | 526.329 | `MANIFEST.json` `data.n_rows_raw` |
| Tanpa 7 ulasan berteks kosong (5 dari `lang="id"`, 2 dari `lang="en"`) | 526.322 | `MANIFEST.json` `data.n_rows_after_language_filter` |
| — di antaranya diterjemahkan dari bahasa Inggris | 14.671 | `facts.yaml` `dataset.penanganan_bahasa` |
| Berlabel biner (rating 3 dikeluarkan) | 504.208 | `MANIFEST.json` `data.n_rows_used` |

Nama `n_rows_after_language_filter` di `MANIFEST.json` adalah nama kunci lama;
dengan mode `translate` tidak ada ulasan yang dibuang karena bahasanya, dan
selisih tujuh baris itu seluruhnya ulasan tanpa teks.

---

## Pemetaan Nama Kolom

Berkas mentah memakai nama kolom asli keluaran `google-play-scraper`. Pipeline
memetakan enam kolom ke nama analisis berbahasa Indonesia saat berkas dibaca
(`ml/config.yaml` `schema.source_columns`, diterapkan `ml/src/ingest.py`);
berkas mentahnya tidak diubah. Nama analisis dipertahankan agar seluruh modul
hilir, basis data, dan API memakai skema yang sama.

| Kolom *scraper* | Nama analisis | Tipe |
|-----------------|---------------|------|
| `content` | `Ulasan` | str |
| `score` | `Rating` | int64 |
| `at` | `Tanggal` | str → datetime |
| `reviewCreatedVersion` | `Versi App` | str |
| `thumbsUpCount` | `Likes` | int64 |
| `userName` | `Nama User` | str |

Kolom lain (`reviewId`, `userImage`, `replyContent`, `repliedAt`, `appVersion`,
`lang_query`) tidak dipakai analisis; `reviewId` dipakai untuk deduplikasi saat
pengambilan dan untuk menautkan terjemahan.

---

## Konsekuensi Metodologis

Pernyataan berikut sah ditulis di bab metodologi:

> Data diambil langsung oleh peneliti dari Google Play Store dengan pustaka
> `google-play-scraper` 1.2.7 untuk aplikasi `com.gojek.app` (negara Indonesia,
> urutan terbaru) pada 11 Oktober 2026, mencakup ulasan 1 Oktober 2021 –
> 30 September 2026. Pengambilan dilakukan dua putaran (`lang="id"` dan
> `lang="en"`) yang digabung tanpa transformasi lain menjadi 526.329 ulasan.
> Sebanyak 14.671 ulasan yang dominan berbahasa Inggris diterjemahkan ke bahasa
> Indonesia dengan model MarianMT `Helsinki-NLP/opus-mt-en-id` pada revisi yang
> dikunci; teks aslinya tetap disimpan.

Yang **tidak boleh** diklaim:

- ❌ Bahwa korpus adalah **sensus** seluruh ulasan Gojek pada periode itu.
  Google Play tidak menjamin seluruh ulasan dapat diambil; yang terambil adalah
  ulasan yang masih ditampilkan layanan pada 11 Oktober 2026.
- ❌ Bahwa parameter `lang` Google Play **secara resmi** mengelompokkan ulasan
  menurut bahasa penulis. Itu temuan empiris penelitian ini.
- ❌ Bahwa menjalankan ulang skrip pengambilan akan menghasilkan berkas yang
  identik. Isi Google Play berubah dari waktu ke waktu; yang dapat direproduksi
  adalah analisis atas berkas dengan SHA-256 di atas, bukan pengambilannya.
- ❌ Bahwa seluruh teks yang dianalisis adalah tulisan asli pengguna. Sebanyak
  14.671 ulasan (2,8%) dianalisis dalam bentuk terjemahan mesin.
- ❌ Bahwa data mewakili seluruh pengguna Gojek. Data hanya memuat pengguna
  Android yang menulis ulasan di Google Play.

## Keterbatasan yang Menyertai

Keterbatasan yang bersumber dari cara data diperoleh dirinci di
`docs/limitations.md`, terutama:

1. Perilaku parameter `lang` Google Play tidak terdokumentasi; dua putaran
   dipakai berdasarkan temuan empiris, dan tidak dapat dipastikan bahwa tidak
   ada kelompok ulasan lain yang hanya muncul pada nilai `lang` lain.
2. Hanya ulasan yang masih tersedia saat pengambilan yang terambil; ulasan yang
   telah dihapus tidak tercakup.
3. Hanya Google Play (tanpa App Store), periode lima tahun.
4. Sebagian korpus berupa terjemahan mesin dengan kelayakan terukur 86% pada
   sampel audit.

---

## Riwayat Sumber Data

Data penelitian ini menggantikan dua versi sebelumnya. Keduanya **tidak
dipakai** dalam hasil akhir dan disimpan hanya sebagai arsip lokal (`archive/`
tidak masuk git).

1. **Dataset Kaggle (versi awal, diganti).** Pipeline semula memakai dataset
   publik Kaggle "Gojek App Reviews Indonesia — Google Play Store" (pengunggah
   `pandaa12`, versi 1; berkas `ulasan_com.gojek.app.csv`, 100.000 ulasan,
   21 Mei 2024 – 31 Desember 2025, SHA-256
   `9b7f8e50737f9f17bce4ab8a44f7d2f8587deea86c6ad175e2579932cc22b524`). Dataset
   ini diganti karena **arahan dosen pembimbing yang tidak memperkenankan data
   dari Kaggle**. Hasil, tabel, artefak, dan dokumen versi Kaggle diarsipkan di
   `archive/kaggle-v1/`, termasuk catatan provenans lamanya
   (`archive/kaggle-v1/data_provenance_notes.md`). Berkas CSV Kaggle masih ada
   di `data/raw/` tetapi tidak dibaca pipeline (`ml/config.yaml`
   `paths.raw_csv`).
2. **Percobaan scraping satu tahun (tidak dipakai).** Percobaan pendahuluan
   mengambil 50.646 ulasan untuk 6 Oktober 2025 – 5 Oktober 2026
   (`gojek_reviews_1Y.csv`) dan membuang ulasan berbahasa Inggris (49.089 ulasan
   dianalisis). Bulan pertama dan terakhirnya tidak penuh. Percobaan ini
   menunjukkan bahwa ulasan berbahasa Inggris yang dibiarkan apa adanya
   membentuk satu topik LDA tersendiri berisi kata fungsi Inggris, yang mendasari
   keputusan menerjemahkan alih-alih membiarkan atau membuangnya. Arsipnya di
   `archive/scraping-1y-v1/`.

Arsip `archive/scraping-5y-r1/` sampai `archive/scraping-5y-r4/` memuat hasil
antara keempat putaran verifikasi pra-pemrosesan atas data lima tahun ini,
bukan sumber data yang berbeda.

<!-- src: archive/kaggle-v1/data_provenance_notes.md; archive/kaggle-v1/data_contract.md; archive/scraping-1y-v1/config.yaml; docs/synthesis/bab-3-pembaruan-data-scraping.md A.1, B.12 -->

## Rujukan

- `docs/data_contract.md` — kontrak data yang mengikat tahap berikutnya.
- `docs/limitations.md` — keterbatasan penelitian.
- `docs/synthesis/bab-3-pembaruan-data-scraping.md` — teks Bab III tentang
  pengambilan dan validasi data.
