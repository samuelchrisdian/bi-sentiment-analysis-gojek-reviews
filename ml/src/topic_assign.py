"""Penetapan topik per ulasan & peringkat (Fase 5, T-5.5 s/d T-5.8).

Nama kategori DIIMPOR dari hasil gerbang H-8, tidak ditentukan di sini.
Yang dikerjakan modul ini murni turunan: memilih kata kunci per kategori dari
bobot LDA, menetapkan topik per ulasan, dan menyusun peringkat.

Pemilihan kata kunci memakai *relevance* (Sievert & Shirley, 2014) — ukuran yang
sama dipakai pyLDAvis — bukan sekadar p(w|topik):

    relevance(w,t) = lambda*log p(w|t) + (1-lambda)*log( p(w|t) / p(w) )

Suku kedua menghukum kata yang sering di SELURUH korpus. Tanpa itu, setiap
kategori akan memperoleh kata kunci `gojek`, `aplikasi`, `nya`, `ada` — yang
benar secara probabilitas tetapi tidak membedakan apa pun.
"""
from __future__ import annotations

import re

import numpy as np
import pandas as pd
from gensim import corpora
from gensim.models import LdaModel

from .config import load_config, resolve
from .topics import korpus_negatif, siapkan_gensim

CFG = load_config()
ROOT = CFG["_root"]
TAB = ROOT / "docs" / "tables"
LAMBDA = 0.6          # Sievert & Shirley merekomendasikan ~0,6 untuk penamaan
N_KATA_KUNCI = 10     # DoD menuntut >=5 per kategori
AMBANG_LDA = 0.3      # T-5.5 pendekatan B
AMBANG_BIGRAM = 0.35  # pangsa minimum kemunculan bigram pada satu topik
MIN_LIFT = 2.0        # kata kunci harus >=2x lebih terkonsentrasi dari pangsa topiknya
MAX_DF_KORPUS = 0.15  # kata di >15% korpus tidak dapat membedakan kategori apa pun
MAX_BIGRAM = 15       # batas bigram per kategori — lihat kata_kunci_bigram()

# Hasil gerbang H-8 — pemetaan topic_id -> kategori bisnis.
# Sumber: docs/tables/lda_clusters_for_labeling_reviewed.csv
# Provenans pelabel dicatat di docs/topic_labeling_rules.md §5.
KATEGORI_H8: dict[int, str] = {
    2: "Pesanan GoFood & Pembatalan",
    0: "Ketersediaan & Respons Mitra Driver",
    4: "Tarif, Ongkir & Promo",
    7: "GoPayLater, GoPinjam & Penagihan",
    5: "Performa & Gangguan Aplikasi",
    6: "Akurasi Lokasi & Rute",
    8: "Akun, Login & Verifikasi",
    1: "Layanan Pelanggan & Penanganan Keluhan",
    3: "Transaksi & Saldo GoPay",
}


def muat_lda(k: int = 9):
    lda = LdaModel.load(str(ROOT / "ml" / "artifacts" / f"lda_k{k}.gensim"))
    dist = np.load(ROOT / "data" / "processed" / "lda_doc_topic.npy")
    return lda, dist


