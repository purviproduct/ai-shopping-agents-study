"""Does the paper's transcript fix (Theorem 6.6) survive LLM readers?

    python src/reader_sim.py > results/reader_sim_output.txt

One business, as in the paper's proof of Proposition 6.5 (Appendix C.3). Proposition 5.4 says each business is lost
independently and only through its own history, so one business is enough.

Deep market (search degree 2, with transcripts): an inspection checks a broad screen with pass probability pi1
(unknown: PI_HI or PI_LO, prior 1/2 each), then a niche screen with known pass probability S. The transcript says
which screen failed. A business is lost once no arriving consumer would inspect it, i.e. V*Q - P - c/pi_hat <= 0
(Proposition 5.1), where pi_hat = S * E[pi1] is the reader's estimate that an inspection passes. Q = 1 here, since
every screen is checked before booking.

Shallow market (the paper's market M, search degree 1): inspection checks only the broad screen. The niche screen
shows up after booking as known quality Q = S, so beliefs move only on broad-screen outcomes.

A reader turns the record into a belief about pi1. Passes and broad failures are read as plain outcomes (both
models scored "never replied" exactly like a plain failure). A niche failure ("no vegan menu") is read with
reason-use alpha, the experiment's forgive index:
    alpha = 0  counts it as a plain failure: the paper's deep market without transcripts
    alpha = 1  ignores it, as if the line were deleted: the experiment's Clean anchor
In between, its log-likelihood ratio is scaled by (1 - alpha). The paper's own transcript reader (Theorem 6.6) goes
one step further: a niche failure means the broad screen passed, so it counts as good news.

A market's readers are a population: each arriving consumer's agent is a fresh draw from it. Three ways to plug in
the experiment:
    average     every agent reads like the mean answer (one alpha)
    sampled     every agent is a fresh draw from the 30 answers (temperature 1, which is how the runs were made)
    temp 0      every agent gives the modal answer
"""

import math

import numpy as np

V, P = 1.0, 0.0
REPS, T = 20_000, 500

# The 30 "doesn't apply" answers per model and format, from experiments/output/*-analysis_results.xlsx (2026-11-02).
PLAIN = 67.0
GPT5MINI = {
    "number first": {"clean": 92.4, "answers": [67] * 23 + [80, 80, 83, 83, 85, 90, 100]},
    "reason first": {"clean": 91.4, "answers": [67] * 11 + [80, 83, 83, 83, 85, 85, 85, 85, 85, 90, 90, 90, 90,
                                                            90, 90, 100, 100, 100, 100]},
}
# gpt-5.6-luna answered 95-100 on all 30 and wrote that the failures came from a need the client lacks. Its Clean
# anchor is unusable (it rated four passes at 54), so it is entered as a full reader.
LUNA_ALPHA = 1.0


def alpha_of(answer, clean):
    return min(max((answer - PLAIN) / (clean - PLAIN), 0.0), 1.0)


def population(alphas):
    """[(alpha, share)] from a list of per-answer alphas."""
    values, counts = np.unique(np.round(alphas, 3), return_counts=True)
    return list(zip(values.tolist(), (counts / counts.sum()).tolist()))


def llr_table(pi_hi, pi_lo, s, alpha=None, paper=False, shallow=False, bayes_broad=False):
    """Log-likelihood-ratio increments (hi vs lo type) for outcomes: 0 pass, 1 broad failure, 2 niche failure.
    bayes_broad reads broad failures as the paper's reader does, instead of as plain failures."""
    broad = math.log((1 - pi_hi) / (1 - pi_lo))
    if shallow:
        return [math.log(pi_hi / pi_lo), broad, 0.0]
    if paper:
        return [math.log(pi_hi / pi_lo), broad, math.log(pi_hi / pi_lo)]
    plain_fail = math.log((1 - pi_hi * s) / (1 - pi_lo * s))
    return [math.log(pi_hi / pi_lo), broad if bayes_broad else plain_fail, (1 - alpha) * plain_fail]


def simulate(readers, pi_hi, pi_lo, s, c, good=True, shallow=False, reps=REPS, rounds=T, seed=0):
    """readers: [(llr_table, share)]. Returns (P(lost), mean consumers who skipped the business while it was live)."""
    rng = np.random.default_rng(seed)
    inc = np.array([r for r, _ in readers])                 # types x 3
    shares = np.array([w for _, w in readers])
    pi1 = pi_hi if good else pi_lo
    L = np.zeros((len(readers), reps))                      # each type's log-odds that pi1 = pi_hi
    skipped = np.zeros(reps)
    cols = np.arange(reps)

    def willing():
        p_hi = 1 / (1 + np.exp(-L))
        e_pi1 = p_hi * pi_hi + (1 - p_hi) * pi_lo
        value, pi_hat = (V * s - P, e_pi1) if shallow else (V - P, s * e_pi1)
        return value - c / pi_hat > 0

    for t in range(rounds):
        w = willing()
        if not w.any():
            break
        kind = rng.choice(len(readers), size=reps, p=shares)
        inspect = w[kind, cols]
        broad_ok = rng.random(reps) < pi1
        if shallow:
            outcome = np.where(broad_ok, 0, 1)
        else:
            outcome = np.where(~broad_ok, 1, np.where(rng.random(reps) < s, 0, 2))
        L += inspect * inc[:, outcome]
        skipped += ~inspect & w.any(axis=0)                 # live business, but this consumer passed it over
    lost = ~willing().any(axis=0)
    return lost.mean(), skipped.mean()


