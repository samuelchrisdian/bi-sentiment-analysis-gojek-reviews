"""ORM SQLAlchemy (Fase 7, T-7.1).

Hanya tabel yang benar-benar dibaca endpoint yang dipetakan. Materialized view
TIDAK dipetakan sebagai ORM — view tidak punya primary key dan tidak pernah
ditulis; `crud.py` membacanya lewat SQL teks. Memaksakan ORM di atasnya hanya
menambah lapisan tanpa menambah keamanan tipe apa pun.
"""
from __future__ import annotations

from sqlalchemy import (BigInteger, DateTime, Float, ForeignKey, Integer,
                        SmallInteger, Text)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Review(Base):
    __tablename__ = "reviews"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    nama_user: Mapped[str | None] = mapped_column(Text)
    ulasan: Mapped[str] = mapped_column(Text, nullable=False)
    ulasan_clean: Mapped[str | None] = mapped_column(Text)
    rating: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    tanggal: Mapped["DateTime"] = mapped_column(DateTime(timezone=True), nullable=False)
    likes: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    versi_app: Mapped[str | None] = mapped_column(Text)
    versi_minor: Mapped[str | None] = mapped_column(Text)
    word_count: Mapped[int | None] = mapped_column(SmallInteger)
    sentimen_aktual: Mapped[int | None] = mapped_column(SmallInteger)


class ReviewScore(Base):
    __tablename__ = "review_scores"

    review_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("reviews.id", ondelete="CASCADE"), primary_key=True)
    model_name: Mapped[str] = mapped_column(Text, primary_key=True)
    pred_label: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    pred_proba: Mapped[float | None] = mapped_column(Float)


class Topic(Base):
    __tablename__ = "topics"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    kategori: Mapped[str] = mapped_column(Text, nullable=False)
    keyword: Mapped[str] = mapped_column(Text, nullable=False)
    bobot: Mapped[float | None] = mapped_column(Float)


class ModelMetric(Base):
    __tablename__ = "model_metrics"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    model_name: Mapped[str] = mapped_column(Text, nullable=False)
    eval_set: Mapped[str] = mapped_column(Text, nullable=False)
    accuracy: Mapped[float | None] = mapped_column(Float)
    precision_neg: Mapped[float | None] = mapped_column(Float)
    recall_neg: Mapped[float | None] = mapped_column(Float)
    f1_neg: Mapped[float | None] = mapped_column(Float)
    macro_f1: Mapped[float | None] = mapped_column(Float)
    train_seconds: Mapped[float | None] = mapped_column(Float)
