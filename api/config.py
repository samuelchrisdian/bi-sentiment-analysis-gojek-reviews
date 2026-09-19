"""Konfigurasi API (Fase 7, T-7.1).

Dua sumber, dengan pembagian yang tegas:

* `.env` / environment — hal yang berubah antar lingkungan (DSN, direktori
  artefak, origin CORS).
* `ml/config.yaml` — parameter metodologis (ambang jumlah ulasan per versi,
  baseline mayoritas, bulan parsial). Nilai-nilai ini TIDAK boleh ditulis
  ulang di sini; `ml/config.yaml` adalah sumber kebenaran tunggal proyek
  (Fase 0, T-0.4) dan API hanya membacanya.
"""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT = Path(__file__).resolve().parents[1]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=ROOT / ".env", env_file_encoding="utf-8", extra="ignore",
        protected_namespaces=(),
    )

    database_url: str = "postgresql+psycopg2://gojek:gojek@localhost:5433/gojek_sentiment"
    artifacts_dir: Path = ROOT / "ml" / "artifacts"
    cors_origins: list[str] = ["http://localhost:5173", "http://localhost:4173"]

    # Nama model produksi — gerbang H-10, docs/model_decision.md.
    # Materialized view agg_* memakai nama yang sama; bila diubah di sini tanpa
    # me-refresh view, angka dashboard dan /predict akan berbeda model.
    model_produksi: str = "logistic_regression_final"

    page_size_default: int = 20
    page_size_max: int = 100
    predict_max_chars: int = 1000


@lru_cache
def get_settings() -> Settings:
    return Settings()


@lru_cache
def get_ml_config() -> dict:
    """ml/config.yaml, dibaca lewat loader Fase 0 — bukan parser sendiri."""
    from ml.src.config import load_config

    return load_config(ROOT / "ml" / "config.yaml")
