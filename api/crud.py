"""Seluruh SQL proyek ini ada di berkas ini (Fase 7, T-7.1).

Aturannya satu arah: `main.py` tidak memuat SQL, dan modul ini tidak memuat
logika ML maupun detail HTTP. Fungsi di sini menerima sesi + parameter dan
mengembalikan `dict`/`list[dict]` biasa; Pydantic yang memvalidasi bentuknya.

Hampir seluruh query membaca MATERIALIZED VIEW, bukan `reviews`/`review_scores`
mentah — keputusan arsitektur Fase 6 §1. Satu-satunya yang menyentuh tabel
mentah adalah drill-down `/api/topics/{id}/reviews`, yang memang harus
mengambil baris ulasan satu per satu, dan itu pun lewat indeks.
"""
from __future__ import annotations

from datetime import date

from sqlalchemy import text
from sqlalchemy.orm import Session

from .config import get_ml_config, get_settings

S = get_settings()
MLCFG = get_ml_config()

MODEL = S.model_produksi
BULAN_PARSIAL = MLCFG["temporal"]["partial_month"]          # '2024-05'
AMBANG_MATVIEW = MLCFG["versions"]["min_reviews_per_version"]  # 100


def _rows(db: Session, sql: str, **p) -> list[dict]:
    return [dict(r) for r in db.execute(text(sql), p).mappings()]


def _one(db: Session, sql: str, **p) -> dict | None:
    r = db.execute(text(sql), p).mappings().first()
    return dict(r) if r else None


# ------------------------------------------------------------------ meta ---
def meta(db: Session) -> dict:
    """Konstanta cakupan data dari agg_meta — satu baris, tidak pernah berubah
    antar request selama view tidak di-refresh."""
    return _one(db, "SELECT * FROM agg_meta") or {}


def rentang_default(db: Session) -> tuple[date, date]:
    m = meta(db)
    return m["tanggal_min"].date(), m["tanggal_max"].date()


# --------------------------------------------------------------- /api/kpi ---
SQL_KPI = """
SELECT
    sum(m.total_ulasan)                                             AS total_ulasan,
    round(100.0 * sum(m.jumlah_negatif) / NULLIF(sum(m.total_ulasan), 0), 2)
                                                                    AS persen_negatif,
    round(sum(m.rata_rating * m.total_ulasan) / NULLIF(sum(m.total_ulasan), 0), 2)
                                                                    AS rata_rating,
    sum(a.n_berlabel)                                               AS n_berlabel,
    round(100.0 * sum(a.n_negatif_aktual) / NULLIF(sum(a.n_berlabel), 0), 2)
                                                                    AS baseline_negatif,
    array_agg(m.bulan ORDER BY m.bulan) FILTER (WHERE m.periode_parsial)
                                                                    AS bulan_parsial
FROM agg_monthly m
JOIN agg_monthly_aktual a ON a.bulan = m.bulan
WHERE m.bulan BETWEEN date_trunc('month', CAST(:dari AS date))
                  AND date_trunc('month', CAST(:sampai AS date))
"""


def kpi(db: Session, dari: date, sampai: date, min_reviews: int) -> dict | None:
    """Rata-rata rating dibobot jumlah ulasan per bulan, bukan rata-rata dari
    rata-rata — bulan dengan 1.879 ulasan tidak boleh berbobot sama dengan
    bulan berisi 6.641."""
    row = _one(db, SQL_KPI, dari=dari, sampai=sampai)
    if not row or not row["total_ulasan"]:
        return None
    row["jumlah_versi"] = jumlah_versi(db, min_reviews)
    row["bulan_parsial"] = row["bulan_parsial"] or []
    return row


