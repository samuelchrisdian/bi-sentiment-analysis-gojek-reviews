# FASE 2 — Preprocessing & Desain Label

**Estimasi:** 2 hari
**Prasyarat:** Fase 1 selesai (`data_contract.md` final)
**Output utama:** `data/processed/reviews_clean.parquet` + `slang_dict.py`
**⚠️ Fase dengan risiko kualitas tertinggi — kesalahan di sini merusak semua fase berikutnya**

---

## 1. Objective

Mengubah teks ulasan mentah yang informal menjadi bentuk yang siap divektorisasi,
sekaligus menetapkan label sentimen secara formal.

Dua hal yang membuat fase ini kritis:

1. **Kamus normalisasi slang** adalah kontribusi keilmuan yang Anda klaim di Bab 1.
   Kualitasnya menentukan apakah `gk bs bayar` dikenali sebagai `tidak bisa bayar`
   atau dibuang sebagai *noise*.
2. **Preprocessing yang terlalu agresif menghapus sinyal negasi.** Jika `tidak`
   masuk daftar *stopword*, maka "tidak bagus" menjadi "bagus" — model akan
   salah total pada justru kelas yang paling Anda pedulikan.

Target: pipeline deterministik, cepat (<5 menit untuk 100k dokumen), dan
terverifikasi manual pada sampel.

---

## 2. Technical Tasks

### T-2.1 — `ml/src/slang_dict.py` · ⛔ GERBANG BERHENTI H-5

Ini pekerjaan manual, dan memang harus manual. Prosedur terbagi dua bagian yang
dipisahkan oleh gerbang berhenti.

**Bagian agent (sebelum gerbang):**

1. Tokenisasi seluruh korpus setelah *case folding*, hitung frekuensi token.
2. Saring token yang **tidak** dikenali kamus baku (gunakan daftar kata dasar
   Sastrawi sebagai referensi).
3. Ambil 500 token teratas berdasarkan frekuensi.
4. Tulis ke `docs/tables/unknown_tokens_500.csv` dengan kolom:
   `token_asli, frekuensi, contoh_konteks, bentuk_baku, buang`
   — kolom `bentuk_baku` dan `buang` **dibiarkan kosong**.
5. Urutkan agar **varian negasi muncul di baris teratas** (token yang mengandung
   pola `gk|ga|ng|tdk|blm|bkn`), karena itu yang paling berdampak.

> ### ⛔ BERHENTI DI SINI — H-5
>
> Agent **menghentikan Fase 2** dan menyerahkan `unknown_tokens_500.csv`.
> Pesan penyerahan memuat: path berkas, jumlah baris, instruksi pengisian kolom
> `bentuk_baku`, dan estimasi waktu (±3 jam).
>
> **Dilarang:** mengisi `bentuk_baku` dengan tebakan, memakai kamus slang pihak
> ketiga sebagai pengganti sementara, atau melanjutkan ke T-2.3 dengan kamus
> parsial. Kualitas kamus ini menentukan kualitas kelas negatif — kelas yang
> menjadi fokus seluruh penelitian.

**Bagian agent (setelah berkas dikembalikan):**

6. Konversi CSV terisi menjadi `ml/src/slang_dict.py` (`SLANG_DICT` dan
   `NOISE_TOKENS`) — konversi mekanis, tanpa menambah entri sendiri.
7. Laporkan jumlah entri final dan berapa di antaranya varian negasi.

