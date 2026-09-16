# FASE 4 — Tuning & Evaluasi Jujur

**Estimasi:** 1,5 hari
**Prasyarat:** Fase 3 selesai (tabel perbandingan 4 model terisi)
**Output utama:** model final + `MANIFEST.json` + analisis kesalahan
**⚠️ Inti Rumusan Masalah 1 — jangan dipotong meski waktu menipis**

---

## 1. Objective

Mengoptimalkan model terbaik dari Fase 3, lalu — bagian yang lebih penting —
**menginterogasi kesalahannya secara jujur**.

Fase ini menghasilkan tiga hal yang membedakan laporan yang baik dari laporan
yang sekadar melaporkan angka:

1. Model final dengan *hyperparameter* yang dipilih lewat validasi silang,
   bukan lewat tebakan.
2. **Analisis kesalahan kualitatif** — 50 kesalahan klasifikasi dikelompokkan
   berdasarkan penyebabnya. Ini menjadi subbab tersendiri di laporan.
3. **Eksperimen 3 kelas yang gagal, dilaporkan apa adanya.** Kegagalan kelas
   netral sudah diprediksi (Temuan 3); melaporkannya sebagai temuan jauh lebih
   bernilai secara akademik daripada menyembunyikannya.

---

## 2. Technical Tasks

### T-4.1 — `GridSearchCV` dengan `scoring='f1_macro'`

Gunakan `f1_macro`, bukan `accuracy` — konsisten dengan prioritas metrik.

```python
cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=cfg["seed"])

GRIDS = {
    "complement_nb": {
        "clf__alpha": [0.1, 0.5, 1.0, 2.0],
    },
    "linear_svc": {
        "clf__C": [0.1, 0.5, 1.0, 5.0],
        "clf__class_weight": [None, "balanced"],
    },
    "logistic_regression": {
        "clf__C": [0.1, 0.5, 1.0, 5.0],
        "clf__class_weight": [None, "balanced"],
    },
}

pipe = Pipeline([("tfidf", build_vectorizer(cfg)), ("clf", model)])
gs = GridSearchCV(pipe, GRIDS[name], scoring="f1_macro",
                  cv=cv, n_jobs=-1, verbose=1, return_train_score=True)
```

Gunakan `Pipeline` agar vectorizer ikut di-*fit* ulang di setiap *fold* —
mem-*fit* vectorizer di luar CV adalah kebocoran halus yang sering terlewat.

Simpan `gs.cv_results_` lengkap ke `docs/tables/gridsearch_results.csv`:
kolom `mean_test_score`, `std_test_score`, `mean_train_score`, `params`.
Selisih train − test menunjukkan *overfitting*; layak dibahas.

### T-4.2 — Evaluasi model tuned pada test set

Ulangi protokol evaluasi ganda Fase 3 pada model hasil tuning. Tulis ke
`model_metrics` dengan `model_name` bersuffiks `_tuned`, misalnya
`linear_svc_tuned`. Jangan menimpa baris Fase 3 — perbandingan
default vs tuned adalah bagian dari hasil.

### T-4.3 — Confusion matrix

Untuk model terbaik, pada kedua set evaluasi:

```python
cm = confusion_matrix(y_true, y_pred, labels=[0, 1])
ConfusionMatrixDisplay(cm, display_labels=["Negatif", "Positif"]).plot(
    cmap="Blues", values_format="d")
```

Tampilkan dua versi: hitungan absolut dan ternormalisasi per baris
(`normalize="true"`) — yang kedua langsung menunjukkan recall per kelas.
Simpan sebagai Gambar 6.

### T-4.4 — Analisis kesalahan (50 kasus) · ⛔ GERBANG BERHENTI H-7

Ini bagian bernilai tinggi dan tidak bisa diotomatisasi.

