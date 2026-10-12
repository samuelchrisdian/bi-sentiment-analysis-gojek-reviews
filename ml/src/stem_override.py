"""Pengecualian stemming (Fase 2, hasil verifikasi manual pra-pemrosesan).

Sastrawi mengupas afiks secara agresif dan pada sebagian kata menghasilkan
bentuk yang salah atau menggeser makna, mis.:

    pengemudi    -> kemudi    (pelaku menjadi alat kemudi)
    pengemudinya -> mud       (bentuk tidak bermakna)
    lemot        -> lot       (token sentimen negatif hilang)

Asal masalahnya: pemetaan kamus slang `driver` -> `pengemudi` benar secara
linguistik, tetapi justru menyerahkan bentuk turunan berimbuhan kepada stemmer. Kata `driver` yang dibiarkan apa adanya tidak akan tersentuh.
Interaksi antar tahap inilah yang membuat pemeriksaan manual tidak tergantikan.

STEM_OVERRIDE memaksa hasil stem untuk kata-kata ini. Nilai yang sama dengan
kuncinya berarti "jangan di-stem sama sekali".
"""
from __future__ import annotations

STEM_OVERRIDE: dict[str, str] = {
    # Entitas domain — pelaku, bukan konsep
    "pengemudi": "pengemudi",
    "pengemudinya": "pengemudi",
    "pelanggan": "pelanggan",
    "pelanggannya": "pelanggan",
    "penumpang": "penumpang",
    "penumpangnya": "penumpang",
    "pengguna": "pengguna",
    "penggunanya": "pengguna",
    "pengalaman": "pengalaman",

    # Token sentimen yang rusak bila di-stem
    "lemot": "lemot",
    "terbaik": "terbaik",          # superlatif hilang bila menjadi `baik`
    "memuaskan": "puas",           # `muas` bukan bentuk yang wajar
    "disayangkan": "disayangkan",  # `sayang` membalik polaritas
    "penanganan": "penanganan",    # `tangan` menghilangkan makna
    "semaunya": "semaunya",        # `mau` mengubah makna frasa
    "sebelah": "sebelah",          # `belah` merusak frasa `aplikasi sebelah`
    "memesan": "pesan",            # `mes` tidak bermakna
    "pemesanan": "pesan",

    # --- Tambahan verifikasi manual data awal putaran 2 ---
    # KRITIS: `sebelumnya` -> `belum` menyuntikkan NEGASI yang tidak pernah ditulis pengguna.
    "sebelumnya": "sebelumnya",
    "sebelum": "sebelum",

    # Verba aksi yang menjadi kata sifat / bentuk tak bermakna
    "perbaiki": "perbaiki",
    "memperbaiki": "perbaiki",
    "diperbaiki": "perbaiki",
    "dibenahi": "benahi",
    "benahin": "benahi",
    "ditingkatkan": "tingkatkan",
    "meningkatkan": "tingkatkan",
    "mengemis": "mengemis",       # `emis` bukan bentuk yang sah
    "tertera": "tertera",         # `tera` bermakna lain
    "mempermudah": "permudah",
    "menyediakan": "sedia",
    "pembuat": "pembuat",         # pelaku, bukan aksi `buat`
    "kebijakan": "kebijakan",     # `bijak` menghilangkan makna kebijakan
    "kesejahteraan": "sejahtera",

    # --- Tambahan verifikasi manual data awal putaran 3 ---
    # Yang MEMBALIK atau melemahkan sentimen bila di-stem
    "seenaknya": "seenaknya",       # -> `enak`: keluhan menjadi terdengar positif
    "menyusahkan": "menyusahkan",   # -> `susah`: "jangan menyusahkan" != "jangan susah"
    "perbanyak": "perbanyak",       # -> `banyak`: permintaan menjadi pernyataan
    "banyakin": "perbanyak",
    "memperbanyak": "perbanyak",

    # Konsep domain yang hilang bila di-stem
    "pembaruan": "pembaruan",       # -> `baru`: konsep update lenyap
    "terbaru": "terbaru",
    "diperbarui": "pembaruan",
    "disetujui": "disetujui",       # -> `tuju`: makna persetujuan hilang
    "menyetujui": "disetujui",
    "keselamatan": "keselamatan",   # -> `selamat`
    "diberlakukan": "berlaku",      # -> `laku`
    "berlaku": "berlaku",
    "tujuannya": "tujuan",
    "dibenahi": "dibenahi",         # pasif dipertahankan
    "sebagainya": "sebagainya",     # -> `bagai`: frasa "dan sebagainya" rusak

    # --- Tambahan verifikasi data scraping putaran 2 ---
    # Ditemukan pemeriksa dan diukur di seluruh korpus (dokumen mentah).
    "sejauh": "sejauh",             # -> `jauh`: "sejauh ini bagus" menjadi keluhan jarak (1.887 dok; muncul di dua putaran)
    "penerima": "penerima",         # -> `terima`: pihak penerima tertukar dengan status diterima (248 dok)
    "setuju": "setuju",             # -> `tuju`: "tidak setuju" menjadi "tidak tuju" (98 dok)
    "tertarik": "tertarik",         # -> `tarik`: bentrok dengan "tarik saldo"
    "menarik": "menarik",

    # --- Tambahan verifikasi data scraping putaran 3 ---
    # `acc` -> `setujui` (kamus) lalu di-stem menjadi `tuju`, akar yang sama
    # dengan `tujuan`: "ACC pengajuan" tercampur dengan tujuan perjalanan (438 dok).
    "setujui": "disetujui",
}
