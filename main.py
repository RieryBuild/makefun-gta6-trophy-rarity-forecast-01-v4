#!/usr/bin/env python3
"""GTA VI trophy-rarity forecaster -- count-space refresh-mixture model.

Reads one case (makefun/gta6-trophies-case/v1) from $MAKEFUN_INPUT_DIR
(or /input) and writes, for each of the case's trophies, the 5/25/50/75/95%
quantiles of its Exophase earn rate at the case's target, to
$MAKEFUN_OUTPUT_DIR (or /output).

Model (built from the competition rules and the design in build-log.md,
its constants selected on the extended synthetic suite -- never on the
practice cases or the dev leaderboard):

* Count space. Tracked players and per-trophy earners are rolled forward
  separately; a trophy's rate is earners / players. An Exophase refresh
  is a jump in the tracked-player denominator, not a change in how
  players behave, so a refresh dilutes every rate by a factor that
  depends on how many of the newcomers earn that trophy.
* Two regimes. If the history shows refreshes, the refresh period, the
  dilution and the newcomer fractions are LEARNED from the transitions
  between successive reads. If it shows none, wide launch-night priors
  apply (first refresh ~270 min after the first read, first dilution
  ~4x, newcomer fraction ~0.12).
* Growth decay. Dilution shrinks from refresh to refresh; the decay is
  estimated from successive observed dilutions and projected forward,
  so rates stabilise as the launch surge fades.
* Newcomer fractions graded by easiness. A newcomer earns an easy
  trophy more often than a rare one: f_i = f_base * sqrt(r_i / r_med),
  with f_base learned from the observed transitions (median over
  trophies and transitions, so one noisy rare trophy cannot move it).
  The trophy at 100% keeps f = 1 and stays at 100% (RULES section 11).
* Mixture over refresh counts. The number of refreshes before the
  target is a discretised-normal mixture centred on the count implied
  by the learned period and the phase of the last refresh (or, with no
  refresh observed, on the prior grid anchored at the first read).
  Each mixture component rolls the counts forward to its own refresh
  count; the five quantiles come from inverting that mixture's CDF on
  the logit scale, so the median and the spread come from one
  predictive distribution instead of being bolted together.
* Spread. The within-component logit spread grows with the number of
  future refreshes (each refresh adds dilution/newcomer noise) and with
  the square root of the horizon in days (random-walk drift between
  refreshes). Its scale is calibrated on the synthetic suite to
  ~0.90 coverage at every horizon from 90 minutes to 4.5 days.

Python 3.13, standard library only. Deterministic: no randomness, no
clock, no network; the same input always yields the same bytes.
"""

import json
import math
import os
import sys
from datetime import datetime

LEVELS = (0.05, 0.25, 0.5, 0.75, 0.95)
SQRT2 = math.sqrt(2.0)

# Calibration constants. Every value below was selected on the extended
# synthetic suite (synth_suite_v4.py: 12 original scenarios + 6 final-like
# ones); none was selected from a practice loss or a dev-board rank.
# See build-log-v4.md for the sweep and the chosen values.
DEFAULT_PARAMS = {
    # Launch-night priors, used only while no refresh has been observed.
    "prior_period_min": 270.0,
    "prior_dilution_median": 3.0,
    "prior_f_base": 0.20,
    "decay_prior": 0.90,
    "decay_min": 0.60,
    "decay_max": 1.00,
    # Refresh-count mixture: sd(k) = sqrt(A*mu + (B*mu)^2 + phase_var).
    "k_sd_a": 0.0,
    "k_sd_b": 0.05,
    "k_sd_floor": 0.70,
    "phase_var_unlearned": 1.0,
    # Within-component logit spread: sqrt(SR^2 * k + SH^2 * days).
    "spread_per_refresh": 0.01,
    "spread_per_day": 0.01,
    "spread_floor": 0.02,
    # Blend of the per-trophy observed newcomer fraction into the
    # easiness-graded one (0 = easiness curve only). Suite optimum is
    # 1.0; 0.75 is a robustness cap (see build-log-v4.md): the suite's
    # generator holds per-trophy fractions fixed, so it cannot penalise
    # over-reliance on observed fractions if the real ones drift.
    "f_blend": 0.75,
    # How the refresh period is estimated from successive transitions:
    # "median_diffs" (median of the last <=3 diffs), "endpoint_span"
    # (first-to-last span / count), or "recent_span" (span of the last
    # three transitions). Suite-selected.
    "period_method": "median_diffs",
    # How the expected refresh count is centred with no refresh observed:
    # "grid" anchors the prior grid at the first read; "phase_avg" uses
    # horizon / period (uniform phase). Suite-selected.
    "unlearned_mu": "phase_avg",
    # Optional override of the learned newcomer base fraction (None =
    # estimate from the history). Used by the suite's holdout check.
    "f_base": None,
}


