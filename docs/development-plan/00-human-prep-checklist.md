# CHECKLIST PERSIAPAN MANUSIA
## Pekerjaan yang tidak bisa didelegasikan ke agent

**Baca sebelum menjalankan Fase 0.**

Dokumen ini memisahkan dua jenis pekerjaan yang sering tercampur:

- **Pekerjaan agent** — menulis kode, menjalankan pipeline, menghasilkan angka.
  Seluruhnya ada di `phase-0` sampai `phase-10`.
- **Pekerjaan manusia** — keputusan, verifikasi, penilaian domain, dan hal-hal
  yang memerlukan akses atau otoritas yang tidak dimiliki agent.

Agent bisa menulis seluruh sistem. Yang tidak bisa dilakukannya: memastikan
data ini benar-benar berasal dari mana, memutuskan apakah "gk" berarti "tidak"
dalam konteks ulasan Gojek, atau menilai apakah sebuah klaster kata pantas
disebut "Mitra Driver". Pekerjaan itu milik Anda, dan kualitas laporan akhir
bergantung padanya.

---

## BAGIAN A — Blocker sebelum mulai · ✅ SELURUHNYA SELESAI

> Dilaporkan dan dikunci pada **16 September 2026**. Agent memakai keputusan di
> bawah sebagai fakta; tidak perlu bertanya ulang.

### H-1 · Provenans dataset — ✅ SELESAI

**Jawaban: (a) Unduhan langsung dari Kaggle, tanpa modifikasi.**

- Dataset: *Gojek App Reviews Indonesia — Google Play Store*, pengunggah `pandaa12`, **versi 1**
- URL: `https://www.kaggle.com/datasets/pandaa12/gojek-app-reviews-indonesia-google-play-store/versions/1?resource=download`
- Berkas dipakai apa adanya; peneliti tidak melakukan transformasi apa pun

Rincian lengkap beserta konsekuensi metodologis dan keterbatasannya:
**`docs/data_provenance_notes.md`**.

Implikasi yang sudah terjawab: penamaan kolom berbahasa Indonesia berasal dari
pengunggah Kaggle, **bukan** hasil *rename* oleh peneliti. Bab 1 tetap perlu
direvisi (Temuan 1), tetapi sebagai koreksi asumsi — bukan sebagai langkah
transformasi yang belum tercatat.

---

### H-2 · Prasyarat environment — ✅ SELESAI (versi lebih baru, terverifikasi aman)

| Komponen | Prasyarat rencana | Terpasang | Status |
|----------|-------------------|-----------|--------|
| Python | 3.11 | **3.12.3** (pip 24.0) | ✅ Dipakai sebagai target resmi |
| Node | 20 | **24.19.0** | ✅ Aman untuk Vite + Vue 3 |
| Docker Compose | v2+ | **v5.5.0** | ✅ Terverifikasi dari binernya |
| Port 5433 | bebas | kosong | ✅ |

**Verifikasi kompatibilitas sudah dijalankan, bukan diasumsikan.** Dua paket
yang paling berisiko terhadap kenaikan versi Python dicek ketersediaan
wheel-nya untuk CPython 3.12:

```
gensim-4.3.3-cp312-cp312-manylinux_2_17_x86_64.whl   ✅ tersedia
numpy-1.26.4-cp312-cp312-manylinux_2_17_x86_64.whl   ✅ tersedia
```

**Kesimpulan: seluruh versi di `ml/requirements.txt` dipertahankan apa adanya.**
Tidak ada paket yang perlu dinaikkan. `numpy` tetap dikunci di `1.26.4` karena
`gensim` 4.3.x menuntut `numpy<2` — batasan ini tidak berubah oleh Python 3.12.

Satu penyesuaian yang mengikuti: `Dockerfile` di `api/` memakai
**`python:3.12-slim`**, bukan `3.11-slim`, agar runtime container sama dengan
runtime tempat artefak `.joblib` dibuat.

---

### H-3 · Skema biner vs 3 kelas — ✅ SELESAI: **BINER**

**Keputusan: skema biner sebagai model utama.** `labeling.scheme: binary`
di `ml/config.yaml` sudah benar, tidak perlu diubah.

**Konteks yang mengubah cara pelaporan:** proyek ini adalah **tugas independen,
bukan tesis.** Tidak ada dosen pembimbing atau sidang. Ruang lingkup ditentukan
sendiri oleh pemilik proyek.

Konsekuensi bagi agent:

