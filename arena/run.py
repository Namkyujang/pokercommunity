"""Run a match between two personas and log the trajectory.

Usage:
    python -m arena.run --p0 calm --p1 bluffer --hands 200 --seed 1

Stacks are reset each hand so that one persona busting out doesn't end the study
early — we want a clean, fixed-game comparison of behaviour, not a tournament.
"""

import argparse

from .agents import make_persona, PERSONAS
from .engine import HeadsUpTable
from .trajectory import TrajectoryLogger


def run_match(p0: str, p1: str, hands: int, seed: int, out: str, n_samples: int):
    a0 = make_persona(p0, seed=seed, n_samples=n_samples)
    a1 = make_persona(p1, seed=seed + 1, n_samples=n_samples)
    logger = TrajectoryLogger(out)
    table = HeadsUpTable([a0, a1], stacks=(1000, 1000), logger=logger, seed=seed)

    wins = [0, 0, 0]  # p0, p1, split
    for _ in range(hands):
        table.stacks = [1000, 1000]  # reset for an isolated, fair comparison
        result = table.play_hand()
        if result.winner == 0:
            wins[0] += 1
        elif result.winner == 1:
            wins[1] += 1
        else:
            wins[2] += 1
        # let tilt-prone personas react to the previous hand
        for idx, ag in enumerate((a0, a1)):
            if hasattr(ag, "note_result"):
                ag.note_result(result.winner == idx)
    logger.close()

    print(f"Match: {p0} (p0) vs {p1} (p1) over {hands} hands")
    print(f"  {p0:>10}: {wins[0]} wins")
    print(f"  {p1:>10}: {wins[1]} wins")
    print(f"  {'split':>10}: {wins[2]}")
    print(f"  trajectory -> {out}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--p0", default="calm", choices=PERSONAS)
    ap.add_argument("--p1", default="bluffer", choices=PERSONAS)
    ap.add_argument("--hands", type=int, default=200)
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--samples", type=int, default=100,
                    help="Monte Carlo samples for equity (lower = faster)")
    ap.add_argument("--out", default=None)
    args = ap.parse_args()
    out = args.out or f"trajectories_{args.p0}_vs_{args.p1}.jsonl"
    run_match(args.p0, args.p1, args.hands, args.seed, out, args.samples)


if __name__ == "__main__":
    main()
