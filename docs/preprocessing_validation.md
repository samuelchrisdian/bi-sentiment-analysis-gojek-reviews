# VALIDASI PREPROCESSING — FASE 2

Seluruh angka di bawah berasal dari kode yang dijalankan atas 526.322 ulasan
hasil scraping Google Play (1 Oktober 2021 – 30 September 2026), dan diukur
ulang secara read-only dari `data/processed/reviews_clean.parquet` versi final
(setelah perbaikan hasil verifikasi putaran 1–3).
<!-- src: facts.yaml preprocessing; data/processed/reviews_clean.parquet -->

## 1. Hasil Pipeline

| Properti | Nilai |
|----------|-------|
| Baris keluaran | 526.322 (12 kolom) |
| `data/processed/reviews_clean.parquet` | 69,1 MB |
| Label: negatif / positif / netral | 145.924 / 358.284 / 22.114 |
| `word_count <= 2` | 210.592 |
| `word_count >= 5` | 242.541 |
| Teks kosong setelah pra-pemrosesan | 1.321 (0,25%) |

`word_count` dihitung dari `ulasan_normalized` (setelah normalisasi slang,
sebelum penghapusan *stopword*), sehingga angkanya sedikit berbeda dari
hitungan kata pada teks mentah di `facts.yaml` `asimetri_panjang`
(213.697 ulasan ≤2 kata; 240.609 ulasan ≥5 kata).

Ulasan yang dominan berbahasa Inggris (14.671 ulasan, 2,8%) sudah diterjemahkan
ke bahasa Indonesia **sebelum** tahap ini (`ml/src/translate.py`), sehingga
kolom `ulasan` untuk baris tersebut berisi teks terjemahan.

## 2. Pemeriksaan Kritis: Negasi Bertahan

Tujuan daftar stopword kustom (`NEGATION_KEEP`, 24 kata) adalah memastikan kata
pembawa negasi tidak ikut terbuang. Terverifikasi dengan membandingkan
`ulasan_normalized` (sebelum stopword & stemming) dengan `ulasan_clean`:

| Kata / frasa | Dokumen di `ulasan_normalized` | Dokumen di `ulasan_clean` |
|--------------|-------------------------------|---------------------------|
| `tidak` | 106.678 | **106.708** |
| `tidak bisa` | 33.736 | **33.766** |
| `tidak ada` | 20.899 | **20.963** |
| `tidak dapat` | 5.615 | 5.967 |
| `belum` | 7.910 | 7.911 |
| `jangan` | 7.858 | **7.898** |
| `bukan` | 4.041 | 4.925 |

<!-- src: facts.yaml preprocessing.dok_tidak, dok_tidak_bisa, dok_tidak_ada, dok_jangan; sisanya diukur read-only dari reviews_clean.parquet -->

Tidak ada dokumen yang kehilangan negasinya. Jumlah di `ulasan_clean` justru
sedikit lebih besar karena dua hal yang dapat dijelaskan: penghapusan
*stopword* di antara dua kata membuat keduanya bersebelahan (misalnya
"tidak juga bisa" menjadi "tidak bisa"), dan stemming mengembalikan bentuk
berimbuhan ke kata dasarnya (misalnya `bukannya` → `bukan`, `dapatkan` →
`dapat`).

Tanpa penyesuaian ini, "tidak bagus" akan menjadi "bagus" — kebalikan maknanya,
tepat pada kelas yang menjadi fokus penelitian.

## 3. Teks yang Menjadi Kosong — 1.321 (0,25%)

Seluruhnya dapat dijelaskan; tidak ada yang merupakan kegagalan pipeline:

| Sebab | Jumlah | Contoh |
|-------|--------|--------|
| Hanya emoji, angka, atau tanda baca (sudah kosong di `ulasan_normalized`) | 1.143 | `🙏`, `🗿`, `🤗`, `💪` |
| Hanya stopword | 178 | `ya`, `oh`, `ya begitu`, `ini`, `sudah` |

Ulasan yang hanya berisi emoji selalu tergolong ulasan pendek, sehingga emoji
yang dikenal sudah dipetakan menjadi kata (lihat §5); yang menjadi kosong
adalah emoji di luar peta emoji (49 emoji), seperti 🙏 dan 🗿 yang maknanya
tidak tegas positif atau negatif. Baris tetap disimpan di parquet (tidak
dibuang) agar statistik deskriptif dan dashboard memakai data penuh; TF-IDF
mengabaikannya secara alami.

