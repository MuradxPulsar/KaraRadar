import os, tempfile, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import kararadar.db as db
import kararadar.i18n as i18n


def test_db_history_diff():
    orig = db.DEFAULT_DB
    db.DEFAULT_DB = os.path.join(tempfile.mkdtemp(), "t.db")
    try:
        r1 = db.record_run(domains=[{"domain": "a.com", "verdict": "neytral", "score": 0}], lang="az")
        r2 = db.record_run(domains=[{"domain": "b.com", "verdict": "neytral", "score": 0}], lang="az")
        h = db.history(5)
        assert len(h) >= 2
        diff = db.diff_runs(r1, r2)
        assert "b.com" in diff["new"]
        db.mark_seen("a.com")
    finally:
        db.DEFAULT_DB = orig


def test_i18n():
    assert i18n.t("az", "opt8") == "Exit"
    assert i18n.t("en", "opt8") == "Exit"
