# KETERBATASAN PENELITIAN

Seluruh angka bersumber dari `docs/synthesis/facts.yaml`, `docs/tables/*.csv`,
`ml/artifacts/MANIFEST.json`, atau dihitung *read-only* dari berkas data yang
disebut di tiap poin — tidak ada yang ditulis dari ingatan.

Dokumen ini bukan pengakuan kelemahan. Ia membedakan laporan yang bisa
dipertanggungjawabkan dari laporan yang mengklaim lebih dari yang dibuktikan.
Setiap poin di bawah menyatakan **apa** batasnya, **seberapa besar** (dengan
angka), dan **apa konsekuensinya** bagi penafsiran hasil.

---

## A. Data dan cara pengambilannya

## 1. Satu platform, lima tahun, dan hanya ulasan yang masih tersedia

Korpus adalah 526.329 ulasan aplikasi `com.gojek.app` di **Google Play saja**,
periode **1 Oktober 2021 – 30 September 2026** (60 bulan penuh), yang diambil
peneliti pada 11 Oktober 2026 (`docs/data_provenance_notes.md`). Tiga hal
membatasi cakupannya:

- **Tanpa App Store.** Ulasan pengguna iOS tidak tercakup, sehingga temuan
  berlaku untuk pengguna Android yang menulis ulasan, bukan seluruh pengguna
  Gojek — apalagi pengguna yang tidak pernah menulis ulasan.
- **Hanya ulasan yang masih ditampilkan saat pengambilan.** Google Play hanya
  mengembalikan ulasan yang masih tersedia pada 11 Oktober 2026. Ulasan yang
  telah dihapus penulisnya atau oleh layanan tidak terambil, dan jumlahnya tidak
  dapat diketahui. Volume bulanan turun dari 24.424 ulasan (November 2021) ke
  2.904 ulasan (Agustus 2026); dari data ini tidak dapat dipisahkan berapa
  bagian penurunan itu yang mencerminkan perubahan perilaku pengguna dan berapa
  yang mencerminkan ketersediaan ulasan lama.
- **Bukan sensus.** Urutan dan batas pengembalian ditentukan layanan, bukan
  peneliti. Korpus karenanya diperlakukan sebagai sampel non-probabilistik
  (sampel tersedia), dan kesimpulan berlaku atas korpus ini.

**Konsekuensi:** proporsi dan tren yang dilaporkan adalah proporsi dan tren
**dalam korpus ulasan Google Play yang masih tersedia**, bukan ukuran kepuasan
seluruh pengguna Gojek. Menjalankan ulang skrip pengambilan pada tanggal lain
tidak akan menghasilkan berkas yang identik; reproduksibilitas dijamin pada
tingkat berkas (SHA-256 `51e87f6b…937f`), bukan pada tingkat pengambilan.

<!-- src: data/raw/gojek_reviews_5Y.meta.json; docs/tables/volume_bulanan.csv; facts.yaml dataset, tren -->

## 2. Bias parameter `lang` Google Play — temuan empiris, mekanisme tidak terdokumentasi

Pengambilan dengan `lang="id"` saja menghasilkan 462.528 ulasan. Putaran
`lang="en"` dengan negara yang sama menghasilkan **63.801 ulasan lain yang tidak
beririsan sama sekali** (0 `reviewId` ganda), padahal hanya 12.834 di antaranya
(20,1%) yang terdeteksi dominan berbahasa Inggris. Putaran `lang="en"` juga jauh
lebih negatif: **41,0%** berating 1–2, dibanding **25,9%** pada putaran
`lang="id"`.

Pola ini konsisten dengan pengelompokan ulasan menurut bahasa yang terkait
dengan penulisnya, bukan bahasa teksnya. Namun mekanisme internal Google Play
**tidak terdokumentasi secara resmi**; penjelasan tersebut adalah temuan empiris
penelitian ini, bukan spesifikasi layanan.

