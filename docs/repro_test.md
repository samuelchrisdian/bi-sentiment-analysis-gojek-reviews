# UJI REPRODUSIBILITAS

**Fase 9, T-9.8** · Dijalankan 19 September 2026

Uji dilakukan dari **klon bersih** repositori ke direktori berbeda, hanya
berbekal `README.md` — tanpa merujuk pengetahuan yang tidak tertulis di sana.
Dokumen ini mencatat apa yang dijalankan, apa yang macet, dan apa yang
diperbaiki. Hambatan dicatat apa adanya, termasuk yang memalukan.

---

## 1. Lingkup dan Batas Uji

| Aspek | Status |
|-------|--------|
| Klon bersih + `docker compose build` | ✅ Diuji penuh |
| Healthcheck ketiga service | ✅ Diuji penuh |
| Restore `docs/db_dump.sql.gz` ke PostgreSQL kosong | ✅ Diuji penuh (berkas tidak di-commit — lihat §5) |
| Endpoint API + dashboard | ✅ Diuji penuh |
| `./ml/run_pipeline.sh` dari CSV mentah | ⚠️ **Tidak diuji ulang** — lihat §4 |
| Uji oleh orang kedua | ⚠️ **Belum** — lihat §4 |

---

## 2. Langkah yang Dijalankan

```bash
git clone <repo> gojek && cd gojek     # 187 berkas terlacak
cp .env.example .env                    # ✅ nilai default cocok untuk lokal
docker compose config                   # ✅ valid
docker compose build                    # ✅ image api & web terbangun
```

Lalu, jalur demo cepat sesuai README:

```bash
gunzip -c docs/db_dump.sql.gz | docker exec -i gojek_db psql -U gojek -d gojek_sentiment
```

Hasil restore ke PostgreSQL 16 yang benar-benar kosong:

| Objek | Jumlah |
|-------|--------|
| `reviews` | 100.000 baris |
| `review_scores` | 500.000 baris (5 model × 100.000) |
| `review_topics` | 52.998 baris |
| `model_metrics` | 20 baris |
| Materialized view | 8 view, seluruhnya **populated** |

Verifikasi akhir terhadap sistem yang berjalan:

```
db:  Up (healthy)      api: Up (healthy)      web: Up (healthy)
GET /api/health  -> 200
GET /api/kpi     -> 200
GET /api/topics  -> 200
GET http://localhost:5173/ -> 200
```

---

## 3. Hambatan yang Ditemukan dan Diperbaiki

### H-1 — Container `web` selalu berstatus `unhealthy` meski situs normal

**Gejala.** `docker compose ps` menunjukkan `gojek_web` sebagai `unhealthy`
dengan `FailingStreak: 43`, padahal http://localhost:5173 melayani dashboard
dengan benar. Log healthcheck:
`wget: can't connect to remote host: Connection refused`.

**Diagnosis.** Di dalam container, `wget http://127.0.0.1/` berhasil tetapi
`wget http://localhost/` gagal. `nginx` hanya *listen* di `0.0.0.0:80` (IPv4),
sementara resolusi `localhost` pada image alpine menempuh `::1` lebih dulu.
Healthcheck karena itu **tidak pernah bisa lulus** — kegagalannya tidak ada
hubungannya dengan kesehatan aplikasi.

**Dampak bila dibiarkan.** `depends_on` berbasis kondisi sehat tidak dapat
dipakai untuk `web`, dan pada saat presentasi `docker compose ps` menampilkan
status merah yang menyesatkan.

**Perbaikan.** `web/Dockerfile` — healthcheck memakai `http://127.0.0.1/`.

**Verifikasi.** Image dibangun ulang dari klon bersih, container dijalankan
terpisah pada port 5199: status berubah `starting` → **`healthy`** dalam 40
detik, `ExitCode: 0`, dan halaman mengembalikan HTTP 200. Stack utama pun
dibangun ulang dan kini ketiga service berstatus `healthy`.

### H-2 — README belum ada sama sekali

**Gejala.** Klon bersih pertama tidak memuat `README.md`; tidak ada satu pun
petunjuk menjalankan sistem di dalam repositori.

**Perbaikan.** `README.md` ditulis lengkap (T-9.2) dan di-*commit* sebelum uji
diulang.

### H-3 — Tiga asumsi tak tertulis yang hanya muncul saat mengikuti README harfiah

Ketiganya ditemukan dengan memeriksa klon bersih, dan seluruhnya kini
dinyatakan eksplisit di README:

1. **`data/raw/ulasan_com.gojek.app.csv` tidak ikut di-*commit*.** Klon bersih
   hanya berisi `.gitkeep`. Tanpa pernyataan eksplisit, pembaca akan menjalankan
   `./ml/run_pipeline.sh` dan gagal di langkah pertama. README kini menyatakan
   ini di bagian Prasyarat lengkap dengan asal unduhannya.
2. **`ml/artifacts/` kosong pada klon bersih.** Container `api` me-*mount*
   direktori ini secara *read-only*, sehingga `/api/predict` tidak dapat
   dipakai sebelum pipeline dijalankan di host. README kini menyatakannya.
3. **Urutan wajib: `db` harus sehat sebelum data dimuat.** Menjalankan restore
   atau pipeline terlalu cepat setelah `docker compose up -d` akan gagal
   menyambung. README kini menyuruh menunggu status `healthy` lebih dulu.

---

## 4. Yang Belum Diuji — dinyatakan, bukan disembunyikan

**`./ml/run_pipeline.sh` tidak dijalankan ulang dari CSV mentah dalam uji ini.**
Yang diverifikasi adalah keluarannya — dump database hasil pipeline yang
di-*restore* ke PostgreSQL kosong dan menghasilkan seluruh tabel serta
materialized view dalam keadaan terisi. Estimasi durasi 30–45 menit yang
tercantum di README berasal dari waktu jalan sebelumnya pada Fase 2–6, bukan
dari pengukuran ulang pada uji ini. Klaim "pipeline dapat dijalankan dari nol"
karena itu bertumpu pada Fase 2–6, bukan pada dokumen ini.

**Uji oleh orang kedua belum dilakukan.** Seluruh langkah di atas dijalankan
pada mesin yang sama dengan direktori berbeda dan klon bersih. Itu menangkap
asumsi tentang *berkas* dan *state repositori* — sebagaimana terbukti pada H-3 —
tetapi **tidak** menangkap asumsi tentang *lingkungan*: Docker yang sudah
terpasang, image dasar yang sudah ter-*cache*, port yang kebetulan bebas, dan
versi Python/Node yang kebetulan cocok. Uji oleh orang kedua pada mesin lain
tetap diperlukan untuk menutup celah itu.

---

## 5. Cara Membuat Ulang `docs/db_dump.sql.gz`

Dump bukan artefak yang ditulis tangan; ia dapat dibuat ulang kapan saja dari
database yang sudah terisi:

```bash
docker exec gojek_db pg_dump -U gojek -d gojek_sentiment \
  --no-owner --no-privileges -Z9 -f /tmp/db_dump.sql.gz
docker cp gojek_db:/tmp/db_dump.sql.gz docs/db_dump.sql.gz
docker exec gojek_db rm -f /tmp/db_dump.sql.gz
```

Ukuran hasil: ≈7,7 MB. `--no-owner --no-privileges` penting agar restore
berhasil pada instalasi dengan nama peran yang berbeda.
