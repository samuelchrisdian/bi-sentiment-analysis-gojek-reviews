"""Pemuatan & validasi data mentah (Fase 1, T-1.1).

Satu-satunya pintu masuk data mentah. Notebook EDA memanggil modul ini,
bukan sebaliknya, agar Fase 2 memakai fungsi validasi yang sama persis.
"""
from __future__ import annotations

import hashlib
import pandas as pd

from .config import load_config, resolve


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
    df = pd.read_csv(resolve(cfg, "paths.raw_csv"))
    validate_schema(df, cfg)
    return parse_types(df, cfg)


if __name__ == "__main__":
    cfg = load_config()
    df = load_raw(cfg)
    print(f"OK — {len(df):,} baris, {len(df.columns)} kolom")
    print(f"Periode: {df['Tanggal'].min().date()} .. {df['Tanggal'].max().date()}")
    print(f"SHA-256: {sha256_of_raw(cfg)}")
