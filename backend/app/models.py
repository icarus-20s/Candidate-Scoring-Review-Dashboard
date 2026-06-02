import aiosqlite
from datetime import datetime, timezone

DATABASE_URL = "app.db"

# Opens a new SQLite connection with row factory and WAL mode.
async def get_db():
    db = await aiosqlite.connect(DATABASE_URL)
    db.row_factory = aiosqlite.Row
    await db.execute("PRAGMA journal_mode=WAL")
    await db.execute("PRAGMA foreign_keys=ON")
    return db

# Creates all tables and indexes on startup. Applies column migrations for existing databases.
async def init_db():
    db = await get_db()
    await db.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            name TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'reviewer',
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS candidates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            role_applied TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'new',
            skills TEXT NOT NULL DEFAULT '[]',
            internal_notes TEXT NOT NULL DEFAULT '',
            ai_summary TEXT NOT NULL DEFAULT '',
            deleted_at TEXT DEFAULT NULL,
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS scores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            candidate_id INTEGER NOT NULL,
            category TEXT NOT NULL,
            score INTEGER NOT NULL CHECK(score >= 1 AND score <= 5),
            reviewer_id INTEGER NOT NULL,
            note TEXT DEFAULT '',
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            FOREIGN KEY (candidate_id) REFERENCES candidates(id),
            FOREIGN KEY (reviewer_id) REFERENCES users(id)
        );

        CREATE INDEX IF NOT EXISTS idx_candidates_status ON candidates(status);
        CREATE INDEX IF NOT EXISTS idx_candidates_role_applied ON candidates(role_applied);
        CREATE INDEX IF NOT EXISTS idx_scores_candidate_id ON scores(candidate_id);
        CREATE INDEX IF NOT EXISTS idx_scores_reviewer_id ON scores(reviewer_id);
    """)
    await db.commit()

    for col in [
        "ai_summary TEXT NOT NULL DEFAULT ''",
        "deleted_at TEXT DEFAULT NULL",
    ]:
        try:
            await db.execute(f"ALTER TABLE candidates ADD COLUMN {col}")
            await db.commit()
        except Exception:
            pass

    await db.close()