- Alasan pengeluaran kelas netral tetap **wajib didokumentasikan** di bab
  metodologi — bukan demi penguji, melainkan demi kejujuran metodologis.
  Justifikasinya: penyederhanaan fokus ke sentimen positif–negatif, diperkuat
  bukti rasio 1:20 dan kemiripan panjang teks bintang 3 dengan kelas negatif.
- Varian 3 kelas (Fase 4, T-4.6) **tetap dijalankan** sebagai eksperimen
  pembanding. Biayanya satu kali *run*, dan hasilnya memperkuat justifikasi
  keputusan biner — bukan sekadar formalitas akademik.
- Hilangkan bahasa berorientasi sidang ("penguji akan menanyakan", "saat
  sidang") dari naskah keluaran Fase 10. Pembacanya adalah pembaca laporan
  teknis independen.

---

### H-4 · Naskah — ✅ SELESAI: **dikelola di luar repositori**

Naskah utama berada di dokumen terpisah, di luar git.

Konsekuensi bagi agent — **penting, mengubah beberapa tugas:**

- Agent **tidak pernah mengedit naskah utama.** Tidak ada file naskah di repo
  yang perlu disinkronkan.
- Keluaran Fase 10 berbentuk `.md` berisi data, tabel, dan draf narasi, yang
  **ditempel manual** oleh manusia ke dokumen utama. Karena itu: tabel ditulis
  sebagai tabel markdown (bukan gambar), dan gambar dirujuk dengan path relatif
  yang jelas agar mudah dilampirkan.
- **Slot `[A-1]`…`[A-24]` dan `[T-…]` tidak ada di repositori.** Fase 1 tetap
  menghasilkan `docs/tables/angka_storytelling.csv` sebagai *tabel rujukan
  angka* untuk ditempel manual — bukan untuk mengisi slot di file yang tidak
  ada. Pemeriksaan placeholder di Fase 9 (T-9.5) hanya berlaku untuk berkas di
  dalam `docs/`, bukan untuk naskah eksternal.

---

## BAGIAN B — Pekerjaan manusia di dalam fase

Tugas berikut ada di dalam fase, tetapi **tidak bisa dikerjakan agent**.
Anggarkan waktunya secara terpisah dari estimasi fase.

---

### ⛔ PROTOKOL GERBANG BERHENTI (mengikat agent)

Lima titik di bawah adalah **gerbang berhenti wajib**. Agent **berhenti
bekerja** di titik itu, menyerahkan berkas, dan **menunggu balasan manusia**.
Agent tidak boleh menebak, mengisi sendiri, atau melanjutkan ke langkah
berikutnya dengan nilai sementara.

| Gerbang | Fase | Agent menyerahkan | Agent menunggu | Baru boleh lanjut ke |
|---------|------|-------------------|----------------|----------------------|
| **H-5** | 2 | `docs/tables/unknown_tokens_500.csv` | kolom `bentuk_baku` terisi | normalisasi slang → preprocessing |
| **H-6** | 2 | `docs/tables/preprocessing_sample_100.csv` | lampu hijau verifikasi manual | penulisan `reviews_clean.parquet` final |
| **H-7** | 4 | `docs/tables/error_analysis_50.csv` | kolom `kategori_penyebab` terisi | penulisan `docs/error_analysis.md` |
| **H-8** | 5 | klaster LDA + 20 kata + 10 dokumen contoh per topik | nama kategori bisnis + aturan pemetaan | pengisian tabel `topics` & `review_topics` |
| **H-9** | 5 | sampel 50 ulasan **tanpa label** | label independen dari rekan | perhitungan skor kesepakatan |

**Bentuk pemberhentian yang benar.** Saat mencapai gerbang, agent mengakhiri
giliran dengan pesan yang memuat empat hal:

1. Berkas yang diserahkan beserta path lengkapnya
2. Apa persisnya yang harus diisi manusia (nama kolom, format nilai)
3. Perkiraan waktu pengerjaan manusia
4. Pernyataan eksplisit bahwa pekerjaan dihentikan sampai ada balasan

Contoh yang benar:

> ⛔ **GERBANG H-5 — menunggu input manusia.**
> Berkas siap: `docs/tables/unknown_tokens_500.csv` (500 baris).
> Mohon isi kolom `bentuk_baku` untuk setiap token; kosongkan bila token
> sebaiknya dibuang. Prioritaskan 40 baris teratas — seluruhnya varian negasi.
> Estimasi ±3 jam. **Fase 2 dihentikan di sini sampai berkas dikembalikan.**

**Yang dilarang:** mengisi `bentuk_baku` dengan tebakan lalu "nanti
dikonfirmasi"; memakai kamus slang bawaan sebagai pengganti sementara;
menamai kategori topik sendiri "sebagai contoh"; melewati H-6 karena
sampelnya "terlihat baik-baik saja". Setiap pelanggaran menghasilkan angka
yang tidak bisa dipertanggungjawabkan di laporan akhir.

**Gerbang non-blocking.** H-10 (keputusan model produksi) dan H-11 (pemeriksaan
naskah) tidak menghentikan pipeline, tetapi agent wajib **mengingatkan secara
eksplisit** saat titiknya tercapai, dan tidak boleh mengklaim keputusan sudah
diambil bila manusia belum menyatakannya.

---

### H-5 · Pemetaan kamus slang (Fase 2) 🔴
**Estimasi: 3–4 jam · pekerjaan manusia terbesar di proyek ini**

Agent bisa mengekstrak 500 token tak dikenal beserta frekuensinya. Yang tidak
bisa dilakukannya adalah memutuskan bahwa `gk` = `tidak`, `bgt` = `banget`,
dan `otw` = `dalam perjalanan` — itu pengetahuan bahasa sehari-hari.

- [ ] Agent menghasilkan `docs/tables/unknown_tokens_500.csv`
- [ ] Anda mengisi kolom `bentuk_baku` baris per baris
- [ ] **Prioritaskan varian negasi lebih dulu** (`gk`, `ga`, `gak`, `nggak`,
      `gbs`, `blm`, …). Salah di sini merusak kelas negatif — kelas yang jadi
      fokus seluruh penelitian
- [ ] Tandai token yang tidak perlu dipetakan (nama orang, typo unik) sebagai buang

**Ini adalah kontribusi keilmuan yang Anda klaim di Bab 1.** Membosankan,
tidak bisa diotomatisasi, dan berdampak langsung pada kualitas model.

---

### H-6 · Verifikasi 100 sampel preprocessing (Fase 2) 🔴
**Estimasi: 45 menit**

- [ ] Buka `docs/tables/preprocessing_sample_100.csv`
- [ ] Periksa kolom before/after satu per satu
- [ ] Cari: teks bermakna yang jadi kosong; negasi yang hilang; slang yang lolos
- [ ] Laporkan temuan ke agent untuk diperbaiki, lalu **periksa ulang**

Agent bisa menghitung berapa baris jadi kosong. Ia tidak bisa menilai apakah
ulasan yang jadi kosong itu memang tidak bermakna atau justru korban bug.

---

### H-7 · Analisis kesalahan 50 kasus (Fase 4) 🔴
**Estimasi: 1,5–2 jam · nilai akademik tertinggi per jam kerja**

- [ ] Buka `docs/tables/error_analysis_50.csv`
- [ ] Baca setiap ulasan, isi kolom `kategori_penyebab` (sarkasme, negasi
      kompleks, campur kode, label keliru, terlalu pendek, off-topic,
      kegagalan preprocessing)
- [ ] Tandai temuan mengejutkan — biasanya: banyak "kesalahan" model sebenarnya
      adalah rating pengguna yang tidak sesuai isi ulasannya

Menilai apakah sebuah ulasan bernada sarkastik adalah penilaian manusia.
Subbab ini biasanya yang paling banyak ditanya saat sidang.

---

### H-8 · Pelabelan kategori topik (Fase 5) 🔴
**Estimasi: 2–3 jam**

- [ ] Agent menghasilkan klaster LDA + 20 kata teratas + 10 dokumen contoh per topik
- [ ] Anda memetakan setiap klaster ke kategori bisnis (Pembayaran, Mitra Driver,
      Performa Aplikasi, Tarif & Promo, Layanan Pelanggan, Akurasi Lokasi)
- [ ] Tuliskan **aturan pemetaan** yang Anda pakai — bukan hanya hasilnya
- [ ] Tambah/ubah kategori bila hasil nyata menuntut demikian; enam kategori di
      config adalah hipotesis awal, bukan kebenaran

---

### H-9 · Validasi silang pelabelan oleh rekan (Fase 5) 🟡
**Estimasi: 1 jam (Anda) + 1 jam (rekan)**

- [ ] Cari satu rekan yang bersedia melabeli 50 ulasan secara independen
- [ ] Beri dia definisi kategori, **jangan beri label Anda**
- [ ] Hitung tingkat kesepakatan (persentase, atau Cohen's κ)
- [ ] Laporkan angkanya apa adanya, termasuk bila rendah

Ini mengubah pelabelan dari "subjektif" menjadi "subjektif tetapi terukur" —
perbedaan yang berarti di mata penguji. Hubungi rekan Anda **sekarang**, jangan
saat Fase 5 sudah berjalan.

---

### H-10 · Keputusan model produksi (Fase 4) 🟡
**Estimasi: 30 menit**

Agent menyajikan angka; keputusan tetap milik Anda:

- [ ] LinearSVC unggul macro-F1 ≥2 poin → jadikan model produksi
- [ ] Selisih <2 poin → pilih model yang lebih sederhana dan mudah dijelaskan
- [ ] Apa pun hasilnya → keempat model tetap dilaporkan

Tuliskan alasannya di `docs/model_decision.md`. Bila hasilnya di perbatasan,
diskusikan dengan pembimbing sebelum memutuskan.

---

### H-11 · Pemeriksaan naskah akhir (Fase 9–10) 🔴
**Estimasi: 2–3 jam**

- [ ] Baca seluruh keluaran Fase 10 sebagai pembaca, bukan sebagai penulis
- [ ] Verifikasi setiap angka terhadap `docs/tables/` — jangan percaya begitu saja
- [ ] Pastikan tidak ada klaim yang melebihi bukti
- [ ] Pastikan tidak ada kalimat yang tidak Anda pahami — bila Anda tidak bisa
      menjelaskannya dengan kalimat sendiri, hapus atau tulis ulang
- [ ] Tempel bagian yang sudah diverifikasi ke dokumen utama (di luar repo, per H-4)

> **Catatan penting:** naskah yang dihasilkan Fase 10 adalah **draf berbasis
> angka nyata**, bukan tulisan siap serah. Tanggung jawab atas isinya ada pada
> Anda sebagai penulis.

---

## BAGIAN C — Keputusan yang sebaiknya diambil sekarang

Empat hal berikut tidak memblokir, tetapi mengubahnya di tengah jalan mahal.
Putuskan sekarang, catat jawabannya.

| # | Pertanyaan | Default rencana ini | Jawaban Anda |
|---|-----------|--------------------|--------------|
| K-1 | Berapa hari kerja realistis yang Anda punya? | ≈16 hari paruh waktu | |
| K-2 | Apakah dashboard (Fase 8) benar-benar dituntut, atau cukup grafik statis di laporan? | Dituntut, tapi dipotong pertama bila waktu habis | |
| K-3 | Apakah ada tenggat sidang/seminar yang mengunci tanggal? | — | |
| K-4 | Bahasa naskah akhir: Indonesia saja, atau perlu artikel versi Inggris? | Indonesia; Fase 10 dapat menyiapkan abstrak Inggris | |

Bila jawaban K-1 di bawah 10 hari, baca ulang bagian "Aturan Pemotongan
Lingkup" di `00-roadmap-index.md` **sebelum** memulai, bukan di tengah jalan.

---

## Ringkasan Beban Kerja Manusia

| Tahap | Tugas | Estimasi |
|-------|-------|----------|
| ~~Sebelum mulai~~ | ~~H-1 provenans, H-2 environment, H-3 skema label, H-4 naskah~~ | ✅ selesai |
| Fase 2 | H-5 kamus slang, H-6 verifikasi sampel | ±4,5 jam |
| Fase 4 | H-7 analisis kesalahan, H-10 keputusan model | ±2,5 jam |
| Fase 5 | H-8 pelabelan topik, H-9 validasi rekan | ±4 jam |
| Fase 9–10 | H-11 pemeriksaan naskah | ±3 jam |
| | **Sisa** | **≈14 jam kerja manusia** |

Angka ini **di luar** waktu menunggu agent bekerja. Jadwalkan sebagai blok
waktu tersendiri — terutama H-5, H-7, dan H-8, yang menuntut konsentrasi penuh
dan tidak bisa dikerjakan sambil mengerjakan hal lain.

---

## Status & Tindakan Berikutnya

**Bagian A selesai seluruhnya (16 September 2026).** Fase 0 boleh dijalankan
sekarang.

Yang masih terbuka dan sebaiknya dibereskan sebelum Fase 2 dimulai:

1. **Hubungi calon rekan untuk H-9** — satu-satunya tugas yang bergantung pada
   ketersediaan orang lain. Jadwalkan sekarang meski baru dipakai di Fase 5.
2. **Jawab K-1 sampai K-4** di tabel Bagian C — terutama K-1 (berapa hari kerja
   yang realistis), karena menentukan apakah Fase 8 dipotong atau tidak.
3. **Blokir waktu untuk H-5** (±3 jam, pemetaan kamus slang). Ini gerbang
   berhenti pertama dan akan tiba cepat — Fase 2 dimulai hanya dua fase lagi.

Urutan fase berikutnya: Fase 0 → 1 → 2 (berhenti di H-5).
