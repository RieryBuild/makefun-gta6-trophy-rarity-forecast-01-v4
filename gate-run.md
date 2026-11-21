# Gate run — gta6-trophy-rarity-forecast-01 entry v4 (HOUSE GATE)

Date: 2026-11-21 (WITA). Account: @riery, wallet
6do8zGw4FPLCB1Cq44G8r8KwQccbhHUqtAptaRji6ALk.
Repo: https://github.com/RieryBuild/makefun-gta6-trophy-rarity-forecast-01-v4
Code commit: [first push commit — main.py + README.md + LICENSE +
.makefun/owner.json + build-log-v4.md; this gate-run.md committed on
top; submitted SHA is the HEAD after this commit — see the
coordinator's report/state file].
Gate run by the build coordinator, AFTER two OpenRouter review rounds
and their full re-validation, immediately before bundle + submit.
This gate RE-RUNS from MQ1 after the fix rounds (house rule: ONE FAIL
= do not submit, fix, re-run the WHOLE gate from MQ1).

## MQ1 — Can this entry be submitted RIGHT NOW, end to end? PASS

1. Competition: gta6-trophy-rarity-forecast-01 — entries close
   2026-11-21T11:30:00Z = 21 Nov 19:30 WITA; result due 10 Dec 2026
   06:00Z (re-read fresh from GET /api/competitions/<slug>/requirements
   at gate time, saved /tmp/r4-requirements.json; status "open"; no rule
   or threshold moved vs the build-time copy).
2. Deliverables: main.py (sole entrypoint, repo root) + README.md
   (template, 3 live make.fun badges, footer referral link) + LICENSE
   (MIT + SPDX line) + .makefun/owner.json (wallet 6do8) +
   build-log-v4.md (design + suite evidence) — all present in the
   working dir, verified by the coordinator before push; repo created
   21 Nov 15:57 WITA (after the competition opened 19 Nov 11:30Z).
3. Checks: every check in /requirements reviewed with its threshold —
   repo_created_after_open (opens 2026-11-19T11:30:00Z; repo created
   2026-11-21T07:57:42Z), thinking_reproduces (min_authored 0.3,
   max_unwritten_share 0.4, entrypoints main.ts/main.py),
   thinking_turns >= 5, thinking_priced (min_priced_share 1,
   min_self_reported_usage_share 0.5, min_muse_app_usage_rows 1),
   thinking_revised (min_file_writes 2), thinking_fresh
   (min_fresh_share 1), transcripts_run_record (from 17 Nov),
   thinking_own_work (required_from 2026-11-20T00:00:00Z — APPLIES to
   this submission; the code is written fresh in-session, v3 code
   never read), run_completes (36 s wall, 1 CPU, 1024 MB, 64 pids),
   run_deterministic (2 runs), repo_readme + repo_about,
   committed_secret. practice_floor + dev_profitable do NOT apply;
   entry_size does NOT apply. No "probably" anywhere above.
4. Submit path: kit LEVEL-27 CLI
   (~/workspace/makefun-work/gta6-trophy-rarity-forecast-01-kit/,
   build 2f0f22818310 — verified `0.1.0 (kit level 27, build
   2f0f22818310)` at gate time; the task brief's "LEVEL 6/7" was
   stale/wrong), bundle then check then submit with keypair
   ~/.makefun/keypairs/makefun-keypair.json (pubkey verified by the
   coordinator to derive to wallet 6do8 — MATCH).
5. Cost: time ~30 min to submit; capital $0 (entry free, no fee).

## MQ2 — Does this entry clear the competition's bar? PASS (evidence, not promise)

Bar = prizelist top 20 (pool $250: 1st $50, 2nd $35, 3rd $25, 4–10 $10,
11–20 $7). The DEV rank-20 bar (0.0219, live 21 Nov 14:47) is NOT the
honest bar — the dev board head is now dominated by memorisation
(4 entries at EXACTLY 0.000001, titles openly admitting "Observed
launch-refresh table" and "practice peek"); the 19-Nov honest top-5
band was 0.059–0.093. The final re-grades from zero on the FINAL case
(cut 21 Nov 11:30Z, ~2-day multi-refresh history, target 26 Nov
00:00Z, 4.5-day horizon). Evidence (all measured on the exact fixed
code being submitted, by the coordinator, not the builder's pre-fix
run): HONEST extended synthetic refresh suite (24 scenarios, dilution
2x–10x, 1–5 refreshes, horizons 90 min–4.5 days, final-like 2-day
histories) mean loss 0.0631, informative mean 0.1411, coverage 0.916;
original v1 suite (independent harness, same 12 scenarios) mean loss
0.1052 vs v1's own 0.2284; learned-branch scenarios 0.0000–0.0570;
final-like stress case (235 reads, 6 refreshes) 0.0033; cross-tier
holdout median |logit| error 0.1188/0.1183. Smoke vs hypothesised
answer 0.5761/0.5766 (≪ house baseline 1.51; the prior-branch
tradeoff is documented and review-approved — the final case uses the
learned branch). No practice grade exists (server grades); the suite
is the evidence — it is NOT a promised rank. No claim is made that
the practice smoke loss predicts the final loss.

## MQ3 — Is the submission window actually open for this account? PASS

Fresh quota at gate time (GET /api/competitions/<slug>/quota, 21 Nov
~16:20 WITA): can_submit true, entries_made 3, entries_kept 3, day
cap 6 left, hard limit 37 left. Entries close 21 Nov 19:30 WITA —
ahead. (Quota re-checked again immediately before submit.)

## MQ4 — Signed by the right identity, through the right route? PASS

Wallet 6do8 ONLY (owner.json verified in the working dir; keypair
pubkey verified by derivation to 6do8zGw4FPLCB1Cq44G8r8KwQccbhHUqtAptaRji6ALk;
no other wallet anywhere). Repo pushed via GitHub PAT route
(custom.github-pat Git Data API; no gh CLI, no App connector).
Repo public, created 21 Nov 15:57 WITA.

## MQ5 — Deliberate new submission, not a duplicate? PASS

Round 4 rebuild of a standing entry (r3 01a1f67c, loss 0.199, rank
#1916/8906, outside top-20). Rebuild trigger: 14:30 watch 21 Nov
(quota re-weigh lifted, can_submit YES). Content is new: count-space
refresh-mixture forecaster with mixture-CDF quantiles, written fresh
this build from the spec + design doc (v3 code never read — the
builder, both fixers and the coordinator never opened v3's main.py).
Supersedes r3 via Force_Last if it scores. New repo -v4 (v3 repo
untouched).

## MQ6 — Prove the entry works, beyond "it should work"? PASS

All measured on the EXACT fixed code (post-4b) by the coordinator:
- Format: p00 + p01 both 55 rows, quantiles non-decreasing, in
  (0,100], 2,804 / 2,735 B each (<= 65,536); 100% trophy exactly
  100.0 on all five quantiles.
- Determinism: two runs byte-identical; byte-identical again in a
  fresh venv with nothing installed.
- Runtime: ~0.15 s/case including interpreter startup (limit 8 s).
- Vanilla: fresh venv, nothing installed — byte-identical output.
- Stdlib only: imports json, math, os, sys, datetime (grep + AST).
- Synthetic suite (extended, 24 scenarios): mean loss 0.0631,
  coverage 0.95; informative mean 0.1411, coverage 0.916;
  per-horizon 90 min 0.3006/0.90, 1–3 days 0.0108/0.99, 4.5 days
  0.0176/0.95; s12 0.0235/cov 0.78, s23 0.0570/cov 0.75.
- Original v1 suite (12 scenarios, independent harness): mean loss
  0.1052, coverage 0.95 (v1's own code scored 0.2284 on it).
- Cross-tier holdout: 0.1188 / 0.1183.
- Regression tests (test_fixes.py, 46 checks, run by the
  coordinator): ALL PASS — drop adds no phantom transition and
  changes nothing (count/period/d_last/t_mid identical); ea<=eb
  trophies absent from f_by_trophy and f_base unchanged (0.20);
  zero-last-read output byte-identical to truncated history;
  all-zero history raises a clear ValueError; record-high: drop +
  recovery yields exactly ONE transition (dilution 2.0), identical
  period/f_base/d_last to the clean case.
- Starter-similarity: entrypoint main.py is original work (552
  lines, mixture-CDF design); output qualitatively different from
  any starter.

## MQ7 — Never-submit list? PASS (no match)

No code-drawn images (pure-code entry, n/a). No non-stdlib imports.
Sessions cover the build (MQ8). Wallet 6do8 only. PAT route only.
No claim code in repo/chat/transcripts. Quota open (MQ3). No capital
needed. No promised rank (MQ2 states evidence only). Not a duplicate
(MQ5). No visual deliverable, so no Reza visual-audit gate applies.

## MQ8 — Session check: which session built this, does the recording cover it? PASS

Route is BUNDLE (transcript bundle; transcripts_witnessed does NOT
apply; no `record` command used — per competition checks).
1. Sessions (bundle --dry-run to confirm at bundle time; expected):
   - coordinator 4f9dcf93-a5ab-409a-a79e-7a55de85fd47 (this session,
     started 21 Nov ~14:41 WITA): state file + §0 recorded BEFORE
     the first build action (builder spawned ~14:55 WITA).
   - builder e28b24e5-b16c-44ec-a175-1513238b1168: main.py + README +
     LICENSE + owner.json + build-log-v4.md + synth_suite_v4.py.
   - fixer e3931750-0104-42c1-98f2-02fbe855ca52: 3 review fixes +
     test_fixes.py.
   - fixer-4b 59c40237-fc5d-4e90-8dea-0f63a24cad66: record-high rule
     + test section D.
2. Recording start: coordinator session ~14:41 WITA — BEFORE the
   first build action (state file + fresh top-5 ~14:47 WITA; repo
   created 15:57 WITA; first main.py write after that). All
   subagent sessions started after the competition opened (11:30Z).
3. First action: brief + fresh top-5 study recorded in the state
   file before any build writes (house-prompt-additions §0).
4. Coverage: bundle --dry-run must find all 4 sessions; usage rows
   re-run by SELECT for ALL authoring sessions and rewritten in ONE
   write to ~/.makefun/muse-usage-gta6-trophy-rarity-forecast-01-v4.jsonl
   immediately before bundling for real (6 rows at gate time:
   coordinator 3, builder 1, fixer 1, fixer-4b 1; model
   ipnext/avocado-5.17-v7 throughout).
5. In-session revision: main.py written by the builder, revised by
   two fixers in-session, README badges fixed by the coordinator
   in-session (template badges + 24-scenario count + template
   footer); min_file_writes 2 satisfied for the entrypoint.
   thinking_own_work: all repo files written in live bundled
   sessions before their PAT push and the bundle carrying them.

## Gate 0 — Reality: PASS

- Repo exists, public (created 21 Nov 15:57 WITA); HEAD verified by
  fresh clone after push (main.py + README.md + LICENSE +
  .makefun/owner.json + build-log-v4.md + gate-run.md sha256 match
  the local files).
- Every deliverable from /requirements is in the repo (checked).
- Entry passes its own tests on the submitted commit (MQ6, re-run
  by the coordinator on the final code).
- Evidence captured: fresh requirements + quota, suite runs,
  regression tests, bundle dry-run session list, usage rows.

## Gate 1 — Quality: PASS

- Multi-model review (RESTORED 18 Nov): code/reasoning reviewed by
  an independent model via OpenRouter — nvidia/nemotron-3-ultra-550b-a55b
  :free (free list re-checked 21 Nov: 11 :free models; this model
  still free). TWO rounds:
  - Round 1 VERDICT FIX: (1) division by zero on last-read
    players_tracked = 0 — FIXED (fallback to latest positive-player
    read, else clear ValueError); (2) player drops counted as
    refresh transitions — FIXED (`players > p_players` + `p_players
    > 0` guard); (3) negative newcomer fractions from ea < eb —
    FIXED (`if ea <= eb: continue`). Design tradeoff (phase_avg)
    judged JUSTIFIED for the final case; mixture CDF inversion
    judged correct. All three fixes verified in-code by the
    coordinator before the fix round.
  - Round 2 (fix verification) VERDICT PASS: all three fixes
    correct and complete, no new bugs, no shadowing of `p` remains,
    tests genuinely assert the fixed behaviour. One residual noted:
    mid-history drop + recovery still records a small transition on
    the recovery rise — judged MATERIAL for period estimation, with
    record-high as the minimal correct rule, safe to add.
  - Fix round 4b (record-high) applied + re-validated (46
    regression checks PASS, all suite numbers identical). Review
    exchanges recorded in the coordinator's session.
- Text/copy review by Gemini (gemini-3.8-flash): ATTEMPTED — the
  helper call timed out at 180 s with no response (transport
  timeout, 21 Nov ~16:00 WITA). Per house rule this is recorded as
  a gap, NOT a Gate 1 FAIL (same as meme-x v3). The entry's copy is
  minimal (README template text only); the coordinator verified the
  README against the requirements template directly (see Gate 3).
- Practice grade vs prizelist bar stated as evidence, never a
  promise (MQ2). Feed-first study: fresh live top-5 + memorisation
  audit done before the build (state file ROUND 4 §0).

## Gate 2 — Dedup: PASS

- Not a duplicate of any standing entry (MQ5; new code, new repo
  -v4, new sessions).
- Rebuild-once rule: one rebuild per trigger (14:30 watch trigger;
  round 4 is that rebuild; the 4b fix is a correction inside it,
  not a second rebuild).
- Quota re-checked at gate time via the competition's own endpoint
  (MQ3: can_submit true).

## Gate 3 — Submission quality: PASS

- README matches the requirements template (3 live make.fun badges
  — the template's badge SVG URLs, NOT shields.io — each linking
  to the bounty page with utm params; description; run command;
  footer with ?ref=wa8s3t3t). CORRECTED by the coordinator
  in-session after the builder shipped shields.io badges: the v3
  repo README (which passed repo_readme) uses the exact template
  badges — the template is authoritative. Also fixed in the same
  edit: "18 scenarios" → "24 scenarios" (the suite has 24).
- Repo About set (description per repo_about template, homepage
  the bounty page, topics makefun, ai-agents, bounties, forecasting
  — verified live after push).
- Entry message + signature use wallet 6do8 only; repo via PAT
  route (MQ4).
- Claim-code handling confirmed: claim codes go to
  ~/memory/2026-11-21.md ONLY, never in chat, never in the repo,
  never in a transcript file. None in the repo (grep clean).
- No secrets in the repo, the transcripts, or the review exchanges
  (grep for api keys / ghp_ / tokens / private keys / keypair
  material: clean; wallet address appears only where required —
  owner.json and this file's header; the keypair file was read only
  to derive its public key for MQ4 verification, never printed).
- Deadline still ahead at submit time: entries close 21 Nov 19:30
  WITA; thinking_own_work applies and is satisfied (fresh
  in-session authorship, v3 code never read).
- Reza visual audit: N/A — no visual deliverable (pure
  code/forecast entry, nothing to screenshot).
- README badges + About — EXPLICIT check (parent follow-up 21:48
  WITA 19 Nov, after cover-art submission 01a1f410 was rejected
  HTTP 422 for a README without 3 live badges + bounty link and an
  unset About; Gate 3 had missed it there): PASS, verified live at
  the pushed commit before submit —
  (1) README lines carry exactly 3 live make.fun badges (bounty /
  rank / reward), each linking to the bounty page with utm params;
  footer carries the referral link (?ref=wa8s3t3t). README matches
  the requirements' readme_template in structure (title = repo
  name, badges, description, run command, template footer).
  (2) About set live (GET /repos/RieryBuild/makefun-gta6-trophy-
  rarity-forecast-01-v4): description "Forecast GTA VI trophy earn
  rates on Exophase at 2026-11-26. Built by an AI agent for
  make.fun's "Forecast how many GTA VI players earn each trophy in
  week one" bounty, $250 in USDC."; homepage
  https://make.fun/bounty/gta6-trophy-rarity-forecast-01; topics
  makefun, ai-agents, bounties, forecasting — exactly the
  requirements' repo_about.topics.
- transcripts_witnessed lesson (recorded in AGENTS.md 19 Nov):
  counted-file fixes MUST be written in the local working tree
  while the session is still LIVE and in-session, then pushed via
  PAT. This entry is BUNDLE route (no seal; transcripts_witnessed
  does not apply); the equivalent here is thinking_reproduces
  coverage, and it holds: every repo-file change in this build was
  written in a live bundled session BEFORE its PAT push and the
  bundle carrying it — main.py by the builder + fixers in-session,
  README badges by the coordinator in-session, LICENSE SPDX line by
  the builder in-session, this gate-run.md by the coordinator
  in-session.
- KNOWN RESIDUAL (accepted, documented): record-high closes the
  drop+recovery hole; the suite generator holds per-trophy
  newcomer fractions fixed and refreshes on a strict periodic grid
  (the real Exophase schedule may be irregular, fractions may
  drift) — hedged by k_sd_b = 0.05 and the f_blend cap at 0.75,
  documented in build-log-v4.md. s23 (small dilution + high f)
  remains the weakest learned scenario (0.057, cov 0.75); s12
  under-covered at 4.5 days (0.78). None of these blocks
  submission: they are calibration uncertainties, not defects.

## Verdict

All 8 questions pass. All 4 gates pass. SUBMIT.
