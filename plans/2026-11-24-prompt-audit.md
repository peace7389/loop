# What the two agents are told: an audit of the texts sent in recent sessions (2026-11-24)

The operator's request: "By looking into prompts of the recent sessions, find out any defects or defiances from the
intentions or correct working. For example, I want to make sure none of agents be steered into specific directions
unfairly by biased prompts."

Nothing in this sheet has been changed in what the agents are told. Two faults of the program found on the way are
repaired (section 5). Every other item waits for the operator's word, because a changed text makes new sessions no
longer comparable with those run on `v1`.

## 1. What was read, and how

- The texts as sent, taken from the sessions' own records of each call to the local Qwen model: the system text and the
  request text of every call, for the researcher and for the supervisor, in s056, s057, s058 (brief after_fix), s059
  (three-hosts) and s061 (three-hosts-link). Only what the agents were given was read, not what they wrote back.
- Three readers worked apart from each other, each with one question: (R) is the researcher steered, (S) is the
  supervisor steered, (C) is each statement of the instructions true of the code. Reader C rebuilt the instructions
  from today's code: they are byte for byte what was sent, so everything below holds for the harness as it stands.
- I checked the readers' main findings against `harness/loop.py`, `harness/network.py` and the sent texts before
  writing them here. A finding marked "read only" was not exercised by a run.
- All three sessions ran the arm "supervised" with competitors. The researcher's instructions there are `LEAN_PROMPT` +
  `COMP_LEAN` + the structure paragraph + the findings paragraph (all in `loop.py`); `prompt.txt` is used only by the
  arms "hypotheses" and "plain".

## 2. The short answer

1. **The researcher is steered toward the hidden answer of each brief, by the text, before any measurement.** In all
   three sessions it stated the hidden answer, or the hidden question, in turn 1, in words close to a sentence it had
   been given (section 3, A1 to A3). What earlier sessions show fits this: on after_fix, s055 and s056 never tried the
   scheduler; s057 tried it in turn 4; s058, the first with the task sentence that names the structure, in turn 1.
2. **The supervisor is not a rubber stamp, but its texts lean toward approving a test and toward a clear ruling**, and
   at the ruling it is asked about a competing guess whose words it is not shown (section 4). Counts from the ledgers:
   in s055 to s059 it sent back 2 to 12 tests a session and refuted 2 to 6 hypotheses; in s061 it approved 5 of 5
   with every question passed.
3. **Several statements of the instructions are not true of the code** (section 6): what happens to a request made
   together with a step, what "half of what is left" means, what the tolerance does to a rule, what "locked" means.
4. **No text tells either agent the scheduling policy, another session's result, or what the operator expects.** The
   supervisor is never sent the researcher's private notes.

## 3. The researcher: where a text points at an answer

Severity: high = it plausibly changed what the researcher did; medium; low = wording only.

