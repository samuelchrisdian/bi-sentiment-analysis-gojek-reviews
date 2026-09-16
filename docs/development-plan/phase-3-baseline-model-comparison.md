# FASE 3 — Baseline & Komparasi Model

**Estimasi:** 2 hari
**Prasyarat:** Fase 2 selesai (`reviews_clean.parquet` tervalidasi)
**Output utama:** tabel perbandingan 4 model × 2 set evaluasi
**⚠️ Inti Rumusan Masalah 1**

---

## 1. Objective

Menjawab RM1: **model mana yang lebih baik untuk klasifikasi sentimen ulasan
Gojek berbahasa Indonesia — Naive Bayes atau SVM?**

Empat model dilatih dengan konfigurasi TF-IDF dan `random_state` yang identik,
sehingga perbedaan skor benar-benar berasal dari algoritma, bukan dari
perbedaan perlakuan data.

Yang membedakan fase ini dari eksperimen ML biasa adalah **protokol evaluasi
ganda**. Karena 39,9% ulasan hanya berisi ≤2 kata dan hampir semuanya positif
(Temuan 2), akurasi tinggi pada test set penuh tidak membuktikan model memahami
sentimen. Selisih skor antara set `full` dan `informative_ge5w` adalah temuan
metodologis utama laporan ini.

---

## 2. Technical Tasks

### T-3.1 — Persiapan data & split

```python
df = pd.read_parquet(cfg_path("clean_parquet"))
df = df[df["sentimen_aktual"].notna()].copy()   # buang rating 3 (skema biner)
assert len(df) == 96466   # 100000 - 3534

X = df["ulasan_clean"]
y = df["sentimen_aktual"].astype(int)

X_tr, X_te, y_tr, y_te, idx_tr, idx_te = train_test_split(
    X, y, df.index,
    test_size=cfg["split"]["test_size"],
    stratify=y if cfg["split"]["stratify"] else None,
    random_state=cfg["seed"],
)
```

**Split dilakukan sebelum deduplikasi dan sebelum fit vectorizer.** Urutan ini
tidak boleh dibalik — mem-*fit* TF-IDF pada data penuh adalah kebocoran data.

### T-3.2 — Deduplikasi training set (dan hanya training set)

```python
if cfg["preprocessing"]["dedup_training_text"]:
    mask = ~X_tr.duplicated()
    n_before = len(X_tr)
    X_tr, y_tr = X_tr[mask], y_tr[mask]
    print(f"Dedup training: {n_before:,} -> {len(X_tr):,} "
          f"({n_before - len(X_tr):,} dibuang)")
```

Test set **tidak** dideduplikasi — ia harus merepresentasikan distribusi nyata
yang akan dihadapi model. Catat jumlah baris sebelum/sesudah untuk dilaporkan.

Jalankan juga varian tanpa deduplikasi sebagai pembanding (satu baris config,
dua kali *run*) — selisihnya adalah bukti kuantitatif seberapa besar pengaruh
32,1% duplikat teks terhadap pembelajaran.

### T-3.3 — Hitung baseline mayoritas **terlebih dahulu**

Ini dikerjakan sebelum model apa pun dilatih, dan angkanya dicatat sebagai
baris pertama di `model_metrics`.

```python
from sklearn.dummy import DummyClassifier

dummy = DummyClassifier(strategy="most_frequent", random_state=cfg["seed"])
dummy.fit(X_tr, y_tr)
y_pred = dummy.predict(X_te)
# accuracy ≈ 0.723, macro_f1 ≈ 0.420, recall_neg = 0.000
```

Catat eksplisit: **model yang tidak mengalahkan macro-F1 baseline tidak
mempelajari apa pun.** Baseline ini wajib muncul di setiap tabel hasil laporan.

### T-3.4 — `ml/src/features.py` — vectorizer tunggal

Satu objek vectorizer, di-*fit* sekali pada training set, dipakai oleh keempat model.

