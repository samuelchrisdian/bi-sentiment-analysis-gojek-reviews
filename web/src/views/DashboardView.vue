<script setup>
import { computed, defineAsyncComponent, nextTick, onMounted, ref, watch } from "vue";
import { storeToRefs } from "pinia";

import { useFilters } from "../stores/filters";
import { useData } from "../stores/data";

import FilterBar from "../components/FilterBar.vue";
import CardPanel from "../components/CardPanel.vue";
import DataTable from "../components/DataTable.vue";
import LoadingState from "../components/LoadingState.vue";
import EmptyState from "../components/EmptyState.vue";
import KpiRow from "../components/KpiRow.vue";
import ReviewTable from "../components/ReviewTable.vue";
import PredictDemo from "../components/PredictDemo.vue";

/* Keempat komponen ini yang menarik ECharts (557 kB, bagian terbesar bundel).
   Dimuat async supaya cangkang dashboard, KPI, dan tabel ulasan sudah bisa
   tampil sebelum mesin grafik selesai diunduh. */
const asinkron = (muat) =>
  defineAsyncComponent({ loader: muat, loadingComponent: LoadingState, delay: 120 });

const TrendChart = asinkron(() => import("../components/TrendChart.vue"));
const TopicsChart = asinkron(() => import("../components/TopicsChart.vue"));
const VersionChart = asinkron(() => import("../components/VersionChart.vue"));
const ModelComparison = asinkron(() => import("../components/ModelComparison.vue"));

import { ribuan, persen, desimal, labelPeriode } from "../theme";

const f = useFilters();
const d = useData();
const { res } = storeToRefs(d);

const LIMIT_TOPIK = 20;
const tabelRef = ref(null);
const sortUlasan = ref("likes");
const halaman = ref(1);

/* --- pemuatan ------------------------------------------------------------
   Debounce 300ms hanya untuk sumber yang terikat filter tanggal: input
   <type=date> memancarkan perubahan pada setiap ketikan digit tahun, dan
   tanpa jeda itu berarti belasan request untuk satu suntingan. Sumber yang
   tidak terikat filter dimuat sekali tanpa jeda. */
function muatTerfilter() {
  if (f.from > f.to) return;   // FilterBar sudah menampilkan pesannya
  const opsi = { debounce: 300 };
  d.muat("kpi", "/api/kpi", { ...f.rentang }, opsi);
  d.muat("trend", "/api/trend", { ...f.rentang, granularity: f.granularity }, opsi);
  d.muat("topics", "/api/topics", { ...f.rentang, limit: LIMIT_TOPIK }, opsi);
}

function muatUlasan() {
  if (f.kategoriId === null) return;
  d.muat("reviews", `/api/topics/${f.kategoriId}/reviews`,
         { sort_by: sortUlasan.value, page: halaman.value });
}

onMounted(() => {
  muatTerfilter();
  d.muat("versions", "/api/versions", {});
  d.muat("metrics", "/api/model/metrics", {});
});

watch(() => [f.from, f.to, f.granularity], muatTerfilter);
watch(() => [f.kategoriId, sortUlasan.value, halaman.value], muatUlasan);

/* --- drill-down ---------------------------------------------------------- */
async function pilihTopik(id, nama) {
  f.pilihKategori(id, nama);
  halaman.value = 1;
  await nextTick();
  tabelRef.value?.scrollIntoView({ behavior: "smooth", block: "start" });
}

function gantiSort(k) {
  sortUlasan.value = k;
  halaman.value = 1;
}

/* --- kembaran tabel ------------------------------------------------------ */
const kolomTrend = computed(() => [
  { kunci: "periode", label: "Periode",
    fmt: (v, r) => labelPeriode(v, f.granularity) + (r.periode_parsial ? " (parsial)" : "") },
  { kunci: "total_ulasan", label: "Volume", angka: true, fmt: ribuan },
  { kunci: "jumlah_negatif", label: "Negatif", angka: true, fmt: ribuan },
  { kunci: "persen_negatif", label: "% Negatif", angka: true, fmt: (v) => persen(v) },
  { kunci: "rata_rating", label: "Rata rating", angka: true, fmt: (v) => desimal(v) },
]);

const kolomTopik = [
  { kunci: "kategori", label: "Kategori" },
  { kunci: "jumlah_ulasan", label: "Ulasan", angka: true, fmt: ribuan },
  { kunci: "persen_negatif", label: "% Negatif", angka: true, fmt: (v) => persen(v) },
  { kunci: "total_likes", label: "Likes", angka: true, fmt: ribuan },
  { kunci: "rata_rating", label: "Rata rating", angka: true, fmt: (v) => desimal(v) },
];

