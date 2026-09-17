# MENGAPA SKEMA TIGA KELAS TIDAK LAYAK PADA DATASET INI

**Fase 4, T-4.6** · Sumber angka: `ml/src/three_class.py`,
`ml/artifacts/reports/three_class_linear_svc.json`, Gambar 7.

Keputusan H-3 membuang rating 3 dan memakai skema biner. Keputusan itu hanya
dapat dipertahankan di laporan bila ada bukti kuantitatif — bukan sekadar
pernyataan bahwa kelas netral kecil. Subbab ini menyediakan buktinya, dengan
menjalankan skema yang dibuang dan melaporkan hasilnya apa adanya.

## 1. Rancangan Eksperimen

Satu kali *run*, protokol identik dengan skema biner kecuali pelabelannya:

- label: `0 = negatif (1–2★)`, `1 = netral (3★)`, `2 = positif (4–5★)`
- seluruh 100.000 baris dipakai (tidak ada yang dibuang)
- split stratified 80:20 → 48.156 train (setelah dedup) / 20.000 test
- model: LinearSVC dengan parameter hasil tuning biner (`C=0.1`,
  `class_weight="balanced"`), TF-IDF identik

Parameter tidak di-*grid search* ulang. Alasannya dinyatakan terbuka: yang
membatasi di sini bukan *hyperparameter*, melainkan 2.595 contoh netral yang
tidak terpisahkan secara leksikal dari kelas negatif — dan Bagian 3 di bawah
menunjukkan mengapa.

## 2. Hasil

| Metrik | Biner (`linear_svc_tuned`) | Tiga kelas | Selisih |
|--------|----------------------------|------------|---------|
| macro-F1 | 0,9341 | **0,6470** | **−28,7 poin** |
| recall negatif | 0,9370 | 0,8949 | −4,2 poin |
| recall positif | 0,9496 | 0,9449 | −0,5 poin |
| **recall netral** | — | **0,1103** | — |

**Recall kelas netral 0,1103.** Dari 707 ulasan bintang 3 di test set, model
mengenali 78. Sisanya — 89% — jatuh ke kelas lain. Kelas netral pada dasarnya
tidak dipelajari.

Perhatikan bahwa recall negatif dan positif hampir tidak berubah. Kegagalan
terkonsentrasi seluruhnya pada kelas ketiga; macro-F1 turun 28,7 poin karena
rata-rata makro memberi bobot sama kepada kelas yang gagal total itu. Bila yang
dilaporkan hanya accuracy, kegagalan ini tidak akan terlihat sama sekali.

## 3. Ke Mana Ulasan Bintang 3 Jatuh — Gambar 7

Confusion matrix, baris = aktual:

| Aktual \ Prediksi | Negatif | Netral | Positif | Total |
|-------------------|---------|--------|---------|-------|
| **Negatif (1–2★)** | 4.784 | 228 | 334 | 5.346 |
| **Netral (3★)** | **474** | 78 | 155 | 707 |
| **Positif (4–5★)** | 611 | 157 | 13.179 | 13.947 |

Dari 707 ulasan bintang 3:

| Diprediksi | n | % |
|------------|---|---|
| **Negatif** | **474** | **67,0%** |
| Positif | 155 | 21,9% |
| Netral | 78 | 11,0% |

**Hipotesis Temuan 3 terkonfirmasi arah dan besarannya:** dua pertiga ulasan
bintang 3 diklasifikasikan sebagai negatif, tiga kali lebih sering daripada
sebagai positif.

## 4. Mengapa — Dua Argumen dengan Buktinya

### (a) Ketimpangan 1:20

| Kelas | Train | Test | Proporsi test |
|-------|-------|------|---------------|
| Negatif | 20.472 | 5.346 | 26,7% |
| **Netral** | **2.595** | **707** | **3,5%** |
| Positif | 25.089 | 13.947 | 69,7% |

Rasio netral terhadap positif adalah **1:19,7** di test set. `class_weight="balanced"`
sudah aktif dan tetap tidak cukup — pembobotan dapat mengoreksi *prior*, tetapi
tidak dapat menciptakan sinyal leksikal yang tidak ada.

### (b) Kemiripan panjang teks dengan kelas negatif

Panjang teks (`word_count`) pada test set:

| Kelas | n | rata-rata | median | std |
|-------|---|-----------|--------|-----|
| Negatif (1–2★) | 5.346 | 21,46 | 16,0 | 18,48 |
| **Netral (3★)** | **707** | **19,76** | **14,0** | **17,88** |
| Positif (4–5★) | 13.947 | 4,94 | 2,0 | 7,87 |

Inilah inti persoalannya. Ulasan netral rata-rata **19,76 kata** — praktis tidak
terbedakan dari ulasan negatif (21,46 kata), sementara ulasan positif hanya
4,94 kata. Pada representasi *bag-of-words*, panjang teks berkorelasi langsung
dengan jumlah token non-nol; ulasan netral karena itu menghasilkan vektor yang
menyerupai vektor kelas negatif.

Secara isi hal ini masuk akal: pengguna yang memberi bintang 3 umumnya menulis
keluhan disertai pengakuan, dan kosakata keluhannya sama dengan kosakata
pengguna bintang 1–2. Yang membedakan keduanya adalah derajat, bukan kata —
dan derajat itu tidak terwakili dalam TF-IDF.

## 5. Kesimpulan

Skema tiga kelas pada dataset ini tidak layak, dengan dua alasan yang keduanya
terukur: kelas netral hanya 3,5% dari data (rasio 1:20 terhadap positif), dan
secara leksikal maupun panjang teks ia tumpang tindih dengan kelas negatif
(19,76 vs 21,46 kata) sehingga tidak membentuk kelas yang terpisah.

Konsekuensinya recall netral 0,1103 dan macro-F1 turun 28,7 poin. Membuang
rating 3 bukan penyederhanaan demi angka yang bagus — ia pengakuan bahwa label
bintang 3 pada data ini tidak membawa sinyal yang cukup untuk dipelajari sebagai
kelas tersendiri.

**Yang harus dinyatakan sebagai keterbatasan:** 3.534 ulasan (3,5%) tidak
tercakup model produksi. Dalam penggunaan nyata, ulasan bernada campuran akan
dipaksa masuk salah satu dari dua kelas, dan eksperimen ini menunjukkan
sebagian besar akan diarahkan ke "negatif". Untuk triase keluhan arah bias itu
kebetulan aman — lebih baik keluhan bernada campuran ikut tertinjau daripada
terlewat — tetapi ia tetap bias, dan harus disebut sebagai bias, bukan fitur.
