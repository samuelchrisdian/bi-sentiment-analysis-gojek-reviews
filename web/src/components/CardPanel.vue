<script setup>
import { ref, computed } from "vue";
import LoadingState from "./LoadingState.vue";
import EmptyState from "./EmptyState.vue";

const props = defineProps({
  judul: { type: String, required: true },
  sub: { type: String, default: "" },
  /** Slot status dari store data: { status, data, pesan }. */
  slot: { type: Object, required: true },
  tinggi: { type: Number, default: 260 },
  /** Tampilkan tombol alih tabel — grafik wajib punya kembaran tabel. */
  adaTabel: { type: Boolean, default: false },
});

defineEmits(["reset", "ulangi"]);

const tabel = ref(false);

/** Catatan metodologis SELALU dari respons API, tidak pernah ditulis ulang di
 *  frontend — kalau ambang atau persentase berubah di backend, teks di bawah
 *  grafik ikut berubah tanpa ada yang perlu disunting di sini. */
const catatan = computed(() => props.slot.data?.catatan ?? []);

const adaData = computed(() => props.slot.data !== null);
const sedangMuat = computed(() => props.slot.status === "loading");
</script>

<template>
  <section class="card panel">
    <header class="panel__head">
      <div>
        <h2 class="card__title">{{ judul }}</h2>
        <p v-if="sub" class="card__sub">{{ sub }}</p>
      </div>
      <div class="panel__aksi">
        <slot name="aksi" />
        <button
          v-if="adaTabel && adaData"
          class="toggle mini"
          :aria-pressed="String(tabel)"
          @click="tabel = !tabel"
        >{{ tabel ? "Grafik" : "Tabel" }}</button>
      </div>
    </header>

    <!-- Galat & kosong menang atas data lama: menahan render usang di sini
         akan menyesatkan, karena filter yang berlaku sudah bukan yang itu. -->
    <EmptyState
      v-if="slot.status === 'error'"
      jenis="error" :pesan="slot.pesan" :tinggi="tinggi"
      @ulangi="$emit('ulangi')"
    />
    <EmptyState
      v-else-if="slot.status === 'empty'"
      jenis="empty" :pesan="slot.pesan" :tinggi="tinggi"
      @reset="$emit('reset')"
    />
    <LoadingState v-else-if="!adaData" :tinggi="tinggi" />

    <!-- Refetch: render sebelumnya ditahan dengan opacity turun, bukan diganti
         skeleton — mencegah layout melompat setiap kali filter digeser. -->
    <div v-else class="panel__isi" :class="{ 'is-memuat': sedangMuat }"
         :aria-busy="String(sedangMuat)">
      <slot :tabel="tabel" />
    </div>

    <ul v-if="catatan.length" class="notes">
      <li v-for="(c, i) in catatan" :key="i">{{ c }}</li>
    </ul>
    <slot name="catatan-tambahan" />
  </section>
</template>

<style scoped>
.panel { display: flex; flex-direction: column; }

.panel__head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 10px;
}

.panel__aksi { display: flex; gap: 6px; flex-shrink: 0; }

.mini { font-size: 12px; padding: 4px 9px; }

.panel__isi { transition: opacity .15s ease; }
.panel__isi.is-memuat { opacity: .45; }

@media (prefers-reduced-motion: reduce) {
  .panel__isi { transition: none; }
}
</style>
