"""Turn a trajectory log into the first finding.

Per persona, computes a few classic poker behavioural stats — the kind of
"behavioural signature" we ultimately want to compare between rule bots and LLM
personas:

  hands        decisions made
  raise%       how often the persona raised
  fold%        how often it folded
  bluff%       raised while holding a weak hand (low equity) -> aggression w/o value
  call%        called
  avg_raise    mean raise size in big blinds

Usage:
    python -m arena.analyze trajectories_calm_vs_bluffer.jsonl
"""

import json
import sys
import re

BIG_BLIND = 20  # matches engine default; only used to express raise size in BB


WEAK = 0.40  # hand strength below which a raise counts as a "bluff"


def _equity(row: dict):
    # prefer the engine-logged ground-truth equity; fall back to a rule-bot tag
    if row.get("equity") is not None:
        return row["equity"]
    m = re.search(r"eq=([0-9.]+)", row.get("reasoning") or "")
    return float(m.group(1)) if m else None


def analyze(path: str):
    rows = []
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            obj = json.loads(line)
            if obj.get("type") == "decision":
                rows.append(obj)

    by_persona: dict[str, list[dict]] = {}
    for r in rows:
        by_persona.setdefault(r["persona"], []).append(r)

    header = f"{'persona':>12} {'hands':>6} {'raise%':>7} {'fold%':>6} {'bluff%':>7} {'call%':>6} {'avgRaiseBB':>11}"
    print(header)
    print("-" * len(header))
    for persona, rs in sorted(by_persona.items()):
        n = len(rs)
        raises = [r for r in rs if r["action"] == "raise"]
        folds = [r for r in rs if r["action"] == "fold"]
        calls = [r for r in rs if r["action"] == "call"]
        # a "bluff" = raised with a weak hand (low ground-truth equity)
        bluffs = [r for r in raises if (_equity(r) or 1.0) < WEAK]
        avg_raise_bb = (sum(r["amount"] for r in raises) / len(raises) / BIG_BLIND
                        if raises else 0.0)
        print(f"{persona:>12} {n:>6} "
              f"{100*len(raises)/n:>6.1f}% {100*len(folds)/n:>5.1f}% "
              f"{100*len(bluffs)/n:>6.1f}% {100*len(calls)/n:>5.1f}% "
              f"{avg_raise_bb:>11.1f}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("usage: python -m arena.analyze <trajectory.jsonl>")
        sys.exit(1)
    analyze(sys.argv[1])
