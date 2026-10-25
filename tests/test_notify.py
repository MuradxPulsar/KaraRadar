import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import kararadar.notify as notify


def test_notify_console(capsys):
    notify.alert("example.invalid", 10, "neytral", 40)
    out = capsys.readouterr().out
    assert "[ALERT]" in out
