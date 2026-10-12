# Kinerja Query Agregat

Endpoint baca-agregat (`/api/kpi`, `/api/trend`, `/api/versions`, `/api/topics`,
`/api/model/metrics`) membaca materialized view atau `model_metrics`. Tidak ada
endpoint agregat yang menjumlahkan `reviews`/`review_scores` mentah saat request;
agregasi dikerjakan sekali saat `REFRESH MATERIALIZED VIEW` (`ml/sql/002_matviews.sql`,
`ml/sql/003_api_views.sql`).

## Cara ukur

- **Tanggal ukur:** 12 Oktober 2026.
- **Mesin basis data:** PostgreSQL 16.15 (container `gojek_db`).
- **Isi basis data:**

  | Tabel / view | Jumlah baris |
  |---|---|
  | `reviews` | 526.322 |
  | `review_scores` | 2.631.610 |
  | `topics` | 125 |
  | `review_topics` | 183.542 |
  | `review_kategori` | 183.542 |
  | `model_metrics` | 20 |

- **Kueri yang diukur:** SQL yang benar-benar dieksekusi API. Setiap fungsi `api/crud.py` dijalankan, SQL beserta parameternya ditangkap lewat *event* SQLAlchemy, lalu diulang 7 kali dengan `EXPLAIN (ANALYZE, FORMAT JSON)`.
- **Angka yang dilaporkan:** median dan maksimum *Execution Time*. Angka ini hanya waktu eksekusi di server, tanpa jaringan dan serialisasi. Waktu respons HTTP ada di `docs/api_test_log.md` §1.

## Hasil

| Endpoint | Kueri | Sumber | Baris hasil | Median | Maks |
|---|---|---|---|---|---|
| `/api/kpi` (seluruh periode) | ringkasan | `agg_monthly` ⨝ `agg_monthly_aktual` | 1 | 0,204 ms | 0,228 ms |
| | cakupan versi | `agg_version` | 1 | 0,039 ms | 0,064 ms |
| `/api/kpi` (2026) | ringkasan | `agg_monthly` ⨝ `agg_monthly_aktual` | 1 | 0,184 ms | 0,329 ms |
| `/api/trend` | bulanan | `agg_monthly` | 60 | 0,097 ms | 0,161 ms |
| `/api/trend?granularity=week` | pekanan | `agg_weekly` | 262 | 0,190 ms | 0,250 ms |
| `/api/versions` | daftar versi | `agg_version` | 198 | 0,249 ms | 0,361 ms |
| | metadata | `agg_meta` | 1 | 0,017 ms | 0,056 ms |
| `/api/topics` (seluruh periode) | peringkat | `agg_kategori` | 5 | 0,062 ms | 0,072 ms |
| | ulasan unik bertopik | `review_kategori` | 1 | 25,578 ms | 33,809 ms |
| `/api/topics` (2026) | peringkat | `review_kategori` | 5 | 17,621 ms | 20,683 ms |
| | ulasan unik bertopik | `review_kategori` | 1 | 24,051 ms | 24,918 ms |
| `/api/topics/{id}/reviews` | total | `review_kategori` | 1 | 3,110 ms | 3,977 ms |
| | halaman (20 baris) | `review_kategori` → `reviews` | 20 | 0,396 ms | 0,605 ms |
| `/api/model/metrics` | metrik | `model_metrics` | 20 | 0,161 ms | 0,205 ms |

**Seluruh kueri di bawah target 200 ms.** Kueri yang membaca pra-agregasi selesai dalam kurang dari 1 ms.

Dua jenis kueri butuh belasan sampai puluhan milidetik:

- **Ulasan unik bertopik** memakai `count(DISTINCT review_id)` atas 183.542 baris `review_kategori`. Jumlah per kategori tidak bisa langsung dijumlahkan, karena satu ulasan dapat masuk lebih dari satu kategori.
- **Peringkat kategori berfilter tanggal** tidak bisa membaca `agg_kategori`, karena view itu teragregasi atas seluruh periode.

Keduanya tetap di bawah 35 ms pada nilai maksimum. Baris uji dan skripnya ada di
`docs/api_test_log.md`.

## Catatan

- **Volume jauh lebih besar, waktu kueri tetap rendah.** Volume data kini sekitar lima kali lipat dibanding pengukuran pada data awal (100.000 ulasan). Kueri pra-agregasi tetap di bawah 1 ms, karena jumlah baris yang dibaca bergantung pada jumlah bulan, pekan, versi, dan kategori, bukan jumlah ulasan.
- **Kueri yang bertambah lambat adalah yang membaca `review_kategori`.** Penyebabnya, jumlah penetapan kategori naik dari 52.998 menjadi 183.542.
- **Satu pengecualian disengaja:** `/api/topics/{id}/reviews` menyentuh tabel `reviews`, karena drill-down harus mengambil teks ulasan satu per satu. Pengambilannya lewat *primary key*, paling banyak 100 baris per halaman.
- **View wajib di-*refresh* setiap kali `reviews`, `review_scores`, atau `review_topics` berubah.** Ini termasuk perubahan nama kategori. Pada data final, `ml/sql/003_api_views.sql` sempat belum dijalankan ulang setelah nama kategori direvisi, sehingga `agg_kategori` menampilkan dua nama lama. Masalah itu sudah diperbaiki sebelum pengukuran ini dan sebelum *dump* `docs/db_dump.sql.gz` dibuat ulang. `ml/run_pipeline.sh` menjalankan kedua berkas SQL setelah `topic_assign`.
