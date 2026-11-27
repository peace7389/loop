# Review of the harness, 2026-11-27

Asked by the operator on 2026-11-27 ("Why doesn't the researcher propose findings? Something is off. Review everything thoroughly, especially
the harness"). Five independent read-only reviews of the tree with today's fixes (`v2work/tree_s14`, branch `v2` at dad374a), one per area, each
followed by my own check of every claim in the code and the records before anything is changed. Line numbers are those of that tree's
`harness/loop.py` unless a file is named.

State of each item: **claimed** (the reviewer's, not yet checked by me), **verified** (I read the code or the record and it is so),
**not so** (checked and wrong), **fixed** (changed, with a check), **for the operator** (a choice of design, not a fault to repair unasked).

## A. Findings: why the researcher never raises one

Facts, verified: in all 99 full replies since findings exist (s052 to s066) the researcher's own answer holds `findings: []` (the field
`answer` of `calls.jsonl`); the harness dropped none; the supervisor raised 145.

Real-model test (`v2work/findings_exp.json`): the first reply of s063, s065 and s066 asked again, twice as it was sent and twice with an empty
list of findings, as the harness prints one.

| first reply of | the supervisor's findings on the list | findings written, as sent | findings written, empty list | guesses, as sent / empty |
|---|---|---|---|---|
| s063 | 2 | 0, 0 | 1, 1 | 0, 2 / 0, 4 |
| s065 | 2 | 0, 0 | 0, 0 | 4, 4 / 6, 5 |
| s066 | 1 | 0, 0 | 1, 1 | 2, 2 / 3, 0 |

So: 0 of 6 with the supervisor's findings already there, 4 of 6 without. The supervisor's first look is the main cause, and not the only one.

| # | Claim | State |
|---|---|---|
| A1 | The supervisor looks first: at the baseline before turn 1 (3491), after every explore experiment (3720), at every ruling (1572), at most 2 each; the researcher's first list already holds them as DUE | verified |
| A2 | The only sentence that invites a finding ("FINDINGS: none so far. When a result is not explained, state it in findings") is printed only for an empty list (2657): it was shown in 0 of 102 replies. Otherwise the list's request names only decisions, "never looked at" and the held-back report | verified (the code); the count is the reviewer's |
| A3 | A finding the researcher writes in the reply that carries its report holds that report back: it is recorded open (settle_findings) before `findings_unseen` is asked (3733), and its id is not announced, so it cannot be parked in the same reply | verified (the code); never met in a session |
| A4 | The supervisor is asked what "nothing on record explains yet" while it is shown no guess and no task (2841, 1144): every look gave a finding (16 of 16), 71 of 89 rulings; in s063, s065, s066 18 of 35 are about side measures (the reviewer's classification) | claimed |
| A5 | The supervisor's findings take the free turns: s065 turns 8 and 9 went to F11 (la_util, a side measure); its ruling raised F12 and F13 with no working turn left | claimed (fits the audit of s065) |
| A6 | The lean instructions give no example of a finding and send an unexplained result to a guess (2333, 2335); `prompt.txt` line 11 has four examples | claimed |
| A7 | Closing is unchecked: any evidence id closes a finding (2772); 25 of 125 closings cite only records older than the finding (s065 F4: about E1, closed by E1) | claimed |
| A8 | "Working on it" and "never looked at" stand together for one finding (2637 to 2639 against the text at 2869); s063 turn 9: F7, F9 to F13 | claimed |
| A9 | No check of duplicates among the supervisor's findings; unequal rules for `about` (2854 against 2745); s066 F8 repeats F7, s065 F5 repeats F1 | claimed |
| A10 | `remap_refs` can tie a decision to the wrong guess when a guess of the reply is refused (2695) | claimed, latent |
| A11 | Small: 2797 says "asked for again in the next turn" in the last turn too; 2782 offers "requests or an experiment in this same answer", which the code no longer takes (s056 N26); 2857's digit check passes on "r003"; a restated guess loses its link to a finding (3171) | claimed |

## B. Gate 1: the review of a test and its repairs

| # | Claim | State |
|---|---|---|
| B1 | After a refusal by the harness, the next repair's simulations are merged with one label twice, and that valid repair is refused ("every simulation needs its own label"): 3408 feeds 3311, whose set of labels does not grow inside the list. s063 P9 -> G30 (H8 lost), s059 G34 (H10) | claimed (the reviewer reproduced it on s063's data) |
| B2 | After a refusal by the harness the next request for a repair gives only the harness's reason: the supervisor's objection is gone (3386). All 13 such round-3 requests of s055 to s065; 5 repeat round 1's rule (s065 H1, H3; s056 H1, H4; s057 H10) | claimed |
| B3 | The supervisor is told "A test sent back in round 3 is run all the same, marked as contested" (1207); the code holds it (not run) when Consistent is not pass (3231). The researcher's instructions say only "three rounds at most" | claimed |
| B4 | The batched first review names the new guesses G1, G2, ..., which are also ids of reviews; the names reach the researcher in the feedback, and the repair request then shows the wrong record (1499, 3353). s063 G17/G18, s058 G40 | claimed |
| B5 | `restated_since` (today's) is incomplete: it compares only `guess`, while the review shows `result` too (s057 Y24); it looks at this turn only; `test_key` leaves out `competes_with` and the definitions of measurements; `prereviewed` is never cleared (an answer left in it: s055 turn 10 H14) | claimed |
| B6 | The request for a repair asks for "an existing live guess" and lists none, nor their standing, nor the competitor's text; nothing says a repair cannot define a measurement. s065 P3 named the refuted Y5 (G15), s063 P8 (G29), s058 G42 | claimed |
| B7 | Every refusal by the harness uses up a round; the instructions name only "a rule the harness cannot read". 13 refusals in round 2, 9 in the last round (not_run); s063 H8, s055 H7: the supervisor saw no repair | claimed |
| B8 | `missing` holds a test at once even where the failing box could be repaired; an objection to the competitor without `missing` gives rounds no repair can meet (3231). s065 G32; s066 H3, s065 H1 | claimed (a judgement) |
| B9 | The request for a repair says "(N can still run)" (3374); the limit is half of what is left (1732), after `reserved`, which counts shared simulations twice (3338) | claimed, no instance |
| B10 | Small: 3250 says "Consistent failed" for "cannot tell"; `objected` (3296) is never cleared | claimed |

## C. Gate 0 (guesses) and gate 2 (rulings)

| # | Claim | State |
|---|---|---|
| C1 | A guess the harness refuses first is never read by the supervisor after its restatement (2067: `ask=by == "supervisor"`): 30 guesses in s055 to s065, for example s063 Y7, Y13, Y15, Y18, s065 Y13. s063 Y13 met the chain's rule by citing G17/G18 and is the hedged competitor that left V4 and V5 inconclusive | claimed |
| C2 | The mark "<- NEW since ..." is put at the end of a record's text, which for a result table is its last line (1421): the supervisor read it as "only the last simulation is new". s066 G11, G13, G22: three false warnings (the guesses were accepted) | claimed |
| C3 | Today's `values_before` states as a fact what is not one: (a) a simulation shared with another test of the same turn is called "in the records before it ran", though the rule was fixed first (s065 X2: S4 same as S2); (b) a measurement of its own is always "first measured by this test", also when an earlier experiment took the same one (s056 X11/H15); (c) the same when a reading had shown the series (s065 H8: T11 held Cubic's queue series) | claimed; (c) fits the answer format's own words ("or the series each is computed from") |
| C4 | "Once in a turn for the same records" is keyed by the records, not the guess (3079): a second faulty guess with the same `about` is accepted with no chance to restate, and its line says "accepted on its second statement". s056 Y25/G44 | claimed |
| C5 | The second look after an objection asks one question "fair", not the three; it shows neither the competing guess nor the ruling's boxes, prints "Defect: ." empty, and its record has no `fits` or `follows` (1621 to 1640, 3672). No objection in s041 to s066 | claimed, never exercised |
| C6 | Refutation does not look at the result: "does not fit" is applied on any ruling with three passes, also an inconclusive one (399 to 403); with several rules only the first rule's competitor is shown and judged (1563, 1605) | claimed, latent |
| C7 | A threshold written as a number is never marked as inside the tolerance (512): s059 C8, `0.100213 <= 0.1` FAILED by 0.21 %, Y14 refuted. `x@a - x@b == 0` is exact, because == is relative | claimed; the turn's text says so (a design) |

Rulings and refutations of s063, s065, s066 as the reviewer classed them: s063 V4, V5 inconclusive (the supervisor's inconsistency and the known
hedge); s065 V2 (run contested, the ruling repeats the review), V3 (the approval before the restatement: B5/today's fix 1), V7 (C3c and the
supervisor's inconsistency); s066 none inconclusive, but Y10 refuted by V3 on a result that supports it (`5792 > 0` held on a 1 Gbit/s link) and
V5's reason misstates a gap (3.8 %, not 1.3 %).

## D. Experiments, the tools and the measurement

The C++ is `scratch/net/net.cc`.

| # | Claim | State |
|---|---|---|
| D1 | Loss, drops and retransmissions use another horizon than goodput, so a longer queue looks better without being better. The loss fraction's denominator is the packets the application sent in the measured seconds; its numerator counts those not arrived by the end of the simulation, one second later with the senders stopped (net.cc 112 to 132, 807, 820 to 823). Goodput counts only bytes that arrive inside the measured seconds. Packets that a still-filling queue takes in count as arrived for the loss and are absent from the goodput. s065 r010: the queue of fb holds 755 packets at t = 2 and 1000 at 2.4; those 245 packets are the difference of the drops (3813 in r009, 3568 in r010): loss 0.099905, while 1 - goodput / rate is 0.1067 in both runs. The other way round: on a slow link, packets not drained in that last second count as lost. The text says only "fraction of the packets flow fb sent that never arrived" | claimed; it is the mechanism behind s065's answer |
| D2 | "A new queue holds 100 packets" is not true where the brief has a knob for the length: the knob sets it (loop.py 230; network.py 507; tools.py 66). s063 r006 to r008, s066 r009, r010. Where the queue is removed, its knobs do nothing, yet designs that differ only there run and are charged as different simulations | claimed (the reviewer ran `network.apply` on the tree) |
| D3 | No record shows a new link's rate or a new flow's rate or type: `edits_say` prints "+link lac a-c" (217 to 221), also to the supervisor (1188). Two simulations with a new link at 90 and at 10 Mbit/s read the same | claimed, no instance |
| D4 | `measure` reads the 0.1 s series for any column both records hold, even after a probe (tools.py 495), against the text "read them with measure". s066 Q3/Q4: `tcp_cwnd` after `probe(0.01)` gave 100 samples, not 1000; s065 Q4 | claimed |
| D5 | `series`: `every_n` is not explained, and a long record is thinned without a word (tools.py 424): 8 of 17 requests passed 0.1 or 0.2 (seconds); with duration 10 every second row is returned, and neither the sample at t = 2 nor the last is shown | claimed |
| D6 | Re-use of a simulation: the note "not run again" stands beside new measurements, although the harness did run it again for the probe (586; s065 E7); an existing `probe.csv` is used at whatever step it was made with (536: 0.1 s in s063, 0.05 s in s065, a fresh one 0.01); a re-used record carries an earlier experiment's measurements, and a value of the same name survives if the new computation fails (563, 577); a rule on a measurement defined again and already known passes "can fail" (1845); the key has no scheduling policy | claimed; the last four from the code only |
| D7 | The flows' start offsets depend on the structure: the random stream for them is made after the stacks and queues (net.cc 559), and each host and each red or pie queue takes a stream first: add_host or such a queue moves every flow's start by up to 10 ms | claimed, from the code; size unmeasured |
| D8 | Refusals that point at a repair: s066 N1 "change a part the network has instead of adding one" (loop.py 91); s063 N2's example is exactly remove + add_queue on l1; network.py 243 "remove a link so that there is one way"; loop.py 1828 "same settings" after a clamp, with no word of the clamp | claimed |
| D9 | Enforced and not stated: ids such as rate, queue, start, type are refused (network.py 113, 209); a scheduler on a side no flow passes is refused (301); a new flow through an existing scheduler gets the part 0.5, not "equal" (444); acknowledgements are served first and their drops are not reported; a simulation that FAILED is charged (loop.py 3710) | claimed |
| D10 | Utilisation above 1: whole packets are counted when their sending ends, so the edge adds or drops up to one packet (1.000012 = 750 bytes). Harmless; the text leaves out "over the measured seconds" | claimed |
| D11 | A flow's rate is payload, a link's rate is on the wire: 80 Mbit/s of 1400-byte packets take 81.7 Mbit/s of lc, which moves the loss threshold by 2.1 %, more than the tolerance. The unit of cwnd (bytes) is not stated | claimed |
| D12 | Small silent changes: the probe's `every` is clamped to 0.001 to 1 (tools.py 445); `t_to` past the end is echoed; samples that divide by zero are dropped | claimed |

True as the reviewer checked: the budget and tolerance lines, a new link's defaults, removal leaving a plain queue of 100 packets, routing by
the fewest links, the probe's columns.

## E. Every refusal against the texts

The complete table is `plans/2026-11-27-refusals-table.md` (175 rules, each with its place in the code, the message, whether a text states it
beforehand, how likely a researcher is to meet it, its cost, and how often sessions s055 to s066 met it). The reviewer's totals: 84 stated (5 of
them since today), 35 partly, 53 not stated; of those 53, 12 cost nothing or favour the researcher, 6 are changes the harness makes to the
supervisor's words, and 35 can cost a part of an answer, a test, a turn or the session. All of it is **claimed** unless a row below says otherwise.
One point of weight: the answer format's field descriptions are not a text the researcher reads (they go to the model server as a constraint
only, loop.py 832), so a rule that only a field description states is not stated.

