# TEMUAN EKSTRAKSI TOPIK — FASE 5 (T-5.1 s/d T-5.3)

Seluruh angka berasal dari `ml/src/topics.py` yang dijalankan, bukan estimasi.
Berkas: `docs/tables/ngram_negatif.csv`, `docs/tables/lda_coherence.csv`,
Gambar 8 dan 8b.

> **Status:** Bagian 1–4 lengkap. Penamaan kategori bisnis menunggu
> **gerbang H-8** — lihat `docs/topic_labeling_rules.md`.

## 1. Korpus Topik

| Properti | Nilai |
|----------|-------|
| Ulasan negatif (label 0) | 26.732 |
| **Korpus topik** (`word_count` ≥ 5) | **23.232** |
| Dibuang karena terlalu pendek | 3.500 (13,09%) |
| Duplikat teks di korpus topik | 20 (0,09%) |
| Rata-rata panjang | 23,86 kata |
| Kamus setelah `filter_extremes` | 2.041 token |

**Ambang `word_count >= 5` berlaku untuk seluruh grafik dan tabel topik** dan
dinyatakan di keterangan masing-masing.

Pemilihan korpus negatif terbukti menguntungkan sebagaimana diperkirakan
(Temuan 2): duplikasi teks hanya **0,09%** di sini, berbanding 32% pada korpus
positif, dan rata-rata panjangnya 23,86 kata berbanding ±4,9 kata pada ulasan
positif. LDA memperoleh materi yang layak, bukan pengulangan pujian dua kata.

## 2. Frekuensi N-gram (T-5.2)

Dikerjakan sebelum LDA, sehingga berfungsi sebagai temuan mandiri sekaligus
rujukan manusia saat menamai klaster di H-8.
`CountVectorizer(ngram_range=(1,2), min_df=10)`.

### 2.1 Unigram teratas

| # | Term | Frekuensi | % dokumen |
|---|------|-----------|-----------|
| 1 | tidak | 22.681 | 59,0% |
| 2 | pengemudi | 14.031 | 38,0% |
| 3 | aplikasi | 7.592 | 26,2% |
| 4 | gojek | 7.342 | 23,9% |
| 5 | nya | 7.190 | 22,1% |
| 6 | ada | 7.033 | 23,8% |
| 7 | bisa | 6.694 | 22,4% |
| 8 | batal | 5.356 | 17,4% |
| 9 | dapat | 4.689 | 15,7% |
| 10 | mau | 4.549 | 16,4% |

**`tidak` muncul di 59% ulasan negatif dan `pengemudi` di 38%.** Kedua angka itu
sendiri sudah merupakan temuan: keluhan pada aplikasi ini dominan berbentuk
*ketiadaan layanan* dan berpusat pada mitra driver.

**Catatan yang harus menyertai tabel ini:** `ada`, `bisa`, `dapat`, `mau`
bertahan karena **sengaja dipertahankan** di `NEGATION_KEEP` (keputusan Fase 2
gerbang H-6 putaran 2). Membuangnya menghancurkan struktur negasi — "tidak bisa"
menyusut dari 4.834 dokumen menjadi 3. Kehadirannya di peringkat atas adalah
konsekuensi yang diketahui dan diterima, bukan kebocoran stopword.

Konsekuensinya, **unigram kurang informatif untuk penamaan topik** dan bigram
harus menjadi rujukan utama.

### 2.2 Bigram teratas — jauh lebih informatif

| # | Term | Frekuensi | % dokumen |
|---|------|-----------|-----------|
| 1 | tidak bisa | 4.292 | 15,7% |
| 2 | tidak ada | 3.496 | 13,1% |
| 3 | **dapat pengemudi** | 2.415 | 8,8% |
| 4 | tidak jelas | 1.345 | 5,4% |
| 5 | **ongkos kirim** | 1.141 | 3,8% |
| 6 | pengemudi nya | 1.099 | 4,2% |
| 7 | **layan pelanggan** | 1.098 | 4,0% |
| 8 | tidak dapat | 1.078 | 4,3% |
| 9 | **pengemudi tidak** | 1.054 | 4,3% |
| 10 | **cari pengemudi** | 1.005 | 4,1% |
| 11 | **bisa batal** | 920 | 3,6% |
| 12 | tidak mau | 904 | 3,5% |
| 13 | tiba tiba | 852 | 3,4% |
| 14 | **tunggu jam** | 778 | 3,1% |
| 15 | **tunggu lama** | 712 | 2,8% |

