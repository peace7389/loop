# Refusals and silent changes of the harness, checked against the texts

Reviewed: the frozen copy `/research/silbmark/chunguck.kim/tools/v2work/tree_s14/harness/` (loop.py, tools.py, network.py, decision_rules.py, schema.json, manifest.json), arm "supervised", competitors on, lean paths.
Real instances: `~/project/sessions/s055 … s066/ledger.jsonl` (notes, reviews by the harness, guesses with a `restated` field, held reviews, readings). s060 and s064 ended at once (model server error; harness error KeyError 'no_cause').

Status: **S** = stated beforehand in the texts (1)-(5); **S27** = stated since 2026-11-27 (already known); **P** = partly; **N** = not stated beforehand ("stated only in the refusal" counts as N).
Texts: (1) instructions = LEAN_PROMPT with COMP_LEAN + STRUCTURE + FINDINGS_TEXT; (2) answer format; (3) brief + tool lines; (4) the turn's text; (5) repair / restate requests.
Note on (2): the answer format reaches the researcher's model only as a constraint of the model server (`response_format`, loop.py:832); it stands in neither the system nor the user message (calls.jsonl of s065). The supervisor is given its fields as text (loop.py:1106), the researcher is not. A rule that only a field description states is therefore marked P.
Likelihood (L): how likely a capable researcher trips without being told. Cost: what is lost. Real: count in s055-s066, one example.
Lines are of loop.py unless a file is named (dr = decision_rules.py, net = network.py, tools = tools.py).

## A. The whole answer, the turn, the session

