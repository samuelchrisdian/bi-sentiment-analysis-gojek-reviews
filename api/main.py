"""Aplikasi FastAPI — 7 endpoint penyajian data (Fase 7).

Enam endpoint membaca agregat dari PostgreSQL; satu (`/api/predict`) memuat
model. Pembagian itu yang menentukan seluruh desain modul: SQL hidup di
`crud.py`, ML di `ml_service.py`, dan berkas ini hanya menangani HTTP —
parameter, kode status, dan perakitan respons.
"""
from __future__ import annotations

import sys
from contextlib import asynccontextmanager
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:                  # agar `import ml.src.preprocess` bekerja
    sys.path.insert(0, str(ROOT))

from fastapi import Depends, FastAPI, HTTPException, Query, Request  # noqa: E402
from fastapi.middleware.cors import CORSMiddleware                    # noqa: E402
from fastapi.responses import JSONResponse                            # noqa: E402
from sqlalchemy.exc import SQLAlchemyError                            # noqa: E402
from sqlalchemy.orm import Session                                    # noqa: E402

from . import crud, ml_service, schemas                               # noqa: E402
from .config import get_ml_config, get_settings                       # noqa: E402
from .db import get_db                                                # noqa: E402

S = get_settings()
MLCFG = get_ml_config()

