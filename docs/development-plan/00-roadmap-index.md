# ROADMAP INDEX — Sistem Analisis Sentimen Ulasan Gojek

Dokumen ini adalah peta navigasi. Spesifikasi teknis lengkap ada di
`tech-architecture-development-plan.md`. Setiap fase dipecah ke file terpisah
agar dapat dieksekusi satu per satu tanpa membaca seluruh dokumen induk.

> **Status persiapan: ✅ Bagian A selesai (16 September 2026).** Keempat blocker
> sudah terjawab — lihat `00-human-prep-checklist.md`. Fase 0 boleh dijalankan.
>
> **Yang mengikat agent selama eksekusi:** lima **gerbang berhenti** (H-5 … H-9).
> Di titik itu agent menyerahkan berkas dan **berhenti menunggu manusia**.
> Lihat tabel di bawah dan protokol lengkapnya di `00-human-prep-checklist.md`.

## Konteks Singkat (wajib dibaca sebelum fase mana pun)

- **Root repositori:** `bi-sentiment-analysis-gojek-reviews/` — sudah
  diinisialisasi (`.git` ada, belum ada commit). Jangan `git init` ulang.
- **Dataset:** `data/raw/ulasan_com.gojek.app.csv` — 100.000 baris, 6 kolom
  (`Nama User`, `Ulasan`, `Rating`, `Tanggal`, `Likes`, `Versi App`),
  periode 21 Mei 2024 – 31 Des 2025. Nama file memakai **titik**, bukan garis bawah.
- **Model yang dibandingkan:** ComplementNB, MultinomialNB, LinearSVC,
  LogisticRegression — semuanya di atas TF-IDF identik (unigram+bigram,
  `min_df=3`, `max_features≈30000`).
- **Skema label utama:** BINER (neg = rating 1–2, pos = rating 4–5,
  rating 3 dikeluarkan) — **dikonfirmasi H-3**. Varian 3 kelas tetap dijalankan
  sebagai eksperimen pembanding.
- **Provenans data:** unduhan langsung Kaggle (`pandaa12`, versi 1), tanpa
  modifikasi — **dikonfirmasi H-1**, rincian di `docs/data_provenance_notes.md`.
- **Environment:** Python 3.12.3, Node 24.19.0, Docker Compose v5.5.0 —
  **dikonfirmasi H-2**; seluruh pin dependensi tetap berlaku.
- **Naskah:** dikelola **di luar repositori** — **dikonfirmasi H-4**. Agent
  tidak pernah mengedit naskah; Fase 10 menghasilkan `.md` bahan tempel.
- **Metrik utama:** recall kelas negatif → macro-F1 → F1 negatif.
  *Accuracy* hanya pelengkap, selalu disandingkan dengan baseline mayoritas **72,3%**.
- **Evaluasi ganda wajib:** set `full` dan set `informative_ge5w` (`word_count >= 5`).
- **Arsitektur:** batch pre-scoring (Python) → PostgreSQL → FastAPI → Vue 3.
  Dashboard TIDAK memanggil model saat request.

## Daftar Berkas

### Persiapan

| File | Isi |
|------|-----|
| `00-human-prep-checklist.md` | Pekerjaan manusia di luar agent: 4 blocker (✅ selesai), protokol gerbang berhenti, 7 tugas manusia di dalam fase, 4 keputusan lingkup. **Sisa ≈14 jam kerja manusia.** |
| `../data_provenance_notes.md` | Jawaban H-1: asal dataset, URL Kaggle, konsekuensi metodologis, keterbatasan dataset sekunder. |

### Fase Pengembangan

| # | File | Estimasi | Jalur Kritis |
|---|------|----------|--------------|
| 0 | `phase-0-foundation-reproducibility.md` | 0,5 hari | |
| 1 | `phase-1-eda-data-contract.md` | 1 hari | |
| 2 | `phase-2-preprocessing-labeling.md` | 2 hari | ⚠️ Risiko kualitas tertinggi |
| 3 | `phase-3-baseline-model-comparison.md` | 2 hari | ⚠️ Inti RM1 |
| 4 | `phase-4-tuning-honest-evaluation.md` | 1,5 hari | ⚠️ Inti RM1 |
| 5 | `phase-5-topic-extraction.md` | 2 hari | ⚠️ Inti RM2 |
| 6 | `phase-6-scoring-database-load.md` | 1 hari | |
| 7 | `phase-7-backend-api.md` | 2 hari | |
| 8 | `phase-8-frontend-dashboard.md` | 3 hari | |
| 9 | `phase-9-packaging-documentation.md` | 1 hari | |
| 10 | `phase-10-research-synthesis.md` | 2 hari | ⚠️ Satu-satunya keluaran yang dibaca orang lain |
| | **Total** | **≈18 hari kerja** | |

