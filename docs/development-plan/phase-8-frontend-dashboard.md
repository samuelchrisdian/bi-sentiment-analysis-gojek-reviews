# FASE 8 — Dashboard Frontend (Vue 3)

**Estimasi:** 3 hari
**Prasyarat:** Fase 7 selesai (7 endpoint berjalan)
**Output utama:** dashboard interaktif satu halaman
**📌 Fase ini yang dipotong lebih dulu bila waktu menipis — bukan Fase 4 atau 5**

---

## 1. Objective

Menyajikan hasil analisis dalam bentuk yang bisa dieksplorasi, bukan sekadar
dibaca. Susunannya mengikuti rancangan Gambar 7 dokumen storytelling.

Tiga hal yang membedakan dashboard ini dari kumpulan grafik biasa:

1. **Filter global yang konsisten** — mengubah periode harus memengaruhi
   seluruh grafik sekaligus, bukan sebagian.
2. **Drill-down** — mengklik batang topik membuka ulasan nyata di baliknya.
   Ini yang mengubah angka menjadi bukti.
3. **Panel perbandingan model yang menampilkan `full` vs `informative_ge5w`
   berdampingan** — temuan metodologis utama harus terlihat, bukan tersembunyi
   di lampiran.

---

## 2. Technical Tasks

### T-8.1 — Scaffold proyek

```bash
npm create vite@latest web -- --template vue
cd web && npm install
npm install pinia axios echarts vue-echarts date-fns
```

Struktur:

```
web/src/
├── api/client.js            # instance axios + base URL dari env
├── stores/filters.js        # Pinia: periode, versi, kategori
├── stores/data.js           # Pinia: cache respons + status loading
├── components/
│   ├── KpiRow.vue
│   ├── TrendChart.vue
│   ├── TopicsChart.vue
│   ├── VersionChart.vue
│   ├── ReviewTable.vue
│   ├── ModelComparison.vue
│   ├── PredictDemo.vue
│   ├── FilterBar.vue
│   ├── LoadingState.vue
│   └── EmptyState.vue
├── views/DashboardView.vue
└── main.js
```

### T-8.2 — Pinia store untuk filter global

Satu sumber kebenaran untuk seluruh filter. Setiap komponen grafik
mengamati store ini, tidak menyimpan state filter sendiri.

```js
// stores/filters.js
export const useFilters = defineStore("filters", {
  state: () => ({
    from: "2024-06-01",     // default: kecualikan Mei 2024 (periode parsial)
    to: "2025-12-31",
    versiMinor: null,
    kategoriId: null,
    granularity: "month",
    modelName: "linear_svc",
  }),
  getters: {
    queryParams: (s) => ({ from: s.from, to: s.to, granularity: s.granularity }),
  },
});
```

Catatan: default `from` sengaja dimulai Juni 2024, dengan tombol
"Sertakan Mei 2024 (periode parsial)" yang eksplisit. Keputusan metodologis
Temuan 6 diwujudkan langsung di UI.

### T-8.3 — Komponen per sumber data

| Komponen | Endpoint | Jenis visual | Catatan |
|----------|----------|--------------|---------|
| `KpiRow` | `/api/kpi` | 4 kartu angka | Total ulasan, % negatif, rata-rata rating, jumlah versi |
| `TrendChart` | `/api/trend` | Garis, **sumbu ganda** | Kiri: % negatif; kanan: volume. Mei 2024 diarsir bila disertakan |
| `TopicsChart` | `/api/topics` | Batang horizontal | Klik batang → set `kategoriId` → buka `ReviewTable` |
| `VersionChart` | `/api/versions` | Batang bertumpuk | Keterangan wajib: ambang ≥100 & 21,9% versi kosong |
| `ReviewTable` | `/api/topics/{id}/reviews` | Tabel berpaginasi | Urut Likes desc; tampilkan teks asli |
| `ModelComparison` | `/api/model/metrics` | Batang berkelompok + tabel | Tampilkan `full` vs `informative_ge5w`; garis baseline 72,3% |
| `PredictDemo` | `/api/predict` | Textarea + kartu hasil | Tampilkan teks hasil preprocessing |

### T-8.4 — ECharts: konfigurasi yang perlu diperhatikan

ECharts dipilih di atas Chart.js karena dua alasan konkret: dukungan
*time series* dengan sumbu ganda, dan event klik yang memudahkan drill-down.

**Sumbu ganda pada `TrendChart`:**

```js
yAxis: [
  { type: "value", name: "% Negatif", min: 0, max: 100,
    axisLabel: { formatter: "{value}%" } },
  { type: "value", name: "Volume Ulasan" },
],
series: [
  { name: "% Negatif", type: "line", yAxisIndex: 0, smooth: true },
  { name: "Volume",    type: "bar",  yAxisIndex: 1, itemStyle: { opacity: 0.3 } },
]
```

**Drill-down pada `TopicsChart`:**

```js
chart.on("click", (params) => {
  filters.kategoriId = topics.value[params.dataIndex].id;
  nextTick(() => reviewTableRef.value?.scrollIntoView({ behavior: "smooth" }));
});
```

**Anotasi periode parsial:**

```js
markArea: {
  data: [[{ xAxis: "2024-05" }, { xAxis: "2024-05" }]],
  itemStyle: { color: "rgba(255,173,177,0.3)" },
  label: { formatter: "Periode parsial" },
}
```

### T-8.5 — Loading & empty state untuk setiap grafik