# ------------------------------------------------------------- /api/trend ---
def trend(db: Session, dari: date, sampai: date, granularity: str) -> list[dict]:
    """agg_weekly sengaja memakai nama kolom yang identik dengan agg_monthly,
    sehingga pilihan granularitas hanya mengganti nama view — bukan mengganti
    query, dan bukan mengganti skema respons."""
    view = "agg_weekly" if granularity == "week" else "agg_monthly"
    trunc = "week" if granularity == "week" else "month"
    return _rows(db, f"""
        SELECT bulan AS periode, total_ulasan, jumlah_negatif, persen_negatif,
               rata_rating, total_likes, periode_parsial
        FROM {view}
        WHERE bulan BETWEEN date_trunc('{trunc}', CAST(:dari AS date))
                        AND date_trunc('{trunc}', CAST(:sampai AS date))
        ORDER BY bulan
    """, dari=dari, sampai=sampai)


# ---------------------------------------------------------- /api/versions ---
def jumlah_versi(db: Session, min_reviews: int) -> int:
    return db.execute(
        text("SELECT count(*) FROM agg_version WHERE total_ulasan >= :n"),
        {"n": min_reviews}).scalar_one()


def versions(db: Session, min_reviews: int) -> dict:
    """`agg_version` sudah menyaring di ambang AMBANG_MATVIEW (100, dari
    ml/config.yaml). Ambang request hanya dapat MEMPERKETAT; nilai di bawahnya
    ditolak di lapisan HTTP, karena barisnya memang tidak ada di view dan
    mengembalikan hasil "seolah-olah tersaring" akan menyesatkan."""
    data = _rows(db, """
        SELECT versi_minor, total_ulasan, jumlah_negatif, persen_negatif,
               rata_rating, pertama_muncul
        FROM agg_version
        WHERE total_ulasan >= :n
        ORDER BY pertama_muncul
    """, n=min_reviews)

    m = meta(db)
    tercakup = sum(d["total_ulasan"] for d in data)
    return {
        "min_reviews_threshold": min_reviews,
        "versions_included": len(data),
        "coverage_pct": round(100.0 * tercakup / m["n_versi_minor_terisi"], 2),
        "coverage_pct_seluruh_ulasan": round(100.0 * tercakup / m["total_ulasan"], 2),
        "null_version_pct": float(m["versi_null_pct"]),
        "data": data,
    }


# ------------------------------------------------------------ /api/topics ---
SQL_TOPICS_CEPAT = """
SELECT id, kategori, jumlah_ulasan, jumlah_negatif, persen_negatif,
       total_likes, rata_rating
FROM agg_kategori
ORDER BY jumlah_ulasan DESC
LIMIT :limit
"""

# Jalur berfilter-tanggal: agg_kategori tidak dapat dipakai karena sudah
# teragregasi atas seluruh periode. `review_kategori` membawa salinan tanggal,
# rating, likes, dan pred_label, sehingga query ini membaca SATU view — tidak
# ada join ke reviews maupun review_scores saat request.
SQL_TOPICS_RENTANG = """
SELECT rk.kategori_id                            AS id,
       rk.kategori,
       count(*)                                  AS jumlah_ulasan,
       count(*) FILTER (WHERE rk.pred_label = 0) AS jumlah_negatif,
       round(100.0 * count(*) FILTER (WHERE rk.pred_label = 0)
             / NULLIF(count(*), 0), 2)           AS persen_negatif,
       sum(rk.likes)                             AS total_likes,
       round(avg(rk.rating)::numeric, 2)         AS rata_rating
FROM review_kategori rk
WHERE rk.tanggal >= CAST(:dari AS date)
  AND rk.tanggal < CAST(:sampai AS date) + INTERVAL '1 day'
GROUP BY rk.kategori_id, rk.kategori
ORDER BY jumlah_ulasan DESC
LIMIT :limit
"""


def topics(db: Session, limit: int, dari: date | None, sampai: date | None) -> list[dict]:
    if dari is None and sampai is None:
        return _rows(db, SQL_TOPICS_CEPAT, limit=limit)
    d0, d1 = rentang_default(db)
    return _rows(db, SQL_TOPICS_RENTANG, limit=limit,
                 dari=dari or d0, sampai=sampai or d1)