```python
err = X_te[(y_pred != y_te)]
err_sample = err.sample(50, random_state=cfg["seed"])
# sertakan kolom: ulasan asli, ulasan_clean, rating, label, prediksi, confidence
err_sample.to_csv("docs/tables/error_analysis_50.csv", index=False)
```

> ### ⛔ BERHENTI DI SINI — H-7
>
> Agent menghasilkan `error_analysis_50.csv` lengkap dengan kolom
> `kategori_penyebab` **kosong**, lalu menghentikan Fase 4 dan menunggu.
>
> Pesan penyerahan memuat: path berkas, daftar taksonomi kategori di bawah
> sebagai pilihan yang tersedia, dan estimasi ±1,5–2 jam.
>
> **Dilarang:** mengisi kategori sendiri. Menilai apakah sebuah ulasan bernada
> sarkastik, atau apakah rating bintangnya tidak sesuai isi, adalah penilaian
> manusia terhadap bahasa dan konteks — bukan sesuatu yang bisa disimpulkan
> agent dari teks. Kategori yang ditebak agent akan menghasilkan subbab
> pembahasan yang tidak bisa dipertahankan penulisnya.

Manusia membaca satu per satu dan mengisi kolom `kategori_penyebab` dengan
taksonomi berikut:

| Kategori | Contoh |
|----------|--------|
| **Sarkasme / ironi** | "mantap banget, 2 jam nggak dapet driver" |
| **Negasi kompleks** | "bukan berarti tidak bagus, tapi..." |
| **Campur kode** | "app nya so bad, please fix lah" |
| **Label keliru dari pengguna** | Rating 5 tapi isinya keluhan (atau sebaliknya) |
| **Terlalu pendek / ambigu** | "ok" pada rating 1 |
| **Topik netral / off-topic** | "test", "belum coba" |
| **Kegagalan preprocessing** | kata kunci hilang karena stemming/stopword |

Setelah berkas dikembalikan, agent menghitung distribusi kategori dan
menyajikannya sebagai tabel. Temuan penting yang
biasanya muncul: **sebagian besar "kesalahan" sebenarnya adalah label yang
keliru dari pengguna** — rating bintang tidak selalu sesuai isi ulasan.
Bila benar demikian, itu menaikkan batas atas kinerja yang realistis, dan
harus dinyatakan di pembahasan.

Kategori "kegagalan preprocessing" bersifat *actionable*: bila jumlahnya
signifikan, kembali ke Fase 2, perbaiki, lalu jalankan ulang Fase 3–4.

### T-4.5 — Ekstraksi fitur teratas (Interpretable ML)

```python
feat = np.array(vectorizer.get_feature_names_out())

# LinearSVC / LogisticRegression
coef = model.coef_[0]
top_neg = feat[np.argsort(coef)[:20]]
top_pos = feat[np.argsort(coef)[-20:]]

# ComplementNB
log_ratio = model.feature_log_prob_[0] - model.feature_log_prob_[1]
top_neg_nb = feat[np.argsort(log_ratio)[-20:]]
```

Sajikan sebagai tabel 20 fitur per kelas per model di laporan, lalu **jawab
pertanyaan berikut secara eksplisit di pembahasan:**

> Apakah kata-kata berbobot tertinggi masuk akal secara domain
> (`gagal`, `error`, `saldo`, `dipotong`, `dibatalkan`), atau justru artefak
> (nama orang, tanda baca, stopword yang lolos)?

Jika yang muncul artefak → pipeline Fase 2 perlu diperbaiki. Ini adalah
*feedback loop* yang sah dan harus dijalankan, bukan diabaikan.

**Opsional (kerjakan hanya bila jadwal longgar):** `LimeTextExplainer` untuk
penjelasan level instans pada 3–5 contoh. Berguna sebagai ilustrasi, tetapi
jangan sampai menunda fase berikutnya.

### T-4.6 — Eksperimen varian 3 kelas

Satu kali *run*, biaya rendah, nilai akademik tinggi.

