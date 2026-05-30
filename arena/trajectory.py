"""Trajectory logging — the actual research artifact.

Every decision and every hand result is appended to a JSONL file. This is the
arena's answer to ARCTraj: not "who won the game" but a structured record of
*how each persona decided, and why*, that we can later mine for behavioural
signatures. Logging is a first-class citizen, not an afterthought.
"""

import json


class TrajectoryLogger:
    def __init__(self, path: str):
        self.path = path
        self._fh = open(path, "w", encoding="utf-8")

    def log_decision(self, record: dict, obs):
        row = {
            "type": "decision",
            "hand_id": record["hand_id"],
            "street": record["street"],
            "actor": record["actor"],
            "persona": record["persona"],
            "hole": [str(c) for c in obs.hole],
            "community": [str(c) for c in obs.community],
            "pot_before": record["pot_before"],
            "to_call": record["to_call"],
            "stack": obs.my_stack,
            "action": record["action"],
            "amount": record["amount"],
            "reasoning": record["reasoning"],
        }
        if "equity" in record:
            row["equity"] = record["equity"]
        self._fh.write(json.dumps(row, ensure_ascii=False) + "\n")

    def log_result(self, result, stacks):
        row = {
            "type": "result",
            "hand_id": result.hand_id,
            "winner": result.winner,
            "pot": result.pot,
            "reason": result.reason,
            "stacks": list(stacks),
            "showdown": result.showdown,
        }
        self._fh.write(json.dumps(row, ensure_ascii=False) + "\n")

    def close(self):
        self._fh.close()

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()
