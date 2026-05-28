import os
import aiosqlite
from contextlib import asynccontextmanager
from typing import Optional
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

DB_PATH = os.path.join(os.path.dirname(__file__), "lost_found.db")

SCHEMA = """
PRAGMA journal_mode = WAL;

CREATE TABLE IF NOT EXISTS users (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    full_name    TEXT NOT NULL,
    email        TEXT NOT NULL UNIQUE,
    password     TEXT NOT NULL,
    phone_number TEXT,
    created_at   TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS categories (
    id   INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS reports (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id     INTEGER NOT NULL REFERENCES users(id),
    category_id INTEGER REFERENCES categories(id),
    item_name   TEXT NOT NULL,
    description TEXT,
    type        TEXT NOT NULL CHECK(type IN ('lost','found')),
    location    TEXT,
    status      TEXT NOT NULL DEFAULT 'active',
    created_at  TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS messages (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    sender_id   INTEGER NOT NULL REFERENCES users(id),
    receiver_id INTEGER NOT NULL REFERENCES users(id),
    content     TEXT NOT NULL,
    is_read     INTEGER NOT NULL DEFAULT 0,
    created_at  TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS matches (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    lost_report_id  INTEGER NOT NULL REFERENCES reports(id),
    found_report_id INTEGER NOT NULL REFERENCES reports(id),
    created_at      TEXT DEFAULT (datetime('now'))
);
"""

CATEGORIES = [
    (1, "Elektronik"), (2, "Kiyafet & Aksesuar"), (3, "Canta & Cuzdan"),
    (4, "Belge & Kimlik"), (5, "Anahtar"), (6, "Taki & Saat"), (7, "Diger"),
]


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.executescript(SCHEMA)
        for cid, name in CATEGORIES:
            await db.execute(
                "INSERT OR IGNORE INTO categories(id,name) VALUES(?,?)", (cid, name)
            )
        await db.commit()
    print(f"DB ready: {DB_PATH}")
    yield


app = FastAPI(title="Lost & Found API", lifespan=lifespan)
app.mount("/static", StaticFiles(directory="static"), name="static")


# ── Page routes ───────────────────────────────────────────

@app.get("/")
async def home(): return FileResponse("templates/index.html")

@app.get("/auth")
async def auth_page(): return FileResponse("templates/auth.html")

@app.get("/reports")
async def reports_page(): return FileResponse("templates/reports.html")

@app.get("/create")
async def create_page(): return FileResponse("templates/create.html")

@app.get("/messages")
async def messages_page(): return FileResponse("templates/messages.html")


# ── DB helpers ────────────────────────────────────────────

def row_to_dict(row):
    return {k: row[k] for k in row.keys()} if row else None


async def fetch_one(query, params=()):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        await db.execute("PRAGMA foreign_keys = ON")
        cur = await db.execute(query, params)
        return await cur.fetchone()


async def fetch_all(query, params=()):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        await db.execute("PRAGMA foreign_keys = ON")
        cur = await db.execute(query, params)
        return [row_to_dict(r) for r in await cur.fetchall()]


async def execute(query, params=()):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("PRAGMA foreign_keys = ON")
        cur = await db.execute(query, params)
        await db.commit()
        return cur.lastrowid


# ── Pydantic models ───────────────────────────────────────

class RegisterIn(BaseModel):
    full_name: str
    email: str
    password: str
    phone_number: Optional[str] = None

class LoginIn(BaseModel):
    email: str
    password: str

class ReportIn(BaseModel):
    user_id: int
    category_id: Optional[int] = None
    item_name: str
    description: Optional[str] = None
    type: str
    location: Optional[str] = None

class MessageIn(BaseModel):
    sender_id: int
    receiver_id: int
    content: str

class MatchIn(BaseModel):
    lost_report_id: int
    found_report_id: int


# ── API routes ────────────────────────────────────────────

@app.post("/api/register", status_code=201)
async def register(body: RegisterIn):
    try:
        uid = await execute(
            "INSERT INTO users(full_name,email,password,phone_number) VALUES(?,?,?,?)",
            (body.full_name.strip(), body.email.strip(), body.password, body.phone_number),
        )
        return {"message": "Kayit basarili.", "kullanici_id": uid}
    except aiosqlite.IntegrityError:
        raise HTTPException(409, "Bu e-posta zaten kayitli.")