**Konsekuensi:** penelitian yang hanya mengambil `lang="id"` akan kehilangan
12,1% ulasan yang lebih negatif. Penelitian ini mengambil kedua putaran, tetapi
tidak dapat memastikan bahwa tidak ada kelompok ulasan lain yang hanya muncul
pada nilai `lang` selain `id` dan `en` — nilai lain tidak diuji.

<!-- src: data/raw/gojek_reviews_5Y.meta.json; perhitungan read-only atas data/raw/gojek_reviews_5Y.csv (lang_query, score) dengan ml/src/language_filter.tandai_inggris -->

## 3. Sebagian korpus adalah terjemahan mesin, dan deteksi bahasanya tidak sempurna

Sebanyak **14.671 ulasan (2,8%)** yang dominan berbahasa Inggris dianalisis dalam
bentuk terjemahan mesin MarianMT `Helsinki-NLP/opus-mt-en-id`, bukan teks asli
penggunanya. Audit manual atas 50 ulasan acak
(`docs/tables/audit_terjemahan_sampel_50_reviewed.csv`) menemukan:

- **Deteksi:** 47 benar (94%). Tiga salah tandai: satu ulasan yang sebenarnya
  dominan bahasa Indonesia dengan frasa Inggris "*is the best*", dan dua
  rangkaian karakter acak tanpa makna.
- **Terjemahan:** 43 layak (86%); **7 tidak layak**. Kegagalannya beragam:
  sentimen terbalik ("*HAS BEEN NORMAL AGAIN*" menjadi "Telah mengerikan lagi"),
  nama merek diterjemahkan ("*grab*" menjadi "ambil"), salah ketik sumber yang
  salah dimaknai ("*is the bast*" menjadi "adalah dasar"), kalimat atau slang yang
  dibiarkan tidak diterjemahkan, dan dua masukan acak yang memang tidak dapat
  diterjemahkan.

Deteksi juga **sengaja melewatkan ulasan Inggris yang pendek**: aturan kata
fungsi menuntut sekurang-kurangnya tiga token dan dua kata fungsi Inggris,
sehingga ulasan seperti "*Good*" atau "*Nice*" tetap dalam bahasa aslinya.
Ulasan berisi persis "Good" saja muncul 11.389 kali, "good" 3.220 kali, "Nice"
2.006 kali, dan "Good job" 1.057 kali (`docs/tables/teks_paling_berulang.csv`).
Audit hanya mengambil sampel dari ulasan yang **ditandai**, sehingga mengukur
ketepatan deteksi, bukan berapa ulasan Inggris yang terlewat.

**Konsekuensi:** dengan kelayakan 86% pada sampel 50, sebagian dari 14.671
terjemahan diperkirakan membawa makna atau sentimen yang menyimpang; besarnya
pada populasi tidak diestimasi dari sampel sekecil ini. Kata Inggris pendek yang
terlewat tetap menjadi fitur leksikal yang sah bagi model (mis. `good` sebagai
penanda positif), tetapi korpus tidak sepenuhnya satu bahasa. Emoji pada ulasan
yang diterjemahkan juga ikut hilang.

<!-- src: facts.yaml dataset.penanganan_bahasa; docs/tables/audit_terjemahan_sampel_50_reviewed.csv; data/interim/terjemahan_inggris.csv; ml/config.yaml language_filter -->

---

## B. Label dan evaluasi model

## 4. Label sentimen diturunkan dari rating bintang, bukan anotasi manusia

Label negatif/positif dipetakan otomatis dari bintang (1–2★ → negatif, 4–5★ →
positif). Rating bintang adalah **proksi**, bukan label sentimen teks.

Pemeriksaan manual 50 kesalahan acak model rujukan LinearSVC tuned
(`docs/error_analysis.md`, `docs/tables/error_analysis_50_reviewed.csv`)
menunjukkan **25 dari 50 (50%) adalah label yang keliru dari pengguna** —
bintang yang bertentangan dengan isi tulisan. Arahnya sangat timpang: 23 dari 25
kasus adalah pengguna yang memberi 4–5★ sambil menulis keluhan, hanya 2 kasus
sebaliknya.

