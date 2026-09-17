"""Ekstraksi topik keluhan — RM2 (Fase 5, T-5.1 s/d T-5.3).

Fokus HANYA korpus negatif. Ini keputusan yang menguntungkan secara teknis:
korpus positif 32% duplikat dan didominasi pujian dua kata, sedangkan korpus
negatif hanya 4,2% duplikat dan lebih panjang (Temuan 2) — LDA punya materi
yang layak untuk bekerja.

Pembagian wewenang di fase ini tegas: modul ini melakukan KLASTERING.
Penamaan kategori bisnis adalah interpretasi domain dan milik manusia
(gerbang H-8). Tidak ada nama kategori yang ditulis modul ini.
"""
from __future__ import annotations

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from gensim import corpora
from gensim.models import CoherenceModel, LdaModel
from sklearn.feature_extraction.text import CountVectorizer

from .config import load_config, resolve

CFG = load_config()
ROOT = CFG["_root"]
SEED = CFG["seed"]
FIG = ROOT / "docs" / "figures"
TAB = ROOT / "docs" / "tables"
AMBANG_KATA = CFG["evaluation"]["informative_min_words"]

# Parameter LDA dicatat di sini, bukan tersebar: hasil LDA stokastik sehingga
# reprodusibilitas bergantung sepenuhnya pada ketiganya.
LDA_PASSES = 10
LDA_ALPHA = "auto"
LDA_ITERATIONS = 100


def korpus_negatif() -> tuple[pd.DataFrame, dict]:
    """T-5.1 — korpus topik: ulasan negatif dengan >=5 kata."""
    df = pd.read_parquet(resolve(CFG, "paths.clean_parquet"))
    neg = df[df["sentimen_aktual"] == 0].copy()
    assert len(neg) == 26732, f"korpus negatif {len(neg)} != 26732"

    topik = neg[neg["word_count"] >= AMBANG_KATA].copy()
    info = {
        "n_negatif": len(neg),
        "n_korpus_topik": len(topik),
        "n_dibuang": len(neg) - len(topik),
        "persen_dibuang": round((len(neg) - len(topik)) / len(neg) * 100, 2),
        "ambang_word_count": AMBANG_KATA,
        "n_duplikat_teks": int(topik["ulasan_clean"].duplicated().sum()),
        "rata_kata": round(float(topik["word_count"].mean()), 2),
    }
    return topik, info


def ngram(topik: pd.DataFrame, top_n: int = 30) -> pd.DataFrame:
    """T-5.2 — frekuensi unigram & bigram.

    Dikerjakan SEBELUM LDA: hasilnya temuan mandiri sekaligus rujukan manusia
    saat menamai klaster di H-8.
    """
    cv = CountVectorizer(ngram_range=(1, 2), min_df=10, token_pattern=r"\S+",
                         lowercase=False)
    X = cv.fit_transform(topik["ulasan_clean"])
    f = pd.DataFrame({"term": cv.get_feature_names_out(),
                      "freq": np.asarray(X.sum(axis=0)).ravel()})
    f["n_dokumen"] = np.asarray((X > 0).sum(axis=0)).ravel()
    f["n_gram"] = f.term.str.count(" ") + 1
    f["persen_dokumen"] = (f.n_dokumen / len(topik) * 100).round(2)

    out = []
    for n in (1, 2):
        g = f[f.n_gram == n].nlargest(top_n, "freq").copy()
        g.insert(0, "rank", range(1, len(g) + 1))
        out.append(g)
    return pd.concat(out, ignore_index=True)[
        ["n_gram", "rank", "term", "freq", "n_dokumen", "persen_dokumen"]]


def siapkan_gensim(topik: pd.DataFrame):
    texts = [t.split() for t in topik["ulasan_clean"]]
    dictionary = corpora.Dictionary(texts)
    dictionary.filter_extremes(no_below=10, no_above=0.5)
    corpus = [dictionary.doc2bow(t) for t in texts]
    return texts, dictionary, corpus


def cari_k(texts, dictionary, corpus) -> tuple[pd.DataFrame, dict]:
    """T-5.3 — coherence c_v untuk k = 5..12."""
    lo, hi = CFG["topics"]["lda_n_topics_range"]
    baris, model = [], {}
    for k in range(lo, hi + 1):
        lda = LdaModel(corpus=corpus, id2word=dictionary, num_topics=k,
                       random_state=SEED, passes=LDA_PASSES, alpha=LDA_ALPHA,
                       iterations=LDA_ITERATIONS)
        cv = CoherenceModel(model=lda, texts=texts, dictionary=dictionary,
                            coherence="c_v").get_coherence()
        umass = CoherenceModel(model=lda, corpus=corpus, dictionary=dictionary,
                               coherence="u_mass").get_coherence()
        baris.append({"k": k, "coherence_cv": cv, "coherence_umass": umass})
        model[k] = lda
        print(f"  k={k:2d}  c_v={cv:.4f}  u_mass={umass:.4f}")
    return pd.DataFrame(baris), model


