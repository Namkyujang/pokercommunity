# Persona Poker Arena

A small research **testbed** (not a game) for studying how a *persona* shapes
decision-making under uncertainty. Hold the poker game fixed, vary the persona,
and log every decision **with its reasoning** — then measure what actually
changes.

This grew out of `pokercommunity`, a project I first attempted before university:
a terminal poker game whose NPCs were each supposed to have a distinct
personality (a bluffer, a high-risk gambler, a cold final boss). Back then I got
stuck on the poker engine itself and never reached the personas. This rebuild
finishes the engine and turns those NPCs into **measurable policies** — the first
step toward replacing them with LLM personas and asking whether a persona
*label* really changes how a model reasons and bets.

## What's here

| file | role |
|------|------|
| `cards.py` | cards / deck (ranks as ints 2–14 so evaluation is arithmetic) |
| `evaluator.py` | best-5-of-7 hand evaluation (the wall the original project hit) |
| `equity.py` | Monte-Carlo win probability — a shared "ground truth" hand strength |
| `engine.py` | heads-up no-limit Hold'em engine with a clean `decide()` seam |
| `agents.py` | rule-based personas: `bluffer`, `highroller`, `calm` (no API needed) |
| `trajectory.py` | JSONL logger — the research artifact (every decision + reasoning) |
| `run.py` | run one persona-vs-persona match |
| `tournament.py` | round-robin + behavioural signature + profit (BB/100) |
| `analyze.py` | per-persona behavioural stats from a trajectory log |

## Play it (story mode)

```bash
python -m arena.campaign     # climb the ladder of NPCs to MR. JOKER
```

A title screen, rules, and a choice of opponent backend (fast rule bots, or
talking local-LLM personas). Beat each of the original pokercommunity NPCs
(Marcus, Mr. Volovski, Pokerbot, Checkmate, Mr. Mafia) and face the final boss,
**Mr. Joker** — with dialogue and ASCII-card graphics in the terminal.

Or a single free-play duel against one persona:

```bash
python -m arena.human --vs rule:calm
python -m arena.human --vs ollama:bluffer
```

## Quick start (research)

```bash
# one match, writes a trajectory log
python -m arena.run --p0 calm --p1 bluffer --hands 200

# behavioural signature from that log
python -m arena.analyze trajectories_calm_vs_bluffer.jsonl

# full round-robin with profitability
python -m arena.tournament --hands 200
```

## First findings (rule-based personas)

- **Personas are behaviourally distinct** under an identical engine and hand
  signal: raise frequency 73% (bluffer) vs 26% (calm), bluff rate 17% vs 2%.
- **Frequency ≠ profit.** The bluffer wins the most *hands* (stealing blinds) but
  loses chips (−29 BB/100); the cold "calm" persona wins the fewest hands yet is
  the only profitable one (+93 BB/100). Aggression buys frequency; discipline
  buys money.

These rule bots are the **baseline**. Next step: drop in an `LLMPersonaAgent`
behind the same `decide()` interface and test whether telling an LLM "you are a
bluffer" reproduces this signature — or whether the persona changes the talk but
not the bet.
