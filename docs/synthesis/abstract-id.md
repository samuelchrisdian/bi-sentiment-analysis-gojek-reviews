# Abstrak (Bahasa Indonesia)

<!-- ===== Abstrak ID — SIAP TEMPEL ===== -->

Ulasan pengguna di toko aplikasi adalah sumber umpan balik berskala besar yang
tidak terstruktur, sehingga keluhan yang berulang sulit dideteksi secara
sistematis. Penelitian ini menganalisis 100.000 ulasan aplikasi Gojek di Google
Play Store periode 21 Mei 2024 – 31 Desember 2025 dengan membandingkan tiga
keluarga algoritma klasik dalam empat varian terlatih — ComplementNB,
MultinomialNB, LinearSVC, dan LogisticRegression — di atas representasi TF-IDF
1–2 gram, memakai skema label biner yang diturunkan dari rating bintang, serta
menerapkan protokol evaluasi ganda pada test set penuh dan pada subset ulasan
berisi minimal lima kata. Model produksi (LogisticRegression) mencapai macro-F1
0,9336 dan recall kelas negatif 0,9315 pada test set penuh terhadap baseline
kelas mayoritas 0,4196, sementara rentang macro-F1 keempat varian hanya 1,88
poin sehingga model paling sederhana setara dengan yang paling kompleks.
Temuan metodologis utamanya adalah selisih 2,59 poin macro-F1 dan 3,70 poin
akurasi antara kedua set evaluasi: karena 39,9% ulasan hanya berisi dua kata
atau kurang dan hampir seluruhnya positif, metrik pada test set penuh
melebih-lebihkan kemampuan model, dan pemeriksaan manual menunjukkan 48,0%
kesalahan model justru berasal dari rating bintang yang bertentangan dengan isi
ulasannya. Ekstraksi topik LDA atas 26.732 ulasan negatif menghasilkan sembilan
kategori keluhan dengan dua teratas — ketersediaan mitra driver (36,15%) dan
pesanan GoFood beserta pembatalannya (34,25%) — menyentuh 70,4% korpus keluhan,
sehingga laporan ini menyarankan evaluasi ganda sebagai praktik standar pada
korpus ulasan aplikasi dan penggunaan sistem sebagai alat triase keluhan, bukan
sebagai pengganti pembacaan manusia.

**Kata kunci:** analisis sentimen; bahasa Indonesia; ulasan aplikasi;
ketidakseimbangan kelas; TF-IDF; pemodelan topik LDA.

---

<!-- Rujukan angka:
     macro-F1 & recall           docs/tables/model_metrics.csv
     rentang antar-model         facts.yaml model.rentang_macro_f1_tuned
     selisih evaluasi ganda      facts.yaml model.produksi
     39,9% ulasan pendek         docs/tables/ulasan_pendek.csv
     48,0% label keliru          docs/tables/error_analysis_50_reviewed.csv
     peringkat topik             docs/tables/topics_ranked.csv          -->