def cakupan_topik(db: Session, dari: date | None, sampai: date | None) -> dict:
    """Ulasan UNIK yang bertopik — bukan jumlah kolom `jumlah_ulasan`.

    Satu ulasan dapat memicu beberapa kategori, sehingga menjumlahkan
    `jumlah_ulasan` akan menghitung ulasan yang sama berkali-kali. Angka inilah
    yang benar untuk kalimat "sekian ulasan tercakup topik" di dashboard.
    """
    if dari is None and sampai is None:
        return _one(db, """
            SELECT (SELECT count(*) FROM agg_kategori)            AS total_kategori,
                   (SELECT count(DISTINCT review_id)
                      FROM review_kategori)                       AS total_ulasan_bertopik
        """)
    d0, d1 = rentang_default(db)
    return _one(db, """
        SELECT count(DISTINCT kategori_id) AS total_kategori,
               count(DISTINCT review_id)   AS total_ulasan_bertopik
        FROM review_kategori
        WHERE tanggal >= CAST(:dari AS date)
          AND tanggal < CAST(:sampai AS date) + INTERVAL '1 day'
    """, dari=dari or d0, sampai=sampai or d1)


def kategori_by_id(db: Session, topic_id: int) -> str | None:
    return db.execute(
        text("SELECT kategori FROM agg_kategori WHERE id = :id"),
        {"id": topic_id}).scalar_one_or_none()


# Pengurutan memakai kolom `review_kategori`, bukan `reviews`: dengan begitu
# 20 baris teratas diambil dari indeks view, dan `reviews` hanya disentuh 20
# kali lewat primary key — bukan 9.663 kali untuk disortir.
_URUT = {
    "likes": "rk.likes DESC, rk.review_id",
    "tanggal": "rk.tanggal DESC, rk.review_id",
    "rating": "rk.rating ASC, rk.likes DESC, rk.review_id",
}


def topic_reviews(db: Session, topic_id: int, sort_by: str,
                  page: int, page_size: int) -> dict:
    """Mengembalikan `ulasan` — teks ASLI. `ulasan_clean` sudah ter-stem dan
    tidak terbaca manusia; menampilkannya di drill-down akan membuat tabel
    bukti di dashboard tidak berguna sebagai bukti."""
    total = db.execute(text(
        "SELECT count(*) FROM review_kategori WHERE kategori_id = :id"),
        {"id": topic_id}).scalar_one()

    data = _rows(db, f"""
        SELECT r.id, r.ulasan, r.rating, r.tanggal, r.likes, r.versi_app,
               r.sentimen_aktual, rs.pred_label, rs.pred_proba
        FROM (SELECT review_id, likes, tanggal, rating
              FROM review_kategori rk
              WHERE rk.kategori_id = :id
              ORDER BY {_URUT[sort_by]}
              LIMIT :limit OFFSET :offset) rk
        JOIN reviews r        ON r.id = rk.review_id
        JOIN review_scores rs ON rs.review_id = r.id AND rs.model_name = :model
        ORDER BY {_URUT[sort_by]}
    """, id=topic_id, model=MODEL, limit=page_size, offset=(page - 1) * page_size)

    return {
        "total_items": total,
        "total_pages": max(1, -(-total // page_size)),
        "data": data,
    }


# ----------------------------------------------------- /api/model/metrics ---
def model_metrics(db: Session) -> list[dict]:
    """Seluruh baris, termasuk `majority_baseline`. Baseline dikembalikan —
    bukan disaring — karena tanpa pembanding itu angka akurasi 94% tidak punya
    arti; pada eval_set `informative_ge5w` baseline justru turun ke 46%, dan
    kontras itulah temuan metodologis yang harus terlihat di dashboard."""
    return _rows(db, """
        SELECT eval_set, model_name, accuracy, precision_neg, recall_neg,
               f1_neg, macro_f1, train_seconds
        FROM model_metrics
        ORDER BY eval_set,
                 (model_name = 'majority_baseline') DESC,
                 macro_f1 DESC
    """)


def ping(db: Session) -> bool:
    return db.execute(text("SELECT 1")).scalar_one() == 1
