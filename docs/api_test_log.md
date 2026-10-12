# Log Uji API

**Tanggal uji:** 12 Oktober 2026

**Build:** `api/main.py` v1.0.0, image `bi-sentiment-analysis-gojek-reviews-api` dibangun ulang dari commit `b27558a`.

**Basis data:**

| Tabel | Jumlah baris |
|---|---|
| `reviews` | 526.322 |
| `review_scores` | 2.631.610 |
| `topics` | 125 |
| `review_topics` | 183.542 |
| `model_metrics` | 20 |

Data scraping Google Play, 1 Okt 2021 – 30 Sep 2026.

**Cara uji:** setiap kasus dipanggil 20 kali dari klien di host setelah satu panggilan pemanasan. Skripnya memakai `urllib`. Bentuk respons diperiksa langsung dari JSON.

Seluruh pengukuran dilakukan terhadap **container** `gojek_api` (`docker compose up api`), bukan uvicorn di venv host. Dengan begitu, risiko "jalan di venv, gagal di container" ikut tertutup.

---

## 1. Waktu respons

Angka mencakup HTTP dan serialisasi JSON. Waktu eksekusi kueri saja ada di `docs/db_performance.md`.

| Method | Endpoint | Status | p50 | p95 | Ukuran respons |
|---|---|---|---|---|---|
| GET | `/api/kpi` | 200 | 9,3 ms | 11,1 ms | 755 B |
| GET | `/api/kpi?from=2026-01-01&to=2026-09-30` | 200 | 8,0 ms | 9,4 ms | 752 B |
| GET | `/api/trend` | 200 | 7,5 ms | 9,3 ms | 9,5 KB |
| GET | `/api/trend?granularity=week` | 200 | 10,8 ms | 12,7 ms | 39,7 KB |
| GET | `/api/versions` | 200 | 10,2 ms | 13,6 ms | 29,4 KB |
| GET | `/api/versions?min_reviews=500` | 200 | 10,1 ms | 13,3 ms | 23,4 KB |
| GET | `/api/topics?limit=10` | 200 | 28,5 ms | 37,7 ms | 1,4 KB |
| GET | `/api/topics?limit=10&from=2026-01-01&to=2026-09-30` | 200 | 65,2 ms | 78,2 ms | 1,4 KB |
| GET | `/api/topics/51/reviews?sort_by=likes&page=1` | 200 | 13,2 ms | 20,6 ms | 10,6 KB |
| GET | `/api/topics/51/reviews?sort_by=tanggal&page=200` | 200 | 12,7 ms | 17,9 ms | 6,7 KB |
| GET | `/api/topics/51/reviews?sort_by=rating&page_size=100` | 200 | 38,6 ms | 44,4 ms | 50,8 KB |
| GET | `/api/model/metrics` | 200 | 4,2 ms | 6,9 ms | 4,9 KB |
| POST | `/api/predict` (4 kata) | 200 | 3,9 ms | 4,6 ms | 340 B |
| POST | `/api/predict` (17 kata) | 200 | 3,5 ms | 4,2 ms | 573 B |
| GET | `/api/health` | 200 | 2,5 ms | 3,7 ms | 92 B |

**Seluruh endpoint di bawah target 200 ms.** Yang paling dekat ke batas adalah `/api/topics` berfilter tanggal, dengan p95 78,2 ms.

- **Penyebab:** endpoint ini tidak bisa memakai pra-agregasi `agg_kategori`. Ia harus menghitung peringkat dan ulasan unik dari 183.542 baris `review_kategori`.
- **Perbandingan dengan data awal (100.000 ulasan):** p50 naik dari 32,5 ms menjadi 65,2 ms, sebanding dengan kenaikan jumlah penetapan kategori (52.998 → 183.542).
- **Endpoint lain** tetap di kisaran satuan sampai belasan milidetik, karena membaca view yang ukurannya bergantung pada jumlah bulan, pekan, dan versi, bukan jumlah ulasan.

Dua optimasi dari tahap pengembangan API masih berlaku:

- `review_kategori` membawa salinan `tanggal`, `rating`, `likes`, dan `pred_label`, sehingga `/api/topics` berfilter tanggal tidak menjoin `reviews` × `review_scores`.
- `/api/topics/{id}/reviews` mengurutkan di `review_kategori` dan hanya menyentuh `reviews` lewat *primary key* untuk baris di halaman yang diminta.

---

## 2. Status kode

### Jalur normal

| Endpoint | Status | Diperiksa |
|---|---|---|
| `GET /api/kpi` | 200 | `total_ulasan = 526322` untuk rentang penuh |
| `GET /api/trend` | 200 | 60 titik bulanan; `granularity=week` → 262 titik |
| `GET /api/versions` | 200 | 198 versi + metadata ambang & cakupan (§7.1) |
| `GET /api/topics` | 200 | 5 kategori final, terperingkat menurun; 112.724 ulasan unik bertopik |
| `GET /api/topics/51/reviews` | 200 | 55.745 item (2.788 halaman), berpaginasi, teks ASLI |
| `GET /api/model/metrics` | 200 | 2 `eval_set`; baseline mayoritas 0,711 ikut dikembalikan |
| `POST /api/predict` | 200 | `text_preprocessed` + `text_normalized` dikembalikan |
| `GET /api/health` | 200 | `{"status":"ok","database":"ok","model_dimuat":true}` |