Bigram bertanda tebal membawa isi keluhan yang dapat dipetakan ke kategori
bisnis; unigram tidak. Ini mengonfirmasi perkiraan rencana Fase 5 bahwa bigram
lebih informatif, dan menjadi alasan `ngram_range=(1,2)` dipertahankan.

Tiga kelompok terbaca langsung dari bigram saja, **sebelum** LDA dijalankan:
ketersediaan pengemudi (`dapat pengemudi`, `cari pengemudi`, `tunggu jam`,
`tunggu lama`), biaya (`ongkos kirim`), dan kanal bantuan (`layan pelanggan`).

## 3. LDA — Pemilihan Jumlah Topik (T-5.3)

Parameter dicatat lengkap karena LDA stokastik dan reprodusibilitasnya
bergantung sepenuhnya pada ketiganya:

| Parameter | Nilai |
|-----------|-------|
| `random_state` | 42 |
| `passes` | 10 |
| `iterations` | 100 |
| `alpha` | `"auto"` |
| `filter_extremes` | `no_below=10, no_above=0.5` |

### 3.1 Coherence per jumlah topik

| k | c_v | u_mass |
|---|-----|--------|
| 5 | 0,5566 | −2,2511 |
| 6 | 0,5583 | −2,2916 |
| 7 | 0,5648 | −2,5371 |
| 8 | 0,5469 | −2,4602 |
| **9** | **0,5763** | −2,4469 |
| 10 | 0,5293 | −2,5737 |
| 11 | 0,5378 | −2,6103 |
| 12 | 0,5449 | −2,6155 |

**k = 9 terpilih** — puncak c_v yang jelas (0,5763), unggul 1,15 poin dari
kandidat terdekat (k=7, 0,5648). Aturan "bila ada dua puncak berdekatan pilih
yang lebih kecil" tidak terpicu: tidak ada k lebih kecil yang berada dalam 0,005
dari puncak. Gambar 8.

Kurvanya tidak monoton dan berfluktuasi (k=8 turun, k=9 melonjak, k=10 turun
tajam). Ini lazim pada c_v dan berarti **k=9 sebaiknya tidak dibaca sebagai
"jumlah topik yang benar"**, melainkan sebagai jumlah yang memberi klaster
paling koheren dalam rentang yang diuji. Rentangnya sendiri (5–12) adalah
batasan yang ditetapkan `config.yaml`, bukan hasil pencarian tak terbatas.

### 3.2 Sembilan klaster — ukuran dan kata kunci

Kategori bisnis **belum dinamai** (gerbang H-8). Yang disajikan di sini murni
keluaran algoritma:

| Topik | % dokumen dominan | n | 10 kata teratas |
|-------|-------------------|---|-----------------|
| 2 | **28,85%** | 6.702 | pengemudi, batal, pesan, lama, tunggu, jam, makan, bisa, dapat, gofood |
| 0 | 16,46% | 3.823 | pengemudi, dapat, mau, jauh, order, banyak, susah, kalau, ambil, nya |
| 4 | 12,03% | 2.794 | makin, kirim, mahal, ongkos, promo, gojek, harga, nya, iklan, ribu |
| 7 | 10,18% | 2.364 | bayar, gopay, ada, gojek, pakai, hari, bisa, pinjam, blokir, padahal |
| 5 | 8,88% | 2.063 | aplikasi, tiba, bisa, ada, padahal, terus, mau, bagus, jelas, buka |
| 6 | 6,87% | 1.596 | pengemudi, gojek, nya, jalan, titik, sesuai, jadi, sama, alamat, gocar |
| 8 | 6,70% | 1.557 | bisa, mau, pakai, akun, gojek, aja, aplikasi, nomor, masuk, terus |
| 1 | 5,99% | 1.391 | pelanggan, layan, aplikasi, ada, gojek, kasih, sangat, buruk, nya, bintang |
| 3 | 4,05% | 942 | gopay, saldo, masuk, up, uang, potong, ada, kembali, isi, transfer |