const kolomVersi = [
  { kunci: "versi_minor", label: "Versi" },
  { kunci: "total_ulasan", label: "Ulasan", angka: true, fmt: ribuan },
  { kunci: "jumlah_negatif", label: "Negatif", angka: true, fmt: ribuan },
  { kunci: "persen_negatif", label: "% Negatif", angka: true, fmt: (v) => persen(v) },
  { kunci: "pertama_muncul", label: "Pertama muncul",
    fmt: (v) => new Date(v).toLocaleDateString("id-ID",
      { day: "numeric", month: "short", year: "numeric" }) },
];

const modelProduksi = computed(() =>
  res.value.kpi.data?.model_produksi ?? res.value.metrics.data?.model_produksi ?? "—");
</script>

<template>
  <div class="halaman">
    <header class="kepala">
      <div>
        <h1>Analisis Sentimen Ulasan Gojek</h1>
        <p class="sub">
          100.000 ulasan Google Play · model produksi
          <b>{{ modelProduksi }}</b>
        </p>
      </div>
    </header>

    <FilterBar />

    <!-- KPI -------------------------------------------------------------- -->
    <section class="blok">
      <LoadingState v-if="res.kpi.status === 'loading' && !res.kpi.data" :tinggi="120" />
      <EmptyState
        v-else-if="res.kpi.status === 'error'" jenis="error"
        :pesan="res.kpi.pesan" :tinggi="120"
        @ulangi="d.ulangi('kpi', '/api/kpi', { ...f.rentang })"
      />
      <EmptyState
        v-else-if="res.kpi.status === 'empty'" :pesan="res.kpi.pesan" :tinggi="120"
        @reset="f.reset()"
      />
      <div v-else-if="res.kpi.data" :class="{ 'is-memuat': res.kpi.status === 'loading' }">
        <KpiRow :kpi="res.kpi.data" />
        <ul class="notes notes--kpi">
          <li v-for="(c, i) in res.kpi.data.catatan" :key="i">{{ c }}</li>
        </ul>
      </div>
    </section>

    <!-- Tren ------------------------------------------------------------- -->
    <CardPanel
      judul="Tren sentimen antarwaktu"
      sub="Proporsi negatif dan volume ulasan pada satu sumbu waktu bersama."
      :slot="res.trend" :tinggi="360" ada-tabel
      @reset="f.reset()"
      @ulangi="d.ulangi('trend', '/api/trend', { ...f.rentang, granularity: f.granularity })"
    >
      <template #default="{ tabel }">
        <DataTable
          v-if="tabel" :kolom="kolomTrend" :baris="res.trend.data.data"
          caption="Nilai tren per periode"
        />
        <TrendChart v-else :trend="res.trend.data" />
      </template>

      <template #catatan-tambahan>
        <p class="nota-desain">
          Dua ukuran ini digambar sebagai dua panel bertumpuk yang berbagi satu sumbu
          waktu, bukan sebagai satu plot bersumbu-y ganda: penjajaran dua skala berbeda
          pada satu bidang membuat perpotongan garis tampak bermakna padahal
          penempatannya sembarang.
        </p>
      </template>
    </CardPanel>

    <!-- Topik + drill-down ----------------------------------------------- -->
    <CardPanel
      judul="Kategori keluhan"
      sub="Klik satu batang untuk membuka ulasan nyata di baliknya."
      :slot="res.topics" :tinggi="320" ada-tabel
      @reset="f.reset()"
      @ulangi="d.ulangi('topics', '/api/topics', { ...f.rentang, limit: LIMIT_TOPIK })"
    >
      <template #default="{ tabel }">
        <DataTable
          v-if="tabel" :kolom="kolomTopik" :baris="res.topics.data.data"
          caption="Peringkat kategori keluhan"
        />
        <TopicsChart
          v-else :topics="res.topics.data" :terpilih="f.kategoriId"
          @pilih="pilihTopik"
        />
      </template>
    </CardPanel>

    <section ref="tabelRef" class="card panel-ulasan">
      <header class="panel__head">
        <div>
          <h2 class="card__title">
            Ulasan
            <template v-if="f.kategoriNama">— {{ f.kategoriNama }}</template>
          </h2>
          <p class="card__sub">Teks asli, belum melewati pipeline preprocessing.</p>
        </div>
        <button v-if="f.kategoriId !== null" class="mini" @click="f.pilihKategori(null, null)">
          Tutup
        </button>
      </header>

      <p v-if="f.kategoriId === null" class="ajakan">
        Pilih satu kategori pada grafik di atas untuk melihat ulasan yang menyusunnya.
      </p>

      <template v-else>
        <LoadingState v-if="res.reviews.status === 'loading' && !res.reviews.data" :tinggi="260" />
        <EmptyState
          v-else-if="res.reviews.status === 'error'" jenis="error"
          :pesan="res.reviews.pesan"
          @ulangi="d.ulangi('reviews', `/api/topics/${f.kategoriId}/reviews`,
                            { sort_by: sortUlasan, page: halaman })"
        />
        <EmptyState
          v-else-if="res.reviews.status === 'empty'" :pesan="res.reviews.pesan"
          @reset="f.reset()"
        />
        <div v-else-if="res.reviews.data"
             :class="{ 'is-memuat': res.reviews.status === 'loading' }">
          <ReviewTable
            :reviews="res.reviews.data"
            @sort="gantiSort" @halaman="(p) => (halaman = p)"
          />
          <p class="nota-desain">
            Daftar ulasan tidak mengikuti filter tanggal: endpoint
            <code>/api/topics/{id}/reviews</code> tidak menerima parameter rentang,
            sehingga yang tampil adalah seluruh ulasan kategori ini.
          </p>
        </div>
      </template>
    </section>

    <!-- Versi ------------------------------------------------------------ -->
    <CardPanel
      judul="Sentimen per versi aplikasi"
      sub="Diurut menurut kemunculan pertama, bukan menurut peringkat."
      :slot="res.versions" :tinggi="340" ada-tabel
      @reset="f.reset()" @ulangi="d.ulangi('versions', '/api/versions', {})"
    >
      <template #default="{ tabel }">
        <DataTable
          v-if="tabel" :kolom="kolomVersi" :baris="res.versions.data.data"
          caption="Sentimen per versi minor"
        />
        <VersionChart v-else :versions="res.versions.data" />
      </template>

      <template #catatan-tambahan>
        <p class="nota-desain">
          Grafik ini mencakup seluruh periode dan <b>tidak mengikuti filter tanggal</b>:
          agregat versi dilayani dari materialized view yang tidak menyimpan dimensi
          waktu. Menggambarnya seolah terfilter akan menyesatkan.
        </p>
      </template>
    </CardPanel>

    <!-- Perbandingan model ----------------------------------------------- -->
    <CardPanel
      judul="Perbandingan model"
      sub="Kedua eval set dilaporkan berdampingan dan harus dibaca bersama."
      :slot="res.metrics" :tinggi="320" ada-tabel
      @reset="f.reset()" @ulangi="d.ulangi('metrics', '/api/model/metrics', {})"
    >
      <template #default="{ tabel }">
        <ModelComparison :metrics="res.metrics.data" :tabel="tabel" />
      </template>
    </CardPanel>

    <!-- Demo prediksi ----------------------------------------------------- -->
    <section class="card">
      <header class="panel__head">
        <div>
          <h2 class="card__title">Coba prediksi</h2>
          <p class="card__sub">Menjalankan pipeline preprocessing yang sama dengan saat pelatihan.</p>
        </div>
      </header>
      <PredictDemo />
    </section>

    <footer class="kaki">
      Angka pada dashboard berasal dari pre-scoring batch (Fase 6). Seluruh catatan
      metodologis di bawah tiap grafik dibaca dari respons API, tidak ditulis ulang
      di frontend.
    </footer>
  </div>
