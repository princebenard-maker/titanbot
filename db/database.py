import sqlite3, asyncio, logging, os
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
logger = logging.getLogger(__name__)
_lock = asyncio.Lock()
_executor = ThreadPoolExecutor(max_workers=1)
DB_PATH = os.getenv("DB_PATH", "./data/titanbot.db")

def _get_conn():
    Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn

async def execute_write(query, params=()):
    async with _lock:
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            _executor, _sw, query, params)

def _sw(q, p):
    c = _get_conn()
    try: c.execute(q,p); c.commit()
    finally: c.close()

async def execute_read(query, params=()):
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(
        _executor, _sr, query, params)

def _sr(q, p):
    c = _get_conn()
    try: return [dict(r) for r in c.execute(q,p).fetchall()]
    finally: c.close()

async def execute_read_one(query, params=()):
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(
        _executor, _sro, query, params)

def _sro(q, p):
    c = _get_conn()
    try:
        r = c.execute(q,p).fetchone()
        return dict(r) if r else None
    finally: c.close()
