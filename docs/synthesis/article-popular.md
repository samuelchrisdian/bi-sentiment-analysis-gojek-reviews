# Saya Mengumpulkan 526.322 Ulasan Pengguna Gojek — dan Menemukan Akurasi Model Bisa Menipu

Ada satu ulasan yang muncul 15.062 kali dalam dataset ini: **"Ok"**.
<!-- src: docs/tables/teks_paling_berulang.csv -->

Bukan sebagai bagian kalimat. Sebagai seluruh ulasan. Satu kata, lima bintang,
kirim. Dan begitu Anda menyadari betapa sering hal itu terjadi, angka akurasi
model klasifikasi teks tidak akan pernah terlihat sama lagi.

Saya mengumpulkan sendiri ulasan aplikasi Gojek di Google Play Store Indonesia
selama lima tahun penuh, dari Oktober 2021 sampai September 2026 — totalnya
526.322 ulasan. Lalu saya mengerjakan tiga hal: melatih model untuk memisahkan
ulasan positif dari negatif, mengelompokkan keluhan ke dalam kategori yang bisa
diurutkan, dan melihat bagaimana suasana hati pengguna bergerak dari bulan ke
bulan dan dari versi ke versi. Yang paling menarik dari keseluruhan proyek
ternyata bukan skor modelnya — melainkan apa yang tersembunyi di balik skor itu.
<!-- src: docs/tables/profil_dataset.csv; data/script-scraping/scrape_5_tahun.py -->

---

## Ulasan "bahasa Inggris" yang ternyata berbahasa Indonesia

Kejutan pertama datang sebelum analisis dimulai. Saya mengambil ulasan dua
kali: dengan pilihan bahasa Indonesia, lalu bahasa Inggris. Ternyata kumpulan
"bahasa Inggris" sebagian besar berisi ulasan berbahasa Indonesia — dan isinya
lebih negatif. Rupanya Google Play mengelompokkan ulasan menurut bahasa
penulisnya, bukan bahasa teksnya. Dengan satu putaran saja, sebagian keluhan
akan hilang begitu saja.
<!-- src: docs/synthesis/bab-3-pembaruan-data-scraping.md -->

Ulasan yang benar-benar berbahasa Inggris hanya **14.671 (2,8%)**. Saya
menerjemahkannya dengan mesin penerjemah, lalu memeriksa 50 sampel: deteksi
bahasanya benar pada **94%**, terjemahannya layak pada **86%**.
<!-- src: facts.yaml dataset.penanganan_bahasa; docs/tables/audit_terjemahan_sampel_50_reviewed.csv -->

---

## Orang yang senang menulis pendek. Orang yang kecewa menulis panjang.

Ini pola kedua yang muncul, dan besarnya mengejutkan.

Ulasan bintang lima rata-rata panjangnya **4,3 kata**. Setengah di antaranya
bahkan hanya **dua kata atau kurang**. Ulasan bintang satu? Rata-rata **20,3
kata** — hampir lima kali lebih panjang.
<!-- src: docs/tables/panjang_per_rating.csv -->

![Rata-rata jumlah kata per rating. Ulasan bintang lima rata-rata 4,3 kata; bintang satu 20,3 kata.](../figures/final/gambar-02-panjang-per-rating.png)

Digabungkan, **213.697 ulasan — 40,6% dari seluruh dataset — hanya berisi dua
kata atau kurang.** Dan ulasan-ulasan itu hampir seluruhnya positif: di kelas
positif, 56,2% ulasan masuk kategori "dua kata atau kurang", sementara di kelas
negatif hanya 6,5%.
<!-- src: docs/tables/ulasan_pendek.csv; docs/tables/kontras_kelas.csv -->

Logikanya masuk akal kalau dipikir. Orang yang puas tidak punya banyak yang ingin
disampaikan — layanannya bekerja, selesai. Orang yang kecewa punya cerita:
menunggu berapa lama, pesanan apa yang dibatalkan, uang berapa yang tidak kembali.

Tapi konsekuensinya untuk model tidak kelihatan masuk akal sama sekali.

---

## Model saya tidak perlu memahami sentimen untuk terlihat pintar

Model klasifikasi teks klasik bekerja dengan menghitung kata. Kalau dua dari
lima ulasan Anda berisi dua kata seperti "ok", "mantap", atau "bagus", dan
semuanya positif, model tidak perlu belajar apa-apa tentang sentimen. Ia cukup
menghafal beberapa lusin kata pujian, dan sebagian besar pekerjaan sudah beres.