@app.post("/api/login")
async def login(body: LoginIn):
    row = await fetch_one(
        "SELECT * FROM users WHERE email=? AND password=?",
        (body.email.strip(), body.password),
    )
    if not row:
        raise HTTPException(401, "Gecersiz e-posta veya sifre.")
    return {
        "kullanici_id": row["id"],
        "full_name": row["full_name"],
        "email": row["email"],
    }


@app.get("/api/categories")
async def get_categories():
    return await fetch_all("SELECT * FROM categories ORDER BY id")


@app.get("/api/reports")
async def get_reports(type: Optional[str] = None, q: Optional[str] = None):
    sql = """
        SELECT r.id, r.item_name, r.description, r.type, r.location, r.status,
               r.created_at AS date, r.category_id, c.name AS category_name,
               r.user_id, u.full_name AS reported_by
        FROM reports r
        LEFT JOIN users      u ON u.id = r.user_id
        LEFT JOIN categories c ON c.id = r.category_id
        WHERE 1=1
    """
    params = []
    if type in ("lost", "found"):
        sql += " AND r.type=?"; params.append(type)
    if q:
        sql += " AND (r.item_name LIKE ? OR r.description LIKE ? OR r.location LIKE ?)"
        params += [f"%{q}%", f"%{q}%", f"%{q}%"]
    sql += " ORDER BY r.created_at DESC"
    return await fetch_all(sql, params)


@app.post("/api/reports", status_code=201)
async def create_report(body: ReportIn):
    if body.type not in ("lost", "found"):
        raise HTTPException(400, "type 'lost' veya 'found' olmali.")
    if not await fetch_one("SELECT id FROM users WHERE id=?", (body.user_id,)):
        raise HTTPException(404, "Kullanici bulunamadi.")
    rid = await execute(
        "INSERT INTO reports(user_id,category_id,item_name,description,type,location) VALUES(?,?,?,?,?,?)",
        (body.user_id, body.category_id, body.item_name.strip(), body.description, body.type, body.location),
    )
    return {"message": "Ilan olusturuldu.", "report_id": rid}


@app.post("/api/messages", status_code=201)
async def send_message(body: MessageIn):
    for uid, label in [(body.sender_id, "sender_id"), (body.receiver_id, "receiver_id")]:
        if not await fetch_one("SELECT id FROM users WHERE id=?", (uid,)):
            raise HTTPException(404, f"{label}={uid} bulunamadi.")
    mid = await execute(
        "INSERT INTO messages(sender_id,receiver_id,content) VALUES(?,?,?)",
        (body.sender_id, body.receiver_id, body.content),
    )
    return {"message": "Mesaj gonderildi.", "message_id": mid}


@app.get("/api/messages/{user_id}")
async def get_messages(user_id: int, box: str = "inbox"):
    if not await fetch_one("SELECT id FROM users WHERE id=?", (user_id,)):
        raise HTTPException(404, "Kullanici bulunamadi.")

    if box == "sent":
        return await fetch_all("""
            SELECT m.id, m.content, m.created_at AS date, m.is_read,
                   m.receiver_id, u.full_name AS receiver_name, m.sender_id
            FROM messages m
            LEFT JOIN users u ON u.id = m.receiver_id
            WHERE m.sender_id = ?
            ORDER BY m.created_at DESC
        """, (user_id,))

    return await fetch_all("""
        SELECT m.id, m.content, m.created_at AS date, m.is_read,
               m.sender_id, u.full_name AS sender_name, m.receiver_id
        FROM messages m
        LEFT JOIN users u ON u.id = m.sender_id
        WHERE m.receiver_id = ?
        ORDER BY m.created_at DESC
    """, (user_id,))


@app.post("/api/matches", status_code=201)
async def create_match(body: MatchIn):
    lost  = await fetch_one("SELECT id,type FROM reports WHERE id=?", (body.lost_report_id,))
    found = await fetch_one("SELECT id,type FROM reports WHERE id=?", (body.found_report_id,))
    if not lost:  raise HTTPException(404, f"lost_report_id={body.lost_report_id} bulunamadi.")
    if not found: raise HTTPException(404, f"found_report_id={body.found_report_id} bulunamadi.")
    if lost["type"]  != "lost":  raise HTTPException(400, "lost_report_id 'lost' turunde degil.")
    if found["type"] != "found": raise HTTPException(400, "found_report_id 'found' turunde degil.")
    mid = await execute(
        "INSERT INTO matches(lost_report_id,found_report_id) VALUES(?,?)",
        (body.lost_report_id, body.found_report_id),
    )
    return {"message": "Eslasme olusturuldu.", "match_id": mid}
