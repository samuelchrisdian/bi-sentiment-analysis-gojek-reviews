<script setup>
defineProps({ tinggi: { type: Number, default: 260 } });
</script>

<template>
  <div class="skel" :style="{ height: tinggi + 'px' }" role="status" aria-live="polite">
    <span class="visually-hidden">Memuat data…</span>
    <div class="bar" v-for="i in 5" :key="i" :style="{ height: (30 + i * 12) + '%' }" />
  </div>
</template>

<style scoped>
.skel {
  display: flex;
  align-items: flex-end;
  gap: 10px;
  padding: 20px 4px;
}
.bar {
  flex: 1;
  border-radius: 4px 4px 0 0;
  background: var(--gridline);
  animation: pulse 1.3s ease-in-out infinite;
}
.bar:nth-child(2) { animation-delay: .1s }
.bar:nth-child(3) { animation-delay: .2s }
.bar:nth-child(4) { animation-delay: .3s }
.bar:nth-child(5) { animation-delay: .4s }
@keyframes pulse { 0%, 100% { opacity: .45 } 50% { opacity: 1 } }
@media (prefers-reduced-motion: reduce) {
  .bar { animation: none; opacity: .6 }
}
</style>
