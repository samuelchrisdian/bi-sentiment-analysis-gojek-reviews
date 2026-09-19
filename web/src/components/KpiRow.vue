<script setup>
import { computed } from "vue";
import { ribuan, persen, desimal } from "../theme";

const props = defineProps({ kpi: { type: Object, required: true } });

/** Selisih model vs label aktual. Dibaca sebagai kalibrasi, bukan sebagai
 *  "kenaikan": baseline_negatif hanya dihitung atas ulasan berlabel (rating
 *  1–2 vs 4–5), sementara persen_negatif mencakup rating 3 juga. Karena itu
 *  label deltanya berbunyi "vs label aktual", bukan "vs periode lalu". */
const selisih = computed(() => props.kpi.persen_negatif - props.kpi.baseline_negatif);

const tanda = computed(() => (selisih.value >= 0 ? "+" : "−"));

const rentangTeks = computed(() => {
  const f = (s) => new Date(s + "T00:00:00").toLocaleDateString("id-ID",
    { day: "numeric", month: "short", year: "numeric" });
  return `${f(props.kpi.periode.dari)} – ${f(props.kpi.periode.sampai)}`;
});
</script>

<template>
  <div class="kpi">
    <!-- Angka utama dashboard: satu-satunya figure ukuran hero di halaman ini. -->
    <div class="card tile tile--hero">
      <p class="tile__label">Ulasan negatif</p>
      <p class="tile__hero">{{ persen(kpi.persen_negatif) }}</p>
      <p class="tile__delta">
        <span class="dot" aria-hidden="true" />
        {{ tanda }}{{ persen(Math.abs(selisih)) }} vs label aktual
        ({{ persen(kpi.baseline_negatif) }})
      </p>
    </div>

    <div class="card tile">
      <p class="tile__label">Total ulasan</p>
      <p class="tile__value">{{ ribuan(kpi.total_ulasan) }}</p>
      <p class="tile__meta">{{ rentangTeks }}</p>
    </div>

    <div class="card tile">
      <p class="tile__label">Rata-rata rating</p>
      <p class="tile__value">{{ desimal(kpi.rata_rating) }}<span class="unit"> / 5</span></p>
      <p class="tile__meta">Skala bintang Google Play</p>
    </div>

    <div class="card tile">
      <p class="tile__label">Versi aplikasi terhitung</p>
      <p class="tile__value">{{ kpi.jumlah_versi }}</p>
      <p class="tile__meta">{{ persen(kpi.versi_null_pct) }} ulasan tanpa versi</p>
    </div>
  </div>
</template>

<style scoped>
.kpi {
  display: grid;
  grid-template-columns: 1.35fr 1fr 1fr 1fr;
  gap: 14px;
}

.tile { display: flex; flex-direction: column; gap: 2px; }

.tile__label {
  margin: 0;
  font-size: 12px;
  font-weight: 500;
  color: var(--text-secondary);
  letter-spacing: .01em;
}

/* Figure besar memakai angka proporsional (default), bukan tabular-nums:
   pada ukuran display, digit selebar "0" membuat angka tampak renggang. */
.tile__hero {
  margin: 4px 0 0;
  font-size: 48px;
  line-height: 1.05;
  font-weight: 600;
  letter-spacing: -0.03em;
  color: var(--text-primary);
}

.tile__value {
  margin: 4px 0 0;
  font-size: 30px;
  line-height: 1.15;
  font-weight: 600;
  letter-spacing: -0.02em;
  color: var(--text-primary);
}

.unit { font-size: 16px; font-weight: 500; color: var(--text-muted); }

.tile__meta, .tile__delta {
  margin: 6px 0 0;
  font-size: 12px;
  color: var(--text-muted);
}

/* Warna hanya menyertai teks yang sudah menyebutkan artinya — tidak pernah
   menjadi satu-satunya pembawa makna. */
.tile__delta { display: flex; align-items: center; gap: 6px; color: var(--text-secondary); }

.dot {
  width: 8px; height: 8px; flex: none;
  border-radius: 50%;
  background: var(--series-8);
}

@media (max-width: 1000px) {
  .kpi { grid-template-columns: 1fr 1fr; }
}
@media (max-width: 560px) {
  .kpi { grid-template-columns: 1fr; }
  .tile__hero { font-size: 40px; }
}
</style>
