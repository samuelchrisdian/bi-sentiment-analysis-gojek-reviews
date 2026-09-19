# Log Uji Manual API — Fase 7, T-7.7

**Tanggal uji:** 19 September 2026
**Build:** `api/main.py` v1.0.0, image `bi-sentiment-analysis-gojek-reviews-api`
**Basis data:** 100.000 `reviews`, 500.000 `review_scores`, 146 `topics`,
52.998 `review_topics`, 20 `model_metrics`
**Cara uji:** Swagger UI (`http://localhost:8000/docs`) untuk pemeriksaan bentuk
respons, dan skrip pengukuran 20 panggilan per endpoint untuk waktu respons.

Seluruh pengukuran di bawah dilakukan terhadap **container** `gojek_api`
(`docker compose up api`), bukan uvicorn di venv host — risiko "jalan di venv,
gagal di container" (Fase 7 §5) hanya tertutup bila yang diukur memang
containernya.

---

## 1. Waktu respons

Diukur dari klien di host, 20 panggilan per kasus, setelah satu panggilan
pemanasan. Angka mencakup HTTP + serialisasi JSON, bukan hanya waktu query.

| Method | Endpoint | Status | p50 | p95 | Ukuran respons |
|---|---|---|---|---|---|
| GET | `/api/kpi` | 200 | 9,0 ms | 55,9 ms | 824 B |
| GET | `/api/kpi?from=2025-01-01&to=2025-06-30` | 200 | 7,4 ms | 10,3 ms | 751 B |
| GET | `/api/trend` | 200 | 5,2 ms | 7,2 ms | 3,4 KB |
| GET | `/api/trend?granularity=week` | 200 | 6,9 ms | 8,7 ms | 13,1 KB |
| GET | `/api/versions` | 200 | 6,6 ms | 9,1 ms | 9,8 KB |
| GET | `/api/versions?min_reviews=500` | 200 | 5,6 ms | 9,4 ms | 8,9 KB |
| GET | `/api/topics?limit=10` | 200 | 11,9 ms | 16,2 ms | 2,0 KB |
| GET | `/api/topics?limit=10&from=…&to=…` | 200 | 32,5 ms | 45,3 ms | 2,0 KB |
| GET | `/api/topics/40/reviews?sort_by=likes&page=1` | 200 | 9,3 ms | 12,2 ms | 10,4 KB |
| GET | `/api/topics/40/reviews?sort_by=tanggal&page=200` | 200 | 11,6 ms | 14,7 ms | 5,7 KB |
| GET | `/api/topics/40/reviews?sort_by=rating&page_size=100` | 200 | 20,8 ms | 23,3 ms | 50,2 KB |
| GET | `/api/model/metrics` | 200 | 6,9 ms | 8,4 ms | 4,9 KB |
| POST | `/api/predict` (6 kata) | 200 | 4,1 ms | 6,4 ms | 361 B |
| POST | `/api/predict` (17 kata) | 200 | 3,9 ms | 6,1 ms | 542 B |
| GET | `/api/health` | 200 | 4,8 ms | 6,2 ms | 92 B |

**Seluruhnya di bawah target 200 ms.** Yang terdekat ke batas adalah
`/api/topics` berfilter tanggal (p95 45,3 ms) — satu-satunya endpoint agregat
yang tidak dapat membaca hasil pra-agregasi penuh, karena `agg_kategori`
teragregasi atas seluruh periode.

p95 `/api/kpi` sebesar 55,9 ms adalah **panggilan pertama ke proses**, bukan
perilaku tunak: pool koneksi SQLAlchemy membuat koneksi pertamanya di situ.
Panggilan berikutnya seluruhnya di kisaran 7–10 ms; lihat baris `/api/kpi`
berfilter tanggal yang dijalankan setelahnya.

### Dua optimasi yang dilakukan setelah pengukuran pertama

Pengukuran putaran pertama menemukan dua endpoint yang jauh lebih lambat
daripada sisanya. Keduanya diperbaiki, bukan dibiarkan lolos karena "masih di
bawah 200 ms":

| Endpoint | Sebelum (p50) | Sesudah (p50) | Perubahan |
|---|---|---|---|
| `/api/topics` berfilter tanggal | 94,7 ms | 32,5 ms | `review_kategori` membawa salinan `tanggal`, `rating`, `likes`, `pred_label`, sehingga query tidak lagi menjoin `reviews` × `review_scores` saat request |
| `/api/topics/{id}/reviews` | 40,2 ms | 9,3 ms | Pengurutan dipindah ke kolom `review_kategori` beserta indeksnya; `reviews` hanya disentuh 20 kali lewat primary key, bukan 9.663 kali untuk disortir |

