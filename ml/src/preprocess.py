"""Pipeline preprocessing teks (Fase 2).

Urutan operasi sengaja tetap dan tidak boleh diubah tanpa alasan tertulis:

    case folding -> hapus URL -> hapus mention/hashtag -> hapus emoji &
    simbol non-ASCII -> hapus angka -> tanda baca menjadi SPASI -> kolapskan
    huruf berulang (3+) -> tokenisasi -> normalisasi slang (per token) ->
    buang noise token -> stopword removal -> stemming (dengan cache) -> gabung

Menghasilkan dua kolom teks:
  * ulasan_normalized — setelah normalisasi slang, SEBELUM stopword & stemming.
    Terbaca manusia; dipakai untuk word_count, analisis n-gram (Fase 5), dan
    tampilan dashboard.
  * ulasan_clean — hasil pipeline penuh; inilah masukan TF-IDF.
"""
from __future__ import annotations

import json
import os
import re
import time
from multiprocessing import Pool

import pandas as pd
from Sastrawi.Stemmer.StemmerFactory import StemmerFactory

from .config import load_config, resolve
from .ingest import derive_versi_minor, load_raw
from .emoji_map import EMOJI_MAP
from .slang_dict import NOISE_TOKENS, SLANG_DICT
from .stem_override import STEM_OVERRIDE
from .stopwords import build_stopwords

CFG = load_config()
ROOT = CFG["_root"]
P = CFG["preprocessing"]

RE_URL = re.compile(r"https?://\S+|www\.\S+")
RE_MENTION = re.compile(r"[@#]\w+")
RE_NONASCII = re.compile(r"[^\x00-\x7F]+")      # emoji & simbol non-ASCII
RE_DIGIT = re.compile(r"\d+")
RE_PUNCT = re.compile(r"[^a-z\s]")               # sisakan huruf & spasi
RE_REPEAT = re.compile(r"(.)\1{2,}")             # 3+ huruf identik -> 1
RE_SPACE = re.compile(r"\s+")
RE_EKOR = re.compile(r"(\w)\1+\b")            # huruf ganda di akhir kata
_PENGUBAH_EMOJI = "[\U0001F3FB-\U0001F3FF️‍]*"   # warna kulit, selektor varian

# Normalisasi tingkat FRASA — dijalankan sebelum angka & tanda baca dibuang,
# karena sebagiannya justru bergantung pada angka atau tanda hubung.
# Seluruh pemetaan berasal dari putusan pemeriksa pada verifikasi manual pra-pemrosesan.
FRASA: list[tuple[re.Pattern, str]] = [
    (re.compile(r"\bgo[\s\-]?jek\b"), "gojek"),
    (re.compile(r"\bkasi[h]?\s+tau\b"), "kasih tahu"),
    (re.compile(r"\bsebagai\s+nya\b"), "sebagainya"),
    (re.compile(r"\bjadi\s+nya\b"), "jadinya"),
    (re.compile(r"\bpada\s+hal\b"), "padahal"),
    (re.compile(r"\btiba2\b"), "tiba tiba"),
    (re.compile(r"\bga+\s*ada\s+kenapa\s+napa\b"), "tidak ada masalah"),
    (re.compile(r"\bbintang\s*1\b"), "bintang satu"),
    (re.compile(r"\bbintang\s*2\b"), "bintang dua"),
    (re.compile(r"\bbintang\s*3\b"), "bintang tiga"),
    (re.compile(r"\bbintang\s*4\b"), "bintang empat"),
    (re.compile(r"\bbintang\s*5\b"), "bintang lima"),
    (re.compile(r"\bb[#@*$]ng[a-z]{1,4}\b"), "bangsat"),   # umpatan tersamar: b#ngasd, b@ngsat
    # Verifikasi data scraping putaran 1. "top up" sebelumnya menjadi
    # "bagus up" karena `top` -> `bagus` dipetakan per token (3.304 ulasan,
    # kebanyakan keluhan GoPay). Disatukan agar mengikuti entri `topup`.
    (re.compile(r"\btop\s*-?\s*up\b"), "topup"),
    # Kata ulang dengan angka: `mati2an` -> `mati matian`, `kata2nya` ->
    # `kata katanya`. Sebelumnya angka dibuang sehingga akhiran tertinggal
    # sebagai token sendiri (`an` -> `sekitar`). Tidak berlaku bila angka
    # bersambung ke angka lain (`rp2.000`, `tahun2022`).
    (re.compile(r"\b(?!rp\b)([a-z]{2,})[2²]([a-z]*)\b(?![.,]?\d)"), r"\1 \1\2"),
    (re.compile(r"\bwas\s*-?\s*was\b"), "waswas"),   # `was` tunggal = bahasa Inggris, dibuang
]

