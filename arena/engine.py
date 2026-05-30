"""Heads-up (1v1) no-limit Texas Hold'em engine.

The engine's job is to produce an `Observation` for whoever is to act, accept a
`Decision` back, enforce the rules, and — crucially for the research goal — hand
every decision to a logger. Agents never see each other; they only see
Observations. That clean seam is what lets a human, a rule bot, or an LLM persona
all plug into the exact same game.
"""

import random
from dataclasses import dataclass, field

from .cards import Card, make_deck, fmt
from .evaluator import evaluate, hand_name

FOLD = "fold"
CALL = "call"  # also covers "check" when there is nothing to call
RAISE = "raise"


@dataclass
class Observation:
    hand_id: int
    street: str
    actor: int                # whose turn (0 or 1)
    hole: list[Card]          # this actor's two hole cards
    community: list[Card]     # shared cards revealed so far
    pot: int                  # chips already collected from prior streets
    street_bets: list[int]    # chips committed this street, indexed by player
    stacks: list[int]         # remaining chips, indexed by player
    big_blind: int
    history: list[dict]       # action history for this hand
    actor_persona: str = ""

    @property
    def to_call(self) -> int:
        return max(self.street_bets) - self.street_bets[self.actor]

    @property
    def current_pot(self) -> int:
        return self.pot + sum(self.street_bets)

    @property
    def my_stack(self) -> int:
        return self.stacks[self.actor]


@dataclass
class Decision:
    action: str               # FOLD / CALL / RAISE
    amount: int = 0           # for RAISE: total street bet to raise *to*
    reasoning: str = ""       # short tag (rule bot) or chain-of-thought (LLM)


@dataclass
class HandResult:
    hand_id: int
    winner: int | None
    pot: int
    reason: str               # "fold" or "showdown"
    showdown: dict = field(default_factory=dict)


