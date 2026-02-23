"""ORM models for ChessCoach AI."""

import uuid
from datetime import datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import JSON, ARRAY, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    games: Mapped[list["Game"]] = relationship(back_populates="user", cascade="all, delete-orphan")


class Game(Base):
    __tablename__ = "games"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=True)
    pgn: Mapped[str] = mapped_column(Text, nullable=False)
    white_player: Mapped[str | None] = mapped_column(String(100))
    black_player: Mapped[str | None] = mapped_column(String(100))
    player_color: Mapped[str | None] = mapped_column(String(5))
    result: Mapped[str | None] = mapped_column(String(10))
    accuracy: Mapped[float | None] = mapped_column(Float)
    summary: Mapped[dict | None] = mapped_column(JSON)
    moves: Mapped[list | None] = mapped_column(JSON)
    source: Mapped[str | None] = mapped_column(String(50))
    lichess_id: Mapped[str | None] = mapped_column(String(20))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    user: Mapped["User"] = relationship(back_populates="games")


class BookChunk(Base):
    __tablename__ = "book_chunks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    book_title: Mapped[str] = mapped_column(String(255), nullable=False)
    chapter: Mapped[str | None] = mapped_column(String(255))
    section: Mapped[str | None] = mapped_column(String(255))
    content: Mapped[str] = mapped_column(Text, nullable=False)
    content_tokens: Mapped[int | None] = mapped_column(Integer)
    concepts: Mapped[list | None] = mapped_column(ARRAY(String))
    embedding = mapped_column(Vector(384), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)


class AnalysisCache(Base):
    __tablename__ = "analysis_cache"

    fen_hash: Mapped[str] = mapped_column(String(64), primary_key=True)
    fen: Mapped[str] = mapped_column(Text, nullable=False)
    stockfish_result: Mapped[dict | None] = mapped_column(JSON)
    coaching_explanation: Mapped[str | None] = mapped_column(Text)
    book_references: Mapped[list | None] = mapped_column(JSON)
    depth: Mapped[int | None] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    hit_count: Mapped[int] = mapped_column(Integer, default=0)
