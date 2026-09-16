# FASE 9 — Pengemasan & Dokumentasi

**Estimasi:** 1 hari
**Prasyarat:** Fase 8 selesai (atau dipotong sesuai lingkup minimum)
**Output utama:** repo yang bisa di-*clone* dan dijalankan orang lain + naskah bebas placeholder

---

## 1. Objective

Menutup dua celah yang selalu tersisa di akhir proyek:

1. **Sistem hanya jalan di laptop Anda.** Satu perintah `docker compose up`
   harus cukup — ini penting saat presentasi, ketika tidak ada waktu untuk
   men-*debug* environment.
2. **Naskah masih berisi asumsi lama.** Bab 1 menyebut nama kolom
   `content`/`score`/`at` yang tidak ada di file aktual (Temuan 1), dan masih
   menetapkan skema 3 kelas yang sudah diputuskan diganti dengan biner
   (Temuan 3). Keduanya harus disinkronkan dengan realitas kode.

Fase ini tidak menghasilkan fitur baru. Nilainya seluruhnya pada
reprodusibilitas dan kejujuran dokumentasi.

---

## 2. Technical Tasks

### T-9.1 — `docker compose up` menjalankan seluruh sistem

```yaml
services:
  db:   { ... }                        # dari Fase 0
  api:  { depends_on: { db: { condition: service_healthy } } }   # Fase 7
  web:  { depends_on: [api] }          # Fase 8
```

Uji dari kondisi bersih — ini bagian yang sering dilewati dan selalu
menemukan masalah:

```bash
docker compose down -v          # hapus volume, database kosong total
docker compose up -d --build
# tunggu db healthy, lalu muat data:
./ml/run_pipeline.sh
# buka http://localhost:5173
```

Bila `run_pipeline.sh` butuh >15 menit, sediakan alternatif: dump SQL hasil
Fase 6 (`docs/db_dump.sql.gz`) yang bisa di-*restore* langsung, sehingga saat
demo tidak perlu menjalankan ulang seluruh pipeline ML.

### T-9.2 — README yang lengkap

Struktur wajib:

```markdown
# Analisis Sentimen & Dashboard Ulasan Gojek

## Ringkasan
Satu paragraf: apa yang dibangun, data apa, hasil apa.

## Temuan Utama
- Model terbaik: <nama>, macro-F1 <angka> (full) vs <angka> (informative_ge5w)
- Baseline mayoritas: 72,3% akurasi — seluruh model mengunggulinya pada macro-F1
- Selisih full vs informative: <angka> poin → <interpretasi>
- 5 topik keluhan teratas: <daftar dengan jumlah>

## Arsitektur
<diagram 4 lapisan dari Bagian 1.2>
Catatan: dashboard TIDAK memanggil model saat request. Seluruh prediksi
dilakukan batch di Fase 6.

## Cara Menjalankan
### Prasyarat
### Menjalankan dengan Docker (direkomendasikan)
### Menjalankan pipeline ML dari awal
### Menjalankan tanpa Docker (dev)

## Struktur Repositori
## Keputusan Metodologis Penting
1. Skema biner, bukan 3 kelas — alasan + bukti
2. Evaluasi ganda full vs informative_ge5w — alasan + hasil
3. ComplementNB bukan MultinomialNB; LinearSVC bukan SVC-RBF — alasan
4. Stopword kustom yang mempertahankan negasi — alasan
5. Ambang versi ≥100 ulasan; 21,9% versi kosong tidak diimputasi

## Keterbatasan
## Lisensi & Sumber Data
```

Bagian "Keputusan Metodologis Penting" adalah yang paling sering ditanya
penguji. Menuliskannya di README berarti Anda tidak perlu mengingatnya saat
presentasi.

### T-9.3 — Ekspor grafik resolusi tinggi

Seluruh gambar untuk naskah: minimal 300 dpi, format PNG (atau PDF vektor
untuk grafik matplotlib).

| Gambar | Sumber | Fase |
|--------|--------|------|
| 1 — Distribusi rating | notebook EDA | 1 |
| 2 — Rata-rata kata per rating | notebook EDA | 1 |
| 3 — Distribusi word_count | notebook EDA | 1 |
| 4 — Volume ulasan per bulan | notebook EDA | 1 |
| 5 — Cakupan per ambang versi | notebook EDA | 1 |
| 6 — Confusion matrix | notebook model | 4 |
| 7 — Tangkapan layar dashboard | browser | 8 |
| 8 — Coherence vs jumlah topik | notebook topik | 5 |
| 9 — Peringkat topik keluhan | notebook topik | 5 |
| 10 — Perbandingan macro-F1 full vs informative | notebook model | 3 |

