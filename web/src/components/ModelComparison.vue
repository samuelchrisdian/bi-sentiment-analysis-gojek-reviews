<script setup>
import { computed, ref } from "vue";
import { VChart } from "../echarts";
import DataTable from "./DataTable.vue";
import { useTokens, dasarGrafik, sumbuNilai, sumbuKategori, desimal } from "../theme";

const props = defineProps({
  metrics: { type: Object, required: true },
  tabel: { type: Boolean, default: false },
});
const t = useTokens();

const METRIK = [
  { kunci: "macro_f1", label: "Macro F1" },
  { kunci: "accuracy", label: "Akurasi" },
];
const metrik = ref("macro_f1");

const BASELINE = "majority_baseline";

/** Urutan model dikunci sekali dari eval_set pertama dan dipakai di KEDUA
 *  panel. Kalau tiap panel diurut sendiri, batang yang sejajar akan merujuk
 *  model berbeda dan perbandingannya jadi menyesatkan. */
const urutanModel = computed(() => {
  const utama = props.metrics.eval_sets[0];
  return utama.models
    .filter((m) => m.model_name !== BASELINE)
    .slice()
    .sort((a, b) => (b.macro_f1 ?? 0) - (a.macro_f1 ?? 0))
    .map((m) => m.model_name);
});

const warnaPanel = computed(() => [t.value.series1, t.value.series2]);

function panel(blok, i) {
  const k = t.value;
  const peta = Object.fromEntries(blok.models.map((m) => [m.model_name, m]));
  // Sumbu kategori ECharts tumbuh ke atas; dibalik agar model terbaik di atas.
  const nama = [...urutanModel.value].reverse();
  const nilai = nama.map((n) => peta[n]?.[metrik.value] ?? null);
  const garis = peta[BASELINE]?.[metrik.value] ?? null;
  const warna = warnaPanel.value[i % 2];

  return {
    ...dasarGrafik(k),
    grid: { left: 158, right: 62, top: 22, bottom: 26 },
    tooltip: {
      ...dasarGrafik(k).tooltip,
      trigger: "item",
      formatter: (p) => {
        const m = peta[nama[p.dataIndex]];
        return [
          `<b>${m.model_name}</b>${m.is_produksi ? " · model produksi" : ""}`,
          `Macro F1: <b>${desimal(m.macro_f1, 4)}</b>`,
          `Akurasi: <b>${desimal(m.accuracy, 4)}</b>`,
          `F1 negatif: <b>${desimal(m.f1_neg, 4)}</b>`,
          `Latih: ${desimal(m.train_seconds, 2)} detik`,
        ].join("<br/>");
      },
    },
    xAxis: sumbuNilai(k, {
      min: 0, max: 1,
      axisLabel: { color: k.textMuted, fontSize: 11, formatter: (v) => desimal(v, 1) },
    }),
    yAxis: sumbuKategori(k, {
      data: nama.map((n) => (peta[n]?.is_produksi ? n + "  ●" : n)),
      axisLine: { show: false },
      axisLabel: { color: k.textSecondary, fontSize: 11, width: 148, overflow: "truncate" },
    }),
    series: [{
      type: "bar",
      data: nilai,
      barMaxWidth: 16,
      itemStyle: { color: warna, borderRadius: [0, 4, 4, 0] },
      label: {
        show: true, position: "right", distance: 6,
        color: k.textPrimary, fontSize: 11,
        formatter: (p) => desimal(p.value, 3),
      },
      // Baseline mayoritas milik eval_set INI — bukan satu angka yang dipakai
      // ulang untuk kedua panel. Pada `full` baseline 0,72; pada
      // `informative_ge5w` ia jatuh ke 0,46, dan justru di situlah jarak
      // sesungguhnya antarmodel terlihat.
      markLine: garis === null ? undefined : {
        silent: true,
        symbol: "none",
        lineStyle: { color: k.textMuted, width: 1, type: "solid" },
        // rotate:0 — ECharts memutar label garis vertikal mengikuti arah
        // garisnya, dan teks berdiri tegak itu praktis tidak terbaca.
        label: {
          position: "end", rotate: 0, distance: 4,
          color: k.textSecondary, fontSize: 10,
          formatter: `baseline ${desimal(garis, 3)}`,
        },
        data: [{ xAxis: garis }],
      },
    }],
  };
}

const opsiPanel = computed(() => props.metrics.eval_sets.map((b, i) => panel(b, i)));

/* --- kembaran tabel ------------------------------------------------------ */
const kolomTabel = computed(() => [
  { kunci: "model_name", label: "Model" },
  ...props.metrics.eval_sets.flatMap((b) => [
    { kunci: `${b.eval_set}__macro_f1`, label: `${b.eval_set} · Macro F1`, angka: true,
      fmt: (v) => desimal(v, 4) },
    { kunci: `${b.eval_set}__accuracy`, label: `${b.eval_set} · Akurasi`, angka: true,
      fmt: (v) => desimal(v, 4) },
  ]),
]);

const barisTabel = computed(() => {
  const nama = [BASELINE, ...urutanModel.value];
  return nama.map((n) => {
    const r = { model_name: n };
    for (const b of props.metrics.eval_sets) {
      const m = b.models.find((x) => x.model_name === n);
      r[`${b.eval_set}__macro_f1`] = m?.macro_f1 ?? null;
      r[`${b.eval_set}__accuracy`] = m?.accuracy ?? null;
      if (m?.is_produksi) r.model_name = n + " (produksi)";
    }
    return r;
  });
});
</script>

<template>
  <div>
    <DataTable
      v-if="tabel"
      :kolom="kolomTabel" :baris="barisTabel" :maks-tinggi="420"
      caption="Metrik setiap model pada kedua eval set"
    />

    <template v-else>
      <div class="alih">
        <button
          v-for="m in METRIK" :key="m.kunci"
          class="toggle mini" :aria-pressed="String(metrik === m.kunci)"
          @click="metrik = m.kunci"
        >{{ m.label }}</button>
      </div>

      <!-- Dua eval set berdampingan, masing-masing panel sendiri. Menumpuknya
           jadi satu plot memaksa satu garis baseline mewakili dua angka yang
           berbeda jauh (0,72 vs 0,46). -->
      <div class="panel-grid">
        <figure v-for="(blok, i) in metrics.eval_sets" :key="blok.eval_set">
          <figcaption>
            <span class="kunci" :style="{ background: warnaPanel[i % 2] }" aria-hidden="true" />
            <b>{{ blok.eval_set }}</b>
            <span class="n" v-if="blok.n_eval">n = {{ blok.n_eval.toLocaleString("id-ID") }}</span>
          </figcaption>
          <VChart class="grafik" :option="opsiPanel[i]" autoresize />
        </figure>
      </div>

      <p class="legenda">
        ● menandai model produksi. Garis vertikal = baseline mayoritas eval set itu.
      </p>
    </template>
  </div>
</template>

<style scoped>
.alih { display: flex; gap: 6px; margin-bottom: 10px; }
.mini { font-size: 12px; padding: 4px 9px; }

.panel-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 18px;
}

figure { margin: 0; }

figcaption {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  color: var(--text-secondary);
  margin-bottom: 6px;
}

.kunci { width: 10px; height: 10px; border-radius: 3px; flex: none; }
.n { color: var(--text-muted); }

.grafik { width: 100%; height: 300px; }

.legenda { margin: 10px 0 0; font-size: 12px; color: var(--text-muted); }

@media (max-width: 900px) {
  .panel-grid { grid-template-columns: 1fr; }
}
</style>
