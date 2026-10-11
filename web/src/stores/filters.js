import { defineStore } from "pinia";

/** Batas nyata korpus (lihat /api/kpi -> periode). Dipakai sebagai clamp
 *  pada input tanggal supaya pengguna tidak bisa meminta rentang kosong. */
export const TANGGAL_MIN = "2021-10-01";
export const TANGGAL_MAX = "2026-09-30";

/** Rentang bulan penuh. Data scraping sengaja diambil tepat 60 bulan penuh
 *  (Oktober 2021 – September 2026), sehingga keduanya sama dengan batas data.
 *  Konstanta ini tetap dipisah: bila suatu saat data dimulai/berakhir di
 *  tengah bulan, titik ujung grafik tren yang hanya berisi sebagian hari tidak
 *  boleh ikut secara diam-diam — keputusan itu diwujudkan sebagai default yang
 *  bisa dimatikan pengguna, bukan sebagai baris data yang dibuang. */
export const AWAL_PENUH = "2021-10-01";
export const AKHIR_PENUH = "2026-09-30";
export const ADA_PARSIAL = AWAL_PENUH !== TANGGAL_MIN || AKHIR_PENUH !== TANGGAL_MAX;

export const useFilters = defineStore("filters", {
  state: () => ({
    from: AWAL_PENUH,
    to: AKHIR_PENUH,
    granularity: "month",
    /** Kategori terpilih untuk drill-down; null = tabel ulasan belum dibuka. */
    kategoriId: null,
    kategoriNama: null,
  }),

  getters: {
    /** Parameter rentang — dipakai bersama oleh /api/kpi, /api/trend, /api/topics.
     *  Satu getter supaya ketiganya dijamin melihat irisan yang sama. */
    rentang: (s) => ({ from: s.from, to: s.to }),

    sertakanParsial: (s) => s.from < AWAL_PENUH || s.to > AKHIR_PENUH,

    /** Kunci cache: setiap perubahan yang memengaruhi hasil harus muncul di sini. */
    kunciRentang: (s) => `${s.from}|${s.to}`,

    tidakDefault: (s) =>
      s.from !== AWAL_PENUH || s.to !== AKHIR_PENUH || s.granularity !== "month",
  },

  actions: {
    setRentang(from, to) {
      this.from = from;
      this.to = to;
    },

    toggleParsial() {
      const sertakan = this.sertakanParsial;
      this.from = sertakan ? AWAL_PENUH : TANGGAL_MIN;
      this.to = sertakan ? AKHIR_PENUH : TANGGAL_MAX;
    },

    pilihKategori(id, nama) {
      this.kategoriId = id;
      this.kategoriNama = nama;
    },

    reset() {
      this.from = AWAL_PENUH;
      this.to = AKHIR_PENUH;
      this.granularity = "month";
      this.kategoriId = null;
      this.kategoriNama = null;
    },
  },
});
