<script setup>
import { computed } from "vue";
import { VChart } from "../echarts";
import {
  useTokens, dasarGrafik, sumbuNilai, sumbuKategori,
  ribuan, persen, labelPeriode, ribuanSingkat,
} from "../theme";

const props = defineProps({ trend: { type: Object, required: true } });
const t = useTokens();

const titik = computed(() => props.trend.data);
const label = computed(() => titik.value.map((d) => labelPeriode(d.periode, props.trend.granularity)));

/** Periode parsial ditandai dari flag `periode_parsial` pada respons — bukan
 *  dari tanggal yang ditulis keras di frontend. Kalau backend mengubah daftar
 *  bulan parsialnya, arsiran di sini ikut berubah sendiri. */
const arsir = computed(() =>
  titik.value
    .map((d, i) => (d.periode_parsial ? i : -1))
    .filter((i) => i >= 0)
    .map((i) => [
      { xAxis: i - 0.5, itemStyle: { color: "rgba(137,135,129,0.14)" } },
      { xAxis: i + 0.5 },
    ])
);

const opsi = computed(() => {
  const k = t.value;
  const n = titik.value.length;
  const iAkhir = n - 1;

  // Dua panel bertumpuk dengan SATU sumbu-x bersama, bukan satu plot bersumbu
  // ganda. Dua skala-y pada satu bidang membuat perpotongan garis tampak
  // bermakna padahal penjajaran skalanya sepenuhnya sembarang; memisahkan
  // panel menjaga perbandingan bentuk antarwaktu tanpa mengarang korelasi.
  const gridBersama = { left: 58, right: 26 };

  return {
    ...dasarGrafik(k),
    // Tiap panel hanya punya SATU seri dan namanya sudah ditulis pada sumbu-y,
    // jadi kotak legenda cuma mengulang judul dan menabrak label sumbu-x.
    legend: { show: false },
    grid: [
      { ...gridBersama, top: 30, height: 150 },
      { ...gridBersama, top: 222, height: 96 },
    ],
    axisPointer: {
      link: [{ xAxisIndex: "all" }],
      lineStyle: { color: k.baseline, width: 1, type: "solid" },
    },
    tooltip: {
      ...dasarGrafik(k).tooltip,
      trigger: "axis",
      axisPointer: { type: "line" },
      formatter: (par) => {
        const i = par[0].dataIndex;
        const d = titik.value[i];
        return [
          `<b>${label.value[i]}</b>${d.periode_parsial ? " · periode parsial" : ""}`,
          `Negatif: <b>${persen(d.persen_negatif)}</b> (${ribuan(d.jumlah_negatif)} ulasan)`,
          `Volume: <b>${ribuan(d.total_ulasan)}</b> ulasan`,
          `Rata rating: <b>${d.rata_rating?.toFixed(2).replace(".", ",") ?? "–"}</b>`,
        ].join("<br/>");
      },
    },
    xAxis: [
      sumbuKategori(k, {
        gridIndex: 0, data: label.value, boundaryGap: true,
        axisLabel: { show: false }, axisLine: { show: false },
      }),
      sumbuKategori(k, {
        gridIndex: 1, data: label.value, boundaryGap: true,
        axisLabel: {
          color: k.textMuted, fontSize: 11, interval: n > 14 ? 1 : 0,
          hideOverlap: true,
        },
      }),
    ],
    yAxis: [
      sumbuNilai(k, {
        gridIndex: 0, name: "Ulasan negatif", nameLocation: "end",
        nameGap: 12, nameTextStyle: { color: k.textSecondary, fontSize: 11, align: "left" },
        min: 0, axisLabel: { color: k.textMuted, fontSize: 11, formatter: "{value}%" },
      }),
      sumbuNilai(k, {
        gridIndex: 1, name: "Volume ulasan", nameLocation: "end",
        nameGap: 12, nameTextStyle: { color: k.textSecondary, fontSize: 11, align: "left" },
        min: 0,
        axisLabel: {
          color: k.textMuted, fontSize: 11,
          formatter: ribuanSingkat,
        },
      }),
    ],
    series: [
      {
        name: "Ulasan negatif",
        type: "line",
        xAxisIndex: 0, yAxisIndex: 0,
        data: titik.value.map((d) => d.persen_negatif),
        lineStyle: { width: 2, color: k.series1, cap: "round", join: "round" },
        itemStyle: { color: k.series1, borderColor: k.surface1, borderWidth: 2 },
        symbol: "circle", symbolSize: 8, showSymbol: n <= 24,
        areaStyle: { color: k.series1, opacity: 0.10 },
        smooth: false,
        // Satu label langsung di ujung — bukan angka di setiap titik.
        label: {
          show: true, position: "top", distance: 8,
          color: k.textPrimary, fontSize: 11, fontWeight: 600,
          formatter: (p) => (p.dataIndex === iAkhir ? persen(p.value) : ""),
        },
        labelLayout: { hideOverlap: true },
        markArea: arsir.value.length
          ? { silent: true, data: arsir.value,
              label: { show: false } }
          : undefined,
        z: 3,
      },
      {
        name: "Volume ulasan",
        type: "bar",
        xAxisIndex: 1, yAxisIndex: 1,
        data: titik.value.map((d) => d.total_ulasan),
        barMaxWidth: 24,
        // Ujung data membulat 4px, siku di garis dasar.
        itemStyle: { color: k.series2, borderRadius: [4, 4, 0, 0] },
        markArea: arsir.value.length
          ? { silent: true, data: arsir.value, label: { show: false } }
          : undefined,
      },
    ],
  };
});
</script>

<template>
  <VChart class="grafik" :option="opsi" autoresize />
</template>

<style scoped>
.grafik { width: 100%; height: 360px; }
</style>