def _weighted_median(pairs):
    """Weighted median of (value, weight) pairs, else None."""
    xs = sorted((v, w) for (v, w) in pairs if w > 0)
    total = sum(w for (_, w) in xs)
    if total <= 0 or not xs:
        return None
    acc = 0.0
    for v, w in xs:
        acc += w
        if acc >= 0.5 * total:
            return v
    return xs[-1][0]


def _median(values):
    """Median of a non-empty list, else None."""
    xs = sorted(values)
    n = len(xs)
    if n == 0:
        return None
    mid = n // 2
    if n % 2:
        return xs[mid]
    return 0.5 * (xs[mid - 1] + xs[mid])


def _parse_time(text):
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    return datetime.fromisoformat(text)


def _minutes_between(a, b):
    return (b - a).total_seconds() / 60.0


def _logit_pct(x):
    p = min(max(x, 0.0001), 99.9999) / 100.0
    return math.log(p / (1.0 - p))


def _inv_logit_pct(L):
    if L >= 0.0:
        p = 1.0 / (1.0 + math.exp(-L))
    else:
        e = math.exp(L)
        p = e / (1.0 + e)
    return p * 100.0


def _phi(x):
    return 0.5 * (1.0 + math.erf(x / SQRT2))


# ---------------------------------------------------------------------------
# History analysis
# ---------------------------------------------------------------------------

def detect_transitions(history, n_trophies):
    """Find refreshes: consecutive reads where players_tracked jumps.

    Returns a list of dicts, oldest first, each with:
      t_mid       -- datetime midway between the bracketing reads
      dilution    -- players_after / players_before (>= 1)
      f_base      -- median newcomer base fraction implied by this
                     refresh (None when it cannot be estimated)
      f_by_trophy -- {trophy index: (f_raw, f_graded)} per trophy
      r_med       -- median pre-refresh rate (excl. the 100% trophy)
    """
    transitions = []
    prev = None
    # Record-high rule (round 4b): the running maximum of
    # players_tracked, and the read that set it. A rise only counts as
    # a refresh when it beats the running max; the dilution is measured
    # against the max, and the baseline earners/rates for f_raw are the
    # max-setting read's, not the previous read's when the previous
    # read was a drop. A drop followed by a recovery to the old level
    # (100 -> 90 -> 100) therefore produces NO transition: the old
    # rise-vs-previous test recorded a phantom 1.111x transition on
    # the recovery, whose midpoint dragged the period estimate down
    # (a true 60-min cadence read as ~30 min) and inflated the
    # expected refresh count. For a monotonically rising history the
    # max-setting read IS the previous read, so behaviour is identical.
    max_read = None
    for read in history:
        try:
            t = _parse_time(read["at"])
        except Exception:
            continue
        players = read.get("players_tracked")
        rates = read.get("rates") or []
        if players is None or players <= 0 or len(rates) < n_trophies:
            continue
        players = float(players)
        earners = [None if rates[i] is None else float(rates[i]) * players / 100.0
                   for i in range(n_trophies)]
        if prev is not None and max_read is not None:
            m_players, m_earners, m_rates, _m_t = max_read
            p_t = prev[3]
            # Only a rise ABOVE the running max is a refresh. A drop
            # is not a transition, and neither is a recovery to (or
            # below) the old maximum. The m_players > 0 guard is
            # belt-and-braces (the reader already skips non-positive
            # reads, so the max can never hold one, but the division
            # players / m_players below must never see 0).
            if m_players > 0 and players > m_players:
                dilution = players / m_players
                # t_mid stays the midpoint of the BRACKETING reads
                # (previous read and this read), not of the max read.
                t_mid = p_t + (t - p_t) / 2
                base_rates = [r for r in m_rates
                              if r is not None and r < 99.995]
                r_med = _median(base_rates) or 1.0
                f_by_trophy = {}
                if dilution > 1.0:
                    for i in range(n_trophies):
                        eb = m_earners[i]
                        ea = earners[i]
                        rb = m_rates[i]
                        if eb is None or ea is None or rb is None:
                            continue
                        if rb >= 99.995 or eb < 2.0:
                            continue
                        if ea <= eb:
                            # Earners did not grow across a refresh
                            # (rate rounding on small counts can do
                            # this): the implied newcomer fraction is
                            # zero or negative, which would drag the
                            # median f_base down. Skip the trophy.
                            continue
                        f_raw = (ea / eb - 1.0) / (dilution - 1.0)
                        f_graded = f_raw / math.sqrt(max(rb, 0.1) / r_med)
                        f_by_trophy[i] = (f_raw, f_graded)
                f_base = None
                if dilution > 1.05 and f_by_trophy:
                    f_base = _median([g for (_, g) in f_by_trophy.values()])
                    if f_base is not None:
                        f_base = min(max(f_base, 0.01), 0.9)
                transitions.append({
                    "t_mid": t_mid,
                    "dilution": max(dilution, 1.0),
                    "f_base": f_base,
                    "f_by_trophy": f_by_trophy,
                    "r_med": r_med,
                })
        if max_read is None or players > max_read[0]:
            max_read = (players, earners, rates, t)
        prev = (players, earners, rates, t)
    return transitions


