# KETERBATASAN PENELITIAN

**Fase 9, T-9.6** · Seluruh angka bersumber dari `docs/tables/*.csv` dan dokumen
temuan yang dirujuk di tiap poin — tidak ada yang ditulis dari ingatan.

Dokumen ini bukan pengakuan kelemahan. Ia membedakan laporan yang bisa
dipertanggungjawabkan dari laporan yang mengklaim lebih dari yang dibuktikan.
Setiap poin di bawah menyatakan **apa** batasnya, **seberapa besar** (dengan
angka), dan **apa konsekuensinya** bagi penafsiran hasil.

---

## 1. Label sentimen diturunkan dari rating bintang, bukan anotasi manusia

Label negatif/positif dipetakan otomatis dari bintang (1–2★ → negatif, 4–5★ →
positif). Rating bintang adalah **proksi**, bukan label sentimen teks.

Pemeriksaan manual 50 kesalahan model (`docs/error_analysis.md` §3.1)
menunjukkan **48% di antaranya adalah label yang keliru dari pengguna** — bintang
yang bertentangan dengan isi tulisan. Arahnya sangat timpang: 22 dari 24 kasus
adalah pengguna yang memberi 4–5★ sambil menulis keluhan (5★ "aplikasinya sering
lemot"), hanya 2 kasus sebaliknya.

**Konsekuensi:** sebagian "kesalahan" model sebenarnya prediksi yang benar atas
label yang salah. Diekstrapolasi, ≈499 baris (2,59%) dari 19.294 baris test
membawa bintang yang bertentangan dengan teksnya, sehingga **plafon akurasi
realistis pada dataset ini ≈0,9741 — bukan 1,000**. Akurasi model produksi
0,9459 karena itu setara **97,1% dari plafon**, dan sisa ruang perbaikan bukan
5,4 poin melainkan ≈2,8 poin. Estimasi ini berasal dari sampel 50 baris dengan
selang kepercayaan lebar (Wilson 95%: 1,88%–3,31%) dan diambil hanya dari baris
yang salah diklasifikasikan, sehingga merupakan **batas bawah** derau label.

## 2. 39,9% ulasan hanya berisi ≤2 kata — metrik pada test set penuh optimistis

Sebanyak **39.859 ulasan (39,9%)** hanya berisi dua kata atau kurang, dan hampir
seluruhnya positif: ulasan 5★ rata-rata **4,4 kata**, sementara 1★ mencapai
**20,8 kata**. Mengevaluasi hanya pada test set penuh berarti menghitung
"bagus" → positif sebagai keberhasilan klasifikasi.

**Konsekuensi:** setiap model dilaporkan pada dua set evaluasi, dan selisihnya
adalah ukuran dari melebih-lebihkan tersebut. Pada model produksi
(LogisticRegression):

| Set evaluasi | n | macro-F1 | recall negatif | akurasi |
|--------------|---|----------|----------------|---------|
| `full` | 19.294 | 0,9336 | 0,9316 | 0,9459 |
| `informative_ge5w` (≥5 kata) | 8.696 | 0,9078 | 0,9536 | 0,9089 |
| **Selisih** | — | **−2,59 poin** | +2,20 poin | −3,70 poin |

Angka `informative_ge5w` adalah ukuran kemampuan yang sesungguhnya pada teks
yang membawa informasi. Setiap klaim kinerja dalam laporan ini harus dibaca
berpasangan, bukan hanya angka `full`-nya.

## 3. Kelas netral (3★) dikeluarkan dari model utama

Rating 3★ hanya **3.534 ulasan (3,5%)** — rasio **1:19** terhadap kelas positif.
Kelas ini dibuang dari skema utama, sehingga model **tidak dapat mengenali
sentimen netral sama sekali**: setiap ulasan 3★ yang masuk akan dipaksa menjadi
negatif atau positif.

Keputusan ini tidak diambil berdasarkan asumsi. Varian 3 kelas dijalankan dengan
protokol identik dan **gagal seperti diprediksi**: macro-F1 **0,6470** vs
**0,9341** pada skema biner — turun **28,7 poin**
(`docs/three_class_experiment.md`, Gambar 7). Penyebabnya bukan
*hyperparameter*, melainkan contoh netral yang tidak terpisahkan secara leksikal
dari kelas negatif.

## 4. 21,9% ulasan tidak mencantumkan versi aplikasi

Sebanyak **21.910 baris (21,9%)** memiliki `Versi App` kosong dan **tidak
diimputasi** — imputasi versi tidak punya dasar yang dapat dipertahankan.
Dari 291 versi unik, analisis per-versi dibatasi pada versi dengan **≥100
ulasan**: 66 versi yang mencakup **96,4%** dari data berversi.

**Konsekuensi:** analisis per-versi berlaku atas ≈75.247 ulasan, bukan atas
100.000. Perbandingan antar-versi tidak boleh digeneralisasi ke seluruh korpus,
dan seperlima data yang tak berversi mungkin tidak acak (misalnya terkonsentrasi
pada kanal atau periode tertentu) — hal yang tidak dapat diuji dari data yang
tersedia.

## 5. Pelabelan kategori topik bersifat manual dan subjektif

Sembilan kategori keluhan dibentuk dengan memetakan topik LDA (k=9, coherence
c_v tertinggi 0,5763) ke label bisnis secara **manual**. Validasi silang atas
sampel berlabel manusia menghasilkan **Cohen's κ = 0,4621** — tingkat *moderate*
menurut Landis & Koch (1977), **bukan substantial**
(`docs/topic_labeling_rules.md`, `docs/tables/h9_hasil_kesepakatan.csv`).

Angka ini dilaporkan apa adanya. Kata kunci pemetaan **tidak** diperbaiki
setelah melihat hasil validasi, karena memperbaikinya akan membatalkan κ = 0,4621
sebagai validasi independen — angka tersebut sah hanya sebagai validasi atas
versi pipeline yang benar-benar diuji.

**Konsekuensi:** peringkat kategori keluhan harus dibaca sebagai **indikasi arah,
bukan pengukuran presisi**. Selisih peringkat yang kecil (misalnya antara
kategori ke-3 dan ke-4, 6.939 vs 6.916 ulasan) berada di dalam derau pelabelan
dan tidak boleh ditafsirkan sebagai perbedaan nyata.

## 6. Data statis satu periode — tidak ada evaluasi *concept drift*

Korpus mencakup satu rentang tetap: **21 Mei 2024 – 31 Desember 2025** (20
bulan, 100.000 baris). Model dilatih dan diuji dengan *split* acak berstratifikasi
atas rentang yang sama, **bukan** dengan *split* temporal.

**Konsekuensi:** tidak ada bukti bagaimana kinerja model bertahan terhadap
perubahan kosakata pengguna, fitur aplikasi baru, atau pergeseran pola keluhan di
luar periode ini. Klaim kinerja berlaku untuk periode tersebut saja. Evaluasi
*concept drift* menuntut *split* berbasis waktu dan data periode berikutnya —
keduanya di luar lingkup penelitian ini.

Ditambah lagi, karena dataset berasal dari unggahan pihak ketiga di Kaggle,
metode pengambilan datanya tidak terdokumentasi: parameter *scraping*, filter
bahasa, apakah ini sensus atau sampel, dan kemungkinan penyaringan oleh
pengunggah **tidak dapat diverifikasi** (`docs/data_provenance_notes.md`).
Ketiga hal itu lazim pada penelitian berbasis data sekunder dan tidak
membatalkan analisis — asalkan dinyatakan.

## 7. Sistem tidak di-*deploy* ke produksi

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
| 1 | Label dari bintang, bukan anotasi manusia | 48% kesalahan = label keliru; plafon akurasi ≈0,974 |
| 2 | Ulasan sangat pendek mendominasi | 39,9% ≤2 kata; selisih evaluasi 2,59 poin macro-F1 |
| 3 | Kelas netral dikeluarkan | 3,5% data; varian 3 kelas −28,7 poin macro-F1 |
| 4 | Versi aplikasi tidak lengkap | 21,9% kosong; cakupan analisis 96,4% data berversi |
| 5 | Pelabelan topik subjektif | Cohen's κ = 0,4621 (*moderate*) |
| 6 | Data statis, sumber sekunder | 20 bulan, tanpa *split* temporal; provenans tak terverifikasi |
| 7 | Prototipe, bukan produksi | 3 container lokal; tanpa auth/monitoring/retraining |