Untuk mengukur seberapa besar efek ini, saya mengevaluasi setiap model **dua
kali**: sekali pada seluruh data uji, sekali lagi hanya pada ulasan yang berisi
minimal lima kata — ulasan yang benar-benar membawa informasi.

Selisihnya nyata:

| Diuji pada | Skor (macro-F1) | Akurasi |
|------------|-----------------|---------|
| Seluruh data uji | 0,9261 | 0,9383 |
| Hanya ulasan ≥5 kata | 0,8951 | 0,8977 |

<!-- src: docs/tables/model_metrics.csv (logistic_regression_final) -->

![Selisih skor antara evaluasi pada seluruh data uji dan pada ulasan minimal lima kata.](../figures/final/gambar-11-selisih-evaluasi.png)

Akurasi turun **4,06 poin** begitu ulasan pendek dikeluarkan.
<!-- src: facts.yaml model.produksi.selisih_accuracy_poin -->

Angka 0,9383 itu bukan bohong. Tapi ia menjawab pertanyaan yang lebih mudah
daripada yang kita kira sedang kita tanyakan. Kalau saya hanya melaporkan angka
pertama — seperti yang lazim dilakukan — saya akan mengklaim kemampuan yang
sebagian berasal dari ribuan ulasan "ok".

**Pelajaran yang bisa dibawa pulang:** kalau Anda membangun klasifikasi teks di
atas data ulasan, periksa distribusi panjang teks per kelas sebelum merayakan
skor Anda. Lalu definisikan satu subset "informatif", dan laporkan kedua
angkanya. Selisihnya adalah harga jujur dari akurasi Anda.

---

## Kejutan berikutnya: separuh "kesalahan" model ternyata bukan kesalahan model

Model-model terbaik dalam proyek ini salah pada sekitar 6% data uji — LinearSVC,
misalnya, pada 6.161 ulasan (6,11%). Saya membaca 50 kesalahannya satu per satu,
lalu mengelompokkan penyebabnya.
<!-- src: facts.yaml analisis_kesalahan -->

Dugaan awal saya — dan dugaan hampir semua literatur analisis sentimen — adalah
sarkasme. Ternyata sarkasme hanya **2 dari 50 kasus**.
<!-- src: docs/tables/error_analysis_50_reviewed.csv -->

Penyebab terbesarnya, dengan **50,0%**, adalah sesuatu yang sama sekali berbeda:
**bintang yang diberikan pengguna bertentangan dengan apa yang mereka tulis.**
<!-- src: docs/tables/error_analysis_50_reviewed.csv -->

Contoh nyata dari dataset: ulasan bintang **lima** yang isinya "Ga bisa update".
Atau bintang lima yang isinya "Knp y setiap isi saldo gk masuk!!!!!!!!!!". Model
menandainya negatif. Model benar. Bintangnya yang tidak sesuai.
<!-- src: docs/tables/error_analysis_50_reviewed.csv (kategori label_keliru_pengguna, rating 5) -->

Polanya sangat timpang: dari kasus salah-label dalam sampel, 23 adalah orang yang
memberi bintang tinggi sambil menulis keluhan, dan hanya 2 yang sebaliknya.
Tampaknya bintang diberikan untuk layanan secara keseluruhan — atau sekadar niat
baik — sementara kolom teks dipakai untuk satu keluhan spesifik.
<!-- src: facts.yaml analisis_kesalahan.n_fp_label_keliru, n_fn_label_keliru -->

Ada konfirmasi yang tidak saya rancang sebelumnya. Saya mencatat seberapa yakin
model pada setiap prediksi. Dari kesalahan yang paling **yakin**, 68,2% adalah
kasus salah-label. Ketika model yakin dan "salah", sering kali modelnya yang benar.
<!-- src: facts.yaml analisis_kesalahan.pct_yakin_label_keliru -->

Artinya, plafon kinerja pada dataset seperti ini bukan 100%. Kalau sekitar 3,05%
data uji membawa bintang yang bertentangan dengan teksnya — perkiraan dari
sampel tadi — tidak ada model yang bisa melewati akurasi sekitar 0,9695. Model
yang akhirnya saya pakai sudah mencapai **96,8% dari plafon itu** — jadi ruang
perbaikan yang tersisa bukan 6 poin, melainkan sekitar 3,12 poin.
<!-- src: facts.yaml analisis_kesalahan -->

---

## Jadi, apa sebenarnya yang dikeluhkan pengguna?

