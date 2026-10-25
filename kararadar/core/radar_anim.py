"""Live radar animation for scans (pure ANSI, threaded, no deps)."""
import atexit
import hashlib
import math
import os
import shutil
import sys
import threading
import time

_HIDE = "\x1b[?25l"
_SHOW = "\x1b[?25h"
_CLEAR_LINE = "\x1b[K"

_BLIP_COLOR = {"brend təhliki şübhəsi": "\x1b[31m", "infrastruktur şübhəsi": "\x1b[33m"}


def _tty():
    try:
        return sys.stdout.isatty()
    except Exception:
        return False


def _cols():
    try:
        return shutil.get_terminal_size().columns
    except Exception:
        return 80


def _hide_cursor():
    sys.stdout.write(_HIDE)
    sys.stdout.flush()


def _show_cursor():
    try:
        sys.stdout.write(_SHOW)
        sys.stdout.flush()
    except Exception:
        pass


atexit.register(_show_cursor)


class RadarState:
    def __init__(self):
        self.lock = threading.Lock()
        self.stage = "idle"
        self.current = ""
        self.scanned = 0
        self.brand_risk = 0
        self.infra_risk = 0
        self.errors = 0
        self.total = 0
        self.start_time = time.time()
        self.blips = []  # (x,y,color)
        self.sweep = 0.0
        self.done = False


def _pos(domain, radius=9):
    h = int(hashlib.md5(domain.encode()).hexdigest(), 16)
    r = 2 + (h % (radius - 1))
    ang = (h % 360) * math.pi / 180.0
    x = int(round(r * math.cos(ang)))
    y = int(round(r * math.sin(ang)))
    return x, y


def render_frame(state, width=32):
    with state.lock:
        stage = state.stage
        current = state.current
        scanned = state.scanned
        brand = state.brand_risk
        infra = state.infra_risk
        errors = state.errors
        total = state.total
        blips = list(state.blips)
        sweep = state.sweep
        elapsed = time.time() - state.start_time

    # grid dimensions
    rows = 11
    cols = 31
    cx, cy = cols // 2, rows // 2
    grid = [[" " for _ in range(cols)] for _ in range(rows)]
    color_grid = [["" for _ in range(cols)] for _ in range(rows)]

    # rings
    for y in range(rows):
        for x in range(cols):
            dx = x - cx
            dy = (y - cy) * 2
            dist = math.sqrt(dx * dx + dy * dy)
            if abs(dist - 4) < 0.9 or abs(dist - 8) < 0.9:
                if grid[y][x] == " ":
                    grid[y][x] = "·"
            if y == cy or x == cx:
                if grid[y][x] == " ":
                    grid[y][x] = "·"

    # sweep trail
    for t in range(8):
        ang = sweep - t * 0.18
        for radius in range(1, 10):
            x = int(round(cx + radius * math.cos(ang)))
            y = int(round(cy + (radius * math.sin(ang)) / 2.0))
            if 0 <= x < cols and 0 <= y < rows:
                if t == 0:
                    grid[y][x] = "█"
                elif t < 3:
                    grid[y][x] = "▓"
                elif t < 6:
                    grid[y][x] = "▒"
                else:
                    grid[y][x] = "░"

    # blips
    for (bx, by, col) in blips:
        gx = cx + bx
        gy = cy + by // 2  # scale y roughly
        if 0 <= gx < cols and 0 <= gy < rows:
            grid[gy][gx] = "*"
            color_grid[gy][gx] = col

    lines = []
    GREEN = "\x1b[32m"
    RESET = "\x1b[0m"
    for y in range(rows):
        row = ""
        for x in range(cols):
            ch = grid[y][x]
            c = color_grid[y][x]
            if c:
                row += c + ch + RESET
            elif ch in "█▓▒░":
                row += GREEN + ch + RESET
            elif ch == "*":
                row += ch
            else:
                row += ch
        lines.append(row)

    # progress bar
    frac = 0.0 if total == 0 else min(1.0, scanned / max(1, total))
    bar_len = 24
    filled = int(bar_len * frac)
    bar = "█" * filled + "░" * (bar_len - filled)
    lines.append("")
    lines.append(f"Stage: {stage}")
    lines.append(f"[{GREEN}{bar}{RESET}] {int(frac*100)}%")
    lines.append(f"Scanned: {scanned} | brand-risk: {brand} | infra-risk: {infra} | errors: {errors}")
    lines.append(f"Current: {current[:40]}")
    lines.append(f"Elapsed: {elapsed:.1f}s")
    return lines


