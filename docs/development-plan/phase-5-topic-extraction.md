# FASE 5 — Ekstraksi Topik Keluhan (RM2)

**Estimasi:** 2 hari
**Prasyarat:** Fase 2 selesai. **Tidak bergantung pada Fase 3–4** — bisa paralel.
**Output utama:** tabel `topics` + `review_topics` terisi
**⚠️ Inti Rumusan Masalah 2 — jangan dipotong**

---

## 1. Objective

Menjawab RM2: **apa saja tema keluhan dominan dalam ulasan negatif, dan
bagaimana peringkatnya?**

Fokusnya hanya pada **korpus negatif (26.732 ulasan)**. Ini pilihan yang
menguntungkan secara teknis: berbeda dari korpus positif yang 32% duplikat dan
didominasi pujian dua kata, korpus negatif relatif bersih — hanya 2% duplikat
teks dan 6% ulasan ≤2 kata (Temuan 2). Artinya LDA punya materi yang layak
untuk bekerja.

Bagian tersulit bukan algoritmanya, melainkan **pelabelan kategori** — memetakan
klaster kata yang dihasilkan LDA ke kategori bisnis yang bermakna. Itu pekerjaan
manusia, dan aturannya harus didokumentasikan agar bisa dipertanggungjawabkan.

---

## 2. Technical Tasks

### T-5.1 — Siapkan korpus negatif

```python
df = pd.read_parquet(cfg_path("clean_parquet"))
neg = df[df["sentimen_aktual"] == 0].copy()
assert len(neg) == 26732

# Buang ulasan terlalu pendek — tidak memberi sinyal topik
neg_topic = neg[neg["word_count"] >= 5].copy()
print(f"Korpus topik: {len(neg_topic):,} dari {len(neg):,} ulasan negatif")
```

Catat berapa banyak yang dibuang dan nyatakan ambangnya di keterangan setiap
grafik topik.

### T-5.2 — Analisis frekuensi unigram & bigram

Dikerjakan **sebelum** LDA. Hasilnya berfungsi ganda: sebagai temuan mandiri
yang bisa langsung dilaporkan, dan sebagai referensi saat menamai klaster LDA nanti.

```python
cv = CountVectorizer(ngram_range=(1, 2), min_df=10, token_pattern=r"\S+")
X = cv.fit_transform(neg_topic["ulasan_clean"])
freq = pd.DataFrame({
    "term": cv.get_feature_names_out(),
    "freq": np.asarray(X.sum(axis=0)).ravel(),
}).sort_values("freq", ascending=False)
```

Sajikan top-30 unigram dan top-30 bigram sebagai tabel. Bigram biasanya lebih
informatif: `gagal bayar`, `saldo hilang`, `driver batal`, `aplikasi error`,
`lokasi tidak akurat`.

Buat juga word cloud korpus negatif sebagai Gambar pelengkap — tetapi **jangan
jadikan ini bukti utama**; tabel frekuensi lebih bisa dipertanggungjawabkan.

### T-5.3 — LDA dengan pemilihan jumlah topik berbasis coherence

```python
from gensim import corpora
from gensim.models import LdaModel, CoherenceModel

texts = [t.split() for t in neg_topic["ulasan_clean"]]
dictionary = corpora.Dictionary(texts)
dictionary.filter_extremes(no_below=10, no_above=0.5)
corpus = [dictionary.doc2bow(t) for t in texts]

scores = {}
for k in range(cfg["topics"]["lda_n_topics_range"][0],
               cfg["topics"]["lda_n_topics_range"][1] + 1):
    lda = LdaModel(corpus=corpus, id2word=dictionary, num_topics=k,
                   random_state=cfg["seed"], passes=10, alpha="auto")
    cm = CoherenceModel(model=lda, texts=texts, dictionary=dictionary,
                        coherence="c_v")
    scores[k] = cm.get_coherence()
```

