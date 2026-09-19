# Saya Membaca 100.000 Keluhan Pengguna Gojek — dan Menemukan Akurasi Model Bisa Menipu

Ada satu kata yang muncul 2.063 kali dalam dataset ini: **"Mantap"**.
<!-- src: docs/tables/teks_paling_berulang.csv -->

Bukan sebagai bagian kalimat. Sebagai seluruh ulasan. Satu kata, lima bintang,
kirim. Dan begitu Anda menyadari betapa sering hal itu terjadi, angka akurasi
model klasifikasi teks tidak akan pernah terlihat sama lagi.

Saya mengambil 100.000 ulasan aplikasi Gojek di Google Play Store dari rentang
21 Mei 2024 sampai 31 Desember 2025, lalu mengerjakan dua hal: melatih model
untuk memisahkan ulasan positif dari negatif, dan mengelompokkan keluhan ke dalam
kategori yang bisa diurutkan. Yang paling menarik dari keseluruhan proyek ternyata
bukan skor modelnya — melainkan apa yang tersembunyi di balik skor itu.
<!-- src: docs/tables/profil_dataset.csv -->

---

## Orang yang senang menulis pendek. Orang yang kecewa menulis panjang.

Ini pola pertama yang muncul, dan besarnya mengejutkan.

Ulasan bintang lima rata-rata panjangnya **4,4 kata**. Setengah di antaranya
bahkan hanya **dua kata atau kurang**. Ulasan bintang satu? Rata-rata **20,8
kata** — hampir lima kali lebih panjang.
<!-- src: docs/tables/panjang_per_rating.csv -->

![Rata-rata jumlah kata per rating. Ulasan bintang lima rata-rata 4,4 kata; bintang satu 20,8 kata.](../figures/final/gambar-02-panjang-per-rating.png)

Digabungkan, **39.859 ulasan — 39,9% dari seluruh dataset — hanya berisi dua kata
atau kurang.** Dan ulasan-ulasan itu hampir seluruhnya positif: di kelas positif,
54,4% ulasan masuk kategori "dua kata atau kurang", sementara di kelas negatif
hanya 6,0%.
<!-- src: docs/tables/ulasan_pendek.csv; docs/tables/kontras_kelas.csv -->

Logikanya masuk akal kalau dipikir. Orang yang puas tidak punya banyak yang ingin
disampaikan — layanannya bekerja, selesai. Orang yang kecewa punya cerita:
menunggu berapa lama, pesanan apa yang dibatalkan, uang berapa yang tidak kembali.

Tapi konsekuensinya untuk model tidak kelihatan masuk akal sama sekali.

---

## Model saya tidak perlu memahami sentimen untuk terlihat pintar

Model klasifikasi teks klasik bekerja dengan menghitung kata. Kalau hampir
separuh data Anda adalah ulasan dua kata yang isinya "mantap", "bagus", atau
"ok", dan semuanya positif, model tidak perlu belajar apa-apa tentang sentimen.
Ia cukup menghafal beberapa lusin kata pujian, dan separuh pekerjaan sudah beres.

Untuk mengukur seberapa besar efek ini, saya mengevaluasi setiap model **dua
kali**: sekali pada seluruh data uji, sekali lagi hanya pada ulasan yang berisi
minimal lima kata — ulasan yang benar-benar membawa informasi.

Selisihnya nyata:

| Diuji pada | Skor (macro-F1) | Akurasi |
|------------|-----------------|---------|
| Seluruh data uji | 0,9336 | 0,9459 |
| Hanya ulasan ≥5 kata | 0,9078 | 0,9089 |

<!-- src: docs/tables/model_metrics.csv -->

![Selisih skor antara evaluasi pada seluruh data uji dan pada ulasan minimal lima kata.](../figures/final/gambar-11-selisih-evaluasi.png)

Akurasi turun **3,70 poin** begitu ulasan dua kata dikeluarkan.
<!-- src: facts.yaml model.produksi.selisih_accuracy_poin -->

Angka 0,9459 itu bukan bohong. Tapi ia menjawab pertanyaan yang lebih mudah
daripada yang kita kira sedang kita tanyakan. Kalau saya hanya melaporkan angka
pertama — seperti yang lazim dilakukan — saya akan mengklaim kemampuan yang
sebagian besar berasal dari ribuan ulasan "mantap".

