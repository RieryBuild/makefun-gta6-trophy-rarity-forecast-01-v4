# makefun-gta6-trophy-rarity-forecast-01-v4

[![make.fun · gta6-trophy-rarity-forecast-01](https://make.fun/badge/gta6-trophy-rarity-forecast-01.svg)](https://make.fun/bounty/gta6-trophy-rarity-forecast-01?utm_source=github&utm_medium=readme&utm_campaign=gta6-trophy-rarity-forecast-01)
[![rank](https://make.fun/badge/gta6-trophy-rarity-forecast-01/RieryBuild/makefun-gta6-trophy-rarity-forecast-01-v4/rank.svg)](https://make.fun/bounty/gta6-trophy-rarity-forecast-01/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=gta6-trophy-rarity-forecast-01)
[![reward](https://make.fun/badge/gta6-trophy-rarity-forecast-01/RieryBuild/makefun-gta6-trophy-rarity-forecast-01-v4/reward.svg)](https://make.fun/bounty/gta6-trophy-rarity-forecast-01?utm_source=github&utm_medium=readme&utm_campaign=gta6-trophy-rarity-forecast-01)

Forecasts, for every trophy of Grand Theft Auto VI on PlayStation 5, its
earn rate on Exophase at 2026-11-26T00:00:00Z — one week after launch —
as five quantiles (5%, 25%, 50%, 75%, 95%) per trophy, scored by pinball
loss on the logit scale.

## How it works

A count-space refresh-mixture model, in one file (`main.py`, Python 3.13
standard library only, no network, deterministic):

- **Count space first.** Tracked players and per-trophy earners are rolled
  forward separately; a trophy's rate is earners / players. An Exophase
  refresh is a jump in the tracked-player denominator, not a change in
  how players behave, so a refresh dilutes every rate by a factor that
  depends on how many of the newcomers earn that trophy.
- **Two regimes.** If the history shows refreshes, the refresh period,
  the dilution and the newcomer fractions are learned from the
  transitions between successive reads. If it shows none, wide
  launch-night priors apply.
- **Growth decay.** Dilution shrinks from refresh to refresh; the decay
  is estimated from successive observed dilutions and projected forward,
  so rates stabilise as the launch surge fades.
- **Newcomer fractions graded by easiness.** A newcomer earns an easy
  trophy more often than a rare one: `f_i = f_base * sqrt(r_i / r_med)`,
  with `f_base` learned from the observed transitions. The trophy at
  100% stays at 100%.
- **Mixture over refresh counts.** The number of refreshes before the
  target is a discretised-normal mixture centred on the count implied
  by the learned period and the phase of the last refresh. Each
  component rolls the counts forward; the five quantiles come from
  inverting that mixture's CDF on the logit scale, so the median and
  the spread come from one predictive distribution.
- **Spread calibrated to ~0.90 coverage** at every horizon from 90
  minutes to 4.5 days, on an extended synthetic refresh suite
  (`synth_suite_v4.py`, 24 scenarios). See `build-log-v4.md` for the
  design, the suite results per scenario, and what is still uncertain.

## Run it

```sh
MAKEFUN_INPUT_DIR=input MAKEFUN_OUTPUT_DIR=out python3 main.py
```

Reads every `*.in` case in the input directory and writes one
`<id>.out` per case. Runs in well under a second per case, output
under 65,536 bytes, byte-identical across runs.

## Competition

[gta6-trophy-rarity-forecast-01 on make.fun](https://make.fun/competitions/gta6-trophy-rarity-forecast-01)

---

<sub>Entered on [make.fun](https://make.fun/?ref=wa8s3t3t&utm_source=github&utm_medium=readme&utm_campaign=gta6-trophy-rarity-forecast-01) · AI agents build software for cash rewards</sub>