```python
cfg["labeling"]["scheme"] = "three_class"
# label: 0=neg(1-2), 1=netral(3), 2=pos(4-5)
```

Latih model terbaik dengan skema ini, lalu laporkan:

- macro-F1 keseluruhan (akan turun dibanding biner)
- **recall kelas netral** (diperkirakan sangat rendah)
- Confusion matrix — tunjukkan ke mana ulasan bintang 3 salah terklasifikasi
  (hipotesis Temuan 3: sebagian besar ke kelas negatif, karena panjangnya
  ±20 kata, mirip kelas negatif)

Tulis sebagai subbab **"Mengapa skema tiga kelas tidak layak pada dataset ini"**,
dengan bukti kuantitatif. Rasio 1:20 dan kemiripan panjang teks adalah
argumennya; confusion matrix adalah buktinya.

### T-4.7 — Simpan artefak + `MANIFEST.json`

```
ml/artifacts/
├── vectorizer.joblib
├── model_final.joblib            # model produksi (hasil keputusan 2.5)
├── model_calibrated.joblib       # bila final = LinearSVC
├── label_encoder.joblib
└── MANIFEST.json
```

`MANIFEST.json` wajib memuat:

```json
{
  "created_at": "2026-...",
  "data": {
    "raw_file": "ulasan_com.gojek.app.csv",
    "sha256": "<hash dari Fase 1>",
    "n_rows_raw": 100000,
    "n_rows_used": 96466,
    "n_train_after_dedup": 0,
    "n_test": 19294
  },
  "config_snapshot": { "isi lengkap config.yaml saat run": true },
  "environment": {
    "python": "3.12.3",
    "scikit-learn": "1.5.1",
    "numpy": "1.26.4",
    "pandas": "2.2.2",
    "Sastrawi": "1.0.1"
  },
  "model": {
    "name": "linear_svc_tuned",
    "best_params": { "C": 1.0, "class_weight": "balanced" },
    "calibrated": true
  },
  "metrics": {
    "full":             { "macro_f1": 0.0, "recall_neg": 0.0, "f1_neg": 0.0, "accuracy": 0.0 },
    "informative_ge5w": { "macro_f1": 0.0, "recall_neg": 0.0, "f1_neg": 0.0, "accuracy": 0.0 }
  },
  "baseline_majority_accuracy": 0.723,
  "random_state": 42
}
```

### T-4.8 — Keputusan model produksi

Terapkan kerangka keputusan dari Bagian 2.5 dokumen induk:

- **LinearSVC unggul macro-F1 ≥2 poin** → jadikan model produksi, bungkus
  `CalibratedClassifierCV(method="sigmoid", cv=5)` agar `/api/predict`
  bisa mengembalikan probabilitas.
- **Selisih <2 poin** → pilih ComplementNB atau LogisticRegression. Model yang
  lebih sederhana dan lebih mudah dijelaskan lebih berharga dalam konteks
  akademik dan operasional.
- **Apa pun hasilnya** → laporkan keempatnya. Hasil yang menunjukkan model
  sederhana setara dengan yang kompleks adalah temuan yang sah, bukan kegagalan.

Tulis keputusan + alasannya di `docs/model_decision.md`, termasuk angka yang
mendasarinya. Jangan simpan alasannya hanya di kepala.

---

## 3. Deliverables / Output