Plot coherence vs jumlah topik (Gambar 8), pilih puncaknya. Bila ada dua puncak
berdekatan, pilih yang jumlah topiknya lebih kecil — lebih mudah dinarasikan.

Catat `passes`, `alpha`, dan `random_state` — hasil LDA stokastik, jadi
reprodusibilitasnya bergantung pada ini.

### T-5.4 — Pelabelan kategori · ⛔ GERBANG BERHENTI H-8

**Batas wewenang di fase ini: agent melakukan klastering, manusia menamai.**

Bagian agent: untuk setiap topik LDA, hasilkan 20 kata teratas + 10 dokumen
dengan probabilitas topik tertinggi, tulis ke
`docs/tables/lda_clusters_for_labeling.csv` dengan kolom
`topic_id, top_terms, contoh_ulasan_1..10, kategori_usulan, alasan` —
dua kolom terakhir **dibiarkan kosong**.

> ### ⛔ BERHENTI DI SINI — H-8
>
> Agent menyerahkan berkas klaster dan menunggu manusia mengisi nama kategori
> bisnis beserta aturan pemetaannya.
>
> Enam kategori di `ml/config.yaml` (Pembayaran, Mitra Driver, Performa
> Aplikasi, Tarif & Promo, Layanan Pelanggan, Akurasi Lokasi) adalah
> **hipotesis awal, bukan kebenaran** — manusia berhak menambah, menggabung,
> atau mengganti berdasarkan hasil nyata.
>
> **Dilarang:** menamai kategori sendiri "sebagai contoh" atau "sementara".
> Penamaan kategori adalah interpretasi domain bisnis; label yang ditebak agent
> akan mengalir ke tabel `topics`, ke dashboard, dan ke Tabel 3 laporan —
> menjadi klaim yang tidak berdasar di tiga tempat sekaligus.

Kategori di config sebagai titik awal pertimbangan manusia:

| Kategori | Kata kunci indikatif (contoh awal — lengkapi dari hasil nyata) |
|----------|---------------------------------------------------------------|
| **Pembayaran** | gopay, saldo, bayar, potong, refund, transaksi, gagal bayar |
| **Mitra Driver** | driver, batal, lama, jemput, tidak datang, orderan |
| **Performa Aplikasi** | error, force close, lemot, loading, update, bug, crash |
| **Tarif & Promo** | mahal, tarif, promo, voucher, diskon, naik, biaya |
| **Layanan Pelanggan** | cs, komplain, respon, laporan, bantuan, tidak ditanggapi |
| **Akurasi Lokasi** | lokasi, gps, peta, alamat, titik, meleset, jauh |

Aturan yang wajib **ditetapkan manusia** dan dicatat di
`docs/topic_labeling_rules.md` (agent yang menuliskan, dari jawaban manusia):

1. Bagaimana satu topik LDA dipetakan ke kategori (kata dominan? dokumen contoh?).
2. Apa yang dilakukan bila satu topik LDA mencakup dua kategori
   (pecah? pilih yang dominan? beri label ganda?).
3. Apa yang dilakukan bila ada topik yang tidak masuk kategori mana pun
   (tambah kategori baru, atau beri label "Lainnya" — keduanya sah, asal konsisten).
4. Siapa yang melabeli dan kapan.

#### ⛔ GERBANG BERHENTI H-9 — validasi silang

Agent menyiapkan `docs/tables/cross_validation_sample_50.csv`: 50 ulasan negatif
acak (`random_state=42`), **berisi teks ulasan asli saja** — tanpa label,
tanpa kategori hasil H-8, tanpa skor topik. Sertakan lembar definisi kategori
terpisah agar penilai memahami pilihan yang tersedia.

> Agent menyerahkan berkas dan menunggu label independen dari rekan penilai.
>
> **Dilarang:** menyertakan label hasil H-8 di berkas yang sama. Penilai yang
> melihat label yang ada tidak lagi menilai secara independen, dan skor
> kesepakatan yang dihasilkan menjadi tidak bermakna.

