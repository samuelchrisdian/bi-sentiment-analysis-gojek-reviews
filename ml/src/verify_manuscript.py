"""Verifikasi silang angka naskah Fase 10 terhadap facts.yaml (T-10.7).

Setiap angka yang muncul di ``research-paper.md``, ``article-popular.md``,
``abstract-id.md``, dan ``abstract-en.md`` harus dapat ditemukan kembali di
``docs/synthesis/facts.yaml`` — berkas yang seluruh isinya dihitung ulang dari
CSV dan laporan JSON oleh ``ml/src/collect_facts.py``.

    python -m ml.src.verify_manuscript

Keluar dengan kode 1 bila ada peringatan, sehingga dapat dipakai sebagai
gerbang otomatis sebelum commit.

Yang **tidak** diperiksa (dan alasannya):

* Isi komentar rujukan ``<!-- src: ... -->``, blok kode, *inline code*, dan
  target tautan/gambar — bagian itu memuat path berkas dan perintah yang
  angkanya bukan klaim hasil.
* Angka penomoran bagian, tahun, dan parameter konfigurasi — didaftarkan
  eksplisit di ``facts.yaml`` pada seksi ``angka_struktural`` agar tetap dapat
  diaudit, bukan disembunyikan dalam kode.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
SYNTH = ROOT / "docs" / "synthesis"
FACTS = SYNTH / "facts.yaml"
REPORT = SYNTH / "verification_report.txt"

NASKAH = [
    "research-paper.md",
    "article-popular.md",
    "abstract-id.md",
    "abstract-en.md",
]

# Pola angka: konvensi Indonesia (26.732 / 0,9336) maupun Inggris (26,732 / 0.9336).
RIBUAN_ID = r"\d{1,3}(?:\.\d{3})+(?:,\d+)?(?![\d.])"
RIBUAN_EN = r"\d{1,3}(?:,\d{3})+(?:\.\d+)?(?![\d,])"
POLA_ANGKA = re.compile(
    rf"{RIBUAN_ID}|{RIBUAN_EN}"
    r"|\d+,\d+"  # 0,9336
    r"|\d+(?:\.\d+)?"  # 0.9336 atau 1040
)

BUANG = [
    (re.compile(r"```.*?```", re.S), " "),  # blok kode
    (re.compile(r"<!--.*?-->", re.S), " "),  # komentar rujukan
    (re.compile(r"`[^`\n]*`"), " "),  # inline code
    (re.compile(r"\]\([^)]*\)"), "] "),  # target tautan & gambar
    (re.compile(r"https?://\S+"), " "),  # URL telanjang
    (re.compile(r"§\s*\d+(?:\.\d+)*"), " "),  # rujukan silang antar-bagian
    (re.compile(r"^\s*#{1,6}\s*\d+(?:\.\d+)*"), " "),  # penomoran judul
    (re.compile(r"(?:Bagian|Lampiran|Tabel|Gambar)\s+\d+[a-z]?(?:\.\d+)*"), " "),
]


def nilai_numerik(obj) -> list[float]:
    """Kumpulkan seluruh nilai numerik dari struktur YAML, rekursif."""
    keluar: list[float] = []
    if isinstance(obj, dict):
        for v in obj.values():
            keluar += nilai_numerik(v)
    elif isinstance(obj, (list, tuple)):
        for v in obj:
            keluar += nilai_numerik(v)
    elif isinstance(obj, bool):
        pass
    elif isinstance(obj, (int, float)):
        keluar.append(float(obj))
    elif isinstance(obj, str):
        # String seperti "C=1.0" atau "{'alpha': 0.5}" tetap membawa angka sah.
        for m in POLA_ANGKA.finditer(obj):
            n = ke_float(m.group())
            if n is not None:
                keluar.append(n)
    return keluar


def ke_float(teks: str) -> float | None:
    """Ubah angka bergaya Indonesia maupun mesin menjadi float."""
    t = teks.strip()
    if re.fullmatch(r"\d{1,3}(?:\.\d{3})+(?:,\d+)?", t):  # 26.732,5 (ID)
        t = t.replace(".", "").replace(",", ".")
    elif re.fullmatch(r"\d{1,3}(?:,\d{3})+(?:\.\d+)?", t):  # 26,732.5 (EN)
        t = t.replace(",", "")
    elif re.fullmatch(r"\d+,\d+", t):  # 0,9336
        t = t.replace(",", ".")
    try:
        return float(t)
    except ValueError:
        return None


def n_desimal(teks: str) -> int:
    if re.fullmatch(r"\d{1,3}(?:\.\d{3})+,\d+", teks):  # 26.732,5 (ID)
        return len(teks.split(",")[1])
    if re.fullmatch(r"\d{1,3}(?:,\d{3})+\.\d+", teks):  # 26,732.5 (EN)
        return len(teks.split(".")[1])
    if re.fullmatch(r"\d{1,3}(?:[.,]\d{3})+", teks):  # bilangan bulat beribuan
        return 0
    for sep in (",", "."):
        if re.fullmatch(rf"\d+\{sep}\d+", teks):
            return len(teks.split(sep)[1])
    return 0


def bersihkan(baris: str) -> str:
    for pola, ganti in BUANG:
        baris = pola.sub(ganti, baris)
    return baris


def bersihkan_blok(teks: str) -> str:
    """Hilangkan blok multi-baris lebih dulu, pertahankan jumlah baris."""
    for pola, _ in BUANG[:2]:
        teks = pola.sub(lambda m: "\n" * m.group().count("\n"), teks)
    return teks


def periksa(path: Path, diizinkan: list[float]) -> list[str]:
    peringatan: list[str] = []
    teks = bersihkan_blok(path.read_text(encoding="utf-8"))
    for no, baris in enumerate(teks.splitlines(), start=1):
        for m in POLA_ANGKA.finditer(bersihkan(baris)):
            tulis = m.group()
            nilai = ke_float(tulis)
            if nilai is None:
                continue
            d = n_desimal(tulis)
            cocok = any(
                round(a, d) == round(nilai, d) or round(a * 100, d) == round(nilai, d)
                for a in diizinkan
            )
            if not cocok:
                peringatan.append(
                    f"PERINGATAN: angka '{tulis}' di {path.name}:{no} "
                    f"tidak ada di facts.yaml"
                )
    return peringatan


def main() -> int:
    if not FACTS.exists():
        print(f"❌ {FACTS} tidak ada — jalankan `python -m ml.src.collect_facts` dulu.")
        return 1

    facts = yaml.safe_load(FACTS.read_text(encoding="utf-8"))
    diizinkan = sorted(set(nilai_numerik(facts)))

    baris_laporan = [
        "LAPORAN VERIFIKASI ANGKA NASKAH — Fase 10, T-10.7",
        f"Sumber angka : docs/synthesis/facts.yaml ({len(diizinkan)} nilai unik)",
        f"Naskah diuji : {', '.join(NASKAH)}",
        "",
    ]
    total = 0
    for nama in NASKAH:
        path = SYNTH / nama
        if not path.exists():
            baris_laporan.append(f"{nama:24} — ❌ berkas tidak ditemukan")
            total += 1
            continue
        peringatan = periksa(path, diizinkan)
        total += len(peringatan)
        status = "✅ nol peringatan" if not peringatan else f"⚠️  {len(peringatan)} peringatan"
        baris_laporan.append(f"{nama:24} — {status}")
        baris_laporan += [f"    {p}" for p in peringatan]

    baris_laporan += ["", f"TOTAL PERINGATAN: {total}"]
    isi = "\n".join(baris_laporan) + "\n"
    REPORT.write_text(isi, encoding="utf-8")
    print(isi, end="")
    return 1 if total else 0


if __name__ == "__main__":
    sys.exit(main())