</template>

<style scoped>
.halaman {
  max-width: 1280px;
  margin: 0 auto;
  padding: 26px 24px 56px;
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.kepala h1 { font-size: 22px; }
.sub { margin: 4px 0 0; font-size: 13px; color: var(--text-secondary); }

.blok { display: block; }

.is-memuat { opacity: .45; transition: opacity .15s ease; }

.notes--kpi {
  border-top: none;
  padding-top: 12px;
  margin-top: 10px;
}

.panel-ulasan { scroll-margin-top: 16px; }

.panel__head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 12px;
}

.mini { font-size: 12px; padding: 4px 9px; }

.ajakan {
  margin: 0;
  padding: 34px 0;
  text-align: center;
  font-size: 13px;
  color: var(--text-muted);
}

.nota-desain {
  margin: 12px 0 0;
  font-size: 12px;
  line-height: 1.45;
  color: var(--text-muted);
}

.nota-desain code {
  font-family: ui-monospace, "SFMono-Regular", Menlo, monospace;
  font-size: 11px;
}

.kaki {
  margin-top: 6px;
  font-size: 12px;
  color: var(--text-muted);
  line-height: 1.5;
}

@media (max-width: 768px) {
  .halaman { padding: 18px 16px 40px; gap: 14px; }
}

@media (prefers-reduced-motion: reduce) {
  .is-memuat { transition: none; }
}
</style>