Bagian kedua proyek ini: mengambil 145.924 ulasan negatif (bintang satu dan dua)
dan mengelompokkannya ke dalam kategori keluhan. Hasilnya lima kategori, dan
peringkatnya cukup tegas. Satu ulasan bisa masuk lebih dari satu kategori,
jadi persentasenya tidak dijumlahkan menjadi 100%.
<!-- src: docs/tables/komposisi_kelas.csv; docs/tables/topics_ranked.csv -->

| # | Yang dikeluhkan | Jumlah ulasan | % dari ulasan negatif |
|---|-----------------|---------------|-----------------------|
| 1 | Pencarian & penugasan driver, waktu tunggu & pembatalan pesanan | 55.745 | 38,20% |
| 2 | Layanan pelanggan & penanganan keluhan | 41.154 | 28,20% |
| 3 | Tarif, ongkir & promo | 36.061 | 24,71% |
| 4 | Transaksi, saldo & pemblokiran GoPay | 32.251 | 22,10% |
| 5 | Kendala penggunaan aplikasi & akses akun | 18.331 | 12,56% |

<!-- src: docs/tables/topics_ranked.csv -->

![Peringkat lima kategori keluhan berdasarkan jumlah ulasan.](../figures/final/gambar-09-peringkat-topik.png)

Juara satunya jelas: mendapatkan driver, menunggunya, dan pesanan yang batal di
tengah jalan.

Kata-katanya sendiri sudah menunjukkannya sebelum algoritma apa pun dijalankan.
Dalam ulasan negatif yang berisi minimal lima kata, kata "pengemudi" muncul di
28,2% dokumen, dan frasa "dapat pengemudi" di 6,1%.
<!-- src: docs/tables/ngram_negatif.csv -->

Seperti yang ditulis seorang pengguna, dengan 742 *like* dari pembaca lain:

> "jika goride hemat ya ga ada yang mau ambil, hapus aja pake single rate.
> buang2 waktu nunggu dan gimick aja"

Atau yang ini, tentang layanan pelanggan, dengan 1.386 *like*:

> "Jawaban Customer Service sangat tidak solutif. Memang sudah saatnya beralih
> ke Aplikasi sebelah"

<!-- src: facts.yaml topik.kutipan (docs/tables/tabel3_storytelling_topik.csv) -->

Dua catatan kejujuran. Saya sempat menduga jumlah topik terbaik akan jatuh di
tengah rentang yang saya uji (5 sampai 12), bukan di tepinya; ternyata tepat di
batas bawahnya, 5, jadi dugaan itu tidak terpenuhi. Dan ketika seorang penilai independen
mengategorikan ulasan secara terpisah, kesepakatan kami hanya moderat
(κ = 0,5430) — pengingat bahwa batas antarkategori keluhan memang kabur.
<!-- src: facts.yaml topik.lda_k, angka_struktural.konfigurasi; docs/tables/h9_hasil_kesepakatan.csv -->

### Satu temuan kecil yang saya suka

Saya mengurutkan kategori dengan dua cara: berdasarkan **berapa banyak orang yang
mengeluh**, dan berdasarkan **berapa banyak orang yang menekan tombol *like*** pada
keluhan itu. Urutannya tidak sama.

Keluhan layanan pelanggan ada di peringkat 2 menurut jumlah keluhan, tapi
peringkat 1 menurut jumlah *like* — dengan rata-rata 3,61 *like* per ulasan,
tertinggi di antara semua kategori. Sebaliknya, keluhan transaksi dan saldo GoPay
punya rata-rata *like* terendah, hanya 2,28.
<!-- src: docs/tables/topics_ranked.csv -->

Penjelasannya sederhana begitu dilihat: kegagalan transaksi bersifat personal —
orang lain tidak mengalaminya, jadi tidak ikut menekan *like*. Sementara jawaban
layanan pelanggan yang tidak menyelesaikan masalah adalah pengalaman yang langsung
dikenali banyak orang.

Dua kolom itu menjawab dua pertanyaan berbeda — berapa banyak yang mengeluh, dan
berapa banyak yang merasakan hal yang sama — dan justru karena berbeda, keduanya
tidak boleh digabung menjadi satu skor prioritas.

---

## Apakah suasana hati pengguna berubah dari waktu ke waktu?

Bagian ketiga: saya menjalankan model pada seluruh ulasan, lalu menghitung
persentase ulasan negatif per bulan dan per versi aplikasi.