ml: dict = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Artefak dimuat SEKALI di sini.

    Kegagalan tidak dilempar sebagai exception yang mematikan proses: enam dari
    tujuh endpoint sama sekali tidak memerlukan model, dan mematikan seluruh
    API karena satu endpoint demo rusak adalah kegagalan yang tidak sebanding.
    Yang dilakukan: status kegagalan disimpan, `/api/predict` mengembalikan 503
    dengan alasannya, dan `/api/health` melaporkannya.
    """
    try:
        ml.update(ml_service.muat())
        print(f"[lifespan] artefak dimuat: {ml['model_name']} "
              f"({ml['load_seconds']} s, predict_proba="
              f"{'ya' if ml['punya_proba'] else 'tidak'})", flush=True)
    except ml_service.ArtefakGagalDimuat as e:
        ml["error"] = str(e)
        print(f"[lifespan] GAGAL memuat artefak: {e}\n"
              f"[lifespan] /api/predict akan mengembalikan 503; "
              f"endpoint agregat tetap melayani.", flush=True)
    yield
    ml.clear()


app = FastAPI(
    title="Gojek Sentiment API",
    description=(
        "API analisis sentimen & topik keluhan ulasan Gojek.\n\n"
        "Enam endpoint membaca agregat pre-scoring dari PostgreSQL. "
        "`/api/predict` memuat model dan berfungsi sebagai demo kapabilitas — "
        "bukan sumber data dashboard."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=S.cors_origins,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


@app.exception_handler(SQLAlchemyError)
async def db_error_handler(request: Request, exc: SQLAlchemyError):
    return JSONResponse(
        status_code=503,
        content={"detail": f"Database tidak dapat dilayani: {type(exc).__name__}"})


def _ribuan(n: int) -> str:
    """Pemisah ribuan gaya Indonesia — TITIK, bukan koma. Catatan ini tampil apa
    adanya di dashboard berbahasa Indonesia."""
    return f"{n:,}".replace(",", ".")


# ------------------------------------------------------------ dependensi ---
def rentang(
    db: Session = Depends(get_db),
    dari: date | None = Query(None, alias="from",
                              description="Inklusif. Default: tanggal ulasan terawal."),
    sampai: date | None = Query(None, alias="to",
                                description="Inklusif. Default: tanggal ulasan terakhir."),
) -> tuple[Session, date, date]:
    d0, d1 = crud.rentang_default(db)
    dari, sampai = dari or d0, sampai or d1
    if dari > sampai:
        raise HTTPException(422, f"from ({dari}) melewati to ({sampai})")
    return db, dari, sampai


# ------------------------------------------------------------------- 1/7 ---
@app.get("/api/kpi", response_model=schemas.KpiResponse, tags=["agregat"],
         summary="Ringkasan KPI untuk kartu atas dashboard")
def baca_kpi(
    r=Depends(rentang),
    min_reviews: int = Query(None, ge=crud.AMBANG_MATVIEW,
                             description="Ambang jumlah ulasan per versi untuk "
                                         "menghitung `jumlah_versi`."),
):
    db, dari, sampai = r
    min_reviews = min_reviews or crud.AMBANG_MATVIEW
    row = crud.kpi(db, dari, sampai, min_reviews)
    if row is None:
        raise HTTPException(404, f"Tidak ada data pada rentang {dari} s/d {sampai}")

    m = crud.meta(db)
    catatan = [
        f"persen_negatif berasal dari model produksi '{S.model_produksi}' "
        f"(gerbang H-10); baseline_negatif berasal dari label aktual rating 1–2.",
        f"baseline_negatif dihitung atas {_ribuan(row['n_berlabel'])} ulasan berlabel; "
        f"{_ribuan(row['total_ulasan'] - row['n_berlabel'])} ulasan berating 3 tidak "
        f"punya label biner dan dikeluarkan dari pembanding itu.",
        f"versi_app kosong pada {m['versi_null_pct']}% ulasan — angka versi "
        f"tidak mencakup seluruh korpus.",
        f"jumlah_versi menghitung versi minor dengan >= {min_reviews} ulasan "
        f"sepanjang SELURUH periode, tidak mengikuti filter tanggal.",
    ]
    if row["bulan_parsial"]:
        catatan.append(
            "Bulan " + ", ".join(str(b) for b in row["bulan_parsial"]) +
            " berdata parsial (data mulai " + str(m["tanggal_min"].date()) + ").")

    return {
        "total_ulasan": row["total_ulasan"],
        "persen_negatif": float(row["persen_negatif"]),
        "baseline_negatif": float(row["baseline_negatif"]),
        "rata_rating": float(row["rata_rating"]),
        "jumlah_versi": row["jumlah_versi"],
        "versi_null_pct": float(m["versi_null_pct"]),
        "model_produksi": S.model_produksi,
        "periode": {"dari": dari, "sampai": sampai,
                    "bulan_parsial": row["bulan_parsial"]},
        "catatan": catatan,
    }


# ------------------------------------------------------------------- 2/7 ---
@app.get("/api/trend", response_model=schemas.TrendResponse, tags=["agregat"],
         summary="Deret waktu proporsi negatif & volume")
def baca_trend(
    r=Depends(rentang),
    granularity: schemas.Granularity = Query(schemas.Granularity.month),
):
    db, dari, sampai = r
    data = crud.trend(db, dari, sampai, granularity.value)
    if not data:
        raise HTTPException(404, f"Tidak ada data pada rentang {dari} s/d {sampai}")

    n_parsial = sum(1 for d in data if d["periode_parsial"])
    catatan = [
        f"Proporsi negatif menurut model produksi '{S.model_produksi}'.",
        "`periode_parsial=true` menandai titik dengan cakupan hari tidak penuh; "
        "titik itu wajib dianotasi di grafik, bukan dihapus diam-diam.",
    ]
    if granularity is schemas.Granularity.month:
        catatan.append(f"Bulan parsial menurut ml/config.yaml: {crud.BULAN_PARSIAL}.")
    if n_parsial:
        catatan.append(f"{n_parsial} dari {len(data)} titik berperiode parsial.")

    return {"granularity": granularity, "model_produksi": S.model_produksi,
            "catatan": catatan, "data": data}


# ------------------------------------------------------------------- 3/7 ---
@app.get("/api/versions", response_model=schemas.VersionsResponse, tags=["agregat"],
         summary="Proporsi sentimen per versi minor aplikasi")
def baca_versions(
    db: Session = Depends(get_db),
    min_reviews: int = Query(
        None, ge=crud.AMBANG_MATVIEW,
        description=f"Minimum {crud.AMBANG_MATVIEW}: materialized view agg_version "
                    f"sudah menyaring pada ambang itu (ml/config.yaml "
                    f"versions.min_reviews_per_version), sehingga nilai lebih "
                    f"kecil tidak dapat dilayani tanpa menyesatkan."),
):
    min_reviews = min_reviews or crud.AMBANG_MATVIEW
    hasil = crud.versions(db, min_reviews)
    hasil["model_produksi"] = S.model_produksi
    hasil["catatan"] = [
        f"Versi dengan < {min_reviews} ulasan dikeluarkan: proporsi negatif dari "
        f"segelintir ulasan tidak stabil dan akan tampil sebagai lonjakan palsu.",
        f"versi_app kosong pada {hasil['null_version_pct']}% ulasan; "
        f"ulasan itu tidak dapat ditautkan ke versi mana pun.",
        f"coverage_pct dihitung atas ulasan yang PUNYA versi "
        f"({hasil['coverage_pct']}%); atas seluruh korpus angkanya "
        f"{hasil['coverage_pct_seluruh_ulasan']}%.",
        "Versi diagregasi ke tingkat MINOR ('4.93.1' -> '4.93') — patch rilis "
        "berjarak hari dan tidak punya cukup ulasan untuk dibandingkan sendiri.",
    ]
    return hasil


# ------------------------------------------------------------------- 4/7 ---
@app.get("/api/topics", response_model=schemas.TopicsResponse, tags=["agregat"],
         summary="Peringkat kategori keluhan")
def baca_topics(
    db: Session = Depends(get_db),
    limit: int = Query(20, ge=1, le=50),
    dari: date | None = Query(None, alias="from"),
    sampai: date | None = Query(None, alias="to"),
):
    if dari and sampai and dari > sampai:
        raise HTTPException(422, f"from ({dari}) melewati to ({sampai})")

    data = crud.topics(db, limit, dari, sampai)
    if not data:
        raise HTTPException(404, "Tidak ada topik pada rentang yang diminta")
    cakupan = crud.cakupan_topik(db, dari, sampai)

    return {
        "kategori_ditampilkan": len(data),
        "total_kategori": cakupan["total_kategori"],
        "total_ulasan_bertopik": cakupan["total_ulasan_bertopik"],
        "model_produksi": S.model_produksi,
        "catatan": [
            "Kategori berasal dari LDA k=9 yang dilatih pada KORPUS NEGATIF saja "
            "(Fase 5). Karena itu persen_negatif per kategori mendekati 100% — "
            "itu konsekuensi desain, bukan temuan.",
            "Satu ulasan dapat tercatat pada lebih dari satu kategori, sehingga "
            "jumlah_ulasan antar kategori tidak dapat dijumlahkan menjadi total.",
            "`id` adalah id kategori (min(topics.id) miliknya), dipakai sebagai "
            "path parameter /api/topics/{id}/reviews.",
        ],
        "data": data,
    }


# ------------------------------------------------------------------- 5/7 ---
@app.get("/api/topics/{topic_id}/reviews", response_model=schemas.TopicReviewsResponse,
         tags=["agregat"], summary="Drill-down ulasan mentah per kategori")
def baca_topic_reviews(
    topic_id: int,
    db: Session = Depends(get_db),
    sort_by: schemas.SortBy = Query(schemas.SortBy.likes),
    page: int = Query(1, ge=1),
    page_size: int = Query(None, ge=1, le=S.page_size_max),
):
    kategori = crud.kategori_by_id(db, topic_id)
    if kategori is None:
        raise HTTPException(404, f"topic_id {topic_id} tidak ada")

    page_size = page_size or S.page_size_default
    hasil = crud.topic_reviews(db, topic_id, sort_by.value, page, page_size)
    return {"topic_id": topic_id, "kategori": kategori, "sort_by": sort_by,
            "page": page, "page_size": page_size, **hasil}


# ------------------------------------------------------------------- 6/7 ---
@app.get("/api/model/metrics", response_model=schemas.ModelMetricsResponse,
         tags=["model"], summary="Perbandingan seluruh model per eval_set")
def baca_model_metrics(db: Session = Depends(get_db)):
    baris = crud.model_metrics(db)
    n_eval = {k: v.get("n_eval")
              for k, v in (ml.get("manifest", {}).get("metrics", {}) or {}).items()}

    blok: dict[str, list[dict]] = {}
    for b in baris:
        blok.setdefault(b["eval_set"], []).append({
            "model_name": b["model_name"],
            "accuracy": b["accuracy"], "precision_neg": b["precision_neg"],
            "recall_neg": b["recall_neg"], "f1_neg": b["f1_neg"],
            "macro_f1": b["macro_f1"], "train_seconds": b["train_seconds"],
            "is_baseline": b["model_name"] == "majority_baseline",
            "is_produksi": b["model_name"] == S.model_produksi,
        })

    return {
        "model_produksi": S.model_produksi,
        "primary_metric": MLCFG["evaluation"]["primary_metric"],
        "majority_baseline_accuracy": MLCFG["evaluation"]["majority_baseline"],
        "catatan": [
            "Dua eval_set dilaporkan berdampingan dan HARUS dibaca bersama. "
            "`full` memuat ulasan sangat pendek yang mudah diklasifikasi; "
            "`informative_ge5w` (>= "
            f"{MLCFG['evaluation']['informative_min_words']} kata) membuang "
            "kemudahan itu.",
            "Pada `full`, majority_baseline sudah mencapai akurasi 0,72 — "
            "akurasi model harus dibaca relatif terhadap angka itu, bukan "
            "terhadap 0. Pada `informative_ge5w` baseline turun ke 0,46, dan "
            "di situlah jarak sesungguhnya antar model terlihat.",
            f"Metrik utama pemilihan model: "
            f"{MLCFG['evaluation']['primary_metric']}.",
        ],
        "eval_sets": [{"eval_set": k, "n_eval": n_eval.get(k), "models": v}
                      for k, v in sorted(blok.items())],
    }


# ------------------------------------------------------------------- 7/7 ---
@app.post("/api/predict", response_model=schemas.PredictResponse, tags=["model"],
          summary="Prediksi sentimen satu teks (demo)")
def prediksi(req: schemas.PredictRequest):
    if "error" in ml:
        raise HTTPException(503, f"Model tidak tersedia: {ml['error']}")

    teks = req.text.strip()
    if not teks:
        raise HTTPException(400, "text kosong setelah dipangkas spasi")

    hasil = ml_service.prediksi(ml, teks)
    if hasil is None:
        raise HTTPException(
            400, "Teks tidak menyisakan token apa pun setelah preprocessing "
                 "(kemungkinan seluruhnya emoji, angka, atau stopword). "
                 "Tidak ada dasar untuk memprediksi.")
    return hasil


# ----------------------------------------------------------------- health ---
@app.get("/api/health", response_model=schemas.HealthResponse, tags=["ops"],
         summary="Kesiapan DB & artefak model")
def health(db: Session = Depends(get_db)):
    try:
        db_ok = "ok" if crud.ping(db) else "error"
    except SQLAlchemyError as e:
        db_ok = f"error: {type(e).__name__}"
    dimuat = "model" in ml
    # `degraded` juga saat DB sehat tetapi artefak gagal dimuat: enam endpoint
    # melayani normal sementara /predict mengembalikan 503, dan itu bukan
    # keadaan yang pantas dilaporkan sebagai "ok".
    return {"status": "ok" if (db_ok == "ok" and dimuat) else "degraded",
            "database": db_ok,
            "model_dimuat": dimuat,
            "model_name": ml.get("model_name") if dimuat else None}
