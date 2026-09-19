# Dashboard Frontend — Fase 8

Vue 3 + Vite + Pinia + ECharts. Menyajikan hasil Fase 1–7 lewat tujuh sumber
data API.

## Menjalankan

```bash
# pengembangan (API harus sudah jalan di :8000)
npm install && npm run dev            # http://localhost:5173

# produksi
npm run build && npx vite preview --port 4173

# seluruh tumpukan
docker compose up -d --build          # dashboard di http://localhost:5173
```

`VITE_API_BASE` di-*inline* saat build, bukan dibaca saat container jalan —
karena itu ia diteruskan sebagai **build arg** di `docker-compose.yml`, bukan
sebagai `environment:`.

## Pemeriksaan asap

`npm run smoke` menjalankan Playwright terhadap build yang sedang disajikan dan
memverifikasi butir Definition of Done yang hanya bisa dibuktikan di peramban
nyata: konsistensi filter, drill-down, paginasi, empty state, kebersihan konsol,
dan layout 768px.

```bash
npm run build && npx vite preview --port 4173 &
npm run smoke                                    # atau SMOKE_URL=http://localhost:5173
```

## Tiga penyimpangan dari rencana Fase 8

Semuanya disengaja dan tampil apa adanya di UI.

**1. `TrendChart` bukan bersumbu-y ganda.** Rencana meminta satu plot dengan
skala kiri (% negatif) dan kanan (volume). Dua skala berbeda pada satu bidang
membuat titik potong antar-seri tampak bermakna padahal penjajarannya
sepenuhnya sembarang. Yang dipakai: **dua panel bertumpuk yang berbagi satu
sumbu waktu** dengan `axisPointer` tertaut — perbandingan bentuk antarwaktu
tetap utuh, korelasi palsunya hilang.

**2. Garis baseline per eval set, bukan satu angka 72,3%.** Rencana menyebut
"garis baseline 72,3%". Angka itu hanya berlaku untuk eval set `full`; pada
`informative_ge5w` baseline mayoritas turun ke 46,5% (akurasi) / 31,7%
(macro F1). Satu garis untuk dua panel akan salah di salah satunya, jadi tiap
panel menggambar baseline miliknya sendiri, dibaca dari respons API.

**3. Filter versi & kategori tidak dibuat.** Tidak ada endpoint Fase 7 yang
menerimanya, sehingga kontrolnya hanya akan menjadi kontrol mati. Dua
konsekuensinya dinyatakan sebagai catatan di bawah komponen terkait:

- `/api/versions` tidak menerima parameter tanggal (materialized view
  `agg_version` tidak menyimpan dimensi waktu) → `VersionChart` **tidak**
  mengikuti filter periode.
- `/api/topics/{id}/reviews` juga tidak menerima rentang → daftar ulasan
  drill-down mencakup seluruh periode.

Model produksi adalah `logistic_regression_final`, bukan `linear_svc` seperti
yang tertulis pada contoh store di dokumen rencana; nilainya tidak pernah
ditulis keras di frontend melainkan dibaca dari respons API.

## Catatan desain

- **Satu Pinia store untuk filter.** Tidak ada komponen grafik yang menyimpan
  state filter sendiri; `stores/filters.js` adalah satu-satunya sumber.
- **Catatan metodologis selalu dari `catatan` pada respons API.** Tidak ada
  ambang, persentase, atau nama model yang ditulis ulang di frontend.
- **Palet sudah divalidasi.** Warna diambil dari palet rujukan `dataviz` dan
  lulus pemeriksaan pemisahan buta-warna pada mode terang maupun gelap. Mode
  gelap adalah langkah yang dipilih untuk permukaan gelap, bukan pembalikan
  otomatis.
- **Setiap grafik punya kembaran tabel** (tombol "Tabel"): tidak ada nilai yang
  hanya bisa dibaca lewat tooltip atau lewat warna.
- **Refetch menahan render sebelumnya** pada opacity turun alih-alih mengganti
  skeleton, supaya layout tidak melompat saat filter digeser.
