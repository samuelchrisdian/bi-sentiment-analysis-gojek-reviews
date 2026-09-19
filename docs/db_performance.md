# Kinerja Query Agregat — Fase 6, T-6.6

Kelima query di bawah adalah query yang akan dipakai lima endpoint
"baca-agregat" Fase 7 (`/api/kpi`, `/api/trend`, `/api/versions`, `/api/topics`,
`/api/model/metrics`). Seluruhnya membaca materialized view atau
`model_metrics` — tidak ada yang menyentuh `reviews`/`review_scores` mentah
(500.000 + 100.000 baris) saat request; agregasi sudah dikerjakan sekali saat
`REFRESH MATERIALIZED VIEW` (`ml/sql/002_matviews.sql`).

Diukur dengan `EXPLAIN ANALYZE` pada database berisi penuh (100.000 `reviews`,
500.000 `review_scores`, 146 `topics`, 52.998 `review_topics`, 20
`model_metrics`), 2026-09-19.

| # | Endpoint | Sumber | Execution Time |
|---|----------|--------|-----------------|
| 1 | `/api/kpi` | `agg_monthly` | 0,170 ms |
| 2 | `/api/trend` | `agg_monthly` | 0,125 ms |
| 3 | `/api/versions` | `agg_version` | 0,143 ms |
| 4 | `/api/topics` | `agg_topic` | 0,152 ms |
| 5 | `/api/model/metrics` | `model_metrics` | 0,165 ms |

**Seluruh query < 1 ms** — jauh di bawah target 200ms. Ini konsekuensi
langsung dari keputusan arsitektur Fase 6 §1: agregasi 500.000+100.000 baris
dikerjakan sekali oleh `REFRESH MATERIALIZED VIEW`, sehingga setiap query
runtime hanya membaca 19–140 baris hasil pre-agregasi, bukan menghitung ulang
dari tabel mentah.

## 1. `/api/kpi`

```sql
EXPLAIN ANALYZE
SELECT count(*) AS total_ulasan,
       round(100.0*sum(jumlah_negatif)/sum(total_ulasan)::numeric, 2) AS persen_negatif,
       round(sum(rata_rating*total_ulasan)/sum(total_ulasan)::numeric, 2) AS rata_rating
FROM agg_monthly
WHERE bulan >= '2024-06-01';
```

```
Aggregate  (cost=1.36..1.39 rows=1 width=72) (actual time=0.062..0.064 rows=1 loops=1)
  ->  Seq Scan on agg_monthly  (cost=0.00..1.25 rows=7 width=48) (actual time=0.023..0.027 rows=19 loops=1)
        Filter: (bulan >= '2024-06-01'::date)
        Rows Removed by Filter: 1
Planning Time: 1.079 ms
Execution Time: 0.170 ms
```

## 2. `/api/trend`

```sql
EXPLAIN ANALYZE
SELECT * FROM agg_monthly
WHERE bulan BETWEEN '2024-06-01' AND '2025-12-31'
ORDER BY bulan;
```

```
Sort  (cost=1.31..1.31 rows=1 width=93) (actual time=0.066..0.068 rows=19 loops=1)
  Sort Key: bulan
  Sort Method: quicksort  Memory: 26kB
  ->  Seq Scan on agg_monthly  (cost=0.00..1.30 rows=1 width=93) (actual time=0.022..0.024 rows=19 loops=1)
        Filter: ((bulan >= '2024-06-01'::date) AND (bulan <= '2025-12-31'::date))
        Rows Removed by Filter: 1
Planning Time: 0.648 ms
Execution Time: 0.125 ms
```

## 3. `/api/versions`

```sql
EXPLAIN ANALYZE
SELECT * FROM agg_version ORDER BY pertama_muncul;
```

```
Sort  (cost=3.51..3.67 rows=63 width=41) (actual time=0.073..0.077 rows=63 loops=1)
  Sort Key: pertama_muncul
  Sort Method: quicksort  Memory: 29kB
  ->  Seq Scan on agg_version  (cost=0.00..1.63 rows=63 width=41) (actual time=0.012..0.017 rows=63 loops=1)
Planning Time: 0.711 ms
Execution Time: 0.143 ms
```

## 4. `/api/topics`

```sql
EXPLAIN ANALYZE
SELECT * FROM agg_topic ORDER BY jumlah_ulasan DESC LIMIT 20;
```

```
Limit  (cost=7.13..7.18 rows=20 width=56) (actual time=0.096..0.100 rows=20 loops=1)
  ->  Sort  (cost=7.13..7.48 rows=140 width=56) (actual time=0.095..0.097 rows=20 loops=1)
        Sort Key: jumlah_ulasan DESC
        Sort Method: top-N heapsort  Memory: 27kB
        ->  Seq Scan on agg_topic  (cost=0.00..3.40 rows=140 width=56) (actual time=0.010..0.028 rows=140 loops=1)
Planning Time: 0.407 ms
Execution Time: 0.152 ms
```

## 5. `/api/model/metrics`

```sql
EXPLAIN ANALYZE
SELECT model_name, eval_set, accuracy, precision_neg, recall_neg, f1_neg, macro_f1
FROM model_metrics
ORDER BY eval_set, macro_f1 DESC;
```

```
Sort  (cost=45.59..47.17 rows=630 width=84) (actual time=0.105..0.107 rows=20 loops=1)
  Sort Key: eval_set, macro_f1 DESC
  Sort Method: quicksort  Memory: 26kB
  ->  Seq Scan on model_metrics  (cost=0.00..16.30 rows=630 width=84) (actual time=0.019..0.023 rows=20 loops=1)
Planning Time: 1.190 ms
Execution Time: 0.165 ms
```

## Catatan — `agg_version` berisi 63 baris, bukan 66

`docs/data_contract.md` §"Versi App" (Fase 1 EDA) dan seluruh rencana Fase
6–8 mencatat **66 versi** pada ambang ≥100 ulasan (cakupan 96,4%,
`docs/tables/cakupan_versi.csv`). Menjalankan ulang `derive_versi_minor()`
(`ml/src/ingest.py`) pada CSV mentah **hari ini menghasilkan 63 versi**
(cakupan 97,1%), bukan 66 — dan `agg_version` yang dibangun dari `reviews`
yang sudah dimuat (yang datanya berasal dari parquet Fase 2, hasil fungsi
yang sama) juga menghasilkan 63 baris.

Ini bukan bug yang diperkenalkan Fase 6: query dan matview menghitung
persis apa yang tercatat di `reviews`/parquet saat ini. Kemungkinan
penyebabnya adalah `derive_versi_minor()` diperbaiki setelah
`docs/tables/cakupan_versi.csv` ditulis di Fase 1, dan tabel itu tidak pernah
dihitung ulang. Angka **63** dilaporkan apa adanya di sini, konsisten dengan
kebijakan proyek (Fase 5, opsi A) untuk melaporkan hasil aktual, bukan
menyesuaikannya ke angka dokumen lama. `docs/data_contract.md` dan rencana
Fase 7–8 perlu diperbarui ke **63 versi / 97,1% cakupan** sebelum dipakai
sebagai acuan DoD.