The fifteen it ranks highest (likelihood times cost):

| # | Rule, in short | Met in s055 to s066 | State |
|---|---|---|---|
| E1 | After round 3 a test whose Consistent box did not pass is not run; the supervisor's own text said it "is run all the same" | 6 | the supervisor's sentence: fixed (B3); the researcher's instructions still say only "three rounds at most": for the operator |
| E2 | A test is held with no repair when the supervisor names a competing cause that is no guess; the note passes the supervisor's cause on word for word and says "Write it as a guess ..., then test H4 against it" | 4 | claimed; the message suggests: for the operator |
| E3 | Every check of the harness on a repair uses up a round; the repair call does not carry the instructions | 13 sent back, 9 not run | claimed (B7): for the operator |
| E4 | A fault: a valid repair refused for a doubled label | 2 | fixed (B1) |
| E5 | "One setting only" is enforced over all rules of a hypothesis and all their simulations together; a first proposal loses the whole experiment | 3 | claimed |
| E6 | One rule the harness cannot read, in a first proposal, refuses every test of the experiment, with no round (the text promises "a round of that test") | 1 | claimed |
| E7 | A test the harness refuses in round 1 gets no repair; "live" is never explained | 6 | the request for a repair now lists the live guesses (B6); the first proposal: claimed |
| E8 | `about` may not name a guess, a note or an experiment; the texts give examples only | 13 | claimed |
| E9 | A guess may compete only with a guess neither revised nor refuted | 8 | claimed (the mark of a refuted guess says it; the instructions do not) |
| E10 | A fault: in the last turn a refused report together with any accepted part gets no second attempt, and the session ends without a report (3601 with 3750) | 0 | claimed, latent |
| E11 | One simulation that does not record a measurement's column refuses the whole experiment | 1 | claimed |
| E12 | A measurement with no value leaves its hypothesis without a ruling, open and blocking | 0 | claimed |
| E13 | Inside one experiment a repeated design is cut and the rule that names it refused; the text says its result "is returned" | 0 | claimed |
| E14 | A report sent together with an experiment is not taken | 0 | claimed |
| E15 | `work` needs recorded ids, and the ids of this answer's own experiment and readings are not told; a reading over 6,000 characters is cut | 3; 2 | claimed |

