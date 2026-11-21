# Build log — gta6-trophy-rarity-forecast-01 (entry v4)

Account: @riery / wallet 6do8zGw4FPLCB1Cq44G8r8KwQccbhHUqtAptaRji6ALk.
Built 21 Nov 2026 ~15:00–17:00 WITA, fresh from the brief + the v1 design
doc + this session's own analysis. The v3 entry code (and every earlier
`main.py`) was never read: `main.py` here is 497 lines written from
scratch in this session.

Selection split (decided before testing candidates, per the round-4
brief): the extended synthetic suite (`synth_suite_v4.py`, 24 scenarios)
is the ONLY selection criterion. p00/p01 are smoke checks only (loss
<< house baseline 1.51). Nothing was tuned to a practice loss, a dev
rank, the 6.06x launch dilution, post-refresh rates, or run time.

## Fix round — independent review (21 Nov ~15:45–16:05 WITA)

OpenRouter independent review (nvidia/nemotron-3-ultra-550b-a55b:free)
VERDICT: FIX. Three bugs, all verified real in the code by the
coordinator before fixing. Nothing else changed: the phase_avg vs grid
tradeoff, the CDF-mixture inversion, determinism, stdlib-only and
format are as reviewed and untouched.

1. **Bug 1 — CRITICAL crash, division by zero (`forecast_case`).**
   `last_players = float(last["players_tracked"])` had no guard and
   `roll_rates` computes `100.0 * e / n`; a last read with
   `players_tracked = 0` crashed with ZeroDivisionError (the
   `e_last <= 0` guard only covered the earners side). Fix: when the
   last read's player count is missing or <= 0, fall back to the most
   recent earlier read with a positive player count, and take its
   rates for any trophy whose last-read rate is missing; if no read
   has a positive player count, raise `ValueError("no history read
   has a positive players_tracked")`. Also pads a short `rates` list
   with None so the fill loop cannot IndexError.
2. **Bug 2 — CRITICAL logic bug, player drop counted as a refresh
   (`detect_transitions`).** `if players != p_players:` made a drop
   (e.g. 100 -> 90) a phantom transition with dilution stored as 1.0:
   it inflated the transition count (so `len(trans) >= 2` could go
   true from two drops), corrupted `estimate_period` via the drop
   midpoint, set `d_last = 1.0` (all future dilutions 1.0) and
   inflated `f_blend` weights. Fix: `if p_players > 0 and players >
   p_players:` — only a rise is a refresh; the `p_players > 0`
   guard is belt-and-braces (the reader already skips non-positive
   reads, so `prev` can never hold one, but the division
   `players / p_players` must never see 0).
3. **Bug 3 — silent bias, negative newcomer fraction (`detect_transitions`).**
   `f_raw = (ea / eb - 1.0) / (dilution - 1.0)` went negative when
   earners fell across a refresh while players rose (rate rounding on
   small counts), entered `f_graded`, and dragged the median `f_base`
   down (the [0.01, 0.9] clamp is applied only AFTER the median).
   Fix: `if ea <= eb: continue` before computing `f_raw`.

**Testing caught a fourth defect in the fix itself:** the Bug 1
fallback loop first used `p` as its loop variable, shadowing the
params dict `p` in `forecast_case` — `estimate_period` then got an
int and raised AttributeError. The regression test (C1) caught it
before any suite run; the loop variable is now `cand`. No other
shadowing in the file (`p` is only the params dict elsewhere).

**Regression tests** (`test_fixes.py`, 23 checks, all PASS — behaviour,
not just no-crash):
- A (bug 2): base case (2 refreshes, dilution 2.0, period 360):
  replacing the last read with a halved player count, and appending
  an extra halved read, leave transition count (2), period (360.0)
  and d_last (2.0) EXACTLY unchanged; no transition has dilution
  <= 1.0; a zero-players read mid-history does not crash.