Distribusinya timpang: topik 2 sendiri menguasai 28,85% dokumen, sementara
topik 3 hanya 4,05%. Rasio terbesar-terkecil 7,1×.

## 4. Catatan Metodologis untuk Pembaca Berkas H-8

**Contoh berprobabilitas tertinggi bias ke dokumen degenerate.** Ulasan pendek
berisi pengulangan satu kata memperoleh probabilitas topik hampir 1 karena
seluruh isinya satu topik. Contoh nyata: ulasan berisi `👎` berulang, yang
dipetakan Fase 2 menjadi `jelek jelek jelek ...` dan menempati peringkat teratas
topik 1.

Ulasan semacam itu hanya **42 dari 23.232 (0,18%)** — jadi bukan cacat korpus,
tetapi cukup untuk menyesatkan bila klaster dinilai hanya dari peringkat
teratas. Pangsanya per topik: tertinggi di topik 1 (0,65%), terendah di topik 8
(0,06%).

Karena itu `lda_clusters_for_labeling.csv` memuat **dua jenis contoh**:

- `contoh_prob_1..5` — probabilitas topik tertinggi (sesuai rencana)
- `contoh_tipikal_1..5` — **acak** dari dokumen yang topik ini dominan dan
  panjangnya 10–60 kata, yaitu yang benar-benar mewakili klaster

Gunakan kolom `contoh_tipikal_*` sebagai dasar penilaian utama.

## 5. Catatan Perkakas

Rencana menyebut *word cloud* sebagai gambar pelengkap dengan catatan eksplisit
"jangan jadikan ini bukti utama; tabel frekuensi lebih bisa
dipertanggungjawabkan". Pustaka `wordcloud` tidak termasuk dependensi yang
dikunci di Fase 0, dan tidak dipasang hanya untuk gambar pelengkap.

Gantinya Gambar 8b: batang berurut untuk 20 unigram dan 20 bigram teratas.
Panjang batang dapat dibaca sebagai angka, sedangkan ukuran huruf pada word
cloud tidak — sehingga substansi yang diminta tetap terpenuhi, bahkan lebih
dapat dipertanggungjawabkan. Bila *word cloud* tetap dikehendaki untuk laporan,
pemasangan `wordcloud` adalah perubahan satu baris di `requirements.txt` dan
merupakan keputusan pemilik proyek.

---

# BAGIAN II — PENETAPAN TOPIK & PERINGKAT (T-5.5 s/d T-5.8)

Sumber: `ml/src/topic_assign.py`. Kategori berasal dari gerbang H-8 — lihat
`docs/topic_labeling_rules.md` untuk pemetaan, aturan pelabelan, dan pelabelnya.

## 6. Pemilihan Kata Kunci per Kategori

Kata kunci tidak diketik manual. Ia diturunkan dari model dengan tiga saringan
berurutan, sehingga dapat direproduksi dan diaudit.

**(a) Relevance** (Sievert & Shirley, 2014 — ukuran yang sama dipakai pyLDAvis),
λ = 0,6:

> relevance(w,t) = λ·log p(w|t) + (1−λ)·log( p(w|t) / p(w) )

Suku kedua menghukum kata yang sering di seluruh korpus. Tanpa itu setiap
kategori memperoleh kata kunci `gojek`, `aplikasi`, `nya`, `ada` — benar secara
probabilitas, tidak membedakan apa pun.

**(b) `MAX_DF_KORPUS = 0,15`.** Kata yang muncul di >15% korpus negatif dibuang.
Tanpa ini `bisa` (22% dokumen) menjadi kata kunci "Akun, Login & Verifikasi"
dan mencocoki seperlima korpus.

**(c) `MIN_LIFT = 2,0`.** Kata harus ≥2× lebih terkonsentrasi pada dokumen
dominan topiknya dibanding pangsa topik itu. Ambang **rasio**, bukan mutlak,
karena ambang mutlak berat sebelah terhadap topik besar — topik 2 sendiri
menguasai 28,85% dokumen.

