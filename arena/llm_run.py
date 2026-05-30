"""Run a match where either seat can be a rule bot or an LLM persona.

Agents are named "<kind>:<persona>", e.g. "llm:bluffer" or "rule:calm". This is
how we put an LLM persona on trial against the rule-bot baseline.

Usage:
    python -m arena.llm_run --p0 llm:bluffer --p1 rule:calm --hands 10
    python -m arena.llm_run --p0 llm:bluffer --p1 llm:calm  --hands 8

Start SMALL — every decision is one API call (real money on your key). Haiku is
cheap, but 10 hands is already ~50-100 calls. Scale up only once it looks right.
"""

import argparse

from .agents import make_persona
from .llm_agent import make_llm_persona
from .ollama_agent import make_ollama_persona
from .engine import HeadsUpTable
from .trajectory import TrajectoryLogger
from .analyze import analyze


def build_agent(spec: str, seed: int):
    kind, _, persona = spec.partition(":")
    if kind == "rule":
        return make_persona(persona, seed=seed, n_samples=80)
    if kind == "llm":
        return make_llm_persona(persona)
    if kind == "ollama":
        return make_ollama_persona(persona)
    raise ValueError(f"bad agent spec {spec!r}; use rule:<name>, ollama:<name>, or llm:<name>")


def run_match(p0: str, p1: str, hands: int, seed: int, out: str):
    a0 = build_agent(p0, seed)
    a1 = build_agent(p1, seed + 1)
    logger = TrajectoryLogger(out)
    table = HeadsUpTable([a0, a1], stacks=(1000, 1000), logger=logger, seed=seed,
                         log_equity=True)  # ground-truth strength for every decision

    wins = [0, 0, 0]
    for h in range(hands):
        table.stacks = [1000, 1000]
        r = table.play_hand()
        if r.winner == 0:
            wins[0] += 1
        elif r.winner == 1:
            wins[1] += 1
        else:
            wins[2] += 1
        for idx, ag in enumerate((a0, a1)):
            if hasattr(ag, "note_result"):
                ag.note_result(r.winner == idx)
        print(f"  hand {h+1}/{hands} done (winner: "
              f"{'p0' if r.winner==0 else 'p1' if r.winner==1 else 'split'})")
    logger.close()

    print(f"\nMatch: {p0} (p0) vs {p1} (p1), {hands} hands")
    print(f"  p0 {p0}: {wins[0]} | p1 {p1}: {wins[1]} | split: {wins[2]}")
    print(f"  trajectory -> {out}\n")
    print("=== behavioural signature ===")
    analyze(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--p0", default="llm:bluffer")
    ap.add_argument("--p1", default="rule:calm")
    ap.add_argument("--hands", type=int, default=10)
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--out", default=None)
    args = ap.parse_args()
    out = args.out or f"llm_{args.p0}_vs_{args.p1}.jsonl".replace(":", "-")
    run_match(args.p0, args.p1, args.hands, args.seed, out)


if __name__ == "__main__":
    main()