94,7 ms bukan kegagalan DoD, tetapi memakai separuh anggaran untuk hasil yang
tidak berubah antar request adalah pemborosan yang akan menyulitkan Fase 8
begitu beberapa panel dashboard memuat serentak.

---

## 2. Status kode

### Jalur normal — ketujuh endpoint

| Endpoint | Status | Diperiksa |
|---|---|---|
| `GET /api/kpi` | 200 | `total_ulasan = 100000` untuk rentang penuh |
| `GET /api/trend` | 200 | 20 titik bulanan; `granularity=week` → 85 titik |
| `GET /api/versions` | 200 | 63 versi + metadata ambang & cakupan |
| `GET /api/topics` | 200 | 9 kategori, terperingkat menurun |
| `GET /api/topics/40/reviews` | 200 | 9.663 item, berpaginasi, teks ASLI |
| `GET /api/model/metrics` | 200 | 2 `eval_set` × 10 model, `majority_baseline` ikut |
| `POST /api/predict` | 200 | `text_preprocessed` + `text_normalized` dikembalikan |
| `GET /api/health` | 200 | tambahan di luar tujuh; untuk healthcheck container |

### Jalur error (T-7.6)

| Permintaan | Status | Respons |
|---|---|---|
| `GET /api/topics/999/reviews` | **404** | `topic_id 999 tidak ada` |
| `GET /api/kpi?from=2026-01-01&to=2026-12-31` | **404** | `Tidak ada data pada rentang …` |
| `GET /api/kpi?from=2025-06-01&to=2025-01-01` | **422** | `from (2025-06-01) melewati to (2025-01-01)` |
| `GET /api/trend?granularity=harian` | **422** | Pydantic enum — `month`/`week` saja |
| `GET /api/versions?min_reviews=50` | **422** | `greater_than_equal`, batas bawah 100 |
| `GET /api/topics/40/reviews?page_size=500` | **422** | `less_than_equal`, batas atas 100 |
| `POST /api/predict` `{"text": ""}` | **422** | `string_too_short` |
| `POST /api/predict` teks 1001 karakter | **422** | `string_too_long` |
| `POST /api/predict` `{"text": "12345 🤣"}` | **400** | Habis setelah preprocessing — tidak ada dasar memprediksi |
| `POST /api/predict` saat artefak hilang | **503** | `Model tidak tersedia: artefak tidak ditemukan: …/vectorizer.joblib` |

Uji 503 dilakukan dengan menjalankan API memakai `ARTIFACTS_DIR` yang menunjuk
direktori kosong. Perilaku yang diamati:

```
[lifespan] GAGAL memuat artefak: artefak tidak ditemukan: …/vectorizer.joblib
[lifespan] /api/predict akan mengembalikan 503; endpoint agregat tetap melayani.
```

`GET /api/kpi` tetap **200** dalam keadaan itu, dan `/api/health` melaporkan
`{"status": "degraded", "model_dimuat": false}`. Ini menyimpang dari rumusan
T-7.6 ("gagal cepat … jangan biarkan API menyala") secara **sengaja**: enam
dari tujuh endpoint sama sekali tidak memerlukan model, dan mematikan seluruh
dashboard karena satu endpoint demo rusak adalah kegagalan yang tidak
sebanding. Syarat "jangan rusak diam-diam" tetap dipenuhi — kegagalannya
terbaca di log startup, di `/api/health`, dan sebagai 503 bertuliskan
penyebabnya, bukan sebagai prediksi yang salah.

---

## 3. Pemuatan model di `lifespan`, bukan per request

Log startup container:

