"""SQLite cache with TTL."""
import json
import os
import sqlite3
import time

DEFAULT_DB = os.path.join(os.path.expanduser("~"), ".kararadar_cache.db")

class Cache:
    def __init__(self, path=DEFAULT_DB, ttl=86400):
        self.path = path
        self.ttl = ttl
        self._conn = sqlite3.connect(path)
        self._conn.execute(
            "CREATE TABLE IF NOT EXISTS cache (key TEXT PRIMARY KEY, value TEXT, expires REAL)"
        )
        self._conn.execute(
            "CREATE TABLE IF NOT EXISTS history (id INTEGER PRIMARY KEY AUTOINCREMENT, domain TEXT, verdict TEXT, score INTEGER, ts REAL)"
        )
        self._conn.commit()

    def get(self, key):
        cur = self._conn.execute(
            "SELECT value, expires FROM cache WHERE key=?", (key,))
        row = cur.fetchone()
        if not row:
            return None
        value, expires = row
        if expires < time.time():
            self._conn.execute("DELETE FROM cache WHERE key=?", (key,))
            self._conn.commit()
            return None
        try:
            return json.loads(value)
        except Exception:
            return value

    def set(self, key, value, ttl=None):
        ttl = ttl or self.ttl
        self._conn.execute(
            "INSERT OR REPLACE INTO cache (key, value, expires) VALUES (?,?,?)",
            (key, json.dumps(value, default=str), time.time() + ttl),
        )
        self._conn.commit()

    def record_run(self, domain, verdict, score):
        self._conn.execute(
            "INSERT INTO history (domain, verdict, score, ts) VALUES (?,?,?,?)",
            (domain, verdict, score, time.time()),
        )
        self._conn.commit()

    def trend(self, limit=30):
        cur = self._conn.execute(
            "SELECT verdict, COUNT(*) FROM history GROUP BY verdict"
        )
        return cur.fetchall()

    def purge(self):
        self._conn.execute("DELETE FROM cache WHERE expires<?", (time.time(),))
        self._conn.commit()

    def close(self):
        self._conn.close()