Setelah berkas kembali, agent menghitung tingkat kesepakatan (persentase, dan
Cohen's κ bila memungkinkan) dan melaporkan angkanya apa adanya, termasuk bila
rendah. Ini mengubah pelabelan dari "subjektif" menjadi "subjektif tetapi
terukur".

### T-5.5 — Penetapan topik per ulasan → `review_topics`

Dua pendekatan, jalankan keduanya lalu bandingkan:

**A. Berbasis aturan kata kunci (utama, dapat dijelaskan):**

```python
def assign_topics_rule(text: str, keyword_map: dict) -> list[int]:
    hits = [tid for tid, kws in keyword_map.items()
            if any(kw in text for kw in kws)]
    return hits   # satu ulasan boleh punya >1 topik
```

**B. Berbasis LDA (pembanding):** ambil topik dengan probabilitas tertinggi,
dengan ambang minimum (mis. `>= 0.3`); di bawah ambang → tidak diberi topik.

Gunakan **A sebagai penetapan resmi** yang masuk ke `review_topics` — alasannya
dapat dijelaskan ke pemangku kepentingan dan dapat diaudit. Gunakan B sebagai
validasi: hitung tingkat kesesuaian antara keduanya dan laporkan.

### T-5.6 — Peringkat topik: dua kolom terpisah

```sql
-- Peringkat berdasarkan frekuensi (PRIMER — sesuai batasan Bab 1)
SELECT t.kategori, COUNT(*) AS jumlah_ulasan
FROM review_topics rt JOIN topics t ON t.id = rt.topic_id
GROUP BY t.kategori ORDER BY jumlah_ulasan DESC;

-- Peringkat berdasarkan total Likes (SEKUNDER — resonansi)
SELECT t.kategori, SUM(r.likes) AS total_likes
FROM review_topics rt
JOIN topics t  ON t.id = rt.topic_id
JOIN reviews r ON r.id = rt.review_id
GROUP BY t.kategori ORDER BY total_likes DESC;
```

**Jangan gabungkan keduanya menjadi satu skor komposit.** Bab 1 membatasi
prioritas hanya berbasis frekuensi; kolom Likes hadir sebagai lensa tambahan
("keluhan mana yang paling beresonansi"), bukan sebagai bobot prioritas.
Sajikan berdampingan, biarkan pembaca yang membandingkan. Bila peringkatnya
berbeda antara dua kolom, itu sendiri temuan menarik.

### T-5.7 — Isi tabel `topics`

Satu baris per (kategori, keyword), dengan bobot dari frekuensi relatif atau
bobot LDA:

```python
topics_rows = [
    {"kategori": "Pembayaran", "keyword": "gopay",  "bobot": 0.087},
    {"kategori": "Pembayaran", "keyword": "saldo",  "bobot": 0.074},
]
```

Minimal **5 kata kunci per kategori** (DoD). Ini yang nanti dipakai oleh
endpoint `/api/topics`.

### T-5.8 — Analisis tren topik per waktu (nilai tambah)

Biayanya satu `GROUP BY`, nilainya besar untuk dashboard dan pembahasan:

```sql
SELECT date_trunc('month', r.tanggal) AS bulan, t.kategori, COUNT(*)
FROM review_topics rt
JOIN topics t  ON t.id = rt.topic_id
JOIN reviews r ON r.id = rt.review_id
GROUP BY 1, 2 ORDER BY 1, 3 DESC;
```

Kecualikan atau beri anotasi Mei 2024 (periode parsial, Temuan 6). Kategori
yang melonjak pada bulan tertentu biasanya berkorelasi dengan rilis versi
aplikasi — hubungkan dengan analisis per-versi untuk narasi yang kuat.

---

## 3. Deliverables / Output

| Artefak | Lokasi | Keterangan |
|---------|--------|------------|
| `topics.py` | `ml/src/` | Frekuensi n-gram, LDA, coherence, penetapan topik |
| `topics.parquet` | `data/processed/` | Pemetaan `review_id → topic_id` |
| `ngram_negatif.csv` | `docs/tables/` | Top-30 unigram + top-30 bigram |
| `lda_coherence.csv` | `docs/tables/` | Coherence per jumlah topik (k=5..12) |
| `topic_labeling_rules.md` | `docs/` | Aturan pemetaan + hasil validasi silang |
| `topics_ranked.csv` | `docs/tables/` | Peringkat: frekuensi **dan** total Likes (2 kolom) |
| `topic_trend_monthly.csv` | `docs/tables/` | Tren kategori per bulan |
| Tabel `topics`, `review_topics` | PostgreSQL | Siap dikonsumsi `/api/topics` |
| Gambar 8 | `docs/figures/` | Coherence vs jumlah topik |
| Gambar 9 | `docs/figures/` | Peringkat topik keluhan (batang horizontal) |
| Tabel 3 storytelling | `docs/tables/` | Kategori, jumlah, %, contoh ulasan nyata |

---

## 4. Definition of Done

- [ ] Analisis n-gram selesai; top-30 unigram dan bigram tersaji sebagai tabel.
- [ ] LDA dijalankan untuk k = 5..12; coherence terhitung; k terpilih beserta alasannya tercatat.
- [ ] **Setiap kategori memiliki ≥5 kata kunci** di tabel `topics`.
- [ ] **Setiap kategori memiliki ≥3 contoh ulasan nyata** yang dikutip di laporan (teks asli, bukan hasil preprocessing).
- [ ] `review_topics` terisi; proporsi ulasan negatif yang mendapat ≥1 topik tercatat (bila <60%, kata kunci perlu diperluas).
- [ ] Peringkat topik tersaji dalam **dua kolom terpisah** (frekuensi & total Likes), tidak digabung jadi skor tunggal.
- [ ] `topic_labeling_rules.md` lengkap, termasuk hasil validasi silang oleh rekan (angka kesepakatan dilaporkan).
- [ ] Ambang `word_count >= 5` untuk korpus topik dinyatakan di keterangan setiap grafik topik.
- [ ] Tabel 3 dokumen storytelling siap isi.
- [ ] **Gerbang H-8 dilewati dengan benar:** nama kategori berasal dari manusia; agent hanya menghasilkan klaster dan menuliskan aturan yang didiktekan.
- [ ] **Gerbang H-9 dilewati dengan benar:** sampel yang diserahkan ke penilai tidak memuat label apa pun; skor kesepakatan dihitung dari label independen.
- [ ] Commit ditag `phase-5-done`.

---

## 5. Risiko & Catatan

| Risiko | Dampak | Mitigasi |
|--------|--------|----------|
| Pelabelan topik subjektif | Sedang | Aturan terdokumentasi + validasi silang rekan dengan angka kesepakatan |
| Topik LDA tidak dapat ditafsirkan (kata campur aduk) | Sedang | Naikkan `min_df`, buang token domain-umum (`gojek`, `aplikasi`), coba k lebih kecil |
| Cakupan penetapan topik rendah | Sedang | Perluas kata kunci dari analisis n-gram; laporkan cakupan apa adanya |
| Satu ulasan masuk banyak kategori → jumlah > total ulasan | Rendah | Wajar dan sah; nyatakan di keterangan tabel bahwa kategori tidak saling eksklusif |
| LDA tidak reprodusibel | Sedang | `random_state=42` + catat `passes` & `alpha` di dokumentasi |

**Catatan urutan kerja:** fase ini hanya bergantung pada Fase 2. Bila ada dua
orang, Fase 3–4 dan Fase 5 dapat berjalan paralel — ini memangkas ±2 hari dari
jalur kritis.