def kata_kunci_unigram(lda: LdaModel, corpus, topik: pd.DataFrame,
                       dominan: np.ndarray) -> pd.DataFrame:
    """Relevance per (topik, kata), disaring dua kali sebelum dipakai mencocokkan.

    Relevance saja tidak cukup. Ia menjawab "kata apa yang khas bagi topik ini",
    sedangkan yang dibutuhkan penetapan berbasis aturan adalah "kata apa yang
    kemunculannya benar-benar menandakan kategori ini". Dua saringan tambahan:

      1. `MAX_DF_KORPUS` — kata yang muncul di >15% korpus negatif tidak dapat
         membedakan apa pun. Tanpa ini `bisa` (22% dokumen) menjadi kata kunci
         "Akun, Login & Verifikasi" dan mencocoki seperlima korpus.
      2. `MIN_LIFT` — kata harus >=2x lebih terkonsentrasi pada dokumen dominan
         topiknya dibanding pangsa topik itu sendiri. Ambang mutlak akan berat
         sebelah terhadap topik besar (topik 2 menguasai 28,85% dokumen).
    """
    phi = lda.get_topics()                              # (k, V) p(w|t)
    V = phi.shape[1]
    cf = np.zeros(V)
    for bow in corpus:
        for wid, n in bow:
            cf[wid] += n
    pw = cf / cf.sum()

    with np.errstate(divide="ignore"):
        rel = LAMBDA * np.log(phi) + (1 - LAMBDA) * np.log(phi / pw[None, :])

    # Kehadiran token per dokumen, untuk menghitung df korpus dan lift.
    tok = topik["ulasan_clean"].fillna("").str.split().apply(set)
    n_dok = len(tok)
    pangsa_topik = np.array([(dominan == t).mean() for t in range(phi.shape[0])])

    baris = []
    for tid in range(phi.shape[0]):
        diambil = 0
        for wid in np.argsort(rel[tid])[::-1]:
            if diambil >= N_KATA_KUNCI:
                break
            kata = lda.id2word[wid]
            ada = tok.apply(lambda s, k=kata: k in s).to_numpy()
            df_korpus = ada.mean()
            if df_korpus > MAX_DF_KORPUS or ada.sum() == 0:
                continue
            konsentrasi = (ada & (dominan == tid)).sum() / ada.sum()
            lift = konsentrasi / pangsa_topik[tid]
            if lift < MIN_LIFT:
                continue
            diambil += 1
            baris.append({"topic_id": tid, "kategori": KATEGORI_H8[tid],
                          "keyword": kata, "rank": diambil,
                          "bobot": round(float(phi[tid, wid]), 6),
                          "relevance": round(float(rel[tid, wid]), 4),
                          "df_korpus": round(float(df_korpus), 4),
                          "lift": round(float(lift), 2), "n_gram": 1})
    return pd.DataFrame(baris)


def kata_kunci_bigram(topik: pd.DataFrame, dominan: np.ndarray,
                      min_freq: int = 150) -> pd.DataFrame:
    """Bigram ditetapkan ke topik tempat ia paling terkonsentrasi.

    Berbasis data, bukan penilaian: untuk setiap bigram dihitung sebaran
    kemunculannya di seluruh topik dominan, dan ia diambil hanya bila >=35%
    kemunculannya berada pada satu topik. Bigram yang tersebar merata dibuang
    karena tidak membedakan kategori.
    """
    from sklearn.feature_extraction.text import CountVectorizer
    cv = CountVectorizer(ngram_range=(2, 2), min_df=min_freq, token_pattern=r"\S+",
                         lowercase=False, binary=True)
    X = cv.fit_transform(topik["ulasan_clean"])
    istilah = np.array(cv.get_feature_names_out())

    k = len(KATEGORI_H8)
    per_topik = np.vstack([np.asarray(X[dominan == t].sum(axis=0)).ravel()
                           for t in range(k)])            # (k, n_bigram)
    total = per_topik.sum(axis=0)
    pangsa = per_topik / np.maximum(total, 1)

    baris = []
    for j, term in enumerate(istilah):
        tid = int(pangsa[:, j].argmax())
        if pangsa[tid, j] >= AMBANG_BIGRAM and total[j] >= min_freq:
            baris.append({"topic_id": tid, "kategori": KATEGORI_H8[tid],
                          "keyword": term, "bobot": round(float(pangsa[tid, j]), 6),
                          "relevance": np.nan, "n_gram": 2,
                          "n_dokumen": int(total[j])})
    d = pd.DataFrame(baris)
    if d.empty:
        return d
    d["rank"] = d.groupby("topic_id").bobot.rank(ascending=False, method="first").astype(int)
    # Tanpa batas ini sebarannya sangat timpang: topik terbesar (28,85% dokumen)
    # menarik 63 bigram sementara dua topik lain tidak memperoleh satu pun,
    # sehingga tabel `topics` menjadi tidak sebanding antar kategori.
    d = d[d["rank"] <= MAX_BIGRAM]
    return d.sort_values(["topic_id", "rank"])


def peta_kata_kunci(kk: pd.DataFrame) -> dict[str, dict]:
    peta = {}
    for kat, g in kk.groupby("kategori"):
        peta[kat] = {
            "unigram": sorted(g[g.n_gram == 1].keyword.tolist()),
            "bigram": sorted(g[g.n_gram == 2].keyword.tolist()),
        }
    return peta


