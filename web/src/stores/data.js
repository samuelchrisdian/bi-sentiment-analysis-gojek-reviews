import { defineStore } from "pinia";
import { client, bacaGalat } from "../api/client";

/** Satu slot status per sumber data.
 *  `data` sengaja DIPERTAHANKAN selagi `status === "loading"` supaya
 *  render sebelumnya bisa ditahan dengan opacity turun — bukan diganti
 *  skeleton yang membuat layout melompat pada setiap refetch. */
const slotBaru = () => ({ status: "idle", data: null, pesan: "", kunci: null });

export const useData = defineStore("data", {
  state: () => ({
    res: {
      kpi: slotBaru(),
      trend: slotBaru(),
      versions: slotBaru(),
      topics: slotBaru(),
      reviews: slotBaru(),
      metrics: slotBaru(),
    },
    /** Cache respons per kunci parameter — menahan request berulang ketika
     *  pengguna bolak-balik ke rentang yang sama. */
    cache: {},
    /** Handle debounce per sumber; lihat muat(). */
    _timer: {},
  }),

  actions: {
    /**
     * @param nama   kunci pada `res`
     * @param path   path endpoint
     * @param params query params (undefined dibuang oleh axios)
     * @param opsi   { debounce: ms }
     */
    muat(nama, path, params = {}, opsi = {}) {
      const kunci = path + "?" + new URLSearchParams(
        Object.entries(params).filter(([, v]) => v !== null && v !== undefined)
      ).toString();

      const slot = this.res[nama];

      // Sudah tampil dan parameternya sama persis -> tidak ada yang perlu dimuat.
      if (slot.kunci === kunci && slot.status === "ok") return Promise.resolve();

      if (this.cache[kunci]) {
        Object.assign(slot, { status: "ok", data: this.cache[kunci], pesan: "", kunci });
        return Promise.resolve();
      }

      clearTimeout(this._timer[nama]);
      const jeda = opsi.debounce ?? 0;

      return new Promise((resolve) => {
        this._timer[nama] = setTimeout(async () => {
          slot.status = "loading";
          slot.kunci = kunci;
          try {
            const { data } = await client.get(path, { params });
            // Balapan: filter mungkin sudah berubah lagi selagi request berjalan.
            // Hanya tulis hasil bila kunci masih yang terakhir diminta.
            if (slot.kunci !== kunci) return resolve();
            this.cache[kunci] = data;
            Object.assign(slot, { status: "ok", data, pesan: "" });
          } catch (err) {
            if (slot.kunci !== kunci) return resolve();
            const { kosong, pesan } = bacaGalat(err);
            Object.assign(slot, { status: kosong ? "empty" : "error", pesan });
            if (kosong) slot.data = null;
          }
          resolve();
        }, jeda);
      });
    },

    /** Dipanggil tombol "coba lagi": buang cache kunci itu lalu muat ulang. */
    ulangi(nama, path, params = {}) {
      const slot = this.res[nama];
      if (slot.kunci) delete this.cache[slot.kunci];
      slot.kunci = null;
      return this.muat(nama, path, params);
    },

    async prediksi(text) {
      const { data } = await client.post("/api/predict", { text });
      return data;
    },
  },
});
