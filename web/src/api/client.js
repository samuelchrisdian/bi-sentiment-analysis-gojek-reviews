import axios from "axios";

export const client = axios.create({
  baseURL: import.meta.env.VITE_API_BASE || "http://localhost:8000",
  timeout: 30000,
});

/** Mengubah galat axios menjadi pesan berbahasa Indonesia yang bisa ditampilkan.
 *
 * 404 diperlakukan khusus: API mengembalikannya ketika rentang filter tidak
 * memuat satu baris pun. Itu keadaan KOSONG, bukan kegagalan — komponen perlu
 * membedakannya supaya bisa menawarkan tombol reset filter, bukan tombol
 * "coba lagi" yang tidak akan menolong. */
export function bacaGalat(err) {
  const status = err?.response?.status;
  const detail = err?.response?.data?.detail;

  if (status === 404) {
    return { kosong: true, pesan: detail || "Tidak ada data pada rentang ini." };
  }
  if (status === 422) {
    const d = Array.isArray(detail) ? detail[0]?.msg : detail;
    return { kosong: false, pesan: d || "Parameter filter tidak valid." };
  }
  if (err?.code === "ECONNABORTED") {
    return { kosong: false, pesan: "Permintaan melewati batas waktu." };
  }
  if (!err?.response) {
    return { kosong: false, pesan: "API tidak dapat dihubungi. Pastikan layanan berjalan di " + client.defaults.baseURL + "." };
  }
  return { kosong: false, pesan: detail || `Galat ${status} dari API.` };
}