```
INFO:     Started server process [1]
INFO:     Waiting for application startup.
[lifespan] artefak dimuat: logistic_regression_final (0.95 s, predict_proba=ya)
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

Baris `[lifespan]` muncul **sekali**, sebelum `Application startup complete`,
dan tidak pernah muncul lagi selama 20 panggilan `/api/predict`. Bukti
kuantitatifnya ada di tabel waktu respons: pemuatan artefak memakan 0,95 detik,
sedangkan `/api/predict` merespons dalam 4 ms — dua orde besaran lebih cepat
daripada satu kali pemuatan, yang tidak mungkin terjadi bila artefak dimuat per
request.

---

## 4. Konsistensi pipeline preprocessing (risiko utama Fase 7)

`api/ml_service.py` **mengimpor** `ml.src.preprocess.praproses_satu`; tidak ada
satu pun regex, kamus slang, daftar stopword, atau pemanggilan stemmer yang
ditulis ulang di direktori `api/`.

`praproses_satu()` sendiri diverifikasi terhadap korpus: 300 ulasan diambil acak
(`seed=7`) dari `data/processed/reviews_clean.parquet`, teks aslinya dijalankan
ulang lewat fungsi itu, lalu hasilnya dibandingkan dengan `ulasan_clean` dan
`ulasan_normalized` yang tersimpan sejak Fase 2.

```
300/300 identik
```

### Lima kalimat uji `/api/predict`

Hasil di container identik dengan hasil di venv host — artefak `.joblib`
ter-*unpickle* dengan perilaku sama pada scikit-learn 1.5.1 di kedua lingkungan.

| # | Teks masukan | `text_preprocessed` | Prediksi | Confidence |
|---|---|---|---|---|
| 1 | aplikasi error terus gabisa bayar | `aplikasi error terus tidak bisa bayar` | **Negatif** | 0,9464 |
| 2 | driver nya kasar banget dan pesanan dibatalin sepihak | `pengemudi nya kasar banget pesan batal pihak` | **Negatif** | 0,9304 |
| 3 | udah top up gopay tapi saldo gak masuk parah | `bagus up gopay saldo tidak masuk parah` | **Negatif** | 0,9697 |
| 4 | pelayanan cepat driver ramah mantap banget | `layan cepat pengemudi ramah mantap banget` | **Positif** | 0,9962 |
| 5 | aplikasi gojek sangat membantu dan mudah dipakai | `aplikasi gojek sangat bantu mudah pakai` | **Positif** | 0,9986 |

Lima dari lima benar (3 negatif jelas, 2 positif jelas).

**Temuan yang harus dicatat, bukan ditutup.** Kalimat 3 memperlihatkan cacat
kamus slang Fase 2: `top` dipetakan ke `bagus` (sebagai pujian, "top!"),
sehingga frasa **"top up"** — istilah yang sangat lazim di korpus ulasan
pembayaran ini — menjadi `bagus up`. Prediksinya tetap benar karena sinyal
negatif lain di kalimat itu kuat, tetapi pemetaannya salah.

Cacat ini **tidak diperbaiki di Fase 7** dan itu keputusan yang disengaja:
`SLANG_DICT` adalah masukan pipeline Fase 2, dan mengubahnya membatalkan
`ulasan_clean`, vectorizer, keempat model tuned, seluruh isi `review_scores`,
dan setiap angka evaluasi di Fase 3–6. Mengubahnya di sini justru akan
menciptakan persis bug yang T-7.2 hendak cegah: pipeline inferensi berbeda dari
pipeline pelatihan. Yang benar adalah menambahkan `top up` ke daftar `FRASA`
(normalisasi tingkat frasa, sebelum tokenisasi) dan menjalankan ulang pipeline
dari Fase 2 — pekerjaan berskala hari, dan keputusannya milik pembimbing, bukan
milik Fase 7.

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

Permintaan dengan `Origin: http://evil.example` **tidak** menerima header
`access-control-allow-origin` sama sekali — allowlist bekerja, bukan `*`.

**Catatan kejujuran uji:** verifikasi dilakukan lewat `curl` dengan header
`Origin`, yaitu mekanisme protokol yang sama dengan yang dipakai browser, bukan
lewat halaman yang benar-benar dimuat di browser. Uji dari browser sungguhan
baru dapat dilakukan saat dev server Vue berjalan di Fase 8, dan harus diulang
di sana.

---

## 6. Ekspor Swagger

```bash
curl http://localhost:8000/openapi.json -o docs/openapi.json
```

`docs/openapi.json` — 17,6 KB, 8 path, 20 skema komponen. Seluruh endpoint
punya `response_model`, sehingga skema respons di berkas itu dihasilkan dari
kode, bukan ditulis tangan dan berisiko basi.

---

## 7. Penyimpangan dari rencana Fase 7

Empat hal di dokumen rencana tidak dapat dijalankan apa adanya. Seluruhnya
dicatat di sini apa adanya, bukan disesuaikan diam-diam.

### 7.1 `/api/versions` mengembalikan **63** versi, bukan 66

DoD menuntut 66. Angka sesungguhnya di `agg_version` dengan ambang ≥100 ulasan
adalah **63** — dan angka itu sudah begitu sejak Fase 6; DoD Fase 6 memuat
target yang sama dan juga tidak terpenuhi. 66 tampaknya perkiraan dari tahap
perencanaan, bukan hasil hitungan atas data yang sudah dimuat. Tidak ada yang
diubah untuk mengejarnya: mengubah ambang demi mencocokkan angka rencana
adalah membuat data melayani dokumen.

Metadata cakupan yang benar, dikembalikan endpoint:

