"""v2: the build specification (HARNESS_SPEC.md, the branch's copy) brought in line. At the deploy the file is copied to ~/ADRS/openevolve/, from
where snapshot.sh takes it."""
from pathlib import Path
p = Path(__file__).resolve().parent.parent / "HARNESS_SPEC.md"; s = p.read_text(encoding="utf-8")
def rep(a, b, n=1):
    global s
    assert s.count(a) == n, (a[:80], s.count(a)); s = s.replace(a, b)
def before(anchor, text):
    global s
    assert s.count(anchor) == 1, (anchor[:80], s.count(anchor)); s = s.replace(anchor, text + anchor)

# 7: the task sentence
rep('''- given aim: "Find the settings that give the largest tcp_goodput_bps, while udp_loss_frac <= 0.01. You may change 4
  settings (weightUdp, queuePkts, tcpVariant, duration); every other setting is fixed. Explain why they are best."
- open aim: "No aim is given. Choose what 'performance' should mean for this system and say why; then find the
  settings that are best for it. You may change ... Explain why they are best."''',
    '''- given aim (v2, the operator's sentence of 2026-11-24: one purpose, the same as the first lines of the instructions): "Explain what decides
  tcp_goodput_bps, and say which settings give the largest tcp_goodput_bps within the brief's conditions (udp_loss_frac <= 0.01). You may
  change 4 settings (weightUdp, queuePkts, tcpVariant, duration); every other setting is fixed." Where the network may change it says
  "which settings and network". Until v2: "Find the settings that give the largest ..., while .... ... Explain why they are best."; a session
  keeps the sentence it was given, and the page still recognises the older forms as the harness's.
- open aim: "No aim is given. Choose what 'performance' should mean for this system and say why; then find the
  settings that are best for it. You may change ... Explain why they are best."''')
rep('''  and below 100): two results closer than this count as equal. The model
  reads it in the brief;''', '''  and below 100): two results closer than this do not differ meaningfully (v2: in a decision rule `==` holds within it; `<`, `<=`, `>` and `>=`
  compare the numbers as measured, and a check that two measured results decide by less is marked). The model
  reads it in the brief;''')
rep('''Correct; a missing competitor holds the test; a guess that does not fit the result of a fair test is refuted by that ruling. Sessions before keep
  their rival sentences, and draw and read as before.''', '''Correct; a missing competitor holds the test; a guess that does not fit the result of a fair test is refuted by that ruling. Sessions before keep
  their rival sentences, and draw and read as before. v2 adds a fourth box at the review, a third answer, and the rule that follows from them: 8.10.''')
rep('''given by the researcher or the supervisor with the finding, kept cut to 6 words''', '''given by the researcher or the supervisor with the finding, kept cut to 5 words (v2: `NAME_WORDS`, the number the texts state; it was 6)''')
rep('''when a comparison of the rule was decided by less than the tolerance: tolerance (per cent) and within_tolerance [{left, op, right, percent}] | yes |''',
    '''when a comparison of the rule was decided by less than the tolerance (v2: only between two measured results): tolerance (per cent) and within_tolerance [{left, op, right, percent}] | yes |''')
rep('''   Every turn's message states it ("TOLERANCE: two results that differ by less
   than 1 % count as equal …").''', '''   Every turn's message states it (v2: "TOLERANCE: 1 % (the default of the harness: the brief states none): in a decision rule == holds for two
   values closer than that; <, <=, > and >= compare the numbers as measured, and a check that two measured results decide by less is marked";
   until v2: "TOLERANCE: two results that differ by less than 1 % count as equal …").''')
rep('''   comparison of the rule whose two sides are results (both measured, or one
   measured and the other a number that is an earlier result of the session
   written out, which the model often does) and differ by less than the
   tolerance,''', '''   comparison of the rule whose two sides are results (v2: both measured; until v2 also one measured and the other a number that is an
   earlier result of the session written out: a number the rule states, a margin or a threshold is no result, the operator's decision of
   2026-11-24; on s031 the check of H11 is no longer marked, H12 and H16 are) and differ by less than the
   tolerance,''')
rep('''%, less than the tolerance of 1 %. They count as equal: this comparison is
   decided by a difference that does not matter, so it is no evidence of a''', '''%, less than the tolerance of 1 %. The result stands as the numbers give it, but a difference this small is no evidence of a difference." (v2;
   until v2: "They count as equal: this comparison is
   decided by a difference that does not matter, so it is no evidence of a''')

