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
| 2, 2b | The supervisor: the competing guess at the ruling, every round shown, only the rule's simulations, "cannot tell", the box "Follows", no forced choice, no earlier answers quoted (B1 to B14, item 4, A9, B6): `s2_supervisor.py`, `s2b_lines.py` | built; the harness checks are being brought in line |
| 3 | One purpose (A4), parking a finding inside the tolerance (A5), true statements from the code's constants (C1 to C13), what the other arms are told | not started |
| 4 | A brief with several moves, with reference runs | not started |
| 5 | The confirmation tool | not started |
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
