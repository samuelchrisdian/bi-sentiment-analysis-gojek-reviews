<script setup>
import { computed } from "vue";
import { VChart } from "../echarts";
import {
  useTokens, dasarGrafik, sumbuNilai, sumbuKategori, ribuan, persen, ribuanSingkat,
} from "../theme";

const props = defineProps({
  topics: { type: Object, required: true },
  terpilih: { type: Number, default: null },
});
const emit = defineEmits(["pilih"]);
const t = useTokens();

/** ECharts menggambar sumbu kategori dari bawah ke atas; dibalik supaya
 *  kategori terbesar duduk di baris teratas. */
const baris = computed(() => [...props.topics.data].reverse());

const opsi = computed(() => {
  const k = t.value;
  return {
    ...dasarGrafik(k),
    grid: { left: 200, right: 76, top: 8, bottom: 30 },
    tooltip: {
      ...dasarGrafik(k).tooltip,
      trigger: "item",
      formatter: (p) => {
        const d = baris.value[p.dataIndex];
        return [
          `<b>${d.kategori}</b>`,
          `${ribuan(d.jumlah_ulasan)} ulasan · ${persen(d.persen_negatif)} negatif`,
          `${ribuan(d.total_likes)} likes · rata rating ${d.rata_rating?.toFixed(2).replace(".", ",") ?? "–"}`,
          `<span style="color:${k.textMuted}">Klik untuk membuka ulasannya</span>`,
        ].join("<br/>");
      },
    },
    // Maks dibiarkan dipilih ECharts supaya tick jatuh di angka bulat; label
    // di ujung batang muat di talang kanan grid.
    xAxis: sumbuNilai(k, {
      axisLabel: { color: k.textMuted, fontSize: 11, formatter: ribuanSingkat },
    }),
    yAxis: sumbuKategori(k, {
      data: baris.value.map((d) => d.kategori),
      axisLine: { show: false },
      axisLabel: {
        color: k.textSecondary, fontSize: 12, width: 186,
        overflow: "truncate", margin: 12,
      },
    }),
    series: [{
      type: "bar",
      // Satu seri, satu warna. Mewarnai batang lebih gelap-karena-lebih-besar
      // hanya menduplikasi panjang batang dan membakar kanal warna.
      data: baris.value.map((d) => ({
        value: d.jumlah_ulasan,
        itemStyle: {
          color: k.series1,
          borderRadius: [0, 4, 4, 0],
          opacity: props.terpilih === null || props.terpilih === d.id ? 1 : 0.42,
        },
      })),
      barMaxWidth: 24,
      label: {
        show: true, position: "right", distance: 8,
        color: k.textPrimary, fontSize: 11,
        formatter: (p) => ribuan(p.value),
      },
      cursor: "pointer",
      emphasis: { itemStyle: { opacity: 1 } },
    }],
  };
});

function klik(p) {
  const d = baris.value[p.dataIndex];
  emit("pilih", d.id, d.kategori);
}
</script>

<template>
  <VChart
    class="grafik"
    :option="opsi"
    autoresize
    @click="klik"
  />
</template>

<style scoped>
.grafik { width: 100%; height: 320px; }
</style>
