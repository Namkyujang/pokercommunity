"""Agents — everything that can sit at the table behind the same `decide()` seam.

The point of the project lives here. Today these are *rule-based* personas: cheap
stand-ins so the whole arena runs with no API. Each one is the SAME hand-strength
signal filtered through a different attitude — which is exactly the variable we
want to study. Tomorrow, `LLMPersonaAgent` drops in with an identical interface,
and the rule bots become the baseline we compare the LLM against.
"""

import random

from .engine import Observation, Decision, FOLD, CALL, RAISE
from .equity import equity


class Agent:
    persona = "agent"

    def decide(self, obs: Observation) -> Decision:
        raise NotImplementedError


class RandomAgent(Agent):
    persona = "random"

    def __init__(self, seed=None):
        self.rng = random.Random(seed)

    def decide(self, obs: Observation) -> Decision:
        roll = self.rng.random()
        if obs.to_call > 0 and roll < 0.2:
            return Decision(FOLD, reasoning="random fold")
        if roll < 0.7:
            return Decision(CALL, reasoning="random call")
        bump = max(obs.big_blind, obs.current_pot // 2)
        return Decision(RAISE, max(obs.street_bets) + bump, "random raise")


class PersonaRuleAgent(Agent):
    """A hand-strength policy bent by a persona's parameters.

    Knobs (this is the persona, made explicit):
      value_threshold  : equity above which the hand is worth raising for value
      call_threshold   : equity above which a bet is worth calling
      bluff_freq       : chance of raising a weak hand anyway
      aggression       : raise size as a fraction of the pot
      tilt             : extra looseness after losing the previous hand
    """

    def __init__(self, persona, value_threshold, call_threshold, bluff_freq,
                 aggression, tilt=0.0, n_samples=100, seed=None):
        self.persona = persona
        self.value_threshold = value_threshold
        self.call_threshold = call_threshold
        self.bluff_freq = bluff_freq
        self.aggression = aggression
        self.tilt = tilt
        self.n_samples = n_samples
        self.rng = random.Random(seed)
        self._tilt_now = 0.0

    def note_result(self, won: bool):
        # losing nudges a tilt-prone persona looser for the next hand
        self._tilt_now = 0.0 if won else self.tilt

    def decide(self, obs: Observation) -> Decision:
        eq = equity(obs.hole, obs.community, self.n_samples, self.rng)
        call_t = max(0.0, self.call_threshold - self._tilt_now)
        value_t = max(0.0, self.value_threshold - self._tilt_now)

        raise_to = max(obs.street_bets) + max(
            obs.big_blind, int(obs.current_pot * self.aggression)
        )

        # Strong hand -> raise for value.
        if eq >= value_t:
            return Decision(RAISE, raise_to,
                            f"value raise (eq={eq:.2f} >= {value_t:.2f})")

        # Weak hand -> occasionally bluff-raise.
        if self.rng.random() < self.bluff_freq:
            return Decision(RAISE, raise_to,
                            f"bluff raise (eq={eq:.2f}, bluff_freq={self.bluff_freq})")

        # Otherwise: call if cheap/decent enough, else fold (or check for free).
        if obs.to_call == 0:
            return Decision(CALL, reasoning=f"check (eq={eq:.2f})")
        pot_odds = obs.to_call / max(1, obs.current_pot + obs.to_call)
        if eq >= call_t and eq >= pot_odds:
            return Decision(CALL, reasoning=f"call (eq={eq:.2f} >= {call_t:.2f})")
        return Decision(FOLD, reasoning=f"fold (eq={eq:.2f} < {call_t:.2f})")


# --- the three NPCs from the original game, reborn as measurable policies ----

def make_persona(name: str, seed=None, n_samples=100) -> PersonaRuleAgent:
    presets = {
        # The bluffer: raises constantly, calls light, hard to put on a hand.
        "bluffer": dict(value_threshold=0.45, call_threshold=0.35,
                        bluff_freq=0.45, aggression=0.8, tilt=0.05),
        # High-risk / high-reward: big bets, swings hard, tilts when it loses.
        "highroller": dict(value_threshold=0.50, call_threshold=0.40,
                           bluff_freq=0.20, aggression=1.2, tilt=0.10),
        # Tight, value-driven, almost no tilt — cold and patient.
        "calm": dict(value_threshold=0.62, call_threshold=0.52,
                     bluff_freq=0.05, aggression=0.5, tilt=0.0),
        # The final boss: ruthless value bets laced with sudden bluffs, ice cold.
        "joker": dict(value_threshold=0.55, call_threshold=0.46,
                      bluff_freq=0.33, aggression=1.0, tilt=0.0),
    }
    if name not in presets:
        raise KeyError(f"unknown persona {name!r}; choose from {list(presets)}")
    return PersonaRuleAgent(name, seed=seed, n_samples=n_samples, **presets[name])


PERSONAS = ["bluffer", "highroller", "calm"]
