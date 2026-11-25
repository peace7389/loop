# v2: sessions that are fair to measure

Branch `v2`, from main (05cb959). Nothing here is deployed. Base: `plans/2026-11-24-prompt-audit.md` and the operator's sheet of 2026-11-24,
with the seven corrections and three proposals the operator accepted. Each stage is one patch script in this folder (`s*.py`, run once from the
tree's root); every text a stage changed stands, before and after, in `texts_<stage>.md`.

## Where it stands: deployed on 2026-11-25 at 16:30 at the operator's word, tagged `v2` (it was ready at 16:20)

**The state of the checks**, all on one copy of this branch's files (harness, page, briefs as committed):

- every harness check (`~/research/tools/harness_checks`, scripted sessions, no model): 36 pass, 3 skip parts that are in neither harness
  (measurements of relations, the short format, taps). They include the checks written for v2: `test_confirm`, `test_fairness`,
  `test_bad_input`, and sections R, S, T and the new G of `test_stage5`. The checks changed for v2 read which harness they run on and pass on
  main's as well.
- the page's own check of v2 (`evidence_checks/ev_v2.py`): 139 points pass. On every supervised session the guesses the page shows as refuted
  are those `loop.guess_refutations` gives; 20 sessions recorded before v2 (one AI and supervised, s006 to s062) read word for word the same
  on v2's page as on main's, on the full and on the lean page, hover texts included.
- the page checks of what v2 touches, on a scratch copy of these files: the set-up page and the builder (`ev_readable`, `ev_usable`,
  `ev_settings`, `ev_run`, `ev_build`, `ev_net`), a session's page (`ev_page`, `ev_test` on s006, `ev_bar`, `ev_home`), the lean page, the
  words, the board, the layout (`ev_lean`, `ev_words`, `ev_board`, `ev_polish`): all pass. Four of them first failed: three expected main's
  wording or the form's old first choice (the task sentence with "while", a session of one AI started from the form) and were brought in line;
  the fourth found stage 10 below. The whole page suite (about 90 minutes, mostly parts v2 does not touch) runs after this report, as a
  follow-up that does not hold the deploy back (the operator, 2026-11-25: the long runs are not all necessary).
- Stage 10 (`s10_page_tolerance.py`), found by `ev_usable checked`: the page worked out for itself which checks were decided by less than
  the tolerance, by the rule the harness had before v2. On a session of v2 it would have marked checks the harness did not mark. It now shows
  the harness's own mark from the check's record (kept there since 2026-11-15) and works it out only for sessions recorded before that. The 20
  sessions compared word for word read as before.

**The size of the instructions** (characters; main -> v2): the supervised researcher with competing guesses 9,782 -> 9,978 of the limit of
10,000; the paragraph on changes of the network 2,373 -> 3,347 (every change at the same depth, every kind of queue described); `prompt.txt`
(one AI) 19,258 -> 19,336; the arm "plain" 10,524 -> 10,598; the supervisor's instructions 1,530 -> 1,606.

**Every text changed**, before and after: `v2/texts_stage1.md` (17), `1b` (3), `2` (32), `2b` (3), `2c` (1), `2d` (4), `2e` (3), `3` (53),
`6` (17, the page), `7` (2, no text changed), `7b` (5), `7c` (4), `8` (1), `8b` (6), `9` (7), `10` (1, the page).

**To deploy** (only at the operator's word; no session running): merge this branch into main; copy this branch's `HARNESS_SPEC.md` to
`~/ADRS/openevolve/HARNESS_SPEC.md` before `snapshot.sh` (it copies from there); restart the control server (tmux `control`); look at
`/api/status` and the page; tag `v2`, push main and the tag. After the tag the texts the agents are sent and the harness's rules are not changed
(a repair of the page would change neither). Then the run plan: one session for each of `after_fix-2`, `three-hosts-2`, `three-hosts-link-2`,
`three-hosts-moves`, each with `harness/fairness.py` and `harness/confirm.py`, before the rest.

## After v2.1 (2026-11-25, evening): Follows in two parts, and the crash of s064

`s12_follows.py`, `texts_stage12_follows.md` (5 changes), from the operator's sheet: Follows has two parts. (1) Strictly: the hypothesis is
about a measure the guess speaks about, in the direction the guess requires; fail if not. (2) The number is the researcher's choice: fail only
if it lies clearly outside what the guess could give, and say why. The review's answer has a field for the part that failed, and the review's
record keeps it (`follows_part`: "measure or direction", "number", or "not said"). Honest is as the sheet asks since the wording of 18:46 (it
fails only if every value the rule compares already stands in the records; the same in the question asked after the run).

s064 (the operator's, brief `three_hosts_neutralprompts`, 18:50) ended in turn 1 with "harness error: KeyError: 'no_cause'": the supervisor
refused a guess for saying that something makes no difference without naming a cause, and the refusal looked the reason up in the list of a
session without competing guesses, which has no such reason. In the harness since 2026-11-23; no session had met it. The refusal now finds the
sentence of every reason; the check `test_stage5`, section U, plays the case.

## v2.1 (2026-11-25): Honest and Follows reworded, at the operator's word after s063

`s11_v21.py`, `texts_stage11_v21.md` (6 changes; only the supervisor's questions). **Honest** failed every test that compares a new run with an
earlier one ("Pass only if no value its rule compares ... already stands in the records"): now it fails only if every value the rule compares
already stands there. **Follows** failed any hypothesis with a number or from a hedged guess ("would have to expect what the hypothesis says"):
now someone who held the guess would expect this result, in its direction and rough size, and a stated threshold follows if the guess expects
the result beyond it.

How the 15 reviews of s063 come out (`replay_s063.py`: each request as the supervisor was sent it, asked again three times with the questions
as they were and three times with v2.1's; only answers are kept). The boxes are Follows, Honest, Consistent, Correct; P pass, F fail, C cannot
tell; "would run" = all four pass:

| Turn | Test | Recorded in s063 | As it was, three askings | would run | v2.1, three askings | would run |
|---|---|---|---|---|---|---|
| 2 | H1, round 1 | FPPC | FPPC FPPC FPPC | 0 of 3 | CPPC PPPC FPPC | 0 of 3 |
| 2 | H1, round 2 | FPFP | FPFP FPFP FPFP | 0 of 3 | FPFP FPFP FPFP | 0 of 3 |
| 2 | H1, round 3 | FPFP | FPFP FPFP FPFP | 0 of 3 | FPFP FPFP FPFP | 0 of 3 |
| 2 | H2, round 1 | PPPP | PPPP PPPP PPPP | 3 of 3 | PPPP PPPP PPPP | 3 of 3 |
| 2 | H3, round 1 | PPPP | PPPP PPPP PPPP | 3 of 3 | PPPP PPPP PPPP | 3 of 3 |
| 4 | H4, round 1 | FPFC | FPFF FPFF FPFF | 0 of 3 | PPFC PPFF PPFC | 0 of 3 |
| 4 | H4, round 3 | FPFF | FFFF FPFC FPFP | 0 of 3 | FPFC PPPP FPFC | 1 of 3 |
| 4 | H5, round 1 | FPFC | FPFF FPFF FPFF | 0 of 3 | FPFC FPFF FPFC | 0 of 3 |
| 4 | H5, round 2 | FPFC | FPFF FPFC FPFC | 0 of 3 | FPFF CPFC FPFF | 0 of 3 |
| 5 | H6, round 1 | FPPC | FPPC PPPP FPPC | 1 of 3 | PPPP PPPC PPPC | 1 of 3 |
| 5 | H6, round 2 | FPPC | FPPF FPPC FPPC | 0 of 3 | FPPC FPFC PPPC | 0 of 3 |
| 5 | H7, round 1 | PPPP | FPPC FPPF FPPF | 0 of 3 | FPPC PPPP PPPP | 2 of 3 |
| 5 | H8, round 1 | FFPP | FPPP FPPP FPPC | 0 of 3 | PPPP PPPP PPPP | 3 of 3 |
| 6 | H10, round 1 | PPPP | PPPC PPPP PPPP | 2 of 3 | PPPP PPPP PPPC | 2 of 3 |
| 6 | H9, round 1 | PPPP | PPPC PPPP PPPP | 2 of 3 | PPPP PPPP PPPC | 2 of 3 |

Of 45 askings each: Follows passes 13 as it was and 26 with v2.1; Honest 44 and 45; Consistent 27 and 27; Correct 20 and 23; a test would run
in 11 and in 17. H8 (a new run against an earlier one) would run in 0 of 3 as it was and in 3 of 3 with v2.1; H6 passes Follows in 3 of 3
(1 of 3 as it was) and still stops at Correct twice; H5 fails Follows under both, rightly (its guess says nothing of the kind of queue it
compares with). No review comes out worse under v2.1.

**The supervisor does not repeat itself.** Asked the same request three times with nothing changed, it gave the same four boxes each time in 7
of the 15 reviews (v2.1: 5 of 15). Most of the difference is in Correct ("cannot tell" against fail or pass). H7 was approved in the session
and passes in 0 of 3 askings as it was. Whether a test runs is in part chance; this is left with the operator (spec 15, item 14a).

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
| 4 | A brief with several moves, with reference runs: `briefs/three-hosts-moves.json`, `v2/ref/` | built; the operator saw its reference runs (below) and kept it as built (2026-11-25) |
| 5 | The confirmation tool: `harness/confirm.py SESSION` | built; its check (`harness_checks/test_confirm.py`, copies of s059, s062, s006, s024, s007) passes |
| 6 | The page: the fourth box, "cannot tell", the confirmation result: `s6_page.py` (17 changes, `texts_stage6.md`) | built; its check `evidence_checks/ev_v2.py` passes on a scratch copy (2026-11-25); the full page suite on the whole tree: see stage 8 |
| 7 | The text-audit script and the fairness checklist; figures in session_figures: `harness/text_audit.py`, `harness/fairness.py`, `checks/fairness/CHECKLIST.md`, `session_figures.fairness_figures`; `s7_figures.py`, `s7b_found.py`, `s7c_found.py` | built; its check (`harness_checks/test_fairness.py`) passes; the report of the texts: `plans/2026-11-25-v2-text-audit.md` |
| 8 | Checks of bad input; all harness checks; s047 to s061 rendered unchanged: `s8_found.py`, `s8b_found.py`, `spec_v2.py`; `harness_checks/test_bad_input.py`, section T of `test_stage5.py` | see "The state of the checks" below |

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
- Stage 6, the page, only what the new boxes and the confirmation need: Follows stands first on the line of a review's questions where the record has
  it; "cannot tell" is a third answer with a look of its own (not the colour of a fail) and a sentence on hover saying what it means at a review
  and at a ruling; a guess the supervisor could not tell to fit a result is said so and is not shown as refuted; a guess is shown as refuted by
  the harness's own rule (not through a hypothesis the review did not find to follow from it), and its sentence says how it was refuted; the
  confirmation of the answer stands under "Recommended configuration", marked as the operator's, not printed, and absent in the replay before its
  last step. `control.py` gives each session's row `confirm` (whether the file exists).
- Stage 6, checked (`ev_v2.py`, reads only): on every supervised session, old and new, the guesses the page shows as refuted are exactly those
  `loop.guess_refutations` gives, by the same ruling; the eleven supervised sessions s047 to s061 read word for word the same on v2's page as
  on main's, on the full and on the lean page, hover texts included.
- main was merged into v2 on 2026-11-25 (the board's simulations, the set-up page starting with a researcher and a supervisor, s062).
- Stage 7: `session_figures.fairness_figures` gives, for a session with a supervisor: the guesses refused by the rule of the chain, the boxes
  answered "cannot tell", in which round each test was approved, and whether the answer stands in turn 1 (each move of the report: simulated in
  turn 1, named in the words of turn 1, the turn that first simulated it). On the sessions so far: s047 first simulated its answer in turn 9;
  s058, s061 and s062 simulated and named theirs in turn 1.
- Stage 7: `harness/fairness.py SESSION` writes the figures (`checks/fairness/<session>.figures.json`) and, once, the audit's form with the 14 items
  of `checks/fairness/CHECKLIST.md`; the judgements are the auditor's and a form that exists is never touched.
- Stage 7: `harness/text_audit.py` writes out the texts as built for a brief in each arm, or as a session was sent them (its calls.jsonl: what
  was given, never what the model wrote), and marks examples that name a value, lists of choices out of alphabetical order, a kind of queue
  described at greater length or apart, and placeholders left unfilled. To build the texts without a session, the lines of `main` that make the
  instructions and the format are now the function `loop.built_texts` (the same lines in the same order; `texts_stage7.md`).
- Stage 7b and 7c, found by the text audit in v2's own texts and fixed: an example rate in the line on a new link ("for example 1Gbps"); the
  scheduler named before the list of the kinds of queue and apart from it; "checks, verdicts" in the answer format of the arms that have neither;
  the TCP types of the three briefs of v2 with the default first (now alphabetical). After the fixes nothing in v2's own texts is marked; the
  list of TCP types of `after_fix` is (the brief is left as its sessions read it: the operator's to decide).
- Stage 8, wrong input from the researcher on a network that may change (`test_bad_input.py`, twelve wrongly written changes): each is refused
  with its reason and nothing raises. Found: a network whose scheduler no flow passes (two new links took both flows off its link) was refused
  with "put it on the side that sends, or use a plain queue", a suggested change; it now says what is wrong and no more. The change a refusal
  ends with, to show the form, takes a queue out and puts the same kind back (after_fix: a plain queue; three-hosts-moves: its own scheduler).
- Stage 8, wrong answers of the supervisor (section T of `test_stage5.py`): a box answered with a word that is no answer is a fail; a box left
  out is asked about once more; a fit answered with a word that is no answer is not recorded and refutes nothing. Found and fixed: "cannot tell"
  with an empty reason reached the researcher as "Honest could not be told: " and nothing after it (now: "(the supervisor gave no reason)"); a
  missing reason was recorded as the word "None"; an answer that is JSON but no object stopped the session with an error of the harness's own
  (now read as an answer that cannot be read: a review's test is run unreviewed with a note, a ruling is asked for again, as before).
- The build specification on this branch (`HARNESS_SPEC.md`) describes v2: 8.10, 10.10, 10.11, 12.1, 15 item 14, 16. At the deploy it is copied
  to `~/ADRS/openevolve/HARNESS_SPEC.md` before `snapshot.sh` runs (which copies from there).
- Stage 9, the operator's decisions of 2026-11-25 ("Do as you recommend") on the three questions left (`s9_decisions.py`, `texts_stage9.md`):
  (1) `three-hosts-moves` stays as built: it differs from three-hosts-2 in one thing, that the network may change; (2) the brief `after_fix-2`:
  after_fix with its TCP types in alphabetical order and its TCP flow locked (in after_fix the flow can be taken out and put back as a TCP flow
  at a constant rate: tried, accepted there, refused in after_fix-2); after_fix and the operator's after_fix2 stay as their sessions read them;
  (3) a review that cannot be read is asked for once more and, unreadable again, counts as "cannot tell" in every box: the test is sent back
  (it ran unreviewed: it then had no answer to Follows, and its guess could be refuted through it, against item 4). The figures count such
  reviews (`unread_reviews`).

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

Decided by the operator on 2026-11-25: the brief stays as built (90 Mbit/s, these limits, the condition not met at the defaults as in
three-hosts-2).
