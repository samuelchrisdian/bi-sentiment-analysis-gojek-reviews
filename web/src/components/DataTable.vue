<script setup>
/** Kembaran tabel untuk setiap grafik: nilai tidak boleh hanya bisa dibaca
 *  lewat tooltip atau lewat warna. */
defineProps({
  kolom: { type: Array, required: true },   // [{ kunci, label, angka?, fmt? }]
  baris: { type: Array, required: true },
  maksTinggi: { type: Number, default: 320 },
  caption: { type: String, default: "" },
});
</script>

<template>
  <div class="bungkus" :style="{ maxHeight: maksTinggi + 'px' }" tabindex="0">
    <table>
      <caption v-if="caption" class="visually-hidden">{{ caption }}</caption>
      <thead>
        <tr>
          <th v-for="k in kolom" :key="k.kunci" :class="{ angka: k.angka }" scope="col">
            {{ k.label }}
          </th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="(r, i) in baris" :key="i">
          <td v-for="k in kolom" :key="k.kunci" :class="{ angka: k.angka }">
            {{ k.fmt ? k.fmt(r[k.kunci], r) : (r[k.kunci] ?? "–") }}
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<style scoped>
.bungkus { overflow: auto; }

table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
}

th, td {
  text-align: left;
  padding: 7px 10px;
  border-bottom: 1px solid var(--gridline);
  white-space: nowrap;
}

th {
  position: sticky;
  top: 0;
  background: var(--surface-1);
  font-weight: 600;
  font-size: 12px;
  color: var(--text-secondary);
}

/* Kolom angka disejajarkan vertikal, jadi di sinilah tabular-nums dipakai. */
td.angka, th.angka { text-align: right; font-variant-numeric: tabular-nums; }

tbody tr:hover { background: color-mix(in srgb, var(--gridline) 45%, transparent); }
</style>
