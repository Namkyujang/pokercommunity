"""Hand strength via Monte Carlo equity.

Gives every agent (rule bots now, LLM personas later) a shared, honest notion of
"how good is my hand right now" — the ground truth against which we can later ask
the research question: does a persona bet according to strength, or against it?
"""

import random

from .cards import make_deck
from .evaluator import evaluate


def equity(hole, community, n_samples: int = 100, rng: random.Random | None = None) -> float:
    """Probability of winning (ties count as half) vs one random opponent,
    rolling out the remaining community cards by Monte Carlo."""
    rng = rng or random
    known = set(hole) | set(community)
    deck = [c for c in make_deck() if c not in known]

    need_community = 5 - len(community)
    wins = 0.0
    for _ in range(n_samples):
        sample = rng.sample(deck, 2 + need_community)
        opp_hole = sample[:2]
        board = list(community) + sample[2:]
        my = evaluate(list(hole) + board)
        op = evaluate(opp_hole + board)
        if my > op:
            wins += 1.0
        elif my == op:
            wins += 0.5
    return wins / n_samples
