# FASE 1 — EDA & Data Contract

**Estimasi:** 1 hari
**Prasyarat:** Fase 0 selesai; CSV mentah ada di `data/raw/`
**Output utama:** `01_eda.ipynb` yang jalan end-to-end + `data_contract.md`

---

## 1. Objective

Memformalkan seluruh temuan Bagian 0 dokumen induk ke dalam notebook yang
**benar-benar dijalankan**, bukan angka yang disalin. Setiap angka yang akan
dikutip di Bab 1 laporan harus punya sel kode yang menghasilkannya.

Sebagian besar analisis sudah dilakukan di Bagian 0 — fase ini pekerjaannya
adalah membuat jejak audit: siapa pun yang menjalankan ulang notebook harus
mendapat angka yang sama persis.

Output kedua yang sama pentingnya: **kontrak data** — dokumen yang menetapkan
nama kolom, tipe, aturan validasi, dan penanganan *null*, sehingga Fase 2 dan
seterusnya tidak perlu menebak.

---

## 2. Technical Tasks

### T-1.1 — `ml/src/ingest.py`

Script (bukan notebook) yang bertanggung jawab memuat + memvalidasi CSV.
Notebook memanggil script ini, bukan sebaliknya — agar Fase 2 bisa memakai
fungsi yang sama.

```python
# ml/src/ingest.py
import pandas as pd
from .config import load_config, resolve

def load_raw(cfg=None) -> pd.DataFrame:
    cfg = cfg or load_config()
    df = pd.read_csv(resolve(cfg, "paths.raw_csv"))
    validate_schema(df, cfg)
    df = parse_types(df, cfg)
    return df

def validate_schema(df, cfg):
    expected = cfg["schema"]["expected_columns"]
    missing = set(expected) - set(df.columns)
    assert not missing, f"Kolom hilang: {missing}"
    assert len(df) == cfg["schema"]["expected_rows"], \
        f"Jumlah baris {len(df)} != {cfg['schema']['expected_rows']}"

def parse_types(df, cfg):
    df["Tanggal"] = pd.to_datetime(df["Tanggal"], errors="coerce")
    assert df["Tanggal"].isna().sum() == 0, "Ada Tanggal gagal parse"
    df["Rating"] = df["Rating"].astype("int8")
    df["Likes"]  = df["Likes"].fillna(0).astype("int32")
    df["Versi App"] = df["Versi App"].astype("string")  # NULL dipertahankan
    return df
```

Tambahkan fungsi turunan:

```python
def derive_versi_minor(s: pd.Series) -> pd.Series:
    """'4.93.1' -> '4.93'; NaN tetap NaN."""
    return s.str.extract(r"^(\d+\.\d+)")[0]

def derive_word_count(s: pd.Series) -> pd.Series:
    return s.fillna("").str.split().str.len().astype("int16")
```

### T-1.2 — Notebook `ml/notebooks/01_eda.ipynb`

Struktur sel, berurutan, tanpa sel yang di-*skip*:

| Seksi | Isi | Menghasilkan angka untuk |
|-------|-----|--------------------------|
| 1. Setup | import, `load_config()`, set seed, `load_raw()` | — |
| 2. Profil dasar | `df.shape`, `df.dtypes`, `df.isna().sum()`, rentang tanggal | Tabel 0.1 |
| 3. Duplikasi | duplikat baris penuh vs duplikat teks `Ulasan` | 0 dan 32.101 (32,1%) |
| 4. Distribusi rating | `value_counts()` + persentase | Tabel distribusi rating |
| 5. **Asimetri panjang** | rata-rata `word_count` per rating; jumlah ulasan ≤2 kata; top-20 teks berulang | **Temuan 2** |
| 6. Kontras kelas | statistik duplikat & ≤2 kata khusus pada subset negatif | 546 (2%), 1.614 (6%) |
| 7. Kelayakan 3 kelas | komposisi biner vs 3 kelas; rasio kelas netral | **Temuan 3** |
| 8. Analisis `Versi App` | jumlah versi unik; tabel cakupan pada ambang 30/100/200/500 | **Temuan 4** |
| 9. Analisis `Likes` | `describe()`, kuartil, skewness | **Temuan 5** |
| 10. Analisis temporal | volume per bulan; cek *gap* | **Temuan 6** |
| 11. Ekspor gambar | simpan Gambar 1–5 ke `docs/figures/` | Dokumen storytelling |

Ketentuan teknis notebook:

- Sel pertama: `%load_ext autoreload` + `%autoreload 2` agar perubahan di
  `ml/src/` langsung terbaca.
- Setiap tabel hasil disimpan juga sebagai CSV di `docs/tables/` supaya bisa
  disalin ke laporan tanpa membuka notebook.
- Setiap angka yang akan dikutip dibungkus `print()` dengan label eksplisit,
  contoh: `print(f"[A-07] Ulasan <=2 kata: {n:,} ({pct:.1f}%)")`.
  Label `[A-xx]` mengikuti slot di dokumen storytelling.

### T-1.3 — Visualisasi Gambar 1–5

| Gambar | Jenis | Isi |
|--------|-------|-----|
| Gambar 1 | Bar chart | Distribusi rating 1–5 (dengan label persentase) |
| Gambar 2 | Bar chart horizontal | Rata-rata jumlah kata per rating — **grafik kunci Temuan 2** |
| Gambar 3 | Histogram (log-y) | Distribusi `word_count`, tandai *cut-off* 2 dan 5 kata |
| Gambar 4 | Line chart | Volume ulasan per bulan; Mei 2024 diberi arsir/anotasi "periode parsial" |
| Gambar 5 | Bar chart | Cakupan data per ambang minimum versi (30/100/200/500) |

