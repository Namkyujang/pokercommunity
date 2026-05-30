"""Play against a persona yourself, in the terminal.

Run it in YOUR OWN terminal (it reads keyboard input):

    cd .../pokercommunity
    python -m arena.human --vs rule:calm          # vs the cold rule bot
    python -m arena.human --vs ollama:bluffer     # vs the local LLM bluffer
    python -m arena.human --vs rule:highroller --stack 500

You are seat 0. Stacks carry over between hands (a real match), and a running
commentary shows what your opponent does — including, for LLM opponents, the
reasoning behind each move.
"""

import argparse

from .cards import fmt
from .engine import Observation, Decision, HeadsUpTable, FOLD, CALL, RAISE
from .agents import make_persona, Agent
from .llm_agent import make_llm_persona
from .ollama_agent import make_ollama_persona
from . import art

LINE = "=" * 60


class HumanAgent(Agent):
    persona = "you"

    def decide(self, obs: Observation) -> Decision:
        current_bet = max(obs.street_bets)
        opp = 1 - obs.actor
        print("\n" + LINE)
        print(f" Hand #{obs.hand_id}   |   Street: {obs.street.upper()}"
              f"      Pot: {obs.current_pot}   To call: {obs.to_call}")
        print(f" Your stack: {obs.my_stack}    Opponent stack: {obs.stacks[opp]}")
        print(art.DIM + " Board:" + art.RESET)
        print(art.cards_row(obs.community))
        print(art.BOLD + " Your hand:" + art.RESET)
        print(art.cards_row(obs.hole))
        print("-" * 60)

        min_raise_to = current_bet + obs.big_blind
        call_label = "check" if obs.to_call == 0 else f"call {obs.to_call}"
        print(f" [f]old   [c]{call_label[1:]}   [r]aise (min total {min_raise_to})")

        while True:
            try:
                choice = input(" > ").strip().lower()
            except EOFError:
                return Decision(FOLD, 0, "human EOF")
            if choice in ("f", "fold"):
                return Decision(FOLD, 0, "human fold")
            if choice in ("c", "call", "check", ""):
                return Decision(CALL, 0, "human call/check")
            if choice in ("r", "raise") or choice.startswith("r"):
                rest = choice[1:].strip()
                amt = rest or input(f"   raise to (>= {min_raise_to}): ").strip()
                try:
                    return Decision(RAISE, int(amt), "human raise")
                except ValueError:
                    print("   ! enter a number")
                    continue
            print("   ! type f / c / r")


class ConsoleLogger:
    """Prints a live commentary instead of (or alongside) writing to disk."""

    def __init__(self, human_seat=0, opp_name=None, show_reasoning=True):
        self.human_seat = human_seat
        self.opp_name = opp_name           # display name for the non-human seat
        self.show_reasoning = show_reasoning

    def _who(self, record):
        return self.opp_name or record["persona"]

    def log_decision(self, record, obs):
        if record["actor"] == self.human_seat:
            return  # the human already saw their own prompt
        who = self._who(record)
        action = record["action"]
        if action == "raise":
            line = f"   >> {who} raises to {record.get('total_bet', record['amount'])}"
        elif action == "call":
            paid = record.get("amount", 0)
            line = f"   >> {who} checks" if paid == 0 else f"   >> {who} calls {paid}"
        else:
            line = f"   >> {who} folds"
        print(art.CYAN + line + art.RESET)
        reason = record.get("reasoning", "")
        if "]" in reason:  # strip the [tag] prefix
            reason = reason.split("]", 1)[1].strip()
        if self.show_reasoning and reason:
            print(art.DIM + f"      “{reason[:140]}”" + art.RESET)

    def log_result(self, result, stacks):
        print("-" * 60)
        opp = self.opp_name or "opponent"
        if result.reason == "fold":
            won = "You" if result.winner == self.human_seat else opp
            print(f"   Hand over (fold).  Pot ({result.pot}) goes to {won}.")
        else:
            from .cards import card_from_str
            sd = result.showdown
            print("   SHOWDOWN")
            print(art.cards_row([card_from_str(c) for c in sd["board"]]))
            for s in (0, 1):
                label = "You " if s == self.human_seat else opp
                print(f"   {label}: {' '.join(sd[s]['hole'])}  ->  {art.BOLD}{sd[s]['hand']}{art.RESET}")
            if result.winner is None:
                print("   Split pot.")
            else:
                won = "You win!" if result.winner == self.human_seat else f"{opp} wins."
                print(f"   {art.YELLOW}{won}{art.RESET}  (pot {result.pot})")
        print(f"   Stacks now ->  you: {art.GREEN}{stacks[0]}{art.RESET}   "
              f"{opp}: {art.MAGENTA}{stacks[1]}{art.RESET}")
        print(LINE)

    def close(self):
        pass


def build_opponent(spec: str):
    kind, _, persona = spec.partition(":")
    if kind == "rule":
        return make_persona(persona, n_samples=120)
    if kind == "ollama":
        return make_ollama_persona(persona)
    if kind == "llm":
        return make_llm_persona(persona)
    raise ValueError(f"bad opponent {spec!r}; use rule:/ollama:/llm: + bluffer/highroller/calm")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--vs", default="rule:calm",
                    help="opponent, e.g. rule:calm, ollama:bluffer, rule:highroller")
    ap.add_argument("--stack", type=int, default=1000)
    ap.add_argument("--seed", type=int, default=None)
    args = ap.parse_args()

    you = HumanAgent()
    opp = build_opponent(args.vs)
    logger = ConsoleLogger(human_seat=0)
    table = HeadsUpTable([you, opp], stacks=(args.stack, args.stack),
                         logger=logger, seed=args.seed)

    print(LINE)
    print(f" You vs {args.vs}   |   starting stacks: {args.stack} each")
    print(" Small/big blind: 10/20.  Ctrl-C to quit anytime.")
    print(LINE)

    while table.stacks[0] > 0 and table.stacks[1] > 0:
        try:
            table.play_hand()
        except KeyboardInterrupt:
            print("\n\n  Quitting. Final stacks -> "
                  f"you: {table.stacks[0]}, opponent: {table.stacks[1]}")
            break
        if hasattr(opp, "note_result"):
            opp.note_result(False)  # opponent reacts to losing (rough)
        try:
            cont = input("\n  Press Enter for next hand (q to quit): ").strip().lower()
        except EOFError:
            break
        if cont == "q":
            break

    if table.stacks[0] <= 0:
        print("\n  You're out of chips. The house wins. \U0001F480")
    elif table.stacks[1] <= 0:
        print("\n  You busted your opponent! \U0001F3C6")
    print(f"  Final -> you: {table.stacks[0]}, opponent: {table.stacks[1]}")


if __name__ == "__main__":
    main()