## 4. Catatan Kinerja

Stemming Sastrawi adalah tahap yang mahal, terutama untuk kata di luar kamus
dasar: Sastrawi menjalankan seluruh kaskade aturan afiks sebelum menyerah.
Mitigasi yang diterapkan di `ml/src/preprocess.py`:

1. **Cache per kata unik**, bukan per dokumen (`data/processed/stem_cache.json`,
   77.356 entri).
2. **Melewati kata yang sudah bentuk dasar** (ada di kamus dasar Sastrawi).
3. **Paralelisasi** ke `cpu_count − 2` proses.
4. **Penulisan cache berkala** tiap 2.000 kata, sehingga run yang terputus
   tidak kehilangan progres.
5. **`STEM_OVERRIDE` diterapkan tanpa memandang cache**, sehingga entri cache
   lama yang terlanjur salah ikut ditimpa saat pengecualian baru ditambahkan.

Waktu tempuh tidak dicantumkan karena tidak tercatat pada run final dan
bergantung pada mesin; hasil stemming identik antara versi satu-core dan
paralel, yang berubah hanya waktu tempuhnya.

## 5. Verifikasi Manual — Empat Putaran

Hasil pra-pemrosesan diverifikasi manual atas sampel sebelum/sesudah 100 ulasan
per putaran (`random_state=42`, putaran berikutnya mengecualikan ulasan yang
sudah diperiksa). Setiap putaran yang menemukan masalah sistemik diikuti
perbaikan pipeline lalu sampel baru; verifikasi berhenti ketika satu putaran
tidak lagi menemukan masalah sistemik yang mengubah makna. Total 400 sampel.
Di kode dan nama berkas lama tahap ini masih disebut "gerbang H-6".
<!-- src: docs/tables/preprocessing_sample_{100,ronde2,ronde3,ronde4}_reviewed.csv; git de271ff, 898b903 -->

| Putaran | Sampel (bercatatan) | Masalah sistemik ditemukan | Dampak terukur di korpus | Perbaikan |
|---------|---------------------|----------------------------|--------------------------|-----------|
| 1 | 100 (66) | "top up" menjadi "bagus up" karena `top` → `bagus` dipetakan per token · kata ulang berangka rusak (`mati2an` → "mati sekitar") · bentuk berhubung tergandakan ("gara-gara gara-gara") · emoji identik berurutan diekspansi berulang (🔥🔥🔥 → "keren keren keren") · nama program `goceng` diganti "lima ribu" | 4.102 ulasan memuat "top up"; 24.853 ulasan memuat kata ulang berangka; 635 ulasan memuat "gara gara"; 5.976 ulasan ≤3 kata memuat emoji identik berulang; 172 ulasan memuat `goceng` | Aturan frasa `top up` → `topup`; aturan kata ulang berangka (`mati2an` → "mati matian"); token lanjutan bentuk berhubung dilewati; emoji identik berurutan dihitung sekali; `goceng` dipertahankan |
| 2 | 100 (34) | Entri kamus berakhiran huruf ganda tidak pernah berlaku karena huruf gandanya diringkas lebih dulu (`gpp` → `gp`, juga `fee`, `sll`, `full`, `call`, `acc`, `shopee`) · stemming mengubah makna (`sejauh` → `jauh`, `penerima` → `terima`, `setuju` → `tuju`, `tertarik`/`menarik` → `tarik`) · varian negasi belum dibakukan (`gda`, `gbsa`, `gakan`, …) | 2.942 ulasan memuat token kamus berakhiran huruf ganda; 3.168 ulasan memuat kelima kata yang salah di-stem (`sejauh` saja 1.967); 882 ulasan memuat 10 varian negasi | Peringkasan huruf ganda dikecualikan untuk entri kamus slang; 5 pengecualian stemming; 10 varian negasi masuk kamus (`gda` → "tidak ada", `gbsa` → "tidak bisa", `gakan` → "tidak akan", `enggak` → "tidak", dst.) |
| 3 | 100 (39) | Akronim berhuruf ganda ikut diringkas ("go bill" → "go bil", `SS` → `s`, `PBB` → `pb` yang sudah tercatat di putaran 2) · `setujui` (termasuk hasil kamus `acc` → `setujui`) di-stem menjadi `tuju`, akar yang sama dengan `tujuan` | 221 ulasan memuat `bill`/`ss`/`pbb`/`cc`; 438 ulasan memuat `setujui` setelah normalisasi | Daftar pengecualian peringkasan (`bill`, `ss`, `pbb`, `cc`); `setujui` → `disetujui` di `STEM_OVERRIDE` |
| 4 | 100 (39) | **Tidak ada** masalah sistemik yang mengubah makna. Dua temuan dicatat sebagai keterbatasan: `address` → `addres` (peringkasan huruf ganda pada kata Inggris) dan `pengemudimu` → `mud` | `addres` 40 ulasan (pemetaan konsisten); token `mud` 47 ulasan, 15 di antaranya dari `pengemudimu` | Tidak diperbaiki (lihat §6) |