**Konsekuensi:** sebagian "kesalahan" model sebenarnya prediksi yang benar atas
label yang salah. Diekstrapolasi ke 6.161 baris uji yang salah diklasifikasikan,
≈3.080 baris (3,05%) dari 100.842 baris uji membawa bintang yang bertentangan
dengan teksnya, sehingga **plafon akurasi realistis ≈0,9695 — bukan 1,000**.
Akurasi model produksi (Logistic Regression) 0,9383 karena itu setara **96,8%
dari plafon**, dan sisa ruang perbaikan ≈3,12 poin, bukan 6,17 poin. Estimasi
ini berasal dari sampel 50 baris dengan selang kepercayaan lebar (Wilson 95%
untuk 25/50: 36,6%–63,4%, setara derau label 2,24%–3,87% dan plafon
0,9613–0,9776). Karena hanya diambil dari baris yang salah diklasifikasikan,
angka ini merupakan **batas bawah** derau label: bintang keliru pada baris yang
"benar" diklasifikasikan tidak terhitung.

<!-- src: facts.yaml analisis_kesalahan, model.produksi; docs/tables/error_analysis_50_reviewed.csv (arah_kesalahan × kategori_penyebab); selang Wilson dihitung dari 25/50 -->

## 5. 40,6% ulasan hanya berisi ≤2 kata — metrik pada test set penuh optimistis

Sebanyak **213.697 ulasan (40,6%)** hanya berisi dua kata atau kurang, dan
sebagian besar positif: ulasan 5★ rata-rata **4,3 kata** (median 2), sementara
1★ mencapai **20,3 kata**. Ulasan ≤2 kata mencakup 56,2% kelas positif dan 6,5%
kelas negatif. Mengevaluasi hanya pada test set penuh berarti menghitung
"bagus" → positif sebagai keberhasilan klasifikasi.

**Konsekuensi:** setiap model dilaporkan pada dua set evaluasi, dan selisihnya
adalah ukuran dari melebih-lebihkan tersebut. Pada model produksi
(Logistic Regression, `C=1.0`, `class_weight="balanced"`):

| Set evaluasi | n | macro-F1 | recall negatif | akurasi |
|--------------|---|----------|----------------|---------|
| `full` | 100.842 | 0,9261 | 0,9192 | 0,9383 |
| `informative_ge5w` (≥5 kata) | 45.069 | 0,8951 | 0,9442 | 0,8977 |
| **Selisih** | — | **−3,10 poin** | +2,50 poin | −4,06 poin |

Angka `informative_ge5w` adalah ukuran kemampuan yang sesungguhnya pada teks
yang membawa informasi. Setiap klaim kinerja harus dibaca berpasangan, bukan
hanya angka `full`-nya.

<!-- src: facts.yaml asimetri_panjang, model.produksi; docs/tables/model_metrics.csv; ml/artifacts/MANIFEST.json metrics -->

## 6. Kelas netral (3★) dikeluarkan dari model utama

Rating 3★ hanya **22.114 ulasan (4,2%)** — rasio **1:16,2** terhadap kelas
positif. Kelas ini dibuang dari skema utama, sehingga model **tidak dapat
mengenali sentimen netral sama sekali**: setiap ulasan 3★ yang masuk akan
dipaksa menjadi negatif atau positif.

Keputusan ini tidak diambil berdasarkan asumsi. Varian tiga kelas (LinearSVC,
protokol identik) dijalankan dan **gagal pada kelas netral**: macro-F1
**0,6617** vs **0,9270** pada skema biner — turun **26,5 poin**
(`docs/three_class_experiment.md`). Recall kelas netral hanya **0,1872**: dari
4.423 ulasan netral di data uji, 2.425 (54,8%) diprediksi negatif dan 1.170
(26,5%) positif. Penyebabnya bukan *hyperparameter*, melainkan contoh netral
yang tidak terpisahkan secara leksikal dari kelas negatif (panjang rata-rata
17,9 kata, dekat dengan 20,6 kata pada kelas negatif).