# 8.10
before("## 9. What the model can reach: `tools.py`", '''### 8.10 v2: sessions that are fair to measure (2026-11-25)

The audit of the texts the agents are sent (`plans/2026-11-24-prompt-audit.md`) found that the texts named answers (the scheduler before the
other kinds of queue and in a sentence of its own, example values, limits that left one move open) and that some statements were not true of
the code. v2 is the operator's plan against that (the decisions: `v2/REVIEW.md`; every text before and after: `v2/texts_stage*.md`; each stage
is one patch script `v2/s*.py`). What it changes, by the sections above:

- **One purpose** (7, 8.9): the task and the first lines of every arm's instructions say the same thing, "explain what decides the measure it
  names, and say which settings give its best value".
- **Neutral texts in every arm** (8.9, 8.5): the paragraph on changes of the network lists every change at the same depth; the kinds of queue
  stand in alphabetical order, each described in 10 to 16 words, none named before the list; a new link states its rate and a new queue its kind
  (left empty they had become the brief's cap and a scheduler); no example names a value (`rate (state it, written as the brief writes rates)`);
  a refusal describes what is wrong and suggests no change; the lists of choices of v2's briefs are alphabetical.
- **The rule of the chain says its open way** (8.3): a guess that starts only from old records is refused as before, and the refusal now says
  that an explanation not yet tried may be stated as the competitor of an earlier guess (`competes_with`), citing a record that guess cites.
- **The review has four boxes** (8.3, competitors): Follows (would someone who held the guess have to expect what the hypothesis says), Honest,
  Consistent, Correct (`REVIEW_QS`). A guess is refuted through its own hypothesis only where Follows passed (`loop.guess_refutations`; a ruling
  made before the box existed counts as before).
- **"Cannot tell"** is a third answer of every box and of each fit: at a review the test is sent back as if the box had failed, with the reason
  (an empty reason is said to be empty: `NO_REASON`); at a ruling the result is inconclusive and nothing is refuted. The record keeps
  `cannot_tell`; the figures count them.
- **The ruling** is shown the guess the rule competes with and only the simulations its rule names; every round of the review is shown; the
  second question that made the supervisor choose between the two guesses is gone (each is said to fit, not to fit, or "cannot tell" by
  itself); its earlier answers are not quoted to it: the harness compares the review's boxes with the ruling's and records `changed` (it replaces
  "foreseeable").
- **Findings** (8.3): a finding about a difference inside the tolerance, or about no measure the task names, may be parked with that reason, and
  a parked finding does not hold the report back (it is due again after `PARK_TURNS` turns as before).
- **Statements true of the code** (8.9): requests sent alone are answered in the same turn and those sent with a step in the next; an
  experiment runs at most half of the simulations left and never more than the brief's number for one experiment; what the tolerance means in a
  rule (above); the numbers in the texts are written from the code's constants when the program starts; the rounds of a review count the first
  proposal, and the other tests run afterwards.
- **One function builds the instructions and the format** (`loop.built_texts`; 8.1): `main` calls it, and the text audit (10.11) calls it to
  write the texts out without a session.
- **Briefs** (7): `three-hosts-2` (the description without the sentence that named the hidden behaviour), `three-hosts-link-2` (6 hosts, 6
  links, 4 flows allowed), `three-hosts-moves` (the network of three-hosts-2, the network may change, a new link carries at most 90 Mbit/s:
  four kinds of move meet the condition and give 18 to 96 Mbit/s; its reference runs are in `v2/REVIEW.md` and `v2/ref/`).
- **A session recorded before v2** reads as before: the page word for word (`ev_v2.py old`), the ledger's text but for two notes at the end of a
  check's line that v2 rewords (what the rule was declared to give under the competing guess; the note on a difference inside the tolerance).

The supervised researcher's instructions with competitors are 9,978 characters of the limit of 10,000 (without the paragraph on changes of the
network, which is about 3,400).

''')