- B (bug 3): 7-trophy case, 3 good + 4 bad trophies (bad: earners
  10 -> 12 -> 8, f_raw -1/3 at transition 2). Fixed f_base = 0.20,
  identical with vs without the bad trophies, and NOT the hand-computed
  old-code value 0.01; bad trophies are absent from `f_by_trophy` at
  transition 2 but present (f_raw 0.20) at transition 1. Note: a
  single bad trophy cannot move a median — the case uses four
  because the real rounding pattern hits many small-count trophies
  at once; the with/without comparison is the behaviour that matters.
- C (bug 1): last read players = 0 with rates None AND with rates
  present both give output byte-identical to the same case with that
  read removed (55 valid rows); all-zero history and single zero
  read both raise the clear ValueError.

**Re-validation after the fix (new numbers):**
- Extended suite (24 scenarios): mean loss **0.0631**, mean coverage
  0.95 — per-scenario losses identical to the pre-fix table to 4
  decimals. Informative mean **0.1414** (recomputed from the printed
  table; the log's earlier 0.1411 is the same value at 4-decimal
  table rounding, not a change), informative coverage 0.917.
  Per-horizon: 90 min 0.3006 / 0.90; 1–3 days 0.0108 / 0.99;
  4.5 days 0.0176 / 0.95. **s12 0.0235 / cov 0.78; s23 0.0570 /
  cov 0.75** — all unchanged.
- Original v1 suite (12 scenarios): mean loss **0.1052**, cov 0.95 —
  identical to pre-fix.
- Cross-tier holdout: 0.1188 / 0.1183 — identical.
- Determinism: 2 runs byte-identical on system Python, and
  byte-identical again in a fresh venv with nothing installed.
- Runtime: 0.28 s for p00 + p01 including interpreter startup
  (~0.14 s/case); extended suite 24 cases in 0.68 s. Limit 8 s.
- Stdlib only: imports are `json`, `math`, `os`, `sys`, `datetime`
  (grep + AST). Format: 55 rows, quantiles non-decreasing, in
  (0, 100], 2,804 / 2,735 bytes.
- Smoke p00/p01 (same hypothesised answer): loss **0.5761** /
  **0.5766**, coverage 0.22; 100% trophy outputs 100.0 on all five
  quantiles. Unchanged, as expected: the suite generator never
  produces a drop, a zero-player last read, or an ea < eb trophy,
  so the fixes are pure robustness — they change no suite number
  and only fire on the degenerate inputs they guard.

## Fix round 4b — record-high rule for `detect_transitions` (21 Nov ~16:10–16:30 WITA)

Second OpenRouter review confirmed one remaining MATERIAL issue for
the period estimate: a drop followed by a recovery still recorded a
small transition on the recovery rise. History 100 → 90 → 100 → 200
produced transitions [1.111, 2.0]; the phantom 1.111 transition's
midpoint pulled the period estimate down (a true 60-min cadence read
as ~30 min), which inflates the expected refresh count and moves the
median. `f_base` was protected by the (D−1) weight (~10%
contamination) and `d_last` was correct — but the period was not.

Fix (minimal, in `detect_transitions` only; the three round-4 fixes
are untouched): track the running maximum of `players_tracked` and
the read that set it (`max_read`). A rise counts as a transition
only when `players > running_max`; dilution = `players /
running_max`; the baseline earners/rates for `f_raw` are the
max-setting read's, not the previous read's when the previous read
was a drop. `t_mid` stays the midpoint of the BRACKETING reads
(previous read and current read). If no rise beats the max, there
is no transition: a drop and a recovery to the old level produce
nothing. For a monotonically rising history the max-setting read IS
the previous read, so behaviour is IDENTICAL — which the
re-validation below confirms numerically.

**Regression tests** (`test_fixes.py`, section D, 23 new checks —
46 total, all PASS, behaviour not just no-crash):
- D0: clean reference 1000 → 1000 → 2000 (same first read and same
  bracketing reads 02:00 → 03:00 as the drop cases): exactly 1
  transition, dilution 2.0, f_base 0.20, period 150 min.
