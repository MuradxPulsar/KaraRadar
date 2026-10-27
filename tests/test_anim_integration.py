import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from kararadar.core import radar_anim
from kararadar.main import monitor_brands


def test_monitor_brands_uses_animation(monkeypatch):
    created = {"n": 0}

    class Fake:
        def __init__(self, *a, **k):
            created["n"] += 1
            self.enabled = True
            self._line_mode = False

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

    monkeypatch.setattr(radar_anim, "RadarAnimation", Fake)
    monkeypatch.setattr("kararadar.sources.crtsh.search_keyword_status", lambda kw, limit=80: ([], "empty"))
    try:
        monitor_brands(limit=1, max_brands=1)
    except Exception:
        pass
    assert created["n"] >= 1, "monitor_brands must use RadarAnimation"
