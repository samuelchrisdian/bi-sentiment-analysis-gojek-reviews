# FASE 10 — Sintesis Hasil ke Dokumen Penelitian & Artikel

**Estimasi:** 2 hari
**Prasyarat:** Fase 9 selesai (seluruh angka final, tidak ada placeholder)
**Output utama:** berkas `.md` berisi naskah penelitian + artikel, siap diproses lebih lanjut

---

## 1. Objective

Mengubah artefak yang tersebar — tabel CSV, gambar PNG, notebook, catatan
analisis — menjadi **naskah berkelanjutan yang bisa dibaca dan diproses**.

Setelah Fase 9, seluruh angka sudah ada, tetapi bentuknya masih berupa bukti
mentah: 12 file CSV di `docs/tables/`, 10 gambar, dan beberapa catatan markdown
per fase. Yang belum ada adalah narasi yang menghubungkannya menjadi argumen.

Fase ini menghasilkan tiga keluaran dengan pembaca berbeda:

| Keluaran | Pembaca | Panjang |
|----------|---------|---------|
| **Naskah penelitian** (`research-paper.md`) | Pembaca laporan teknis; bahan tempel ke dokumen utama | ±6.000–8.000 kata |
| **Artikel populer** (`article-popular.md`) | Pembaca umum / blog teknis | ±1.200–1.800 kata |
| **Paket bahan** (`assets-manifest.md` + tabel) | Diri sendiri saat menyusun ke Word/LaTeX | — |

Dua prinsip yang mengikat seluruh fase ini:

1. **Setiap angka wajib punya sumber.** Tidak ada kalimat yang memuat angka
   tanpa rujukan ke file di `docs/tables/`. Bila angka tidak ada di sana,
   angka itu tidak boleh ditulis.
2. **Keluaran ini adalah draf, bukan naskah siap serah.** Tanggung jawab
   akademik ada pada penulis manusia (lihat H-11 di
   `00-human-prep-checklist.md`).

> **Konteks proyek (H-3 & H-4):** ini **tugas independen, bukan tesis** — tidak
> ada pembimbing atau sidang. Naskah utama dikelola **di luar repositori**.
> Karena itu keluaran fase ini bukan dokumen final, melainkan **bahan tempel**:
> `.md` bersih berisi tabel markdown, angka bersumber, dan draf narasi yang
> disalin manusia ke dokumen utamanya. Agent tidak pernah mengedit naskah utama,
> dan tidak menulis dengan bahasa berorientasi sidang.

---

## 2. Technical Tasks

### T-10.1 — Kumpulkan seluruh angka ke satu berkas fakta

Sebelum menulis satu kalimat pun, konsolidasikan seluruh angka final ke
`docs/synthesis/facts.yaml`. Berkas ini menjadi satu-satunya sumber angka untuk
seluruh naskah — bila sebuah angka tidak ada di sini, ia tidak boleh muncul di
naskah.

```yaml
# docs/synthesis/facts.yaml
dataset:
  n_rows: 100000
  n_columns: 6
  periode: "21 Mei 2024 – 31 Desember 2025"
  n_bulan: 20
  source_file: "ulasan_com.gojek.app.csv"
  source_table: "docs/tables/profil_dataset.csv"

distribusi_rating:
  bintang_1: { n: 23178, pct: 23.2 }
  bintang_2: { n: 3554,  pct: 3.6 }
  bintang_3: { n: 3534,  pct: 3.5 }
  bintang_4: { n: 5083,  pct: 5.1 }
  bintang_5: { n: 64651, pct: 64.7 }
  source_table: "docs/tables/distribusi_rating.csv"

asimetri_panjang:
  rata_kata_per_rating: { r1: 20.8, r2: 22.4, r3: 20.0, r4: 10.0, r5: 4.4 }
  n_ulasan_max_2_kata: 39859
  pct_ulasan_max_2_kata: 39.9
  duplikat_teks_total: 32101
  duplikat_teks_negatif: 546
  source_table: "docs/tables/panjang_per_rating.csv"

model:
  baseline_majority_accuracy: 0.723
  # DIISI DARI docs/tables/model_metrics.csv — jangan ditulis dari ingatan
  best_model: null
  macro_f1_full: null
  macro_f1_informative: null
  selisih_poin: null
  recall_neg_full: null
  source_table: "docs/tables/model_metrics.csv"

topik:
  n_kategori: null
  peringkat_frekuensi: null
  kesepakatan_validasi_silang: null
  source_table: "docs/tables/topics_ranked.csv"
```