def estimate_f_base(transitions, only=None):
    """Median newcomer base fraction across transitions.

    With `only` (a set of trophy indices) the per-transition value is
    recomputed from just those trophies -- the suite's holdout check.
    """
    vals = []
    for tr in transitions:
        if only is None:
            if tr["f_base"] is not None:
                # A transition with a bigger dilution pins the newcomer
                # fraction down more precisely (the (D - 1) divisor
                # amplifies rate-rounding noise less), so weight by it.
                vals.append((tr["f_base"], tr["dilution"] - 1.0))
        else:
            sub = [g for i, (_, g) in tr["f_by_trophy"].items() if i in only]
            v = _median(sub)
            if v is not None:
                vals.append((min(max(v, 0.01), 0.9), tr["dilution"] - 1.0))
    if not vals:
        return None
    return _weighted_median(vals)


def estimate_period(transitions, first_t, checkpoint_t, params):
    """Refresh period in minutes, the anchor (last refresh moment) and
    whether the phase is learned from the history."""
    if len(transitions) >= 2:
        mids = [tr["t_mid"] for tr in transitions]
        method = params.get("period_method", "median_diffs")
        if method == "endpoint_span":
            # Span over the whole observed refresh sequence: midpoint
            # noise (+-half a cadence at each end) is averaged over the
            # full span instead of per-diff, so the period estimate is
            # steadier when the refresh grid is regular.
            period = _minutes_between(mids[0], mids[-1]) / (len(mids) - 1)
        elif method == "recent_span":
            # Span of the last three transitions only (recency + span).
            use = mids[-3:]
            period = _minutes_between(use[0], use[-1]) / (len(use) - 1)
        else:  # median_diffs
            diffs = [_minutes_between(mids[i], mids[i + 1])
                     for i in range(len(mids) - 1)]
            period = _median(diffs[-3:])
        return period, mids[-1], True
    if len(transitions) == 1:
        # One transition: the span from the first read to it is the only
        # period estimate available (the page was frozen from the start).
        period = _minutes_between(first_t, transitions[0]["t_mid"])
        return period, transitions[0]["t_mid"], True
    span = _minutes_between(first_t, checkpoint_t)
    # No refresh observed in `span` minutes: a period shorter than the
    # span is ruled out, so the prior period cannot be below it.
    period = max(params["prior_period_min"], span + 60.0)
    return period, first_t, False


def estimate_decay(transitions, params):
    """Growth-decay factor for successive dilutions, from observed
    (D_{k+1} - 1) / (D_k - 1) ratios, else the prior."""
    if len(transitions) >= 2:
        ratios = []
        for a, b in zip(transitions, transitions[1:]):
            if a["dilution"] > 1.05 and b["dilution"] > 1.0:
                ratios.append((b["dilution"] - 1.0) / (a["dilution"] - 1.0))
        if ratios:
            d = _median(ratios)
            return min(max(d, params["decay_min"]), params["decay_max"])
    return params["decay_prior"]


# ---------------------------------------------------------------------------
# Forward projection
# ---------------------------------------------------------------------------