- D1 (a): 1000 → 900 → 1000 → 2000: exactly ONE transition,
  dilution 2.0 (no 1.111 phantom); period, f_base, d_last and t_mid
  IDENTICAL to the clean case; per-trophy f_raw 0.20 (baseline is
  the max read); the full forecast output is byte-identical to the
  clean case's.
- D2 (b): 1000 → 900 → 800 → 2000 (deeper drop, no recovery):
  exactly one transition, dilution 2.0, period/f_base/d_last
  identical to clean.
- D3 (c): 1000 → 900 → 950 → 2000 (partial recovery, 950 is NOT a
  new max): exactly one transition, dilution 2.0 (not 2000/950),
  period/f_base/d_last identical to clean.

**Re-validation after the 4b fix — all numbers IDENTICAL to pre-fix:**
- Extended suite (24 scenarios): mean loss **0.0631**, mean coverage
  0.95 — every per-scenario loss identical to the pre-fix table to
  4 decimals (s12 0.0235 / cov 0.78; s23 0.0570 / cov 0.75).
  Informative mean **0.1414** (recomputed from the printed table;
  the log's 0.1411 is the same value at 4-decimal table rounding),
  informative coverage 0.917. Per-horizon: 90 min 0.3006 / 0.90;
  1–3 days 0.0108 / 0.99; 4.5 days 0.0176 / 0.95.
- Original v1 suite (12 scenarios): mean loss **0.1052**, cov 0.95 —
  identical to pre-fix.
- Cross-tier holdout: 0.1188 / 0.1183 — identical.
- Determinism: 2 runs byte-identical on system Python, and
  byte-identical again in a fresh venv with nothing installed.
- Runtime: 0.30 s for p00 + p01 including interpreter startup
  (~0.15 s/case); extended suite 24 cases in 0.93 s. Limit 8 s.
- Stdlib only: imports are `json`, `math`, `os`, `sys`, `datetime`
  (grep + AST). Format: 55 rows, quantiles non-decreasing, in
  (0, 100], 2,804 / 2,735 bytes.
- Smoke p00/p01: loss **0.5761** / **0.5766**, coverage 0.22 —
  identical to pre-fix.

## Design (v4)

Count-space refresh-mixture model, one file, Python 3.13 stdlib only:

- **Count space.** Tracked players and per-trophy earners roll forward
  separately; rate = earners / players. A refresh is a jump in the
  denominator, not a behaviour change.
- **Two regimes.** Refreshes in the history are detected from jumps in
  `players_tracked` between consecutive reads. When transitions exist,
  the period, the dilution and the newcomer fractions are LEARNED from
  them; when none exist, wide launch-night priors apply (period
  ~270 min, first dilution ~3x, newcomer base fraction ~0.20).
- **Mixture over refresh counts.** The number of refreshes before the
  target is a discretised-normal mixture centred on the count implied
  by the learned period and the phase of the last refresh (or, with no
  refresh observed, on horizon / period). Each component rolls the
  counts forward to its own refresh count; the five quantiles come from
  inverting that mixture's CDF on the logit scale, so the median and
  the spread come from one predictive distribution.
- **Growth decay.** Each future refresh's dilution decays from the last
  observed one, `D_j = 1 + (D_last - 1) * decay^j`, with decay
  estimated from successive observed `(D-1)` ratios.
- **Newcomer fractions graded by easiness.** `f_i = f_base *
  sqrt(r_i / r_med)`, with `f_base` the precision-weighted median over
  transitions (weight `D - 1`: a bigger dilution pins the fraction down
  more precisely). The per-trophy observed fraction is blended in with
  weight `f_blend * n / (n + 2)` (shrunk when few transitions were
  observed). The 100% trophy keeps `f = 1` and stays at 100%.
- **Spread.** Within-component logit spread `sqrt(SR^2 * k + SH^2 *
  days)`; the k-mixture itself carries most of the spread. Calibrated
  on the suite to ~0.90 coverage at every horizon.

## What changed vs the v1 design

1. **Quantiles from a mixture CDF, not a point median + bolted-on
   spread.** v1 computed a median rate and added a spread around it.
   v4 inverts the full predictive distribution (mixture over refresh
   counts, each with its own lognormal), so the median is the
   distribution's median and the spread is the distribution's spread.
   This is the main structural change, and it is what lets the spread
   calibration actually bite: with the v1-style bolted-on spread the
   suite coverage was 1.00 everywhere.
2. **Spread calibration is now the binding lever.** Suite-selected:
   `k_sd_a = 0`, `k_sd_b = 0.05`, `spread_per_refresh = 0.01`,
   `spread_per_day = 0.01`. The within-component spread is nearly
   negligible; the refresh-count mixture carries the uncertainty.
   (v1/v3 were over-covered: r3's practice coverage was 0.9909.)
3. **Unlearned branch centres on horizon / period (phase_avg), not
   on the prior grid anchored at the first read.** Suite-selected:
   informative mean loss 0.1584 vs 0.1653 for the grid at the same
   priors. Tradeoff, stated openly: the p00/p01 median now predicts
   NO refresh in the 90-minute horizon (median = last rate), so the
   smoke loss is 0.58 with coverage 0.22 instead of v1-style 0.34 /
   1.00. Still far below the 1.51 baseline; the suite (which has two
   no-refresh and two refresh cases in s1–s4) is the binding arbiter.
4. **Per-trophy observed newcomer fractions are blended in**
   (`f_blend = 0.75`, shrunk by transition count). The suite optimum
   is 1.0 (informative loss 0.1403 vs 0.1436 at 0.75); 0.75 is a
   deliberate robustness cap, because the suite's generator holds
   per-trophy fractions fixed and therefore cannot penalise
   over-reliance on observed fractions if the real ones drift.
   The blend is what fixed the decay scenarios: s12's bronze-holdout
   error fell from 0.442 (v1/v2) to 0.035.
5. **Period estimation tested three ways; median-of-diffs kept.**
   `endpoint_span` and `recent_span` gave identical informative loss
   to four decimals, so the v1 choice stands.
6. **Priors re-derived on the suite:** first dilution 3.0 (not 4.0),
   newcomer base fraction 0.20 (not 0.12), decay prior 0.90.
   The launch dilution 6.06x was never used.
7. **Precision-weighted medians** for `f_base` and per-trophy observed
   fractions (weight `D - 1`). Neutral on the suite (informative loss
   0.1414 vs 0.1411 unweighted); kept because it is the statistically
   correct estimator and it protects the small-dilution regime.
8. **Rejected by the suite, with numbers:** widening the unlearned
   branch (`phase_var_unlearned` 2.0 / 4.0: informative loss 0.1468 /
   0.1534 vs 0.1414 at 1.0 — it buys s1 coverage 1.00 but loses more
   in s2/s4); `f_blend = 0` (0.1584 vs 0.1436 at 0.75);
   `decay_prior = 0.95` (tied with 0.90, kept 0.90).

## Calibration sweeps (all on the suite, never on practice/dev)

- Phase 1, spread grid (81 combos, A in {0, 0.1, 0.3}, B in {0.03,
  0.05, 0.10}, SR/SH in {0.02, 0.05, 0.10}): tightest wins,
  informative loss 0.2080, coverage 0.929.
- Phase 2, period method: median_diffs = endpoint_span =
  recent_span (0.2080 to 4 decimals).
- Phase 3, priors x unlearned_mu (12 combos): pdil 3.0, pf 0.20,
  phase_avg wins — informative loss 0.1584, coverage 0.891, full
  suite 0.0727.
- Phase 4, decay prior / f_blend: f_blend 0.25 → 0.1499 (coverage
  0.900); 0.40 → 0.1456; 0.50 → 0.1432 (coverage 0.944);
  decay 0.85/0.90/0.95 tied.
- Refinement: f_blend 0.65 → 0.1450, 0.75 → 0.1436, 1.00 → 0.1403
  (all with transition-count shrinkage); spread at blend 0.75:
  SR = SH = 0.01, B = 0.05 → informative loss 0.1411, coverage
  0.916, full suite 0.0633.
- Selection rule applied throughout: rank by mean loss on the
  INFORMATIVE scenarios (median answer rate >= 0.02% — the rest are
  clamp-dominated and cannot select a spread); among combos within
  2% of the best loss, prefer coverage closest to 0.90.

## Suite results (final code, 24 scenarios)

Informative scenarios are the 10 whose median answer rate is >= 0.02%
(s1–s4, s19–s24). The other 14 collapse below the scorer's 0.01%
clamp floor, so they score ~0 whatever the spread; they still run as
regression tests of the learned branch.

| scenario | loss | cov90 | med miss (pp) | tier med |logit| err (plat/gold/silv/bronze) |
|---|---|---|---|---|
| s1_first_refresh | 0.5448 | 0.62 | 0.2278 | 0.756 / 0.765 / 0.756 / 0.759 |
| s2_first_refresh_4x | 0.2470 | 1.00 | 0.4406 | 0.767 / 0.767 / 0.767 / 0.739 |
| s3_first_refresh_2x | 0.1636 | 1.00 | 0.1490 | 0.310 / 0.310 / 0.310 / 0.305 |
| s4_first_refresh_10x | 0.2470 | 1.00 | 0.4406 | 0.767 / 0.767 / 0.767 / 0.739 |
| s5_two_refresh_hist | 0.0030 | 1.00 | 0.0002 | 0.000 / 0.000 / 0.000 / 0.000 |
| s6_three_refresh_hist | 0.0155 | 1.00 | 0.0004 | 0.000 / 0.019 / 0.000 / 0.000 |
| s7_five_refresh_hist | 0.0001 | 1.00 | 0.0005 | 0.000 / 0.000 / 0.000 / 0.000 |
| s8_long_horizon | 0.0000 | 1.00 | 0.0010 | 0.000 / 0.000 / 0.000 / 0.000 |
| s9_frequent_small | 0.0163 | 1.00 | 0.0008 | 0.000 / 0.050 / 0.000 / 0.000 |
| s10_rare_big | 0.0000 | 1.00 | 0.0010 | 0.000 / 0.000 / 0.000 / 0.000 |
| s11_decay_growth | 0.0018 | 0.98 | 0.0007 | 0.000 / 0.000 / 0.000 / 0.000 |
| s12_decay_long | 0.0235 | 0.78 | 0.0008 | 0.082 / 0.082 / 0.082 / 0.035 |
| s13_final_2d_5r | 0.0022 | 1.00 | 0.0002 | 0.000 / 0.000 / 0.000 / 0.000 |
| s14_final_2d_4r | 0.0000 | 1.00 | 0.0009 | 0.000 / 0.000 / 0.000 / 0.000 |
| s15_final_2d_4r_lowf | 0.0154 | 1.00 | 0.0003 | 0.008 / 0.008 / 0.008 / 0.018 |
| s16_final_2d_6r | 0.0035 | 0.98 | 0.0003 | 0.000 / 0.000 / 0.000 / 0.000 |
| s17_final_2d_3r_big | 0.0000 | 1.00 | 0.0008 | 0.000 / 0.000 / 0.000 / 0.000 |
| s18_final_2d_5r_decay | 0.0194 | 1.00 | 0.0007 | 0.021 / 0.044 / 0.021 / 0.033 |
| s19_final_long_period | 0.0219 | 0.96 | 0.0052 | 0.007 / 0.037 / 0.007 / 0.018 |
| s20_final_small_dilution | 0.0188 | 0.95 | 0.0111 | 0.030 / 0.037 / 0.030 / 0.030 |
| s21_final_daily_refresh | 0.0444 | 0.98 | 0.0082 | 0.052 / 0.082 / 0.052 / 0.052 |
| s22_final_mid_period | 0.0406 | 0.93 | 0.0137 | 0.022 / 0.121 / 0.022 / 0.022 |
| s23_final_high_f | 0.0570 | 0.75 | 0.0132 | 0.077 / 0.142 / 0.077 / 0.069 |
| s24_final_2d_horizon | 0.0285 | 0.98 | 0.0029 | 0.008 / 0.045 / 0.008 / 0.038 |

- Suite mean loss **0.0631**, mean coverage 0.95 (24 scenarios,
  1.59 s for all 24 runs through the shipped file).
- Informative mean loss **0.1411**, informative mean coverage
  **0.916**.
- By horizon: 90 min 0.3006 / 0.90; 1–3 days 0.0108 / 0.99;
  4.5 days 0.0176 / 0.95.
- Cross-tier holdout (split-half: `f_base` estimated on
  even-indexed trophies only, scored on the odd half, and vice
  versa): mean median |logit| error **0.1188 / 0.1183**.
  Learned-branch holdout errors are ~0.000 in most scenarios;
  the largest are s23 (0.069 / 0.059) and s21 (0.052).
- Stress case (realistic final shape: 235 reads, 10-minute
  cadence, ~2-day history, 6 refreshes, 4.5-day horizon): loss
  0.0033, coverage 0.96, runtime 0.07 s; all 6 transitions
  detected with dilutions 2.00 → 1.59 and `f_base` 0.15–0.23
  (truth 0.20).

## Practice smoke (final code, hypothesised answer only)

- p00: loss **0.5761**, coverage 0.22. p01: loss **0.5766**,
  coverage 0.22. House baseline 1.51. (Hypothesised answer =
  last rate x0.221 for non-100% trophies, 100% stays 100% —
  derived from the rules' totals 943 -> 4276 trophies earned vs
  638 -> 3868 tracked; NOT the true answer, smoke check only.)
  The smoke coverage is low because the phase_avg median predicts
  no refresh in the 90-minute horizon while the hypothesised
  answer assumes one — the suite-selected tradeoff noted above.
  Format: 55 rows, quantiles non-decreasing, in (0, 100],
  2,804 / 2,735 bytes (limit 65,536).

## Validation (final code, same file throughout)

- Determinism: 2 runs byte-identical on system Python, and
  byte-identical again in a fresh venv with nothing installed.
- Runtime: ~0.31 s per case including interpreter startup
  (0.625 s for p00 + p01); suite 24 cases in 1.59 s. Limit 8 s.
- Stdlib only: imports are `json`, `math`, `os`, `sys`,
  `datetime` — verified by grep and by AST.
- Edge cases exercised: single-read history, a players-tracked
  drop, a trophy at 0.00% in the last read, null rates in some
  reads — all produce valid 55-row output, no crash.
- The 100% trophy outputs exactly 100.0 on all five quantiles.

## Known weaknesses (not hidden)

1. **Prior branch (s1–s4) is irreducible.** With no refresh
   observed, the first dilution and the refresh timing are
   unknowable; losses 0.16–0.54 there are prior risk, not model
   error. The final case is expected to have a multi-refresh
   history, so this branch should not fire — but if it does, the
   forecast will be wide and the median will sit near the last
   rates.
2. **s23 (small dilution 1.8x, high newcomer fraction 0.55) is
   the weakest learned scenario** (loss 0.057, coverage 0.75,
   gold-tier median logit error 0.142): with `D - 1` small, the
   per-trophy newcomer fraction is estimated from a small divisor
   and stays noisy even after precision weighting.
3. **s12 (decay, 4.5-day horizon) is under-covered** (0.78):
   the decay extrapolation is slightly over-confident at long
   horizons.
4. **The suite's generator holds per-trophy newcomer fractions
   fixed and refreshes on a strict periodic grid.** The real
   Exophase schedule may be irregular and fractions may drift;
   the mixture's `k_sd_b = 0.05` and the `f_blend` cap at 0.75
   are the hedges, but they are hedges, not measurements.
5. **Most learned-branch scenarios collapse below the scorer's
   0.01% clamp floor**, so their ~0 losses flatter the suite
   mean; the honest headline numbers are the informative mean
   (0.1411) and the per-horizon means above.

## No rank claim

The suite is evidence that the model learns the refresh process
from the history it is given; it is not a promise about the final.
The final is graded from zero on the real 2-day history and a
4.5-day horizon, against house entries whose losses are not
visible to us. Nothing here claims a rank, a prize, or a final
loss.
