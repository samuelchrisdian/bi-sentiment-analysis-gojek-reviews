# INDEKS GAMBAR & TABEL — Fase 10, T-10.5

Peta dari setiap gambar dan tabel ke lokasi pemakaiannya di naskah, lengkap
dengan keterangan yang sudah tertulis. Gunanya: saat menyusun ke Word atau LaTeX,
tidak perlu menelusuri ulang gambar mana milik bagian mana, dan keterangan gambar
tidak perlu dikarang ulang saat menempel.

Seluruh gambar berada di `docs/figures/final/` pada 300 dpi. Seluruh tabel berada
di `docs/tables/`. Naskah merujuk gambar dengan path relatif
`../figures/final/<berkas>`, yang benar bila naskah dibaca dari
`docs/synthesis/`.

---

## 1. Gambar

| ID | Berkas | Dipakai di | Keterangan gambar (siap tempel) |
|----|--------|-----------|---------------------------------|
| Gambar 1 | `gambar-01-distribusi-rating.png` | §4.1 | Distribusi rating 1–5 bintang pada 100.000 ulasan. Dua ujung skala menguasai 87,9% data. |
| Gambar 2 | `gambar-02-panjang-per-rating.png` | §4.1, §5.1, artikel populer | Rata-rata jumlah kata per rating. Ulasan bintang 5 rata-rata 4,4 kata; bintang 1 mencapai 20,8 kata. |
| Gambar 3 | `gambar-03-distribusi-wordcount.png` | §4.1 | Distribusi jumlah kata per ulasan. 39,9% ulasan berisi dua kata atau kurang. |
| Gambar 4 | `gambar-04-volume-bulanan.png` | §4.1 | Volume ulasan bulanan dan rata-rata rating, Mei 2024 – Desember 2025 (20 bulan). Mei 2024 adalah periode parsial. |
| Gambar 5 | `gambar-05-cakupan-versi.png` | §4.1 | Cakupan analisis per versi aplikasi pada beberapa ambang minimum ulasan. Ambang 100 mencakup 96,4% data berversi. |
| Gambar 6 | `gambar-06-confusion-matrix.png` | §4.2 | Confusion matrix model produksi (LogisticRegression) pada test set penuh, n=19.294. |
| Gambar 6b | `gambar-06b-confusion-matrix-linear-svc.png` | Lampiran C | Confusion matrix LinearSVC hasil tuning — model yang menjadi sumber 50 sampel analisis kesalahan. |
| Gambar 7 | `gambar-07-tiga-kelas.png` | §5.4 | Confusion matrix skema tiga kelas. Dari 707 ulasan bintang 3, hanya 78 dikenali sebagai netral. |
| Gambar 8 | `gambar-08-lda-coherence.png` | §4.4 | Koherensi `c_v` LDA pada rentang k=5 sampai k=12. Tertinggi pada k=9 (0,5763). |
| Gambar 8b | `gambar-08b-ngram-negatif.png` | §4.4 | Unigram dan bigram teratas pada korpus ulasan negatif. Kata `tidak` muncul di 59,0% dokumen, `pengemudi` di 38,0%. |
| Gambar 9 | `gambar-09-peringkat-topik.png` | §4.4, artikel populer | Peringkat sembilan kategori keluhan berdasarkan jumlah ulasan negatif. |
| Gambar 10 | `gambar-10-perbandingan-model.png` | §4.2 | Perbandingan macro-F1 empat varian model pada dua set evaluasi, terhadap baseline kelas mayoritas. |
| Gambar 11 | `gambar-11-selisih-evaluasi.png` | §4.3, artikel populer | Selisih skor antara set `full` dan `informative_ge5w`. Pada model produksi, macro-F1 turun 2,59 poin. |
| Gambar 12 | `gambar-12-waktu-latih.png` | §4.2 | Waktu latih per model setelah tuning, dalam detik. |
| Gambar 13 | `gambar-13-dashboard.png` | Lampiran A | Tangkapan layar dashboard: penelusuran dari kategori keluhan sampai teks ulasan asli. |

**Gambar yang dipakai di artikel populer (maksimal tiga):** Gambar 2, Gambar 11,
Gambar 9 — dalam urutan itu.

---

## 2. Tabel yang dirujuk naskah

