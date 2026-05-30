"""Ollama persona agent — the same experiment, run on a FREE local model.

Identical personas, identical rules, identical situation prompt as the
Anthropic-backed agent (we import them so the only thing that ever differs
between backends is the model). The model runs entirely on your laptop via the
Ollama server at localhost:11434 — zero API cost, fully offline.

We use Ollama's structured-output `format` (a JSON schema) so even a 7B model
returns a clean, parseable action every time.
"""

import json
import urllib.request

from .engine import Observation, Decision, FOLD, CALL, RAISE
from .cards import fmt
from .llm_agent import PERSONA_PROMPTS, RULES  # shared, identical across backends

OLLAMA_URL = "http://localhost:11434/api/chat"
DEFAULT_MODEL = "qwen2.5:7b"

ACTION_SCHEMA = {
    "type": "object",
    "properties": {
        "reasoning": {"type": "string"},
        "action": {"type": "string", "enum": ["fold", "call", "raise"]},
        "raise_to": {"type": "integer"},
    },
    "required": ["reasoning", "action"],
}


class OllamaPersonaAgent:
    def __init__(self, persona, model=DEFAULT_MODEL, temperature=0.7,
                 url=OLLAMA_URL, timeout=120):
        if persona not in PERSONA_PROMPTS:
            raise KeyError(f"unknown persona {persona!r}")
        self.persona = persona
        self.model = model
        self.temperature = temperature
        self.url = url
        self.timeout = timeout

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
            f"Decide your action, in character. Reply as JSON."
        )

    def decide(self, obs: Observation) -> Decision:
        payload = {
            "model": self.model,
            "stream": False,
            "format": ACTION_SCHEMA,
            "options": {"temperature": self.temperature},
            "messages": [
                {"role": "system",
                 "content": f"{PERSONA_PROMPTS[self.persona]}\n\n{RULES}"},
                {"role": "user", "content": self._situation(obs)},
            ],
        }
        try:
            req = urllib.request.Request(
                self.url, data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"},
            )
            with urllib.request.urlopen(req, timeout=self.timeout) as r:
                body = json.loads(r.read().decode("utf-8"))
            out = json.loads(body["message"]["content"])
            action = out.get("action", "call")
            reasoning = out.get("reasoning", "")
            raise_to = int(out.get("raise_to", 0) or 0)
            tag = f"[ollama:{self.persona}] {reasoning}"
            if action == "raise":
                return Decision(RAISE, raise_to, tag)
            if action == "fold":
                return Decision(FOLD, 0, tag)
            return Decision(CALL, 0, tag)
        except Exception as e:
            return Decision(CALL, 0, f"[ollama:{self.persona}] error -> check/call: {e}")


def make_ollama_persona(name: str, **kw) -> OllamaPersonaAgent:
    return OllamaPersonaAgent(name, **kw)
