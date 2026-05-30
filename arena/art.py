"""Tiny terminal graphics: ASCII playing cards, banners, speech boxes.

Pure text + a little ANSI colour. Red suits print red; face-down cards show a
patterned back. Cards render as a horizontal row by stacking each card's lines.
"""

import unicodedata

from .cards import RANK_STR, SUIT_SYMBOL


def disp_width(s: str) -> str:
    """Display width counting CJK/fullwidth glyphs as 2 columns."""
    return sum(2 if unicodedata.east_asian_width(c) in ("W", "F") else 1 for c in s)

RESET = "\033[0m"
RED = "\033[31m"
BOLD = "\033[1m"
DIM = "\033[2m"
CYAN = "\033[36m"
YELLOW = "\033[33m"
GREEN = "\033[32m"
MAGENTA = "\033[35m"

RED_SUITS = {"h", "d"}


def clear():
    print("\033[2J\033[3J\033[H", end="")


def _card_lines(card, color=True):
    r = RANK_STR[card.rank]
    s = SUIT_SYMBOL[card.suit]
    tl = f"{r:<2}"
    br = f"{r:>2}"
    lines = [
        "┌───────┐",
        f"│ {tl}    │",
        f"│   {s}   │",
        f"│    {br} │",
        "└───────┘",
    ]
    if color and card.suit in RED_SUITS:
        lines = [RED + ln + RESET for ln in lines]
    return lines


def _back_lines():
    return [
        "┌───────┐",
        "│░░░░░░░│",
        "│░░░░░░░│",
        "│░░░░░░░│",
        "└───────┘",
    ]


def cards_row(cards, color=True, hidden=False, indent="  ") -> str:
    if not cards:
        return indent + DIM + "(none yet)" + RESET
    arts = [_back_lines() if hidden else _card_lines(c, color) for c in cards]
    rows = []
    for i in range(5):
        rows.append(indent + "  ".join(a[i] for a in arts))
    return "\n".join(rows)


def title_banner() -> str:
    return (
        CYAN + BOLD +
        "   ╔══════════════════════════════════════════════╗\n"
        "   ║                                                ║\n"
        "   ║      ♠ ♥   P O K E R   C O M M U N I T Y   ♦ ♣ ║\n"
        "   ║                                                ║\n"
        "   ║          " + YELLOW + "～ the road to MR. JOKER ～" + CYAN + "            ║\n"
        "   ║                                                ║\n"
        "   ╚══════════════════════════════════════════════╝" + RESET
    )


JOKER_FACE = (
    MAGENTA +
    "             .-\"\"\"\"\"\"\"-.\n"
    "           .'  _     _  '.\n"
    "          /   (o)   (o)   \\\n"
    "         |        <        |\n"
    "         |   '._.-'-._.'   |\n"
    "          \\   \\       /   /\n"
    "           '.  '-...-'  .'\n"
    "             '-._____.-'\n"
    "            <  MR. JOKER  >" + RESET
)


def speech(name: str, title: str, text: str, color=YELLOW) -> str:
    head = f"{name}" + (f"  ({title})" if title else "")
    lines = text.splitlines() or [""]
    quoted = [f'"{t}"' for t in lines]
    inner = max([disp_width(head) + 2] + [disp_width(q) for q in quoted])  # content width
    top = ("  ╭─ " + color + BOLD + head + RESET + " "
           + "─" * max(1, inner - 1 - disp_width(head)) + "╮")
    body = "\n".join(
        f"  │ {color}{q}{RESET}{' ' * (inner - disp_width(q))} │" for q in quoted
    )
    bot = "  ╰" + "─" * (inner + 2) + "╯"
    return f"{top}\n{body}\n{bot}"


def divider(ch="─", n=52):
    return DIM + ch * n + RESET
