"""Skema respons Pydantic (Fase 7, T-7.4).

Setiap endpoint punya `response_model`. Selain validasi, ini yang membuat
`openapi.json` menjadi kontrak yang bisa dilampirkan di laporan — bukan
dokumentasi yang ditulis terpisah lalu basi.
"""
from __future__ import annotations

from datetime import date, datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class Skema(BaseModel):
    """Basis semua skema respons.

    `protected_namespaces=()` mematikan peringatan Pydantic atas field berawalan
    `model_`. Nama seperti `model_name` dan `model_produksi` adalah istilah
    domain proyek ini, bukan tabrakan yang perlu dihindari dengan mengganti nama
    field yang sudah dipakai di kontrak API.
    """

    model_config = ConfigDict(protected_namespaces=())


class Granularity(str, Enum):
    month = "month"
    week = "week"


class SortBy(str, Enum):
    likes = "likes"
    tanggal = "tanggal"
    rating = "rating"


# --------------------------------------------------------------- /api/kpi ---
class PeriodeInfo(Skema):
    dari: date = Field(..., description="Batas bawah rentang yang benar-benar dipakai")
    sampai: date = Field(..., description="Batas atas rentang yang benar-benar dipakai")
    bulan_parsial: list[date] = Field(
        default_factory=list,
        description="Bulan dengan cakupan hari tidak penuh; ikut dihitung, "
                    "tetapi harus dianotasi di grafik.")


class KpiResponse(Skema):
    total_ulasan: int
    persen_negatif: float = Field(..., ge=0, le=100,
                                  description="Proporsi negatif menurut model produksi")
    baseline_negatif: float = Field(
        ..., ge=0, le=100,
        description="Proporsi negatif menurut LABEL AKTUAL (rating 1–2), dihitung "
                    "atas ulasan berlabel saja — rating 3 tidak punya label biner. "
                    "Pembanding untuk persen_negatif.")
    rata_rating: float = Field(..., ge=1, le=5)
    jumlah_versi: int = Field(..., description="Versi minor yang lolos ambang min_reviews")
    versi_null_pct: float = Field(..., ge=0, le=100)
    model_produksi: str
    periode: PeriodeInfo
    catatan: list[str]


# ------------------------------------------------------------- /api/trend ---
class TrendPoint(Skema):
    periode: date
    total_ulasan: int
    jumlah_negatif: int
    persen_negatif: float = Field(..., ge=0, le=100)
    rata_rating: float | None = Field(None, ge=1, le=5)
    total_likes: int
    periode_parsial: bool


class TrendResponse(Skema):
    granularity: Granularity
    model_produksi: str
    catatan: list[str]
    data: list[TrendPoint]


# ---------------------------------------------------------- /api/versions ---
class VersionItem(Skema):
    versi_minor: str
    total_ulasan: int
    jumlah_negatif: int
    persen_negatif: float = Field(..., ge=0, le=100)
    rata_rating: float | None = Field(None, ge=1, le=5)
    pertama_muncul: datetime


class VersionsResponse(Skema):
    min_reviews_threshold: int
    versions_included: int
    coverage_pct: float = Field(
        ..., ge=0, le=100,
        description="Ulasan yang tercakup versi lolos-ambang, sebagai persen dari "
                    "ulasan yang PUNYA versi_minor.")
    coverage_pct_seluruh_ulasan: float = Field(
        ..., ge=0, le=100,
        description="Persentase yang sama, tetapi atas seluruh 100.000 ulasan — "
                    "termasuk yang versi_app-nya NULL.")
    null_version_pct: float = Field(..., ge=0, le=100)
    model_produksi: str
    catatan: list[str]
    data: list[VersionItem]


# ------------------------------------------------------------ /api/topics ---
class TopicItem(Skema):
    id: int = Field(..., description="Id kategori — min(topics.id) milik kategori itu")
    kategori: str
    jumlah_ulasan: int
    jumlah_negatif: int
    persen_negatif: float = Field(..., ge=0, le=100)
    total_likes: int
    rata_rating: float | None = Field(None, ge=1, le=5)


class TopicsResponse(Skema):
    kategori_ditampilkan: int = Field(..., description="Banyak baris pada `data` (dibatasi `limit`)")
    total_kategori: int = Field(..., description="Seluruh kategori yang ada, terlepas dari `limit`")
    total_ulasan_bertopik: int = Field(
        ..., description="Ulasan UNIK yang menyentuh minimal satu kategori. Bukan "
                         "jumlah dari kolom jumlah_ulasan — satu ulasan dapat "
                         "masuk beberapa kategori sekaligus.")
    model_produksi: str
    catatan: list[str]
    data: list[TopicItem]


class ReviewItem(Skema):
    id: int
    ulasan: str = Field(..., description="Teks ASLI, bukan ulasan_clean")
    rating: int = Field(..., ge=1, le=5)
    tanggal: datetime
    likes: int
    versi_app: str | None
    pred_label: int = Field(..., ge=0, le=1)
    pred_proba: float | None = Field(
        None, description="P(kelas POSITIF) dari pre-scoring batch Fase 6 — bukan "
                          "keyakinan atas kelas terpilih. pred_label=0 dengan "
                          "pred_proba=0,06 berarti model 94% yakin ulasan ini negatif.")
    sentimen_aktual: int | None


class TopicReviewsResponse(Skema):
    topic_id: int
    kategori: str
    sort_by: SortBy
    page: int
    page_size: int
    total_items: int
    total_pages: int
    data: list[ReviewItem]


# ----------------------------------------------------- /api/model/metrics ---
class MetricRow(Skema):
    model_name: str
    accuracy: float | None
    precision_neg: float | None
    recall_neg: float | None
    f1_neg: float | None
    macro_f1: float | None
    train_seconds: float | None
    is_baseline: bool
    is_produksi: bool


class EvalSetBlock(Skema):
    eval_set: str
    n_eval: int | None = Field(None, description="Dari MANIFEST.json bila tersedia")
    models: list[MetricRow]


class ModelMetricsResponse(Skema):
    model_produksi: str
    primary_metric: str
    majority_baseline_accuracy: float
    catatan: list[str]
    eval_sets: list[EvalSetBlock]


# ----------------------------------------------------------- /api/predict ---
class PredictRequest(Skema):
    text: str = Field(..., min_length=1, max_length=1000,
                      json_schema_extra={"example": "aplikasi error terus gabisa bayar"})


class PredictResponse(Skema):
    text: str
    text_preprocessed: str = Field(..., description="Masukan TF-IDF: hasil pipeline penuh, sudah ter-stem")
    text_normalized: str = Field(..., description="Setelah normalisasi slang, sebelum stopword & stemming — versi yang masih terbaca manusia")
    prediction: int = Field(..., ge=0, le=1)
    label: str
    confidence: float | None = Field(
        None, ge=0, le=1,
        description="null bila estimator tidak punya predict_proba")
    model_name: str
    note: str


class HealthResponse(Skema):
    status: str
    database: str
    model_dimuat: bool
    model_name: str | None
