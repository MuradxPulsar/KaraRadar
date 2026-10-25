"""SQLite helpers for runs, history and seen domains (watch mode)."""
import sqlite3, os, time, json
DEFAULT_DB = os.path.join(os.path.expanduser("~"), ".kararadar.db")


def _conn(path=None):
    if path is None:
        path=DEFAULT_DB
    c = sqlite3.connect(path)
    c.execute("""CREATE TABLE IF NOT EXISTS runs(id INTEGER PRIMARY KEY AUTOINCREMENT, ts REAL, lang TEXT)""")
    c.execute("""CREATE TABLE IF NOT EXISTS run_domains(run_id INTEGER, domain TEXT, verdict TEXT, score INTEGER)""")
    c.execute("""CREATE TABLE IF NOT EXISTS seen(domain TEXT PRIMARY KEY, first_seen REAL, last_seen REAL)""")
    c.commit()
    return c


def record_run(run_id=None, domains=None, lang="az"):
    c = _conn()
    ts = time.time()
    cur = c.execute("INSERT INTO runs(ts,lang) VALUES(?,?)", (ts, lang))
    rid = cur.lastrowid
    for d in (domains or []):
        c.execute("INSERT INTO run_domains(run_id,domain,verdict,score) VALUES(?,?,?,?)",
                  (rid, d.get("domain"), d.get("verdict"), d.get("score")))
    c.commit()
    c.close()
    return rid


def mark_seen(domain):
    c = _conn()
    now = time.time()
    cur = c.execute("SELECT first_seen FROM seen WHERE domain=?", (domain,))
    r = cur.fetchone()
    if r:
        c.execute("UPDATE seen SET last_seen=? WHERE domain=?", (now, domain))
    else:
        c.execute("INSERT INTO seen VALUES(?,?,?)", (domain, now, now))
    c.commit()
    c.close()


def history(limit=10):
    c = _conn()
    rows = c.execute("SELECT id,ts,lang FROM runs ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
    out = []
    for rid, ts, lang in rows:
        dd = c.execute("SELECT domain,verdict,score FROM run_domains WHERE run_id=?", (rid,)).fetchall()
        out.append({"id": rid, "ts": ts, "lang": lang, "domains": dd})
    c.close()
    return out


def diff_runs(a_id, b_id):
    c = _conn()
    a = {r[0]: r for r in c.execute("SELECT domain,verdict,score FROM run_domains WHERE run_id=?", (a_id,)).fetchall()}
    b = {r[0]: r for r in c.execute("SELECT domain,verdict,score FROM run_domains WHERE run_id=?", (b_id,)).fetchall()}
    c.close()
    new = sorted(set(b) - set(a))
    gone = sorted(set(a) - set(b))
    changed = sorted([d for d in set(a) & set(b) if a[d] != b[d]])
    return {"new": new, "gone": gone, "changed": changed}