Bigram ditetapkan dengan prinsip yang sama: sebuah bigram masuk kategori tempat
≥35% kemunculannya terkonsentrasi. Dibatasi 15 teratas per kategori — tanpa
batas itu topik terbesar menarik 63 bigram sementara dua topik lain tidak
memperoleh satu pun.

**Hasil: 146 kata kunci (89 unigram + 57 bigram), 10–25 per kategori.**
DoD menuntut ≥5 per kategori — terpenuhi seluruhnya.
Berkas: `docs/tables/topic_keywords.csv` (memuat kolom `lift` dan `df_korpus`,
sehingga kata kunci lemah terlihat, bukan tersembunyi).

### 6.1 Satu tabrakan, diselesaikan berbasis data

`gopay` muncul sebagai kata khas pada **dua** kategori pembayaran sekaligus
("Transaksi & Saldo GoPay" lift 5,74; "GoPayLater, GoPinjam & Penagihan" lift
4,08). Membiarkannya membuat setiap ulasan bergopay masuk keduanya dan
peringkat frekuensi menghitung ganda.

Diselesaikan dengan aturan yang sudah dipakai menyaring — **lift tertinggi
menang** — bukan penilaian baru. `gopay` menjadi milik "Transaksi & Saldo
GoPay". Tabrakan ini satu-satunya dari 146 kata kunci.

## 7. Penetapan Topik per Ulasan (T-5.5)

### 7.1 Pendekatan A — berbasis kata kunci (RESMI)

Dijalankan pada **seluruh 26.732 ulasan negatif**, bukan hanya korpus LDA:
pencocokan kata kunci tidak menuntut panjang minimum, dan DoD meminta proporsi
ulasan negatif yang memperoleh ≥1 topik.

Pencocokan unigram dilakukan pada level **token**, bukan substring. Ini penting:
`bayar` sebagai substring juga cocok dengan `pembayaran` dan `membayarkan`,
yang membuat cakupan tampak lebih tinggi daripada sebenarnya.

| Metrik | Nilai |
|--------|-------|
| Ulasan dengan ≥1 kategori | **23.422 / 26.732 = 87,62%** (DoD: ≥60%) |
| Tanpa kategori | 3.310 (12,38%) |
| Rata-rata kategori per ulasan | 2,26 |
| Baris `review_topics` | 52.998 |

**Kategori tidak saling eksklusif.** Satu ulasan boleh masuk lebih dari satu
kategori — diizinkan eksplisit oleh T-5.5, dan wajar karena satu keluhan sering
menyinggung beberapa hal sekaligus. Konsekuensinya jumlah seluruh kategori
(52.998) melebihi jumlah ulasan (26.732), dan itu **bukan kesalahan
penghitungan**. Keterangan ini wajib menyertai setiap tabel peringkat.

### 7.2 Pendekatan B — berbasis LDA (pembanding)

Topik dominan dengan ambang probabilitas ≥ 0,3; di bawah ambang tidak diberi
topik. Hanya terdefinisi pada korpus LDA (23.232 ulasan).

| Metrik | Nilai |
|--------|-------|
| Memperoleh topik (prob ≥ 0,3) | 21.783 / 23.232 = 93,76% |
| **Kesesuaian dengan A** | **79,02%** |

Empat dari lima ulasan memperoleh kategori yang sama dari dua metode yang
sepenuhnya berbeda — satu berbasis kata kunci eksplisit, satu berbasis model
probabilistik. Kesesuaian sebesar itu **bukan bukti kebenaran kategori**, tetapi
bukti bahwa kata kunci yang dipilih benar-benar mewakili klaster yang
dihasilkan LDA, bukan daftar kata yang kebetulan terdengar masuk akal.

A dipakai sebagai penetapan resmi sesuai rencana: alasannya dapat dijelaskan ke
pemangku kepentingan dan dapat diaudit sampai ke kata pemicunya.

### 7.3 Satu baris per (ulasan, kategori) — bukan per kata kunci