Simpan semuanya di `docs/figures/final/` dengan penamaan
`gambar-<nn>-<slug>.png`.

### T-9.4 — Daftar koreksi untuk naskah eksternal ⚠️

> **Disesuaikan dengan H-4:** agent **tidak mengedit naskah utama**. Keluaran
> tugas ini adalah `docs/koreksi-naskah.md` — daftar perubahan yang harus
> dilakukan manusia pada dokumen di luar repo.

Checklist koreksi yang wajib masuk daftar:

| Item | Kondisi sekarang di naskah | Harus menjadi |
|------|---------------------------|---------------|
| **Nama kolom** (Temuan 1) | `content`, `at`, `score`, `reviewCreatedVersion`, `thumbsUpCount` | `Ulasan`, `Tanggal`, `Rating`, `Versi App`, `Likes`, `Nama User` |
| **Jumlah kelas** (Temuan 3) | 3 kelas (negatif/netral/positif) | **Biner sebagai model utama**; 3 kelas sebagai eksperimen pembanding yang kegagalannya dilaporkan |
| **Jumlah data** | "100k+" | 100.000 baris, periode 21 Mei 2024 – 31 Des 2025 |
| **Sumber data** | Sitasi Kaggle | Sesuai hasil klarifikasi provenans (Fase 1) — nyatakan apa adanya |
| **Algoritma** | Naive Bayes & SVM | ComplementNB & LinearSVC + LogisticRegression sebagai pembanding, dengan alasan teknisnya |
| **Metrik** | Akurasi | Recall negatif & macro-F1 sebagai utama; akurasi pelengkap dengan baseline 72,3% |
| **Tabel variabel** | Berdasarkan asumsi | Berdasarkan `data_contract.md` Fase 1 |

Gunakan `docs/revisi-bab1.md` (dibuat di Fase 1) sebagai daftar periksa.

### T-9.5 — Bersihkan placeholder di berkas repositori

> **Disesuaikan dengan H-4:** naskah utama ada di luar repo dan **tidak disentuh
> agent**. Pemeriksaan ini hanya berlaku untuk berkas di dalam repositori.

```bash
grep -rn "TBD\|XXX\|placeholder\|<angka>\|TODO" docs/ README.md \
  --exclude-dir=development-plan
```

Perintah ini harus **tidak mengembalikan hasil** saat DoD dipenuhi. Sumber
angkanya: `docs/tables/angka_storytelling.csv` (Fase 1) dan
`docs/tables/model_metrics.csv` (Fase 3–4).

### T-9.6 — Dokumen keterbatasan (jujur, eksplisit)

Buat `docs/limitations.md`. Yang wajib dinyatakan:

1. Label sentimen diturunkan dari rating bintang, **bukan anotasi manusia** —
   sebagian rating tidak sesuai isi ulasan (dibuktikan oleh analisis kesalahan Fase 4).
2. **39,9% ulasan hanya berisi ≤2 kata** dan hampir seluruhnya positif; ini
   membuat akurasi pada test set penuh melebih-lebihkan kemampuan sesungguhnya.
   Selisih `full` − `informative_ge5w` sebesar N poin adalah ukurannya.
3. Kelas netral (bintang 3, 3,5%) dikeluarkan dari model utama karena rasio 1:20;
   varian 3 kelas dijalankan dan gagal seperti diprediksi.
4. **21,9% ulasan tidak mencantumkan versi aplikasi**; analisis per-versi hanya
   mencakup 96,4% dari data berversi pada ambang ≥100 ulasan.
5. Pelabelan kategori topik dilakukan manual dan bersifat subjektif; validasi
   silang menghasilkan kesepakatan N%.
6. Data statis satu periode — tidak ada evaluasi terhadap *concept drift*.
7. Sistem tidak di-*deploy* ke produksi; lingkup dibatasi pada prototipe lokal.

Dokumen ini bukan pengakuan kelemahan — ini yang membedakan laporan yang bisa
dipertanggungjawabkan dari laporan yang mengklaim lebih dari yang dibuktikan.

### T-9.7 — Kebersihan repositori

```bash
git status                       # harus bersih
du -sh .git                      # wajar (<50MB); bila besar, ada data ter-commit
grep -rn "password\|secret\|api_key" --include="*.py" --include="*.js" .
```