```python
from sklearn.feature_extraction.text import TfidfVectorizer

def build_vectorizer(cfg):
    t = cfg["features"]["tfidf"]
    return TfidfVectorizer(
        ngram_range=tuple(t["ngram_range"]),   # (1, 2)
        min_df=t["min_df"],                    # 3
        max_features=t["max_features"],        # 30000
        sublinear_tf=t["sublinear_tf"],        # True
        lowercase=False,      # sudah dilakukan di Fase 2
        token_pattern=r"\S+", # teks sudah ditokenisasi & digabung spasi
    )
```

`lowercase=False` dan `token_pattern=r"\S+"` penting — tanpa itu, TF-IDF akan
melakukan tokenisasi ulang dengan regex bawaan dan membuang token satu huruf
serta memotong hasil normalisasi Fase 2.

### T-3.5 — `ml/src/train.py` — latih 4 model

```python
MODELS = {
    "complement_nb": ComplementNB(alpha=1.0),
    "multinomial_nb": MultinomialNB(alpha=1.0),
    "linear_svc": LinearSVC(C=1.0, class_weight="balanced",
                            max_iter=5000, random_state=cfg["seed"]),
    "logistic_regression": LogisticRegression(C=1.0, class_weight="balanced",
                            max_iter=1000, solver="liblinear",
                            random_state=cfg["seed"]),
}
```

Catatan wajib:

- **`ComplementNB`, bukan `MultinomialNB` saja.** ComplementNB dirancang untuk
  data tidak seimbang (rasio 27:72 di sini). Keduanya tetap dijalankan agar
  perbandingannya bisa dilaporkan — biayanya hitungan detik.
- **`LinearSVC`, JANGAN `SVC(kernel='rbf')`.** Kompleksitas `SVC` antara O(n²)
  dan O(n³); pada 96k baris pelatihannya bisa berjam-jam atau gagal. Ini batas
  komputasi, bukan preferensi.
- `LogisticRegression` sebagai model ketiga memberi dua hal yang tidak dimiliki
  LinearSVC: probabilitas terkalibrasi (untuk indikator keyakinan di dashboard)
  dan koefisien yang langsung ditafsirkan sebagai log-odds.
- NB **tidak** menerima `class_weight` — jangan paksakan; ketidakseimbangan
  ditangani oleh ComplementNB secara struktural.

### T-3.6 — Ukur waktu latih dengan benar

```python
import time
t0 = time.perf_counter()
model.fit(X_tr_vec, y_tr)
train_seconds = time.perf_counter() - t0
```

Gunakan `perf_counter()`, bukan `time.time()`, dan jangan mengira-ngira.
Ukur juga waktu inferensi pada test set (`predict_seconds`) — ini relevan untuk
argumen kelayakan operasional di pembahasan.

### T-3.7 — Evaluasi ganda (wajib)

```python
EVAL_SETS = {
    "full": te_idx,
    "informative_ge5w": te_idx[df.loc[te_idx, "word_count"] >= 5],
}
```

Untuk setiap model × setiap set, hitung dan simpan:

| Metrik | Fungsi sklearn | Prioritas laporan |
|--------|----------------|-------------------|
| `recall_neg` | `recall_score(..., pos_label=0)` | **1** |
| `macro_f1` | `f1_score(..., average="macro")` | **2** |
| `f1_neg` | `f1_score(..., pos_label=0)` | **3** |
| `precision_neg` | `precision_score(..., pos_label=0)` | pelengkap |
| `accuracy` | `accuracy_score` | pelengkap — selalu dampingkan baseline 72,3% |
| `train_seconds` | `perf_counter` | pelengkap |

Simpan juga `classification_report(output_dict=True)` lengkap ke
`ml/artifacts/reports/<model>_<evalset>.json`.

### T-3.8 — Tulis hasil ke `model_metrics`

Dua jalur penulisan, keduanya dilakukan:

1. CSV: `docs/tables/model_metrics.csv` — untuk laporan, tidak butuh DB hidup.
2. PostgreSQL tabel `model_metrics` — untuk endpoint `/api/model/metrics` di Fase 7.

