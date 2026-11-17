# Two-hosts hypothesis harness — history and lessons

One place for what was done, what came out, and what was learned. Detail is elsewhere and is not repeated here:
`HARNESS_SPEC.md` describes the system as it is (section 16 has the dated list of changes, section 15 the open
items); the sessions themselves are under `sessions/`. A lesson is never deleted: when it turns out wrong it is marked
superseded.

## 1. What this is for

A language model, served locally, works as a researcher on a small network simulation it cannot see inside (two
computers, one link, a UDP and a TCP flow, a scheduler between them). Each turn it states hypotheses with a decision
rule written before the simulations run; the harness runs the simulations, checks the rules itself, and keeps every
record in a ledger; the page shows the whole trail to a reader. The aim is an honest demonstration for researchers of
what such a loop does and does not do. The operator's statement of the purpose (2026-11-15): the AI should not just
optimise settings from simulations but ask why; it should tell a meaningful difference from a marginal one; and when
no setting makes a meaningful improvement it should ask why rather than present a marginal gain as the best.

## 2. Timeline

| When | What |
|---|---|
| 2026-11-09 | First session (s001) on the first harness. |
| 2026-11-10 | Simulator revised (warm-up of 1 s, the seed matters, queue and retransmission measures). The harness shown in the viewer; a control server on port 8600. |
| 2026-11-11 | `RESTRUCTURE_PLAN.md`, stages 1 to 5: sessions, briefs, experiments of several simulations with rules the harness checks, the final report, sweeps with an answer key and a score. The evidence page. The project becomes a public git repository. Sessions s002 to s019. |
| 2026-11-12 | Stage 7: the specification rewritten as a whole. The page redesigned as one page for the whole cycle; views of verdicts against checks; polish. |
| 2026-11-13 | The overview redesigned. `FORMAT_FIX.md`: the model server writes an answer's fields in the format's order, so optional fields could make a setting unstateable; every design now states every knob. `NOTEBOOK_VIEW.md`: the notebook. Sessions s020 to s025. |
| 2026-11-14 | Simulator build 5 (each queue's own length). `READABLE_PAGE.md`: the page in eight numbered parts. The live view of a running session. A required "why" on every hypothesis. |
| 2026-11-15, night | Simulator builds 6 and 7 (TCP's first window and buffers, the device's transmit queue, the series written sample by sample). Tiles of the simulations being run. |
| 2026-11-15, day | A long run of small usability requests while sessions s029 and s030 ran (fields in the set-up cards, bars, hover boxes, one word per concept, nothing moves by itself). The session ran into its usage limit with five changes deployed by hand and nothing committed. |
| 2026-11-15, evening | The interrupted work completed and checked; four faults it had left were found by the full run and repaired. A test's detail cut to what it is for (a rule with an "or" as either-or lines). Session s031 on the operator's brief `trap` read closely, by the operator, by Claude chat and here: it led to the three harness changes of section 4, lessons A1 to A5. |
| 2026-11-17 | After the usage limit: the interrupted work completed (the page of 15 November checked as a whole and published; the report's parts "what limits the result" and "made no difference" tested and shown). The page shared with the lab: any account of the server through its own SSH tunnel, one session at a time, the page says who runs it. The task is now written by the harness, after the operator found that `trap`'s task contradicted its aim and settings. Briefs with the seed fixed. Two comparison arms built: the loop without the hypothesis format, and random search. |

## 3. Results (headline figures only)

- 31 sessions (s001 to s031), 989 simulations run, 459 decision rules.
- On the brief with a given aim (`two-hosts-udp-demand`) the scored sessions end within a tenth of a Mbps of the best
  row of a sweep of 2,190 settings (s004, s005: 0.075 Mbps under it; s006: 0.047 Mbps above it; s011: equal to it).
- In the 24 sessions that record what a hypothesis follows from: of 286 hypotheses stated after the first turn, 81 %
  name an earlier check or verdict, and 41 % of those a failed, refuted or inconclusive one (the model's own statement
  of what it built on); 64 % of their 414 checks held.
- Of the 459 decision rules of all sessions, worked out again, 112 rested on a comparison of two results less than 1 %
  apart. 37 of those compared a simulation with itself (the fault repaired on 2026-11-13, shown on the page as void);
  75 (16 %) compared two different simulations.
- Of 174 failed checks, 130 were followed by a verdict without a further test of that hypothesis (58 refuted, 72
  inconclusive).
- **The instructions of 2026-11-15 on the corrected `trap` brief** (`trap-2`, session s033, 2026-11-17: 6 turns, 15 of
  20 simulations). s031 on `trap` had recommended a TCP type for 0.02 % and a seed, and never asked what held TCP at
  419 Mbps. s033 asked it as a hypothesis ("What caps BBR TCP at about 419 Mbps?", then "Is BBR's plateau the 1 MB
  buffer divided by the 20 ms round-trip time?"), found it (1 MB / 20 ms = 419.4 Mbps; measured 418.9), listed the
  ratio, the queue length and the measured time as making no meaningful difference, and did not prefer one TCP type
  over another for a lead under 1 %. Three operator simulations agree with its diagnosis: with TCP's buffers at 1, 2
  and 4 MB, TCP goodput is 418.9, 595.6 and 658.3 Mbps. One session; the brief changed too (the task sentence, no
  seed), so this does not separate the instructions from the brief.
- **A first control experiment** (2026-11-17, brief `two-hosts-udp-demand-2`, policy share, 40 simulations allowed):
  three sessions with the hypothesis format (s034 to s036), three without it (`--arm plain`, s037 to s039), three
  random searches of 40 settings each. All five sessions that gave a report recommend the same settings, the brief's
  defaults (668.6 Mbps, 0.44 % under the best row of the sweep, inside the 1 % tolerance, as the instructions of
  2026-11-15 ask when nothing makes a meaningful difference), and all five name the same limit: the link is full, UDP's
  fixed 300 Mbps comes first, TCP gets what is left. The random searches reach 668.6 to 668.9 Mbps. With hypotheses:
  35, 30 and 25 simulations, three reports. Without: 40, 40 and 33 simulations, two reports (s038 used all 40 and gave
  no usable report). **On this brief the format does not change the answer**; it may save simulations, and three
  sessions an arm cannot show that. The brief is too easy to separate the arms: every setting within reach of a random
  draw is inside the tolerance.
- The seed: 53 settings were run under two or more seeds; TCP goodput differed by a median of 0.0002 %, at most 0.17 %.
  113 simulations (11 %) were spent on other seeds.

## 4. Lessons

Each: the lesson in plain words; *Evidence*; *What we changed*; *Status* (confirmed: measured, or the repair was seen
to work; partly: seen, the repair unproven; open: not settled). Nearly everything rests on single sessions.

### A. What the loop makes the AI do

**A1. Stating hypotheses and checking them makes the AI react to results. It does not make it ask why.**
*Evidence:* s031 (`trap`). By turn 3 the AI knew that neither the ratio nor the queue changes TCP goodput, and its
report says TCP is "capped by TCP congestion control/buffers". It never asked why the cap is 419 Mbps when 700 Mbps of
the link are free (1 MB of buffer over a 20 ms round trip gives exactly that; the brief states both). It spent 13 of 20
simulations comparing TCP types and seeds.
*What we changed:* the prompt now puts understanding before settings, asks every turn for what the results do not yet
explain, and says "ask why before you ask which" (spec 8.9).
*Status:* partly. No real session had run with it when this was written.

**A2. A difference of a few hundredths of a per cent gets treated as a finding unless something says it is nothing.**
*Evidence:* s031 recommended "TcpBic" over BBR for 0.02 %, and "seed 3". Over all sessions, 75 of 459 checks compared
two different simulations whose results were less than 1 % apart.
*What we changed:* a tolerance always holds (the brief's, or 1 %), every turn states it, and the harness marks each
check that was decided by less than it, in the record and in the line the model reads. The result of the rule is kept.
*Status:* the measurement is confirmed; the effect on the model is not yet seen.

**A3. A failed check is not yet a refutation: the test may be at fault.**
*Evidence:* s030, H1 ("the scheduler is work-conserving …") was judged refuted on a failed check; the cause was the TCP
type, which the session then found, and its report's first claim says what H1 said. A verdict closes a hypothesis, so
H1 stays refuted in the record.
*What we changed:* the prompt says to state why a check failed, to judge refuted only when the test was a fair one, and
otherwise to test again or say inconclusive. The harness has always allowed an open hypothesis to be tested again.
*Status:* partly. Guidance only; nothing enforces it.

**A4. The rival explanation has to stand beside the result, not some records earlier.**
*Evidence:* s031, H2 failed in turn 1. Its rival read "all TCP variants are capped by the same scheduler share or
buffer limit", which was the truth of the whole session. The rival stood only in the experiment's line.
*What we changed:* a check's line, as the model reads it, ends with the rival and whether it predicted this result.
*Status:* partly.

**A5. The seed is not a setting, and offering it as one costs simulations and invites false conclusions.**
*Evidence:* section 3; two reports recommended a seed.
*What we changed:* the prompt says what a seed is for. On 2026-11-17 the operator decided: new briefs with the seed
fixed at 1 (`two-hosts-open-2`, `two-hosts-udp-demand-2`, `trap-2`); the old briefs and their sessions stay.
*Status:* confirmed; changed for every session from now on.

**A6. A short measured window turns "how fast it starts" into "how good it is".**
*Evidence:* `trap` (10 ms link): Cubic climbs for about 12 s and is still climbing through a 10 s measurement; every
TCP type ends at the same 419 Mbps. "Which TCP type is best" was produced by the window.
*What we changed:* nothing yet. The simulator has a warm-up option that could become a setting of the brief.
*Status:* confirmed; the remedy is open.

**A7. The answer format decides what the model can say.**
*Evidence:* the model server writes fields in the format's order, so with optional fields a design that began with one
setting could not state another (2026-11-13). The report's recommendation was a fixed list of six optional settings: a
knob outside it could be tested and not recommended, and s030's recommendation lost three settings.
*What we changed:* designs and the recommendation are built from the brief, every knob required.
*Status:* confirmed (s020 to s025 ran clean after the first repair; scripted tests cover the second).

**A8. One sentence in the last turn's request caused seventeen refusals.**
*Evidence:* s030: "give your verdicts on hypotheses whose decision rules have been checked" was read as "judge every one
again".
*What we changed:* the request names the hypotheses that still need a verdict.
*Status:* confirmed by scripted tests.

**A9. The model does not plan for a limit it is only told about.**
*Evidence:* s030 used 12, 12, 11, 4 and 1 simulations and wrote that its optimum "was not finely swept".
*What we changed:* the prompt says to plan for the limit from the first turn.
*Status:* partly.

**A10. A text that is typed once does not follow the settings beside it.**
*Evidence:* the operator, reading `trap` on the page: "Is it okay that the task the AI is given stays the same
regardless of settings?" The task said "both at maximum rate" (UDP was fixed at 300 Mbps), "find the best ratio" (five
settings were open) and "say what 'performance' you chose to mean" (the aim was given). The set-up page had copied the
text from the brief it started from; s031 ran on it. The description had the same fault in one place ("the setting
udpRate" where it was fixed).
*What we changed:* the harness writes the task from the aim and the open settings (`tools.task_text`); the set-up page
shows that sentence and has no task field; a name in braces in the description reads as a value or as "the knob …".
The old briefs keep their texts and say so on the set-up page.
*Status:* confirmed for the task. A description is still typed by hand and can still say something the settings do not.

### B. Measuring and judging

**B1. There is no control, so nothing shows that the hypothesis format helps.**
*Evidence:* until 2026-11-17 no session had run the same brief and budget without hypotheses, or as a random search.
*What we changed:* two comparison arms (`loop.py --arm plain`, `random_search.py`) and a first experiment (section 3).
*Status:* a first answer, and a weak one: on `two-hosts-udp-demand-2` the three arms end in the same place, because
there every reachable setting is inside the tolerance. The question needs a brief where the default is not already
within 1 % of the best and where the cause is not visible in one table (`trap-2` is closer to that: its default is
28 % under what a change of TCP type gives, and the cause is a buffer the brief does not offer as a knob).

**B2. A sweep that is dense near the optimum is not a fair random baseline.**
*Evidence:* 51 of 73 ratio values of the sweep lie between 0.300 and 0.310.
*Status:* open.

**B3. Nothing checks the model's sentences, only its numbers.**
*Evidence:* s031, the verdict on H10: "all within 1 Mbps of TcpBbr's", where one value is 91 Mbps below. The numbers
match the records, so the page's check passes.
*Status:* open; a reader has to catch it, which is what the page is for.

### C. The page

**C1. Two words one letter apart will be confused when they stand side by side.**
*Evidence:* "1 refused" beside a turn was read as "1 refuted". *What we changed:* the count says "not accepted".
*Status:* confirmed; the detailed lines still say "refused".

**C2. One bar per comparison says "must hold" of each, which is false for one side of an either-or.**
*Evidence:* a rule that held showed "does not hold" on four of eight lines. *What we changed:* such a rule is shown as
either-or lines; every line was compared with the harness's own result on the 15 recorded rules of that kind (117
comparisons). *Status:* confirmed.

**C3. Measure a pane before defending it.**
*Evidence:* a test's detail was 4,327 characters over two screens, a third of it a chart that repeated the sections
under it, and the rule appeared four times. *What we changed:* the chart is folded, the rule is shown once in short
form; the pane is 2,595 characters. *Status:* confirmed.

**C4. What the operator asks for again and again:** controls at the thing they configure; no bare labels or numbers;
a hover box on every mark; one word per concept; the page never moves by itself; each kind of thing with a look of its
own (by form, not by a colour of good and bad).

**C5. A line that can grow must not be able to change the height of the bar that holds it.**
*Evidence:* the banner of a running session wrapped to a second line when a note of what had just arrived was
added, and the page moved by 20 px. It had always been able to; it showed when a shorter text at the banner's end
left the line just short enough to fit before the note and not after it. The live view's own check found it in the
full run. *What we changed:* the banner's line never wraps (the rest is cut with an ellipsis and stands in the
note's box); the check now adds a very long note for each kind of viewer and measures the height.
*Status:* confirmed.

### D. How the work is done

**D1. A full check run is not done until its summary has been read to the last line.**
*Evidence:* four faults (tile values running out of their tiles, the first screen 18 px too tall, a stale expectation
of a check, a field name in a summed-up refusal) were already reported by the last full run of the interrupted session
and were found only by the next one. *What we changed:* every line that is not "ok" is read and settled before a state
is committed. *Status:* confirmed.

**D2. Nothing tried only by hand goes to the live page in the last minutes of a session.**
*Evidence:* five such changes; three were faulty. *What we changed:* each change gets a check in the same piece of
work; at a usage warning the work stays in the work copy and the report says what is live and what is not.
*Status:* confirmed.

**D3. When the page changes at the operator's word, the check that describes the old page changes in the same piece.**
*Evidence:* a check still expected "0.05 to 0.95 … from 0.5" after the columns lowest, highest and starts at replaced
it. *Status:* confirmed.

**D4. A check with a fixed wait fails on a loaded machine.**
*Evidence:* a hover card "did not open" within 330 ms at a load of 45. *What we changed:* the check waits for the card.
*Status:* confirmed.

**D5. The harness and the records can be published before the page.**
*Evidence:* the page was not yet verified, and Claude chat was judging a session it could not see. Commit 2343e1a holds
the harness and s031 alone. *Status:* confirmed as a way of working.

**D6. A change made in the folder the sessions run from is in use at once, tested or not.**
*Evidence:* the report's two new parts were written into `harness/` minutes before the usage limit; for two days the
next session started from the page would have run with them, with one test line failing (the test's fault, as it
turned out).
*What we changed:* harness changes are made and tested in a copy and copied in when their tests pass, as the page's
are. *Status:* confirmed as a way of working.

**D7. Sharing needs one rule per conflict, not a design.**
*Evidence:* the operator asked that everybody in the lab can use the page "as much as I am without too much works",
and then for "the least safety measure": see who runs the ongoing session, and no new session during it.
*What we changed:* any account of the server may use the page through its own tunnel; one session at a time; the page
names the session and who started it; only that account or the owner stops it; each action is noted with its account.
*Status:* built and tested with pretended accounts; no second person has used it yet.

**D8. A rule the operator sets for the page holds for the one who builds the page too.**
*Evidence:* an hour after the operator asked for one session at a time, the six sessions of the control experiment
were about to be started side by side from a terminal, on the reasoning that the rule was "for the page". The start
was blocked by the tool's permission check. Asked, the operator allowed it "this once".
*What we changed:* an exception to a rule the operator has just set is asked for, not reasoned out.
*Status:* confirmed.

## 5. Open questions

1. Does the loop help at all, against the same budget without hypotheses and against random search? (B1)
2. Do the instructions of 2026-11-15 change what the model does? One session says yes (s033, section 3); a few more
   on `trap-2`, and the same sessions without the two paragraphs, would say how often.
3. Should the final report have fields of its own for what limits the result and for the settings that made no
   difference? (They are asked for in the explanation.)
4. The warm-up as a setting. (The seed and the task text were settled on 2026-11-17: A5, A10.)
5. Should the page say "not accepted" everywhere, and show how a hypothesis and the simulations of its test belong
   together outside the test's detail?
