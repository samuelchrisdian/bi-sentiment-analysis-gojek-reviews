<script setup>
import { computed } from "vue";
import { ribuan, persen } from "../theme";

const props = defineProps({ reviews: { type: Object, required: true } });
const emit = defineEmits(["halaman", "sort"]);

const SORT = [
  { kunci: "likes", label: "Likes" },
  { kunci: "tanggal", label: "Terbaru" },
  { kunci: "rating", label: "Rating" },
];

const r = computed(() => props.reviews);

const dari = computed(() => (r.value.page - 1) * r.value.page_size + 1);
const sampai = computed(() =>
  Math.min(r.value.page * r.value.page_size, r.value.total_items));

const tgl = (s) =>
  new Date(s).toLocaleDateString("id-ID", { day: "numeric", month: "short", year: "numeric" });

/** `pred_proba` adalah P(kelas POSITIF) dari pre-scoring batch Fase 6 —
 *  bukan keyakinan atas kelas yang terpilih. Untuk ulasan yang diprediksi
 *  negatif, keyakinannya adalah 1 − pred_proba. Menampilkannya apa adanya
 *  akan terbaca terbalik. */
function keyakinan(d) {
  if (d.pred_proba === null || d.pred_proba === undefined) return null;
  return d.pred_label === 1 ? d.pred_proba : 1 - d.pred_proba;
}
</script>

<template>
  <div>
    <div class="bar">
      <div class="urut">
        <span class="ket">Urut:</span>
        <button
          v-for="s in SORT" :key="s.kunci"
          class="toggle mini" :aria-pressed="String(r.sort_by === s.kunci)"
          @click="emit('sort', s.kunci)"
        >{{ s.label }}</button>
      </div>
      <p class="hitung">
        {{ ribuan(dari) }}–{{ ribuan(sampai) }} dari {{ ribuan(r.total_items) }} ulasan
      </p>
    </div>

    <ul class="daftar">
      <li v-for="d in r.data" :key="d.id" class="ulasan">
        <div class="meta">
          <span class="bintang" :aria-label="`rating ${d.rating} dari 5`">
            <span aria-hidden="true">{{ "★".repeat(d.rating) }}{{ "☆".repeat(5 - d.rating) }}</span>
          </span>
          <span class="pisah" aria-hidden="true">·</span>
          <span>{{ tgl(d.tanggal) }}</span>
          <span class="pisah" aria-hidden="true">·</span>
          <span>{{ ribuan(d.likes) }} likes</span>
          <span v-if="d.versi_app" class="pisah" aria-hidden="true">·</span>
          <span v-if="d.versi_app">v{{ d.versi_app }}</span>

          <!-- Warna tidak pernah sendirian: selalu ada teks labelnya. -->
          <span class="tag" :class="d.pred_label === 0 ? 'tag--neg' : 'tag--pos'">
            {{ d.pred_label === 0 ? "Negatif" : "Positif" }}
            <template v-if="keyakinan(d) !== null">
              {{ persen(keyakinan(d) * 100, 0) }}
            </template>
          </span>
        </div>
        <!-- Teks ASLI, bukan ulasan_clean. -->
        <p class="teks">{{ d.ulasan }}</p>
      </li>
    </ul>

    <nav class="nav" aria-label="Navigasi halaman ulasan">
      <button :disabled="r.page <= 1" @click="emit('halaman', r.page - 1)">‹ Sebelumnya</button>
      <span class="hal">Halaman {{ ribuan(r.page) }} dari {{ ribuan(r.total_pages) }}</span>
      <button :disabled="r.page >= r.total_pages" @click="emit('halaman', r.page + 1)">Berikutnya ›</button>
    </nav>
  </div>
</template>

<style scoped>
.bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  flex-wrap: wrap;
  margin-bottom: 12px;
}

.urut { display: flex; align-items: center; gap: 6px; }
.ket { font-size: 12px; color: var(--text-secondary); }
.mini { font-size: 12px; padding: 4px 9px; }
.hitung { margin: 0; font-size: 12px; color: var(--text-muted); font-variant-numeric: tabular-nums; }

.daftar { list-style: none; margin: 0; padding: 0; }

.ulasan {
  padding: 13px 0;
  border-top: 1px solid var(--gridline);
}
.ulasan:first-child { border-top: none; padding-top: 0; }

.meta {
  display: flex;
  align-items: center;
  gap: 7px;
  flex-wrap: wrap;
  font-size: 12px;
  color: var(--text-muted);
  margin-bottom: 5px;
}

.bintang { color: var(--status-warning); letter-spacing: 1px; }
.pisah { color: var(--baseline); }

.tag {
  font-size: 11px;
  font-weight: 600;
  padding: 2px 7px;
  border-radius: 999px;
  line-height: 1.5;
}
.tag--neg { color: #fff; background: var(--series-8); }
.tag--pos { color: #fff; background: var(--series-1); }

.teks {
  margin: 0;
  font-size: 14px;
  line-height: 1.55;
  color: var(--text-primary);
  white-space: pre-wrap;
  overflow-wrap: anywhere;
}

.nav {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 14px;
  margin-top: 16px;
  padding-top: 14px;
  border-top: 1px solid var(--gridline);
}

.nav button:disabled { opacity: .4; cursor: not-allowed; }
.hal { font-size: 12px; color: var(--text-secondary); font-variant-numeric: tabular-nums; }
</style>
