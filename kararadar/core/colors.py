"""Color helpers for KaraRadar console output."""
try:
    from colorama import init, Fore, Style
    init(autoreset=True)
except Exception:  # pragma: no cover
    class Fore:
        GREEN = RED = YELLOW = CYAN = WHITE = MAGENTA = RESET = ""
    class Style:
        BRIGHT = DIM = RESET_ALL = ""

def ok(msg): return f"{Fore.GREEN}[+]{Style.RESET_ALL} {msg}"
def danger(msg): return f"{Fore.RED}[!]{Style.RESET_ALL} {msg}"
def info(msg): return f"{Fore.YELLOW}[i]{Style.RESET_ALL} {msg}"
def header(msg): return f"{Fore.CYAN}{Style.BRIGHT}{msg}{Style.RESET_ALL}"
def warn(msg): return f"{Fore.MAGENTA}[w]{Style.RESET_ALL} {msg}"

def card(text, color=Fore.CYAN):
    width = 78
    lines = text.splitlines()
    out = [f"{color}+{'-'*(width-2)}+{Style.RESET_ALL}"]
    for line in lines:
        pad = width - 2 - len(line)
        if pad < 0:
            pad = 0
            line = line[:width-2]
        out.append(f"{color}|{Style.RESET_ALL} {line}{' '* (pad-1)}{color}|{Style.RESET_ALL}")
    out.append(f"{color}+{'-'*(width-2)}+{Style.RESET_ALL}")
    return "\n".join(out)

VERDICT_COLOR = {
    "brend təhliki şübhəsi": Fore.RED,
    "infrastruktur şübhəsi": Fore.YELLOW,
    "neytral": Fore.GREEN,
}