Tulis script pembantu `ml/src/collect_facts.py` yang **membaca CSV di
`docs/tables/` dan mengisi nilai `null` secara otomatis**, bukan diisi tangan.
Ini menutup celah terbesar penulisan laporan: angka yang disalin salah.

### T-10.2 — Kerangka naskah penelitian

Buat `docs/synthesis/research-paper.md` dengan struktur berikut. Setiap bagian
menarik bahan dari fase tertentu — tidak ada bagian yang ditulis dari nol.

| Bagian | Sumber bahan | Fase asal |
|--------|--------------|-----------|
| Abstrak | ringkasan seluruh temuan (tulis terakhir) | — |
| 1. Pendahuluan | latar belakang + rumusan masalah dari naskah Bab 1 | H-4 |
| 2. Tinjauan Pustaka | rujukan NB/SVM/LogReg, preprocessing bahasa Indonesia | manual |
| 3. Metodologi | | |
| 3.1 Dataset & provenans | `data_contract.md`, `data_provenance_notes.md` | 1, H-1 |
| 3.2 Preprocessing | `preprocessing_validation.md`, `slang_dict.csv` | 2 |
| 3.3 Desain label | keputusan biner + alasan | 2, H-3 |
| 3.4 Model & konfigurasi | `MANIFEST.json`, `config.yaml` | 3, 4 |
| 3.5 Protokol evaluasi | evaluasi ganda + baseline | 3 |
| 4. Hasil | | |
| 4.1 Karakteristik data | Gambar 1–5, tabel EDA | 1 |
| 4.2 Perbandingan model | `model_metrics.csv`, Gambar 10 | 3 |
| 4.3 Hasil tuning | `gridsearch_results.csv`, Gambar 6 | 4 |
| 4.4 Topik keluhan | `topics_ranked.csv`, Gambar 8–9 | 5 |
| 5. Pembahasan | | |
| 5.1 Temuan metodologis: asimetri panjang | selisih `full` vs `informative_ge5w` | 3, 4 |
| 5.2 Analisis kesalahan | `error_analysis.md` | 4, H-7 |
| 5.3 Interpretasi fitur | `top_features.csv` | 4 |
| 5.4 Kegagalan skema 3 kelas | `three_class_experiment.md` | 4 |
| 5.5 Implikasi bisnis | peringkat topik + tren bulanan | 5 |
| 6. Keterbatasan | `limitations.md` | 9 |
| 7. Kesimpulan & Saran | jawaban eksplisit atas RM1 & RM2 | — |
| Daftar Pustaka | manual | — |
| Lampiran | `openapi.json`, `slang_dict.csv`, tangkapan layar | 7, 2, 8 |

Ketentuan penulisan:

- **Setiap klaim numerik diikuti rujukan tabel** dalam komentar HTML:
  `<!-- src: docs/tables/model_metrics.csv row 3 -->`. Komentar ini tidak
  tampil saat di-*render*, tetapi memungkinkan verifikasi cepat oleh manusia
  maupun agent.
- **Gambar dirujuk dengan path relatif**: `![Gambar 2](../figures/final/gambar-02-panjang-per-rating.png)`.
- **Tabel ditulis sebagai tabel markdown**, bukan gambar — agar bisa disalin
  ke Word tanpa mengetik ulang.
