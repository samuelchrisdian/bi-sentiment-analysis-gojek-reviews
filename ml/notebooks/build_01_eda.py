"""Membangun 01_eda.ipynb dari definisi sel di bawah (Fase 1, T-1.2).

Notebook sengaja digenerate agar isinya selalu sinkron dengan ml/src/eda.py —
notebook memanggil modul, tidak menduplikasi logikanya.
"""
from pathlib import Path
import nbformat as nbf

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "ml" / "notebooks" / "01_eda.ipynb"

CELLS: list[tuple[str, str]] = [
    ("md", """# 01 — EDA & Data Contract
**Fase 1** · Sistem Analisis Sentimen Ulasan Gojek

Notebook ini **memanggil** `ml/src/eda.py`; ia tidak menduplikasi logikanya.
Dengan begitu angka di notebook dan angka yang dipakai fase berikutnya dijamin identik.

Sumber data: `data/raw/ulasan_com.gojek.app.csv` — unduhan langsung Kaggle
(`pandaa12`, versi 1), tanpa modifikasi. Lihat `docs/data_provenance_notes.md`."""),
    ("code", """%load_ext autoreload
%autoreload 2

import sys, pathlib
ROOT = pathlib.Path.cwd().parents[1] if pathlib.Path.cwd().name == 'notebooks' else pathlib.Path.cwd()
sys.path.insert(0, str(ROOT))

import pandas as pd
from ml.src.config import load_config
from ml.src import eda

pd.set_option('display.width', 120)
cfg = load_config()
print('seed:', cfg['seed'], '| skema label:', cfg['labeling']['scheme'])"""),
    ("md", "## 1. Muat & validasi data\n\nValidasi skema dilakukan di `ingest.py` lewat `assert` — bila sel ini lolos, kontrak data terpenuhi."),
    ("code", """from ml.src.ingest import load_raw
df = eda.prepare(load_raw(cfg))
print(df.shape)
df.head(3)"""),
    ("md", "## 2. Profil dasar\n\n> Menghasilkan `[A-01]`, `[A-02]`"),
    ("code", "eda.profil_dataset(df)"),
    ("md", "## 3. Duplikasi\n\n> Menghasilkan `[A-03]` — bahan Temuan 2"),
    ("code", "eda.duplikasi(df)"),
    ("md", "## 4. Distribusi rating → **Gambar 1**"),
    ("code", "eda.distribusi_rating(df)"),
    ("md", """## 5. Asimetri panjang ulasan → **Gambar 2**

Ini temuan paling kritis (Temuan 2). Perbedaan panjang antar kelas menentukan
seluruh protokol evaluasi di Fase 3."""),
    ("code", "eda.panjang_per_rating(df)"),
    ("md", "### 5b. Ulasan sangat pendek → **Gambar 3**"),
    ("code", """display(eda.ulasan_pendek(df))
pd.read_csv(ROOT / 'docs/tables/teks_paling_berulang.csv').head(10)"""),
    ("md", """## 6. Kontras kelas negatif vs positif

Korpus negatif jauh lebih bersih — inilah alasan ekstraksi topik (Fase 5)
hanya dijalankan pada kelas negatif."""),
    ("code", "eda.kontras_kelas(df)"),
    ("md", """## 7. Kelayakan skema 3 kelas → dasar keputusan H-3

> Menghasilkan `[A-23]` (baseline mayoritas) dan `[A-24]` (rasio kelas netral)"""),
    ("code", "eda.komposisi_kelas(df)"),
    ("md", "## 8. Analisis versi aplikasi → **Gambar 5**"),
    ("code", "eda.cakupan_versi(df)"),
    ("md", "## 9. Profil kolom Likes\n\nDistribusi sangat timpang — dipakai sebagai filter dashboard, bukan fitur model."),
    ("code", "eda.profil_likes(df)"),
    ("md", "## 10. Volume temporal → **Gambar 4**"),
    ("code", "eda.volume_bulanan(df)"),
    ("md", """## 11. Tabel rujukan angka

`angka_storytelling.csv` berisi kolom `kalimat_siap_tempel` — dipakai saat
menulis naskah (di luar repo, per H-4) agar tidak ada angka yang ditulis dari ingatan."""),
    ("code", """angka = pd.read_csv(ROOT / 'docs/tables/angka_storytelling.csv')
for r in angka.itertuples():
    print(f"[{r.label}] {r.kalimat_siap_tempel}")"""),
]


def main() -> None:
    nb = nbf.v4.new_notebook()
    nb.cells = [nbf.v4.new_markdown_cell(src) if kind == "md" else nbf.v4.new_code_cell(src)
                for kind, src in CELLS]
    nb.metadata = {"kernelspec": {"display_name": "Python 3", "language": "python",
                                  "name": "python3"},
                   "language_info": {"name": "python"}}
    nbf.write(nb, OUT)
    print(f"Ditulis: {OUT.relative_to(ROOT)} ({len(nb.cells)} sel)")


if __name__ == "__main__":
    main()
