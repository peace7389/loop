# Part D (proposed, not built): guess refusals and the cascade, arm "supervised" — 2026-11-22

Harness: `harness/loop.py` (ns-3 research loop). Both agents are the local model Qwen/Qwen3.8-Flash-Next-FP8: a researcher that proposes,
and in the arm "supervised" a supervisor asked apart from it. Would be built on branch `review/harness-2026-11-22`, after parts A (findings)
and B (test review in rounds) are committed. Not deployed.

## The problem
Most guess refusals come from the supervisor's defect "not_from_what_was_learned" (the chain rule that went live on 2026-11-22). In s050
turn 6 it refused a guess because new readings "only quantify" an earlier guess, which is good research, not a repeat. A refused guess
also takes down, in the same answer, every hypothesis built on it and then the experiment (nothing left to test): s051 ran 8 turns with
0 simulations, then 2 in turn 9 (stopped by the operator).

## Counts from the recorded guess reviews

| Session | Guesses stated | Refused today | Refused under the new rule | Fell with the refused guesses (same turn) |
|---|---|---|---|---|
| s047 | 20 | 1 (not_in_the_records) | 1 (unchanged) | 1 hypothesis, 1 experiment |
| s050 | 14 | 3 (all not_from_what_was_learned) | 0 | 1 hypothesis |
| s051 | 9 | 4 (3 not_from_what_was_learned, 1 not_in_the_records) | 1 | 6 hypotheses, 1 experiment |

s048 and s049 ran in the single-AI arm, which has no supervisor reading guesses.

## Proposed changes
1. **not_from_what_was_learned becomes a recorded warning, not a refusal.** The guess is accepted; its review record says "accepted with a
   warning: ..." and the researcher reads it next turn. Chosen over "accept only if it revises the earlier guess", which would still refuse
   every refinement the researcher forgets to mark. The harness's own rule (a second guess from the baseline alone, nothing learned since)
   stays.
2. **Instructions** (arm "supervised"): one sentence: "A guess that states an earlier one more exactly (new numbers, a narrower cause) names
   it in revises." Its instructions are at 7,977 of 8,000 characters: one sentence elsewhere is trimmed to fit.
3. **The cascade fix**, for the refusals that remain (not_in_the_records, repeats, ignores_a_ruling):
   - one short call to the researcher in the same turn: the refused guess and the supervisor's reason, asking for the guess restated;
   - the existing rule already accepts a guess stated a second time about the same records, marked "contested", so its hypotheses and
     the experiment go ahead in that turn, linked to the restated guess;
   - cost: 1 researcher call + 1 supervisor call per refused guess;
   - a guess whose `about` names ids that do not exist keeps the valid ones (with a note) instead of being refused outright.
4. **Checks**: a guess with not_from_what_was_learned accepted with the warning; a refused guess restated in the same turn, its hypotheses and
   test going ahead; unknown ids in `about` dropped with a note; every harness check again; s047 to s051 render the same ledger text.

## Open question for the operator
Go ahead with this, including the same-turn restatement in (3)?