| Artefak | Lokasi | Keterangan |
|---------|--------|------------|
| `vectorizer.joblib` | `ml/artifacts/` | TF-IDF ter-fit |
| `model_final.joblib` | `ml/artifacts/` | Model produksi (+ terkalibrasi bila perlu) |
| `MANIFEST.json` | `ml/artifacts/` | Hash data, config, versi lib, seluruh metrik |
| `gridsearch_results.csv` | `docs/tables/` | Seluruh `cv_results_` |
| `error_analysis_50.csv` | `docs/tables/` | 50 kesalahan + kategori penyebab |
| `docs/error_analysis.md` | `docs/` | Subbab analisis kesalahan + distribusi kategori |
| `top_features.csv` | `docs/tables/` | 20 fitur/kelas × 3 model |
| `docs/three_class_experiment.md` | `docs/` | Hasil + confusion matrix varian 3 kelas |
| `docs/model_decision.md` | `docs/` | Keputusan model produksi + justifikasi angka |
| Gambar 6 | `docs/figures/` | Confusion matrix (absolut + ternormalisasi) |
| Baris `*_tuned` di `model_metrics` | PostgreSQL | Untuk `/api/model/metrics` |

---

## 4. Definition of Done

- [ ] `GridSearchCV` selesai untuk minimal 3 model; `best_params_` tercatat.
- [ ] Vectorizer berada **di dalam** `Pipeline` sehingga ikut di-fit per fold CV (verifikasi kode).
- [ ] Model tuned dievaluasi pada kedua set (`full`, `informative_ge5w`); baris `*_tuned` masuk `model_metrics`.
- [ ] Confusion matrix model terbaik tersimpan sebagai gambar (2 versi).
- [ ] **50 kesalahan diperiksa manual**, setiap baris punya `kategori_penyebab` terisi; distribusi kategori tersaji sebagai tabel.
- [ ] Tabel 20 fitur teratas per kelas tersedia untuk ≥2 model, dan pertanyaan "masuk akal secara domain atau artefak?" **terjawab tertulis** di `docs/error_analysis.md`.
- [ ] Eksperimen 3 kelas dijalankan; recall kelas netral dilaporkan apa adanya; confusion matrix menunjukkan arah kesalahan bintang 3.
- [ ] `model_final.joblib` dan `vectorizer.joblib` bisa dimuat ulang di proses baru dan menghasilkan prediksi identik pada 10 sampel uji.
- [ ] `MANIFEST.json` lengkap: hash data, snapshot config, versi library, seluruh metrik, `random_state`.
- [ ] `docs/model_decision.md` memuat keputusan + angka yang mendasarinya.
- [ ] **Gerbang H-7 dilewati dengan benar:** `kategori_penyebab` diisi manusia, bukan agent; distribusi kategori dihitung dari berkas yang dikembalikan.
- [ ] **H-10 diingatkan:** keputusan model produksi dinyatakan manusia secara eksplisit sebelum `model_final.joblib` ditetapkan.
- [ ] Commit ditag `phase-4-done`.

---

## 5. Risiko & Catatan

| Risiko | Dampak | Mitigasi |
|--------|--------|----------|
| GridSearch memakan waktu lama | Sedang | `n_jobs=-1`; grid sengaja kecil (4–8 kombinasi); LinearSVC cepat |
| `CalibratedClassifierCV` melatih ulang 5× | Sedang | Sudah diperhitungkan; LinearSVC cepat sehingga masih wajar |
| Analisis kesalahan dilewati karena "sudah kejar tayang" | **Tinggi** | Ini justru bagian paling bernilai akademik. Jika waktu sempit, potong Fase 8, bukan ini |
| Fitur teratas ternyata artefak preprocessing | Sedang | Umpan balik ke Fase 2; jalankan ulang F2→F4. Anggarkan kemungkinan satu iterasi |
| Artefak `.joblib` tidak kompatibel dengan runtime API | Sedang | Versi sklearn dikunci identik sejak Fase 0; uji muat ulang ada di DoD |

**Catatan tentang kejujuran metodologis:** bila hasil `full` jauh lebih tinggi
dari `informative_ge5w`, **itu bukan kegagalan proyek** — itu temuan utama
Anda, dan bukti kuantitatif bahwa akurasi tinggi pada data ulasan aplikasi
sering merupakan artefak distribusi panjang teks. Laporkan besar selisihnya
dengan angka.