`review_topics` merujuk baris `topics`, yaitu pasangan (kategori, keyword). Bila
satu ulasan ditautkan ke tiga baris keyword dari kategori yang sama, maka
`COUNT(*) GROUP BY kategori` pada T-5.6 menghitungnya **tiga kali** dan
peringkatnya salah.

Karena itu setiap (ulasan, kategori) hanya menyimpan **satu kata kunci pemicu**
— yang berlift tertinggi di antara yang cocok. Hitungan tetap benar, dan
penetapan tetap dapat diaudit: terlihat kata mana yang memicunya.

## 8. Peringkat Topik (T-5.6) — Gambar 9

Dua kolom **terpisah**, tidak digabung menjadi skor komposit. Bab 1 membatasi
prioritas hanya berbasis frekuensi; Likes hadir sebagai lensa tambahan.
Menggabung keduanya menyelundupkan pembobotan yang tidak diizinkan batasan itu.

| # | Kategori | Ulasan | % negatif | Total Likes | Rata Likes | #Frek | #Likes |
|---|----------|--------|-----------|-------------|------------|-------|--------|
| 1 | Ketersediaan & Respons Mitra Driver | 9.663 | 36,15% | 25.913 | 2,68 | 1 | 2 |
| 2 | Pesanan GoFood & Pembatalan | 9.155 | 34,25% | **27.805** | 3,04 | 2 | **1** |
| 3 | Tarif, Ongkir & Promo | 6.939 | 25,96% | 17.754 | 2,56 | 3 | 4 |
| 4 | Layanan Pelanggan & Penanganan Keluhan | 6.916 | 25,87% | 20.941 | 3,03 | 4 | 3 |
| 5 | Transaksi & Saldo GoPay | 4.874 | 18,23% | 11.869 | 2,44 | 5 | **8** |
| 6 | GoPayLater, GoPinjam & Penagihan | 4.786 | 17,90% | 12.657 | 2,65 | 6 | 6 |
| 7 | Performa & Gangguan Aplikasi | 4.479 | 16,76% | 15.321 | 3,42 | 7 | **5** |
| 8 | Akurasi Lokasi & Rute | 3.138 | 11,74% | 12.086 | **3,85** | 8 | 7 |
| 9 | Akun, Login & Verifikasi | 3.048 | 11,40% | 8.037 | 2,64 | 9 | 9 |

*Persentase dihitung terhadap 26.732 ulasan negatif. Kategori tidak saling
eksklusif sehingga totalnya melebihi 100%.*

### 8.1 Jawaban RM2

**Tema keluhan dominan adalah ketersediaan dan respons mitra driver
(36,15% ulasan negatif), disusul pesanan GoFood dan pembatalannya (34,25%).**
Keduanya terpaut tipis dan bersama-sama menguasai dua pertiga korpus keluhan.

Ini konsisten dengan analisis n-gram yang dikerjakan sebelum LDA: `pengemudi`
muncul di 38% ulasan negatif, dan bigram `dapat pengemudi` di 8,8% dokumen.
Dua metode yang berbeda menunjuk ke tempat yang sama.

### 8.2 Peringkat frekuensi ≠ peringkat resonansi

Rencana menyebut: "bila peringkatnya berbeda antara dua kolom, itu sendiri
temuan menarik." Perbedaannya memang ada, dan pada satu kategori cukup tajam:

- **Transaksi & Saldo GoPay turun 3 peringkat** — #5 menurut frekuensi, #9
  menurut rata-rata Likes (2,44, terendah). Masalah saldo banyak dilaporkan
  tetapi **paling sedikit diamini pengguna lain**. Penjelasan yang masuk akal:
  kegagalan transaksi bersifat personal — pembaca lain tidak mengalaminya,
  sehingga tidak menekan tombol *like*.
- **Akurasi Lokasi & Rute punya rata-rata Likes tertinggi (3,85)** meski
  frekuensinya peringkat 8. Kebalikannya: keluhan titik jemput yang salah
  adalah pengalaman yang segera dikenali banyak orang.