## Graf Dependensi

```
F0 ──► F1 ──► F2 ──┬──► F3 ──► F4 ──┐
                   │                 ├──► F6 ──► F7 ──► F8 ──► F9 ──► F10
                   └──► F5 ──────────┘
```

- F3 dan F5 sama-sama bergantung pada F2, tetapi **tidak saling bergantung** —
  bisa dikerjakan paralel bila ada dua orang.
- F6 baru bisa jalan setelah artefak model final (F4) **dan** tabel topik (F5) siap.
- F10 menuntut seluruh angka final dan bebas placeholder (hasil F9).

## ⛔ Gerbang Berhenti (mengikat agent)

| Gerbang | Fase | Agent menyerahkan | Menunggu |
|---------|------|-------------------|----------|
| **H-5** | 2 | `unknown_tokens_500.csv` | kolom `bentuk_baku` terisi manusia |
| **H-6** | 2 | `preprocessing_sample_100.csv` | lampu hijau verifikasi manual |
| **H-7** | 4 | `error_analysis_50.csv` | kolom `kategori_penyebab` terisi manusia |
| **H-8** | 5 | klaster LDA + kata + contoh ulasan | nama kategori bisnis dari manusia |
| **H-9** | 5 | 50 ulasan **tanpa label** | label independen dari rekan penilai |

Di setiap gerbang, agent mengakhiri giliran dengan menyebut: path berkas, apa
yang harus diisi, estimasi waktu, dan pernyataan bahwa pekerjaan dihentikan.
Menebak isian, memakai nilai sementara, atau melewati gerbang karena hasilnya
"terlihat wajar" adalah pelanggaran — angka yang dihasilkannya tidak bisa
dipertanggungjawabkan di laporan.

H-10 (keputusan model produksi) dan H-11 (pemeriksaan naskah) tidak
menghentikan pipeline, tetapi wajib diingatkan secara eksplisit.

## Aturan Eksekusi (berlaku untuk semua fase)

1. Seluruh parameter dibaca dari `ml/config.yaml`. Tidak ada angka *hardcode* di script.
2. `random_state=42` di setiap tempat yang stokastik.
3. Kerjakan satu fase saja per sesi; jangan lanjut sebelum Definition of Done terpenuhi.
4. Setiap metrik harus berasal dari kode yang benar-benar dijalankan. Jangan mengarang angka.
5. Commit di akhir setiap fase dengan tag `phase-<N>-done`.
6. **Agent tidak menulis sitasi atau daftar pustaka.** Lihat batasan di Fase 10.
7. **Agent berhenti di setiap gerbang H-5…H-9** dan tidak melanjutkan sebelum
   manusia membalas.
8. **Agent tidak mengedit naskah utama** — naskah ada di luar repo (H-4).

## Aturan Pemotongan Lingkup

Bila waktu menipis: **potong Fase 8** (sederhanakan dashboard jadi 3 grafik inti).
**Jangan potong Fase 4, Fase 5, atau Fase 10** — Fase 4 dan 5 adalah inti
akademik yang menjawab rumusan masalah, dan Fase 10 adalah satu-satunya fase
yang menghasilkan bahan untuk dokumen akhir.

## Prompt Eksekusi per Fase

Berikan satu fase per sesi, jangan sekaligus:

```
Konteks: proyek analisis sentimen ulasan Gojek.
Root repo: bi-sentiment-analysis-gojek-reviews (sudah ter-init).
Dataset: data/raw/ulasan_com.gojek.app.csv — 100.000 baris, kolom:
Nama User, Ulasan, Rating, Tanggal, Likes, Versi App.
Arsitektur & keputusan desain: lihat tech-architecture-development-plan.md
Spesifikasi fase: docs/development-plan/phase-<N>-*.md
Keputusan manusia & gerbang berhenti: docs/development-plan/00-human-prep-checklist.md

Kerjakan FASE <N> saja. Patuhi:
- Seluruh parameter dibaca dari ml/config.yaml
- random_state=42 di semua tempat yang stokastik
- Jangan lanjut ke fase berikutnya
- BERHENTI di setiap gerbang H-5..H-9 dan tunggu balasan saya;
  jangan menebak isian atau memakai nilai sementara
- Jangan mengedit naskah utama (ada di luar repo)
- Laporkan Definition of Done fase ini secara eksplisit
- Jangan mengarang angka; setiap metrik harus berasal dari kode yang dijalankan
```