| Field | Nilai |
|---|---|
| `min_reviews_threshold` | 100 |
| `versions_included` | 63 |
| `coverage_pct` | 97,11 % (dari ulasan yang punya `versi_minor`) |
| `coverage_pct_seluruh_ulasan` | 75,83 % (dari 100.000 ulasan) |
| `null_version_pct` | 21,91 % |

Rencana menyebut `coverage_pct: 96.4`. Angka itu pun tidak cocok dengan
perhitungan mana pun atas data terpasang, sehingga endpoint mengembalikan
**dua** angka cakupan dengan basis yang dinyatakan eksplisit — pembaca laporan
tidak perlu menebak penyebutnya.

### 7.2 `/api/predict` melayani `logistic_regression_final`, bukan `linear_svc_tuned`

Rencana Fase 7 ditulis sebelum gerbang H-10 (`docs/model_decision.md`,
17 September 2026) menetapkan LogisticRegression `C=1.0` sebagai model
produksi. Seluruh materialized view `agg_*` sudah memakai model itu sejak Fase
6; melayani `/predict` dengan model lain akan membuat demo tidak konsisten
dengan grafik di layar yang sama.

Efek sampingnya menguntungkan: risiko "`LinearSVC` tanpa `predict_proba`" di
tabel risiko Fase 7 **hilang sepenuhnya**. `LogisticRegression` punya
`predict_proba` bawaan, sehingga `confidence` selalu terisi dan
`model_calibrated.joblib` tidak diperlukan. `api/ml_service.py` tetap menangani
kasus estimator tanpa `predict_proba` (`confidence: null`) supaya pergantian
model kelak tidak merusak endpoint.

`ml_service.muat()` menolak start bila `MANIFEST.json` menyebut nama model yang
berbeda dari `settings.model_produksi` — ketidakcocokan itu dilaporkan sebagai
503 dengan alasannya, bukan dilayani diam-diam.

### 7.3 Endpoint topik bekerja di tingkat **kategori**, bukan baris `topics`

`topics` berisi 146 baris, yaitu pasangan (kategori, keyword) untuk 9 kategori
bisnis, dan `agg_topic` dari Fase 6 dikelompokkan per `topics.id`. Peringkat
146 kata kunci bukan yang diminta dashboard: "Peringkat topik + frekuensi +
total likes" (T-7.3 nomor 4) berarti peringkat kategori.

Karena itu Fase 7 menambahkan `ml/sql/003_api_views.sql`:

| View | Isi | Melayani |
|---|---|---|
| `review_kategori` | 52.998 baris (kategori, ulasan) + salinan `tanggal`, `rating`, `likes`, `pred_label` | `/api/topics` berfilter tanggal, `/api/topics/{id}/reviews` |
| `agg_kategori` | 9 baris peringkat kategori | `/api/topics` tanpa filter |
| `agg_weekly` | 85 baris pekanan | `/api/trend?granularity=week` |
| `agg_monthly_aktual` | 20 baris label aktual per bulan | `baseline_negatif` di `/api/kpi` |
| `agg_meta` | 1 baris konstanta cakupan | `versi_null_pct`, rentang tanggal default |

`agg_topic` dibiarkan utuh — view itu milik Fase 6 dan tetap berguna untuk
menelusuri kata kunci pemicu.

Konsekuensi yang harus diingat: **kelima view ini ikut basi bila
`review_scores`, `reviews`, atau `review_topics` berubah**, sama seperti
`agg_monthly`/`agg_version`. `REFRESH MATERIALIZED VIEW` harus mencakup
seluruhnya.

`id` kategori adalah `min(topics.id)` milik kategori itu — stabil selama isi
tabel `topics` tidak diubah, dan tidak menuntut tabel kategori baru. Bila Fase
5 dijalankan ulang dengan kategori berbeda, id ini berubah; frontend tidak
boleh menyimpannya sebagai konstanta.

### 7.4 `granularity=week` memerlukan view baru

`agg_monthly` tidak dapat dipecah menjadi pekan. `agg_weekly` dibuat dengan
nama kolom yang **identik**, sehingga pilihan granularitas hanya mengganti nama
view di `crud.py` — bukan mengganti query maupun skema respons.

Penandaan `periode_parsial` pada tingkat pekan dihitung dari data, bukan dari
`ml/config.yaml`: pekan pertama (data mulai Selasa 21 Mei 2024) dan pekan
terakhir (data berhenti Rabu 31 Desember 2025). `ml/config.yaml` hanya
menetapkan bulan parsial `2024-05`, dan nilai itu tetap dipakai apa adanya
untuk granularitas bulanan.
