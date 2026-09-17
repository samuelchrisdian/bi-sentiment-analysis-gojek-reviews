"""Membangun 02_model_comparison.ipynb (Fase 3, T-3.9).

Notebook memanggil ml/src/train.py dan ml/src/viz_models.py, tidak
menduplikasi logikanya, agar angka notebook identik dengan angka yang dipakai
fase berikutnya.
"""
from pathlib import Path
import nbformat as nbf

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "ml" / "notebooks" / "02_model_comparison.ipynb"

CELLS = [
    ("md", """# 02 — Baseline & Komparasi Model
**Fase 3** · Menjawab Rumusan Masalah 1

Empat model dilatih dengan konfigurasi TF-IDF dan `random_state` identik,
sehingga perbedaan skor benar-benar berasal dari algoritmanya.

**Accuracy bukan metrik utama.** Dengan komposisi 72,3% positif, model yang
selalu menebak "positif" langsung memperoleh akurasi 72,3% tanpa mempelajari
apa pun. Prioritas: recall kelas negatif → macro-F1 → F1 negatif."""),
    ("code", """%load_ext autoreload
%autoreload 2
import sys, pathlib
ROOT = pathlib.Path.cwd().parents[1] if pathlib.Path.cwd().name == 'notebooks' else pathlib.Path.cwd()
sys.path.insert(0, str(ROOT))
import pandas as pd
from ml.src.config import load_config
cfg = load_config()
pd.set_option('display.width', 140)
print('seed:', cfg['seed'], '| baseline referensi:', cfg['evaluation']['majority_baseline'])"""),
    ("md", """## 1. Urutan yang tidak boleh dibalik

1. **split stratified** — sebelum apa pun yang melihat data
2. **deduplikasi** — HANYA training set
3. **fit vectorizer** — HANYA pada training set

Mem-fit TF-IDF pada data penuh, atau mendeduplikasi test set, adalah kebocoran
data yang membatalkan seluruh angka di fase ini."""),
    ("code", "from ml.src.train import siapkan_data\nd = siapkan_data(dedup=True)"),
    ("md", "## 2. Tabel hasil lengkap\n\n4 model × 2 set evaluasi + baseline."),
    ("code", """m = pd.read_csv(ROOT / 'docs/tables/model_metrics.csv')
m = m[m.dedup_training]
m[['model_name','eval_set','n_eval','macro_f1','recall_neg','f1_neg','accuracy','train_seconds']].round(4)"""),
    ("md", """## 3. Baseline yang harus dikalahkan

Baseline mayoritas dihitung **sebelum** model apa pun dilatih. Model yang tidak
mengungguli macro-F1 baseline tidak mempelajari apa pun."""),
    ("code", """base = m[m.model_name=='majority_baseline']
display(base[['eval_set','accuracy','macro_f1','recall_neg']].round(4))
mdl = m[m.model_name!='majority_baseline']
b = base[base.eval_set=='full'].macro_f1.iloc[0]
print(f"seluruh model mengungguli baseline macro_f1={b:.4f}:",
      bool((mdl[mdl.eval_set=='full'].macro_f1 > b).all()))"""),
    ("md", "## 4. Gambar 10 — perbandingan model"),
    ("code", "from ml.src import viz_models\nviz_models.gambar_10_perbandingan().round(4)"),
    ("md", """## 5. Gambar 11 — temuan metodologis utama

Selisih macro-F1 antara set `full` dan `informative_ge5w` mengukur seberapa
besar kinerja model bertumpu pada kata pujian pendek yang berulang — 39,9%
ulasan hanya berisi ≤2 kata dan hampir seluruhnya positif (Temuan 2)."""),
    ("code", "viz_models.gambar_11_selisih().round(4)"),
    ("md", "## 6. Gambar 12 — waktu latih\n\nDiukur `time.perf_counter()`, bukan dikira-kira."),
    ("code", "viz_models.gambar_12_waktu().round(4)"),
    ("md", """## 7. Dampak deduplikasi training

Varian dengan dan tanpa deduplikasi dijalankan dengan konfigurasi identik.
Selisihnya adalah bukti kuantitatif pengaruh 32,1% duplikat teks."""),
    ("code", "pd.read_csv(ROOT / 'docs/tables/dedup_impact.csv').round(4)"),
]


def main() -> None:
    nb = nbf.v4.new_notebook()
    nb.cells = [nbf.v4.new_markdown_cell(s) if k == "md" else nbf.v4.new_code_cell(s)
                for k, s in CELLS]
    nb.metadata = {"kernelspec": {"display_name": "Python 3", "language": "python",
                                  "name": "python3"},
                   "language_info": {"name": "python"}}
    nbf.write(nb, OUT)
    print(f"Ditulis: {OUT.relative_to(ROOT)} ({len(nb.cells)} sel)")


if __name__ == "__main__":
    main()