STOPWORDS = build_stopwords()


# --------------------------------------------------------------- tahap 1 ---
def bersihkan(teks: str, petakan_emoji: bool = False) -> str:
    """Case folding sampai kolaps huruf berulang. Belum ditokenisasi.

    `petakan_emoji` sengaja default False. Lihat `bersihkan_adaptif`.
    """
    t = teks.lower() if P["lowercase"] else teks
    for pola, ganti in FRASA:          # sebelum angka & tanda baca dibuang
        t = pola.sub(ganti, t)
    if petakan_emoji:
        for emo, kata in EMOJI_MAP.items():       # sebelum non-ASCII dibuang
            if emo in t:
                # Emoji identik yang berurutan dihitung sekali: "🔥🔥🔥" -> "keren",
                # bukan "keren keren keren" (verifikasi data scraping putaran 1).
                t = re.sub(f"(?:{re.escape(emo)}{_PENGUBAH_EMOJI})+", f" {kata} ", t)
    if P["remove_url"]:
        t = RE_URL.sub(" ", t)
    t = RE_MENTION.sub(" ", t)
    if P["remove_emoji"]:
        t = RE_NONASCII.sub(" ", t)
    if P["remove_digits"]:
        t = RE_DIGIT.sub(" ", t)
    if P["remove_punctuation"]:
        t = RE_PUNCT.sub(" ", t)          # tanda baca -> SPASI, bukan dihapus
    t = RE_REPEAT.sub(r"\1", t)
    t = RE_KATA.sub(_ringkas_ekor, t)  # `jahatt` -> `jahat`, `mudahh` -> `mudah`
    return RE_SPACE.sub(" ", t).strip()


RE_KATA = re.compile(r"\b[a-z]+\b")


def _ringkas_ekor(m: re.Match) -> str:
    """Huruf ganda di akhir kata diringkas, KECUALI kata itu entri kamus slang.

    Verifikasi data scraping putaran 2 menemukan entri kamus yang berakhiran
    huruf ganda tidak pernah berlaku karena sudah diringkas lebih dulu:
    `gpp` -> `gp` (bukan "tidak apa-apa"), `fee` -> `fe`, `sll` -> `sl`,
    `full` -> `ful`, `call` -> `cal`, `acc` -> `ac`, `shopee` -> `shope`.

    Putaran 3 menambahkan akronim dan istilah yang memang berakhiran huruf
    ganda: "go bill" menjadi "go bil", "SS" (tangkapan layar) menjadi "s", dan
    pada putaran 2 "PBB" menjadi "pb".
    """
    w = m.group(0)
    if w in SLANG_DICT or w in NOISE_TOKENS or w in EKOR_SAH:
        return w
    return RE_EKOR.sub(r"\1", w)


EKOR_SAH = frozenset({"bill", "ss", "pbb", "cc"})


# Ambang kata untuk pemetaan emoji. Lihat bersihkan_adaptif().
MAKS_KATA_EMOJI = 3