class HeadsUpTable:
    def __init__(self, agents, stacks=(1000, 1000), sb=10, bb=20,
                 logger=None, seed=None):
        assert len(agents) == 2
        self.agents = list(agents)
        self.stacks = list(stacks)
        self.sb = sb
        self.bb = bb
        self.logger = logger
        self.rng = random.Random(seed)
        self.hand_id = 0
        self.button = 0  # heads-up: button posts small blind, acts first preflop

    # -- a single hand -------------------------------------------------------
    def play_hand(self) -> HandResult:
        self.hand_id += 1
        hid = self.hand_id
        deck = make_deck()
        self.rng.shuffle(deck)

        holes = [deck[0:2], deck[2:4]]
        community_full = deck[4:9]  # 3 flop + turn + river, revealed progressively

        street_bets = [0, 0]
        pot = 0
        folded = None
        history: list[dict] = []

        sb_player = self.button
        bb_player = 1 - self.button
        self._post(sb_player, self.sb, street_bets)
        self._post(bb_player, self.bb, street_bets)

        streets = [("preflop", 0), ("flop", 3), ("turn", 4), ("river", 5)]
        for street, ncom in streets:
            community = community_full[:ncom]
            first = self.button if street == "preflop" else 1 - self.button
            folded = self._betting_round(
                hid, street, holes, community, street_bets, pot, history, first
            )
            # collect this street's bets, returning any uncalled excess
            self._settle_street(street_bets)
            pot += sum(street_bets)
            street_bets[:] = [0, 0]
            if folded is not None:
                break
            if self.stacks[0] == 0 and self.stacks[1] == 0:
                continue  # both all-in: run out remaining streets, no betting

        # -- resolve -----------------------------------------------------------
        if folded is not None:
            winner = 1 - folded
            self.stacks[winner] += pot
            result = HandResult(hid, winner, pot, "fold")
        else:
            board = community_full
            s0 = evaluate(holes[0] + board)
            s1 = evaluate(holes[1] + board)
            if s0 > s1:
                winner = 0
            elif s1 > s0:
                winner = 1
            else:
                winner = None  # split
            if winner is None:
                self.stacks[0] += pot // 2
                self.stacks[1] += pot - pot // 2
            else:
                self.stacks[winner] += pot
            result = HandResult(hid, winner, pot, "showdown", showdown={
                0: {"hole": [str(c) for c in holes[0]], "hand": hand_name(s0)},
                1: {"hole": [str(c) for c in holes[1]], "hand": hand_name(s1)},
                "board": [str(c) for c in board],
            })

        if self.logger:
            self.logger.log_result(result, self.stacks)
        self.button = 1 - self.button  # alternate dealer
        return result

    # -- one betting round on one street ------------------------------------
    def _betting_round(self, hid, street, holes, community, street_bets, pot,
                       history, first) -> int | None:
        # only players who still have chips can act; all-in bets simply stand
        queue = [p for p in (first, 1 - first) if self.stacks[p] > 0]
        while queue:
            p = queue.pop(0)
            current_bet = max(street_bets)
            to_call = current_bet - street_bets[p]
            if to_call == 0 and self.stacks[p] == 0:
                continue

            persona = getattr(self.agents[p], "persona", "") or type(self.agents[p]).__name__
            obs = Observation(
                hand_id=hid, street=street, actor=p,
                hole=holes[p], community=list(community), pot=pot,
                street_bets=list(street_bets), stacks=list(self.stacks),
                big_blind=self.bb, history=list(history), actor_persona=persona,
            )
            decision = self.agents[p].decide(obs)
            decision = self._sanitize(decision, obs)

            record = {
                "hand_id": hid, "street": street, "actor": p, "persona": persona,
                "action": decision.action, "amount": 0,
                "to_call": to_call, "pot_before": obs.current_pot,
                "reasoning": decision.reasoning,
            }

            if decision.action == FOLD:
                record["amount"] = 0
                history.append(record)
                if self.logger:
                    self.logger.log_decision(record, obs)
                return p

            if decision.action == CALL:
                amt = min(to_call, self.stacks[p])
                self._commit(p, amt, street_bets)
                record["amount"] = amt
                record["total_bet"] = street_bets[p]

            elif decision.action == RAISE:
                raise_to = decision.amount
                amt = raise_to - street_bets[p]
                self._commit(p, amt, street_bets)
                record["amount"] = amt
                record["total_bet"] = street_bets[p]  # actual raise-to after commit
                other = 1 - p
                if self.stacks[other] > 0 and other not in queue:
                    queue.append(other)

            history.append(record)
            if self.logger:
                self.logger.log_decision(record, obs)
        return None

    # -- helpers -------------------------------------------------------------
    def _post(self, p, amount, street_bets):
        amt = min(amount, self.stacks[p])
        self.stacks[p] -= amt
        street_bets[p] += amt

    def _commit(self, p, amount, street_bets):
        amount = max(0, min(amount, self.stacks[p]))
        self.stacks[p] -= amount
        street_bets[p] += amount

    def _settle_street(self, street_bets):
        # if bets are unequal at round end, the short side is all-in; return the
        # uncalled excess to whoever over-committed
        diff = street_bets[0] - street_bets[1]
        if diff > 0:
            self.stacks[0] += diff
            street_bets[0] -= diff
        elif diff < 0:
            self.stacks[1] += -diff
            street_bets[1] -= -diff

    def _sanitize(self, decision: Decision, obs: Observation) -> Decision:
        """Make any agent output a legal action. Forgiving by design so that
        rule bots — and later, free-form LLM outputs — can't crash the table."""
        a = decision.action
        if a not in (FOLD, CALL, RAISE):
            a = CALL
        p = obs.actor
        to_call = obs.to_call
        stack = self.stacks[p]

        if a == FOLD:
            # never fold when you can check for free
            if to_call == 0:
                return Decision(CALL, 0, decision.reasoning + " [check, no cost]")
            return Decision(FOLD, 0, decision.reasoning)

        if a == CALL:
            return Decision(CALL, 0, decision.reasoning)

        # RAISE: clamp into a legal range
        current_bet = max(obs.street_bets)
        min_raise_to = current_bet + obs.big_blind
        max_raise_to = obs.street_bets[p] + stack  # all-in
        raise_to = decision.amount
        if raise_to < min_raise_to:
            raise_to = min(min_raise_to, max_raise_to)
        raise_to = min(raise_to, max_raise_to)
        if raise_to <= current_bet:  # cannot actually raise -> just call
            return Decision(CALL, 0, decision.reasoning + " [raise->call, no chips]")
        return Decision(RAISE, raise_to, decision.reasoning)
