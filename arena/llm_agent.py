"""LLM personas — the same `decide()` seam, now driven by a language model.

The experiment this enables: give the model ONLY the raw situation (its hole
cards, the board, pot, amount to call, stacks) plus a persona description, and
ask it to act. We deliberately withhold the Monte-Carlo equity that the rule bots
use, so the LLM must judge hand strength itself. Then we compare its behavioural
signature against the rule-bot baseline and ask the core question:

    does telling a model "you are a bluffer" actually change how it BETS,
    or only how it TALKS?

The model's own chain-of-thought is captured verbatim into the trajectory log —
that reasoning trace is the real research artifact.
"""

import os

import anthropic

from .engine import Observation, Decision, FOLD, CALL, RAISE
from .cards import fmt

DEFAULT_MODEL = "claude-haiku-4-5-20251001"  # cheap; good enough for this probe

# Persona descriptions are the ONLY thing that varies between agents. Everything
# else — the rules, the situation, the output format — is held fixed.
PERSONA_PROMPTS = {
    "bluffer": (
        "You are a relentless BLUFFER. You apply constant pressure and love to "
        "raise and re-raise, even with weak hands, to push opponents off pots. "
        "You rarely fold; you would rather represent strength than give up."
    ),
    "highroller": (
        "You are a HIGH-RISK, HIGH-REWARD gambler. You make big, bold bets and "
        "chase big pots. You swing hard and are happy to gamble when there is a "
        "chance at a large reward."
    ),
    "calm": (
        "You are the cold, disciplined FINAL BOSS. You play tight, patient, "
        "value-driven poker with almost no emotion. You fold weak hands without "
        "hesitation and commit chips mainly when you judge you are ahead."
    ),
}

# Force a structured action so free-form prose can never crash the table.
ACT_TOOL = {
    "name": "act",
    "description": "Submit your poker action for this decision.",
    "input_schema": {
        "type": "object",
        "properties": {
            "reasoning": {
                "type": "string",
                "description": "Brief reasoning, in character, for this action.",
            },
            "action": {
                "type": "string",
                "enum": ["fold", "call", "raise"],
                "description": "fold, call (also = check when nothing to call), or raise.",
            },
            "raise_to": {
                "type": "integer",
                "description": "If raising, the TOTAL chips you want your bet this "
                               "street to reach. Ignored for fold/call.",
            },
        },
        "required": ["reasoning", "action"],
    },
}

RULES = (
    "You are playing heads-up (1 vs 1) No-Limit Texas Hold'em.\n"
    "Standard hand rankings apply. You act on one decision at a time.\n"
    "- 'call' matches the amount to call; if the amount to call is 0 it is a free check.\n"
    "- 'raise' must set raise_to ABOVE the current bet; going all-in is allowed.\n"
    "- 'fold' surrenders the hand (never fold when you can check for free)."
)


class LLMPersonaAgent:
    def __init__(self, persona, client=None, model=DEFAULT_MODEL,
                 max_tokens=400):
        if persona not in PERSONA_PROMPTS:
            raise KeyError(f"unknown persona {persona!r}")
        self.persona = persona
        self.model = model
        self.max_tokens = max_tokens
        self.client = client or anthropic.Anthropic(
            api_key=os.environ["ANTHROPIC_API_KEY"]
        )

    def _system(self):
        # Cached: persona + rules are identical across every decision, so prompt
        # caching makes repeated calls much cheaper.
        return [{
            "type": "text",
            "text": f"{PERSONA_PROMPTS[self.persona]}\n\n{RULES}",
            "cache_control": {"type": "ephemeral"},
        }]

    def _situation(self, obs: Observation) -> str:
        current_bet = max(obs.street_bets)
        return (
            f"Street: {obs.street}\n"
            f"Your hole cards: {fmt(obs.hole)}\n"
            f"Community cards: {fmt(obs.community) if obs.community else '(none yet)'}\n"
            f"Pot so far: {obs.current_pot}\n"
            f"Amount to call: {obs.to_call}\n"
            f"Your stack: {obs.my_stack}\n"
            f"Opponent stack: {obs.stacks[1 - obs.actor]}\n"
            f"Current bet to match this street: {current_bet}\n"
            f"Minimum legal raise_to: {current_bet + obs.big_blind}\n\n"
            f"Decide your action, in character."
        )

    def decide(self, obs: Observation) -> Decision:
        try:
            resp = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                system=self._system(),
                tools=[ACT_TOOL],
                tool_choice={"type": "tool", "name": "act"},
                messages=[{"role": "user", "content": self._situation(obs)}],
            )
            block = next(b for b in resp.content if b.type == "tool_use")
            inp = block.input
            action = inp.get("action", "call")
            reasoning = inp.get("reasoning", "")
            raise_to = int(inp.get("raise_to", 0) or 0)
            tag = f"[LLM:{self.persona}] {reasoning}"
            if action == "raise":
                return Decision(RAISE, raise_to, tag)
            if action == "fold":
                return Decision(FOLD, 0, tag)
            return Decision(CALL, 0, tag)
        except Exception as e:  # never let an API hiccup crash the table
            return Decision(CALL, 0, f"[LLM:{self.persona}] api error -> check/call: {e}")


def make_llm_persona(name: str, **kw) -> LLMPersonaAgent:
    return LLMPersonaAgent(name, **kw)
