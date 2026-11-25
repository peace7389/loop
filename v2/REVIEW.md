# v2: sessions that are fair to measure

Branch `v2`, from main (05cb959). Nothing here is deployed. Base: `plans/2026-11-24-prompt-audit.md` and the operator's sheet of 2026-11-24,
with the seven corrections and three proposals the operator accepted. Each stage is one patch script in this folder (`s*.py`, run once from the
tree's root); every text a stage changed stands, before and after, in `texts_<stage>.md`.

## Decisions of the operator (2026-11-24)

New branch from main. One purpose: "Explain what decides <measure>, and say which settings (and network, where it may change) give the largest
<measure> within the brief's conditions." A8 in the narrow form, chain-rule refusals counted per session. "Follows" as a fourth box. "Cannot tell":
a fail with a required reason at the review, inconclusive at the ruling, counted per session. C1: say the truth (to look first, send requests
alone). C4/C5: `<` and `>` on the raw numbers; the note "decided by little" only between two measured results. B4: no earlier answers quoted at the
ruling, compared in code. Confirmation: 3 seeds at 5 times the measured time, under `checks/`, not shown to the agents. The page: only what the new
boxes and the confirmation result need. three-hosts-link-2: its limits change too. Nothing beyond these items. Run plan: one session per brief
first, with fairness audits, before the rest.

## Stages

| Stage | What | State |
|---|---|---|
| 1 | Neutral texts in both arms (A1, A2, A7, A10, A11, C29): `s1_neutral.py` | built |
| 1b | Briefs three-hosts-2, three-hosts-link-2; the chain rule's refusal says the open way (A8): `s1b_briefs.py` | built |
| 2, 2b | The supervisor: the competing guess at the ruling, every round shown, only the rule's simulations, "cannot tell", the box "Follows", no forced choice, no earlier answers quoted (B1 to B14, item 4, A9, B6): `s2_supervisor.py`, `s2b_lines.py`, `s2c_record.py`, `s2d_marks.py`, `s2e_figures.py` | built; every harness check passes on it (2026-11-24) |
| 3 | One purpose (A4), parking a finding inside the tolerance (A5), true statements from the code's constants (C1 to C13), what the other arms are told: `s3_true.py` (48 changes, `texts_stage3.md`) | built; every harness check passes on it and on main (2026-11-25: 33 pass, 3 skip parts that are in neither harness). The three viewer files it touches (the page's copy of the task sentence, the writer of a network's description) have had no page check yet: stage 6 |
| 4 | A brief with several moves, with reference runs: `briefs/three-hosts-moves.json`, `v2/ref/` | a candidate, with its reference runs (below); no session on it before the operator has seen them |
| 5 | The confirmation tool: `harness/confirm.py SESSION` | built; its check (`harness_checks/test_confirm.py`, copies of s059, s062, s006, s024, s007) passes |
| 6 | The page: the fourth box, "cannot tell", the confirmation result | not started |
| 7 | The text-audit script and the fairness checklist; figures in session_figures | not started |
| 8 | Checks of bad input; all harness checks; s047 to s061 rendered unchanged | not started |

## Found while building (for the operator)

- Stage 1: the harness already allowed the narrow form of A8 (a declared competitor may start from the records of the guess it competes with); only
  its refusal did not say so. No rule changed.
- Stage 1: an added link now states its rate and an added queue its kind (left empty they became the brief's cap and a scheduler: the best values
  in two briefs). Sessions before v2 hold changes written the old way; they are records and are not built again.
- Stage 1: how packets find their way is said once, by the harness, in the paragraph on changes of the network (every brief whose network may
  change), and no longer in one brief's description.
- three-hosts-link-2: limits 6 hosts, 6 links, 4 flows (they were 4, 4, 2). In this network a new link is still the one change that helps: the
  limits no longer single it out, but only the several-moves brief (stage 4) has more than one real move.
- after_fix (unchanged, in the run plan): its TCP flow is not among the locked objects, so it may be replaced by a TCP flow at a constant rate.
  The operator may want it locked in a brief after_fix-2.
- Stage 2: the fields `honest_foreseeable` and the like are gone from the ruling (B4): the harness compares the review's boxes with the ruling's and
  records `changed` (a question the review passed and the ruling does not). The second question that made the supervisor choose which guess a result
  fits is gone (B1): each guess is said to fit, not to fit, or "cannot tell", by itself.
- Stage 2: a guess is refuted through a ruling only where the review's box Follows passed (`guess_refutations`); a ruling recorded before the box
  existed counts as before, so s047 to s061 read unchanged.
- Stage 2: the scripted supervisor of the harness checks (`harness_checks/scripted.py`, outside the repository) fills in Follows for scripts written
  before it; the checks that state their own answers keep them.
- Stage 2d: the refusal of a new link without a rate said "(for example 1Gbps)": an example value is a pointer, so it is gone. The mark of a
  refuted guess said "on a hypothesis that follows from it" for every refuted guess; a competing guess is refuted another way (the supervisor
  found that it does not fit the result of a fair test), and its mark now says that.
- Stage 2e: the session's figures (`session_figures.competitor_figures`) count, for a v2 session only: the box Follows, the boxes answered
  "cannot tell" (reviews of every round, rulings, the two fits), and by question the rulings that do not pass what the review passed (`changed`).
  A session before v2 gives the figures it gave.
- The harness checks (outside the repository) read which harness they run on: on v2 they check the new marks, `changed` in place of
  "foreseeable", no second question on the fits; two scripted sessions were added for the rule of item 4 (a refuted hypothesis the review did
  not find to follow from its guess leaves the guess standing, and the same test with Follows passed refutes it) and one for "cannot tell" (it
  sends a test back at the review, makes a ruling inconclusive, and is counted). The same files still pass on the live harness.
- Stage 3: the supervised researcher's instructions with competitors are 9,978 characters of the limit of 10,000 (they were 10,555 after the first
  version of the stage; room was made by saying nothing twice, see "room:" in `texts_stage3.md`). Any further sentence needs a cut.