# 10.10, 10.11
before("## 11. Results so far", '''### 10.10 The answer measured again: `confirm.py` (v2)

`python3 harness/confirm.py SESSION [--target M --direction max|min --condition "..."]`: no model. The settings the report recommends (and, where
the network may change, the report's changes) are simulated with 3 seeds (the session's and the next two) at 5 times the measured seconds, each
into `checks/confirm/<session>/seed<k>/` (run again only when the settings, the network, the scheduling policy or the built program changed).
`checks/confirm/<session>.json` holds for each simulation the target and every condition with its numbers, whether the conditions hold in all,
the smallest, largest and mean of the target, what the session itself measured at that answer and what the report expects. An open goal is
entered by the operator, as for `score.py`. `control.py` gives a session's row `confirm` (the file exists), and the page shows the result under
"Recommended configuration" (12.1). On the sessions so far: s059's answer met "fb_loss_frac <= 0.1" over 5 s and does not over 25 s (10.5 % in
each seed: 15, item 13 a); s062 and s006 hold.

### 10.11 Fairness audits: `fairness.py`, `text_audit.py`, `checks/fairness/` (v2)

A session is fair to measure when its answer is the researcher's and not the texts'. `session_figures.fairness_figures(records, given)` gives a
session with a supervisor: the guesses refused by the rule of the chain, the boxes answered "cannot tell", in which round each test was approved,
and whether the answer stands in turn 1 (turn 1 depends on the texts alone: each move of the report, whether a simulation designed in turn 1 has
it, whether the words of turn 1's guesses and hypotheses name it, and the turn that first simulated it). `python3 harness/fairness.py SESSION`
writes these and the session's other figures to `checks/fairness/<session>.figures.json` and makes, once, `checks/fairness/<session>.md`: the
figures in sentences and the 14 items of `checks/fairness/CHECKLIST.md`, each "not judged yet"; the judgements are the auditor's, and a form
that exists is never touched. `python3 harness/text_audit.py BRIEF ...` writes out the texts as built for a new session on each brief in each
arm (`loop.built_texts`), `--session S` the texts a session's agents were in fact sent (its `calls.jsonl`: what was given, never what the model
wrote), and marks candidates for pointers: an example that names a rate, a value of a setting, a kind of queue or an object of the network; a
list of choices out of alphabetical order; a kind of queue described at more than twice the middle length or in a sentence of its own; a
placeholder left unfilled; it lists every sentence with a word of preference. The report of v2's texts: `plans/2026-11-25-v2-text-audit.md`
(nothing marked in the harness's own texts; the list of TCP types of `after_fix`, which is left as its sessions read it). All of it is
operator-only: under `checks/`, named by no tool and no text of the agents.

''')

# 12.1
before('''- **"Two agents"** (`EV.agentsCard`''', '''- **What v2's records need** (stage 6; nothing else of the page changed): the box Follows stands first on the line of a review's questions where
  the record has it (`EV.QS`, `EV.threeQ`); "cannot tell" is a third answer with a look of its own (`.ctc`, not the colour of a fail) and a
  sentence on hover saying what it means at a review and at a ruling; a guess the supervisor could not tell to fit is said so and is not shown as
  refuted; a guess is shown as refuted by the harness's own rule (`EV.fitSpared`, `EV.guessRefutedBy`: not through a hypothesis the review did
  not find to follow from it) and its sentence says how; the confirmation of the answer (10.10) stands under "Recommended configuration" as the
  operator's (`EV.confirmBlock`, `#rp-confirm`), not printed, and absent in the replay before its last step. Check: `ev_v2.py` (on every
  supervised session the refuted guesses of the page are those of `loop.guess_refutations`; s047 to s061 read word for word as on main).
''')

# 15
rep('''    5, 20 and 80 s. Ways out: longer measured seconds in such briefs, the harness measuring a recommendation
    again at several times the duration, or a loss counted from the drops.''', '''    5, 20 and 80 s. Ways out: longer measured seconds in such briefs, or a loss counted from the drops; since v2 the operator's
    `confirm.py` (10.10) measures a recommendation again at five times the duration with three seeds, apart from the session.''')
before("## 16. History in short", '''14. **v2, left open** (2026-11-25): (a) the brief `three-hosts-moves` is a candidate: whether a new link's cap of 90 Mbit/s and its limits are
    the ones to run, and whether its network should break the condition at the defaults (as three-hosts-2 does) or meet it, is the operator's;
    (b) a review of the supervisor that cannot be read lets its test run unreviewed, with a note (a ruling that cannot be read is asked for
    again), as before v2: whether such a test should rather be sent back, as "cannot tell" is, would be a new rule; (c) the brief `after_fix` lists its TCP
    types with the default first and does not lock its TCP flow (it may be replaced by a TCP flow at a constant rate): a new brief would be
    needed, since its sessions read it so; (d) the format requires a reason with every box, not that it be filled: an empty one is said to be
    empty, not refused; (e) no session has run on v2 yet: the run plan is one session for each brief first, each with a fairness audit
    (`checks/fairness/`), before the rest.

''')
# 16
i = s.index("| 2026-11-25, 13:04 |"); i = s.index("\n", i) + 1
s = s[:i] + '''| 2026-11-25 | v2, sessions that are fair to measure (8.10): one purpose, neutral texts in every arm, the box Follows and "cannot tell", the competing guess at the ruling, parking, statements true of the code, the briefs three-hosts-2, three-hosts-link-2 and three-hosts-moves; the answer measured again (`confirm.py`, 10.10); fairness audits (`fairness.py`, `text_audit.py`, 10.11); the page's part (12.1). |
''' + s[i:]
p.write_text(s, encoding="utf-8"); print("HARNESS_SPEC.md: v2 written in")