<!-- src: facts.yaml komposisi_kelas, tiga_kelas; ml/artifacts/reports/three_class_linear_svc.json -->

---

## C. Pra-pemrosesan

## 7. Residu pra-pemrosesan setelah empat putaran verifikasi

Hasil pra-pemrosesan diverifikasi manual empat putaran (400 sampel). Putaran 1–3
masing-masing menemukan masalah sistemik yang diperbaiki; putaran 4 tidak
menemukan lagi masalah sistemik yang **mengubah makna**. Namun beberapa
kesalahan yang tersisa diketahui dan tidak diperbaiki, karena dampaknya pada
sentimen kecil atau perbaikannya berisiko memunculkan kesalahan baru:

- **Angka dibuang secara global.** Informasi nominal dan jumlah hilang ("2 juta"
  kehilangan "2"; "40k dan 65k" kehilangan angkanya; rentang "2–4 hari" hilang).
- **Sebagian kata fungsi bermakna ikut terbuang sebagai *stopword*.** Misalnya
  "masih" dan "hanya": "tidak hanya SMS" menjadi "tidak SMS", sehingga makna
  pilihan SMS-dan-WhatsApp terbaca sebagai WhatsApp saja.
- **Salah ketik satuan (kasus per kasus, tidak sistemik) tidak dinormalisasi**,
  termasuk pada kata sentimen (`maasih`, `mantrap`, `oky`, `trmksh`), sehingga
  sebagian token positif tidak dikenali sebagai bentuk bakunya.
- **Stemming berfrekuensi rendah yang mengubah makna** (`pengemudimu` → `mud`,
  `perasaan` → `asa`). Kasus berfrekuensi tinggi (`sejauh`, `setujui`,
  `tertarik`) sudah dikecualikan.
- **Kata Inggris berakhiran huruf ganda ikut diringkas** (`address` → `addres`).
  Pemetaannya konsisten di seluruh korpus, sehingga tidak memecah satu kata
  menjadi dua fitur.
- **Campur kode belum seragam** ("very bad" menjadi "sangat bad"; "on time"
  menjadi "on waktu").

Teks yang menjadi kosong setelah pra-pemrosesan berjumlah 1.321 baris (0,3%).

**Konsekuensi:** residu ini menurunkan presisi fitur leksikal dan dapat menggeser
kata kunci topik, tetapi pada sampel putaran 4 tidak ditemukan sentimen yang
berbalik karenanya. Kategori `kegagalan_preprocessing` hanya muncul pada 1 dari
50 kesalahan model yang diperiksa (`docs/error_analysis.md`).

<!-- src: facts.yaml preprocessing, analisis_kesalahan.kategori; docs/tables/preprocessing_sample_{100,ronde2,ronde3,ronde4}_reviewed.csv (catatan_pemeriksa); docs/synthesis/bab-3-pembaruan-data-scraping.md A.2 butir 5, B.16(c) -->

---

## D. Ekstraksi dan pelabelan topik keluhan

## 8. k LDA terpilih jatuh di batas bawah rentang, dan klaster terbesar bersifat umum

LDA dipindai pada k = 5 sampai 12 atas 125.834 ulasan negatif berisi ≥5 kata.
Koherensi $c_v$ tertinggi berada pada **k = 5 (0,5908)** — tepat di **batas
bawah** rentang yang ditetapkan sebelum analisis, dengan k = 8 (0,5880) di
urutan kedua. Kriteria hipotesis tema keluhan bahwa k terpilih berada di dalam
rentang dan bukan di batasnya karenanya **tidak terpenuhi**. Rentang tidak
diubah setelah hasil dibaca, sehingga tidak diketahui apakah k < 5 akan
menghasilkan koherensi lebih tinggi.

Klaster terbesar mencakup **40,2% dokumen** sebagai topik dominan, tetapi isinya
umum dan heterogen. Kata kunci pembedanya spesifik tentang penggunaan aplikasi
dan akses akun, sehingga hanya **12,56%** ulasan negatif yang ditetapkan ke
kategori "Kendala Penggunaan Aplikasi & Akses Akun".

