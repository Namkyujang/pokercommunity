"""Cards and decks.

A card is just (rank, suit). rank is an int 2..14 (11=J,12=Q,13=K,14=A) so that
comparisons and straights are trivial arithmetic — this is exactly the design
choice that makes hand evaluation (the part the original project got stuck on)
straightforward.
"""

from dataclasses import dataclass

SUITS = "shdc"  # spades, hearts, diamonds, clubs
RANKS = list(range(2, 15))  # 2..14

RANK_STR = {11: "J", 12: "Q", 13: "K", 14: "A"}
for _r in range(2, 11):
    RANK_STR[_r] = str(_r)
RANK_FROM_STR = {v: k for k, v in RANK_STR.items()}
RANK_FROM_STR["T"] = 10  # accept 'T' as well as '10'

SUIT_SYMBOL = {"s": "♠", "h": "♥", "d": "♦", "c": "♣"}


@dataclass(frozen=True)
class Card:
    rank: int
    suit: str

    def __str__(self) -> str:
        return f"{RANK_STR[self.rank]}{self.suit}"

    def pretty(self) -> str:
        return f"{RANK_STR[self.rank]}{SUIT_SYMBOL[self.suit]}"


def make_deck() -> list[Card]:
    return [Card(r, s) for s in SUITS for r in RANKS]


def card_from_str(text: str) -> Card:
    """'As' -> Card(14,'s'), 'Td'/'10d' -> Card(10,'d')."""
    text = text.strip()
    suit = text[-1].lower()
    rank_part = text[:-1].upper()
    return Card(RANK_FROM_STR[rank_part], suit)


def fmt(cards) -> str:
    return " ".join(c.pretty() for c in cards)
