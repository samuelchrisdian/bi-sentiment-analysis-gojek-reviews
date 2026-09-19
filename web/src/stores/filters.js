import { defineStore } from "pinia";

/** Batas nyata korpus (lihat /api/kpi -> periode). Dipakai sebagai clamp
 *  pada input tanggal supaya pengguna tidak bisa meminta rentang kosong. */
export const TANGGAL_MIN = "2024-05-21";
export const TANGGAL_MAX = "2025-12-31";

/** Awal Juni: Mei 2024 baru mulai tercatat 21 Mei, jadi bulan itu parsial.
 *  Memasukkannya secara diam-diam akan membuat titik pertama grafik tren
 *  tampak anjlok padahal yang berkurang hanyalah jumlah hari. Keputusan
 *  metodologis ini diwujudkan sebagai default yang bisa dimatikan pengguna,
 *  bukan sebagai baris data yang dibuang. */
export const AWAL_PENUH = "2024-06-01";

export const useFilters = defineStore("filters", {
  state: () => ({
    from: AWAL_PENUH,
    to: TANGGAL_MAX,
    granularity: "month",
    /** Kategori terpilih untuk drill-down; null = tabel ulasan belum dibuka. */
    kategoriId: null,
    kategoriNama: null,
  }),

  getters: {
    /** Parameter rentang — dipakai bersama oleh /api/kpi, /api/trend, /api/topics.
     *  Satu getter supaya ketiganya dijamin melihat irisan yang sama. */
    rentang: (s) => ({ from: s.from, to: s.to }),

    sertakanMei: (s) => s.from < AWAL_PENUH,

    /** Kunci cache: setiap perubahan yang memengaruhi hasil harus muncul di sini. */
    kunciRentang: (s) => `${s.from}|${s.to}`,

    tidakDefault: (s) =>
      s.from !== AWAL_PENUH || s.to !== TANGGAL_MAX || s.granularity !== "month",
  },

  actions: {
    setRentang(from, to) {
      this.from = from;
      this.to = to;
    },

    toggleMei() {
      this.from = this.sertakanMei ? AWAL_PENUH : TANGGAL_MIN;
    },

    pilihKategori(id, nama) {
      this.kategoriId = id;
      this.kategoriNama = nama;
    },

    reset() {
      this.from = AWAL_PENUH;
      this.to = TANGGAL_MAX;
      this.granularity = "month";
      this.kategoriId = null;
      this.kategoriNama = null;
    },
  },
});