def needed_niche_failures(alpha, pi_hi, pi_lo, s, c):
    """In the paper's example, a good business is lost once n niche failures in a row drag pi_hat down to c."""
    p_star = (c / s - pi_lo) / (pi_hi - pi_lo)              # P(good) at which pi_hat = c
    tau = math.log(p_star / (1 - p_star))                   # its log-odds; the prior sits at 0
    step = (1 - alpha) * math.log((1 - pi_lo * s) / (1 - pi_hi * s))
    return math.inf if step <= 0 else math.ceil(-tau / step - 1e-12)


def staircase(alpha, pi_hi, pi_lo, s, c):
    """Closed form for the paper's example, ignoring the O(eps) paths that start with a broad failure: lost iff the
    first n inspections all fail the niche screen, each with probability pi_hi * (1 - s)."""
    n = needed_niche_failures(alpha, pi_hi, pi_lo, s, c)
    return 0.0 if n == math.inf else (pi_hi * (1 - s)) ** n


def alpha_threshold(pi_hi, pi_lo, s, c):
    """Smallest alpha at which one niche failure no longer loses the business."""
    p_star = (c / s - pi_lo) / (pi_hi - pi_lo)
    tau = math.log(p_star / (1 - p_star))
    return 1 + tau / math.log((1 - pi_lo * s) / (1 - pi_hi * s))


def scenarios(pi_hi, pi_lo, s, bayes_broad=False):
    """Named reader populations for one parameter setting."""
    t = lambda a: llr_table(pi_hi, pi_lo, s, alpha=a, bayes_broad=bayes_broad)  # noqa: E731
    out = [("Shallow search, the paper's market M", [(llr_table(pi_hi, pi_lo, s, shallow=True), 1.0)], True),
           ("Deep, niche failures counted as plain (alpha 0)", [(t(0.0), 1.0)], False)]
    for fmt, d in GPT5MINI.items():
        alphas = [alpha_of(a, d["clean"]) for a in d["answers"]]
        mean_alpha = (np.mean(d["answers"]) - PLAIN) / (d["clean"] - PLAIN)
        out += [(f"gpt-5-mini {fmt}, average reader (alpha {mean_alpha:.2f})", [(t(mean_alpha), 1.0)], False),
                (f"gpt-5-mini {fmt}, sampled readers", [(t(a), w) for a, w in population(alphas)], False)]
    out += [("gpt-5-mini at temp 0, every agent counts (alpha 0)", [(t(0.0), 1.0)], False),
            (f"gpt-5.6-luna (alpha {LUNA_ALPHA:g})", [(t(LUNA_ALPHA), 1.0)], False),
            ("Half gpt-5-mini temp 0, half luna", [(t(0.0), 0.5), (t(LUNA_ALPHA), 0.5)], False),
            ("Paper's Bayesian transcript reader", [(llr_table(pi_hi, pi_lo, s, paper=True), 1.0)], False)]
    return out


def report(title, pi_hi, pi_lo, s, c, closed_form=False, bayes_broad=False):
    print(f"\n=== {title}: pi1 in {{{pi_lo:g}, {pi_hi:g}}}, niche pass {s:g}, inspection cost {c:g}, "
          f"{REPS:,} runs x {T} consumers" + (", broad failures read the Bayesian way" if bayes_broad else ""))
    print(f"  {'readers':58s} {'good lost':>9s} {'bad kept':>9s} {'skipped':>9s}")
    for name, readers, shallow in scenarios(pi_hi, pi_lo, s, bayes_broad):
        g, skip = simulate(readers, pi_hi, pi_lo, s, c, good=True, shallow=shallow)
        b, _ = simulate(readers, pi_hi, pi_lo, s, c, good=False, shallow=shallow, seed=1)
        print(f"  {name:58s} {g:9.3f} {1 - b:9.3f} {skip:9.1f}")
    print(f"  {'alpha sweep, everyone reads alike':58s} {'good lost':>9s}" + (f" {'closed':>9s}" if closed_form else ""))
    for a in np.round(np.arange(0, 1.0001, 0.1), 2):
        g, _ = simulate([(llr_table(pi_hi, pi_lo, s, alpha=a, bayes_broad=bayes_broad), 1.0)], pi_hi, pi_lo, s, c)
        closed = f" {staircase(a, pi_hi, pi_lo, s, c):9.3f}" if closed_form else ""
        print(f"  {'  alpha ' + format(a, '.1f'):58s} {g:9.3f}{closed}")


if __name__ == "__main__":
    eps = 0.01
    report("Paper's Prop 6.5 example (Appendix C.3)", 1 - eps, eps, 0.5, 0.2, closed_form=True)
    print(f"\n  alpha below which one niche failure still loses the business: "
          f"{alpha_threshold(1 - eps, eps, 0.5, 0.2):.3f} at eps {eps:g}, "
          f"{alpha_threshold(1 - 1e-9, 1e-9, 0.5, 0.2):.3f} as eps -> 0")
    # With broad failures read as plain failures (what both models did), alpha 0 is the paper's deep market
    # without transcripts. Reading them the Bayesian way is a robustness check on that choice.
    report("Softer prior", 0.9, 0.3, 0.5, 0.25)
    report("Softer prior", 0.9, 0.3, 0.5, 0.25, bayes_broad=True)
