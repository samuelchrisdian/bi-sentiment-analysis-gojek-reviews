<script setup>
import { ref } from "vue";
import { useData } from "../stores/data";
import { bacaGalat } from "../api/client";
import { persen } from "../theme";

const CONTOH = [
  "aplikasi error terus gabisa bayar",
  "driver ramah, pesanan cepat sampai, mantap",
  "udah nunggu 30 menit driver malah cancel sepihak",
];

const data = useData();
const teks = ref(CONTOH[0]);
const hasil = ref(null);
const galat = ref("");
const memuat = ref(false);

async function kirim() {
  const t = teks.value.trim();
  if (!t) return;
  memuat.value = true;
  galat.value = "";
  try {
    hasil.value = await data.prediksi(t);
  } catch (e) {
    hasil.value = null;
    galat.value = bacaGalat(e).pesan;
  } finally {
    memuat.value = false;
  }
}
</script>

<template>
  <div class="demo">
    <form class="masuk" @submit.prevent="kirim">
      <label class="field">
        Teks ulasan
        <textarea
          v-model="teks" rows="4" maxlength="1000"
          placeholder="Tulis ulasan berbahasa Indonesia…"
        />
      </label>

      <div class="contoh">
        <span class="ket">Contoh:</span>
        <button v-for="c in CONTOH" :key="c" type="button" class="chip" @click="teks = c">
          {{ c.slice(0, 28) }}{{ c.length > 28 ? "…" : "" }}
        </button>
      </div>

      <div class="aksi">
        <button class="primary" type="submit" :disabled="memuat || !teks.trim()">
          {{ memuat ? "Memproses…" : "Prediksi" }}
        </button>
        <span class="sisa">{{ teks.length }} / 1000</span>
      </div>
    </form>

    <div class="keluar">
      <p v-if="galat" class="galat">{{ galat }}</p>

      <div v-else-if="hasil" class="kartu">
        <p class="baris">
          <span class="tag" :class="hasil.prediction === 0 ? 'tag--neg' : 'tag--pos'">
            {{ hasil.label }}
          </span>
          <span v-if="hasil.confidence !== null" class="yakin">
            keyakinan {{ persen(hasil.confidence * 100, 1) }}
          </span>
        </p>

        <!-- Rantai preprocessing ditampilkan supaya yang masuk ke TF-IDF
             terlihat, bukan hanya labelnya. -->
        <dl class="pipeline">
          <dt>Setelah normalisasi slang</dt>
          <dd>{{ hasil.text_normalized }}</dd>
          <dt>Masukan TF-IDF (sudah stopword + stemming)</dt>
          <dd class="mono">{{ hasil.text_preprocessed }}</dd>
          <dt>Model</dt>
          <dd>{{ hasil.model_name }}</dd>
        </dl>

        <p class="nota">{{ hasil.note }}</p>
      </div>

      <p v-else class="kosong">Hasil prediksi akan muncul di sini.</p>
    </div>
  </div>
</template>

<style scoped>
.demo { display: grid; grid-template-columns: 1fr 1fr; gap: 18px; }

textarea {
  width: 100%;
  resize: vertical;
  font-size: 14px;
  line-height: 1.5;
}

.contoh { display: flex; align-items: center; gap: 6px; flex-wrap: wrap; margin-top: 10px; }
.ket { font-size: 12px; color: var(--text-secondary); }

.chip {
  font-size: 11px;
  padding: 3px 8px;
  border-radius: 999px;
  color: var(--text-secondary);
}

.aksi { display: flex; align-items: center; gap: 10px; margin-top: 12px; }
.sisa { font-size: 12px; color: var(--text-muted); font-variant-numeric: tabular-nums; }

.keluar { display: flex; }

.kartu, .kosong, .galat {
  flex: 1;
  border: 1px solid var(--gridline);
  border-radius: var(--radius);
  padding: 14px 16px;
}

.kosong, .galat {
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0;
  font-size: 13px;
  color: var(--text-muted);
  text-align: center;
}
.galat { color: var(--status-critical); border-color: var(--status-critical); }

.baris { display: flex; align-items: center; gap: 10px; margin: 0 0 12px; }

.tag {
  font-size: 12px; font-weight: 600;
  padding: 3px 10px; border-radius: 999px; color: #fff;
}
.tag--neg { background: var(--series-8); }
.tag--pos { background: var(--series-1); }

.yakin { font-size: 13px; color: var(--text-secondary); }

.pipeline { margin: 0; font-size: 12px; }
.pipeline dt { color: var(--text-muted); margin-top: 9px; }
.pipeline dt:first-child { margin-top: 0; }
.pipeline dd {
  margin: 2px 0 0;
  color: var(--text-primary);
  font-size: 13px;
  overflow-wrap: anywhere;
}
.mono { font-family: ui-monospace, "SFMono-Regular", Menlo, monospace; font-size: 12px; }

.nota {
  margin: 14px 0 0;
  padding-top: 10px;
  border-top: 1px solid var(--gridline);
  font-size: 11px;
  color: var(--text-muted);
}

@media (max-width: 860px) {
  .demo { grid-template-columns: 1fr; }
}
</style>