def pilih_k(sk: pd.DataFrame) -> tuple[int, str]:
    """Puncak c_v; bila ada puncak lain dalam 0,005, pilih k yang lebih kecil.

    Selisih coherence sekecil itu tidak bermakna, sedangkan jumlah topik yang
    lebih kecil jauh lebih mudah dinarasikan dan dilabeli manusia di H-8.
    """
    puncak = sk.loc[sk.coherence_cv.idxmax()]
    dekat = sk[sk.coherence_cv >= puncak.coherence_cv - 0.005]
    k = int(dekat.k.min())
    if k == int(puncak.k):
        return k, (f"k={k} adalah puncak c_v ({puncak.coherence_cv:.4f}) "
                   f"dan tidak ada k lebih kecil dalam 0,005 dari puncak")
    return k, (f"puncak c_v di k={int(puncak.k)} ({puncak.coherence_cv:.4f}), "
               f"tetapi k={k} hanya selisih "
               f"{puncak.coherence_cv - float(dekat[dekat.k == k].coherence_cv.iloc[0]):.4f} "
               f"— dipilih yang lebih kecil karena lebih mudah dinarasikan")


def gambar_08(sk: pd.DataFrame, k_pilih: int) -> None:
    fig, ax = plt.subplots(figsize=(7.8, 4.2))
    ax.plot(sk.k, sk.coherence_cv, "o-", color="#4C78A8", lw=2, ms=6)
    for _, r in sk.iterrows():
        ax.annotate(f"{r.coherence_cv:.3f}", (r.k, r.coherence_cv),
                    textcoords="offset points", xytext=(0, 8), ha="center", fontsize=7.5)
    y = float(sk[sk.k == k_pilih].coherence_cv.iloc[0])
    ax.plot(k_pilih, y, "o", ms=13, mfc="none", mec="#E45756", mew=2.2)
    ax.annotate(f"k terpilih = {k_pilih}", (k_pilih, y), textcoords="offset points",
                xytext=(16, 10), ha="left", color="#E45756", fontsize=9.5,
                fontweight="bold")
    ax.margins(x=0.08)
    ax.set_xlabel("Jumlah topik (k)"); ax.set_ylabel("Coherence $c_v$")
    ax.set_xticks(sk.k)
    ax.set_title("Gambar 8 — Coherence LDA vs jumlah topik\n"
                 "korpus ulasan negatif, word_count ≥ 5", fontsize=11)
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(axis="y", alpha=.25)
    for dpi, suf in ((150, ""), (300, "@300")):
        fig.savefig(FIG / f"gambar-08-lda-coherence{suf}.png", dpi=dpi, bbox_inches="tight")
    plt.close(fig)


def gambar_08b(ng: pd.DataFrame, info: dict) -> None:
    """Pelengkap T-5.2 — pengganti word cloud.

    Rencana menyebut word cloud sebagai pelengkap dan bukan bukti utama.
    Batang berurut dipilih karena panjang batang dapat dibaca sebagai angka,
    sementara ukuran huruf pada word cloud tidak — dan karena `wordcloud`
    tidak termasuk dependensi terkunci Fase 0.
    """
    fig, axes = plt.subplots(1, 2, figsize=(12.5, 6.2))
    for ax, n, warna, judul in ((axes[0], 1, "#4C78A8", "Unigram"),
                                (axes[1], 2, "#F58518", "Bigram")):
        g = ng[ng.n_gram == n].head(20).iloc[::-1]
        ax.barh(g.term, g.freq, color=warna)
        for i, (v, p) in enumerate(zip(g.freq, g.persen_dokumen)):
            ax.text(v * 1.01, i, f"{v:,} ({p:.1f}%)", va="center", fontsize=7.5)
        ax.set_xlim(0, g.freq.max() * 1.22)
        ax.set_title(f"{judul} — 20 teratas", fontsize=10.5)
        ax.set_xlabel("Frekuensi (persentase = pangsa dokumen)")
        ax.tick_params(axis="y", labelsize=8.5)
        ax.spines[["top", "right"]].set_visible(False)
    fig.suptitle(f"Gambar 8b — Istilah paling sering pada ulasan negatif\n"
                 f"{info['n_korpus_topik']:,} ulasan, ambang word_count ≥ "
                 f"{info['ambang_word_count']}", fontsize=11.5)
    fig.tight_layout(rect=[0, 0, 1, 0.93])
    for dpi, suf in ((150, ""), (300, "@300")):
        fig.savefig(FIG / f"gambar-08b-ngram-negatif{suf}.png", dpi=dpi, bbox_inches="tight")
    plt.close(fig)