def future_refresh_weights(period, anchor_min, checkpoint_min, target_min,
                           learned, params):
    """Discretised-normal mixture over the number of refreshes before
    the target. Times are minutes since the first history read."""
    if learned or params["unlearned_mu"] == "grid":
        # Count grid points (anchor + j*period) in (checkpoint, target].
        g = anchor_min + period
        while g <= checkpoint_min:
            g += period
        mu = 0.0
        while g <= target_min:
            mu += 1.0
            g += period
    else:
        mu = max(0.0, (target_min - checkpoint_min) / period)
    var = params["k_sd_a"] * mu + (params["k_sd_b"] * mu) ** 2
    if not learned:
        var += params["phase_var_unlearned"]
    sd = max(math.sqrt(var), params["k_sd_floor"])
    k_min = max(0, int(math.floor(mu - 3.0 * sd)))
    k_max = int(math.ceil(mu + 3.0 * sd))
    ks = list(range(k_min, k_max + 1))
    ws = [math.exp(-0.5 * ((k - mu) / sd) ** 2) for k in ks]
    total = sum(ws)
    ws = [w / total for w in ws]
    return ks, ws, mu, sd


def dilution_schedule(k_max, d_last, decay, n_trans, params):
    """Dilution of each future refresh, decaying from the last observed
    one (or from the prior first-refresh dilution when none observed)."""
    ds = []
    for j in range(1, k_max + 1):
        if n_trans == 0:
            if j == 1:
                d = params["prior_dilution_median"]
            else:
                d = 1.0 + (params["prior_dilution_median"] - 1.0) * (decay ** (j - 1))
        else:
            d = 1.0 + (d_last - 1.0) * (decay ** j)
        ds.append(max(d, 1.0))
    return ds


def roll_rates(e_last, n_last, f_i, dilutions):
    """Rate (percent) after 0..len(dilutions) future refreshes."""
    e, n = e_last, n_last
    out = [100.0 * e / n]
    for d in dilutions:
        e *= 1.0 + (d - 1.0) * f_i
        n *= d
        out.append(100.0 * e / n)
    return out


def mixture_quantiles(rates_k, weights, sigmas):
    """Quantiles of a mixture of lognormals (one per refresh count),
    by bisection on the mixture CDF on the logit scale."""
    logits = [_logit_pct(r) for r in rates_k]
    out = []
    for tau in LEVELS:
        a, b = -13.0, 4.6
        for _ in range(40):
            m = 0.5 * (a + b)
            cdf = 0.0
            for lg, w, s in zip(logits, weights, sigmas):
                cdf += w * _phi((m - lg) / s)
            if cdf < tau:
                a = m
            else:
                b = m
        out.append(_inv_logit_pct(0.5 * (a + b)))
    return out


# ---------------------------------------------------------------------------
# One case
# ---------------------------------------------------------------------------

