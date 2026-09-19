<script setup>
import { computed } from "vue";
import { VChart } from "../echarts";
import {
  useTokens, dasarGrafik, sumbuNilai, sumbuKategori, ribuan, persen, ribuanSingkat,
} from "../theme";

const props = defineProps({ versions: { type: Object, required: true } });
const t = useTokens();

/** Diurut menurut kemunculan pertama, bukan menurut jumlah ulasan: yang ingin
 *  dibaca dari grafik ini adalah pergerakan antarrilis, dan urutan peringkat
 *  akan menghapus sumbu waktu itu. */
const baris = computed(() =>
  [...props.versions.data].sort(
    (a, b) => new Date(a.pertama_muncul) - new Date(b.pertama_muncul)
  )
);

const opsi = computed(() => {
  const k = t.value;

  // Celah 2px berwarna permukaan yang memisahkan kedua segmen — bukan garis
  // tepi kontras yang menambah tinta bukan-data.
  const celah = { borderColor: k.surface1, borderWidth: 2 };

  return {
    ...dasarGrafik(k),
    grid: { left: 56, right: 20, top: 38, bottom: 46 },
    // Kanan atas: kiri atas sudah ditempati nama sumbu-y.
    legend: { ...dasarGrafik(k).legend, top: 0, right: 0 },
    tooltip: {
      ...dasarGrafik(k).tooltip,
      trigger: "axis",
      axisPointer: { type: "shadow", shadowStyle: { color: "rgba(137,135,129,0.10)" } },
      formatter: (par) => {
        const d = baris.value[par[0].dataIndex];
        const tgl = new Date(d.pertama_muncul).toLocaleDateString("id-ID",
          { day: "numeric", month: "short", year: "numeric" });
        return [
          `<b>Versi ${d.versi_minor}</b> · pertama muncul ${tgl}`,
          `Negatif: <b>${ribuan(d.jumlah_negatif)}</b> (${persen(d.persen_negatif)})`,
          `Positif: <b>${ribuan(d.total_ulasan - d.jumlah_negatif)}</b>`,
          `Total: <b>${ribuan(d.total_ulasan)}</b> · rata rating ${d.rata_rating?.toFixed(2).replace(".", ",") ?? "–"}`,
        ].join("<br/>");
      },
    },
    xAxis: sumbuKategori(k, {
      data: baris.value.map((d) => d.versi_minor),
      axisLabel: {
        color: k.textMuted, fontSize: 10, rotate: 60,
        hideOverlap: true, margin: 10,
      },
    }),
    yAxis: sumbuNilai(k, {
      name: "Jumlah ulasan", nameLocation: "end", nameGap: 12,
      nameTextStyle: { color: k.textSecondary, fontSize: 11, align: "left" },
      axisLabel: {
        color: k.textMuted, fontSize: 11,
        formatter: ribuanSingkat,
      },
    }),
    series: [
      {
        name: "Negatif", type: "bar", stack: "ulasan",
        data: baris.value.map((d) => d.jumlah_negatif),
        itemStyle: { color: k.series8, ...celah },
        barMaxWidth: 24,
      },
      {
        name: "Positif", type: "bar", stack: "ulasan",
        data: baris.value.map((d) => d.total_ulasan - d.jumlah_negatif),
        itemStyle: { color: k.series1, borderRadius: [4, 4, 0, 0], ...celah },
        barMaxWidth: 24,
      },
    ],
  };
});
</script>

<template>
  <VChart class="grafik" :option="opsi" autoresize />
</template>

<style scoped>
.grafik { width: 100%; height: 340px; }
</style>
