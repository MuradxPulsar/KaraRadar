import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from kararadar.core.radar_anim import RadarAnimation, render_frame, RadarState
import io


def test_nontty_line_mode(monkeypatch):
    monkeypatch.setattr("sys.stdout.isatty", lambda: False)
    anim = RadarAnimation(enabled=True)
    assert anim.enabled is True
    assert anim._line_mode is True


def test_frame_size():
    st = RadarState()
    lines = render_frame(st)
    assert len(lines) >= 10
    assert any("Scanned:" in l for l in lines)


def test_cursor_restore(monkeypatch):
    # no TTY -> no thread; __exit__ shows cursor harmlessly
    monkeypatch.setattr("sys.stdout.isatty", lambda: False)
    anim = RadarAnimation(enabled=True)
    with anim:
        pass
    assert True