| ID | Berkas | Dipakai di | Isi |
|----|--------|-----------|-----|
| Tabel 1 | `profil_dataset.csv` | §3.1 | Profil dataset: jumlah baris, periode, SHA-256, nilai kosong per kolom. |
| Tabel 2 | `distribusi_rating.csv` | §4.1 | Distribusi rating 1–5 beserta persentasenya. |
| Tabel 3 | `panjang_per_rating.csv` | §4.1, §5.1 | Rata-rata dan median jumlah kata per rating. |
| Tabel 4 | `ulasan_pendek.csv` | §4.1, §5.1 | Jumlah ulasan ≤2 kata dan ≥5 kata. |
| Tabel 5 | `kontras_kelas.csv` | §3.6, §4.1, §5.1 | Kontras kelas negatif vs positif: duplikasi teks dan proporsi ulasan sangat pendek. |
| Tabel 6 | `komposisi_kelas.csv` | §3.3 | Komposisi kelas pada skema biner dan tiga kelas. |
| Tabel 7 | `duplikasi.csv` | §4.1 | Duplikat baris penuh dan duplikat teks ulasan. |
| Tabel 8 | `teks_paling_berulang.csv` | §4.1, §5.1, artikel populer | 20 teks ulasan yang paling sering berulang. |
| Tabel 9 | `volume_bulanan.csv` | §4.1 | Volume ulasan dan rata-rata rating per bulan. |
| Tabel 10 | `cakupan_versi.csv` | §4.1, §6 | Cakupan analisis per versi pada beberapa ambang. |
| Tabel 11 | `profil_likes.csv` | §4.1 | Statistik deskriptif kolom Likes. |
| Tabel 12 | `model_metrics.csv` | §4.2, §4.3, §5.1, §7.1 | Metrik seluruh model × dua set evaluasi — tabel inti laporan. |
| Tabel 13 | `gridsearch_results.csv` | §4.3 | 24 kombinasi GridSearchCV beserta skor latih, skor validasi, dan selisihnya. |
| Tabel 14 | `error_analysis_50_reviewed.csv` | §5.2 | 50 kesalahan model beserta kategori penyebab hasil pemeriksaan manusia. |
| Tabel 15 | `top_features.csv` | §5.3 | 20 fitur berbobot tertinggi per kelas untuk keempat model. |
| Tabel 16 | `ngram_negatif.csv` | §4.4, §7.2 | Unigram dan bigram teratas pada korpus negatif. |
| Tabel 17 | `lda_coherence.csv` | §3.6, §4.4 | Koherensi LDA untuk k=5 sampai k=12. |
| Tabel 18 | `topics_ranked.csv` | §4.4, §5.5, §7.2 | Peringkat sembilan kategori keluhan menurut frekuensi dan Likes. |
| Tabel 19 | `topic_trend_monthly.csv` | §4.4, §5.5 | Tren bulanan per kategori keluhan, 180 baris. |
| Tabel 20 | `tabel3_storytelling_topik.csv` | artikel populer | Kategori keluhan beserta tiga contoh ulasan nyata per kategori. |
| Tabel 21 | `h9_hasil_kesepakatan.csv` | §3.6, §4.4, §6 | Data mentah validasi silang pelabelan kategori (Cohen's κ). |

---

## 3. Berkas lain yang dirujuk naskah

| Berkas | Dipakai di | Keterangan |
|--------|-----------|------------|
| `ml/config.yaml` | §3.4, Lampiran B | Seluruh parameter proyek dalam satu berkas. |
| `ml/artifacts/MANIFEST.json` | §3.1, §3.4, Lampiran B | Hash data, snapshot konfigurasi, versi pustaka, seluruh metrik. |
| `ml/artifacts/best_params.json` | §4.3 | Parameter terpilih grid dan hasil seleksi satu simpangan baku. |
| `ml/artifacts/reports/three_class_linear_svc.json` | §5.4 | Laporan lengkap eksperimen tiga kelas. |
| `ml/artifacts/reports/logistic_regression_final_full.json` | §4.2 | Laporan klasifikasi model produksi pada set penuh. |
| `docs/data_provenance_notes.md` | §3.1, §6 | Provenans dataset dan keterbatasan yang menyertainya. |
| `docs/preprocessing_validation.md` | §3.2, §5.3 | Validasi preprocessing tiga putaran. |
| `docs/model_decision.md` | §4.2, §7.1 | Keputusan model produksi beserta pertimbangannya. |
| `docs/error_analysis.md` | §5.2, Lampiran C | Analisis kesalahan dan interpretasi fitur. |
| `docs/three_class_experiment.md` | §3.3, §5.4 | Eksperimen skema tiga kelas. |
| `docs/limitations.md` | §6 | Tujuh keterbatasan beserta ukurannya. |
| `docs/openapi.json` | Lampiran A, B | Spesifikasi API. |
| `docs/tables/token_normalisasi_terisi.csv` | Lampiran B | Kamus normalisasi slang hasil pemetaan manusia. |
| `docs/synthesis/facts.yaml` | seluruh naskah | Sumber angka tunggal, dihasilkan `python -m ml.src.collect_facts`. |

---

## 4. Urutan penempelan yang disarankan

Naskah `research-paper.md` memuat penanda `<!-- ===== §x … — SIAP TEMPEL ===== -->`
di awal setiap bagian, sehingga dapat dipotong per bagian. Urutan yang paling
sedikit menimbulkan pekerjaan ulang:

1. §3 Metodologi dan §4 Hasil lebih dulu — keduanya memuat seluruh tabel dan
   gambar, sehingga penomoran gambar di dokumen utama langsung terkunci.
2. §5 Pembahasan dan §6 Keterbatasan, yang merujuk balik ke penomoran itu.
3. §7 Kesimpulan.
4. §1 Pendahuluan dan §0 Abstrak **paling akhir**, setelah seluruh angka final
   terpasang di dokumen utama.
5. §2 Tinjauan Pustaka dan §8 Daftar Pustaka dikerjakan penulis sepenuhnya, dari
   sumber yang benar-benar dibaca.