```python
# ml/src/slang_dict.py
SLANG_DICT = {
    # negasi — PRIORITAS TERTINGGI, jangan sampai terlewat
    "gk": "tidak", "ga": "tidak", "gak": "tidak", "nggak": "tidak",
    "ngga": "tidak", "enggak": "tidak", "tdk": "tidak", "g": "tidak",
    "gbs": "tidak bisa", "gabisa": "tidak bisa", "gamau": "tidak mau",
    "blm": "belum", "blom": "belum", "gapernah": "tidak pernah",

    # intensitas
    "bgt": "banget", "bngt": "banget", "banget": "banget", "pol": "sangat",
    "parah": "parah", "bener": "benar", "bner": "benar",

    # umum
    "udh": "sudah", "udah": "sudah", "dah": "sudah", "sdh": "sudah",
    "aja": "saja", "aj": "saja", "gmn": "bagaimana", "knp": "kenapa",
    "krn": "karena", "krna": "karena", "dgn": "dengan", "utk": "untuk",
    "yg": "yang", "jd": "jadi", "tp": "tapi", "tpi": "tapi",
    "org": "orang", "orng": "orang", "sy": "saya", "gw": "saya", "gue": "saya",

    # domain Gojek
    "drver": "driver", "driver": "driver", "ojol": "ojek online",
    "gopay": "gopay", "gofood": "gofood", "cs": "layanan pelanggan",
    "apk": "aplikasi", "app": "aplikasi", "aplikasinya": "aplikasi",
    "promonya": "promo", "sldo": "saldo", "trf": "transfer",
    "otw": "dalam perjalanan", "cancel": "batal", "ngecancel": "batal",
}

# Token yang dibuang sepenuhnya (bukan dinormalisasi)
NOISE_TOKENS = {"wkwk", "wkwkwk", "hehe", "hihi", "xixi", "hmm", "yaa"}
```

Simpan juga versi CSV `docs/tables/slang_dict.csv`
(kolom: `token_asli, bentuk_baku, frekuensi, kategori`) untuk dilampirkan
di laporan sebagai bukti kontribusi.

### T-2.2 — Daftar *stopword* kustom

**Jangan pakai daftar stopword Sastrawi apa adanya.** Daftar itu berisi
`tidak`, `bukan`, `jangan`, `belum` — kata-kata pembawa negasi yang justru
paling penting untuk klasifikasi sentimen.

```python
# ml/src/stopwords.py
from Sastrawi.StopWordRemover.StopWordRemoverFactory import StopWordRemoverFactory

# Kata yang WAJIB dipertahankan meski ada di daftar Sastrawi
NEGATION_KEEP = {
    "tidak", "bukan", "jangan", "belum", "tanpa",
    "kurang", "susah", "sulit", "sering", "selalu", "pernah",
}

def build_stopwords() -> set[str]:
    base = set(StopWordRemoverFactory().get_stop_words())
    return base - NEGATION_KEEP
```

Dokumentasikan keputusan ini di laporan — ini bukan detail implementasi,
melainkan keputusan metodologis yang bisa ditanya penguji.

### T-2.3 — `ml/src/preprocess.py`

Urutan operasi (urutan ini penting, jangan diubah tanpa alasan):

```
case folding
  → hapus URL
  → hapus mention/hashtag
  → hapus emoji & simbol non-ASCII
  → hapus angka
  → hapus tanda baca (ganti dengan spasi, bukan string kosong)
  → normalisasi pengulangan huruf (baguuuus → bagus)
  → tokenisasi (split whitespace)
  → normalisasi slang (per token)
  → buang noise token
  → stopword removal (daftar kustom T-2.2)
  → stemming Sastrawi (dengan cache)
  → gabung kembali dengan spasi
```

Catatan implementasi penting:

- **Tanda baca → spasi.** `bagus,mantap` harus jadi `bagus mantap`, bukan
  `bagusmantap`.
- **Normalisasi pengulangan:** `re.sub(r"(.)\1{2,}", r"\1", text)` — tiga huruf
  identik atau lebih dipangkas jadi satu. Jangan dua, karena `maaf`, `seenaknya`
  punya huruf ganda sah.
- **Normalisasi slang dilakukan per token, setelah tokenisasi** — bukan dengan
  `str.replace` di level string, karena itu akan mengubah `gak` di dalam `bagak`.
- Simpan **dua kolom hasil**: `ulasan_clean` (setelah seluruh pipeline, untuk
  model) dan `ulasan_normalized` (setelah normalisasi slang, sebelum stemming —
  untuk ditampilkan di dashboard dan untuk analisis n-gram Fase 5, karena teks
  ter-*stem* sulit dibaca manusia).

### T-2.4 — Cache stemming per kata unik ⚡

Ini bukan optimasi opsional. Tanpa cache, Sastrawi pada 100k dokumen memakan
>10 menit; dengan cache, turun ke <30 detik.