**Pelajaran yang bisa dibawa pulang:** kalau Anda membangun klasifikasi teks di
atas data ulasan, periksa distribusi panjang teks per kelas sebelum merayakan
skor Anda. Lalu definisikan satu subset "informatif", dan laporkan kedua
angkanya. Selisihnya adalah harga jujur dari akurasi Anda.

---

## Kejutan kedua: separuh "kesalahan" model ternyata bukan kesalahan model

Model produksi salah pada sekitar 5% data uji. Saya membaca 50 kesalahan itu satu
per satu, lalu mengelompokkan penyebabnya.

Dugaan awal saya — dan dugaan hampir semua literatur analisis sentimen — adalah
sarkasme. Ternyata sarkasme hanya **2 dari 50 kasus**.
<!-- src: docs/tables/error_analysis_50_reviewed.csv -->

Penyebab terbesarnya, dengan **48,0%**, adalah sesuatu yang sama sekali berbeda:
**bintang yang diberikan pengguna bertentangan dengan apa yang mereka tulis.**
<!-- src: docs/tables/error_analysis_50_reviewed.csv -->

Contoh nyata dari dataset: ulasan bintang **lima** yang isinya "aplikasinya
sering lemot". Atau bintang lima yang isinya keluhan saldo GoPay yang berkurang
tapi tidak sampai ke penerima. Model menandainya negatif. Model benar. Bintangnya
yang tidak sesuai.
<!-- src: docs/error_analysis.md §3.1 -->

Polanya sangat timpang: dari kasus salah-label dalam sampel, 22 adalah orang yang
memberi bintang tinggi sambil menulis keluhan, dan hanya 2 yang sebaliknya.
Tampaknya bintang diberikan untuk layanan secara keseluruhan — atau sekadar niat
baik — sementara kolom teks dipakai untuk satu keluhan spesifik.
<!-- src: docs/error_analysis.md §3.1 -->

Ada konfirmasi yang tidak saya rancang sebelumnya. Saya mencatat seberapa yakin
model pada setiap prediksi. Dari kesalahan yang paling **yakin**, 72,7% adalah
kasus salah-label. Ketika model yakin dan "salah", biasanya modelnya yang benar.
<!-- src: docs/error_analysis.md §3.2 -->

Artinya, plafon kinerja pada dataset seperti ini bukan 100%. Kalau sekitar 2,59%
data uji membawa bintang yang bertentangan dengan teksnya, tidak ada model yang
bisa melewati sekitar 0,9741. Model saya sudah mencapai **97,1% dari plafon itu**
— jadi ruang perbaikan yang tersisa bukan 5 poin, melainkan sekitar 2,82 poin.
<!-- src: facts.yaml analisis_kesalahan -->

---

## Jadi, apa sebenarnya yang dikeluhkan pengguna?

Bagian kedua proyek ini: mengambil 26.732 ulasan negatif dan mengelompokkannya ke
dalam kategori keluhan. Hasilnya sembilan kategori, dan peringkatnya cukup tegas.
<!-- src: docs/tables/komposisi_kelas.csv; docs/tables/topics_ranked.csv -->

| # | Yang dikeluhkan | Jumlah ulasan | % dari ulasan negatif |
|---|-----------------|---------------|-----------------------|
| 1 | Ketersediaan & respons mitra driver | 9.663 | 36,15% |
| 2 | Pesanan GoFood & pembatalan | 9.155 | 34,25% |
| 3 | Tarif, ongkir & promo | 6.939 | 25,96% |
| 4 | Layanan pelanggan & penanganan keluhan | 6.916 | 25,87% |
| 5 | Transaksi & saldo GoPay | 4.874 | 18,23% |

<!-- src: docs/tables/topics_ranked.csv -->

![Peringkat sembilan kategori keluhan berdasarkan jumlah ulasan.](../figures/final/gambar-09-peringkat-topik.png)

Dua teratas menyentuh **70,4%** korpus keluhan, dan jaraknya terlalu tipis untuk
disebut juara satu dan dua. Keduanya satu masalah yang sama dilihat dari dua sisi:
mendapatkan driver.
<!-- src: facts.yaml topik.dua_teratas_pct -->

Kata-katanya sendiri sudah menunjukkannya sebelum algoritma apa pun dijalankan.
Dalam ulasan negatif, kata "pengemudi" muncul di 38,0% dokumen, dan frasa "dapat
pengemudi" di 8,8%.
<!-- src: docs/tables/ngram_negatif.csv -->

