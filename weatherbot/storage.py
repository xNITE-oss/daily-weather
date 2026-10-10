"""Foydalanuvchilar joylashuvi va xabar vaqtini SQLite'da saqlash."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass


@dataclass
class User:
    chat_id: int
    name: str | None
    lat: float
    lon: float
    timezone: str
    hour: int = 7
    minute: int = 0


class Storage:
    def __init__(self, path: str) -> None:
        self.conn = sqlite3.connect(path, check_same_thread=False)
        self.conn.execute(
            """CREATE TABLE IF NOT EXISTS users (
                chat_id INTEGER PRIMARY KEY,
                name TEXT,
                lat REAL NOT NULL,
                lon REAL NOT NULL,
                timezone TEXT NOT NULL,
                hour INTEGER NOT NULL DEFAULT 7,
                minute INTEGER NOT NULL DEFAULT 0
            )"""
        )
        self.conn.commit()

    def save(self, u: User) -> None:
        self.conn.execute(
            """INSERT INTO users (chat_id, name, lat, lon, timezone, hour, minute)
               VALUES (?, ?, ?, ?, ?, ?, ?)
               ON CONFLICT(chat_id) DO UPDATE SET
                 name=excluded.name, lat=excluded.lat, lon=excluded.lon,
                 timezone=excluded.timezone, hour=excluded.hour, minute=excluded.minute""",
            (u.chat_id, u.name, u.lat, u.lon, u.timezone, u.hour, u.minute),
        )
        self.conn.commit()

    def get(self, chat_id: int) -> User | None:
        row = self.conn.execute(
            "SELECT chat_id, name, lat, lon, timezone, hour, minute FROM users WHERE chat_id=?",
            (chat_id,),
        ).fetchone()
        return User(*row) if row else None

    def all(self) -> list[User]:
        rows = self.conn.execute(
            "SELECT chat_id, name, lat, lon, timezone, hour, minute FROM users"
        ).fetchall()
        return [User(*r) for r in rows]

    def delete(self, chat_id: int) -> None:
        self.conn.execute("DELETE FROM users WHERE chat_id=?", (chat_id,))
        self.conn.commit()