- Gunakan kalimat aktif dan lugas. Hindari "dapat dilihat bahwa", "sangatlah
  penting", dan pengisi sejenis.
- **Optimalkan untuk tempel manual (H-4):** setiap bagian diawali penanda
  `<!-- ===== §4.2 Perbandingan Model — SIAP TEMPEL ===== -->` agar manusia
  dapat memotong per bagian tanpa membaca ulang seluruh berkas. Jangan memakai
  fitur markdown yang hilang saat ditempel ke pengolah kata (footnote markdown,
  definition list); tabel dan judul biasa aman.

### T-10.3 — Bagian yang menuntut perlakuan khusus

Tiga bagian di bawah adalah inti nilai laporan ini. Jangan tulis sebagai
ringkasan angka; tulis sebagai argumen.

**5.1 Temuan metodologis (bagian terpenting).** Struktur argumennya:

1. Fakta: 39,9% ulasan hanya ≤2 kata; bintang 5 rata-rata 4,4 kata, bintang 1
   sepanjang 20,8 kata.
2. Konsekuensi teoretis: TF-IDF akan mempelajari korelasi trivial
   `mantap|bagus|ok → positif`.
3. Bukti: selisih macro-F1 antara set `full` dan `informative_ge5w`.
4. Implikasi: akurasi tinggi pada dataset ulasan aplikasi sering merupakan
   artefak distribusi panjang teks, bukan bukti pemahaman sentimen.
5. Rekomendasi metodologis bagi penelitian sejenis: laporkan evaluasi ganda.

**5.4 Kegagalan skema 3 kelas.** Tulis sebagai temuan, bukan permintaan maaf.
Rasio 1:20 dan kemiripan panjang teks bintang 3 dengan kelas negatif adalah
argumennya; confusion matrix adalah buktinya.

**7. Kesimpulan.** Jawab RM1 dan RM2 dengan kalimat yang berdiri sendiri —
satu paragraf per rumusan masalah, memuat angka, tanpa hedging. Bila hasilnya
"ketiga model setara", tulis begitu: temuan yang menunjukkan model sederhana
setara dengan yang kompleks adalah hasil yang sah.

> **Pemutakhiran H-10 (17 September 2026).** RM1 membandingkan **tiga keluarga
> algoritma dengan empat varian terlatih** — Naive Bayes (ComplementNB,
> MultinomialNB), SVM (LinearSVC), dan Logistic Regression. Tulis "tiga keluarga
> algoritma dengan empat varian", **bukan** "tiga model": tabel hasil memuat
> empat baris dan penguji akan menanyakan selisihnya.
>
> Angka inti jawaban RM1 sudah tersedia: **rentang macro-F1 keempat varian hanya
> 1,88 poin (0,9153–0,9341)** pada set `full`, dan model produksi yang terpilih
> justru bukan yang paling kompleks. Sumber: `docs/model_decision.md`,
> `docs/tuning_results.md`.

### T-10.4 — Artikel populer

`docs/synthesis/article-popular.md` — pembacanya bukan pembaca laporan teknis,
melainkan praktisi atau pembaca umum. Perbedaan perlakuannya:

- **Sudut pandang:** bukan "saya membandingkan dua algoritma", melainkan
  "apa yang 100.000 keluhan pengguna ungkapkan, dan mengapa akurasi model
  bisa menipu".
- **Buang:** notasi matematis, tabel hyperparameter, rincian `GridSearchCV`.
- **Pertahankan:** temuan asimetri panjang (ini menarik bagi siapa pun yang
  pernah membangun klasifikasi teks), peringkat topik keluhan, dan 2–3 contoh
  ulasan nyata.
- **Struktur:** kail pembuka (angka yang mengejutkan) → konteks → temuan utama
  → satu pelajaran yang bisa dibawa pulang.
- Maksimal 3 grafik, masing-masing dengan keterangan yang bisa dipahami tanpa
  membaca teks di sekitarnya.

