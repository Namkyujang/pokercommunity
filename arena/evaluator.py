"""Poker hand evaluation — the wall the original project hit.

The trick: represent each hand as a comparable tuple
    (category, tiebreak1, tiebreak2, ...)
where higher category = stronger hand, and Python's native tuple comparison
handles all the kicker logic for free. To find the best 5 of 7 cards, just
score every 5-card combination and take the max.
"""

import itertools
from collections import Counter

from .cards import Card

# Hand categories, high = strong.
HIGH_CARD = 0
ONE_PAIR = 1
TWO_PAIR = 2
TRIPS = 3
STRAIGHT = 4
FLUSH = 5
FULL_HOUSE = 6
QUADS = 7
STRAIGHT_FLUSH = 8

CATEGORY_NAME = {
    HIGH_CARD: "High Card",
    ONE_PAIR: "One Pair",
    TWO_PAIR: "Two Pair",
    TRIPS: "Three of a Kind",
    STRAIGHT: "Straight",
    FLUSH: "Flush",
    FULL_HOUSE: "Full House",
    QUADS: "Four of a Kind",
    STRAIGHT_FLUSH: "Straight Flush",
}


def _straight_high(ranks: set[int]) -> int | None:
    """Highest card of a 5-long straight within `ranks`, or None.
    Handles the wheel (A-2-3-4-5) by treating Ace as 1 as well."""
    vals = set(ranks)
    if 14 in vals:
        vals = vals | {1}
    for high in range(14, 4, -1):
        if all(v in vals for v in range(high, high - 5, -1)):
            return high
    return None


def eval5(cards) -> tuple:
    """Score exactly 5 cards as a comparable tuple."""
    ranks = [c.rank for c in cards]
    suits = [c.suit for c in cards]
    counts = Counter(ranks)
    count_vals = sorted(counts.values(), reverse=True)
    is_flush = len(set(suits)) == 1
    st_high = _straight_high(set(ranks))

    # ranks sorted by (multiplicity, rank) — natural kicker ordering
    by_count = sorted(ranks, key=lambda r: (counts[r], r), reverse=True)

    if is_flush and st_high:
        return (STRAIGHT_FLUSH, st_high)
    if count_vals[0] == 4:
        quad = max(r for r in counts if counts[r] == 4)
        kicker = max(r for r in counts if r != quad)
        return (QUADS, quad, kicker)
    if count_vals[0] == 3 and count_vals[1] >= 2:
        trip = max(r for r in counts if counts[r] == 3)
        pair = max(r for r in counts if counts[r] >= 2 and r != trip)
        return (FULL_HOUSE, trip, pair)
    if is_flush:
        return (FLUSH, *sorted(ranks, reverse=True))
    if st_high:
        return (STRAIGHT, st_high)
    if count_vals[0] == 3:
        trip = max(r for r in counts if counts[r] == 3)
        kickers = sorted((r for r in ranks if r != trip), reverse=True)
        return (TRIPS, trip, *kickers)
    if count_vals[0] == 2 and count_vals[1] == 2:
        pairs = sorted((r for r in counts if counts[r] == 2), reverse=True)
        kicker = max(r for r in counts if counts[r] == 1)
        return (TWO_PAIR, pairs[0], pairs[1], kicker)
    if count_vals[0] == 2:
        pair = max(r for r in counts if counts[r] == 2)
        kickers = sorted((r for r in ranks if r != pair), reverse=True)
        return (ONE_PAIR, pair, *kickers)
    return (HIGH_CARD, *sorted(ranks, reverse=True))


def evaluate(cards) -> tuple:
    """Best 5-card score from 5, 6, or 7 cards."""
    if len(cards) == 5:
        return eval5(cards)
    return max(eval5(combo) for combo in itertools.combinations(cards, 5))


def hand_name(score: tuple) -> str:
    return CATEGORY_NAME[score[0]]