**Konsekuensi:** lima kategori adalah struktur kasar, bukan taksonomi keluhan
yang lengkap; tema yang lebih sempit mungkin tergabung. Angka 40,2% **tidak
boleh** ditafsirkan sebagai proporsi masalah aplikasi atau akun.

<!-- src: docs/tables/lda_coherence.csv; facts.yaml topik; data/processed/lda_doc_topic.npy (argmax per dokumen); docs/synthesis/bab-3-pembaruan-data-scraping.md C.2 -->

## 9. Penamaan dan validasi kategori topik bersifat subjektif

Usulan nama awal kelima kategori disusun **dengan bantuan model bahasa**, lalu
dinilai dan direvisi penulis; nama final ditetapkan penulis
(`docs/tables/lda_clusters_for_labeling_reviewed.csv`, kolom
`catatan_perubahan`). Kata kunci tiap kategori dipilih otomatis dari bobot LDA
(*relevance*, `ml/src/topic_assign.py`), dan penetapan berbasis kata kunci itu
mencakup **77,25%** ulasan negatif; 22,75% sisanya tidak masuk kategori mana pun.

Validasi silang oleh penilai independen atas 50 ulasan negatif menghasilkan
**Cohen's κ = 0,543** — tingkat *moderate* menurut Landis & Koch (1977),
**bukan substantial** — dengan kesepakatan longgar 78% dan ketat 62%
(`docs/tables/h9_hasil_kesepakatan.csv`). Penilai memakai **nama dan definisi
kategori versi awal**; labelnya dipetakan satu-satu ke nama final. Dua ulasan
tentang GoPayLater yang diblokir dilabeli penilai "Layanan Pelanggan &
Pemblokiran Akun", padahal menurut definisi final keduanya masuk kategori GoPay;
bila dibaca menurut definisi final, **κ = 0,591** — tetap *moderate*.

Angka ini dilaporkan apa adanya. Kata kunci pemetaan **tidak** disesuaikan
setelah melihat hasil validasi, karena penyesuaian semacam itu akan membatalkan κ
sebagai validasi independen.

**Konsekuensi:** peringkat kategori keluhan harus dibaca sebagai **indikasi
arah, bukan pengukuran presisi**. Urutan dua kategori teratas (38,20% dan
28,20% ulasan negatif) relatif tegas, tetapi selisih yang kecil — misalnya
peringkat ke-3 dan ke-4, 24,71% vs 22,10% — berada dalam rentang yang dapat
dipengaruhi kesepakatan *moderate* dan tidak boleh ditafsirkan sebagai perbedaan
pasti. Validasi dengan definisi final oleh penilai yang sama belum dilakukan.

<!-- src: facts.yaml topik, validasi_silang; docs/tables/h9_hasil_kesepakatan.csv; docs/tables/cross_validation_sample_50_reviewed.csv (kategori_penilai_1_asli); docs/synthesis/bab-3-pembaruan-data-scraping.md C.3, C.6 -->

---

## E. Versi aplikasi dan dimensi waktu

## 10. 21,5% ulasan tidak mencantumkan versi aplikasi

Sebanyak **113.357 baris (21,5%)** memiliki `Versi App` kosong dan **tidak
diimputasi** — imputasi versi tidak punya dasar yang dapat dipertahankan.
Dari 449 string versi unik, analisis per versi diagregasi ke versi minor dan
dibatasi pada versi dengan **≥100 ulasan**: 198 versi minor yang mencakup
**410.313 ulasan (99,4%)** dari data berversi.

Kekosongan ini **tidak acak**: proporsinya berbeda menurut putaran pengambilan
(22,4% pada `lang="id"` vs 15,3% pada `lang="en"`) dan menurut tahun (19,7% pada
2024 hingga 24,4% pada 2021).

**Konsekuensi:** analisis per versi berlaku atas 410.313 ulasan, bukan atas
526.322. Perbandingan antar-versi tidak boleh digeneralisasi ke seluruh korpus,
karena seperlima data yang tak berversi berbeda komposisinya dari data berversi.