Sertakan di bagian akhir: tautan repositori dan catatan bahwa seluruh angka
dapat direproduksi.

### T-10.5 — Paket bahan untuk penyusunan akhir

`docs/synthesis/assets-manifest.md` — indeks yang memetakan setiap gambar dan
tabel ke lokasi pemakaiannya di naskah:

| ID | Berkas | Dipakai di | Keterangan gambar/tabel |
|----|--------|-----------|-------------------------|
| Gambar 1 | `figures/final/gambar-01-distribusi-rating.png` | §4.1 | Distribusi rating 1–5 (n=100.000) |
| Tabel 2 | `tables/model_metrics.csv` | §4.2 | Perbandingan 4 model × 2 set evaluasi |
| … | | | |

Gunanya: saat menyusun ke Word/LaTeX, Anda tidak perlu menelusuri ulang gambar
mana milik bagian mana, dan keterangan gambar sudah tertulis — tidak perlu
dikarang ulang saat menempel.

### T-10.6 — Abstrak dan kata kunci

Tulis **paling akhir**, setelah seluruh naskah selesai. Struktur 5 kalimat:

1. Konteks & masalah
2. Data & metode (sebutkan ketiga model dan protokol evaluasi ganda)
3. Hasil utama dengan angka
4. Temuan metodologis (selisih `full` vs `informative_ge5w`)
5. Implikasi

Siapkan dua versi: Indonesia dan Inggris (lihat K-4 pada
`00-human-prep-checklist.md`). Kata kunci: 4–6 istilah, termasuk
"analisis sentimen", "bahasa Indonesia", "ketidakseimbangan kelas",
"ulasan aplikasi".

### T-10.7 — Verifikasi silang angka (otomatis)

Tulis `ml/src/verify_manuscript.py` yang:

1. Mengekstrak seluruh pola angka dari `research-paper.md` dan `article-popular.md`.
2. Mencocokkannya dengan nilai di `facts.yaml`.
3. Melaporkan angka yang **tidak** ditemukan di `facts.yaml` sebagai peringatan.

```bash
python -m ml.src.verify_manuscript
# → PERINGATAN: angka '0.891' di research-paper.md:142 tidak ada di facts.yaml
```

Ini menangkap kesalahan paling umum dalam penulisan laporan: angka yang
berubah setelah *run* terakhir tetapi lupa diperbarui di naskah.

### T-10.8 — Ekspor ke format lain (opsional)

Karena keluaran berbentuk `.md` murni, konversi menjadi mekanis:

```bash
# ke Word
pandoc docs/synthesis/research-paper.md -o docs/synthesis/research-paper.docx \
       --reference-doc=docs/synthesis/template.docx

# ke PDF via LaTeX
pandoc docs/synthesis/research-paper.md -o research-paper.pdf \
       --pdf-engine=xelatex --toc
```

Jangan jadikan langkah ini DoD — format akhir bergantung pada ketentuan kampus
yang mungkin menuntut template khusus. Yang penting: sumbernya `.md` yang bersih.

---

## 3. Deliverables / Output

| Artefak | Lokasi | Keterangan |
|---------|--------|------------|
| `facts.yaml` | `docs/synthesis/` | Seluruh angka final + rujukan tabel sumber |
| `collect_facts.py` | `ml/src/` | Mengisi `facts.yaml` otomatis dari CSV |
| `research-paper.md` | `docs/synthesis/` | Naskah penelitian lengkap, 7 bagian + lampiran |
| `article-popular.md` | `docs/synthesis/` | Artikel populer 1.200–1.800 kata |
| `assets-manifest.md` | `docs/synthesis/` | Indeks gambar & tabel → lokasi pemakaian |
| `abstract-id.md`, `abstract-en.md` | `docs/synthesis/` | Abstrak dua bahasa + kata kunci |
| `verify_manuscript.py` | `ml/src/` | Pemeriksa konsistensi angka naskah |
| `verification_report.txt` | `docs/synthesis/` | Hasil pemeriksaan terakhir (nol peringatan) |

