"""Fixed-scenario probe — the controlled experiment.

A full game confounds persona with card luck: when two personas diverge, you
can't tell whether it's the persona or just a different hand. This probe removes
that confound. It builds ONE fixed battery of poker decision points (each with a
known Monte-Carlo equity) and feeds the *identical* battery to every persona. Any
difference in behaviour is then 100% attributable to the persona.

Headline metric: corr(equity, aggression). How tightly does a persona's
aggression track actual hand strength?
  - high  -> bets rationally, by strength (value-driven)
  - ~0    -> bets regardless of strength (pure persona / bluff-driven)

Also: raise rate, bluff rate (raise with weak hand), and pairwise action
disagreement between personas on identical spots.

Usage:
    python -m arena.probe --scenarios 200 --seed 1                 # rule bots
    python -m arena.probe --backend ollama --scenarios 40 --personas bluffer,calm
"""

import argparse
import json
import random

from .cards import make_deck
from .engine import Observation, FOLD, CALL, RAISE
from .equity import equity
from .agents import make_persona
from .ollama_agent import make_ollama_persona

WEAK = 0.40            # equity below which a raise is a "bluff"
AGGR = {FOLD: 0, CALL: 1, RAISE: 2}   # ordinal aggression of an action
NCOM = {"preflop": 0, "flop": 3, "turn": 4, "river": 5}


def make_scenarios(n: int, seed: int, eq_samples: int = 300):
    """A reproducible battery of (Observation, ground-truth-equity) decision points."""
    rng = random.Random(seed)
    scenarios = []
    for i in range(n):
        deck = make_deck()
        rng.shuffle(deck)
        hole = deck[0:2]
        street = rng.choice(["preflop", "flop", "turn", "river"])
        community = deck[2:2 + NCOM[street]]
        to_call = rng.choice([0, 20, 40, 80])
        pot = rng.choice([0, 40, 120, 200])
        obs = Observation(
            hand_id=i, street=street, actor=0,
            hole=hole, community=community, pot=pot,
            street_bets=[to_call, 0],     # opponent has bet `to_call`; we owe it
            stacks=[500, 500], big_blind=20, history=[],
        )
        eq_rng = random.Random(seed * 100000 + i)
        eq = equity(hole, community, eq_samples, eq_rng)
        scenarios.append((obs, eq))
    return scenarios


def pearson(xs, ys) -> float:
    n = len(xs)
    if n < 2:
        return 0.0
    mx, my = sum(xs) / n, sum(ys) / n
    cov = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    vx = sum((x - mx) ** 2 for x in xs)
    vy = sum((y - my) ** 2 for y in ys)
    return cov / (vx * vy) ** 0.5 if vx > 0 and vy > 0 else 0.0


def build_agent(backend: str, persona: str):
    return make_ollama_persona(persona) if backend == "ollama" \
        else make_persona(persona, n_samples=200)


def run_probe(personas, backend, n, seed):
    scenarios = make_scenarios(n, seed)
    eqs = [eq for _, eq in scenarios]
    actions_by_persona = {}    # persona -> list of action strings (aligned to scenarios)
    stats = {}

    for persona in personas:
        agent = build_agent(backend, persona)
        actions = []
        for i, (obs, eq) in enumerate(scenarios):
            d = agent.decide(obs)
            actions.append(d.action)
        actions_by_persona[persona] = actions

        aggr = [AGGR[a] for a in actions]
        raises = sum(1 for a in actions if a == RAISE)
        bluffs = sum(1 for a, eq in zip(actions, eqs) if a == RAISE and eq < WEAK)
        stats[persona] = {
            "n": n,
            "raise_pct": 100 * raises / n,
            "bluff_pct": 100 * bluffs / n,
            "eq_aggr_corr": pearson(eqs, aggr),
            "avg_aggr": sum(aggr) / n,
        }
        print(f"  {persona}: done ({raises} raises, {bluffs} bluffs)")

    return scenarios, actions_by_persona, stats


def report(personas, stats, actions_by_persona, n):
    print("\n=== Behaviour on identical scenarios ===")
    h = f"{'persona':>12} {'n':>5} {'raise%':>7} {'bluff%':>7} {'eq~aggr r':>10} {'avgAggr':>8}"
    print(h)
    print("-" * len(h))
    for p in personas:
        s = stats[p]
        print(f"{p:>12} {s['n']:>5} {s['raise_pct']:>6.1f}% {s['bluff_pct']:>6.1f}% "
              f"{s['eq_aggr_corr']:>+10.2f} {s['avg_aggr']:>8.2f}")
    print("\n  eq~aggr r = correlation between hand strength and aggression.")
    print("  High = bets by strength (rational). ~0 = bets regardless (persona-driven).")

    print("\n=== Pairwise action disagreement (same scenarios) ===")
    for i in range(len(personas)):
        for j in range(i + 1, len(personas)):
            a, b = personas[i], personas[j]
            diff = sum(1 for x, y in zip(actions_by_persona[a], actions_by_persona[b])
                       if x != y)
            print(f"  {a:>11} vs {b:<11}: {100*diff/n:>5.1f}% of spots differ")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--scenarios", type=int, default=200)
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--backend", choices=["rule", "ollama"], default="rule")
    ap.add_argument("--personas", default="bluffer,highroller,calm,joker")
    ap.add_argument("--out", default=None)
    args = ap.parse_args()
    personas = [p.strip() for p in args.personas.split(",") if p.strip()]

    print(f"Probe: {args.backend} {personas}, {args.scenarios} fixed scenarios "
          f"(seed {args.seed})\n")
    scenarios, actions, stats = run_probe(personas, args.backend, args.scenarios, args.seed)
    report(personas, stats, actions, args.scenarios)

    if args.out:
        with open(args.out, "w", encoding="utf-8") as fh:
            json.dump({"backend": args.backend, "seed": args.seed,
                       "scenarios": args.scenarios, "stats": stats}, fh,
                      ensure_ascii=False, indent=2)
        print(f"\n  stats -> {args.out}")


if __name__ == "__main__":
    main()
