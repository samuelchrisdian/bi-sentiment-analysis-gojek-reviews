# UJI REPRODUSIBILITAS

**Dijalankan 12 Oktober 2026** pada commit `b27558a` dengan data scraping lima tahun (526.322 ulasan).

Uji dilakukan dari **klon bersih** repositori ke direktori berbeda, hanya berbekal `README.md`. Dokumen ini mencatat apa yang dijalankan, apa yang macet, dan apa yang diperbaiki.

---

## 1. Lingkup dan Batas Uji

| Aspek | Status |
|-------|--------|
| Klon bersih + `docker compose up -d --build` | ✅ Diuji penuh |
| Healthcheck ketiga service | ✅ Diuji penuh |
| Restore `docs/db_dump.sql.gz` ke PostgreSQL baru, mengikuti perintah README | ✅ Diuji penuh (berkas tidak di-commit; disalin ke klon, lihat §5) |
| Endpoint API | ✅ Diuji penuh (`docs/api_test_log.md`) |
| Dashboard di peramban (`web/scripts/smoke.mjs`, Playwright) | ✅ 9/9 langkah lulus pada stack dengan artefak model; 8/9 pada klon bersih (§3, H-1) |
| `./ml/run_pipeline.sh` sebagai satu skrip dari data mentah | ⚠️ **Tidak diuji sebagai satu skrip** (§4) |
| Uji oleh orang kedua | ⚠️ **Belum** (§4) |

---

## 2. Langkah yang Dijalankan

```bash
git clone <repo> gojek && cd gojek      # 234 berkas terlacak
cp .env.example .env                     # ✅ nilai default cocok untuk lokal
docker compose config -q                 # ✅ valid
cp <sumber>/db_dump.sql.gz docs/         # dump tidak di-commit
docker compose up -d --build             # ✅ db, api, web
```

Restore dump mengikuti perintah README apa adanya:

```bash
docker cp docs/db_dump.sql.gz gojek_db:/tmp/data.sql.gz
docker exec gojek_db sh -c "psql -q -U gojek -d gojek_sentiment \
  -c 'DROP SCHEMA public CASCADE; CREATE SCHEMA public;' \
  && gunzip -c /tmp/data.sql.gz | psql -q -U gojek -d gojek_sentiment"
```

Restore selesai dalam **14 detik**. Isinya:

| Objek | Jumlah |
|-------|--------|
| `reviews` | 526.322 baris |
| `review_scores` | 2.631.610 baris (5 model × 526.322) |
| `review_topics` | 183.542 baris |
| `model_metrics` | 20 baris |
| Materialized view | 8 view, seluruhnya **populated** |

Verifikasi terhadap sistem yang berjalan:

```
gojek_db  Up (healthy)    gojek_api  Up (healthy)    gojek_web  Up (healthy)
GET /api/health -> 200
GET /api/kpi    -> 200   total_ulasan 526322, periode 2021-10-01 s/d 2026-09-30
GET /api/topics -> 200
GET http://localhost:5173/ -> 200
```

Waktu total dari klon sampai sistem sehat: 51 detik. Image dasar sudah ada di *cache* mesin uji, jadi angka ini tidak mewakili instalasi pertama.

Setelah restore, container `api` dinyalakan ulang sebelum pemeriksaan. README tidak memintanya. Perlu tidaknya langkah ini tidak diuji terpisah.

---

## 3. Hambatan yang Ditemukan dan Diperbaiki

### H-1 — Demo prediksi tidak jalan pada klon bersih

**Gejala:** pada klon bersih, `smoke.mjs` gagal di langkah "Demo prediksi", dan konsol peramban mencatat 503 dari `/api/predict`.

**Penyebab:** `ml/artifacts/` tidak di-commit, sehingga API menyala tanpa model. Ini sesuai rancangan: `/api/health` berstatus `degraded`, dan endpoint agregat tetap melayani. README belum menyebutnya, sehingga pengguna yang hanya me-*restore* dump akan mengira dashboard rusak.