Rentangnya lebar. Bulan dengan proporsi negatif terendah adalah Juni 2022
(**20,67%**); yang tertinggi justru bulan terakhir data, September 2026
(**56,62%**). Rata-rata rating bulanan bergerak searah: dari 3,98 pada Oktober
2021 menjadi 2,90 pada September 2026.
<!-- src: facts.yaml pola_sentimen_rm3; facts.yaml tren -->

Menurut versi aplikasi, perbedaannya bahkan lebih tajam. Dari 198 versi yang
masing-masing punya minimal 100 ulasan, proporsi negatifnya berkisar dari
**17,66%** (versi 4.13) sampai **60,63%** (versi 5.75).
<!-- src: facts.yaml pola_sentimen_rm3 -->

Perbedaan itu juga diuji. Sebuah versi ditandai bila keluhannya naik minimal 5
poin persentase dari versi sebelumnya *dan* kenaikan itu lolos uji statistik
yang sudah dikoreksi untuk banyaknya perbandingan. Dari 197 perbandingan, 23
versi ditandai; 16 di antaranya tetap ditandai ketika dihitung dari bintang
pemberian pengguna, bukan dari tebakan model.

Ini tetap asosiasi, bukan vonis atas rilis tertentu: 21,5% ulasan tidak
mencantumkan versi, dan tanggal ulasan pertama hanya mendekati tanggal rilis.
Tapi gambarannya sudah jelas — sistem seperti ini bisa memberi tahu tim produk
versi mana yang perlu dilihat lebih dulu.
<!-- src: facts.yaml dataset.pct_missing_versi_app; pola_sentimen_rm3.uji -->

---

## Dan model mana yang menang?

Ini pertanyaan yang paling sering ditanyakan, dan jawabannya paling tidak seru:
**praktis seri.**

Empat varian dari tiga keluarga algoritma klasik, dengan perlakuan data yang
persis sama, hanya berjarak **2,33 poin** antara yang terbaik dan terburuk. Dua
teratas bahkan berselisih kurang dari sepersepuluh poin.
<!-- src: facts.yaml model.rentang_macro_f1_tuned; docs/model_decision.md -->

Yang akhirnya saya pakai bukan yang skornya tertinggi, melainkan yang paling
mudah dijelaskan dan paling sederhana dioperasikan: Logistic Regression. Bahkan
proses *tuning*-nya berakhir kembali persis di konfigurasi bawaan yang saya mulai.
<!-- src: docs/model_decision.md §4 -->

Pada data teks sebesar ini dengan representasi sederhana, pilihan algoritma dan
penyetelan parameter ternyata bukan faktor penentu. Yang menentukan adalah
hal-hal yang lebih membosankan: menjaga kata "tidak" tidak terbuang saat
pembersihan teks, memetakan singkatan seperti "gk" dan "bgt" ke bentuk bakunya,
dan memilih metrik yang tidak bisa dibohongi oleh kelas mayoritas.

---

## Yang saya bawa pulang

1. **Periksa distribusi panjang teks per kelas sebelum percaya pada akurasi.**
   Kalau satu kelas didominasi teks super pendek, skor Anda sebagian adalah
   hadiah gratis.
2. **Rating bintang adalah proksi, bukan kebenaran.** Sebagian "kesalahan" model
   Anda mungkin justru koreksi atas label yang keliru.
3. **Periksa bahasa data Anda, bukan hanya labelnya.** Filter bahasa di sumber
   data tidak selalu berarti apa yang tertulis di namanya.
4. **Preprocessing bahasa Indonesia adalah pekerjaan yang tidak bisa
   diotomatiskan sepenuhnya.** Kamus normalisasi slang dalam proyek ini berisi
   639 entri, dan hasil pembersihannya saya periksa manual dalam 4 putaran atas
   total 400 sampel.
   <!-- src: facts.yaml preprocessing.n_entri_slang, n_putaran_verifikasi, n_sampel_verifikasi_manual -->
5. **Laporkan eksperimen yang gagal.** Percobaan menambahkan kelas "netral" pada
   proyek ini gagal total — model hanya mengenali 0,1872 dari ulasan netral — dan
   justru itu yang membuktikan keputusan desainnya benar.
   <!-- src: facts.yaml tiga_kelas.recall_netral -->

---

*Seluruh angka dalam artikel ini dihasilkan kode yang dapat dijalankan ulang dari
data mentah hasil pengambilan ulasan, dan tersimpan di satu berkas sumber angka
yang diverifikasi otomatis terhadap naskah. Kode, tabel, dan gambar ada di
repositori proyek; keterbatasan penelitiannya — termasuk yang tidak nyaman —
ditulis lengkap di berkas `docs/limitations.md`.*