Sertakan baris `model_name='majority_baseline'` agar dashboard bisa
menampilkannya sebagai garis referensi.

### T-3.9 — Notebook `02_model_comparison.ipynb`

Notebook ini memanggil `train.py`, bukan menduplikasi logikanya. Isinya:
tabel perbandingan, grafik batang macro-F1 per model × set evaluasi (dengan
garis baseline), dan **grafik selisih `full` − `informative_ge5w`** — grafik
terakhir ini adalah visual kunci Temuan 2 di laporan.

---

## 3. Deliverables / Output

| Artefak | Lokasi | Keterangan |
|---------|--------|------------|
| `features.py` | `ml/src/` | Builder TF-IDF dari config |
| `train.py` | `ml/src/` | Latih 4 model + baseline, ukur waktu |
| `evaluate.py` | `ml/src/` | Metrik untuk 2 set evaluasi |
| `model_metrics.csv` | `docs/tables/` | 5 baris (4 model + baseline) × 2 set |
| Tabel `model_metrics` di DB | PostgreSQL | Sumber `/api/model/metrics` |
| `reports/*.json` | `ml/artifacts/reports/` | `classification_report` lengkap |
| `02_model_comparison.ipynb` | `ml/notebooks/` | Tabel + 3 grafik |
| Grafik perbandingan | `docs/figures/` | macro-F1 per model; selisih full vs informative |
| Catatan dedup | `docs/dedup_impact.md` | Selisih skor dengan/tanpa deduplikasi training |

---

## 4. Definition of Done

- [ ] Baseline mayoritas terhitung dan tercatat **sebelum** model mana pun dilatih (accuracy ≈ 0,723; recall_neg = 0).
- [ ] Keempat model terlatih tanpa error; `LinearSVC` konvergen (tidak ada `ConvergenceWarning` yang diabaikan — bila muncul, naikkan `max_iter` dan catat).
- [ ] Tabel perbandingan **4 model × 2 set evaluasi = 8 baris** terisi penuh; tidak ada sel kosong.
- [ ] **Seluruh model mengungguli baseline pada macro-F1** di set `full`. Bila ada yang tidak, jangan lanjut — periksa pipeline Fase 2.
- [ ] Selisih macro-F1 `full` − `informative_ge5w` terhitung untuk setiap model dan tercatat sebagai temuan.
- [ ] `train_seconds` diukur dengan `perf_counter()` untuk setiap model.
- [ ] Vectorizer di-*fit* **hanya** pada training set (verifikasi dengan membaca kode, bukan asumsi).
- [ ] Deduplikasi diterapkan **hanya** pada training set; jumlah baris sebelum/sesudah tercatat.
- [ ] `SELECT count(*) FROM model_metrics` mengembalikan ≥10 (5 model × 2 set).
- [ ] Commit ditag `phase-3-done`.

---

## 5. Risiko & Catatan

| Risiko | Dampak | Mitigasi |
|--------|--------|----------|
| Kebocoran data (vectorizer di-fit pada data penuh) | **Kritis** — seluruh angka tidak sah | Urutan split → fit; review kode eksplisit di DoD |
| Akurasi tinggi menyesatkan (Temuan 2) | **Tinggi** | Evaluasi ganda + baseline selalu ditampilkan |
| `LinearSVC` tidak konvergen | Sedang | `max_iter=5000`; bila masih gagal, turunkan `C` dan catat |
| Test set ikut dideduplikasi | Sedang | Kode memisahkan eksplisit; verifikasi jumlah baris test = 19.294 |
| Model kalah dari baseline | Tinggi | Indikator bug di Fase 2 — jangan lanjut, telusuri balik |

**Yang TIDAK dikerjakan di fase ini:** *hyperparameter tuning*, *confusion matrix*
mendalam, analisis kesalahan, ekstraksi fitur teratas, dan eksperimen 3 kelas.
Semuanya milik Fase 4. Fase 3 menghasilkan **baseline komparatif dengan
parameter default** — itu titik referensi yang akan dibandingkan dengan hasil
tuning nanti.