def tetapkan_aturan(teks: pd.Series, peta: dict[str, dict]) -> pd.DataFrame:
    """Pendekatan A (RESMI) — berbasis kata kunci, dapat dijelaskan & diaudit.

    Pencocokan unigram dilakukan pada level TOKEN, bukan substring: `bayar`
    sebagai substring juga cocok dengan `pembayaran` dan `membayarkan`, yang
    membuat cakupan tampak lebih tinggi daripada sebenarnya.
    """
    tok = teks.fillna("").str.split().apply(set)
    padded = " " + teks.fillna("") + " "
    out = {}
    for kat, kw in peta.items():
        uni = set(kw["unigram"])
        hit = tok.apply(lambda s: bool(s & uni))
        for bg in kw["bigram"]:
            hit |= padded.str.contains(f" {re.escape(bg)} ", regex=True)
        out[kat] = hit
    return pd.DataFrame(out, index=teks.index)


def tetapkan_lda(dist: np.ndarray, ambang: float = AMBANG_LDA) -> np.ndarray:
    """Pendekatan B (pembanding) — topik dominan di atas ambang, else -1."""
    best = dist.argmax(axis=1)
    return np.where(dist.max(axis=1) >= ambang, best, -1)


def buang_tabrakan(kk: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Satu kata kunci hanya boleh milik satu kategori.

    `gopay` muncul sebagai kata khas pada dua kategori pembayaran sekaligus.
    Membiarkannya membuat setiap ulasan bergopay masuk keduanya, sehingga
    peringkat frekuensi menghitung ganda. Pemenangnya ditentukan `lift` —
    ukuran yang sudah dipakai menyaring, bukan penilaian baru.
    """
    kk = kk.copy()
    kk["_skor"] = kk.lift.fillna(kk.bobot * 10)
    dobel = kk[kk.duplicated("keyword", keep=False)].sort_values(["keyword", "_skor"],
                                                                ascending=[True, False])
    menang = kk.sort_values("_skor", ascending=False).drop_duplicates("keyword")
    return menang.drop(columns="_skor").sort_values(["kategori", "n_gram", "rank"]), dobel


def jalankan() -> dict:
    topik, info = korpus_negatif()
    texts, dictionary, corpus = siapkan_gensim(topik)
    lda, dist = muat_lda()
    dominan = dist.argmax(axis=1)

    uni = kata_kunci_unigram(lda, corpus, topik, dominan)
    big = kata_kunci_bigram(topik, dominan)
    kk, tabrakan = buang_tabrakan(pd.concat([uni, big], ignore_index=True))
    peta = peta_kata_kunci(kk)

    # Pendekatan A dijalankan pada SELURUH korpus negatif (26.732), bukan hanya
    # korpus LDA: pencocokan kata kunci tidak menuntut panjang minimum, dan DoD
    # meminta proporsi ulasan negatif yang memperoleh >=1 topik.
    df = pd.read_parquet(resolve(CFG, "paths.clean_parquet"))
    neg = df[df["sentimen_aktual"] == 0].copy()
    A_semua = tetapkan_aturan(neg["ulasan_clean"], peta)

    # Perbandingan A vs B hanya sah pada irisan tempat keduanya terdefinisi.
    A_sub = A_semua.loc[topik.index]
    B = tetapkan_lda(dist)
    kat_urut = [KATEGORI_H8[t] for t in range(len(KATEGORI_H8))]
    B_kat = pd.Series([KATEGORI_H8[t] if t >= 0 else None for t in B], index=topik.index)

    sepakat = pd.Series(
        [bool(k) and bool(A_sub.loc[i, k]) for i, k in B_kat.items()], index=topik.index)
    punya_b = B_kat.notna()

    return {"topik": topik, "info": info, "neg": neg, "kk": kk, "tabrakan": tabrakan,
            "peta": peta, "A_semua": A_semua, "A_sub": A_sub, "B_kat": B_kat,
            "sepakat": sepakat, "punya_b": punya_b, "dist": dist,
            "dominan": dominan, "kat_urut": kat_urut}


def kata_kunci_pemicu(neg: pd.DataFrame, kk: pd.DataFrame) -> pd.DataFrame:
    """Untuk tiap (ulasan, kategori) yang cocok, catat SATU kata kunci pemicu.

    Ini bukan detail kosmetik. `review_topics` merujuk baris `topics`, yaitu
    pasangan (kategori, keyword). Bila satu ulasan ditautkan ke tiga baris
    keyword dari kategori yang sama, maka `COUNT(*) GROUP BY kategori` pada
    T-5.6 menghitungnya tiga kali dan peringkatnya menjadi salah. Satu baris per
    (ulasan, kategori) menjaga hitungan tetap benar, sekaligus membuat penetapan
    dapat diaudit: terlihat kata mana yang memicunya.
    """
    tok = neg["ulasan_clean"].fillna("").str.split().apply(set)
    padded = " " + neg["ulasan_clean"].fillna("") + " "
    baris = []
    for kat, g in kk.groupby("kategori"):
        # Kata kunci terkuat lebih dulu; yang pertama cocok menjadi pemicu.
        g = g.assign(_s=g.lift.fillna(g.bobot * 10)).sort_values("_s", ascending=False)
        belum = pd.Series(True, index=neg.index)
        for r in g.itertuples():
            if not belum.any():
                break
            cocok = (tok.apply(lambda s, k=r.keyword: k in s) if r.n_gram == 1
                     else padded.str.contains(f" {re.escape(r.keyword)} ", regex=True))
            kena = belum & cocok
            if kena.any():
                baris.append(pd.DataFrame({"review_id": neg.index[kena].map(neg["id"]),
                                           "kategori": kat, "keyword": r.keyword}))
                belum &= ~cocok
    return pd.concat(baris, ignore_index=True)


def peringkat(pemicu: pd.DataFrame, neg: pd.DataFrame) -> pd.DataFrame:
    """T-5.6 — dua kolom TERPISAH, tidak digabung menjadi skor komposit.

    Bab 1 membatasi prioritas hanya berbasis frekuensi; kolom Likes hadir
    sebagai lensa tambahan ("keluhan mana yang paling beresonansi"). Menggabung
    keduanya menjadi satu angka akan menyelundupkan pembobotan yang tidak
    diizinkan batasan itu.
    """
    likes = neg.set_index("id")["likes"]
    g = pemicu.groupby("kategori").agg(jumlah_ulasan=("review_id", "nunique"))
    g["total_likes"] = pemicu.groupby("kategori").review_id.apply(
        lambda s: int(likes.loc[s.unique()].sum()))
    g["persen_ulasan_negatif"] = (g.jumlah_ulasan / len(neg) * 100).round(2)
    g["rata_likes"] = (g.total_likes / g.jumlah_ulasan).round(3)
    g["peringkat_frekuensi"] = g.jumlah_ulasan.rank(ascending=False).astype(int)
    g["peringkat_likes"] = g.total_likes.rank(ascending=False).astype(int)
    g["selisih_peringkat"] = g.peringkat_frekuensi - g.peringkat_likes
    return g.sort_values("jumlah_ulasan", ascending=False).reset_index()


def tulis_db(kk: pd.DataFrame, pemicu: pd.DataFrame) -> dict:
    """T-5.7 — isi `topics` dan `review_topics`."""
    import os
    from dotenv import load_dotenv
    from sqlalchemy import create_engine, text

    load_dotenv(ROOT / ".env")
    eng = create_engine(os.environ[CFG["database"]["dsn_env"]])

    t = kk[["kategori", "keyword", "bobot"]].copy()
    with eng.begin() as c:
        c.execute(text("TRUNCATE review_topics"))
        c.execute(text("TRUNCATE topics RESTART IDENTITY CASCADE"))
    t.to_sql("topics", eng, if_exists="append", index=False)

    peta_id = pd.read_sql("SELECT id, kategori, keyword FROM topics", eng)
    rt = pemicu.merge(peta_id, on=["kategori", "keyword"], how="left")
    assert rt.id.notna().all(), "ada pemicu yang tidak menemukan baris topics"
    rt = rt[["review_id", "id"]].rename(columns={"id": "topic_id"}).drop_duplicates()
    rt.to_sql("review_topics", eng, if_exists="append", index=False,
              chunksize=5000, method="multi")

    with eng.connect() as c:
        n_t = c.execute(text("SELECT count(*) FROM topics")).scalar()
        n_rt = c.execute(text("SELECT count(*) FROM review_topics")).scalar()
        n_r = c.execute(text("SELECT count(DISTINCT review_id) FROM review_topics")).scalar()
    return {"engine": eng, "n_topics": n_t, "n_review_topics": n_rt, "n_review": n_r}


def tren_bulanan(eng) -> pd.DataFrame:
    """T-5.8 — tren kategori per bulan, lewat SQL sesuai rencana."""
    q = """
        SELECT date_trunc('month', r.tanggal)::date AS bulan,
               t.kategori,
               count(DISTINCT r.id) AS jumlah
        FROM review_topics rt
        JOIN topics  t ON t.id = rt.topic_id
        JOIN reviews r ON r.id = rt.review_id
        GROUP BY 1, 2
        ORDER BY 1, 3 DESC
    """
    d = pd.read_sql(q, eng)
    # Mei 2024 parsial (Temuan 6) — tidak dibuang, tetapi ditandai agar tidak
    # terbaca sebagai bulan dengan volume rendah.
    parsial = pd.Timestamp(CFG["temporal"]["partial_month"] + "-01").date()
    d["periode_parsial"] = d.bulan == parsial
    return d


def tabel3_storytelling(pr: pd.DataFrame, pemicu: pd.DataFrame,
                        neg: pd.DataFrame, n_contoh: int = 3) -> pd.DataFrame:
    """Tabel 3 — kategori, jumlah, %, dan contoh ulasan NYATA (teks asli).

    Dua kriteria, berurutan:

    1. **Eksklusivitas.** Ulasan yang masuk banyak kategori sekaligus tidak
       mengilustrasikan satu pun dengan baik. Tanpa syarat ini, satu ulasan
       ber-likes tinggi yang menyinggung ongkir, pembatalan, dan layanan
       pelanggan akan muncul sebagai contoh ketiganya.
    2. **Likes tertinggi** di antara yang eksklusif: kutipan yang paling banyak
       diamini pembaca lain paling layak mewakili kategori di laporan.

    Panjang dibatasi 40-300 karakter agar dapat dikutip utuh.
    """
    src = neg.set_index("id")[["ulasan", "likes", "rating"]]
    n_kat = pemicu.groupby("review_id").kategori.nunique()
    baris = []
    for r in pr.itertuples():
        ids = pemicu[pemicu.kategori == r.kategori].review_id.unique()
        kand = src.loc[ids].copy()
        kand["n_char"] = kand.ulasan.str.len()
        kand["n_kategori"] = n_kat.reindex(kand.index).to_numpy()
        kand = kand[(kand.n_char >= 40) & (kand.n_char <= 300)]
        eksklusif = kand[kand.n_kategori == 1]
        pilih = (eksklusif if len(eksklusif) >= n_contoh else kand).nlargest(
            n_contoh, "likes")
        row = {"kategori": r.kategori, "jumlah_ulasan": r.jumlah_ulasan,
               "persen": r.persen_ulasan_negatif, "total_likes": r.total_likes,
               "peringkat_frekuensi": r.peringkat_frekuensi,
               "peringkat_likes": r.peringkat_likes}
        for i, (rid, c) in enumerate(pilih.iterrows(), 1):
            row[f"contoh_{i}"] = str(c.ulasan).replace("\n", " ").strip()
            row[f"contoh_{i}_likes"] = int(c.likes)
            row[f"contoh_{i}_n_kategori"] = int(c.n_kategori)
        baris.append(row)
    return pd.DataFrame(baris)


def gambar_09(pr: pd.DataFrame, info: dict) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    d = pr.sort_values("jumlah_ulasan")
    fig, axes = plt.subplots(1, 2, figsize=(13.5, 5.4), sharey=True)
    # Kedua panel memakai URUTAN YANG SAMA (frekuensi). Mengurutkan panel kanan
    # menurut likes akan menyembunyikan justru hal yang ingin ditunjukkan:
    # kategori mana yang peringkatnya bergeser antara kedua lensa.
    for ax, kol, rk, warna, judul, satuan in (
            (axes[0], "jumlah_ulasan", "peringkat_frekuensi", "#4C78A8",
             "FREKUENSI — peringkat primer\n(sesuai batasan Bab 1)", "ulasan"),
            (axes[1], "total_likes", "peringkat_likes", "#F58518",
             "TOTAL LIKES — lensa sekunder (resonansi)\nurutan batang mengikuti panel kiri", "likes")):
        ax.barh(d.kategori, d[kol], color=warna)
        for i, (v, p, r) in enumerate(zip(d[kol], d.persen_ulasan_negatif, d[rk])):
            ket = (f"{v:,.0f}  ({p:.1f}%)" if kol == "jumlah_ulasan" else f"{v:,.0f}")
            ax.text(v * 1.01, i, f"#{r}  {ket}", va="center", fontsize=8.5)
        ax.set_xlim(0, d[kol].max() * 1.24)
        ax.set_title(judul, fontsize=10)
        ax.set_xlabel(f"Jumlah {satuan}")
        ax.spines[["top", "right"]].set_visible(False)
    axes[0].tick_params(axis="y", labelsize=9)
    fig.suptitle("Gambar 9 — Peringkat topik keluhan pada ulasan negatif\n"
                 f"{info['n_negatif']:,} ulasan negatif; penetapan berbasis kata kunci; "
                 f"korpus LDA memakai ambang word_count ≥ {info['ambang_word_count']}",
                 fontsize=11.5)
    fig.tight_layout(rect=[0, 0, 1, 0.9])
    for dpi, suf in ((150, ""), (300, "@300")):
        fig.savefig(ROOT / "docs" / "figures" / f"gambar-09-peringkat-topik{suf}.png",
                    dpi=dpi, bbox_inches="tight")
    plt.close(fig)


if __name__ == "__main__":
    h = jalankan()
    kk, neg, info = h["kk"], h["neg"], h["info"]
    print(f"kata kunci   : {len(kk)} ({(kk.n_gram==1).sum()} unigram + "
          f"{(kk.n_gram==2).sum()} bigram), {kk.kategori.nunique()} kategori")
    print(f"per kategori : {kk.groupby('kategori').size().min()}–"
          f"{kk.groupby('kategori').size().max()}  (DoD: ≥5)")

    pemicu = kata_kunci_pemicu(neg, kk)
    n_topik = pemicu.groupby("review_id").size()
    cakupan = pemicu.review_id.nunique() / len(neg)
    print(f"\nT-5.5 penetapan A (resmi, berbasis kata kunci)")
    print(f"  cakupan    : {pemicu.review_id.nunique():,}/{len(neg):,} = {cakupan:.2%}"
          f"   (DoD: ≥60%)")
    print(f"  rata-rata  : {n_topik.mean():.2f} kategori/ulasan")
    s, pb = h["sepakat"], h["punya_b"]
    print(f"  A vs B (LDA prob≥{AMBANG_LDA}) : sepakat {s[pb].mean():.2%} "
          f"dari {pb.sum():,} ulasan")

    pr = peringkat(pemicu, neg)
    print(f"\nT-5.6 peringkat")
    print(pr[["kategori", "jumlah_ulasan", "persen_ulasan_negatif", "total_likes",
              "peringkat_frekuensi", "peringkat_likes"]].to_string(index=False))

    db = tulis_db(kk, pemicu)
    print(f"\nT-5.7 PostgreSQL: topics={db['n_topics']} baris, "
          f"review_topics={db['n_review_topics']:,} baris ({db['n_review']:,} ulasan)")

    tren = tren_bulanan(db["engine"])
    t3 = tabel3_storytelling(pr, pemicu, neg)
    gambar_09(pr, info)

    kk.to_csv(TAB / "topic_keywords.csv", index=False)
    pr.to_csv(TAB / "topics_ranked.csv", index=False)
    tren.to_csv(TAB / "topic_trend_monthly.csv", index=False)
    t3.to_csv(TAB / "tabel3_storytelling_topik.csv", index=False)
    pemicu.to_parquet(ROOT / "data" / "processed" / "topics.parquet", index=False)

    print(f"\nT-5.8 tren: {len(tren)} baris, {tren.bulan.nunique()} bulan "
          f"({tren.periode_parsial.sum()} baris ditandai periode parsial)")
    print("\nDisimpan: docs/tables/{topic_keywords,topics_ranked,topic_trend_monthly,"
          "tabel3_storytelling_topik}.csv")
    print("          data/processed/topics.parquet, docs/figures/gambar-09-peringkat-topik.png")