| id | where | message the researcher gets | rule | status, and the sentence that states it | L | cost | real |
|---|---|---|---|---|---|---|---|
| A1 | 3580-3582 | none in the second attempt; next turn: "an answer the harness could not use…: empty content or finish_reason=length" | An answer that is empty or reaches the token limit (32,000 with the draft, main default 3181; half for the draft) is discarded whole and asked once more with the same text | N (no text names a token limit) | low | whole answer; twice = the turn | 0 (cut_off 0 in all sessions) |
| A2 | 3583-3587 | "invalid JSON: …" (record only) | Unparsable answer: same as A1 | N | low (format constraint) | whole answer | 0 |
| A3 | 3601-3612 | "YOUR ANSWER TO THIS TURN COULD NOT BE USED, AND YOU ARE ASKED ONCE MORE. What the harness refused, and why: …" / "the answer does nothing: no hypothesis, drop, verdict, experiment, report or request" | An answer with no usable part is discarded whole (its observations too) and asked once more; a second one loses the turn | P ("the harness leaves that part out, accepts the rest"; the second attempt and the lost turn are not stated; message names "verdict", which this arm has not) | low | the turn | 0 |
| A4 | 3618-3621, 3537, 3613-3614 | "3 turns in a row gave no usable answer: the harness ends the session after one last turn, in which only the final report is accepted" | UNUSABLE = 3 unusable turns in a row end the session | N (said when it happens) | low | session ended | 0 |
| A5 | 3507-3511 | "loop stopped by the harness: the rendered ledger is N tokens, over the limit of 100000" | LEDGER_TOKENS: the session stops at once, with no report and no last turn | N | low-medium (many long readings) | session ended without a report | 0 |
| A6 | 3504-3505, 3535-3546 | turn text "used up … you have this turn and 1 more …" | Budget used up: 2 free turns, then the last turn | S ("When they run out you get two more turns to look and to test on simulations already run, then one last turn for the report") | | | |
| A7 | 1876, 1883, 1910, 2051, 2111 | "this last turn accepts only the final report" | After A4, objections, guesses, hypotheses, drops are refused | S (that turn's text: "Only the final report (report) is accepted in this turn") | | | 0 |
| A8 | 2200 | "the simulation budget is used up: no experiment is accepted in the last turn" | Last turn: no experiment | S (turn text; LEAN) | | | 0 |
| A9 | 3598, 3640 | "requests are not answered in the last turns: N left unanswered" | Last turn: requests are not answered | P (the turn text asks for the report; requests are not mentioned) | low | a part | 0 |
| A10 | 3601 with 3750-3751 | none | In the last turn a refused report together with any accepted other part (a guess, a drop, an objection) counts as a usable answer: no second attempt, the session ends "all simulations used, no usable report". A refused report alone is asked for once more with the reason | N | low-medium | session ended without a report | 0 (3 sessions ended in the last turn, each with its report) |
| A11 | 3653, 3661, 3558-3563 | "THIS TURN GOES ON (your reply 2 in this turn, at most 3) …" | A reply without a step is followed by another call in the same turn, at most CONTINUES = 2 | S ("you are asked again in the same turn, at most twice") | | | |
| A12 | 3649-3651, 3556 | "The limit of turns with requests only is reached: decide now." | LOOKS = 6 turns in a row that only look; a sentence only, nothing is refused | N (number in no text) | low | none | 0 |
| A13 | 2042-2045, 2101-2102, 2163-2170, 2689-2696 | none | Ids of this answer's new guesses and hypotheses are replaced by the ids they were recorded with | S (turn text NEW IDS) | | | |
| A14 | 734, 740 | none | Observations and every record are shown cut at 6,000 characters | N | low | none | 0 |
| A15 | 2446-2470 | none | Parts this arm does not write are filled in (worth verify, role supports, expected {}, no_difference [], done) | N, harmless | - | none | every answer |

## B. Objections

| id | where | message | rule | status | L | cost | real |
|---|---|---|---|---|---|---|---|
| B1 | 1884-1885 | "an objection names a ruling of the supervisor by its id (to: for example V2): 'x' is not one" | to must be a ruling of the supervisor | S ("to (the ruling's id, for example V2)") | | | 0 |
| B2 | 1886-1887 | "a ruling is objected to once, and the supervisor's second look stands" | One objection per ruling; none to a second look | S ("object once") | | | 0 |
| B3 | 1888-1889 | "an objection says what in the records shows that the ruling is wrong (because)" | because must be a text | S | | | 0 |
| B4 | 3676-3677 | "the supervisor's answer to the objection O1 could not be read (…): the ruling V2 stands as it was" | An unreadable second look loses the objection (it cannot be made again, B2) | N | low | the objection | 0 |

## C. Drop

| id | where | message | rule | status | L | cost | real |
|---|---|---|---|---|---|---|---|
| C1 | 1913-1914 | "H3 must be an open hypothesis, and a drop needs a reason" | Only an open hypothesis, with a reason | S ("drop: open hypotheses you give up before they were tested (id, and why in one sentence)") | | | 0 |

## D. Guesses (whys)

A guess the harness or the supervisor does not accept comes back once in the same turn (restate_fn 3150); it is then recorded, "contested" if it still fails. Cost of every row here: one more call in the turn and, at worst, a guess marked contested.

| id | where | message | rule | status | L | cost | real |
|---|---|---|---|---|---|---|---|
| D1 | 1986-1988 | "a why needs result …, guess …, unseen (what in the system, not directly visible, would make it so), matters … and reason …" | result and guess must be texts | S (rule); the message names three fields this arm's format does not have | | | 0 |
| D2 | 1991, 1999-2001 | "about must list the records whose result the why explains: ids of evidence tables, simulations, checks, verdicts or readings in the ledger (for example E2, C3, T7), a run id …, or the word brief" | about may name only E, S, C, V, T and G records (or brief): a note (N), an experiment (X), a hypothesis, a repair refuses the whole guess | P ("about (the ids of the records it starts from, for example E0, S2, C1, V1, a reading T7, an objection of the supervisor G4; …)": examples, no word that a note cannot be cited, while the instructions say "read the note") | high | restatement | 4 (s055 Y6 cited N2; s056 Y9, s058 Y29, s061 Y6) |
| D3 | 1993-1998, 1999 | "about lists the records a guess starts from (results, readings, checks, rulings), never guesses: Y13 is a guess. A guess this one explains otherwise goes in competes_with, one it states more exactly in revises" / "about names ids that are not in the ledger: Y7" | about may not name a guess (of the ledger, or of this answer) | N | high | restatement | 9 (s059 Y15; s056 Y8) |
| D4 | 2003-2009 | "this guess starts only from records your earlier guesses already had (…). A later guess must come from something learned since: … Name its id in about (for example V2, C3, E2, T7, G4) and say in result what it showed; made since your last guess: …" | The chain: a later guess names a record made in or after the turn of the newest earlier guess, or declares a competitor and cites one of its records | S ("every later guess names in about a record made since your last guesses (a ruling, a check, a result table, a reading, an objection) and says in result what it showed, or competes with an earlier guess") | | restatement | 9 (s056 Y10) |
| D5 | 2010-2012 | "competes_with is null, or the id of a live guess (in the ledger or earlier in this answer) whose result this one explains by another cause: 'Y23' is refuted" | A guess may compete only with an existing guess that is neither revised nor refuted | P ("competes_with (the id of an earlier guess whose result this one explains by another cause, or null…)"; "live" is said only for rules; a refuted guess's ledger line says "no guess or test may name it as a competitor", a revised guess's line says nothing; the message says "earlier in this answer" although a later guess of the answer is taken too, 2010 `ahead`) | high | restatement | 8 (s057 Y26 refuted; s056 Y34 "not a guess") |
| D6 | 2013-2014 | "revises is null, or the id of an earlier why in the ledger that this one replaces with a better guess (one that has not been revised already)" | A guess can be revised once only, and a guess of this same answer cannot be revised | N | medium | restatement | 0 |
| D7 | 2046-2047, 2061-2062 | none | revises is set to null when it equals competes_with | N in the instructions (the restate request says "a guess competes with a guess or revises it, never both") | low-medium | a link dropped without a note | not countable (no note) |
| D8 | 2049, 2064 | none | A run id in about becomes its simulation's id; doubles leave | N, harmless | - | none | - |
| D9 | 2675-2687 | none | A finding id in about is replaced by the finding's records, and a work decision is written | S ("A guess of why whose about names a finding … works on it (the chain's rule still holds for the records it rests on)") | | | |
| D10 | 2015-2021, 3075-3083 | "the supervisor does not accept this guess as it stands: <defect>. The records show: … State what the cited records show, and what in them is new, or leave the guess. No hypothesis can come from a guess that was not accepted" | The supervisor's reading refuses a guess once per turn for the same cited records | S ("A guess it does not accept comes back to you once, in the same turn, to restate") | | restatement | 23 (s055 Y20) |
| D11 | 2067-2074, 2025-2033 | ledger: "[restated in the same turn: first not accepted by …; accepted as contested: …]" | After the restatement the guess is recorded whatever it says; empty texts are filled from the first statement, about is replaced by its valid ids (or the first statement's, or brief), an unusable revises is set to null | P (restate request: "It is taken as you restate it; if it still does not meet the rule above, it is recorded as contested"; the replacements are not stated) | low | guess contested | 5 contested by the harness (s057 Y3); 9 recorded with the supervisor still objecting (s056 Y24) |
| D12 | 2065-2066 | none beyond D11 | An unreadable restatement (also one cut at 12,000 tokens): the first statement goes on, contested | N | low | guess contested | 1 (s055 Y21) |
| D13 | 2091-2095 | "competes_with Y4: your new guess number 2 of this answer was not accepted, so this guess competes with none" | A competitor later in the same answer that was not accepted: competes_with set to null | N | low | a link dropped | 0 |
| D14 | 3078, 1448 | none | The defect not_from_what_was_learned is a warning only; for a declared competitor it is dropped | N, in the researcher's favour | - | none | - |

## E. Hypotheses

| id | where | message | rule | status | L | cost | real |
|---|---|---|---|---|---|---|---|
| E1 | 2107-2109 | "it comes from Y7, your new guess number 2 of this answer, which was not accepted (its note says why): no hypothesis can come from it in this answer" | No hypothesis from a guess of this answer that was not recorded | P (said only inside D10's refusal) | low (D11 records nearly every guess) | hypothesis and its test | 0 |
| E2 | 2112-2115 | "H15 is still open and untested: test it (send the experiment), or give it up in drop with what you learned, before you state another hypothesis. The next hypothesis comes from what a test showed" | While a hypothesis of an earlier turn is open and unchecked, no new one is accepted, also when this answer sends its test | S ("while one is still open and untested no further hypothesis is accepted. Test what is open, or give it up in drop") | | hypothesis, its test | 2 (s056 N21) |
| E3 | 2116-2117 | "at most 3 new hypotheses in one answer: state the ones you will test now" | OPEN_MOST = 3 | S ("state at most three in one answer") | | | 0 |
| E4 | 2118-2123 | "a hypothesis comes from a guess: from_why must be the id of a guess, one in the ledger or one of this answer (… the first new one is Y10); Y5 was revised as Y9" | from_why must be a guess that is neither refuted nor revised | S for refuted ("no new hypothesis comes from it"); P for revised ("replaces") | medium | hypothesis, its test | 1 (s057 N4) |
| E5 | 2130-2131 | "a hypothesis needs a text" | text must be a text | S | | | 0 |

## F. The experiment: simulations, labels, budget

A refusal of the experiment as a whole (part "experiment") loses every test of the answer: the turn's work.

| id | where | message | rule | status | L | cost | real |
|---|---|---|---|---|---|---|---|
| F1 | 1713-1714 | "an experiment has 1 to 4 simulations; this one has 5" | 1 to limits.simulations_per_experiment simulations | S (turn text: "it may list at most 4, repeats included") | | whole experiment | 2 (s055 G26, in a repair; made by the harness's own merge, since changed at 3314) |
| F2 | 1715-1716 | "every simulation needs its own label: letters, digits and _ only, at most 20 characters" | Label form and uniqueness; the format has the length but no pattern | S ("a label of its own (letters, digits and _, at most 20 characters)") for a reply; P for a repair (K10) | | whole experiment / a round | 2 (s059 G34, s063 G30: both false, see K9) |
| F3 | 1717-1718 | "a simulation's params has keys that are not settings of the brief" | Only the brief's knobs | S (format; "a value for EVERY knob of the brief") | | | 0 |
| F4 | tools:299-300, 1803-1808 | "design `a` does not state `k`" | Every knob in every simulation | S | | that simulation | 0 |
| F5 | 1725-1729 | "a simulation has a setting that cannot be read: bad rate '…'" | A rate or time must be written digits + (k/M/G)bps or ns/us/ms/s | P (the brief shows the form in min/max; "written as the brief writes rates" stands only in STRUCTURE) | low | whole experiment | 0 |
| F6 | 1730-1731 | "the experiment needs 5 new simulations but only 3 are left in the budget" | Budget | S (turn text) | | whole experiment | 0 |
| F7 | 1732-1734 | "the experiment needs 4 new simulations; with 5 left, one experiment may run at most 3 (half of what is left), so that something remains for what its results raise. Keep the simulations that decide your hypotheses and leave the others out" | spend_cap: half of what is left, rounded up, at most the brief's number | S (turn text: "may run at most 3 new simulations (half of what is left, rounded up, and never more than the brief's 4 …)") | | whole experiment | 0 |
| F8 | 2205-2207 | "the simulation budget is used up: in the turns before the report an experiment may use only simulations already run …" | Free turns: no new simulation | S (turn text of those turns) | | | 0 |
| F9 | 1739-1740 | "a test experiment needs tests: the ids of open hypotheses" | tests non-empty, all open (when every one is closed or not accepted) | S ("tests lists the open hypotheses it tests"); the message does not say which id is not open | | whole experiment | 1 (s057 N5) |
| F10 | 2181-2188 | "tests H17 (…not accepted), H18 (…): not an open hypothesis (not accepted in this answer, or already ruled on or given up), so its test is left out. The other tests of this experiment are taken as they are" | Tests of hypotheses that are not open leave; the others stay | S (same sentence) | | those tests | 1 (s056 N23) |
| F11 | 1741-1742 | "a test experiment needs at least one decision rule for each tested hypothesis, and none for any other" | A rule for each test; a rule for a hypothesis not in tests refuses the whole experiment | S for the first half ("decision_rules has at least one rule for each"); P for "none for any other" | low | whole experiment | 0 |
| F12 | 1766-1768 | "an explore experiment needs a question, and has no tests, no needs and no decision rules" | Explore: a question, no tests, no rules | S ("kind explore: question says what you want to find out; tests and decision_rules stay empty"); "needs" is no part of this arm's answer | | whole experiment | 0 |
| F13 | 2195-2197 | "design `base` is named by no decision rule of this test, so it is not run. In a test every simulation is one a rule compares; to look around without a rule, use an explore experiment" | In a test a simulation no rule names is not run | S27 | | that simulation | 7 (s056 N1) |
| F14 | 1825-1831 | "design `b` has the same settings and seed as `a`; give it different settings or remove it" | Two simulations of one experiment with the same settings (after clamping and rounding): the later one is cut | N (the instructions say of a repeated simulation only "is not run again: its result is returned and costs nothing") | medium (the same control under a second label for a second hypothesis) | that simulation, and with F15 a test | 0 |
| F15 | 1832-1836 | "this decision rule names `b`, a design that was refused; change the designs or the rule" | A rule that names a simulation cut by F14 (or by F4) is refused; its hypothesis is not tested | N | medium (with F14) | a test not run, hypothesis stays open | 0 |
| F16 | 1819-1824 | "this decision rule compares `a` with `b`, which are the same simulation (same settings and seed), so it cannot hold or fail for a reason; change the designs or the rule" | A rule may not compare two labels of one simulation | P ("must differ in one setting only") | low | a test | 0 |
| F17 | 1851-1855 | "design `x` is named only by a decision rule that was refused, so it is not run" | Follows F13 for refused rules | P (follows the S27 rule) | low | that simulation | 0 |
| F18 | 1812, 1859, 1861 | "no design / no decision rule of this experiment is left, so nothing is run" | Consequence of the cuts above | P | low | whole experiment | 0 |
| F19 | 499-501, 580-582 | "simulation x of X3 has the same settings and seed as S0 (run r001): the earlier result is returned, nothing was run again, and it is not counted against the budget" | A simulation run before in the session is not run again | S ("A simulation with the same settings as an earlier one is not run again: its result is returned and costs nothing") | | none | 66 (s055 N1) |
| F20 | 601, 3710; tools:382-397 | evidence line "… FAILED: …" | A simulation that fails (or gives nothing within 600 s) counts against the budget; rules naming it are not checked | N | low | a simulation, a test | 0 |
| F21 | tools:292-331; 627-628 | experiment line "[k: asked a, used u]" | A value outside its range is moved into it | S ("a value outside its range is moved into it, as the record then says") | | | 0 clamps |
| F22 | tools:309-310, 313, 321-327 | same line | A choice not on the list becomes the knob's default; a number is rounded to the knob's step and to a whole number; a clamped rate is rewritten in whole Mbps | P (only the range is stated) | low (format types and enums) | a simulation at another value | 0 |

## G. Measurements of the researcher's own (measurement_problem, 125-179; any refusal here refuses the WHOLE experiment, 2175-2178)

| id | where | message | rule | status | L | cost | real |
|---|---|---|---|---|---|---|---|
| G1 | 134-135 | "measurements is a list of at most 8, each with name, of, stat, t_from, t_to, level and with" | At most 8 measurements | N (no text, no maxItems; "with" is no field of the format) | low-medium | whole experiment | 0 |
| G2 | 158-159 | "a measurement needs a name of its own: 2 to 31 lower-case letters, digits and _, beginning with a letter, not the name of an output and not used twice ('x')" | Name: 2-31 characters, begins with a letter, not an output's name, not twice | P ("name (lower-case, for example <column>_max)"; length, first letter and "not an output's name" in no text) | low-medium | whole experiment | 0 |
| G3 | 161-162 | "measurement n: stat must be one of …" | stat from the list | S (format's list; tool line) | | | 0 |
| G4 | 163-164 | "measurement n: time_above needs level, the number to compare with" | level for the four level statistics | S ("level (the number time_above and the like compare with; null otherwise)") | | whole experiment | 0 |
| G5 | 167-168 | "measurement n: t_from and t_to are seconds of the simulation (or null: the measured seconds), t_from before t_to" | Window | S | | | 0 |
| G6 | 169-178 | "measurement n: of must be a column a simulation records, or arithmetic over columns of one record, in every design: design x does not record it. What x records: the series (every 0.1 s): … The probe (every 0.01 s; it only listens): …" | of must be readable in every simulation of the experiment (also those no rule uses it on; a changed network records other columns), all its columns from one of the two records | P ("takes of each of its simulations"; "arithmetic over columns of one record"; that one simulation without the column refuses the whole experiment is not stated) | medium; high where the structure changes | whole experiment | 1 (s061 N2) |
| G7 | 543-550; dr:147-149; 597-598 | check line "… : NOT CHECKED" with "simulation x gave no value for m" | A measurement that gives no value (first_time_above never reached, no sample in its window, undefined at every sample) is left out; every rule naming it is not checked; the hypothesis gets no ruling and stays open | N | medium (a level that is never crossed is a normal outcome) | simulations spent, test undecided, hypothesis blocks (E2) | 0 |
| G8 | 569-571; 536-542 | simulation record "probe: not used: the same simulation run without the probe gave another result" | Then no own measurement is taken: as G7 | N | low | as G7 | 0 |
| G9 | 1747-1754 | "the decision rule for H12 cannot be read: q_full_fine is not one of the outputs … q_full_fine is a measurement experiment X8 defined: … a rule may name it only where its own experiment defines it too (in measurements, the same definition again)" | A measurement belongs to the experiment that defines it | S ("a measurement this experiment defines") | | whole experiment / a round | 1 (s058 G42) |

## H. Reading a decision rule (decision_rules.py). In a first proposal an unreadable rule refuses the whole experiment (1743-1754); in a repair it is a round (3328-3330)

| id | where | message | rule | status | L | cost | real |
|---|---|---|---|---|---|---|---|
| H1 | dr:23 | "the decision rule for H cannot be read: cannot read '…'" | Only the listed signs (no %, !=, units, quotes) | S ("Write it exactly in this form: numbers; measure@label …; + - * / and parentheses; abs(), min(), max(); exactly one of < <= > >= == in each comparison …") | | | 0 |
| H2 | dr:63, 78, 108 | "a bracket is not closed" | | S | | | 0 |
| H3 | dr:71 | "unknown function f()" | Only abs, min, max | S | | | 0 |
| H4 | dr:79-80 | "abs() takes one value" / "min() takes two values or more, separated by commas" | Argument counts | N | low | as H13 | 0 |
| H5 | dr:83 | "X is not one of the outputs" | A rule names outputs and this experiment's own measurements only: not a series or probe column, not a setting | S ("measure@label (an output, or a measurement this experiment defines, …)") | | | 2 (s063 G29 named the column l1_q_tcp; s058 G42) |
| H6 | dr:85 | "say which simulation: X@label" | | S | | | 0 |
| H7 | dr:87; 1751-1752 | "no simulation in this experiment is labelled p0179 … A rule compares the simulations of its own test: to compare with one that ran before, list it among the runs with its settings (the same settings are returned, not run again)" | A rule names simulations of its own experiment | S27 | | | 6 (s059 N3 whole experiment; s056 G19, s059 G31, G33, s063 G19, G28 in repairs) |
| H8 | dr:89, 94, 124 | "a value is missing" / "each comparison needs exactly one of < <= > >= ==" / "comparisons are joined by AND or OR" | | S | | | 0 |
| H9 | 1755-1757 | "names m@l, but the network of simulation `l` has no such measure: a decision rule may only name measures that exist in every simulation it names" | | S (STRUCTURE, same words) | | | 0 |
| H10 | 1773-1778 | "the decision rule for H11 makes 4 comparisons, and a rule makes at most 3: keep the comparisons that decide what H11 claims, every part of it, and leave the rest, such as further settings, to a later test (a claim that needs more than 3 comparisons is more than one claim)" | COMPARISONS_MOST = 3 | S ("at most 3 comparisons, joined by AND and OR") | | a test (J7) / a round | 1 (s056 G39) |
| H11 | dr:156-157; 597-598 | check "not checked: division by zero" | A rule that divides by zero is not checked; as G7 | N | low | as G7 | 0 |
| H12 | 282-283 | "the decision rule for H names no measure: write it as measure@label, for example an output or a measurement of your own in the simulation with that label" | A rule must name a measure with @label | S (the form) | | whole experiment | 0 |
| H13 | 1743-1754 with 2200-2211 | part "experiment": "the decision rule for H6 cannot be read: …" | In the first proposal ONE unreadable rule refuses the whole experiment, every other test with it, and no round follows | P, and against the text ("A rule the harness cannot read comes back to you as a round of that test") | medium | every test of the turn | 1 (s059 N3) |

## I. A rule against its simulations

| id | where | message | rule | status | L | cost | real |
|---|---|---|---|---|---|---|---|
| I1 | 2473-2491 (lean_needs), 2189-2193 | "the simulations the rule for H9 compares (q4_cubic, q4_linuxreno, q1000_cubic) differ in more than one setting (l1.queue.length, tcp.type): a difference in the measure then has more than one possible cause. Make them differ in one setting only, or test the settings in separate hypotheses" | All simulations named by all rules of one hypothesis, taken together, may differ in one setting only (not: each pair a rule compares); in a first proposal the whole experiment is refused | P ("The simulations one rule compares must differ in one setting only": said per rule; a rule with a shared control and two one-setting comparisons is refused; that the whole experiment falls is not stated) | high | whole experiment / a round | 3 (s055 N10 whole experiment; s056 G58, s065 G8 in repairs) |
| I2 | 319-320 (needs_problem) | "the decision rule for H does not name `m`, the measure its need says decides it" | Every rule of one hypothesis must name the first measure of its first rule | N ("need" is no part of this arm's answer) | low-medium (0 of 88 real tests had two rules) | whole experiment | 0 |
| I3 | 1837-1848 | "this decision rule names only results that are already in the ledger (q1000_cubic = S2), so it cannot fail and is no test. What the known results show belongs in a why or in observations; a test needs a simulation whose result you do not know yet" | A rule all of whose simulations ran before is refused, unless it names a measurement of this experiment | S ("A rule must be able to fail: it names at least one result you do not know yet. A rule on a measurement of your own may be about simulations you already ran") | | a test / a round | 1 (s056 G15) |
| I4 | 286-307, 316-325 | "the need of H must list its simulations …", "the need of H says …" | Checks of derived needs; not reachable in this arm as far as I could follow, except I2 | - | - | - | 0 |

## J. The competing guess of a rule (competitor_problem 429-455). In round 1 the test is left out by a note with NO repair round (3260-3271); in a repair it is a round

| id | where | message | rule | status | L | cost | real |
|---|---|---|---|---|---|---|---|
| J1 | 433-434 | "the decision rule for H names the guess it competes with: competes_with, the id of another guess (for example Y3) …" | competes_with required | S (format; instructions) | | | 0 |
| J2 | 435-437 | "competes with Y17, which is not a guess in the ledger: name an existing guess, or write the competing guess first (it is reviewed like any guess) and test against it in a later turn" | The competitor must be a recorded guess (one of this same answer counts) | S ("write the competing explanation as a guess first"); the message's "in a later turn" is not what the code requires | | a test (J7) | 3 (s055 N6) |
| J3 | 438-443 | "competes with Y10, which Y29 revised: name the live guess (Y29, or another)" / "… Y5 is H5's own guess, so name another live guess that explains the same result otherwise, or write one" | Not a revised guess | P ("another live guess": live is not explained) | medium | a test / a round | 4 (s055 N14, s066 N2; s057 G40, s056 G18) |
| J4 | 444-446 | "competes with Y23, which the ruling V8 refuted: name a live guess" | Not a refuted guess | P (a refuted guess's ledger line: "no guess or test may name it as a competitor") | medium | a test / a round | 2 (s057 N16, s065 G15) |
| J5 | 447-450 | "competes with Y4, which is H's own guess Y4 or one linked to it by revises: a test tells its guess from ANOTHER explanation of the same result" | Not the hypothesis's own guess or its revises family | S ("not the hypothesis's own nor one linked to it by revises") | | | 0 |
| J6 | 451-454 | "this decision rule would hold if Y3 were true too, so it cannot tell the two apart: choose simulations where the two guesses give different results" | rival_predicts held is refused | S ("held is refused") | | | 0 |
| J7 | 3260-3271 | "refused part of the answer: test of H8. Reason: …" | A test the harness refuses in round 1 (J2-J6, H10) is left out and gets no round to repair; the hypothesis stays open and blocks (E2) | P (the instructions promise a repair "at once" for the supervisor's refusals and a round for an unreadable rule) | medium | a test this turn, often the next turn | 6 (s055 N6, N14, s057 N12, N16, s062 N5, s066 N2) |

## K. Review rounds and repairs

| id | where | message | rule | status | L | cost | real |
|---|---|---|---|---|---|---|---|
| K1 | 3231-3232, 3245-3251 | "the test of H4 is not run in this turn and H4 stays open: the supervisor names a competing cause that is none of your guesses: <the cause> Write it as a guess (competes_with: Y2), then test H4 against it" | When the supervisor names a competing cause no guess states, the test is held: not run, no repair | N ("If one does not pass, it says what is wrong and you repair that test at once") | high | test not run, hypothesis blocks: usually a turn | 4 (s055 G9, G11, s063 G21, s065 G32) |
| K2 | 3231-3232, 3250 | "the test of H is not run and H stays open: after the last round it does not test its claim (Consistent failed): …" | After round 3, a test whose box Consistent did not pass is not run | N (the researcher's texts say nothing of what follows the last round; the supervisor's own text says "A test sent back in round 3 is run all the same, marked as contested", 1207) | high | two repair calls, test not run, hypothesis blocks | 6 (s056 G16, G40, s063 G11, G20, s065 G16, G28) |
| K3 | 3220, 3295-3296, 3422-3424 | review line "run, but the supervisor still objects after the last round" | After round 3 with another box failing the test runs, contested | N, in the researcher's favour | - | none | 2 |
| K4 | 3392-3397 | "your repair of the test of H for round 2 could not be read (…): the test is not run in this turn and H stays open" | An unreadable repair (also one cut at 12,000 tokens, 1055) ends the rounds | N | low | test not run | 0 |
| K5 | 3401-3409 | review by the harness "SENT BACK …" then "the test of H5 is not run: its last repair could not be used (…); H5 stays open" | Every check of the harness on a repair counts as a round; refused in round 3 the test is not run, the supervisor never having seen it | P ("A rule the harness cannot read comes back to you as a round of that test": only unreadable rules) | high | rounds, then the test | 13 sent back + 9 not run (s056 G19 / N5) |
| K6 | 3061-3063, 3303-3317 | none | A repair holds one decision rule (several rules of the test become one) and cannot define a measurement; only measurements of the answer may be named | P (repair request: "a repair changes the rule, the guess it competes with and the simulations"; "a measurement your answer defines (listed above)") | medium | a round | 2 (s058 G42, s063 G29) |
| K7 | 3312-3315 | none | Simulations the repaired rule does not name leave | S (repair request: "A simulation your repaired rule does not name is not run") | | | |
| K8 | 3338 with 1732; 3355, 3374 | "the experiment needs 3 new simulations; with 3 left, one experiment may run at most 2 (half of what is left) …" | A repaired test is held to half of what is left after the approved tests, while the repair request says "(3 can still run)" | P (number in the text differs from the number enforced) | medium at a small budget | a round | 0 |
| K9 | 3308-3312, 3408 | "every simulation needs its own label: letters, digits and _ only, at most 20 characters" | FAULT: the simulations of a repair the harness refused are kept twice (as kept and as written); the next repair that names one of them again gets that label twice and is refused, although its own labels are right | N; the reason given is false | certain in that case | the last round, test not run, hypothesis stays open | 2 (s059 G34 -> N15, test labels p0188_len1000, p0188_len100, p0188_len100; s063 G30 -> N7) |
| K10 | 3390 | - | The repair call carries only REPAIR_SYSTEM_COMP (+ STRUCTURE) and the request, not the instructions: label form, the one-setting rule, the number of simulations, value ranges, what a measure is are enforced on a repair and stand in neither ("in the form of your instructions") | P | medium | a round | part of K5 (s056 G58, s065 G8: one setting; s063 G29: a column as a measure) |
| K11 | 1322-1342 | "the supervisor's review of this test could not be read, twice, so no box could be told. Send the test again, as it is or changed." | A review unreadable twice counts as refused | N | low | a round | 0 |
| K12 | 3456-3462, 3438-3448 | "the supervisor's ruling on H could not be read (…): H stays open" then "… has no ruling: the supervisor is asked for it again" | An unreadable ruling is asked for once more next turn | N | low | none | 0 |
| K13 | 3364-3365 | repair request: "The hypothesis's sentence and its guess stay as they are …" | A repair cannot change the hypothesis's sentence | S27 | | | |
| K14 | 3276-3284 | none | A test whose guess was restated in the turn is reviewed again alone | N, no cost | - | none | - |

## L. Changes of the network's structure (network.py through structure_problem 76-93; in a first proposal the whole experiment is refused, 1719-1722: S "A simulation whose network cannot be built is refused with the reason, and the rest of the experiment is not run")

| id | where | message | rule | status | L | cost | real |
|---|---|---|---|---|---|---|---|
| L1 | net:478-479 | "change 1: do must be one of …" | | S (format) | | | 0 |
| L2 | net:481-482 | "change 1: a new object needs an id of its own: at most 12 lower-case letters and digits that begin with a letter, not used yet (got 'x')" | Every new host, link and flow; "not used yet" across hosts, links and flows together | P (the form is stated for add_host only; one name space for all three is not stated) | medium | whole experiment / a round | 0 |
| L3 | net:209, 113 | "the id rate is kept for a setting of the simulation" | 20 words may not be ids (duration, seed, queue, parts, rate, delay, type, loss, …) | N | low | whole experiment | 0 |
| L4 | net:487-488, 217 | "a link joins two hosts of the network (from, to)" | | S | | | 0 |
| L5 | net:490-491 | "a new link states its rate" | | S ("rate (state it …)") | | | 0 |
| L6 | net:220 | "… are joined by a link already (one link for each two hosts)" | | S ("One link for each two hosts") | | | 0 |
| L7 | net:224, 256 | "link l: rate = 'x' is not a value the program accepts" / "flow f: rate = 'x' is not a rate" | Rate form | P ("written as the brief writes rates") | low | whole experiment | 0 |
| L8 | net:586-589 | "link l carries 1Gbps: this brief allows at most 100Mbps for a new link" | Cap of a new link; also for a link of the brief taken out and put back changed | S where the brief caps (structure_text fills the cap); P for the put-back case | low | whole experiment | 0 |
| L9 | net:494-497 | "a flow needs a kind (udp or tcp) and two hosts of the network (from, to)" / "app is onoff …, bulk … or empty" | | S (bulk is accepted and not described) | | | 0 |
| L10 | net:260 | "flow f: type must be one of TcpCubic, TcpNewReno, TcpLinuxReno, TcpBbr, TcpVegas, TcpBic" | TCP types of a new flow | N (STRUCTURE: "type for tcp (left empty: TcpCubic)"; the list is nowhere) | low-medium | whole experiment | 0 |
| L11 | net:181, 242, 245 | "flow f has 2 equally short ways from a to c: remove a link so that there is one way" / "there is no way from a to c" | One shortest way | S ("a flow needs exactly one such way") | | | 0 |
| L12 | net:501-504 | "a queue is put on a side of a link that has none there (id: the link; on: one of its two hosts)" | A queue only on a side that has none | S27 | | whole experiment | 1 (s063 N2) |
| L13 | net:505-506 | "a new queue states its kind: one of …" | | S ("kind (state it)") | | | 0 |
| L14 | net:301-302 | "no flow passes <the scheduler>: a scheduler divides its link between the flows that pass it on that side" | A scheduler on a side no flow is sent from is refused | N | low-medium | whole experiment | 0 |
| L15 | net:526-527 | "link l has a queue on each side: say which one (on: a or b)" | | S ("where the link has a queue on each side, on says which") | | | 0 |
| L16 | net:535-536 | "there is no flow 'f1' to remove (kind: host, link, flow or queue; a queue's id is its link's)" | The object must exist by the brief's id | S | | a round | 2 (s055 G10, s056 G7) |
| L17 | net:211-212 | "a network needs at least two hosts, one link and one flow" | | N | low | whole experiment | 0 |
| L18 | net:567 | "3 flows: this brief allows at most 2" | The brief's structure.most | S ("The brief's structure says how many hosts, links and flows a network may have at most") | | a round | 2 (s056 G38, s066 G10) |
| L19 | net:203-204, 42 | "9 hosts: a network holds at most 8" | Where the brief states no number: 8 hosts, 12 links, 8 flows | N | low | whole experiment | 0 |
| L20 | net:590-593 | "flow udp may not be removed (the operator keeps it)" | Locked objects | S ("which objects you may not remove") | | | 0 |
| L21 | net:594-598 | "flow udp may not be replaced: the operator keeps it as the brief states it (it was taken out and put back with other values; a setting of it that is a knob is set by its knob)" | A locked object may not be removed and added again with other values | P (only "may not remove") | medium | whole experiment | 0 |
| L22 | net:599-602 | "the aim is about m, which this network would not have: what the aim measures cannot be removed" | | S ("what the goal measures cannot be removed either") | | | 0 |
| L23 | 89-93 | appended to L1-L22: "A change written correctly for this network, for example: [{…}]" or "The change is written correctly, but this brief does not allow it: change a part the network has instead of adding one" | - | see list (a) | | | 5 |
| L24 | tools:67; net:312-356 | none | A knob of an object the change removed sets nothing: the value the simulation states for it is ignored with no note, the evidence line still prints it as a changed setting, and two simulations that differ only in it are both run | N | medium (a queue removed and not replaced; part knobs after a scheduler is replaced) | simulations spent on a comparison of nothing | 0 (in the real simulations that replaced a queue, about 70, the queue's length knob still applied) |
| L25 | net:428-453 | none | A flow that is new at a scheduler that stands gets the mean of the parts there | N, no refusal | low | none | - |
| L26 | 187-214 | none | Two change lists that build the same network are one simulation; a list that changes nothing is the brief's network | S (the repeated-simulation sentence) | | | |
| L27 | 62 | none | A change that is no object is dropped; empty fields become "" | N, harmless | - | none | - |

## M. Requests and tools

| id | where | message | rule | status | L | cost | real |
|---|---|---|---|---|---|---|---|
| M1 | 3598, 3639-3641 | "only the first 6 requests of a reply are answered: 2 more were left unanswered (…)" | LOOKS = 6 | S ("Up to six requests in a reply"; format maxItems) | | | 0 |
| M2 | 2975-2982 | "unknown tool" / "error: measure() got an unexpected keyword argument 'x'" | A wrong argument gives Python's own error text | P (the tool lines name the arguments) | low | a request | 0 |
| M3 | tools:411-415 | "error: unknown run 'S3'" | Run ids (r003) of this session only | S (tool line: "run ids are in the evidence lines, e.g. r003") | | | 0 |
| M4 | tools:424-425 | none | series: at most 100 rows; every_n is raised without a word so that the rows span the run | P ("at most 100 rows") | low | none | - |
| M5 | 2982, 702 | reading ends " ...[truncated]" / "(cut here: N characters in all)" | A reading longer than 6,000 characters is cut; of a series the last rows (the end of the run) are lost unless it is asked again with a larger every_n | P (said only in the turn after a request was answered, 3555; not in the instructions or the tool lines) | medium (100 rows of a network with several queues) | part of a reading | 2 (s057 T6, T7) |
| M6 | 700-711 | "(... N more characters of this reading are left out here, to keep the ledger within its size: ask again with the same request for the whole of it)" | Past 40,000 characters of readings, long ones (over 1,500) older than the newest four are shortened to 600 | P (same line: 40,000 stated; 1,500, 600 and "four" not) | low | part of an older reading | 0 |
| M7 | tools:445 | none (the answer's "every_s" shows the value used) | probe's every is forced into 0.001 to 1 s | N | low | none | 0 |
| M8 | tools:455-459 | "error: the simulation run again with the probe did not give the same result as before …: the probe's record is not kept" | | S (tool line) | | | 0 |
| M9 | tools:481-498, 523-536 | "error: stat must be one of …" / "error: … is not recorded for this simulation. The series has: … made by probe(run_id): ask for it first" / "error: no sample between 0 s and 0.02 s (the series runs from 1.001 s to 12 s)" / "error: … needs level" | measure's own checks | S (tool line), except that the series' first sample time is in no text | low | a request | 2 (s055 T4, T5: no sample) |
| M10 | tools:518-522 | none | The window holds the samples after t_from, up to t_to | S27 | | | |
| M11 | tools:552-561; schema requests.tool | "this simulation has no packet trace (the program that builds a network writes none)" | grep_trace is in the format's list of tools and not in a network brief's tool lines; pattern cut at 200 characters | N | low | a request | 0 |

## O. Findings and decisions (settle_findings 2736-2797; only that finding or decision is left out)

| id | where | message | rule | status | L | cost | real |
|---|---|---|---|---|---|---|---|
| O1 | 2746-2747 | "a finding needs text: one sentence, what the results do not explain, with its numbers" | | S | | | 0 |
| O2 | 2744-2750 | "about must name the records it rests on: ids of evidence tables, simulations, checks, verdicts or readings in the ledger (for example E2, C3, T7); not such a record: Y3" | A finding rests on E, S, C, V, T (or G) records | S ("about (the ids of the records it rests on: evidence tables, simulations, checks, rulings or readings …)") | | a finding | 0 |
| O3 | 2597-2600, 2581 | none | name cut to 5 words and to 48 characters | P ("at most 5 words"; 48 characters in no text) | low | none | not countable |
| O4 | 2760-2761 | "a decision names a finding by its id (F1, F2, ...): 'x' is not one" | | S | | | 0 |
| O5 | 2763-2764 | "a finding gets one decision in an answer" | | S ("one for each") | | | 0 |
| O6 | 2766-2767 | "F3 is closed already: if it is unexplained again, state it as a new finding" | No decision on a closed finding | N | low | a decision | 0 |
| O7 | 2774-2776 | "park needs a reason: why not now" | | S | | | 0 |
| O8 | 2772, 2779-2785 | "work needs refs: the why, hypothesis, experiment or reading that works on it (one of this answer by the id it gets), or requests or an experiment in this same answer; not usable here: H17" | refs of work must be recorded Y, H, X, T, C or E ids: a part of this answer that was not accepted, or an experiment or reading id guessed wrongly, leaves the decision out | P ("one of this answer by the id it will get": the turn's NEW IDS gives only Y and H numbers; the X and T ids of this answer are not told, and a repaired test gets an X of its own); the message offers "requests or an experiment in this same answer", which the code no longer counts (2779 comment) | medium | decision left out, the finding stays DUE | 3 (s056 N26, N27, s057 N6) |
| O9 | 2781-2783 | "close needs refs: the evidence, checks, verdicts or readings in the ledger that explain it" | | S | | | 0 |
| O10 | 2786-2787 | "left out of its refs, not records a close decision can name: Y8; the decision stands with T6, …, E3" | A guess or hypothesis cannot close a finding: it is taken out of refs, with a note | S ("close: refs names the evidence, checks, rulings or readings that explain it") | | a ref | 20 (s056 N6; s059 N4-N11); 1 more on a work decision (s062 N6) |
| O11 | 2789 | none | same_as keeps the first ref only | N, harmless | - | none | - |
| O12 | 2795-2797 | "no decision for F15, which was due this turn: it stays open and is asked for again in the next turn" | A reminder; nothing is refused | S ("one for each finding the list marks DUE") | | | 2 (s056 N28) |
| O13 | 2618-2621, 2637-2639 | - | A finding counts as looked at only through ids named in a decision's refs (or a guess about it) that reach a reading, check or evidence table | P ("left empty, it counts as worked on but not as looked at") | medium | the report held (P2) | 0 holds |

## P. The final report

| id | where | message | rule | status | L | cost | real |
|---|---|---|---|---|---|---|---|
| P1 | 3730-3732 | "the report is held back: this answer's experiment (X7) ran in this turn, and its results and checks come to you in the next turn. Give the report after you have read them" | A report sent with an experiment is not taken | N | medium (a last test sent with the report) | one more turn | 0 |
| P2 | 3733-3737 | "the report is held back: these findings were never looked at (no reading, check or evidence reaches them): F3. Look at each first (a reading, a measurement on simulations already run, or a test), or close it with the records that explain it; then give the report" | Held while an open or working finding was never looked at; at most FINDING_HOLDS = 2 turns | S ("A final report is held back while a finding that is not parked was never looked at … and you can still work"); the 2 is in no text (in the researcher's favour) | | a turn | 0 |
| P3 | 3738-3741, 2803-2811 | "open_questions did not name F12, F13: the harness added them there, as not resolved" | The harness adds the findings not named to the report | P (the text asks the researcher to name them) | medium | the report is changed | 1 (s062 N17) |
| P4 | 1648-1654 | "report.goal must be a text" / "report.limit must be a text: what limits the result at your recommendation … if you did not find it, say so and what you would test next" | | S | | | 0 |
| P5 | 1678-1685 | "report.recommendation must state a value for every knob of the brief …" | | S (format) | | | 0 |
| P6 | 1686-1691 | "report.recommendation has a value outside its allowed range: k=v" | A recommended value outside its range refuses the whole report (in a simulation it is moved into the range) | P (only the format's description: "each within its range") | low-medium | report refused: a turn, or A10 | 0 |
| P7 | 1671-1677 | "report.structure cannot be used: …" | The rules of L for the recommended network | as L | low | report refused | 0 |
| P8 | 1694-1701 | "report.claims must be a list of {text, role, evidence: [ledger ids]}" / "report.claims cites ids that are not in the ledger: x" | One id that is not in the ledger (a simulation's label, for instance) refuses the whole report | P ("evidence: the ids of the checks, rulings, evidence tables and readings that support it": that one wrong id refuses the report is not stated; "role" is no field of this arm) | medium | report refused: a turn, or A10 | 0 |
| P9 | 2223-2224 | none | A run id in a claim's evidence becomes its simulation's id | N, harmless | - | none | - |

## Q. What the harness changes in the supervisor's words before they reach the researcher

| id | where | message | rule | status | L | cost | real |
|---|---|---|---|---|---|---|---|
| Q1 | 1255-1258, 1394-1397, 3241-3242 | "the harness cut 1 part(s) of the supervisor's feedback on the test of H (round 2): they wrote a decision rule, and the repair is the researcher's" | Sentences of feedback that hold measure@label are cut | N | - | less feedback | 0 |
| Q2 | 1600-1603, 1617 | none in the ledger text (the record keeps changed_by_harness; shown() 645-651 does not print it) | A ruling that does not fit the checks or its three boxes is recorded as inconclusive | N | - | a ruling changed without a word | 0 |
| Q3 | 1635-1639 | none | The same for the second look after an objection | N | - | | 0 |
| Q4 | 2847-2861 | "a finding of the supervisor was left out: it cites ids that are not in the ledger (p0179, …)" / "… it states no measured number" | | N | - | none | 2 (s059 N13, N14) |
| Q5 | 1349, 1386 | review line "Follows cannot tell, …" | A box that is "cannot tell" (or unreadable) counts as failed at the review | N to the researcher | - | a round | not counted |
| Q6 | 3468-3469 | "the supervisor's ruling on H ran on in its findings and was cut off at its limit: the ruling stands, its findings are left out" | | N | - | none | 0 |
| Q7 | 387-413 | ledger line of the guess: "refuted by the ruling V… : no new hypothesis is accepted from it, and no guess or test may name it as a competitor; a new guess may revise it" | When a guess is refuted | S ("a guess is refuted when a fair test of a hypothesis that follows from it fails, or when the supervisor finds that it does not fit a fair test's result …") | | | |

## Counts

Rows: 175 (A 15, B 4, C 1, D 14, E 5, F 22, G 9, H 13, I 4, J 7, K 14, L 27, M 11, O 13, P 9, Q 7). Three carry no status of their own: I4 (checks I could not reach in this arm), L23 (a sentence appended to other refusals), P7 (the rules of L applied to the report).
Stated: 84 (of them stated since 2026-11-27: 5 - F13, H7, K13, L12, M10). Partly: 35. Not stated: 53.
Of the 53 not stated: 12 cost the researcher nothing or are in its favour (A12, A14, A15, D8, D14, K3, K14, L25, L27, M7, O11, P9); 6 are changes the harness makes to the supervisor's words (Q1-Q6); 35 can cost the researcher a part, a test, a turn or the session.

## (a) Messages that suggest what to do, or hint at an answer

1. loop.py:3248-3249 (K1): the supervisor's competing cause, word for word, then "Write it as a guess (competes_with: Y2), then test H4 against it". The supervisor's rival explanation reaches the researcher with the instruction to adopt it. 4 real.
2. loop.py:442 (J3): "name the live guess (Y29, or another)" names the id to write. 443: "so name another live guess that explains the same result otherwise, or write one". 436-437: "name an existing guess, or write the competing guess first … and test against it in a later turn". 446: "name a live guess".
3. loop.py:2005-2009 (D4): "Name its id in about (for example V2, C3, E2, T7, G4) and say in result what it showed; made since your last guess: <the ids>"; "test what is open, or look with a request, before you guess again"; "An explanation not tried yet may be stated without a new record as the competitor of an earlier guess: name that guess in competes_with and cite a record it cites".
4. loop.py:1996-1998 (D3): "A guess this one explains otherwise goes in competes_with, one it states more exactly in revises".
5. loop.py:2020-2021 (D10): "State what the cited records show, and what in them is new, or leave the guess".
6. loop.py:2114-2115 (E2): "test it (send the experiment), or give it up in drop with what you learned, before you state another hypothesis". 2117: "state the ones you will test now".
7. loop.py:2196 (F13): "to look around without a rule, use an explore experiment".
8. loop.py:2488-2489 (I1): "Make them differ in one setting only, or test the settings in separate hypotheses".
9. loop.py:1733-1734 (F7): "Keep the simulations that decide your hypotheses and leave the others out".
10. loop.py:1751-1754 (H7, G9): "to compare with one that ran before, list it among the runs with its settings"; "(in measurements, the same definition again)".
11. loop.py:1776-1778 (H10): "keep the comparisons that decide what H claims, every part of it, and leave the rest, such as further settings, to a later test".
12. loop.py:454, 1789 (J6): "choose simulations where the two guesses give different results".
13. loop.py:1824, 1828, 1836, 1848 (F14-F16, I3): "change the designs or the rule"; "give it different settings or remove it"; "What the known results show belongs in a why or in observations; a test needs a simulation whose result you do not know yet".
14. loop.py:91 (L23): "change a part the network has instead of adding one". loop.py:93: "A change written correctly for this network, for example: [...]" (a real change on a real link of the brief; the comment at 96-99 calls it form only).
15. loop.py:3735-3736 (P2): "Look at each first (a reading, a measurement on simulations already run, or a test), or close it with the records that explain it; then give the report". 3731: "Give the report after you have read them". 2671: "Look at them in these turns: a reading or a measurement on simulations already run costs no simulation".
16. loop.py:2767 (O6): "if it is unexplained again, state it as a new finding".
17. loop.py:1339 (K11): "Send the test again, as it is or changed."
18. loop.py:283 (H12): "write it as measure@label, for example an output or a measurement of your own".
19. loop.py:3556, 3559-3563: "decide now"; "state your hypotheses and their test now".
20. tools.py:422, 498; loop.py:701: "ask for probe(run_id) first"; "ask again with the same request for the whole of it".
21. network.py:242: "remove a link so that there is one way"; 527: "say which one (on: a or b)".
22. Repair request, loop.py:3364-3374 (a request, not a refusal): "If the objection is to the sentence itself, no repair meets it: send the test as it stands, and if it is then not run, drop the hypothesis in your next reply and state a new one"; "write it as a guess in your next reply"; "choose simulations where the two differ"; "name at least one simulation that has not run yet (N can still run), or such a measurement".

Messages that speak of parts this arm's answer does not have: D1 (unseen, matters, reason), D2 and D6 ("why", "verdicts"), G1 ("with"), I2 and H12/I4 ("need"), A3 ("verdict"), P8 ("role"), O8 ("requests or an experiment in this same answer").

## (b) Numbers in the texts against the constants

1. Repair request (3355, 3374) "(N can still run)": N = budget - used - reserved. Enforced on the repaired test (3338 -> 1732): spend_cap(N) = half of N rounded up, at most the brief's number per experiment. They differ whenever N >= 3.
2. Turn text (3546) "This turn's experiment may run at most C new simulations": each repaired test is run as an experiment of its own and held to its own cap (3703-3708), so a turn can run more than C.
3. Measurements: at most 8 (134), name of 2 to 31 characters (158): in no text; the format has no maxItems and no pattern.
4. Finding name: NAME_CHARS = 48 (2581) in no text; NAME_WORDS = 5 is filled.
5. Tokens: 32,000 for a reply with its draft (3181), 12,000 for a repair or a restatement (1055), 100,000 for the ledger (32): in no text of the researcher.
6. UNUSABLE = 3 (36): said only in the last turn it causes. FINDING_HOLDS = 2 (2583): nowhere. LOOKS = 6 as "turns in a row that only look" (1066, 3650): nowhere.
7. CAP = 6,000 and READINGS_ROOM = 40,000 are filled from the constants (3555) but shown only in a turn after a request was answered; 1,500, 600 and "the newest four" (700, 706-710) are typed in the code and stated only inside a shortened reading.
8. STRUCTURE types its numbers as text, none filled from a constant; today they equal the code's: "at most 12 lower-case letters and digits" (net:41 ID), "50us" (net:456), "1500 bytes" and "a device queue of 10 packets" (net:492), "100 packets" three times (net:507), "100Mbps" and "1400 bytes" (net:498), "TcpCubic" (net:500). Only a capped brief's rate and delay are checked at the start (stated_new_link 248).
9. The measured seconds begin at 2 s: typed in schema.json (t_from "(2)"), in manifest.json ("from 2 s to the end"; "the measured seconds begin at t = 2"), and as 2.0 in tools.py:518 and loop.py:1194; none is taken from the brief.
10. manifest.json: "at most 100 rows" (tools:424-425, typed twice in the code), "left out: 0.01" (PROBE_EVERY, tools:427), "at most 50" (tools:559): equal, typed.
11. Supervisor's texts: "FINDINGS (findings, at most 2, or none)" and "at most 2" are typed (2828, 2831) beside SUP_FINDINGS = 2; "A test sent back in round 3 is run all the same, marked as contested" (1207) differs from the code (K2).
12. Filled from the constants and equal: REVIEW_ROUNDS, LOOKS (requests of a reply, also the format's maxItems), CONTINUES, OPEN_MOST, LABEL_MOST (also maxLength), COMPARISONS_MOST (also in the repair request), FREE_TURNS, PARK_TURNS, NAME_WORDS, the tolerance, the budget numbers of the turn.

## (c) Rules the texts state that the code does not enforce, or enforces differently

1. "The simulations one rule compares must differ in one setting only" - enforced over all rules of one hypothesis together (I1).
2. "A rule the harness cannot read comes back to you as a round of that test" - in a first proposal the whole experiment is refused and no round follows (H13); in a repair every check of the harness is a round, not only an unreadable rule (K5).
3. "If one does not pass, it says what is wrong and you repair that test at once (three rounds at most …)" - no repair when the supervisor names a missing competing cause (K1) or when the harness refuses the test in round 1 (J7); after round 3 the test is run contested or not run at all, by the box Consistent (K2, K3).
4. "A simulation with the same settings as an earlier one is not run again: its result is returned and costs nothing" - true across experiments; inside one experiment the second one is cut and a rule that names it is refused (F14, F15).
5. "a value outside its range is moved into it" - in the report's recommendation it refuses the report (P6); a choice not on the list becomes the default (F22).
6. STRUCTURE: "A new queue holds 100 packets" - where the brief has the knob <link>.queue.length, the new queue takes the value the simulation states for that knob (tools:67, net:339-356); real: 20 simulation designs with a replaced queue and another length, for example s057 X4 sched_cubic_q1000. The opposite case: a queue removed and not replaced, where the knob is ignored (L24).
7. STRUCTURE: "The brief's structure says how many hosts, links and flows a network may have at most" - where it says none, 8, 12 and 8 hold (L19).
8. FINDINGS: "A final report is held back while a finding that is not parked was never looked at" - at most twice (P2).
9. FINDINGS: "\"it does not change the recommendation\" alone is no reason" - a park's reason is not read (2774-2778).
10. FINDINGS: "decisions: one for each finding the list marks DUE" - a note only (O12).
11. "the word brief only when nothing is measured yet" - brief is accepted in about at any time (1991); only the chain rule (D4) limits it.
12. "state at most three in one answer, with the experiment that tests them" - hypotheses without an experiment are accepted (and then block, E2).
13. "A turn ends with a step" - after three replies without one the turn ends all the same (3653).
14. "Keep every text short: one or two sentences" - not checked.
15. STRUCTURE on add_flow describes app "" and onoff; "bulk" is accepted too (net:496).
16. Not checked against the simulator (outside this review): "A new link has … on each of its two sides, a plain queue of 100 packets" and "Where a queue is removed, a plain queue of 100 packets … stands in its place": network.apply adds no queue to a new link (net:492); what stands there is the program's default.

## Not gone through

- loop.py: render/shown/record_line and the supervisor's request builders (_case, _measured, _looked, guesses_text, first_review, values_before) were read for cuts only, not for what they show; judge_link, rethink, the arms "hypotheses" and "plain", short_format, plain_format, prompt.txt were left out (not this arm).
- network.py: problems() lines 225-310 (ends of a link, classes, largest_rate, flow times), text() and outputs() were read by their messages only; with_values and sync in part.
- tools.py: check_brief (a brief's own checks, not the researcher's answer) skimmed.
- control.py, fairness.py, text_audit.py, the viewer, and the ns-3 programs: not read. What the simulator does with a setting or a new link is not verified.
- The texts were read from the code of this frozen copy; the s065 session.json prompt (older) only for the turn's text as sent.
- From calls.jsonl only agent, step, turn, system, user of s065 were read; no reasoning, no draft, no drafts.jsonl.
