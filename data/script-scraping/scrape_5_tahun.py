"""Scraping ulasan Gojek di Google Play untuk rentang lima tahun.

Mengambil ulasan `com.gojek.app` (negara Indonesia) dengan urutan terbaru
(Sort.NEWEST) halaman demi halaman memakai continuation token, sampai ulasan
tertua pada satu halaman sudah lebih tua dari TANGGAL_AWAL. Hasil dipotong ke
rentang [TANGGAL_AWAL, TANGGAL_AKHIR] dan disimpan apa adanya (kolom keluaran
scraper) ditambah kolom `lang_query`.

Pengambilan dilakukan DUA kali, dengan `lang="id"` dan `lang="en"`. Google Play
mengelompokkan ulasan menurut bahasa yang terkait dengan penulisnya, bukan
menurut bahasa teksnya: ulasan berbahasa Indonesia dari pengguna yang perangkatnya
berbahasa Inggris hanya muncul pada `lang="en"`, dan kedua himpunan tidak
beririsan. Hanya mengambil `lang="id"` akan kehilangan ulasan tersebut.

Progres disimpan berkala ke berkas checkpoint, sehingga run yang terputus dapat
dilanjutkan dengan menjalankan skrip yang sama.

    .venv/bin/python data/script-scraping/scrape_5_tahun.py
"""
from __future__ import annotations

import json
import pickle
import sys
import time
from datetime import datetime, timezone
from importlib.metadata import version
from pathlib import Path

import pandas as pd
from google_play_scraper import Sort, reviews

APP_ID = "com.gojek.app"
LANGS, COUNTRY = ("id", "en"), "id"
PER_HALAMAN = 200
TANGGAL_AWAL = pd.Timestamp("2021-10-01")
TANGGAL_AKHIR = pd.Timestamp("2026-09-30 23:59:59")

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "data" / "raw"
KELUARAN = RAW / "gojek_reviews_5Y.csv"
META = RAW / "gojek_reviews_5Y.meta.json"
BAGIAN = RAW / "bagian"


def _ambil(lang, token):
    for coba in range(6):
        try:
            return reviews(APP_ID, lang=lang, country=COUNTRY, sort=Sort.NEWEST,
                           count=PER_HALAMAN, continuation_token=token)
        except Exception as e:                      # jaringan / batas laju
            tunggu = 5 * 2 ** coba
            print(f"  galat: {e!r}; coba lagi dalam {tunggu} s", flush=True)
            time.sleep(tunggu)
    raise RuntimeError("Gagal enam kali berturut-turut")


def scrape(lang: str) -> None:
    """Satu putaran pengambilan untuk satu nilai `lang`; hasil ke data/raw/bagian/."""
    keluaran = BAGIAN / f"gojek_reviews_5Y_{lang}.csv"
    meta_path = keluaran.with_suffix(".meta.json")
    if keluaran.exists():
        print(f"[{lang}] sudah ada: {keluaran.name}", flush=True)
        return
    BAGIAN.mkdir(parents=True, exist_ok=True)
    CHECKPOINT = BAGIAN / f".checkpoint_{lang}.pkl"
    if CHECKPOINT.exists():
        st = pickle.loads(CHECKPOINT.read_bytes())
        print(f"Melanjutkan dari checkpoint: {len(st['baris']):,} ulasan", flush=True)
    else:
        st = {"baris": [], "token": None, "mulai": datetime.now(timezone.utc).isoformat(),
              "halaman": 0}

    t0 = time.perf_counter()
    while True:
        hasil, token = _ambil(lang, st["token"])
        st["halaman"] += 1
        if not hasil:
            print("Halaman kosong — Google Play tidak mengembalikan ulasan lagi.", flush=True)
            break
        st["baris"].extend(hasil)
        st["token"] = token
        tertua = min(r["at"] for r in hasil)
        if st["halaman"] % 25 == 0:
            CHECKPOINT.write_bytes(pickle.dumps(st))
            laju = len(st["baris"]) / max(time.perf_counter() - t0, 1e-9)
            print(f"  {len(st['baris']):,} ulasan · tertua {tertua:%Y-%m-%d} · "
                  f"{laju:.0f} ulasan/detik", flush=True)
        if pd.Timestamp(tertua) < TANGGAL_AWAL:
            print(f"Melewati batas awal ({tertua:%Y-%m-%d}).", flush=True)
            break
        if token is None or token.token is None:
            print("Continuation token habis.", flush=True)
            break

    df = pd.DataFrame(st["baris"]).drop_duplicates("reviewId")
    df["at"] = pd.to_datetime(df["at"])
    n_semua = len(df)
    df = df[(df["at"] >= TANGGAL_AWAL) & (df["at"] <= TANGGAL_AKHIR)]
    df = df.sort_values("at", ascending=False)
    df.to_csv(keluaran, index=False)

    meta = {
        "app_id": APP_ID, "lang": lang, "country": COUNTRY, "sort": "NEWEST",
        "count_per_halaman": PER_HALAMAN,
        "rentang": [str(TANGGAL_AWAL.date()), str(TANGGAL_AKHIR.date())],
        "google_play_scraper": version("google-play-scraper"),
        "scraping_mulai_utc": st["mulai"],
        "scraping_selesai_utc": datetime.now(timezone.utc).isoformat(),
        "jumlah_halaman": st["halaman"],
        "ulasan_unik_terambil": n_semua,
        "ulasan_dalam_rentang": len(df),
        "tanggal_tertua_dalam_rentang": str(df["at"].min()),
        "tanggal_terbaru_dalam_rentang": str(df["at"].max()),
    }
    meta_path.write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")
    CHECKPOINT.unlink(missing_ok=True)
    print(json.dumps(meta, indent=2, ensure_ascii=False))


def gabung() -> None:
    """Gabungkan seluruh putaran menjadi satu berkas mentah."""
    bagian = []
    for lang in LANGS:
        d = pd.read_csv(BAGIAN / f"gojek_reviews_5Y_{lang}.csv")
        bagian.append(d.assign(lang_query=lang))
    df = pd.concat(bagian, ignore_index=True)
    n_ganda = int(df["reviewId"].duplicated().sum())
    df = df.drop_duplicates("reviewId").sort_values("at", ascending=False)
    df.to_csv(KELUARAN, index=False)
    meta = {"per_lang": {lang: json.loads((BAGIAN / f"gojek_reviews_5Y_{lang}.meta.json")
                                         .read_text()) for lang in LANGS},
            "reviewId_ganda_antar_lang": n_ganda,
            "ulasan_gabungan": len(df),
            "ulasan_per_lang_query": df["lang_query"].value_counts().to_dict()}
    META.write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({k: v for k, v in meta.items() if k != "per_lang"}, indent=2))


def main() -> None:
    for lang in LANGS:
        scrape(lang)
    gabung()


if __name__ == "__main__":
    sys.exit(main())
