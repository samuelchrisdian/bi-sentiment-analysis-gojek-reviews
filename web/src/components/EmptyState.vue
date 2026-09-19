<script setup>
defineProps({
  pesan: { type: String, required: true },
  /** "empty" -> tawarkan reset filter; "error" -> tawarkan coba lagi. */
  jenis: { type: String, default: "empty" },
  tinggi: { type: Number, default: 260 },
});
defineEmits(["reset", "ulangi"]);
</script>

<template>
  <div class="kosong" :style="{ minHeight: tinggi + 'px' }" role="status">
    <svg width="26" height="26" viewBox="0 0 24 24" fill="none" aria-hidden="true"
         :stroke="jenis === 'error' ? 'var(--status-critical)' : 'var(--text-muted)'"
         stroke-width="1.6" stroke-linecap="round">
      <circle cx="12" cy="12" r="9" />
      <template v-if="jenis === 'error'">
        <path d="M12 7v6" /><path d="M12 16.5v.01" />
      </template>
      <template v-else>
        <path d="M8 12h8" />
      </template>
    </svg>

    <p class="pesan">{{ pesan }}</p>

    <button v-if="jenis === 'error'" @click="$emit('ulangi')">Coba lagi</button>
    <button v-else @click="$emit('reset')">Atur ulang filter</button>
  </div>
</template>

<style scoped>
.kosong {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 10px;
  padding: 26px 16px;
  text-align: center;
}
.pesan {
  margin: 0;
  max-width: 40ch;
  font-size: 13px;
  color: var(--text-secondary);
}
</style>