<!-- src: facts.yaml dataset.missing_versi_app, dataset.n_versi_unik, pola_sentimen_rm3.n_versi_dianalisis; perhitungan read-only atas data/raw/gojek_reviews_5Y.csv (reviewCreatedVersion × lang_query, × tahun; 526.322 baris berteks) -->

## 11. Data statis — tidak ada evaluasi *concept drift*

Korpus mencakup satu rentang tetap: **1 Oktober 2021 – 30 September 2026** (60
bulan, 526.322 ulasan dianalisis). Model dilatih dan diuji dengan *split* acak
berstratifikasi atas rentang yang sama, **bukan** dengan *split* temporal.
Pola sentimen menurut waktu dan versi (RM3) dihitung dari **label prediksi**
model produksi atas seluruh periode yang sama.

**Konsekuensi:** tidak ada bukti bagaimana kinerja model bertahan terhadap
perubahan kosakata pengguna, fitur aplikasi baru, atau pergeseran pola keluhan
di luar periode ini. Bila akurasi model berbeda antarperiode, sebagian variasi
proporsi negatif bulanan (20,67% pada Juni 2022 hingga 56,62% pada September
2026) dapat berasal dari kesalahan model, bukan dari perubahan sentimen; hal ini
tidak diuji. Evaluasi *concept drift* menuntut *split* berbasis waktu dan data
periode berikutnya — keduanya di luar lingkup penelitian ini.

<!-- src: facts.yaml dataset, pola_sentimen_rm3; ml/config.yaml split -->

---

## F. Sistem

## 12. Sistem tidak di-*deploy* ke produksi

Lingkup dibatasi pada **prototipe lokal**: tiga container yang berjalan lewat
`docker compose` di satu mesin. Tidak ada autentikasi, kendali akses,
pemantauan, *rate limiting*, pencatatan audit, maupun strategi *retraining*.

Skoring bersifat **batch sekali jalan** — ulasan baru tidak masuk secara otomatis
dan dashboard hanya membaca agregat pre-scoring. Endpoint `/api/predict` ada
sebagai demo kapabilitas, bukan sebagai jalur layanan yang telah diuji beban.
Setiap klaim tentang kesiapan operasional berada di luar yang dibuktikan
penelitian ini.

---

## Ringkasan dalam Satu Tabel

| # | Keterbatasan | Ukuran |
|---|-------------|--------|
| 1 | Hanya Google Play, ulasan yang masih tersedia, bukan sensus | 60 bulan; tanpa App Store; ulasan terhapus tidak terukur |
| 2 | Bias parameter `lang` (temuan empiris) | Putaran `lang="en"` 12,1% korpus, 41,0% vs 25,9% rating 1–2 |
| 3 | Terjemahan mesin dan deteksi bahasa | 2,8% korpus diterjemahkan; 7/50 tidak layak; Inggris pendek terlewat |
| 4 | Label dari bintang, bukan anotasi manusia | 50% kesalahan = label keliru; plafon akurasi ≈0,9695 |
| 5 | Ulasan sangat pendek mendominasi | 40,6% ≤2 kata; selisih evaluasi 3,10 poin macro-F1 |
| 6 | Kelas netral dikeluarkan | 4,2% data; recall netral 0,1872 pada varian tiga kelas |
| 7 | Residu pra-pemrosesan | Angka, sebagian *stopword*, *typo*, stemming langka, `addres` |
| 8 | k LDA di batas bawah; klaster umum | k = 5 (c_v 0,5908); klaster umum 40,2% dokumen |
| 9 | Penamaan & validasi topik subjektif | κ = 0,543 (0,591 definisi final), *moderate*; cakupan 77,25% |
| 10 | Versi aplikasi tidak lengkap | 21,5% kosong, tidak acak; cakupan 99,4% data berversi |
| 11 | Data statis | 60 bulan, tanpa *split* temporal |
| 12 | Prototipe, bukan produksi | 3 container lokal; tanpa auth/monitoring/retraining |
