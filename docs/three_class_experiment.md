# MENGAPA SKEMA TIGA KELAS TIDAK LAYAK PADA DATASET INI

**Fase 4, T-4.6** · Sumber angka: `ml/src/three_class.py`,
`ml/artifacts/reports/three_class_linear_svc.json`, `docs/synthesis/facts.yaml`
(`tiga_kelas`), Gambar 7. Data: scraping Google Play lima tahun (526.322
ulasan, Oktober 2021 – September 2026).

Penelitian ini membuang rating 3 dan memakai skema biner. Keputusan itu hanya
dapat dipertahankan di laporan bila ada bukti kuantitatif, bukan sekadar
pernyataan bahwa kelas netral kecil. Subbab ini menyediakan buktinya, dengan
menjalankan skema yang dibuang dan melaporkan hasilnya apa adanya.

## 1. Rancangan Eksperimen

Satu kali *run*, protokol identik dengan skema biner kecuali pelabelannya:

- label: `0 = negatif (1–2★)`, `1 = netral (3★)`, `2 = positif (4–5★)`
- seluruh 526.322 baris dipakai (tidak ada yang dibuang)
- split stratified 80:20 → 237.626 train (setelah deduplikasi) / 105.265 test
- model: LinearSVC dengan parameter hasil tuning biner (`C=0.1`,
  `class_weight="balanced"`), TF-IDF identik

Parameter tidak di-*grid search* ulang. Alasannya dinyatakan terbuka: yang
membatasi di sini bukan *hyperparameter*, melainkan contoh netral yang tidak
terpisahkan secara leksikal dari kelas negatif. Bagian 4 di bawah menunjukkan
mengapa.

## 2. Hasil

| Metrik | Biner (`linear_svc_tuned`) | Tiga kelas | Selisih |
|--------|----------------------------|------------|---------|
| macro-F1 | 0,9270 | **0,6617** | **−26,5 poin** |
| accuracy | 0,9389 | 0,8864 | −5,3 poin |
| recall negatif | 0,9237 | 0,8686 | −5,5 poin |
| recall positif | 0,9451 | 0,9368 | −0,8 poin |
| **recall netral** | — | **0,1872** | — |
| presisi netral | — | 0,2066 | — |

**Recall kelas netral 0,1872.** Dari 4.423 ulasan bintang 3 di test set, model
mengenali 828. Sisanya, 81%, jatuh ke kelas lain. Presisinya pun hanya 0,2066:
dari 4.008 ulasan yang diprediksi netral, hanya 828 yang memang bintang 3. Kelas
netral pada dasarnya tidak dipelajari.

Kegagalan terkonsentrasi pada kelas ketiga. macro-F1 turun 26,5 poin karena
rata-rata makro memberi bobot sama kepada kelas yang hampir gagal total itu
(F1 netral 0,1964). Recall positif hampir tidak berubah. Recall negatif turun
5,5 poin, dan penurunan itu hampir seluruhnya disebabkan ulasan negatif yang
kini diprediksi netral (1.861 baris, 6,4% dari negatif). Bila yang dilaporkan
hanya accuracy (0,8864), kegagalan ini nyaris tidak terlihat.

## 3. Ke Mana Ulasan Bintang 3 Jatuh — Gambar 7

Confusion matrix, baris = aktual:

| Aktual \ Prediksi | Negatif | Netral | Positif | Total |
|-------------------|---------|--------|---------|-------|
| **Negatif (1–2★)** | 25.350 | 1.861 | 1.974 | 29.185 |
| **Netral (3★)** | **2.425** | 828 | 1.170 | 4.423 |
| **Positif (4–5★)** | 3.208 | 1.319 | 67.130 | 71.657 |

Dari 4.423 ulasan bintang 3:

| Diprediksi | n | % |
|------------|---|---|
| **Negatif** | **2.425** | **54,8%** |
| Positif | 1.170 | 26,5% |
| Netral | 828 | 18,7% |

**Hipotesis Temuan 3 terkonfirmasi arahnya:** lebih dari separuh ulasan bintang
3 diklasifikasikan sebagai negatif, dua kali lebih sering daripada sebagai
positif.

## 4. Mengapa — Dua Argumen dengan Buktinya

### (a) Ketimpangan kelas

| Kelas | Train (setelah dedup) | Test | Proporsi test |
|-------|-----------------------|------|---------------|
| Negatif | 109.396 | 29.185 | 27,7% |
| **Netral** | **15.447** | **4.423** | **4,2%** |
| Positif | 112.783 | 71.657 | 68,1% |

Rasio netral terhadap positif adalah **1:16,2** di test set. Di data latih,
setelah deduplikasi membuang banyak pujian pendek berulang, rasionya 1:7,3, dan
kelas netral hanya 6,5% dari data latih. `class_weight="balanced"` sudah aktif
dan tetap tidak cukup. Pembobotan dapat mengoreksi *prior*, tetapi tidak dapat
menciptakan sinyal leksikal yang tidak ada.

### (b) Kemiripan panjang teks dengan kelas negatif

Panjang teks (`word_count`) pada test set:

| Kelas | n | rata-rata | median | std |
|-------|---|-----------|--------|-----|
| Negatif (1–2★) | 29.185 | 20,57 | 15,0 | 18,11 |
| **Netral (3★)** | **4.423** | **17,86** | **12,0** | **17,50** |
| Positif (4–5★) | 71.657 | 4,76 | 2,0 | 7,69 |

Inilah inti persoalannya. Ulasan netral rata-rata **17,86 kata**, jauh lebih
dekat ke ulasan negatif (20,57 kata) daripada ke ulasan positif (4,76 kata).
Pada representasi *bag-of-words*, panjang teks berkorelasi langsung dengan
jumlah token non-nol; ulasan netral karena itu menghasilkan vektor yang
menyerupai vektor kelas negatif.

Secara isi hal ini masuk akal: pengguna yang memberi bintang 3 umumnya menulis
keluhan disertai pengakuan, dan kosakata keluhannya sama dengan kosakata
pengguna bintang 1–2. Yang membedakan keduanya adalah derajat, bukan kata, dan
derajat itu tidak terwakili dalam TF-IDF.

## 5. Kesimpulan

Skema tiga kelas pada dataset ini tidak layak, dengan dua alasan yang keduanya
terukur. Pertama, kelas netral hanya 4,2% dari data (rasio 1:16,2 terhadap
positif di test set). Kedua, secara leksikal maupun panjang teks ia tumpang
tindih dengan kelas negatif (17,86 vs 20,57 kata), sehingga tidak membentuk
kelas yang terpisah.

Konsekuensinya recall netral 0,1872 dan macro-F1 turun 26,5 poin. Membuang
rating 3 bukan penyederhanaan demi angka yang bagus. Ia pengakuan bahwa label
bintang 3 pada data ini tidak membawa sinyal yang cukup untuk dipelajari sebagai
kelas tersendiri.

**Yang harus dinyatakan sebagai keterbatasan:** 22.114 ulasan (4,2%) tidak
tercakup model produksi. Dalam penggunaan nyata, ulasan bernada campuran akan
dipaksa masuk salah satu dari dua kelas, dan eksperimen ini menunjukkan
sebagian besar akan diarahkan ke "negatif". Untuk triase keluhan arah bias itu
kebetulan aman, karena lebih baik keluhan bernada campuran ikut tertinjau
daripada terlewat. Namun ia tetap bias, dan harus disebut sebagai bias, bukan
fitur.