Seperti yang ditulis seorang pengguna, dengan 190 *like* dari pembaca lain:

> "tolong fitur pencarian drivernya segera diperbaiki, setiap kali memesan selalu
> saja dapat driver yang lokasinya terlampau jauh, padahal dilokasi pemesanan
> banyak sekali driver yang lebih dekat…"

Atau yang ini, 168 *like*:

> "sudah di tunggu sejam lebih malah di cancel go-food saya!"

<!-- src: docs/tables/tabel3_storytelling_topik.csv -->

### Satu temuan kecil yang saya suka

Saya mengurutkan kategori dengan dua cara: berdasarkan **berapa banyak orang yang
mengeluh**, dan berdasarkan **berapa banyak orang yang menekan tombol *like*** pada
keluhan itu. Urutannya tidak sama.

Masalah saldo GoPay ada di peringkat 5 menurut jumlah keluhan, tapi peringkat
terakhir menurut rata-rata *like*. Sebaliknya, keluhan soal akurasi lokasi ada di
peringkat 8 menurut jumlah, tapi memiliki rata-rata *like* tertinggi.
<!-- src: docs/tables/topics_ranked.csv -->

Penjelasannya sederhana begitu dilihat: kegagalan transaksi bersifat personal —
orang lain tidak mengalaminya, jadi tidak ikut menekan *like*. Sementara titik
jemput yang meleset adalah pengalaman yang langsung dikenali semua orang.

Dua kolom itu menjawab dua pertanyaan berbeda — berapa banyak yang mengeluh, dan
berapa banyak yang merasakan hal yang sama — dan justru karena berbeda, keduanya
tidak boleh digabung menjadi satu skor prioritas.

---

## Dan model mana yang menang?

Ini pertanyaan yang paling sering ditanyakan, dan jawabannya paling tidak seru:
**praktis seri.**

Saya melatih empat varian dari tiga keluarga algoritma klasik dengan perlakuan
data yang persis sama. Jarak antara yang terbaik dan yang terburuk hanya **1,88
poin**. Jarak antara dua teratas: **0,03 poin** — setara sekitar enam baris dari
19.294 data uji.
<!-- src: facts.yaml model.rentang_macro_f1_tuned -->

Yang akhirnya saya pakai bukan yang skornya tertinggi, melainkan yang paling
mudah dijelaskan dan paling sederhana dioperasikan. Bahkan proses *tuning*-nya
berakhir kembali persis di konfigurasi bawaan yang saya mulai.
<!-- src: docs/model_decision.md §5 -->

Itu sendiri sebuah temuan. Pada data teks sebesar ini dengan representasi
sederhana, pilihan algoritma dan penyetelan parameter bukan faktor penentu. Yang
menentukan adalah hal-hal yang lebih membosankan: menjaga kata "tidak" tidak
terbuang saat pembersihan teks, memetakan singkatan seperti "gk" dan "bgt" ke
bentuk bakunya, dan memilih metrik yang tidak bisa dibohongi oleh kelas mayoritas.

---

## Yang saya bawa pulang

1. **Periksa distribusi panjang teks per kelas sebelum percaya pada akurasi.**
   Kalau satu kelas didominasi teks super pendek, skor Anda sebagian adalah
   hadiah gratis.
2. **Rating bintang adalah proksi, bukan kebenaran.** Sebagian "kesalahan" model
   Anda mungkin justru koreksi atas label yang keliru.
3. **Preprocessing bahasa Indonesia adalah pekerjaan yang tidak bisa
   diotomatiskan sepenuhnya.** Kamus normalisasi slang dalam proyek ini berisi
   572 entri, dan dipetakan satu per satu oleh manusia.
   <!-- src: facts.yaml preprocessing.n_entri_slang -->
4. **Laporkan eksperimen yang gagal.** Percobaan menambahkan kelas "netral" pada
   proyek ini gagal total, dan justru itu yang membuktikan keputusan desainnya
   benar.

---

*Seluruh angka dalam artikel ini dihasilkan kode yang dapat dijalankan ulang dari
data mentah, dan tersimpan di satu berkas sumber angka yang diverifikasi otomatis
terhadap naskah. Kode, tabel, dan gambar ada di repositori proyek; keterbatasan
penelitiannya — termasuk yang tidak nyaman — ditulis lengkap di berkas
`docs/limitations.md`.*
