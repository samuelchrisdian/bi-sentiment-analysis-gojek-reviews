# Abstrak (Bahasa Indonesia)

<!-- ===== Abstrak ID — SIAP TEMPEL ===== -->

Ulasan pengguna di toko aplikasi adalah sumber umpan balik berskala besar yang
tidak terstruktur, sehingga keluhan yang berulang dan perubahan sentimen dari
rilis ke rilis sulit dipantau secara sistematis. Penelitian ini mengumpulkan
sendiri ulasan aplikasi Gojek dari Google Play Indonesia selama lima tahun
(Oktober 2021 – September 2026) dan menganalisis 526.322 ulasan; 14.671 ulasan
(2,8%) yang dominan berbahasa Inggris diterjemahkan ke bahasa Indonesia dengan
model terjemahan mesin MarianMT. Klasifikasi sentimen biner dibangun di atas
representasi TF-IDF 1–2 gram dengan label yang diturunkan dari rating bintang;
model produksi dipilih dari empat varian tiga keluarga algoritma klasik melalui
kerangka keputusan yang ditetapkan sebelumnya, lalu dievaluasi dengan protokol
ganda pada data uji penuh dan pada ulasan berisi minimal lima kata. Model
terpilih, Logistic Regression, mencapai macro-F1 0,9261 dan recall kelas negatif
0,9192 pada data uji penuh terhadap baseline kelas mayoritas 0,4154, tetapi macro-F1
turun 3,10 poin menjadi 0,8951 pada ulasan informatif: 40,6% ulasan hanya
berisi dua kata atau kurang dan hampir seluruhnya positif, sementara pemeriksaan
manual atas 50 kesalahan klasifikasi menunjukkan 50,0% di antaranya berasal dari
rating bintang yang bertentangan dengan isi ulasan. Pemodelan topik LDA atas
ulasan negatif yang dilanjutkan dengan penetapan kategori berbasis kata kunci
menghasilkan lima kategori keluhan, dipimpin oleh pencarian dan penugasan
driver, waktu tunggu, dan pembatalan pesanan (38,20% ulasan negatif) serta
layanan pelanggan (28,20%), dengan kesepakatan moderat terhadap penilai
independen (κ = 0,5430). Secara deskriptif, proporsi ulasan negatif hasil
prediksi model berkisar 20,67%–56,62% per bulan dan 17,66%–60,63% di antara 198 versi
aplikasi, dengan nilai bulanan tertinggi justru pada bulan terakhir data. Aturan
penandaan rilis menandai 23 dari 197 perbandingan versi berurutan, 16 di antaranya
juga ditandai dengan label rating.
Penelitian ini menyimpulkan bahwa evaluasi ganda perlu menjadi praktik standar
pada korpus ulasan aplikasi dan bahwa sistem lebih tepat diposisikan sebagai alat
triase serta pemantauan keluhan per waktu dan per rilis, bukan sebagai pengganti
pembacaan manusia.

**Kata kunci:** analisis sentimen; bahasa Indonesia; ulasan aplikasi;
terjemahan mesin; ketidakseimbangan kelas; TF-IDF; pemodelan topik LDA.

---

<!-- Rujukan angka:
     526.322 ulasan & periode    facts.yaml dataset (docs/tables/profil_dataset.csv)
     14.671 ulasan diterjemahkan facts.yaml dataset.penanganan_bahasa
     macro-F1 & recall           docs/tables/model_metrics.csv; facts.yaml model.produksi
     selisih evaluasi ganda      facts.yaml model.produksi.selisih_macro_f1_poin
     40,6% ulasan pendek         docs/tables/ulasan_pendek.csv
     50,0% label keliru          docs/tables/error_analysis_50_reviewed.csv
     peringkat topik             docs/tables/topics_ranked.csv
     kappa penilai independen    docs/tables/h9_hasil_kesepakatan.csv
     pola per bulan & versi      facts.yaml pola_sentimen_rm3 (data/processed/review_scores.parquet) -->