### Jalur error

| Permintaan | Status | Respons |
|---|---|---|
| `GET /api/topics/999/reviews` | **404** | `topic_id 999 tidak ada` |
| `GET /api/kpi?from=2027-01-01&to=2027-12-31` | **404** | `Tidak ada data pada rentang 2027-01-01 s/d 2027-12-31` |
| `GET /api/kpi?from=2025-06-01&to=2025-01-01` | **422** | `from (2025-06-01) melewati to (2025-01-01)` |
| `GET /api/trend?granularity=harian` | **422** | enum — `month`/`week` saja |
| `GET /api/versions?min_reviews=50` | **422** | `greater_than_equal`, batas bawah 100 |
| `GET /api/topics/51/reviews?page_size=500` | **422** | `less_than_equal`, batas atas 100 |
| `POST /api/predict` `{"text": ""}` | **422** | `string_too_short` |
| `POST /api/predict` teks 1001 karakter | **422** | `string_too_long` |
| `POST /api/predict` `{"text": "12345 🤣"}` | **400** | Tidak ada token tersisa setelah pra-pemrosesan |
| `POST /api/predict` saat artefak hilang | **503** | `Model tidak tersedia: artefak tidak ditemukan: /tmp/kosong/vectorizer.joblib` |

Uji 503 dijalankan pada container kedua dari image yang sama, dengan `ARTIFACTS_DIR=/tmp/kosong`. Log startup-nya:

```
[lifespan] GAGAL memuat artefak: artefak tidak ditemukan: /tmp/kosong/vectorizer.joblib
[lifespan] /api/predict akan mengembalikan 503; endpoint agregat tetap melayani.
```

Dalam keadaan itu `GET /api/kpi` tetap **200**, dan `/api/health` melaporkan `{"status":"degraded","database":"ok","model_dimuat":false}`.

Kegagalan model sengaja tidak mematikan API:

- Enam dari tujuh endpoint tidak memerlukan model.
- Kegagalannya tetap terbaca di tiga tempat: log startup, `/api/health`, dan 503 yang menyebut penyebabnya.

---

## 3. Pemuatan model di `lifespan`, bukan per request

```
INFO:     Waiting for application startup.
[lifespan] artefak dimuat: logistic_regression_final (1.059 s, predict_proba=ya)
INFO:     Application startup complete.
```

Baris `[lifespan]` muncul **sekali**, sebelum `Application startup complete`, dan tidak muncul lagi selama 40 panggilan `/api/predict`. Pemuatan artefak butuh 1,06 detik, sedangkan `/api/predict` merespons dalam ±4 ms. Itu mustahil bila artefak dimuat per request.

---

## 4. Konsistensi pipeline pra-pemrosesan

`api/ml_service.py` **mengimpor** `ml.src.preprocess.praproses_satu`. Tidak ada regex, kamus slang, daftar stopword, atau pemanggilan stemmer yang ditulis ulang di `api/`.

Fungsi itu diuji ulang terhadap korpus final dengan prosedur berikut:

1. Ambil 300 ulasan acak (`random_state=7`) dari `data/processed/reviews_clean.parquet`.
2. Jalankan ulang teks aslinya lewat `praproses_satu()`.
3. Bandingkan hasilnya dengan `ulasan_normalized` dan `ulasan_clean` yang tersimpan.

```
konsistensi praproses_satu: 300/300 identik
```

Uji ini juga mencakup seluruh perbaikan dari empat putaran verifikasi pra-pemrosesan: aturan frasa, pengecualian peringkasan huruf ganda, pengecualian stemming, dan kamus slang 639 entri.

### Lima kalimat uji `/api/predict`

| # | Teks masukan | `text_preprocessed` | Prediksi | Confidence |
|---|---|---|---|---|
| 1 | aplikasi error terus gabisa bayar | `aplikasi error terus tidak bisa bayar` | **Negatif** | 0,9590 |
| 2 | driver nya kasar banget dan pesanan dibatalin sepihak | `pengemudi nya kasar banget pesan batal pihak` | **Negatif** | 0,9554 |
| 3 | udah top up gopay tapi saldo gak masuk parah | `top up gopay saldo tidak masuk parah` | **Negatif** | 0,9659 |
| 4 | pelayanan cepat driver ramah mantap banget | `layan cepat pengemudi ramah mantap banget` | **Positif** | 0,9989 |
| 5 | aplikasi gojek sangat membantu dan mudah dipakai | `aplikasi gojek sangat bantu mudah pakai` | **Positif** | 0,9987 |

Kelima kalimat diprediksi benar.

