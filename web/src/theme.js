import { ref, readonly } from "vue";

/** ECharts butuh warna nyata, bukan `var(--...)`. Token dibaca sekali dari
 *  CSS lalu dibagikan; ketika mode gelap sistem berubah, token dibaca ulang
 *  dan seluruh grafik ikut ter-render ulang karena objek ini reaktif. */
const NAMA = [
  "surface-1", "text-primary", "text-secondary", "text-muted",
  "gridline", "baseline", "series-1", "series-2", "series-8",
  "status-critical", "status-warning",
];

function baca() {
  const cs = getComputedStyle(document.documentElement);
  const t = {};
  for (const n of NAMA) t[camel(n)] = cs.getPropertyValue("--" + n).trim();
  return t;
}

const camel = (s) => s.replace(/-(\w)/g, (_, c) => c.toUpperCase());

const tokens = ref(baca());

if (window.matchMedia) {
  window.matchMedia("(prefers-color-scheme: dark)")
    .addEventListener("change", () => { tokens.value = baca(); });
}

export const useTokens = () => readonly(tokens);

/** Basis konfigurasi yang dipakai SEMUA grafik: chrome resesif, hairline
 *  solid (tidak putus-putus), teks memakai token teks — tidak pernah warna
 *  seri. Komponen hanya menambahkan seri dan sumbu di atas ini. */
export function dasarGrafik(t) {
  return {
    backgroundColor: "transparent",
    textStyle: { fontFamily: "system-ui, -apple-system, 'Segoe UI', sans-serif" },
    animationDuration: 300,
    tooltip: {
      backgroundColor: t.surface1,
      borderColor: t.gridline,
      borderWidth: 1,
      padding: [8, 11],
      textStyle: { color: t.textPrimary, fontSize: 12 },
      extraCssText: "box-shadow:0 4px 14px rgba(0,0,0,.10);border-radius:8px;",
    },
    legend: {
      textStyle: { color: t.textSecondary, fontSize: 12 },
      icon: "roundRect",
      itemWidth: 10,
      itemHeight: 10,
      itemGap: 16,
    },
  };
}

export function sumbuNilai(t, extra = {}) {
  return {
    type: "value",
    axisLine: { show: false },
    axisTick: { show: false },
    axisLabel: { color: t.textMuted, fontSize: 11 },
    nameTextStyle: { color: t.textSecondary, fontSize: 11 },
    splitLine: { lineStyle: { color: t.gridline, width: 1, type: "solid" } },
    ...extra,
  };
}

export function sumbuKategori(t, extra = {}) {
  return {
    type: "category",
    axisLine: { lineStyle: { color: t.baseline, width: 1 } },
    axisTick: { show: false },
    axisLabel: { color: t.textMuted, fontSize: 11 },
    splitLine: { show: false },
    ...extra,
  };
}

/** Pemisah ribuan gaya Indonesia — TITIK, sama seperti yang dipakai API. */
export const ribuan = (n) =>
  n === null || n === undefined ? "–" : Math.round(n).toLocaleString("id-ID");

export const persen = (n, d = 1) =>
  n === null || n === undefined ? "–" : n.toFixed(d).replace(".", ",") + "%";

/** Label sumbu ringkas: 2000 -> "2rb". Hanya dipakai pada tick yang memang
 *  kelipatan ribuan; nilai lain ditulis utuh supaya "10691" tidak pernah
 *  muncul sebagai "10.691rb". */
export const ribuanSingkat = (v) =>
  v >= 1000 && v % 1000 === 0 ? v / 1000 + "rb" : ribuan(v);

export const desimal = (n, d = 2) =>
  n === null || n === undefined ? "–" : n.toFixed(d).replace(".", ",");

const BULAN = ["Jan", "Feb", "Mar", "Apr", "Mei", "Jun",
               "Jul", "Agu", "Sep", "Okt", "Nov", "Des"];

export function labelPeriode(iso, granularity) {
  const d = new Date(iso + "T00:00:00");
  if (granularity === "week") {
    return `${d.getDate()} ${BULAN[d.getMonth()]} ${String(d.getFullYear()).slice(2)}`;
  }
  return `${BULAN[d.getMonth()]} ${String(d.getFullYear()).slice(2)}`;
}
