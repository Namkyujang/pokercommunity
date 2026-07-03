"""전제 관문 파일럿: 중립 모델이 equity를 활성화에 (선형) 표상하나?

해상도 캘리브레이션 — 층마다:
  ① 연속 equity  (Ridge 회귀)      -> R2, Spearman
  ② 약/강 이분   (Logistic 분류)    -> accuracy

usage:
  python pilot_probe.py --model Qwen/Qwen2.5-0.5B-Instruct --n 60  --eq 300   # 스모크
  python pilot_probe.py --model Qwen/Qwen2.5-3B-Instruct  --n 300 --eq 1000  # 본 파일럿
"""
import os, sys, pickle, argparse
import numpy as np
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import Ridge, LogisticRegression
from sklearn.model_selection import cross_val_predict, cross_val_score, KFold
from sklearn.metrics import r2_score
from scipy.stats import spearmanr

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from arena.probe import make_scenarios
from arena.cards import fmt
from arena.llm_agent import RULES

NEUTRAL_SYS = "You are a poker player.\n\n" + RULES


def situation(obs):
    cur = max(obs.street_bets)
    return (
        f"Street: {obs.street}\n"
        f"Your hole cards: {fmt(obs.hole)}\n"
        f"Community cards: {fmt(obs.community) if obs.community else '(none yet)'}\n"
        f"Pot so far: {obs.current_pot}\n"
        f"Amount to call: {obs.to_call}\n"
        f"Your stack: {obs.my_stack}\n"
        f"Opponent stack: {obs.stacks[1 - obs.actor]}\n"
        f"Current bet to match this street: {cur}\n"
        f"Minimum legal raise_to: {cur + obs.big_blind}\n\n"
        f"Decide your action."
    )


def get_scenarios(n, seed, eq):
    cache = os.path.join(HERE, f"_scen_n{n}_s{seed}_eq{eq}.pkl")
    if os.path.exists(cache):
        return pickle.load(open(cache, "rb"))
    print(f"generating {n} scenarios (eq_samples={eq})...")
    scen = make_scenarios(n, seed=seed, eq_samples=eq)
    pickle.dump(scen, open(cache, "wb"))
    return scen


def extract(model_name, scenarios, device):
    safe = model_name.replace("/", "_")
    cache = os.path.join(HERE, f"_acts_{safe}_n{len(scenarios)}.npz")
    if os.path.exists(cache):
        d = np.load(cache)
        return d["acts"], d["eqs"]
    print(f"loading {model_name} on {device} ...")
    tok = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForCausalLM.from_pretrained(
        model_name, torch_dtype=torch.float16).to(device).eval()
    acts, eqs = [], []
    for i, (obs, eq) in enumerate(scenarios):
        msgs = [{"role": "system", "content": NEUTRAL_SYS},
                {"role": "user", "content": situation(obs)}]
        text = tok.apply_chat_template(msgs, add_generation_prompt=True, tokenize=False)
        ids = tok(text, return_tensors="pt").to(device)
        with torch.no_grad():
            out = model(**ids, output_hidden_states=True)
        last = torch.stack([h[0, -1, :] for h in out.hidden_states])  # [L+1, hid]
        acts.append(last.float().cpu().numpy())
        eqs.append(eq)
        if (i + 1) % 20 == 0:
            print(f"  extracted {i+1}/{len(scenarios)}")
    acts = np.array(acts)          # [N, L+1, hid]
    eqs = np.array(eqs)
    np.savez(cache, acts=acts, eqs=eqs)
    return acts, eqs


def probe(acts, eqs):
    N, L, H = acts.shape
    weak = (eqs < 0.5).astype(int)
    kf = KFold(5, shuffle=True, random_state=0)
    print(f"\nN={N}, layers={L}, hidden={H}, weak/strong split={weak.mean():.2f}")
    print(f"{'layer':>5} {'R2':>7} {'Spearman':>9} {'bin_acc':>8}")
    rows = []
    for l in range(L):
        X = acts[:, l, :]
        reg = make_pipeline(StandardScaler(), Ridge(alpha=100.0))
        pred = cross_val_predict(reg, X, eqs, cv=kf)
        r2 = r2_score(eqs, pred)
        rho = spearmanr(eqs, pred).statistic
        if 0 < weak.mean() < 1:
            clf = make_pipeline(StandardScaler(), LogisticRegression(max_iter=2000, C=0.1))
            acc = cross_val_score(clf, X, weak, cv=kf).mean()
        else:
            acc = float("nan")
        rows.append((l, r2, rho, acc))
        print(f"{l:>5} {r2:>7.3f} {rho:>9.3f} {acc:>8.3f}")
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="Qwen/Qwen2.5-0.5B-Instruct")
    ap.add_argument("--n", type=int, default=60)
    ap.add_argument("--eq", type=int, default=300)
    ap.add_argument("--seed", type=int, default=1)
    args = ap.parse_args()

    device = "mps" if torch.backends.mps.is_available() else "cpu"
    scen = get_scenarios(args.n, args.seed, args.eq)
    acts, eqs = extract(args.model, scen, device)
    rows = probe(acts, eqs)

    best = max(rows, key=lambda r: r[2])  # by Spearman
    print(f"\nBEST layer {best[0]}: R2={best[1]:.3f} Spearman={best[2]:.3f} bin_acc={best[3]:.3f}")

    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        ls = [r[0] for r in rows]
        fig, ax = plt.subplots(1, 2, figsize=(11, 4))
        ax[0].plot(ls, [r[2] for r in rows], "-o", ms=3)
        ax[0].axhline(0.5, ls="--", c="gray"); ax[0].set_title("Continuous equity: Spearman")
        ax[0].set_xlabel("layer"); ax[0].set_ylabel("Spearman")
        ax[1].plot(ls, [r[3] for r in rows], "-o", ms=3, c="tab:orange")
        ax[1].axhline(0.5, ls="--", c="gray")
        ax[1].set_title("Weak/Strong binary: accuracy"); ax[1].set_xlabel("layer"); ax[1].set_ylabel("acc")
        safe = args.model.replace("/", "_")
        out = os.path.join(HERE, f"_probe_{safe}_n{args.n}.png")
        plt.tight_layout(); plt.savefig(out, dpi=120)
        print(f"plot -> {out}")
    except Exception as e:
        print("plot skipped:", e)


if __name__ == "__main__":
    main()
