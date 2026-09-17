"""Pengecualian stemming (Fase 2 — hasil gerbang H-6 putaran 1).

Sastrawi mengupas afiks secara agresif dan pada sebagian kata menghasilkan
bentuk yang salah atau menggeser makna. Pemeriksaan manual 100 sampel oleh
manusia menemukan 25 kasus semacam itu; dampaknya diukur di seluruh korpus:

    pengemudi    -> kemudi    12.419 dokumen   (pelaku menjadi alat kemudi)
    pengemudinya -> mud        3.095 dokumen   (bentuk tidak bermakna)
    pelanggan    -> langgan    3.440 dokumen
    kasian       -> kasi         645 dokumen
    penumpang    -> tumpang      636 dokumen
    lemot        -> lot          402 dokumen   (token sentimen negatif hilang)

Perhatikan asal masalahnya: pemetaan `driver` -> `pengemudi` pada gerbang H-5
benar secara linguistik, tetapi justru menyerahkan bentuk turunan berimbuhan
kepada stemmer. Kata `driver` yang dibiarkan apa adanya tidak akan tersentuh.
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
}