Dampak terukur dihitung ulang secara read-only: kolom `ulasan` (teks mentah,
huruf kecil) untuk pola teks, dan `ulasan_normalized` untuk kata yang menjadi
masukan stemming. Angka ini dapat sedikit berbeda dari angka di komentar kode,
yang diukur pada saat perbaikan dibuat.

Pola konvergensinya jelas: putaran 1–3 masing-masing menemukan cacat yang
mengubah makna pada ratusan hingga ribuan dokumen, dan setiap perbaikan
memunculkan lapisan berikutnya (misalnya pengecualian huruf ganda di putaran 2
baru menyingkap akronim di putaran 3). Putaran 4 hanya menemukan typo satuan,
angka yang hilang (keterbatasan yang sudah disepakati), dan dua kasus
berfrekuensi rendah.

Sebagian besar catatan pemeriksa di keempat putaran **bukan** masalah sistemik:
angka yang hilang, typo satuan, campur bahasa yang diterjemahkan sebagian,
dan ketidaksesuaian rating dengan isi teks yang berasal dari sumbernya.

### Bukti perbaikan bekerja

- `ulasan_clean` kini memuat `top up` di 4.107 dokumen; `bagus up` tersisa di
  9 dokumen, seluruhnya varian ejaan yang tidak tertangkap aturan frasa
  (`top.up`, `top up2`, `top upp`).
- `sejauh` kini muncul sebagai salah satu dari 20 fitur positif berbobot
  tertinggi model produksi (`docs/tables/top_features.csv`) — frasa
  "sejauh ini bagus" tidak lagi terbaca sebagai keluhan jarak.
- Tidak satu pun dari 20 fitur teratas per kelas memuat artefak yang dikenal
  (`bagus up`, `mud`, `addres`, `kemudi`, `langgan`).

### Rekapitulasi aturan akhir

| Aspek | Akhir | Sumber |
|-------|-------|--------|
| `SLANG_DICT` | 639 entri (56 multi-kata) | `ml/src/slang_dict.py` |
| `NOISE_TOKENS` | 9 token dibuang | `ml/src/slang_dict.py` |
| `STEM_OVERRIDE` | 55 pengecualian | `ml/src/stem_override.py` |
| `NEGATION_KEEP` | 24 kata | `ml/src/stopwords.py` |
| Normalisasi frasa (`FRASA`) | 16 pola | `ml/src/preprocess.py` |
| Pengecualian peringkasan huruf ganda | entri kamus slang + 4 akronim (`bill`, `ss`, `pbb`, `cc`) | `ml/src/preprocess.py` |
| Pemetaan emoji | 49 emoji, hanya pada ulasan ≤3 kata; emoji identik berurutan dihitung sekali | `ml/src/emoji_map.py`, `ml/src/preprocess.py` |
| Teks kosong | 1.321 (0,25%) | `facts.yaml` `preprocessing` |

### Kamus slang

Kamus disusun dari 500 token tak dikenal berfrekuensi tertinggi yang bentuk
bakunya diputuskan peneliti baris per baris, lalu dipakai ulang pada data
scraping setelah cakupannya diukur (440 dari 500 token tak dikenal teratas
data baru sudah tercakup). Sisa 60 token — sebagian besar kata serapan bahasa
Inggris seperti `cashback`, `crash`, `link` — diputuskan peneliti: 57 dipetakan
dan 3 dibuang (`ng`, `was`, `gg`). Berkas yang sama memuat 10 varian negasi
dari putaran 2 dan koreksi `goceng` dari putaran 1; empat pemetaan lain
dikoreksi atas persetujuan penulis (`fix` → "perbaiki", `ia` → "dia",
`my` → "saya", `was` dibuang karena "was was" sudah ditangani aturan frasa).
<!-- src: docs/tables/unknown_tokens_baru_scraping_reviewed.csv; docs/synthesis/bab-3-pembaruan-data-scraping.md B.16(3) -->

