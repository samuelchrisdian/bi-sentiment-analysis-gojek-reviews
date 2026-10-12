"""Pemetaan emoji ke token sentimen (Fase 2, hasil verifikasi manual pra-pemrosesan).

Verifikasi manual menemukan ulasan yang isinya hanya emoji menjadi kosong total,
padahal umumnya berating 4-5 dan jelas membawa sentimen positif.

Membuang emoji berarti membuang sinyal pada ulasan yang memang hanya berisi
emoji. Emoji dipetakan lebih dulu ke kata, baru sisanya dibersihkan.

Dibatasi pada emoji yang maknanya tidak ambigu dalam konteks ulasan aplikasi.
Emoji ambigu (mis. 🤣, 🙏) sengaja TIDAK dipetakan: tertawa dapat berarti senang
maupun mengejek, dan 🙏 dapat berarti terima kasih maupun memohon.
"""
from __future__ import annotations

EMOJI_MAP: dict[str, str] = {
    # Positif
    "👍": "bagus", "👍🏻": "bagus", "👍🏼": "bagus", "👍🏽": "bagus", "👍🏾": "bagus", "👍🏿": "bagus",
    "😍": "suka", "🥰": "suka", "❤": "suka", "❤️": "suka", "💕": "suka", "💖": "suka",
    "😊": "senang", "😁": "senang", "😀": "senang", "😃": "senang", "🙂": "senang",
    "😎": "keren", "🔥": "keren", "💯": "sempurna", "⭐": "bintang", "🌟": "bintang",
    "👏": "apresiasi", "🙌": "apresiasi", "✅": "baik", "😘": "suka",
    "👌": "oke", "✊": "semangat", "🤝": "apresiasi", "🥇": "terbaik", "😇": "baik",

    # Negatif
    "👎": "jelek", "😡": "marah", "🤬": "marah", "😠": "marah",
    "😭": "kecewa", "😢": "kecewa", "😞": "kecewa", "😔": "kecewa", "🥲": "kecewa",
    "😤": "kesal", "😒": "kesal", "🙄": "kesal", "😑": "kesal", "😪": "lelah",
    "💔": "kecewa", "❌": "buruk", "🤮": "buruk", "🤢": "buruk",
}