Kalimat 3 menunjukkan satu perbaikan pada data final. Frasa **"top up"** sebelumnya berubah menjadi `bagus up`, karena `top` dipetakan per token sebagai pujian. Kini frasa itu tetap `top up` berkat aturan frasa dari verifikasi pra-pemrosesan putaran pertama (`docs/preprocessing_validation.md`).

---

## 5. CORS

```
$ curl -i -X OPTIONS http://localhost:8000/api/kpi \
       -H "Origin: http://localhost:5173" \
       -H "Access-Control-Request-Method: GET"

HTTP/1.1 200 OK
access-control-allow-methods: GET, POST
access-control-max-age: 600
access-control-allow-origin: http://localhost:5173
```

Preflight dengan `Origin: http://evil.example` dijawab **400** tanpa header `access-control-allow-origin`. Jadi yang berlaku adalah allowlist, bukan `*`.

Allowlist juga memuat `127.0.0.1` dan `0.0.0.0` pada port 5173/4173 (`api/config.py`), karena peramban memperlakukan ketiga alamat itu sebagai origin berbeda.

Verifikasi ini memakai `curl` dengan header `Origin`, bukan halaman yang dimuat di peramban. Pemeriksaan lewat peramban dicakup uji dashboard (`docs/repro_test.md`).

---

## 6. Ekspor Swagger

```bash
curl http://localhost:8000/openapi.json -o docs/openapi.json
```

`docs/openapi.json` berukuran 17,6 KB, dengan 8 path dan 20 skema komponen. Seluruh endpoint punya `response_model`, sehingga skema respons dihasilkan dari kode, bukan ditulis tangan. Satu-satunya perubahan dari ekspor sebelumnya adalah teks keterangan (baseline set informatif 0,44).

---

## 7. Catatan perilaku

### 7.1 Cakupan versi dikembalikan dengan basis yang eksplisit

| Field `/api/versions` | Nilai |
|---|---|
| `min_reviews_threshold` | 100 |
| `versions_included` | 198 |
| `coverage_pct` | 99,36 % (dari ulasan yang punya `versi_minor`) |
| `coverage_pct_seluruh_ulasan` | 77,96 % (dari 526.322 ulasan) |
| `null_version_pct` | 21,54 % |

Dua angka cakupan dikembalikan sekaligus, masing-masing dengan penyebutnya, supaya pembaca laporan tidak perlu menebak basisnya.

### 7.2 `/api/predict` melayani `logistic_regression_final`

Model ini sama dengan yang dipakai semua materialized view `agg_*` (`docs/model_decision.md`), sehingga demo prediksi konsisten dengan grafik di layar yang sama. `LogisticRegression` punya `predict_proba` bawaan, jadi `confidence` selalu terisi tanpa lapisan kalibrasi.

`ml_service.muat()` menolak start bila `MANIFEST.json` menyebut nama model yang berbeda dari `settings.model_produksi`. Ketidakcocokan itu dilaporkan sebagai 503 beserta alasannya.

### 7.3 Endpoint topik bekerja di tingkat kategori

`topics` berisi 125 pasangan (kategori, kata kunci) untuk 5 kategori final. Endpoint topik memeringkat **kategori**, lewat view berikut di `ml/sql/003_api_views.sql`:

| View | Isi | Melayani |
|---|---|---|
| `review_kategori` | 183.542 baris (kategori, ulasan) + salinan `tanggal`, `rating`, `likes`, `pred_label` | `/api/topics` berfilter tanggal, `/api/topics/{id}/reviews` |
| `agg_kategori` | 5 baris peringkat kategori | `/api/topics` tanpa filter |
| `agg_weekly` | 262 baris pekanan | `/api/trend?granularity=week` |
| `agg_monthly_aktual` | 60 baris label aktual per bulan | `baseline_negatif` di `/api/kpi` |
| `agg_meta` | 1 baris konstanta cakupan | `versi_null_pct`, rentang tanggal default |

`id` kategori adalah `min(topics.id)` milik kategori itu: 1, 26, 51, 76, 101 pada data final. Id ini berubah bila penetapan kategori dijalankan ulang dengan isi `topics` berbeda, jadi frontend tidak boleh menyimpannya sebagai konstanta.

**Kelima view ini wajib di-*refresh*** setiap kali `reviews`, `review_scores`, atau `review_topics` berubah, termasuk saat nama kategori direvisi. Pada data final, `agg_kategori` sempat menampilkan dua nama kategori lama karena `003_api_views.sql` belum dijalankan ulang setelah revisi nama. Masalah itu diperbaiki sebelum uji ini, dan `docs/db_dump.sql.gz` dibuat ulang sesudahnya.

### 7.4 Periode parsial pekanan dihitung dari data

`agg_weekly` menandai pekan pertama sebagai parsial (data mulai Jumat 1 Oktober 2021), begitu pula pekan terakhir (data berhenti Rabu 30 September 2026). Tingkat bulanan tidak punya bulan parsial, karena rentang scraping dipilih tepat 60 bulan penuh (`ml/config.yaml`, `temporal.partial_months: []`).