def berkas_pelabelan(lda: LdaModel, corpus, topik: pd.DataFrame,
                     n_kata: int = 20, n_prob: int = 5, n_tipikal: int = 5,
                     dist: np.ndarray | None = None):
    """T-5.4 bagian agent — klaster mentah untuk gerbang H-8.

    Dua jenis contoh disertakan, dan itu disengaja. Dokumen dengan probabilitas
    topik TERTINGGI cenderung degenerate: ulasan pendek berisi pengulangan satu
    kata (mis. emoji 👎 yang dipetakan Fase 2 menjadi "jelek jelek jelek...")
    memperoleh probabilitas hampir 1 karena seluruh isinya satu topik. Ulasan
    semacam itu hanya 0,18% korpus tetapi mendominasi peringkat teratas, dan
    menilai klaster hanya darinya akan menyesatkan.

    Karena itu `contoh_tipikal_*` diambil acak dari dokumen yang topik ini
    dominan DAN panjangnya wajar (10-60 kata) — inilah yang mewakili klaster.

    Kolom `kategori_usulan` dan `alasan` dibiarkan KOSONG. Penamaan kategori
    bisnis adalah interpretasi domain; label yang ditebak agent akan mengalir ke
    tabel `topics`, ke dashboard, dan ke Tabel 3 laporan sekaligus.
    """
    if dist is None:
        dist = np.zeros((len(corpus), lda.num_topics))
        for i, bow in enumerate(corpus):
            for tid, pr in lda.get_document_topics(bow, minimum_probability=0.0):
                dist[i, tid] = pr

    asli = topik["ulasan"].to_numpy()
    wc = topik["word_count"].to_numpy()
    dominan = dist.argmax(axis=1)
    rng = np.random.default_rng(SEED)

    baris = []
    for tid in range(lda.num_topics):
        kata = lda.show_topic(tid, topn=n_kata)
        mask_dom = dominan == tid
        r = {"topic_id": tid,
             "n_dokumen_dominan": int(mask_dom.sum()),
             "pangsa_dokumen_dominan": round(float(mask_dom.mean()) * 100, 2),
             "top_terms": ", ".join(w for w, _ in kata),
             "top_terms_bobot": ", ".join(f"{w}:{b:.4f}" for w, b in kata)}

        for j, idx in enumerate(np.argsort(dist[:, tid])[::-1][:n_prob], 1):
            r[f"contoh_prob_{j}"] = str(asli[idx]).replace("\n", " ").strip()
            r[f"prob_{j}"] = round(float(dist[idx, tid]), 4)

        layak = np.flatnonzero(mask_dom & (wc >= 10) & (wc <= 60))
        pilih = rng.choice(layak, size=min(n_tipikal, len(layak)), replace=False)
        pilih = pilih[np.argsort(dist[pilih, tid])[::-1]]
        for j, idx in enumerate(pilih, 1):
            r[f"contoh_tipikal_{j}"] = str(asli[idx]).replace("\n", " ").strip()
            r[f"prob_tipikal_{j}"] = round(float(dist[idx, tid]), 4)

        r["kategori_usulan"] = ""      # DIISI MANUSIA — gerbang H-8
        r["alasan"] = ""               # DIISI MANUSIA — gerbang H-8
        baris.append(r)
    return pd.DataFrame(baris), dist


if __name__ == "__main__":
    print("=" * 66)
    topik, info = korpus_negatif()
    print("T-5.1 korpus topik")
    for k, v in info.items():
        print(f"  {k:22s} {v:,}" if isinstance(v, int) else f"  {k:22s} {v}")

    print("\nT-5.2 frekuensi n-gram")
    ng = ngram(topik)
    ng.to_csv(TAB / "ngram_negatif.csv", index=False)
    for n, nama in ((1, "unigram"), (2, "bigram")):
        atas = ng[ng.n_gram == n].head(12)
        print(f"  {nama} teratas: " + ", ".join(
            f"{r.term}({r.freq:,})" for r in atas.itertuples()))
    gambar_08b(ng, info)

    print("\nT-5.3 LDA — coherence k=5..12")
    texts, dictionary, corpus = siapkan_gensim(topik)
    print(f"  kamus setelah filter_extremes: {len(dictionary):,} token")
    sk, model = cari_k(texts, dictionary, corpus)
    sk.to_csv(TAB / "lda_coherence.csv", index=False)
    k, alasan = pilih_k(sk)
    print(f"\n  k terpilih = {k}\n  alasan     : {alasan}")
    gambar_08(sk, k)

    print("\nT-5.4 (bagian agent) berkas klaster untuk H-8")
    lab, dist = berkas_pelabelan(model[k], corpus, topik)
    lab.to_csv(TAB / "lda_clusters_for_labeling.csv", index=False)
    np.save(ROOT / "data" / "processed" / "lda_doc_topic.npy", dist)
    model[k].save(str(ROOT / "ml" / "artifacts" / f"lda_k{k}.gensim"))
    dictionary.save(str(ROOT / "ml" / "artifacts" / "lda_dictionary.gensim"))
    for r in lab.itertuples():
        print(f"  topik {r.topic_id}: {r.pangsa_dokumen_dominan:5.2f}% dok — "
              f"{', '.join(r.top_terms.split(', ')[:10])}")
    print(f"\nDisimpan: docs/tables/{{ngram_negatif,lda_coherence,"
          f"lda_clusters_for_labeling}}.csv")
    print(f"          docs/figures/gambar-08-lda-coherence.png, gambar-08b-ngram-negatif.png")
    print(f"          ml/artifacts/lda_k{k}.gensim, lda_dictionary.gensim")