| # | Where | The text (exact) | What it favours | Severity | A neutral form |
|---|---|---|---|---|---|
| A1 | structure paragraph, every brief whose network may change | "kind (scheduler, fifo, or another of ns-3's queue discs: pfifofast, codel, fqcodel, red, pie). A scheduler gives each flow that passes it a part of the link; fifo is one queue for all, first in, first out." | The scheduler: named first, the only kind whose effect is said, in words that fit the problem of after_fix (its answer). fqcodel, also per flow, gets no word. s058, turn 1: "A scheduler queue on l1 that gives each flow a share of the link will let TCP deliver nonzero goodput." | high | the kinds in alphabetical order, each with one line of the same length, or none with a line |
| A2 | structure paragraph of three-hosts-link, and its brief | "rate (at most 100Mbps in this brief; left empty: 100Mbps). One link for each two hosts. A new link has a one-way delay of 1ms in this brief, packets of at most 1500 bytes, a device queue of 10 packets and, on each of its two sides, a plain queue of 100 packets"; brief: every host, link and flow locked, at most 4 links where 3 exist; description: "Each host sends a packet along the route with the fewest links to the packet's destination" | Adding a link (the answer): it has four times the words of any other change, its empty value is the best value, the limits leave it as the only addition that can be built, and the routing sentence says a direct link will carry the flow. s061, turn 1: "Adding a direct a-c link ..."; no other change was ever tried. | high | the same depth for every kind of change; the routing sentence in every brief or in none; limits that leave more than one move |
| A3 | description of three-hosts | "How the scheduler behaves when one flow has less to send than its part allows is not described here; finding that out is part of the work." | The hidden behaviour (whether a flow may use what the other leaves), named before any data. s059, turn 1, states it as a guess at once. | high | leave the sentence out |
| A4 | first lines of the instructions, against every brief's task | "The purpose is to understand why the system behaves as it does, not to optimise" against "Find the settings that give the largest fa_goodput_bps, while fb_loss_frac <= 0.1 ... Explain why they are best." | Two purposes. In s059, 8 of 11 new simulations bisected one setting. | high in s059 | one purpose in both places |
| A5 | findings paragraph and every turn's first block | "A final report is held back while a finding was never looked at." and "\"It does not change the recommendation\" is not a reason to park a finding" against "A difference inside it is not a finding" | Staying with the first answer and explaining side numbers. In s061 turns 2 to 6 and all 9 remaining simulations went to a difference of 6, 0 and 4 dropped packets with goodput equal within 0.03 %; the other link, other queues and the queue length were never tried. | high in s061 | a finding inside the tolerance, or about no measure of the goal, may be parked with that reason |
| A6 | task sentence of after_fix | "the structure of the network (its hosts, links, flows and queues, within the brief's limits)" with limits that allow no host, link or flow to be added | A change of the queue, the only one that can be built; with A1 that is the scheduler. | medium | name only what can be changed in this brief |
| A7 | instructions, and the text of the tool `measure` in every brief | "name (lower-case, for example rwnd_max)"; "(the bits per second of two flows added, or, once the simulation has its probe, a flow's bytes in flight divided by its receiver's window: <flow>_inflight / <flow>_rwnd)" | The receiver's window as a cause. In these briefs it is a distraction; in the trap briefs it is the hidden answer. The examples were copied word for word (s058 T12, T18; s059 T5), and became the competing guess of s058's first tests. `schema.json` holds more of them ("rwnd_mean", "rwnd or inflight / rwnd"). | medium | placeholders: "for example <column>_max", "<column_a> / <column_b>" |
| A8 | rule of the chain, and its refusal | "every later guess names in about a record made since your last guesses"; refusal: "this guess starts only from records your earlier guesses already had" | What was already found, over what was not yet tried: it refused "TcpLinuxReno or TcpBic could ..." and "A pfifofast queue disc may ..." in s058. | medium | a guess about an option not yet tried may start from the baseline or the brief |
| A9 | marks the harness writes on guesses and checks | "[refuted by V1: no hypothesis can come from it, and no guess or test may compete with it ...]"; "[the rival explanation predicted FAILED and does not fit this result ...]" | Whatever the last rule said. In s058 the guess that names the true cause was marked refuted because one consequence of it failed. "Predicted FAILED" is printed as a fact although the format accepts nothing else. | medium | "its hypothesis H1 failed"; "was declared to predict FAILED" |
| A10 | the supervisor's first finding, due in turn 1 | example in its format: "name (text): at most 5 words, to show it by (for example: TCP gets nothing)" | The first finding, which the researcher must answer before anything else: on the two-host briefs the baseline is literally that. | medium | no example |
| A11 | parts 5 and 7 of the answer | "drop: ... Usually empty."; "objections: ... Usually empty." | Accepting the supervisor's rulings: no objection exists in any of the three ledgers. | low to medium | leave "Usually empty" out |
| A12 | one repair request of s058 (turn 9) | an example change that put a scheduler in place of the queue | The answer of after_fix, word for word. No effect there (the researcher had used it since turn 1). The code no longer does this for the researcher, but still copies the old example into the supervisor's history of rounds (B6). | medium | done for the researcher |

## 4. The supervisor: where a text leans