- Pastikan `.env` **tidak** ter-commit; hanya `.env.example`.
- Hapus notebook checkpoint, `__pycache__`, `node_modules`.
- Hapus kode mati dan komentar `TODO` yang sudah tidak relevan.

### T-9.8 — Uji reprodusibilitas oleh orang lain

Minta satu orang (rekan, atau Anda sendiri di mesin/direktori berbeda)
menjalankan dari nol hanya berbekal README:

```bash
git clone <repo> && cd gojek-sentiment
# ikuti README, tanpa bertanya
```

Catat setiap langkah yang macet di `docs/repro_test.md`, perbaiki README,
ulangi. Iterasi ini biasanya menemukan 3–5 asumsi tak tertulis.

---

## 3. Deliverables / Output

| Artefak | Lokasi | Keterangan |
|---------|--------|------------|
| `docker-compose.yml` final | root | 3 service, satu perintah |
| `README.md` | root | Cara jalan, arsitektur, temuan, keputusan metodologis |
| `docs/figures/final/` | `docs/` | Gambar 1–10, 300 dpi |
| `docs/limitations.md` | `docs/` | 7 keterbatasan eksplisit |
| `docs/db_dump.sql.gz` | `docs/` | Dump DB untuk demo cepat |
| Bab 1 revisi | naskah | Sinkron dengan Temuan 1 & 3 |
| Naskah bebas placeholder | naskah | Seluruh `[A-…]` & `[T-…]` terisi |
| `docs/repro_test.md` | `docs/` | Catatan uji reprodusibilitas |
| Tag rilis | git | `v1.0` |

---

## 4. Definition of Done

- [ ] `docker compose down -v && docker compose up -d --build` dari kondisi bersih menghasilkan sistem berjalan; dashboard terbuka di browser.
- [ ] README memuat: ringkasan, temuan utama dengan **angka nyata**, diagram arsitektur, cara menjalankan (Docker + non-Docker), dan 5 keputusan metodologis.
- [ ] `grep -rn "TBD\|XXX\|placeholder\|TODO" docs/ README.md --exclude-dir=development-plan` → **nol hasil**.
- [ ] `docs/koreksi-naskah.md` lengkap: nama kolom, skema biner + alasan, provenans Kaggle, algoritma, metrik — masing-masing dengan kutipan pengganti yang siap tempel.
- [ ] Seluruh Gambar 1–10 tersedia di 300 dpi dan terbaca saat dicetak.
- [ ] `docs/limitations.md` memuat minimal 7 poin, masing-masing dengan angka pendukung.
- [ ] `git status` bersih; `.env` tidak ter-commit; tidak ada kredensial di kode.
- [ ] Ukuran `.git` wajar — tidak ada data mentah atau artefak biner ter-commit.
- [ ] **Uji reprodusibilitas oleh orang lain berhasil** hanya berbekal README (atau: setiap hambatan yang ditemukan sudah diperbaiki dan diuji ulang).
- [ ] Tag `v1.0` dibuat.

---

## 5. Risiko & Catatan

| Risiko | Dampak | Mitigasi |
|--------|--------|----------|
| Sistem hanya jalan di mesin sendiri | **Tinggi** saat presentasi | Uji dari `docker compose down -v`, bukan dari state yang sudah jalan |
| Pipeline ML terlalu lama untuk demo | Sedang | Sediakan `db_dump.sql.gz` sebagai jalur cepat |
| Naskah eksternal lupa dikoreksi | **Tinggi** — laporan memuat deskripsi dataset yang salah | `docs/koreksi-naskah.md` (T-9.4) sebagai daftar periksa manual; H-11 memverifikasi |
| Angka di naskah berbeda dengan angka di kode | **Tinggi** | Semua angka bersumber dari CSV di `docs/tables/`, tidak ditulis dari ingatan |
| Data mentah ter-commit | Sedang | `.gitignore` sejak Fase 0 + verifikasi `du -sh .git` |

### Checklist akhir sebelum menyerahkan

- [ ] Sistem jalan dari nol dengan satu perintah
- [ ] Setiap angka di naskah bisa ditelusuri ke sel notebook atau baris tabel
- [ ] Keterbatasan dinyatakan eksplisit, bukan disembunyikan
- [ ] Kegagalan eksperimen 3 kelas dilaporkan sebagai temuan
- [ ] Baseline 72,3% muncul di setiap tabel hasil model
- [ ] Selisih `full` vs `informative_ge5w` dibahas sebagai temuan metodologis utama