def bersihkan_adaptif(teks: str) -> str:
    """Emoji dipetakan hanya pada ulasan pendek.

    Alasannya ditemukan pada verifikasi manual pra-pemrosesan. Ulasan
    "jangan mengemis ke konsumen 🤣🤣🤣" berating 1: emoji tertawa di situ
    sarkastik, dan memetakannya menjadi token positif menyuntik sinyal yang
    berlawanan dengan isi ulasannya.

    Tetapi putaran berikutnya menunjukkan sisi sebaliknya: "Go-jek memang 👍💯"
    kehilangan seluruh sentimennya bila emoji diabaikan, menyisakan "go jek memang".

    Kompromi yang dipakai: emoji dipetakan bila teks tersisa paling banyak
    MAKS_KATA_EMOJI kata. Pada ulasan pendek, emoji memang pembawa sentimen
    utamanya dan ruang untuk sarkasme kecil. Pada ulasan panjang, kata-katanya
    sudah membawa sentimen sendiri dan risiko sarkasme jauh lebih besar.
    """
    t = bersihkan(teks, petakan_emoji=False)
    if len(t.split()) > MAKS_KATA_EMOJI:
        return t
    return bersihkan(teks, petakan_emoji=True)


# --------------------------------------------------------------- tahap 2 ---
def normalisasi_token(tokens: list[str]) -> list[str]:
    """Terapkan kamus slang per token; satu token dapat menjadi beberapa kata.

    Bila sebuah token dipetakan ke bentuk berhubung (`gara` -> `gara-gara`,
    `ugal` -> `ugal-ugalan`), token berikutnya yang merupakan bagian dari bentuk
    itu dilewati. Tanpa ini, "gara gara" menjadi "gara-gara gara-gara".
    """
    out: list[str] = []
    bagian: set[str] = set()
    for tok in tokens:
        if tok in NOISE_TOKENS:
            continue
        if tok in bagian:
            bagian = set()
            continue
        baku = SLANG_DICT.get(tok, [tok]) if P["normalize_slang"] else [tok]
        bagian = set()
        if len(baku) == 1 and baku[0].count("-") == 1:
            a, b = baku[0].split("-")
            if b.startswith(a):                  # kata ulang, bukan `gocar-nya`
                bagian = {a, b}
        out.extend(baku)
    return out


# --------------------------------------------------------------- tahap 3 ---
_worker_stemmer = None


def _init_worker() -> None:
    """Tiap worker membuat stemmer-nya sendiri; objek Sastrawi tidak dapat di-pickle."""
    global _worker_stemmer
    _worker_stemmer = StemmerFactory().create_stemmer()


def _stem_one(w: str) -> tuple[str, str]:
    return w, _worker_stemmer.stem(w)


def _bangun_cache_stem(tokens_unik: set[str]) -> dict[str, str]:
    """Stem per KATA UNIK, bukan per dokumen, dan diparalelkan antar core.

    Tiga lapis penghematan:

    1. Cache per kata unik. Korpus memuat jutaan token tetapi jumlah kata
       unik jauh lebih kecil.
    2. Kata yang sudah ada di kamus dasar Sastrawi tidak perlu di-stem — bentuk
       dasarnya adalah dirinya sendiri.
    3. Sisanya (kata di luar kamus) adalah bagian yang mahal: Sastrawi
       menghabiskan seluruh kaskade aturan afiks sebelum menyerah (~79 ms per
       kata), sehingga dijalankan paralel.

    Hasilnya identik dengan versi satu-core; yang berubah hanya waktu tempuh.
    """
    cache_path = resolve(CFG, "paths.processed_dir") / "stem_cache.json"
    cache: dict[str, str] = {}
    if P["stem_cache"] and cache_path.exists():
        cache = json.loads(cache_path.read_text(encoding="utf-8"))

    # Override diterapkan TANPA memandang cache: entri lama yang terlanjur
    # memuat hasil stem yang salah harus ditimpa, bukan dilewati.
    ditimpa = sum(1 for w, v in STEM_OVERRIDE.items()
                  if w in tokens_unik and cache.get(w) != v)
    for w in tokens_unik & STEM_OVERRIDE.keys():
        cache[w] = STEM_OVERRIDE[w]
    if ditimpa:
        print(f"        {ditimpa} entri cache ditimpa oleh STEM_OVERRIDE", flush=True)

    baru = tokens_unik - cache.keys()
    if not baru:
        cache_path.write_text(json.dumps(cache, ensure_ascii=False), encoding="utf-8")
        return cache

    kamus = set(StemmerFactory().get_words())
    for w in baru & kamus:            # sudah bentuk dasar
        cache[w] = w
    perlu = sorted(baru - kamus)

    if perlu:
        n_proc = max(1, (os.cpu_count() or 2) - 2)
        print(f"        stemming {len(perlu):,} kata di luar kamus pada {n_proc} proses"
              f" ({len(baru & kamus):,} kata lain sudah bentuk dasar)", flush=True)
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        selesai = 0
        t0 = time.perf_counter()
        with Pool(n_proc, initializer=_init_worker) as pool:
            for w, hasil in pool.imap_unordered(_stem_one, perlu, chunksize=50):
                cache[w] = hasil
                selesai += 1
                # Cache ditulis berkala, bukan hanya di akhir: run yang terputus
                # (laptop dimatikan, proses dibunuh) tidak kehilangan progresnya.
                if selesai % 2000 == 0:
                    cache_path.write_text(json.dumps(cache, ensure_ascii=False),
                                          encoding="utf-8")
                    laju = selesai / (time.perf_counter() - t0)
                    sisa = (len(perlu) - selesai) / laju / 60
                    print(f"        {selesai:,}/{len(perlu):,} kata "
                          f"({laju:.0f} kata/detik, sisa ~{sisa:.1f} menit)", flush=True)

    if P["stem_cache"]:
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        cache_path.write_text(json.dumps(cache, ensure_ascii=False), encoding="utf-8")
    return cache