Its three further lists: (a) 22 groups of messages that suggest what to do (the worst is E2; also "name the live guess (Y29, or another)", "or
test the settings in separate hypotheses", "use an explore experiment", "change a part the network has instead of adding one", and, since
today, my own "drop the hypothesis in your next reply and state a new one" in the request for a repair); (b) numbers: "(N can still run)" in the
request for a repair against the enforced half (B9), the turn's "at most C new simulations" while each repaired test is capped on its own, and
limits that stand in no text (8 measurements, a name of 2 to 31 characters, the token limits, 3 unusable turns, 2 holds of a report); (c) 16
statements of the texts that the code does not enforce or enforces otherwise ("a new queue holds 100 packets": D2; a report is held back at most
twice; a park's reason is never read; "brief only when nothing is measured" is accepted at any time; and others).

## F. Today's two fixes put to the real model (`v2work/replay_s065.json`)

- The review of H3's test alone, against Y10 as restated (fix 1): Correct "cannot tell" in 3 of 3 askings: the test would have been sent back
  for a repair instead of running to an inconclusive ruling. The fix changes the outcome.
- The ruling of H8 (fix 2), three askings each: as it was sent, Honest passes 3 of 3 (in the session it failed: the supervisor does not repeat
  itself), results supported / inconclusive / inconclusive; with the line of facts, Honest passes 3 of 3, results inconclusive 3 of 3 (Correct
  "cannot tell" or fail). The line cannot be shown to help on this case, and C3 says it can be wrong: it is corrected before anything is deployed.

## G. What was changed on 2026-11-27, and what waits

Changed (branch `v2`, stages 13 to 16; each read in the code by me, tried on the records it came from, and given a check in `test_stage5`):

| Item | Stage | State |
|---|---|---|
| A cited review of a test read "held. None" | 13 | fixed, live since 16:38 |
| The audits' five (an approval after a restatement; the facts at the ruling; what a repair cannot change; three rules stated; a window's samples) | 14 | fixed |
| C3, B1, C2, B5, B2, B6, B3, B4 | 15 | fixed |
| A1, A2, A3, A4 | 16 | fixed |

The supervisor's look in its new form (after the reply, with the guesses), asked on the real model with the records of s063, s065 and s066
(`v2work/look_exp.json`): on the same results for which the sessions hold 11 findings of the supervisor in 5 looks and rulings, it raises 6 in
10 askings (0, 0; 0, 2; 1, 2; 0, 0; 1, 0), all of them about side measures no guess speaks of.

Not shown yet by any real session: that the researcher raises findings in turns after the first.

Waiting for the operator (choices of design, or claims I have not yet read in the code): A5 to A11, B7 to B10, C1, C4 to C7, D1 to D12, and
section E apart from E1's sentence, E4 and E7's list. My recommendation for each is in the report to the operator of 2026-11-27.