**Perbaikan:** README kini menyatakan bahwa dump tidak memuat artefak model. Tanpa artefak, demo prediksi mengembalikan 503. Artefak bisa disalin dari pemilik proyek atau dibuat dengan pipeline. Pada stack yang memiliki artefak, langkah itu lulus dengan prediksi Negatif untuk "driver batalin pesanan sepihak lagi lagi".

### H-2 — Skrip uji dashboard memakai asumsi data lama

**Gejala:** dua langkah `smoke.mjs` gagal karena skripnya, bukan karena dashboard:

- Tombol preset "Seluruh periode penuh" sudah berganti nama menjadi "Seluruh periode".
- Uji *empty state* memakai Juni 2026 sebagai "rentang tanpa data", padahal data kini mencakup bulan itu.

Kegagalan pertama juga membuat uji layout 768px gagal, karena halaman masih dalam keadaan filter yang belum dipulihkan.

**Perbaikan:** nama tombol disesuaikan, dan rentang kosong dipindah ke Januari 2027, di luar korpus. Sesudahnya kesembilan langkah lulus, termasuk layout 768px tanpa scroll horizontal, dan konsol bersih.

### H-3 — View kategori basi setelah nama kategori direvisi (ditemukan saat uji API)

**Gejala:** `agg_kategori` dan `review_kategori` masih menampilkan dua nama kategori lama, padahal tabel `topics` sudah memakai nama final. *Dump* yang dibuat sebelum uji ini ikut membawa nama lama.

**Penyebab:** nama kategori direvisi setelah `ml/sql/003_api_views.sql` dijalankan, lalu view itu tidak di-*refresh*.

**Perbaikan:** `002_matviews.sql` dan `003_api_views.sql` dijalankan ulang, lalu `docs/db_dump.sql.gz` dibuat ulang. Dump yang diuji di §2 adalah hasil perbaikan ini. `ml/run_pipeline.sh` menjalankan kedua berkas SQL sesudah `topic_assign`, jadi masalah ini hanya muncul bila langkah dijalankan manual.

---

## 4. Yang Belum Diuji

**`./ml/run_pipeline.sh` belum dijalankan sebagai satu skrip dari data mentah.**

- **Yang sudah:** setiap modul di dalamnya sudah dijalankan pada data final dengan urutan yang sama, sebagai langkah terpisah, selama pengerjaan data scraping. Hasilnya adalah artefak, tabel, dan dump yang diuji di atas.
- **Yang belum:** skrip versi sekarang (scraping opsional, terjemahan, analisis lanjutan, `rm3`, `collect_facts`) belum dieksekusi utuh dari awal sampai akhir.
- **Kebutuhan bila dijalankan:**
  - Lingkungan `.venv-translate` (README, bagian pipeline).
  - Isian manual di `docs/tables/*_reviewed.csv`.
  - Internet bila `--scrape` dipakai.

**Uji oleh orang kedua belum dilakukan.** Uji dijalankan pada mesin yang sama dengan direktori berbeda dan klon bersih. Cara ini menangkap asumsi tentang *berkas* dan *state repositori*, seperti H-1. Cara ini **tidak** menangkap asumsi tentang *lingkungan*:

- Docker yang sudah terpasang;
- image dasar yang sudah ter-*cache*;
- port 5173, 8000, dan 5434 yang kebetulan bebas.

---

## 5. Cara Membuat Ulang `docs/db_dump.sql.gz`

Dump dapat dibuat ulang kapan saja dari basis data yang sudah terisi dan view-nya sudah di-*refresh*:

```bash
docker exec gojek_db pg_dump -U gojek -d gojek_sentiment \
  --no-owner --no-privileges -Z9 -f /tmp/db_dump.sql.gz
docker cp gojek_db:/tmp/db_dump.sql.gz docs/db_dump.sql.gz
docker exec gojek_db rm -f /tmp/db_dump.sql.gz
```

Ukuran hasil ±44 MB. Opsi `--no-owner --no-privileges` membuat restore tetap berhasil pada instalasi dengan nama peran berbeda. Dump dibuat dengan `pg_dump` 16.15. Restore pada image `postgres:16-alpine` yang lebih lama dapat gagal dengan pesan `invalid command \restrict`; perbaikannya `docker compose pull db`.
