"""Loader konfigurasi tunggal. Seluruh script membaca config lewat modul ini."""
from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parents[2]


def load_config(path: str | Path | None = None) -> dict:
    path = Path(path) if path else ROOT / "ml" / "config.yaml"
    with open(path, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    cfg["_root"] = ROOT
    return cfg


def resolve(cfg: dict, key_path: str) -> Path:
    """resolve(cfg, 'paths.raw_csv') -> Path absolut."""
    node = cfg
    for k in key_path.split("."):
        node = node[k]
    return cfg["_root"] / node
