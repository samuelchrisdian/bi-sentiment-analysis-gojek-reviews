<script setup>
import { computed } from "vue";
import { useFilters, TANGGAL_MIN, TANGGAL_MAX, AWAL_PENUH } from "../stores/filters";

const f = useFilters();

const galatRentang = computed(() => (f.from > f.to ? "Tanggal mulai melewati tanggal akhir." : ""));

const PRESET = [
  { label: "Seluruh periode penuh", from: AWAL_PENUH, to: TANGGAL_MAX },
  { label: "2025 saja", from: "2025-01-01", to: TANGGAL_MAX },
  { label: "6 bulan terakhir", from: "2025-07-01", to: TANGGAL_MAX },
];

const presetAktif = (p) => f.from === p.from && f.to === p.to;
</script>

<template>
  <!-- Satu baris filter di atas segalanya yang dicakupnya. Tidak ada komponen
       grafik yang menyimpan state filter sendiri. -->
  <div class="filter card">
    <div class="grup">
      <label class="field">
        Dari
        <input type="date" v-model="f.from" :min="TANGGAL_MIN" :max="TANGGAL_MAX" />
      </label>
      <label class="field">
        Sampai
        <input type="date" v-model="f.to" :min="TANGGAL_MIN" :max="TANGGAL_MAX" />
      </label>
      <label class="field">
        Granularitas
        <select v-model="f.granularity">
          <option value="month">Bulanan</option>
          <option value="week">Mingguan</option>
        </select>
      </label>
    </div>

    <div class="grup">
      <div class="preset">
        <button
          v-for="p in PRESET" :key="p.label"
          class="toggle mini" :aria-pressed="String(presetAktif(p))"
          @click="f.setRentang(p.from, p.to)"
        >{{ p.label }}</button>
      </div>

      <!-- Keputusan metodologis Temuan 6 sebagai sakelar eksplisit, bukan
           sebagai baris yang dihapus diam-diam dari data. -->
      <button
        class="toggle mini mei" :aria-pressed="String(f.sertakanMei)"
        @click="f.toggleMei()"
      >Sertakan Mei 2024 (parsial)</button>

      <button class="mini" :disabled="!f.tidakDefault" @click="f.reset()">Atur ulang</button>
    </div>

    <p v-if="galatRentang" class="galat" role="alert">{{ galatRentang }}</p>
  </div>
</template>

<style scoped>
.filter {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 16px;
  flex-wrap: wrap;
  padding: 14px 18px;
}

.grup { display: flex; align-items: flex-end; gap: 10px; flex-wrap: wrap; }

.preset { display: flex; gap: 6px; flex-wrap: wrap; }

.mini { font-size: 12px; padding: 6px 10px; }
.mei { max-width: 100%; }

.mini:disabled { opacity: .4; cursor: not-allowed; }

.galat {
  flex-basis: 100%;
  margin: 0;
  font-size: 12px;
  color: var(--status-critical);
}

@media (max-width: 768px) {
  .filter { flex-direction: column; align-items: stretch; }
  .grup { justify-content: flex-start; }
  .field { flex: 1 1 140px; }
}
</style>