- Stage 3 (C5, the operator's decision): the note "decided by less than the tolerance" stands only between two measured results. On a real session:
  in s031 the check of H11 (a measured result against a number its rule copied from an earlier result) was marked on main and is not on v2; H12 and
  H16 (two measured results each) are marked as before.
- Stage 3 (C11): the texts said a finding's name has at most five words and the code cut at six; the code now cuts at the constant the texts are
  written from (`NAME_WORDS` = 5).
- Stage 3 (A5): a finding parked with a reason does not hold the report back (it comes back after `PARK_TURNS` turns as before); whether the reason
  was a fair one is read in the fairness audit, not judged by the code.
- The text an old session's researcher would read (`loop.render`) is, on all 60 recorded sessions, the same on v2 as on main but for two notes at the
  end of a check's line, both reworded on purpose: what the rule was declared to give under the competing explanation (stage 2, A9) and the note on a
  difference inside the tolerance (stage 3, C4). The records are not touched; it shows only if an old session is continued on v2. The three harness
  checks that compare old sessions allow these two notes on v2 and nothing else.
- The harness checks brought in line for stage 3 (each reads which harness it runs on; the same files pass on main): test_arms, test_continue,
  test_design_rounds, test_findings, test_guess_restate, test_network, test_now_steps, test_supervised, test_task_text, test_tolerance.
- Stage 5: `harness/confirm.py SESSION` measures a finished session's answer again, apart from the session: its report's settings (and, where the
  network may change, its report's changes) with three seeds (the session's and the next two) at five times the measured time, into
  `checks/confirm/<session>.json` (each simulation's target and conditions with the numbers, whether the conditions hold in all three, the spread,
  what the session itself measured at that answer, what the report expects). Operator only: under `checks/`, named by no tool, text or instruction.
  Tried on copies of real sessions: the answer of s059 (three-hosts) met fb_loss_frac <= 0.1 over 5 s and does not over 25 s (10.5 % in each of the
  three seeds), as the audit of 2026-11-24 had found by hand; s062 and s006 hold.

## Stage 4: the candidate brief `three-hosts-moves` and its reference runs (2026-11-25)

The network and the three settings of `three-hosts-2` (a scheduler on r's side of lc, fa's part a setting; fb is UDP at 80 Mbit/s over a link of
100 Mbit/s; the aim: the largest fa_goodput_bps with fb_loss_frac <= 0.1), and the network may change: at most 6 hosts, 6 links, 4 flows; the four
hosts, three links and two flows it has are locked; a link a change adds carries at most 90 Mbit/s. 20 simulations, 4 in one experiment. The
description is that of three-hosts-2, word for word; it names no change.

Reference runs (the built program through the harness's own run path, in a scratch folder, 5 s measured, seed 1; `v2/ref/`):

| What is changed | fa goodput, Mbit/s | fb loss | Condition |
|---|---|---|---|
| nothing (the network as given, defaults) | 48.20 | 38.81 % | not met |
| a setting alone: fa's part 0.17 (0.18: 10.02 %, not met; 0.15: 22.32 with 5.86 %) | 24.46 | 8.67 % | met |
| the scheduler removed (a plain queue) | 17.86 | 0.30 % | met |
| the scheduler replaced by codel / red / pie / pfifofast | 17.90 / 19.51 / 17.83 / 17.86 | 0.40 / 2.39 / 0.27 / 0.30 % | met |
| the scheduler replaced by fqcodel | 48.20 | 38.75 % | not met |
| a new link a-c at 90 Mbit/s (fa takes it) | 86.77 | 0.00 % | met |
| a new link b-c at 90 Mbit/s (fb takes it; fa has lc alone) | 96.40 | 0.00 % | met |
| a new link b-c at 85 / 80 / 75 / 70 Mbit/s | 96.40 | 0.00 / 2.10 / 8.22 / 14.34 % | met / met / met / not met |
| both new links, the scheduler removed | 86.77 | 0.00 % | met |
| on the link b-c at 90: fa NewReno / BBR / Vegas | 96.40 / 96.40 / 82.86 | 0.00 % | met |

So four kinds of move meet the condition and give different results: a setting alone (24), another queue (18 to 20), a link for fa (87), a link
for fb (96). The largest needs the less direct move: the new link is slower than lc, so the other flow goes on it. With the new link, fa's part and
the scheduler make no difference; both new links with the scheduler kept cannot be built (no flow passes it), and the harness says so.
With three seeds at 25 s measured each figure is the same to the last digit shown but for the plain queue (17.85 to 17.88; fb loss 0.28 to 0.31 %).
The scheduling policy (share or cap) makes no difference in a network brief (48.20 against 48.27 at the defaults, every other row the same).
With a new link of at most 60 Mbit/s only one move is left (a-c: 57.84; b-c loses 26.57 % of fb), so 90 was taken.

Open for the operator: whether 90 Mbit/s and these limits are the brief to run; whether the given network should break the condition at its
defaults (as in three-hosts-2) or meet it (a plain queue as in three-hosts-link-2: 17.86 at the start, and no setting for fa's part).
