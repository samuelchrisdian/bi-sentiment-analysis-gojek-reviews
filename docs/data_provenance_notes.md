# CATATAN PROVENANS DATASET

**Status:** ✅ Terjawab (H-1) · **Tanggal pencatatan:** 16 September 2026
**Dijawab oleh:** pemilik proyek

---

## Asal Berkas

| Properti | Nilai |
|----------|-------|
| **Kategori provenans** | (a) Unduhan langsung dari Kaggle — **tanpa modifikasi** |
| **Nama berkas** | `ulasan_com.gojek.app.csv` |
| **Lokasi di repo** | `data/raw/ulasan_com.gojek.app.csv` |
| **Ukuran** | 10.771.654 byte (10,3 MiB) |
| **Platform sumber** | Kaggle Datasets |
| **Penyunting/pengunggah** | `pandaa12` |
| **Nama dataset** | Gojek App Reviews Indonesia — Google Play Store |
| **Versi dataset** | Version 1 |
| **URL** | https://www.kaggle.com/datasets/pandaa12/gojek-app-reviews-indonesia-google-play-store/versions/1?resource=download |
| **Modifikasi oleh peneliti** | Tidak ada — berkas dipakai apa adanya |

---

## Konsekuensi Metodologis

Karena berkas ini **unduhan langsung tanpa modifikasi**, pernyataan berikut
sah ditulis di bab metodologi:

> Data diperoleh dari dataset publik Kaggle "Gojek App Reviews Indonesia —
> Google Play Store" (pengunggah: `pandaa12`, versi 1), diunduh langsung tanpa
> proses transformasi tambahan oleh peneliti. Skema kolom, penamaan, dan isi
> berkas adalah sebagaimana disediakan oleh sumber.

Yang **tidak boleh** diklaim:

- ❌ Bahwa peneliti melakukan *scraping* sendiri dengan `google-play-scraper`.
- ❌ Bahwa kolom di-*rename* oleh peneliti dari konvensi `content`/`at`/`score`.

## Penjelasan Ketidaksesuaian Nama Kolom (Temuan 1)

Rencana awal (Bab 1) mengasumsikan konvensi kolom *google-play-scraper*
(`content`, `at`, `score`, `reviewCreatedVersion`, `thumbsUpCount`), sementara
berkas aktual memakai nama berbahasa Indonesia.

Dengan provenans (a) terkonfirmasi, penjelasannya menjadi jelas: **penamaan
berbahasa Indonesia berasal dari pengunggah dataset di Kaggle, bukan dari
peneliti.** Bab 1 perlu direvisi karena mendeskripsikan konvensi kolom yang
tidak dipakai dataset ini — bukan karena ada langkah transformasi yang tidak
tercatat.

| Bab 1 (asumsi awal) | Berkas aktual | Tipe |
|---------------------|---------------|------|
| `content` | `Ulasan` | str |
| `score` | `Rating` | int64 |
| `at` | `Tanggal` | str → datetime |
| `reviewCreatedVersion` | `Versi App` | str |
| `thumbsUpCount` | `Likes` | int64 |
| — | `Nama User` | str |

## Keterbatasan yang Menyertai

Karena berkas berasal dari unggahan pihak ketiga, hal-hal berikut **tidak dapat
diverifikasi** oleh peneliti dan harus dinyatakan di bagian Keterbatasan:

1. Metode pengambilan data oleh pengunggah asli (parameter *scraping*, filter
   bahasa, rentang tanggal yang diminta) tidak terdokumentasi di halaman dataset.
2. Apakah dataset merupakan sensus atau sampel dari seluruh ulasan pada periode
   tersebut tidak diketahui.
3. Kemungkinan adanya penyaringan atau pembersihan oleh pengunggah sebelum
   diunggah tidak dapat dikesampingkan.

Ketiganya lazim untuk penelitian berbasis dataset sekunder dan tidak
membatalkan analisis — asalkan dinyatakan, bukan disembunyikan.

## Tugas Lanjutan untuk Agent

- **Fase 1:** salin isi dokumen ini ke bagian "Provenans" pada `data_contract.md`,
  lengkapi dengan hash SHA-256 berkas hasil perhitungan.
- **Fase 9:** pakai sebagai sumber bagian "Lisensi & Sumber Data" di README.
- **Fase 10:** pakai sebagai bahan §3.1 (Dataset & provenans) dan poin
  keterbatasan tentang dataset sekunder.
