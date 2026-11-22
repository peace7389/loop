# Part C (proposed, not built): follow-through on findings — 2026-11-22

Harness: `harness/loop.py`. Both agents are the local model Qwen/Qwen3.8-Flash-Next-FP8. New branch `review/followthrough-2026-11-22`
on top of A (findings) + B (test review in rounds). Flag `--followthrough on|off`, default off, stored in session.json flags. With the
flag off, code paths, answer format and instructions are identical to A+B. Not deployed.

## Rule 1: no untouched finding (harness)
- Stale: open, or "working" with nothing new linked, for `STALE_TURNS = 2` turns (A's existing clock, `finding_due`). Parked findings
  are never stale.
- Accepted as working on a stale finding (checked right after the answer is read, before B's review):
  1. a hypothesis in this turn's experiment whose guess's `about` named the finding;
  2. a "work" decision whose refs name a reading requested in this answer (by the T id it will get);
  3. a park with a non-empty reason;
  4. a close with refs that exist.
  A "work" decision with no refs does not count.
- Otherwise only the experiment is held (not run, not counted), with a note naming the stale findings ("a free lookup or a park with a
  reason is enough"). The other parts stand.
- `HOLDS_PER_FINDING = 1`: the next time, the finding is marked `ignored` and the experiment runs (no stall).

## Rule 2: link check (model)
- A link = a guess whose `about` names F*n*, with a tested hypothesis from that guess.
- Supervised arm: B's `REVIEW_SCHEMA` gains `finding_reason` (one sentence), then the box `explains_finding` (yes / no / none named).
  A "no" is a refusal in B's rounds, under B's feedback rules (no rule, no runs; measure@label cut). No extra call.
- Single-AI arm: one extra judge call per claimed link (reason, then yes/no); a "no" is asked again; still "no": the link is removed
  with a note, the hypothesis stays. 1-2 extra calls per claimed link.
- Never refuses for other reasons, never ranks findings.

## Records, figures, page
- New record type L*n* with `kind` in {stale, held, ignored, link}; a link record holds the finding, hypothesis, box, reason, who
  answered and the round; `by` kept.
- `session_figures.followthrough()`: stale, held, ignored, links claimed / accepted / refused / "from feedback" (links approved after a
  refused round); None without the flag.
- Page: a stale mark on the finding's bar, "ignored" at its end, refused links in the finding's history.

## Verification
All harness checks with the flag off and on; scripted checks: stale; each of the 4 accepted ways; held; ignored on the second time;
"work" without refs not counted; link accepted; false link refused and repaired (supervised); false link removed (single-AI). The held
note and the review form shown. s047 to s050 render unchanged. Instruction size reported, flag off and on.

## Open questions for the operator
1. A non-empty reason is enough to park (as in A); or should the harness refuse "it does not change the recommendation"?
2. "Links from feedback" read as links approved after a refused round: right?