Simpan dua format: `.png` (dpi=150, untuk draf) dan `.pdf` atau `.png` dpi=300
(untuk naskah akhir). Gunakan `bbox_inches="tight"`.

### T-1.4 — `docs/data_contract.md`

Isi wajib:

1. **Provenans:** ✅ sudah terjawab — salin dari `docs/data_provenance_notes.md`
   (unduhan langsung Kaggle, pengunggah `pandaa12`, versi 1, tanpa modifikasi).
   Lengkapi dengan hash SHA-256 berkas hasil perhitungan.
2. **Kamus kolom:** nama, tipe pandas, tipe PostgreSQL, *nullable*, contoh nilai,
   keterangan.
3. **Aturan validasi** yang di-*assert* di `ingest.py`:
   - `Rating ∈ {1,2,3,4,5}`
   - `Tanggal ∈ [2024-05-21, 2025-12-31]`
   - `Likes >= 0`
   - `Ulasan` tidak boleh null/kosong
   - jumlah baris = 100.000
4. **Penanganan null:** `Versi App` NULL pada 21,9% baris → **jangan diimputasi**;
   baris tetap dipakai untuk analisis sentimen & tren, tetapi dikecualikan dari
   analisis per-versi. Setiap grafik per-versi wajib mencantumkan catatan ini.
5. **Kolom turunan:** definisi formal `word_count`, `versi_minor`,
   `sentimen_aktual` (0=neg dari rating 1–2, 1=pos dari rating 4–5, NULL jika rating 3).
6. **Pemetaan nama kolom Bab 1 → file aktual** (Temuan 1), untuk dilampirkan
   saat merevisi Bab 1.

### T-1.5 — Tabel rujukan angka untuk naskah eksternal

> **Disesuaikan dengan H-4:** naskah dikelola di luar repositori, sehingga tidak
> ada slot `[A-…]` di dalam repo yang perlu diisi agent.

Buat `docs/tables/angka_storytelling.csv` dengan kolom
`label, nilai, satuan, sumber_sel_notebook, kalimat_siap_tempel`. Kolom
terakhir berisi angka dalam bentuk frasa yang langsung bisa ditempel ke naskah
(mis. `"39.859 ulasan (39,9%) hanya berisi ≤2 kata"`).

Ini menjadi satu-satunya rujukan saat menulis naskah, sehingga tidak ada angka
yang ditulis dari ingatan. Berkas yang sama dipakai ulang di Fase 10 untuk
membangun `facts.yaml`.

---

## 3. Deliverables / Output

| Artefak | Lokasi | Keterangan |
|---------|--------|------------|
| `ingest.py` | `ml/src/` | Load + validasi skema + parse tipe + kolom turunan |
| `01_eda.ipynb` | `ml/notebooks/` | Jalan end-to-end, output tersimpan |
| Gambar 1–5 | `docs/figures/` | PNG 150dpi + 300dpi |
| Tabel EDA | `docs/tables/*.csv` | Distribusi rating, panjang per kelas, cakupan versi, volume bulanan |
| `data_contract.md` | `docs/` | Kamus kolom, aturan validasi, penanganan null, provenans |
| `angka_storytelling.csv` | `docs/tables/` | Angka + `kalimat_siap_tempel` + rujukan sel notebook |
| Catatan revisi Bab 1 | `docs/revisi-bab1.md` | Daftar perubahan yang harus dilakukan (Temuan 1 & 3) |

---

## 4. Definition of Done

- [ ] `jupyter nbconvert --execute --to notebook --inplace ml/notebooks/01_eda.ipynb` selesai tanpa error dari sel pertama.
- [ ] Seluruh angka Bagian 0 direproduksi ulang oleh notebook dan **cocok persis**: 100.000 baris; 21.910 null `Versi App`; 32.101 duplikat teks; 39.859 ulasan ≤2 kata; rata-rata kata per rating 20,8/22,4/20,0/10,0/4,4.
- [ ] Gambar 1–5 tersimpan di `docs/figures/` dan terbaca (bukan file 0 byte).
- [ ] `data_contract.md` lengkap: 6 kolom asli + 3 kolom turunan terdefinisi, aturan validasi tertulis, provenans dinyatakan.
- [ ] `angka_storytelling.csv` terisi lengkap dengan kolom `kalimat_siap_tempel`; tidak ada nilai `TBD`.
- [ ] Hash SHA-256 file CSV tercatat di `data_contract.md` (akan dipakai di `MANIFEST.json` Fase 4).
- [ ] Commit ditag `phase-1-done`.

---

## 5. Risiko & Catatan

| Risiko | Mitigasi |
|--------|----------|
| Angka notebook berbeda dari Bagian 0 | **Jangan tulis ulang angka lama.** Angka notebook yang menang; perbarui dokumen induk dan catat selisihnya |
| `Tanggal` gagal di-parse pada sebagian baris | `errors="coerce"` + assert jumlah NaT = 0; bila gagal, periksa format dan set `date_format` di config |
| ~~Provenans file tidak bisa dipastikan~~ | ✅ Terselesaikan di H-1: unduhan langsung Kaggle tanpa modifikasi. Keterbatasan yang tersisa (metode pengambilan oleh pengunggah asli tidak terdokumentasi) sudah dicatat di `data_provenance_notes.md` |

**Catatan:** fase ini tidak mengubah data sama sekali. Tidak ada file di
`data/processed/` yang dihasilkan di sini — itu pekerjaan Fase 2.