def forecast_case(case, params=None):
    p = dict(DEFAULT_PARAMS)
    if params:
        p.update(params)
    trophies = case["trophies"]
    n = len(trophies)
    history = case.get("history") or []
    if not history:
        raise ValueError("case has no history reads")

    t0 = _parse_time(history[0]["at"])
    checkpoint_t = _parse_time(case["at"])
    target_t = _parse_time(case["target"])
    checkpoint_min = _minutes_between(t0, checkpoint_t)
    target_min = _minutes_between(t0, target_t)
    horizon_min = max(target_min - checkpoint_min, 0.0)
    horizon_days = horizon_min / 1440.0

    last = history[-1]
    last_players = last.get("players_tracked")
    last_rates = list(last.get("rates") or [])
    if len(last_rates) < n:
        last_rates.extend([None] * (n - len(last_rates)))
    if last_players is None or float(last_players) <= 0:
        # The last read has no usable player count (0 or missing):
        # fall back to the most recent earlier read with a positive
        # player count, and take its rates for any trophy whose
        # last-read rate is missing. Without this, roll_rates divides
        # by zero (100.0 * e / n with n = 0) and the case crashes.
        last_players = None
        for read in reversed(history[:-1]):
            cand = read.get("players_tracked")
            if cand is not None and float(cand) > 0:
                last_players = float(cand)
                fb_rates = read.get("rates") or []
                for i in range(n):
                    if last_rates[i] is None and i < len(fb_rates) \
                            and fb_rates[i] is not None:
                        last_rates[i] = fb_rates[i]
                break
        if last_players is None:
            raise ValueError(
                "no history read has a positive players_tracked")
    else:
        last_players = float(last_players)
    # Fill a missing last-read rate from the most recent read that has it.
    for i in range(n):
        if last_rates[i] is None:
            for read in reversed(history[:-1]):
                r = (read.get("rates") or [None] * n)[i]
                if r is not None:
                    last_rates[i] = r
                    break
    known = [r for r in last_rates if r is not None and r < 99.995]
    r_med_all = _median(known) or 1.0
    for i in range(n):
        if last_rates[i] is None:
            last_rates[i] = r_med_all

    trans = detect_transitions(history, n)
    period, anchor_t, learned = estimate_period(trans, t0, checkpoint_t, p)
    period = min(max(period, 30.0), 200000.0)
    anchor_min = _minutes_between(t0, anchor_t)
    decay = estimate_decay(trans, p)
    f_base = p["f_base"]
    if f_base is None:
        f_base = estimate_f_base(trans)
    if f_base is None:
        f_base = p["prior_f_base"]

    # Per-trophy observed newcomer fractions (for the optional blend),
    # precision-weighted by each transition's dilution.
    observed_f = {}
    for i in range(n):
        pairs = [(tr["f_by_trophy"][i][0], tr["dilution"] - 1.0)
                 for tr in trans if i in tr["f_by_trophy"]]
        v = _weighted_median(pairs)
        if v is not None:
            observed_f[i] = min(max(v, 0.02), 0.95)

    ks, ws, mu, sd = future_refresh_weights(
        period, anchor_min, checkpoint_min, target_min, learned, p)
    k_max = ks[-1] if ks else 0
    d_last = trans[-1]["dilution"] if trans else 1.0
    dilutions = dilution_schedule(k_max, d_last, decay, len(trans), p)
    sigmas = []
    for k in ks:
        var = (p["spread_per_refresh"] ** 2) * k \
            + (p["spread_per_day"] ** 2) * horizon_days
        sigmas.append(max(math.sqrt(var), p["spread_floor"]))

    rows = []
    cache = {}
    for idx, tr in enumerate(trophies):
        r_last = float(last_rates[idx])
        if r_last >= 99.995:
            # Universal trophy: every newcomer earns it, so it stays 100%.
            rows.append({"id": tr["id"], "q": [100.0, 100.0, 100.0, 100.0, 100.0]})
            continue
        f_i = min(max(f_base * math.sqrt(max(r_last, 0.1) / r_med_all),
                      0.02), 0.95)
        if p["f_blend"] > 0.0 and idx in observed_f:
            # Blend toward the trophy's own observed newcomer fraction.
            # The weight is shrunk when few transitions were observed:
            # one transition's per-trophy fraction is noisy, five are not.
            w = p["f_blend"] * len(trans) / (len(trans) + 2.0)
            f_i = (1.0 - w) * f_i + w * observed_f[idx]
        key = (round(r_last, 4), round(f_i, 5))
        if key not in cache:
            e_last = r_last * last_players / 100.0
            if e_last <= 0.0:
                # No earner yet: a half-earner pseudo-count so the
                # forecast is a small positive rate, not exactly zero.
                e_last = 0.5
            rolled = roll_rates(e_last, last_players, f_i, dilutions)
            rates_k = [rolled[k] for k in ks]
            qs = mixture_quantiles(rates_k, ws, sigmas)
            fixed = []
            prev_q = 0.001
            for q in qs:
                q = min(max(round(q, 4), 0.001), 99.999)
                q = max(q, prev_q)
                fixed.append(q)
                prev_q = q
            cache[key] = fixed
        rows.append({"id": tr["id"], "q": list(cache[key])})
    return {"trophies": rows}


def main(argv=None):
    in_dir = os.environ.get("MAKEFUN_INPUT_DIR") or "/input"
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR") or "/output"
    os.makedirs(out_dir, exist_ok=True)
    names = sorted(name for name in os.listdir(in_dir)
                   if name.endswith(".in"))
    for name in names:
        with open(os.path.join(in_dir, name), "r", encoding="utf-8") as fh:
            case = json.load(fh)
        out = forecast_case(case)
        out_name = name[:-3] + ".out"
        with open(os.path.join(out_dir, out_name), "w", encoding="utf-8") as fh:
            json.dump(out, fh, separators=(",", ":"))
            fh.write("\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