## 6. Residu yang Diketahui dan Alasan Tidak Dikejar Lebih Jauh

Putaran 4 menyisakan typo satuan yang tidak dipetakan. Keputusan untuk
menghentikan iterasi didasarkan pada bukti, bukan kelelahan:

**71,6% token unik (44.035 dari 61.543) memiliki document frequency di bawah 3**,
sehingga `TfidfVectorizer(min_df=3)` membuangnya sebelum model melihatnya.
Typo yang dicatat pemeriksa putaran 2–4 sebagian besar memang tidak akan
mencapai model: `sejaihnya`, `tlpun`, `plyastor`, `dersember`, `guej` (df=1),
`goreed` (df=3, tepat di ambang), `kern` (df=4).

Yang masih lolos ke model dan layak dipertimbangkan bila kamus diperluas:
`tranfer` (df=260), `ntap` (df=174), `trmksh` (df=141), `jngan` (df=137),
`sangan` (df=121), `bls` (df=80), `oky` (df=74), `nais` (df=47),
`driverx` (df=44), `jagan` (df=31). `jngan` dan `jagan` adalah varian
`jangan` — negasi yang lolos dari pembakuan.

Keterbatasan struktural yang tidak diselesaikan dan dinyatakan apa adanya:

1. **Angka dibuang secara global.** Aturan sempit ditambahkan untuk
   `bintang 1..5`, `tiba2`, dan kata ulang berangka, tetapi nominal harga,
   durasi, jarak, dan kuantitas lain tetap hilang. Ini catatan pemeriksa
   paling sering di keempat putaran. Mengaktifkan angka secara global akan
   memasukkan ribuan nominal sebagai fitur.
2. **Sebagian kata fungsi ikut terbuang sebagai stopword**, terutama "masih"
   dan "hanya". Contoh dari putaran 3: "tidak hanya SMS" menjadi "tidak SMS".
3. **Stemming berfrekuensi rendah yang menggeser makna** (`menurutku` →
   `turut`, `mengetik` → `etik`, `perasaan` → `asa`). Satu kasus berfrekuensi
   tinggi yang tidak tertangkap verifikasi: **`pesen` (ragam informal
   "pesan") belum ada di kamus slang sehingga di-stem menjadi `sen`**, termasuk
   `pesenan`, `dipesen`, dan seterusnya; token `sen` muncul di 8.331 dokumen.
   Pemetaannya konsisten, sehingga bagi model `sen` tetap satu fitur yang
   bermakna "pesan", tetapi token ini muncul sebagai kata kunci kategori
   topik (lihat `docs/topic_extraction_findings.md`).
4. **Kata Inggris berakhiran huruf ganda ikut diringkas** (`address` →
   `addres`, 40 ulasan). Pemetaannya konsisten sehingga tidak merusak fitur.
5. **Campur bahasa diterjemahkan sebagian** pada ulasan yang tidak lolos
   ambang deteksi bahasa Inggris ("very bad" → "sangat bad", "the best" →
   "the terbaik"), karena kamus slang bekerja per token.
6. **Umpatan tersamar** hanya ditangani untuk satu pola (`b#ngasd`).

**Umpan balik dari tahap pemodelan:** 20 fitur berbobot tertinggi per kelas
(`docs/tables/top_features.csv`) diperiksa dengan pertanyaan "apakah ini
istilah domain atau artefak pra-pemrosesan?". Bila artefak muncul di daftar
itu, iterasi kembali ke tahap ini dengan bukti kuantitatif, bukan dugaan.
Pada data final tidak ada artefak yang dikenal di daftar tersebut (§5).

## 7. Status Verifikasi

- **Kamus slang** — selesai. 500 token awal dan 60 token baru data scraping
  diputuskan manusia, ditambah 10 varian negasi; kamus akhir 639 entri.
- **Verifikasi sampel** — selesai setelah 4 putaran, 400 sampel diperiksa;
  putaran 4 tanpa masalah sistemik yang mengubah makna.
