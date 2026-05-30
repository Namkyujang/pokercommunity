"""Round-robin every persona against every other, and report two things:

  1. Behavioural signature  — how each persona acts (raise/fold/bluff/size)
  2. Profitability          — net chips won, in BB/100 (the standard poker unit)

Why both: the first experiment showed the bluffer *won more hands* by stealing
blinds, but hand-frequency is not the same as money. Tracking net chips turns
"who is busier" into "who is actually better" — and the gap between the two is
itself a finding. Stacks reset each hand so the comparison stays clean.

Usage:
    python -m arena.tournament --hands 200 --seed 1
"""

import argparse
import itertools
import re

from .agents import make_persona, PERSONAS
from .engine import HeadsUpTable

BIG_BLIND = 20


def _eq(reasoning: str):
    m = re.search(r"eq=([0-9.]+)", reasoning or "")
    return float(m.group(1)) if m else None


class StatsCollector:
    """A logger that accumulates per-persona stats in memory instead of to disk."""

    def __init__(self):
        self.dec: dict[str, dict] = {}
        self.profit: dict[str, list] = {}   # persona -> [net_chips, hands]
        self._cur: dict[int, str] = {}

    def start_match(self, p0: str, p1: str):
        self._cur = {0: p0, 1: p1}

    def _bucket(self, persona: str) -> dict:
        return self.dec.setdefault(persona, {
            "n": 0, "raise": 0, "fold": 0, "call": 0, "bluff": 0, "raise_amt": 0,
        })

    def log_decision(self, record: dict, obs):
        b = self._bucket(record["persona"])
        b["n"] += 1
        b[record["action"]] += 1
        if record["action"] == "raise":
            b["raise_amt"] += record["amount"]
            eq = _eq(record["reasoning"])
            if eq is not None and eq < 0.45:
                b["bluff"] += 1

    def log_result(self, result, stacks):
        for idx, persona in self._cur.items():
            p = self.profit.setdefault(persona, [0, 0])
            p[0] += stacks[idx] - 1000  # net chips this hand (stacks reset to 1000)
            p[1] += 1

    def close(self):
        pass


def run_tournament(hands: int, seed: int, n_samples: int):
    collector = StatsCollector()
    for i, (p0, p1) in enumerate(itertools.combinations(PERSONAS, 2)):
        a0 = make_persona(p0, seed=seed + i, n_samples=n_samples)
        a1 = make_persona(p1, seed=seed + 100 + i, n_samples=n_samples)
        collector.start_match(p0, p1)
        table = HeadsUpTable([a0, a1], logger=collector, seed=seed + 1000 + i)
        hw = {p0: 0, p1: 0}
        for _ in range(hands):
            table.stacks = [1000, 1000]
            r = table.play_hand()
            if r.winner == 0:
                hw[p0] += 1
            elif r.winner == 1:
                hw[p1] += 1
            for idx, ag in enumerate((a0, a1)):
                if hasattr(ag, "note_result"):
                    ag.note_result(r.winner == idx)
        print(f"  {p0} vs {p1}: {hw[p0]}-{hw[p1]} hands")

    print("\n=== Behavioural signature (all matches pooled) ===")
    header = f"{'persona':>12} {'decisions':>9} {'raise%':>7} {'fold%':>6} {'bluff%':>7} {'call%':>6} {'avgRaiseBB':>11}"
    print(header)
    print("-" * len(header))
    for persona, b in sorted(collector.dec.items()):
        n = b["n"]
        avg = b["raise_amt"] / b["raise"] / BIG_BLIND if b["raise"] else 0.0
        print(f"{persona:>12} {n:>9} "
              f"{100*b['raise']/n:>6.1f}% {100*b['fold']/n:>5.1f}% "
              f"{100*b['bluff']/n:>6.1f}% {100*b['call']/n:>5.1f}% {avg:>11.1f}")

    print("\n=== Profitability (net chips won) ===")
    print(f"{'persona':>12} {'hands':>6} {'netChips':>9} {'BB/100':>8}")
    print("-" * 38)
    for persona, (net, h) in sorted(collector.profit.items(),
                                    key=lambda kv: -kv[1][0]):
        bb100 = net / BIG_BLIND / h * 100 if h else 0.0
        print(f"{persona:>12} {h:>6} {net:>9} {bb100:>+8.1f}")
    print("\nBB/100 = big blinds won per 100 hands (standard poker win-rate unit).")
    print("Positive = profitable. Note how this can disagree with hands-won.")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--hands", type=int, default=200)
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--samples", type=int, default=100)
    args = ap.parse_args()
    print(f"Round-robin: {PERSONAS}, {args.hands} hands each pair\n")
    run_tournament(args.hands, args.seed, args.samples)


if __name__ == "__main__":
    main()