Tiga state per komponen, tidak boleh ada yang dilewati:

- **Loading:** skeleton atau spinner, bukan layar kosong.
- **Empty:** ketika filter menghasilkan 0 baris → pesan jelas
  ("Tidak ada ulasan pada rentang ini") + tombol reset filter.
- **Error:** pesan + tombol coba lagi. Jangan biarkan grafik kosong tanpa penjelasan.

Buat `LoadingState.vue` dan `EmptyState.vue` sebagai komponen bersama, lalu
gunakan lewat `<slot>` — mencegah tujuh implementasi berbeda.

### T-8.6 — Catatan metodologis yang tampil di UI

Ini yang membedakan dashboard akademik dari dashboard biasa. Cantumkan sebagai
teks kecil di bawah grafik terkait, **diambil dari respons API** (metadata di
T-7.3), bukan di-*hardcode*:

- Di bawah `VersionChart`: *"Hanya versi dengan ≥100 ulasan (66 versi, 96,4% data berversi). 21,9% ulasan tidak mencantumkan versi aplikasi dan dikecualikan dari grafik ini."*
- Di bawah `TrendChart`: *"Mei 2024 merupakan periode parsial (mulai 21 Mei) dan dikecualikan secara default."*
- Di panel `ModelComparison`: *"Baseline mayoritas = 72,3% akurasi. Set `informative_ge5w` mencakup ulasan dengan ≥5 kata."*
- Di `PredictDemo`: *"Endpoint demo. Data dashboard berasal dari pre-scoring batch, bukan inferensi real-time."*

### T-8.7 — Responsif & tambahkan service `web`

Layout: grid 12 kolom, turun ke 1 kolom di bawah 768px. Panggil
`chart.resize()` pada event resize window — ECharts tidak melakukannya otomatis.

```yaml
  web:
    build: ./web
    depends_on: [api]
    ports:
      - "5173:80"
    environment:
      VITE_API_BASE: http://localhost:8000
```

---

## 3. Deliverables / Output

| Artefak | Lokasi | Keterangan |
|---------|--------|------------|
| Proyek Vue 3 + Vite | `web/` | Struktur sesuai T-8.1 |
| 7 komponen grafik | `web/src/components/` | Satu per sumber data |
| Pinia stores | `web/src/stores/` | `filters.js`, `data.js` |
| `DashboardView.vue` | `web/src/views/` | Layout sesuai Gambar 7 |
| `Dockerfile` + nginx conf | `web/` | Build produksi |
| Service `web` | `docker-compose.yml` | Port 5173 |
| Tangkapan layar dashboard | `docs/figures/` | Resolusi tinggi untuk laporan (Gambar 7) |

---

## 4. Definition of Done

- [ ] `npm run build` selesai tanpa error dan tanpa warning yang diabaikan.
- [ ] Ketujuh komponen menampilkan data nyata dari API (bukan data dummy).
- [ ] **Filter periode memengaruhi seluruh grafik secara konsisten** — diuji dengan mengubah rentang dan memverifikasi keempat grafik ikut berubah.
- [ ] **Klik batang topik membuka tabel ulasan terkait** dan tabel ter-scroll ke tampilan.
- [ ] Tabel ulasan terurut Likes desc dan berpaginasi; menampilkan teks ulasan asli.
- [ ] Panel perbandingan model menampilkan `full` dan `informative_ge5w` **berdampingan**, dengan garis baseline 72,3%.
- [ ] Kotak demo prediksi bekerja dan menampilkan teks hasil preprocessing.
- [ ] Setiap grafik punya loading state dan empty state yang berfungsi (diuji dengan filter yang menghasilkan 0 baris).
- [ ] Catatan metodologis (ambang versi, null 21,9%, periode parsial, baseline) tampil di UI dan **bersumber dari respons API**.
- [ ] **Tidak ada error atau warning di konsol browser** saat memuat dan berinteraksi.
- [ ] Layout tetap terbaca pada lebar 768px.
- [ ] Tangkapan layar resolusi tinggi tersimpan untuk laporan.
- [ ] Commit ditag `phase-8-done`.

---

## 5. Risiko & Catatan

| Risiko | Dampak | Mitigasi |
|--------|--------|----------|
| Waktu habis di styling | Sedang | **Lingkup minimum** bila mepet: KPI + Trend + Topics + tabel drill-down. Sisanya opsional |
| Grafik tidak resize saat window berubah | Rendah | Panggil `chart.resize()` pada `window.resize` |
| Filter tidak konsisten antar komponen | Sedang | Satu Pinia store; komponen tidak boleh punya state filter sendiri |
| Terlalu banyak request saat filter berubah | Rendah | Debounce 300ms + cache di `data.js` store |
| Catatan metodologis di-hardcode lalu tidak sinkron | Sedang | Ambil dari metadata respons API (sudah disiapkan di Fase 7) |

### Lingkup minimum bila waktu menipis

Bila sisa waktu < 1,5 hari, kerjakan hanya ini dan nyatakan pemotongannya di README:

1. `KpiRow` — 4 angka
2. `TrendChart` — tren bulanan
3. `TopicsChart` + `ReviewTable` — drill-down (**ini yang paling bernilai demo**)
4. `ModelComparison` — tabel statis, tanpa grafik

Yang dipotong: `VersionChart`, `PredictDemo`, filter versi/kategori.
Nilai akademiknya tetap utuh — keempat komponen di atas sudah menjawab RM1 dan RM2.