| # | Where | The text (exact) | What it leans to | Severity | A neutral form |
|---|---|---|---|---|---|
| B1 | follow-up question after a ruling (`loop.py:1520`; sent once, s057) | "These do not fit together: a fair test that failed fits the guess that predicted it and not the other. One question: which of the two guesses does this result fit?" | It forces "the competitor fits" after every refutation. In that case the numbers fitted neither guess. | high | "You marked both as not fitting. Confirm or change; both may stand." |
| B2 | all 52 ruling requests | asked "fits_competitor: whether the competing guess fits this result", while the competing guess appears only as an id | Three of its answers are about a guess it cannot read; the tested guess stands in full. | high | show the competing guess with the same lines as at the review |
| B3 | rounds 2 and 3 of a review | "THIS IS ROUND 3 of at most 3 for this test. The researcher repaired it after:" | Approving at last. In s059 the round-3 test of H2 was word for word the round-1 test that had been sent back, and it was approved. The earlier version is not shown, and it is not told that a third refusal still lets the test run. | high | show the test of each round; say it may be unchanged |
| B4 | all ruling requests | its three earlier answers quoted, then "Answer the three questions again with the result in hand", and a further field only where an answer changes to fail | Keeping "pass", hence a clear ruling: of 47 rulings whose result is visible, 3 are inconclusive. | high | ask without quoting the earlier boxes; compare afterwards |
| B5 | every supervisor request of s057 and s058 | "for example a link's queue replaced by a scheduler" in the line that says the network may change | The answer of after_fix. Already removed (2026-11-23), absent in s061. | high then, repaired | - |
| B6 | history of rounds in a review (s056) | the harness's refusal for the researcher, with its example change (a scheduler), copied whole | The same answer by another way; still in the code. | high for one call | "the harness refused the test as unreadable", without an example |
| B7 | all 70 test reviews | "WHAT THE RESEARCHER SAYS THE RULE GIVES IF THAT GUESS IS TRUE AND THE TESTED ONE FALSE: FAILED" | "Correct: pass". It is FAILED 70 times of 70 because the harness accepts nothing else, so it tells nothing and only anchors. | medium | leave the line out |
| B8 | the three questions | "Honest: can the test fail? Its result is not already known from the records, and its threshold is not one that almost any result passes." | "Pass": the conditions are written as statements about the test, and only "pass" is defined. At the ruling the sentence is untrue (the result is in the request). | medium | "pass only if (a) ... and (b) ...; otherwise fail" |
| B9 | system text | "... is a proper test, never by itself a reason to send it back: the defect already_answered means only ..." | Approving tests on records already shown: in 26 of 70 reviews every simulation had run and its series stood in the same request. `already_answered` exists in no answer format of this arm. | medium | "fail Honest if the compared value, or the series it is computed from, is already shown" |
| B10 | a third of the rulings | "THE SIMULATIONS OF THIS TEST, as measured:" over the whole experiment's table | A sibling test's result stands under this test (in s058 the scheduler's result under the queue-length test, and the ruling then cites it). | medium | only the simulations the rule names; the rest under another heading |
| B11 | guesses marked as competitors | "the question whether it comes from what was learned since is not asked of it" | Lighter scrutiny for a competing guess, said by the harness. | medium | "the researcher declares it a competitor; whether it concerns the same result is for you to say" |
| B12 | answer formats | "fits_tested (one of: fits, does not fit)"; "honest (one of: pass, fail)" | No way to say "cannot tell", which the system text asks for. | medium | add "cannot tell" |
| B13 | s061 reviews | simulations that had already run shown as "(new)" | "Honest: pass". Caused by the fault repaired this morning (repeats on a changed network). | medium then, repaired | - |
| B14 | system text against the formats | "You never propose a hypothesis, a setting or an experiment of your own" against the fields `missing` (a cause) and `retest` (what a fair test would compare) | A contradiction; in s059 its feedback prescribed a design. | low | name the two fields as the exception |

Checked and found fair: both guesses are quoted in the researcher's own words at the review; the counts stated in a
request match its sections; the check lines and the tolerance line are the same everywhere; no private field of the
researcher reaches the supervisor.

## 5. Faults of the program, repaired on 2026-11-24

| What | How it showed | Repair | Check |
|---|---|---|---|
| A "locked" object could be taken out and put back under its id with other values: the fixed UDP flow at 1 Mbit/s, a brief's link at 10 Gbit/s past the cap of a new link, the TCP flow as a flow at a constant rate. The instructions say such objects "may not be removed" and "every other setting is fixed". | by a call of `network.changed_problems` (no session used it) | a locked object must be as the brief states it; a brief's link put back with other values counts as a new link for the cap | `harness_checks/test_locked_replace.py` |
| The supervisor's request on an objection printed `{verdict['id']}: {b['result']}. {b['because']}` as written (a text without its values) | by reading `loop.py:1552` (no objection was ever made) | the values are filled in | the same file |
| A simulation on a changed network that had already run was run again (s061: 9 of its 12) | this morning's audit | repaired this morning | `test_reuse_structure.py` |

## 6. Statements of the instructions that are not true of the code

| # | The statement | What the code does | Severity |
|---|---|---|---|
| C1 | "the results come back at once, in the same turn" (requests) | only for a reply without a step; a reply with requests and a step sees its readings in the next turn. In all three sessions every reply with requests also had a step, so "look before you simulate" never happened within a turn. | high |
| C2 | "one experiment may run at most half of them"; each turn: "at most N new simulations: never more than half of what is left" | N is right; the reason is not: the smaller of the brief's number per experiment and half of what is left, rounded up (16 left: 4, not 8; 3 left: 2; 1 left: 1) | medium |
| C3 | "at most N new simulations" | an experiment may list at most the brief's number of simulations in all, repeats included; `LEAN_PROMPT` never says what `simulations_per_experiment` is | medium |
| C4 | "Two results closer than the tolerance count as equal" | only `==` uses the tolerance; `<`, `<=`, `>`, `>=` are decided on the raw numbers and the check gets a note | medium |
| C5 | the note "They count as equal ... so it is no evidence of a difference" | also written when a rule states its own margin (`x <= 1.01 * y`) or when a measured value equals the rule's own threshold (s061 C3: "10.0 against 10.0") | medium |
| C6 | "A guess of why whose about names a finding (for example F2) works on it" | the finding's id is swapped for its records before the rule of the chain is applied, and the guess is then refused as starting from old records | medium |
| C7 | "measure@label (an output, or a measurement of your own ...)" | a measurement an earlier experiment defined is unknown unless this experiment defines it again (s058: a test not run for it) | medium |
| C8 | the repair step's system text: "the strongest rival you can think of" | with competitors on, the same call asks for an existing guess and says an unwritten cause "cannot be named here" | medium |
| C9 | "limits": {"simulations": 20} beside "12 simulations left (12 granted so far)" (s059) | the session was started with 12, and this arm cannot ask for more | low to medium |
| C10 | "you repair that test at once, up to three rounds; the other tests run meanwhile" | at most two repairs (round 1 is the first proposal); the other tests run after the rounds | low |
| C11 | "name (at most 5 words)" | cut at 6 words and 48 characters, never refused | low |
| C12 | "Every reading stays in the ledger" | a reading is cut at 6,000 characters; past 40,000 in all, older long ones shrink | low |
| C13 | "the flows start within the first 10 ms" | they start at 1.00 to 1.01 s of the simulation's clock, which the series shows | low |

Missing for the stated goals: a UDP rate is a rate of payload (80 Mbit/s is 81.7 Mbit/s on the wire, which decides where
the 10 % line of three-hosts falls); what a removed queue leaves (a plain queue of 100 packets); that `list_runs` does
not show a simulation's change of the network; the loss measure counts as delivered a packet still waiting at the end
(this morning's audit, lesson B4).

Only `prompt.txt` (the other two arms) says: what the brief's number per experiment means, that values out of range are
forced into it, that an unreadable rule refuses the whole experiment, that checks decided inside the tolerance are
marked. The supervised arm's researcher is told none of these, though all hold for it.

## 7. What I recommend, in order

1. **Take the pointers out (A1, A2, A3, A7, A10, B6, A11).** These follow the operator's rule of 2026-11-23, "describe,
   never suggest". A1, A7, A10, B6 and A11 are texts of the harness; A2 and A3 are texts of two briefs, so they mean new
   briefs (`three-hosts-2`, `three-hosts-link-2`), the old ones staying as the record of s059 and s061.
2. **Give the supervisor what it is asked about (B2, B3, B10) and let it say "cannot tell" (B12); drop B1's forced
   answer and B7's empty line.** B4 (its earlier answers quoted back) is a real design choice: decide it apart.
3. **Make the instructions true (C1 to C8).** C1 by saying what happens; C4 and C5 by deciding what the tolerance is to
   mean for a rule with `<` or `>`.
4. **Decide the two purposes (A4, A5)**: understand or optimise, and whether a finding inside the tolerance may be
   parked. This is the operator's design, not a wording matter.
5. **Then measure it**: the same three briefs, in their neutral form, three sessions each. If the answer is no longer
   stated in turn 1, the texts were doing the finding.

A fair comparison needs one more thing the texts cannot give: a brief whose limits leave more than one move open
(A2, A6). With one move open, even a neutral text finds it.