# ------------------------------------------------------------- pipeline ---
def jalankan() -> pd.DataFrame:
    t0 = time.perf_counter()
    print("  [1/6] memuat CSV...", flush=True)
    df = load_raw(CFG)
    df.insert(0, "id", range(1, len(df) + 1))

    print(f"  [2/6] membersihkan {len(df):,} teks...", flush=True)
    bersih = df["Ulasan"].astype(str).map(bersihkan_adaptif)
    print("  [3/6] normalisasi slang...", flush=True)
    tokens = bersih.str.split().map(normalisasi_token)
    df["ulasan_normalized"] = tokens.str.join(" ")
    t_norm = time.perf_counter()

    print("  [4/6] stopword removal...", flush=True)
    tanpa_stop = tokens.map(
        lambda ts: [t for t in ts if t not in STOPWORDS] if P["remove_stopwords"] else ts)

    if P["stemming"]:
        print("  [5/6] mengumpulkan kata unik...", flush=True)
        unik: set[str] = set()
        tanpa_stop.map(unik.update)
        cache = _bangun_cache_stem(unik)
        print("  [6/6] menerapkan stem ke seluruh dokumen...", flush=True)
        df["ulasan_clean"] = tanpa_stop.map(lambda ts: " ".join(cache[t] for t in ts))
    else:
        df["ulasan_clean"] = tanpa_stop.str.join(" ")
    t_stem = time.perf_counter()

    # Kolom turunan. word_count DARI ulasan_normalized — lihat data_contract.md §2.2
    df["word_count"] = df["ulasan_normalized"].str.split().str.len().astype("int16")
    neg, pos = CFG["labeling"]["negative_ratings"], CFG["labeling"]["positive_ratings"]
    df["sentimen_aktual"] = pd.Series(
        [0 if r in neg else (1 if r in pos else pd.NA) for r in df["Rating"]],
        dtype="Int8")
    df["versi_minor"] = derive_versi_minor(df["Versi App"])

    out = df.rename(columns={
        "Nama User": "nama_user", "Ulasan": "ulasan", "Rating": "rating",
        "Tanggal": "tanggal", "Likes": "likes", "Versi App": "versi_app",
    })[["id", "nama_user", "ulasan", "ulasan_normalized", "ulasan_clean", "rating",
        "tanggal", "likes", "versi_app", "versi_minor", "word_count", "sentimen_aktual"]]

    print(f"  normalisasi : {t_norm - t0:6.1f} s")
    print(f"  stemming    : {t_stem - t_norm:6.1f} s")
    print(f"  total       : {time.perf_counter() - t0:6.1f} s")
    return out