```python
from functools import lru_cache
from Sastrawi.Stemmer.StemmerFactory import StemmerFactory

_stemmer = StemmerFactory().create_stemmer()

@lru_cache(maxsize=None)
def stem_word(word: str) -> str:
    return _stemmer.stem(word)

def stem_tokens(tokens: list[str]) -> list[str]:
    return [stem_word(t) for t in tokens]
```

Alasannya: korpus 100k dokumen hanya punya ±40–60 ribu kata unik, sementara
total token mencapai jutaan. Cache mengubah jutaan pemanggilan menjadi puluhan ribu.

Tambahan: simpan hasil cache ke `data/processed/stem_cache.json` agar
menjalankan ulang pipeline tidak perlu menghitung dari nol.

### T-2.5 — Kolom turunan & pelabelan

```python
df["word_count"] = df["ulasan_normalized"].str.split().str.len()

def label_sentiment(rating: int, cfg) -> int | None:
    if rating in cfg["labeling"]["negative_ratings"]: return 0
    if rating in cfg["labeling"]["positive_ratings"]: return 1
    return None   # rating 3 -> netral, NULL pada skema biner

df["sentimen_aktual"] = df["Rating"].map(lambda r: label_sentiment(r, cfg))
df["versi_minor"] = derive_versi_minor(df["Versi App"])
```

Catatan: `word_count` dihitung dari `ulasan_normalized`, **bukan** dari
`ulasan_clean`. Alasannya: setelah *stopword removal* dan *stemming*, ulasan
7 kata bisa menyusut jadi 3 kata, sehingga ambang `>=5` untuk set
`informative_ge5w` tidak lagi mengukur apa yang dimaksud. Definisi ini harus
konsisten dengan yang dipakai di Fase 3 dan Fase 6.

### T-2.6 — Simpan hasil

```python
df.to_parquet(resolve(cfg, "paths.clean_parquet"), index=False)
```

Kolom yang wajib ada di parquet:

| Kolom | Tipe | Keterangan |
|-------|------|------------|
| `id` | int64 | index 1..100000, jadi PK di DB |
| `nama_user` | string | apa adanya |
| `ulasan` | string | teks asli, tidak diubah |
| `ulasan_normalized` | string | setelah slang, sebelum stemming |
| `ulasan_clean` | string | hasil pipeline penuh |
| `rating` | int8 | 1–5 |
| `tanggal` | datetime64 | UTC-aware |
| `likes` | int32 | |
| `versi_app` | string | NULL dipertahankan |
| `versi_minor` | string | turunan |
| `word_count` | int16 | dari `ulasan_normalized` |
| `sentimen_aktual` | Int8 (nullable) | 0/1/NULL |

### T-2.7 — Verifikasi manual 100 sampel · ⛔ GERBANG BERHENTI H-6

```python
sample = df.sample(100, random_state=cfg["seed"])[
    ["ulasan", "ulasan_normalized", "ulasan_clean", "rating", "word_count"]
]
sample.to_csv("docs/tables/preprocessing_sample_100.csv", index=False)
```

Periksa manual, khusus cari:

1. Teks bermakna yang menjadi **kosong** setelah preprocessing → bug, perbaiki.
2. Negasi yang hilang (`tidak bisa bayar` → `bayar`) → stopword salah, perbaiki.
3. Slang frekuen yang belum tertangani → tambah ke `SLANG_DICT`.
4. Stemming *over-aggressive* (`aplikasi` → `aplik`) → catat, bila terlalu banyak
   pertimbangkan stemming opsional via flag config.

> ### ⛔ BERHENTI DI SINI — H-6
>
> Agent menyerahkan `preprocessing_sample_100.csv` dan **menunggu lampu hijau**
> sebelum menulis `reviews_clean.parquet` sebagai keluaran final Fase 2.
>
> Pesan penyerahan memuat: path berkas, empat hal yang perlu diperiksa manusia
> (daftar di atas), dan estimasi ±45 menit.
>
> **Dilarang:** melewati gerbang karena sampel "terlihat baik"; agent tidak
> punya dasar untuk menilai apakah teks Indonesia informal yang hilang itu
> bermakna atau tidak. Bila manusia melaporkan temuan, perbaiki lalu **serahkan
> sampel baru** — jangan anggap selesai setelah satu putaran.

