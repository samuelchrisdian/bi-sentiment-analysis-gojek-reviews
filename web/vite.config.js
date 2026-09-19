import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";

export default defineConfig({
  plugins: [vue()],
  build: {
    // ECharts (557 kB mentah / 187 kB gzip) adalah lantai keras: sudah
    // di-tree-shake lewat echarts/core dan hanya modul yang dipakai yang
    // diregistrasi (lihat src/echarts.js). Ambang dinaikkan ke 600 kB sebagai
    // keputusan sadar atas satu chunk vendor yang sudah diketahui ukurannya —
    // bukan untuk membungkam peringatan atas kode aplikasi, yang tetap
    // dijaga di bawah ambang (47 kB).
    chunkSizeWarningLimit: 600,
    // ECharts + zrender sendirian sudah melewati 500 kB dan tidak bisa
    // dipecah lebih jauh secara bermakna. Yang dilakukan di sini bukan
    // menaikkan ambang peringatan, melainkan memisahkannya menjadi chunk
    // sendiri yang dimuat secara async (lihat defineAsyncComponent di
    // DashboardView) — cangkang dashboard tampil lebih dulu, mesin grafik
    // menyusul, dan chunk itu ter-cache lintas rilis karena jarang berubah.
    rolldownOptions: {
      output: {
        advancedChunks: {
          groups: [
            { name: "echarts", test: /node_modules[\\/](echarts|zrender)[\\/]/ },
            { name: "vendor", test: /node_modules[\\/](vue|pinia|axios|@vue)[\\/]/ },
          ],
        },
      },
    },
  },
});