class RadarAnimation:
    def __init__(self, message="Scanning...", enabled=True):
        self.message = message
        self.enabled = bool(enabled)
        if _cols() < 60:
            self.enabled = False
        self._line_mode = self.enabled and (not _tty())
        self.state = RadarState()
        self._thread = None
        self._stop = threading.Event()
        self._first = True
        self._last_lines = 0

    def __enter__(self):
        if not self.enabled:
            return self
        self.state.start_time = time.time()
        if self._line_mode:
            self._thread = threading.Thread(target=self._run_lines, daemon=True)
            self._thread.start()
            return self
        _hide_cursor()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()
        return self

    def __exit__(self, *exc):
        if not self.enabled:
            return False
        self.stop()
        if not self._line_mode:
            _show_cursor()
        return False

    def _run_lines(self):
        syms = ["◜", "◝", "◞", "◟"]
        i = 0
        green = "[32m" if _color_ok() else ""
        reset = "[0m" if green else ""
        while not self._stop.is_set():
            with self.state.lock:
                stage = self.state.stage
                scanned = self.state.scanned
                total = self.state.total
                elapsed = time.time() - self.state.start_time
            frac = 0.0 if total == 0 else min(1.0, scanned / max(1, total))
            sym = syms[i % len(syms)]
            line = f"{green}{sym} {self.message} | {stage} | {int(frac*100)}% | {scanned}/{total} | {elapsed:.1f}s{reset}"
            print(line, flush=True)
            i += 1
            # wait ~2s in small increments to allow stop
            for _ in range(20):
                if self._stop.is_set():
                    break
                time.sleep(0.1)
        print(f"{green}scan complete{reset}", flush=True)

    def _run(self):
        while not self._stop.is_set():
            with self.state.lock:
                self.state.sweep += 0.25
            lines = render_frame(self.state)
            # draw
            if not self._first:
                # move up
                sys.stdout.write(f"\x1b[{self._last_lines}A")
            self._first = False
            out = ""
            for ln in lines:
                out += ln + _CLEAR_LINE + "\n"
            sys.stdout.write(out)
            sys.stdout.flush()
            self._last_lines = len(lines)
            time.sleep(1.0 / 12.0)
        # final "scan complete" frame
        self._stop_frame()

    def _stop_frame(self):
        try:
            sys.stdout.write(f"\x1b[{self._last_lines}A")
            done_lines = ["", "  Scan complete.  ", ""]
            out = ""
            for ln in done_lines:
                out += ln + _CLEAR_LINE + "\n"
            sys.stdout.write(out)
            sys.stdout.flush()
            time.sleep(0.5)
            # clear animation region
            total = self._last_lines + len(done_lines)
            sys.stdout.write(f"\x1b[{total}A")
            for _ in range(total):
                sys.stdout.write(_CLEAR_LINE + "\n")
            sys.stdout.write(f"\x1b[{total}A")
            sys.stdout.flush()
        except Exception:
            pass

    def stop(self):
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=1.0)
        if not self._line_mode:
            _show_cursor()

    def set_stage(self, stage):
        with self.state.lock:
            self.state.stage = stage

    def set_current(self, domain):
        with self.state.lock:
            self.state.current = domain

    def advance(self, error=False):
        with self.state.lock:
            self.state.scanned += 1
            if error:
                self.state.errors += 1

    def add_blip(self, domain, verdict):
        with self.state.lock:
            color = _BLIP_COLOR.get(verdict, "\x1b[33m")
            x, y = _pos(domain)
            self.state.blips.append((x, y, color))
            if verdict == "brend təhliki şübhəsi":
                self.state.brand_risk += 1
            elif verdict == "infrastruktur şübhəsi":
                self.state.infra_risk += 1

    def set_total(self, n):
        with self.state.lock:
            self.state.total = n


def with_radar(text="Scanning..."):
    def deco(fn):
        def wrapper(*a, **k):
            with RadarAnimation(text):
                return fn(*a, **k)
        return wrapper
    return deco


def _color_ok():
    # best-effort: env or tty
    if os.getenv("NO_COLOR"):
        return False
    try:
        return sys.stdout.isatty()
    except Exception:
        return False