Setelah lampu hijau: catat hasil pemeriksaan di
`docs/preprocessing_validation.md` dengan jumlah temuan per kategori dan
tindakan yang diambil, lalu tulis parquet final.

---

## 3. Deliverables / Output

| Artefak | Lokasi | Keterangan |
|---------|--------|------------|
| `slang_dict.py` | `ml/src/` | 300–500 entri hasil pemetaan manual |
| `slang_dict.csv` | `docs/tables/` | Versi lampiran laporan (+ frekuensi) |
| `stopwords.py` | `ml/src/` | Daftar Sastrawi minus kata negasi |
| `preprocess.py` | `ml/src/` | Pipeline lengkap + cache stemming |
| `reviews_clean.parquet` | `data/processed/` | 100.000 baris × 12 kolom |
| `stem_cache.json` | `data/processed/` | Cache kata unik → kata dasar |
| `preprocessing_sample_100.csv` | `docs/tables/` | Sampel before/after |
| `preprocessing_validation.md` | `docs/` | Catatan hasil pemeriksaan manual |

---

## 4. Definition of Done

- [ ] `python -m ml.src.preprocess` selesai **< 5 menit** untuk 100.000 baris.
- [ ] `reviews_clean.parquet` berisi tepat 100.000 baris dan 12 kolom sesuai tabel T-2.6.
- [ ] `df["ulasan_clean"].str.strip().eq("").sum()` — jumlah teks kosong tercatat; **semua** yang kosong berasal dari ulasan yang memang hanya berisi emoji/angka/tanda baca (diverifikasi manual), bukan dari ulasan bermakna.
- [ ] Pemeriksaan manual 100 sampel selesai; nol kasus "teks bermakna → kosong" yang belum diperbaiki.
- [ ] Kata negasi (`tidak`, `bukan`, `jangan`, `belum`) **masih ada** di `ulasan_clean` — verifikasi: `df["ulasan_clean"].str.contains(r"\btidak\b").sum() > 0`.
- [ ] `SLANG_DICT` berisi ≥300 entri, dan ≥20 di antaranya adalah varian negasi.
- [ ] Distribusi label: `sentimen_aktual==0` → 26.732; `==1` → 69.734; NULL → 3.534.
- [ ] `word_count` konsisten dengan EDA Fase 1 (jumlah baris `word_count<=2` ≈ 39.859 pada teks normalized).
- [ ] Pipeline deterministik: jalankan dua kali, hash parquet identik.
- [ ] **Gerbang H-5 dilewati dengan benar:** `unknown_tokens_500.csv` diserahkan, dikembalikan terisi manusia, dan `SLANG_DICT` dibangun dari berkas itu — bukan dari tebakan agent.
- [ ] **Gerbang H-6 dilewati dengan benar:** lampu hijau manusia diterima sebelum parquet final ditulis.
- [ ] Commit ditag `phase-2-done`.

---

## 5. Risiko & Catatan

| Risiko | Dampak | Mitigasi |
|--------|--------|----------|
| Stopword Sastrawi menghapus `tidak` | **Kritis** — model buta terhadap negasi | Daftar kustom T-2.2 + assert di DoD |
| Stemming Sastrawi lambat | Sedang | Cache `lru_cache` per kata unik (T-2.4) |
| Stemming merusak istilah domain (`gopay`→`gopay`? `gofood`?) | Sedang | Tambahkan *whitelist* kata yang dilewati stemmer |
| Kamus slang tidak lengkap | Sedang | Iterasi: setelah Fase 3, periksa fitur berbobot tinggi (2.4 dokumen induk); token aneh di sana menandakan kamus perlu ditambah |
| `word_count` dihitung dari kolom yang salah | Sedang | Sudah ditetapkan: dari `ulasan_normalized`. Konsisten di Fase 3 & 6 |

**Catatan deduplikasi:** `dedup_training_text: true` di config **tidak**
diterapkan di fase ini. Parquet menyimpan seluruh 100.000 baris apa adanya —
deduplikasi dilakukan di Fase 3, hanya pada *training set*, setelah *split*.
Statistik deskriptif dan dashboard tetap memakai data penuh.