---

## 4. Definition of Done

- [ ] `facts.yaml` terisi penuh — **tidak ada nilai `null`**; setiap entri punya `source_table` yang benar-benar ada.
- [ ] `python -m ml.src.collect_facts` berjalan dan menghasilkan `facts.yaml` dari CSV, bukan diisi tangan.
- [ ] `research-paper.md` memuat ketujuh bagian; tidak ada bagian berisi `TODO` atau `[isi nanti]`.
- [ ] **Setiap klaim numerik di naskah punya komentar rujukan** `<!-- src: ... -->`.
- [ ] `python -m ml.src.verify_manuscript` → **nol peringatan** pada kedua naskah.
- [ ] RM1 dan RM2 **terjawab eksplisit** di Bab 7, masing-masing satu paragraf memuat angka.
- [ ] Bagian 5.1 (temuan asimetri panjang) tersusun sebagai argumen lima langkah, bukan daftar angka.
- [ ] Kegagalan skema 3 kelas dilaporkan sebagai temuan dengan bukti confusion matrix.
- [ ] Seluruh gambar yang dirujuk naskah benar-benar ada di `docs/figures/final/` (uji: tidak ada tautan gambar rusak).
- [ ] `article-popular.md` ≤1.800 kata, maksimal 3 grafik, tanpa notasi matematis.
- [ ] Abstrak Indonesia selesai; versi Inggris selesai bila K-4 menghendaki.
- [ ] `assets-manifest.md` mencakup seluruh 10 gambar dan seluruh tabel yang dirujuk.
- [ ] **H-11 selesai:** naskah sudah dibaca ulang oleh manusia, setiap angka diverifikasi, tidak ada kalimat yang tidak bisa dijelaskan penulis dengan kalimatnya sendiri.
- [ ] Commit ditag `phase-10-done` dan `v1.1`.

---

## 5. Risiko & Catatan

| Risiko | Dampak | Mitigasi |
|--------|--------|----------|
| Angka di naskah tidak sinkron dengan hasil *run* terakhir | **Tinggi** | `facts.yaml` + `verify_manuscript.py` (T-10.1, T-10.7) |
| Naskah hasil agent terdengar generik dan tidak bisa dipertanggungjawabkan penulis | **Tinggi** | H-11 wajib; setiap kalimat yang tidak dipahami penulis harus ditulis ulang |
| Klaim melebihi bukti (mis. "model memahami sentimen") | **Tinggi** | Batasi klaim pada apa yang diukur; bagian Keterbatasan wajib dirujuk di Pembahasan |
| Bagian Tinjauan Pustaka dikarang, sitasi tidak nyata | **Kritis** — rujukan palsu merusak seluruh laporan | **Agent tidak menulis sitasi.** Daftar pustaka diisi manusia dari sumber yang benar-benar dibaca |
| Artikel populer menyederhanakan sampai keliru | Sedang | Temuan metodologis tetap dinyatakan utuh; jangan mengubah "selisih X poin" jadi "model kami akurat" |

> ⚠️ **Batas yang tidak boleh dilanggar:** agent boleh menyusun narasi dari angka
> yang dihasilkan kode, tetapi **tidak boleh menulis sitasi, mengarang rujukan,
> atau mengklaim membaca literatur.** Bagian Tinjauan Pustaka dan Daftar Pustaka
> adalah pekerjaan manusia sepenuhnya. Naskah yang dihasilkan fase ini adalah
> draf berbasis data, bukan karya ilmiah yang selesai.

**Catatan bentuk keluaran:** seluruh hasil berupa `.md` murni dengan tabel
markdown dan tautan gambar relatif. Format ini bisa dibaca langsung, diproses
agent lain, dikonversi `pandoc` ke Word/PDF, atau ditempel ke Google Docs tanpa
kehilangan struktur — itulah alasan tidak memakai `.docx` sebagai sumber.