def sampel_verifikasi(df: pd.DataFrame, n: int = 100,
                      nama: str = "preprocessing_sample_100",
                      kecuali: set[int] | None = None) -> pd.DataFrame:
    """Sampel before/after untuk pemeriksaan manual.

    Putaran berikutnya memakai `kecuali` (id yang sudah pernah diperiksa) agar
    sampelnya baru, dengan `random_state` yang sama.
    """
    pool = df[~df["id"].isin(kecuali)] if kecuali else df
    s = pool.sample(n, random_state=CFG["seed"])[
        ["id", "ulasan", "ulasan_normalized", "ulasan_clean", "rating", "word_count"]]
    s = s.assign(menjadi_kosong=s.ulasan_clean.str.strip() == "",
                 catatan_pemeriksa="")
    path = ROOT / "docs" / "tables" / f"{nama}.csv"
    s.to_csv(path, index=False)
    return s


# ----------------------------------------------------- inferensi satuan ---
# Dipakai oleh `api/ml_service.py` (Fase 7). Sengaja ditempatkan di
# modul yang sama dengan pipeline pelatihan, bukan ditulis ulang di sisi API:
# pipeline yang berbeda antara pelatihan dan inferensi adalah kelas bug yang
# tidak memunculkan error, hanya prediksi yang pelan-pelan salah.
#
# Satu-satunya perbedaan yang disengaja terhadap `jalankan()` adalah sumber
# hasil stemming. `jalankan()` membangun cache dari SELURUH kata unik korpus;
# di sini kata yang belum ada di cache di-stem langsung oleh Sastrawi. Untuk
# kata yang ada di cache hasilnya identik menurut konstruksi — cache itu memang
# keluaran stemmer yang sama.

_stemmer_inferensi = None
_cache_inferensi: dict[str, str] | None = None


def _muat_cache_inferensi() -> dict[str, str]:
    """Cache stem korpus + STEM_OVERRIDE; override menang, seperti di `jalankan()`."""
    global _cache_inferensi
    if _cache_inferensi is None:
        path = resolve(CFG, "paths.processed_dir") / "stem_cache.json"
        cache = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
        cache.update(STEM_OVERRIDE)
        _cache_inferensi = cache
    return _cache_inferensi


def stem_kata(w: str) -> str:
    global _stemmer_inferensi
    cache = _muat_cache_inferensi()
    if w in cache:
        return cache[w]
    if _stemmer_inferensi is None:
        _stemmer_inferensi = StemmerFactory().create_stemmer()
    cache[w] = _stemmer_inferensi.stem(w)      # kata baru ikut di-cache in-memory
    return cache[w]


def praproses_satu(teks: str) -> dict[str, str]:
    """Pipeline Fase 2 untuk SATU teks. Mengembalikan dua kolom yang sama.

    Urutan operasinya mengikuti `jalankan()` tahap demi tahap; lihat docstring
    modul untuk urutan lengkapnya.
    """
    tokens = normalisasi_token(bersihkan_adaptif(str(teks)).split())
    normalized = " ".join(tokens)

    tanpa_stop = ([t for t in tokens if t not in STOPWORDS]
                  if P["remove_stopwords"] else tokens)
    clean = (" ".join(stem_kata(t) for t in tanpa_stop) if P["stemming"]
             else " ".join(tanpa_stop))

    return {"ulasan_normalized": normalized, "ulasan_clean": clean}


def simpan(df: pd.DataFrame) -> None:
    path = resolve(CFG, "paths.clean_parquet")
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(path, index=False)
    print(f"Disimpan: {path.relative_to(ROOT)} ({path.stat().st_size / 1e6:.1f} MB)")


if __name__ == "__main__":
    df = jalankan()
    simpan(df)
    sampel_verifikasi(df)
    print(f"\nbaris: {len(df):,} | kolom: {len(df.columns)}")
    print(df["sentimen_aktual"].value_counts(dropna=False).to_string())
    kosong = int((df.ulasan_clean.str.strip() == "").sum())
    print(f"ulasan_clean kosong: {kosong:,} ({kosong / len(df) * 100:.1f}%)")