- **Performa & Gangguan Aplikasi naik 2 peringkat** (#7 → #5) dengan rata-rata
  Likes 3,42 — gangguan aplikasi dialami serentak oleh banyak pengguna.

Implikasi praktisnya: **frekuensi mengukur berapa banyak yang mengeluh,
rata-rata Likes mengukur berapa banyak yang merasakan hal yang sama.** Keduanya
sah, dan justru karena berbeda maka tidak boleh digabung menjadi satu angka.

## 9. Tren Bulanan (T-5.8)

`docs/tables/topic_trend_monthly.csv` — 180 baris, 20 bulan, 9 kategori.

Mei 2024 **tidak dibuang** melainkan ditandai kolom `periode_parsial = true`
(Temuan 6): datanya mulai 21 Mei, sehingga volumenya rendah karena cakupan
waktu, bukan karena keluhan berkurang. Membuangnya akan menghapus data yang
sah; membiarkannya tanpa tanda akan menghasilkan pembacaan tren yang salah.

Puncak keluhan terjadi **Desember 2024** (Ketersediaan Driver 801,
GoFood 760) dan **April 2025** (GoFood 833 — puncak tertinggi kategori itu).
Sepanjang 2025 kategori "Tarif, Ongkir & Promo" menurun konsisten
(572 → 259 dari Des 2024 ke Des 2025) sementara dua kategori teratas kembali
naik pada kuartal akhir. Menghubungkan lonjakan ini dengan rilis versi aplikasi
adalah bahan Fase 6.

## 10. Tabel 3 Storytelling

`docs/tables/tabel3_storytelling_topik.csv` — kategori, jumlah, persen, total
Likes, kedua peringkat, dan **3 contoh ulasan nyata (teks asli, bukan hasil
preprocessing)** per kategori. Seluruh 27 kutipan unik.

Contoh dipilih dengan dua kriteria berurutan:

1. **Eksklusif** — hanya masuk satu kategori. Tanpa syarat ini, satu ulasan
   ber-likes tinggi yang menyinggung ongkir, pembatalan, dan layanan pelanggan
   akan muncul sebagai contoh ketiganya sekaligus, dan tidak mengilustrasikan
   satu pun dengan baik.
2. **Likes tertinggi** di antara yang eksklusif, panjang 40–300 karakter agar
   dapat dikutip utuh.

## 11. Validasi Silang (H-9)

Penilai: **Samuel Chrisdian** (pemilik proyek), 19 September 2026. 50 ulasan
negatif acak (`random_state=42`) dilabeli tanpa melihat keluaran pipeline.

Yang dibandingkan adalah **hasil penetapan otomatis** pendekatan A — bukan skema
H-8 di atas kertas. Ini pilihan yang disengaja: yang perlu divalidasi adalah
kategorisasi yang benar-benar masuk `review_topics`, dashboard, dan Tabel 3.
Membandingkan dengan skema saja hanya menguji konsistensi penamaan.

| Metrik | Nilai | Membandingkan |
|--------|-------|---------------|
| **Cohen's κ** | **0,4621** — *moderate* | kategori utama penilai vs kategori otomatis berbobot tertinggi |
| Kesepakatan longgar | 84,0% | kategori utama penilai ada di dalam himpunan otomatis |
| Kesepakatan ketat | 52,0% | kecocokan persis label tunggal |
| Jaccard rerata | 0,4967 | {kolom 1, kolom 2} vs seluruh himpunan otomatis |

κ = 0,4621 berada di rentang *moderate* menurut Landis & Koch (1977), **bukan
tinggi.** Angka itu dilaporkan apa adanya. Yang mengubah pelabelan dari
"subjektif" menjadi "subjektif tetapi terukur" bukan besar angkanya, melainkan
keberadaannya.

### 11.1 Validasi menemukan cacat nyata — dan itu memang gunanya

Ketidaksepakatan tidak tersebar merata. Delapan dari sembilan kategori berada di
67–100%; **Akurasi Lokasi & Rute gagal total: 0 dari 3, Jaccard 0,000.**

Penyebabnya terdiagnosis sampai akar, bukan diduga. Kata kunci kategori itu —
`titik, jalan, alamat, sesuai, motor, tuju, rumah, barang, nyaman, bawa` —
tidak memuat satu pun istilah yang paling jelas menandakannya:

| Istilah | Frekuensi korpus negatif | Peringkat relevance topik 6 | Jadi kata kunci? |
|---------|--------------------------|------------------------------|------------------|
| `lokasi` | 497 | #15 | ❌ |
| `peta` | 265 | #19 | ❌ |
| `map` | 254 | #13 | ❌ |
| `gps` | 51 | — | ❌ |

Ketiga ulasan yang tidak disepakati persis bertipe ini — *"Maps tidak akurat"*,
*"Maps ngawur parah."*, *"Gajelas gocek masa maps ga terdetek"* — dan seluruhnya
**tidak memperoleh kategori apa pun** dari penetapan otomatis.

Keempat istilah itu **lolos seluruh saringan kualitas** (`MAX_DF_KORPUS`,
`MIN_LIFT`). Yang menyingkirkannya semata-mata batas `N_KATA_KUNCI = 10`, yang
ditetapkan sembarang karena DoD hanya menuntut ≥5 kata kunci per kategori.

Ini persis jenis cacat yang tidak dapat ditemukan metrik agregat mana pun.
Cakupan 87,62% tampak sehat; kesesuaian A vs B 79,02% tampak meyakinkan.
Keduanya tidak memperlihatkan bahwa satu kategori kehilangan kosakata intinya,
karena kedua angka itu dihitung dari pipeline yang sama yang mengandung cacatnya.
**Hanya penilaian manusia independen yang dapat menemukannya.**

### 11.2 Besaran dampak, diukur bukan dikira

Dampak di tingkat korpus lebih kecil daripada kesan yang ditimbulkan sampel:

| Besaran | Nilai |
|---------|-------|
| Ulasan negatif menyebut `peta`/`lokasi`/`gps` | 771 |
| Di antaranya **tanpa kategori apa pun** | **59 (7,7%)** |
| Porsi dari seluruh korpus negatif | 0,22% |

Sampel 50 kebetulan menarik tiga ulasan pendek yang isinya hanya kata tersebut,
sehingga kegagalannya tampak total. Pada ulasan yang lebih panjang, kata lain
(`titik`, `alamat`, `jalan`) tetap menangkapnya.

### 11.3 Mengapa cacat ini tidak diperbaiki di Fase 5

Memperbaiki kata kunci berdasarkan temuan di atas **membatalkan κ = 0,4621
sebagai validasi versi yang diperbaiki** — parameternya akan disetel memakai
sampel yang sama yang dipakai mengukurnya. Perbaikan yang sah menuntut sampel
validasi baru dengan `random_state` berbeda.

Keputusan pemilik proyek: **laporkan apa adanya.** κ = 0,4621 sah sebagai
validasi versi pipeline yang benar-benar diuji, dan dilaporkan sebagai itu.
Perbaikannya (menaikkan `N_KATA_KUNCI` secara global) tercatat sebagai
rekomendasi, bukan dieksekusi diam-diam.

> ### 📌 Catatan untuk Fase 9 — `docs/limitations.md`
>
> Tiga butir dari fase ini masuk bab Keterbatasan:
>
> 1. **Kesepakatan penilai moderate (κ = 0,46), bukan tinggi.** Pelabelan topik
>    tetap mengandung subjektivitas yang terukur, dan divalidasi oleh **satu**
>    penilai — bukan dua penilai independen.
> 2. **Kategori "Akurasi Lokasi & Rute" kehilangan kosakata intinya**
>    (`lokasi`, `peta`, `map`, `gps`) akibat batas `N_KATA_KUNCI = 10`.
>    Terukur: 59 ulasan (7,7% dari yang bermuatan istilah itu) tidak
>    terkategorikan. Perbaikannya diketahui — naikkan batas secara global —
>    tetapi menuntut validasi ulang dengan sampel baru.
> 3. **12,38% ulasan negatif tidak memperoleh kategori apa pun** (3.310 dari
>    26.732), sebagian besar karena terlalu pendek atau memakai kosakata di luar
>    daftar kata kunci.
