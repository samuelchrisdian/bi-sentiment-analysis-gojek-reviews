"""Pemuatan & validasi data mentah (Fase 1).

Satu-satunya pintu masuk data mentah. Notebook EDA memanggil modul ini,
bukan sebaliknya, agar Fase 2 memakai fungsi validasi yang sama persis.
"""
from __future__ import annotations

import hashlib
import pandas as pd

from .config import load_config, resolve
from .language_filter import tandai_inggris


def sha256_of_raw(cfg: dict | None = None) -> str:
    """Hash berkas mentah — dicatat di data_contract.md dan MANIFEST.json."""
    cfg = cfg or load_config()
    path = resolve(cfg, "paths.raw_csv")
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def validate_schema(df: pd.DataFrame, cfg: dict) -> None:
    expected = cfg["schema"]["expected_columns"]
    missing = set(expected) - set(df.columns)
    assert not missing, f"Kolom hilang: {missing}"
    n_expected = cfg["schema"]["expected_rows"]
    if n_expected is not None:
        assert len(df) == n_expected, f"Jumlah baris {len(df)} != {n_expected}"


def parse_types(df: pd.DataFrame, cfg: dict) -> pd.DataFrame:
    df = df.copy()
    df["Tanggal"] = pd.to_datetime(df["Tanggal"], errors="coerce", format="mixed")
    n_nat = int(df["Tanggal"].isna().sum())
    assert n_nat == 0, f"{n_nat} nilai Tanggal gagal di-parse"

    lo, hi = cfg["schema"]["valid_date_range"]
    assert df["Tanggal"].min() >= pd.Timestamp(lo), "Ada tanggal sebelum rentang sah"
    assert df["Tanggal"].max() <= pd.Timestamp(hi) + pd.Timedelta(days=1), \
        "Ada tanggal setelah rentang sah"

    df["Rating"] = df["Rating"].astype("int8")
    assert df["Rating"].between(1, 5).all(), "Ada Rating di luar 1-5"

    df["Likes"] = df["Likes"].fillna(0).astype("int32")
    assert (df["Likes"] >= 0).all(), "Ada Likes negatif"

    df["Versi App"] = df["Versi App"].astype("string")  # NULL dipertahankan
    df["Nama User"] = df["Nama User"].astype("string")
    df["Ulasan"] = df["Ulasan"].astype("string")
    assert df["Ulasan"].notna().all(), "Ada Ulasan bernilai null"
    return df


def derive_versi_minor(s: pd.Series) -> pd.Series:
    """'4.93.1' -> '4.93'; NaN tetap NaN."""
    return s.str.extract(r"^(\d+\.\d+)")[0].astype("string")


def derive_word_count(s: pd.Series) -> pd.Series:
    return s.fillna("").str.split().str.len().astype("int16")


def load_raw(cfg: dict | None = None) -> pd.DataFrame:
    cfg = cfg or load_config()
    # utf-8-sig: CSV hasil scraping diawali BOM, yang tanpa ini menempel pada
    # nama kolom pertama.
    df = pd.read_csv(resolve(cfg, "paths.raw_csv"), encoding="utf-8-sig")
    peta = cfg["schema"].get("source_columns")
    if peta:
        hilang = set(peta) - set(df.columns)
        assert not hilang, f"Kolom sumber hilang: {hilang}"
        df = df.rename(columns=peta)[["reviewId", *peta.values()]]
    validate_schema(df, cfg)
    # Ulasan tanpa teks tidak dapat dianalisis dan dikeluarkan secara eksplisit
    # (data scraping memuat 7 baris seperti ini).
    df = df[df["Ulasan"].fillna("").astype(str).str.strip() != ""]
    df = parse_types(df, cfg)

    mode = cfg.get("language_filter", {}).get("mode", "off")
    inggris = tandai_inggris(df["Ulasan"], cfg)
    if mode == "drop":
        df = df[~inggris].reset_index(drop=True)
    elif mode == "translate":
        df = terapkan_terjemahan(df, inggris, cfg)
    n_analisis = cfg["schema"].get("expected_rows_analysis")
    if n_analisis is not None:
        assert len(df) == n_analisis, f"Baris dianalisis {len(df)} != {n_analisis}"
    # Indeks harus rapat 0..n-1: preprocess menempelkan kolom turunan yang
    # dibangun sebagai Series/list berindeks posisi.
    return df.drop(columns="reviewId").reset_index(drop=True)


def terapkan_terjemahan(df: pd.DataFrame, inggris: pd.Series, cfg: dict) -> pd.DataFrame:
    """Ganti teks ulasan dominan Inggris dengan terjemahannya (ml/src/translate.py)."""
    path = resolve(cfg, "translation.output_csv")
    assert path.exists(), (f"{path} belum ada — jalankan "
                           "`.venv-translate/bin/python -m ml.src.translate` lebih dulu")
    tr = pd.read_csv(path).set_index("reviewId")["content_terjemahan"]
    ids = df.loc[inggris, "reviewId"]
    belum = ~ids.isin(tr.index)
    assert not belum.any(), (f"{int(belum.sum())} ulasan Inggris belum diterjemahkan — "
                             "jalankan ulang ml.src.translate")
    df = df.copy()
    df.loc[inggris, "Ulasan"] = ids.map(tr).astype("string").to_numpy()
    return df


def ringkasan_saring_bahasa(cfg: dict | None = None) -> dict:
    """Jumlah ulasan dominan Inggris (diterjemahkan/dikeluarkan), per rating."""
    cfg = cfg or load_config()
    mentah = pd.read_csv(resolve(cfg, "paths.raw_csv"), encoding="utf-8-sig")
    mentah = mentah.rename(columns=cfg["schema"]["source_columns"])
    inggris = tandai_inggris(mentah["Ulasan"], cfg)
    return {"n_mentah": len(mentah), "n_inggris": int(inggris.sum()),
            "n_analisis": int((~inggris).sum()) if cfg["language_filter"]["mode"] == "drop"
                          else len(mentah),
            "inggris_per_rating": mentah.loc[inggris, "Rating"]
                                        .value_counts().sort_index().to_dict()}


if __name__ == "__main__":
    cfg = load_config()
    df = load_raw(cfg)
    r = ringkasan_saring_bahasa(cfg)
    print(f"Mentah {r['n_mentah']:,} baris; dominan Inggris "
          f"{r['n_inggris']:,} (mode: {cfg['language_filter']['mode']}); "
          f"per rating {r['inggris_per_rating']}")
    print(f"OK — {len(df):,} baris dianalisis, {len(df.columns)} kolom")
    print(f"Periode: {df['Tanggal'].min().date()} .. {df['Tanggal'].max().date()}")
    print(f"SHA-256: {sha256_of_raw(cfg)}")
