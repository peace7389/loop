# The texts of v2, audited by the mechanical tests (2026-11-25)

Made with `harness/text_audit.py` (v2, stage 7), on the tree of branch `v2` after stages 7b and 7c. It follows the audit by reading of
`2026-11-24-prompt-audit.md`: that one found what the texts said; this one is the test that can be run again after every change of a text.
A marked line is a candidate for a pointer to an answer; an unmarked line is listed so that it can be read.

## What it found

1. **In v2's own texts, before the fixes of this stage** (each is fixed; the texts before and after are in `v2/texts_stage7b.md` and
   `v2/texts_stage7c.md`):
   - the paragraph on changes of the network said "rate (state it, for example 1Gbps)" in a brief that does not cap a new link: an example value,
     the rate of the brief's fast links. Now: "rate (state it, written as the brief writes rates)";
   - the same paragraph began its list of the kinds of queue with "The kinds, each ns-3's queue disc of that name except the scheduler: codel
     ...": the scheduler was named before the list and apart from the others. Now: "The kinds: codel: ...", alphabetical, 10 to 16 words each;
   - the answer format's line on the records of a finding said "checks, verdicts" in every arm: the arm "plain" is never told of either, the
     arm "supervised" has rulings. Each arm's line now names what the arm's own text on findings names;
   - the three briefs of v2 listed the TCP types with the default first. Now alphabetical (the default stays TcpCubic).
2. **Still marked, left for the operator**: the brief `after_fix` lists its TCP types with the default first. It is unchanged in v2 because its
   earlier sessions read it so; a copy with the list in alphabetical order (and, as noted in `v2/REVIEW.md`, its TCP flow locked) would be a new
   brief.
3. **For comparison, the texts s062 was in fact sent** (2026-11-25, on main, brief after_fix2): five marks, among them the two the operator
   called the scheduler hint: the kinds of queue listed "scheduler, fifo, pfifofast, codel, fqcodel, red, pie", and the sentence "A scheduler
   gives each flow that passes it a part of the link; fifo is one queue for all". Its answer (the scheduler in place of the queue) is simulated
   and named in turn 1 (`session_figures.fairness_figures`). On v2 these sentences do not exist.
4. **Not tested mechanically**: whether a number a text states equals the code's constant. Since stage 3 the texts are filled from the constants
   when the program starts, and the harness checks compare the sizes and the limits.

The supervised researcher's instructions with competitors are 9,978 characters of the limit of 10,000 where the network is fixed; with the
paragraph on changes of the network they are about 13,330 (the limit of 10,000 is checked on the part without that paragraph, as before).

# The four briefs of the run plan, as built

## Brief after_fix: the texts as built for a new session

| Text | Characters |
|---|---|
| supervised: the instructions | 13,325 |
| supervised: the answer format's descriptions | 5,478 |
| hypotheses: the instructions | 24,179 |
| hypotheses: the answer format's descriptions | 8,662 |
| plain: the instructions | 15,251 |
| plain: the answer format's descriptions | 4,302 |
| the supervisor: its instructions | 1,606 |
| the brief: its task | 288 |
| the brief: its description | 683 |
| the brief: the meaning of its settings | 86 |

**Examples**: 47 found, 0 marked.

- [supervised: the instructions] Each has about (the ids of the records it starts from, for example E0, S2, C1, V1, a reading T7, an objection of the supervisor G4; the word brief only when nothing is measured yet), result (that result in one sentence, with its numbers), guess (what in the system would make it so), revises (the id of an earlier guess this one replaces or states more exactly; or null), and competes_with (the id of an earlier guess whose result this one explains by another cause, or null; it may cite that guess's records).
- [supervised: the instructions] Each has name (lower-case, for example <column>_max), of (a column a simulation records over time, or arithmetic over columns of one record: the columns the tools series and probe name in the brief), stat (one of the statistics the format lists), t_from and t_to (seconds; null: the measured seconds) and level (the number time_above and the like compare with; null otherwise).
- [supervised: the instructions] objections: if the records show that a ruling of the supervisor is wrong, object once: to (the ruling's id, for example V2) and because (the numbers it overlooked).
- [supervised: the instructions] report: null until you can answer the task; then the final report, which ends the session: goal (the goal your answer is best for; if the brief's goal is open, the one you chose and why), recommendation (a value for every knob of the brief), limit (what limits the result at your recommendation, and the ledger ids that show it; if you did not find it, say so), explanation (why, in a few sentences), claims (the statements your answer rests on, each with text and evidence: the ids of the checks, rulings, evidence tables and readings that support it, for example C2, V1, E3, T7).
- [supervised: the instructions] - findings: each new one, once: about (the ids of the records it rests on: evidence tables, simulations, checks, rulings or readings, for example E2, C3, T7) text (one sentence: what is unexplained, with its numbers) and name (at most 5 words, to show it by).
- [supervised: the instructions] - A guess of why whose about names a finding (for example F2) works on it (the chain's rule still holds for the records it rests on).
- [supervised: the answer format's descriptions] properties.findings.items.properties.about: the ids of the records it rests on: evidence tables, simulations, checks, rulings or readings (for example E2, C3, T7)
- [supervised: the answer format's descriptions] properties.whys.items.properties.about: the records whose result this is about: ids of evidence tables, simulations, checks or verdicts in the ledger (for example E2, C3), or the word brief
- [supervised: the answer format's descriptions] properties.whys.items.properties.revises.anyOf: the id of an earlier why that this one replaces with a better guess (for example Y1)
- [supervised: the answer format's descriptions] properties.hypotheses.items.properties.from_why: the id of the why this hypothesis comes from (one you chose to verify), for example Y2
- [supervised: the answer format's descriptions] properties.experiment.anyOf.properties.measurements.items.properties.name: a name of its own: lower-case letters, digits and _, for example <column>_mean
- [supervised: the answer format's descriptions] properties.experiment.anyOf.properties.measurements.items.properties.of: a column a simulation records over time, or arithmetic over columns of one record, for example <column> or <column_a> / <column_b>
- [supervised: the answer format's descriptions] properties.experiment.anyOf.properties.decision_rules.items.properties.decision_rule: a comparison the harness will check, e.g.
- [supervised: the answer format's descriptions] properties.experiment.anyOf.properties.decision_rules.items.properties.competes_with: the id of another live guess (for example Y3): not the hypothesis's own, nor one linked to it by revises
- [supervised: the answer format's descriptions] properties.objections.items.properties.to: the id of the supervisor's ruling, for example V2
- [supervised: the answer format's descriptions] properties.decisions.items.properties.id: the finding, for example F2
- [supervised: the answer format's descriptions] properties.report.anyOf.properties.claims.items.properties.evidence.items: a ledger id, e.g.
- [hypotheses: the instructions] Each names the records it is about (about: ids of evidence tables, simulations, checks or verdicts, for example E2, C3; a reading a tool returned, by its id, for example T7; for what you read in a run's series or trace, that run's id, for example r001; the word brief only when nothing has been measured yet), says the result in one sentence (result), your guess of why (guess), what in the system, not directly visible in the measures, would make it so (unseen), and how it could matter for the goal if it is true (matters).
- [hypotheses: the instructions] When results have come in since a why was stated, look at it again before you build on it: rethink names the why by its own id (id: Y1, Y2, ...; not the K number of a rethink), the new results you looked at it with (in_light_of: for example E2, C3; a reading a tool returned, by its id, for example T7; or a run id, for example r010, for that run's simulation and what the tools returned about it), what it is now (now: verify if it is still open and worth verifying, set_aside if it is not worth following now, refuted if the results speak against it, supported if they speak for it) and because of what in them.
- [hypotheses: the instructions] It may hold several simulations, for example a control and variations of one setting, so that one simulation can be compared with another.
- [hypotheses: the instructions] Each has a name (lower-case letters, digits and _, for example <column>_mean), of (a column a simulation records over time, or arithmetic over columns of one record: the columns are those the tools series and probe name in the brief), stat (mean, min, max, std, first, last, p05, p50, p95, slope, rate, time_above, time_below, first_time_above, first_time_below), a window (t_from, t_to in seconds of the simulation; null: the measured seconds) and level (the number time_above and the like compare with; null otherwise).
- [hypotheses: the instructions] The harness checks it itself from the measured values, so write decision_rule exactly in this form: numbers; measure@label, the value of an output in the simulation with that label (a measurement of your own that this experiment defines is named the same way, for example <column>_mean@label); + - * / and parentheses; abs(), min(), max(); exactly one of < <= > >= == in each comparison; comparisons joined by AND and OR, with parentheses to group them.
- [hypotheses: the instructions] - claims: the statements your answer rests on, each with evidence: the ids of the ledger records that support it (for example E3, C5; a reading a tool returned, for example T7; a run by its id, for example r010).
- [hypotheses: the instructions] If one part of your answer cannot be used (for example a verdict on a hypothesis that has not been tested, or a decision rule the harness cannot read), the harness leaves that part out, accepts the rest, and says in a note which part it refused and why; read the note and repair that part.
- [hypotheses: the instructions] - findings: each new one, once: about (the ids of the records it rests on: evidence tables, simulations, checks, verdicts or readings, for example E2, C3, T7) text (one sentence: what is unexplained, with its numbers) and name (at most 5 words, to show it by).
- [hypotheses: the instructions] - A guess of why whose about names a finding (for example F2) works on it.
- [hypotheses: the answer format's descriptions] properties.findings.items.properties.about: the ids of the records it rests on: evidence tables, simulations, checks, verdicts or readings (for example E2, C3, T7)
- [hypotheses: the answer format's descriptions] properties.rethink.items.properties.id: the earlier why's own id, for example Y1 (never a K number: those are the numbers of rethinks)
- [hypotheses: the answer format's descriptions] properties.rethink.items.properties.in_light_of: the results you look at it again with: ids of evidence tables, checks or verdicts that came in after it (for example E2, C3)
- [hypotheses: the answer format's descriptions] properties.whys.items.properties.about: the records whose result this is about: ids of evidence tables, simulations, checks or verdicts in the ledger (for example E2, C3), or the word brief
- [hypotheses: the answer format's descriptions] properties.whys.items.properties.revises.anyOf: the id of an earlier why that this one replaces with a better guess (for example Y1)
- [hypotheses: the answer format's descriptions] properties.hypotheses.items.properties.from_why: the id of the why this hypothesis comes from (one you chose to verify), for example Y2
- [hypotheses: the answer format's descriptions] properties.experiment.anyOf.properties.measurements.items.properties.name: a name of its own: lower-case letters, digits and _, for example <column>_mean
- [hypotheses: the answer format's descriptions] properties.experiment.anyOf.properties.measurements.items.properties.of: a column a simulation records over time, or arithmetic over columns of one record, for example <column> or <column_a> / <column_b>
- [hypotheses: the answer format's descriptions] properties.experiment.anyOf.properties.decision_rules.items.properties.decision_rule: a comparison the harness will check, e.g.
- [hypotheses: the answer format's descriptions] properties.decisions.items.properties.id: the finding, for example F2
- [hypotheses: the answer format's descriptions] properties.report.anyOf.properties.claims.items.properties.evidence.items: a ledger id, e.g.
- [plain: the instructions] It may hold several simulations, for example a control and variations of one setting, so that one simulation can be compared with another.
- [plain: the instructions] Each has a name (lower-case letters, digits and _, for example <column>_mean), of (a column a simulation records over time, or arithmetic over columns of one record: the columns are those the tools series and probe name in the brief), stat (mean, min, max, std, first, last, p05, p50, p95, slope, rate, time_above, time_below, first_time_above, first_time_below), a window (t_from, t_to in seconds of the simulation; null: the measured seconds) and level (the number time_above and the like compare with; null otherwise).
- [plain: the instructions] - claims: the statements your answer rests on, each with evidence: the ids of the ledger records that support it (for example E3; a reading a tool returned, for example T7; a run by its id, for example r010).
- [plain: the instructions] If one part of your answer cannot be used (for example an experiment that repeats a design you already ran), the harness leaves that part out, accepts the rest, and says in a note which part it refused and why; read the note and repair that part.
- [plain: the instructions] - findings: each new one, once: about (the ids of the records it rests on: evidence tables, simulations or readings, for example E2, T7) text (one sentence: what is unexplained, with its numbers) and name (at most 5 words, to show it by).
- [plain: the answer format's descriptions] properties.findings.items.properties.about: the ids of the records it rests on: evidence tables, simulations or readings (for example E2, T7)
- [plain: the answer format's descriptions] properties.experiment.anyOf.properties.measurements.items.properties.name: a name of its own: lower-case letters, digits and _, for example <column>_mean
- [plain: the answer format's descriptions] properties.experiment.anyOf.properties.measurements.items.properties.of: a column a simulation records over time, or arithmetic over columns of one record, for example <column> or <column_a> / <column_b>
- [plain: the answer format's descriptions] properties.decisions.items.properties.id: the finding, for example F2
- [plain: the answer format's descriptions] properties.report.anyOf.properties.claims.items.properties.evidence.items: a ledger id, e.g.

**Words of preference or expectation**: 35 found, 0 marked.

- [supervised: the instructions] The purpose is the task's: to explain what decides the measure it names, and to say which settings give its best value.  <- best
- [supervised: the instructions] report: null until you can answer the task; then the final report, which ends the session: goal (the goal your answer is best for; if the brief's goal is open, the one you chose and why), recommendation (a value for every knob of the brief), limit (what limits the result at your recommendation, and the ledger ids that show it; if you did not find it, say so), explanation (why, in a few sentences), claims (the statements your answer rests on, each with text and evidence: the ids of the checks, rulings, evidence tables and readings that support it, for example C2, V1, E3, T7).  <- best
- [supervised: the instructions] The kinds: codel: one queue, it drops packets that have waited longer than a target time; fifo: one queue, first in, first out, it drops a packet that arrives when it is full; fqcodel: a queue for each flow, served in turn, each dropping as codel does; pfifofast: three queues by a packet's priority, the higher served first; pie: one queue, it drops arriving packets at random, more often the longer packets wait; red: one queue, it drops arriving packets at random, more often the fuller it is; scheduler: a queue for each flow that passes it, each with an equal part of the link.  <- often
- [supervised: the answer format's descriptions] properties.whys.items.properties.revises.anyOf: the id of an earlier why that this one replaces with a better guess (for example Y1)  <- better
- [supervised: the answer format's descriptions] properties.report.anyOf.properties.limit: what limits the result at the recommendation, that is, why it is not better: the cause and the ledger ids that show it; if you did not find it, say so and what you would test next  <- better
- [supervised: the answer format's descriptions] properties.report.anyOf.properties.explanation: why this setting is best, building on limit and no_difference  <- best
- [hypotheses: the instructions] The purpose of the work is the task's: to explain what decides the measure it names, and to say which settings give its best value.  <- best
- [hypotheses: the instructions] A session that names a best setting and cannot say why it is best, or what stops the result from being better, has not done the work.  <- best, better
- [hypotheses: the instructions] Your guesses are not fixed once made: every new result is a reason to look at them again, to drop one the results speak against, to replace one with a better guess, and to make new ones.  <- better
- [hypotheses: the instructions] Make more than one guess for a result that matters: the first explanation that comes to mind is often not the one that holds.  <- often
- [hypotheses: the instructions] To replace a why with a better guess, state a new why and name the old one in revises (otherwise revises is null); the old one then counts as revised.  <- better
- [hypotheses: the instructions] - goal: the goal your answer is best for.  <- best
- [hypotheses: the instructions] - recommendation: the settings you recommend, as knob: value: a value for every knob of the brief, each within its range (a knob you leave as it was is stated with the value it has; a setting the brief fixes cannot be recommended).  <- recommended
- [hypotheses: the instructions] - limit: what limits the result at your recommendation, that is, why it is not better: the cause, and the ledger ids that show it.  <- better
- [hypotheses: the instructions] - explanation: why this setting is best, building on limit and no_difference.  <- best
- [hypotheses: the instructions] State that as a hypothesis and test it, with the settings you may change and with the tools: the detailed record of a simulation often shows what one number hides, and what the brief says about the system is there to be reasoned from.  <- often
- [hypotheses: the instructions] If no setting you can change makes a meaningful difference to the goal, do not pick the one that is ahead by a hair and present it as the best.  <- best
- [hypotheses: the instructions] Prefer experiments that distinguish between explanations.  <- prefer
- [hypotheses: the instructions] The kinds: codel: one queue, it drops packets that have waited longer than a target time; fifo: one queue, first in, first out, it drops a packet that arrives when it is full; fqcodel: a queue for each flow, served in turn, each dropping as codel does; pfifofast: three queues by a packet's priority, the higher served first; pie: one queue, it drops arriving packets at random, more often the longer packets wait; red: one queue, it drops arriving packets at random, more often the fuller it is; scheduler: a queue for each flow that passes it, each with an equal part of the link.  <- often
- [hypotheses: the answer format's descriptions] properties.whys.items.properties.revises.anyOf: the id of an earlier why that this one replaces with a better guess (for example Y1)  <- better
- [hypotheses: the answer format's descriptions] properties.report.anyOf.properties.limit: what limits the result at the recommendation, that is, why it is not better: the cause and the ledger ids that show it; if you did not find it, say so and what you would test next  <- better
- [hypotheses: the answer format's descriptions] properties.report.anyOf.properties.explanation: why this setting is best, building on limit and no_difference  <- best
- [plain: the instructions] The purpose of the work is the task's: to explain what decides the measure it names, and to say which settings give its best value.  <- best
- [plain: the instructions] A session that names a best setting and cannot say why it is best, or what stops the result from being better, has not done the work.  <- best, better
- [plain: the instructions] Your guesses are not fixed once made: every new result is a reason to look at them again, to drop one the results speak against, to replace one with a better guess, and to make new ones.  <- better
- [plain: the instructions] - goal: the goal your answer is best for.  <- best
- [plain: the instructions] - recommendation: the settings you recommend, as knob: value: a value for every knob of the brief, each within its range (a knob you leave as it was is stated with the value it has; a setting the brief fixes cannot be recommended).  <- recommended
- [plain: the instructions] - limit: what limits the result at your recommendation, that is, why it is not better: the cause, and the ledger ids that show it.  <- better
- [plain: the instructions] - explanation: why this setting is best, building on limit and no_difference.  <- best
- [plain: the instructions] Explore that, with the settings you may change and with the tools: the detailed record of a simulation often shows what one number hides, and what the brief says about the system is there to be reasoned from.  <- often
- [plain: the instructions] If no setting you can change makes a meaningful difference to the goal, do not pick the one that is ahead by a hair and present it as the best.  <- best
- [plain: the instructions] Prefer experiments that distinguish between explanations.  <- prefer
- [plain: the instructions] The kinds: codel: one queue, it drops packets that have waited longer than a target time; fifo: one queue, first in, first out, it drops a packet that arrives when it is full; fqcodel: a queue for each flow, served in turn, each dropping as codel does; pfifofast: three queues by a packet's priority, the higher served first; pie: one queue, it drops arriving packets at random, more often the longer packets wait; red: one queue, it drops arriving packets at random, more often the fuller it is; scheduler: a queue for each flow that passes it, each with an equal part of the link.  <- often
- [plain: the answer format's descriptions] properties.report.anyOf.properties.limit: what limits the result at the recommendation, that is, why it is not better: the cause and the ledger ids that show it; if you did not find it, say so and what you would test next  <- better
- [plain: the answer format's descriptions] properties.report.anyOf.properties.explanation: why this setting is best, building on limit and no_difference  <- best

**Lists of choices and their order**: 4 found, 1 marked.

- [supervised: the instructions] the kinds of queue, in the order the sentence names them: codel, fifo, fqcodel, pfifofast, pie, red, scheduler
- [hypotheses: the instructions] the kinds of queue, in the order the sentence names them: codel, fifo, fqcodel, pfifofast, pie, red, scheduler
- [plain: the instructions] the kinds of queue, in the order the sentence names them: codel, fifo, fqcodel, pfifofast, pie, red, scheduler
- **MARKED** [brief after_fix] the choices of tcp.type, as the brief lists them: TcpCubic, TcpNewReno, TcpLinuxReno, TcpBbr, TcpVegas, TcpBic (default TcpCubic)

**How long each kind of queue is described**: 3 found, 0 marked.

- [supervised: the instructions] words for each kind: codel 13, fifo 16, fqcodel 13, pfifofast 10, pie 14, red 14, scheduler 16
- [hypotheses: the instructions] words for each kind: codel 13, fifo 16, fqcodel 13, pfifofast 10, pie 14, red 14, scheduler 16
- [plain: the instructions] words for each kind: codel 13, fifo 16, fqcodel 13, pfifofast 10, pie 14, red 14, scheduler 16

**Placeholders left unfilled**: 0 found, 0 marked.


## Brief three-hosts-2: the texts as built for a new session

| Text | Characters |
|---|---|
| supervised: the instructions | 9,978 |
| supervised: the answer format's descriptions | 5,145 |
| hypotheses: the instructions | 20,832 |
| hypotheses: the answer format's descriptions | 8,329 |
| plain: the instructions | 11,931 |
| plain: the answer format's descriptions | 3,969 |
| the supervisor: its instructions | 1,606 |
| the brief: its task | 247 |
| the brief: its description | 909 |
| the brief: the meaning of its settings | 233 |

**Examples**: 47 found, 0 marked.

- [supervised: the instructions] Each has about (the ids of the records it starts from, for example E0, S2, C1, V1, a reading T7, an objection of the supervisor G4; the word brief only when nothing is measured yet), result (that result in one sentence, with its numbers), guess (what in the system would make it so), revises (the id of an earlier guess this one replaces or states more exactly; or null), and competes_with (the id of an earlier guess whose result this one explains by another cause, or null; it may cite that guess's records).
- [supervised: the instructions] Each has name (lower-case, for example <column>_max), of (a column a simulation records over time, or arithmetic over columns of one record: the columns the tools series and probe name in the brief), stat (one of the statistics the format lists), t_from and t_to (seconds; null: the measured seconds) and level (the number time_above and the like compare with; null otherwise).
- [supervised: the instructions] objections: if the records show that a ruling of the supervisor is wrong, object once: to (the ruling's id, for example V2) and because (the numbers it overlooked).
- [supervised: the instructions] report: null until you can answer the task; then the final report, which ends the session: goal (the goal your answer is best for; if the brief's goal is open, the one you chose and why), recommendation (a value for every knob of the brief), limit (what limits the result at your recommendation, and the ledger ids that show it; if you did not find it, say so), explanation (why, in a few sentences), claims (the statements your answer rests on, each with text and evidence: the ids of the checks, rulings, evidence tables and readings that support it, for example C2, V1, E3, T7).
- [supervised: the instructions] - findings: each new one, once: about (the ids of the records it rests on: evidence tables, simulations, checks, rulings or readings, for example E2, C3, T7) text (one sentence: what is unexplained, with its numbers) and name (at most 5 words, to show it by).
- [supervised: the instructions] - A guess of why whose about names a finding (for example F2) works on it (the chain's rule still holds for the records it rests on).
- [supervised: the answer format's descriptions] properties.findings.items.properties.about: the ids of the records it rests on: evidence tables, simulations, checks, rulings or readings (for example E2, C3, T7)
- [supervised: the answer format's descriptions] properties.whys.items.properties.about: the records whose result this is about: ids of evidence tables, simulations, checks or verdicts in the ledger (for example E2, C3), or the word brief
- [supervised: the answer format's descriptions] properties.whys.items.properties.revises.anyOf: the id of an earlier why that this one replaces with a better guess (for example Y1)
- [supervised: the answer format's descriptions] properties.hypotheses.items.properties.from_why: the id of the why this hypothesis comes from (one you chose to verify), for example Y2
- [supervised: the answer format's descriptions] properties.experiment.anyOf.properties.measurements.items.properties.name: a name of its own: lower-case letters, digits and _, for example <column>_mean
- [supervised: the answer format's descriptions] properties.experiment.anyOf.properties.measurements.items.properties.of: a column a simulation records over time, or arithmetic over columns of one record, for example <column> or <column_a> / <column_b>
- [supervised: the answer format's descriptions] properties.experiment.anyOf.properties.decision_rules.items.properties.decision_rule: a comparison the harness will check, e.g.
- [supervised: the answer format's descriptions] properties.experiment.anyOf.properties.decision_rules.items.properties.competes_with: the id of another live guess (for example Y3): not the hypothesis's own, nor one linked to it by revises
- [supervised: the answer format's descriptions] properties.objections.items.properties.to: the id of the supervisor's ruling, for example V2
- [supervised: the answer format's descriptions] properties.decisions.items.properties.id: the finding, for example F2
- [supervised: the answer format's descriptions] properties.report.anyOf.properties.claims.items.properties.evidence.items: a ledger id, e.g.
- [hypotheses: the instructions] Each names the records it is about (about: ids of evidence tables, simulations, checks or verdicts, for example E2, C3; a reading a tool returned, by its id, for example T7; for what you read in a run's series or trace, that run's id, for example r001; the word brief only when nothing has been measured yet), says the result in one sentence (result), your guess of why (guess), what in the system, not directly visible in the measures, would make it so (unseen), and how it could matter for the goal if it is true (matters).
- [hypotheses: the instructions] When results have come in since a why was stated, look at it again before you build on it: rethink names the why by its own id (id: Y1, Y2, ...; not the K number of a rethink), the new results you looked at it with (in_light_of: for example E2, C3; a reading a tool returned, by its id, for example T7; or a run id, for example r010, for that run's simulation and what the tools returned about it), what it is now (now: verify if it is still open and worth verifying, set_aside if it is not worth following now, refuted if the results speak against it, supported if they speak for it) and because of what in them.
- [hypotheses: the instructions] It may hold several simulations, for example a control and variations of one setting, so that one simulation can be compared with another.
- [hypotheses: the instructions] Each has a name (lower-case letters, digits and _, for example <column>_mean), of (a column a simulation records over time, or arithmetic over columns of one record: the columns are those the tools series and probe name in the brief), stat (mean, min, max, std, first, last, p05, p50, p95, slope, rate, time_above, time_below, first_time_above, first_time_below), a window (t_from, t_to in seconds of the simulation; null: the measured seconds) and level (the number time_above and the like compare with; null otherwise).
- [hypotheses: the instructions] The harness checks it itself from the measured values, so write decision_rule exactly in this form: numbers; measure@label, the value of an output in the simulation with that label (a measurement of your own that this experiment defines is named the same way, for example <column>_mean@label); + - * / and parentheses; abs(), min(), max(); exactly one of < <= > >= == in each comparison; comparisons joined by AND and OR, with parentheses to group them.
- [hypotheses: the instructions] - claims: the statements your answer rests on, each with evidence: the ids of the ledger records that support it (for example E3, C5; a reading a tool returned, for example T7; a run by its id, for example r010).
- [hypotheses: the instructions] If one part of your answer cannot be used (for example a verdict on a hypothesis that has not been tested, or a decision rule the harness cannot read), the harness leaves that part out, accepts the rest, and says in a note which part it refused and why; read the note and repair that part.
- [hypotheses: the instructions] - findings: each new one, once: about (the ids of the records it rests on: evidence tables, simulations, checks, verdicts or readings, for example E2, C3, T7) text (one sentence: what is unexplained, with its numbers) and name (at most 5 words, to show it by).
- [hypotheses: the instructions] - A guess of why whose about names a finding (for example F2) works on it.
- [hypotheses: the answer format's descriptions] properties.findings.items.properties.about: the ids of the records it rests on: evidence tables, simulations, checks, verdicts or readings (for example E2, C3, T7)
- [hypotheses: the answer format's descriptions] properties.rethink.items.properties.id: the earlier why's own id, for example Y1 (never a K number: those are the numbers of rethinks)
- [hypotheses: the answer format's descriptions] properties.rethink.items.properties.in_light_of: the results you look at it again with: ids of evidence tables, checks or verdicts that came in after it (for example E2, C3)
- [hypotheses: the answer format's descriptions] properties.whys.items.properties.about: the records whose result this is about: ids of evidence tables, simulations, checks or verdicts in the ledger (for example E2, C3), or the word brief
- [hypotheses: the answer format's descriptions] properties.whys.items.properties.revises.anyOf: the id of an earlier why that this one replaces with a better guess (for example Y1)
- [hypotheses: the answer format's descriptions] properties.hypotheses.items.properties.from_why: the id of the why this hypothesis comes from (one you chose to verify), for example Y2
- [hypotheses: the answer format's descriptions] properties.experiment.anyOf.properties.measurements.items.properties.name: a name of its own: lower-case letters, digits and _, for example <column>_mean
- [hypotheses: the answer format's descriptions] properties.experiment.anyOf.properties.measurements.items.properties.of: a column a simulation records over time, or arithmetic over columns of one record, for example <column> or <column_a> / <column_b>
- [hypotheses: the answer format's descriptions] properties.experiment.anyOf.properties.decision_rules.items.properties.decision_rule: a comparison the harness will check, e.g.
- [hypotheses: the answer format's descriptions] properties.decisions.items.properties.id: the finding, for example F2
- [hypotheses: the answer format's descriptions] properties.report.anyOf.properties.claims.items.properties.evidence.items: a ledger id, e.g.
- [plain: the instructions] It may hold several simulations, for example a control and variations of one setting, so that one simulation can be compared with another.
- [plain: the instructions] Each has a name (lower-case letters, digits and _, for example <column>_mean), of (a column a simulation records over time, or arithmetic over columns of one record: the columns are those the tools series and probe name in the brief), stat (mean, min, max, std, first, last, p05, p50, p95, slope, rate, time_above, time_below, first_time_above, first_time_below), a window (t_from, t_to in seconds of the simulation; null: the measured seconds) and level (the number time_above and the like compare with; null otherwise).
- [plain: the instructions] - claims: the statements your answer rests on, each with evidence: the ids of the ledger records that support it (for example E3; a reading a tool returned, for example T7; a run by its id, for example r010).
- [plain: the instructions] If one part of your answer cannot be used (for example an experiment that repeats a design you already ran), the harness leaves that part out, accepts the rest, and says in a note which part it refused and why; read the note and repair that part.
- [plain: the instructions] - findings: each new one, once: about (the ids of the records it rests on: evidence tables, simulations or readings, for example E2, T7) text (one sentence: what is unexplained, with its numbers) and name (at most 5 words, to show it by).
- [plain: the answer format's descriptions] properties.findings.items.properties.about: the ids of the records it rests on: evidence tables, simulations or readings (for example E2, T7)
- [plain: the answer format's descriptions] properties.experiment.anyOf.properties.measurements.items.properties.name: a name of its own: lower-case letters, digits and _, for example <column>_mean
- [plain: the answer format's descriptions] properties.experiment.anyOf.properties.measurements.items.properties.of: a column a simulation records over time, or arithmetic over columns of one record, for example <column> or <column_a> / <column_b>
- [plain: the answer format's descriptions] properties.decisions.items.properties.id: the finding, for example F2
- [plain: the answer format's descriptions] properties.report.anyOf.properties.claims.items.properties.evidence.items: a ledger id, e.g.

**Words of preference or expectation**: 32 found, 0 marked.

- [supervised: the instructions] The purpose is the task's: to explain what decides the measure it names, and to say which settings give its best value.  <- best
- [supervised: the instructions] report: null until you can answer the task; then the final report, which ends the session: goal (the goal your answer is best for; if the brief's goal is open, the one you chose and why), recommendation (a value for every knob of the brief), limit (what limits the result at your recommendation, and the ledger ids that show it; if you did not find it, say so), explanation (why, in a few sentences), claims (the statements your answer rests on, each with text and evidence: the ids of the checks, rulings, evidence tables and readings that support it, for example C2, V1, E3, T7).  <- best
- [supervised: the answer format's descriptions] properties.whys.items.properties.revises.anyOf: the id of an earlier why that this one replaces with a better guess (for example Y1)  <- better
- [supervised: the answer format's descriptions] properties.report.anyOf.properties.limit: what limits the result at the recommendation, that is, why it is not better: the cause and the ledger ids that show it; if you did not find it, say so and what you would test next  <- better
- [supervised: the answer format's descriptions] properties.report.anyOf.properties.explanation: why this setting is best, building on limit and no_difference  <- best
- [hypotheses: the instructions] The purpose of the work is the task's: to explain what decides the measure it names, and to say which settings give its best value.  <- best
- [hypotheses: the instructions] A session that names a best setting and cannot say why it is best, or what stops the result from being better, has not done the work.  <- best, better
- [hypotheses: the instructions] Your guesses are not fixed once made: every new result is a reason to look at them again, to drop one the results speak against, to replace one with a better guess, and to make new ones.  <- better
- [hypotheses: the instructions] Make more than one guess for a result that matters: the first explanation that comes to mind is often not the one that holds.  <- often
- [hypotheses: the instructions] To replace a why with a better guess, state a new why and name the old one in revises (otherwise revises is null); the old one then counts as revised.  <- better
- [hypotheses: the instructions] - goal: the goal your answer is best for.  <- best
- [hypotheses: the instructions] - recommendation: the settings you recommend, as knob: value: a value for every knob of the brief, each within its range (a knob you leave as it was is stated with the value it has; a setting the brief fixes cannot be recommended).  <- recommended
- [hypotheses: the instructions] - limit: what limits the result at your recommendation, that is, why it is not better: the cause, and the ledger ids that show it.  <- better
- [hypotheses: the instructions] - explanation: why this setting is best, building on limit and no_difference.  <- best
- [hypotheses: the instructions] State that as a hypothesis and test it, with the settings you may change and with the tools: the detailed record of a simulation often shows what one number hides, and what the brief says about the system is there to be reasoned from.  <- often
- [hypotheses: the instructions] If no setting you can change makes a meaningful difference to the goal, do not pick the one that is ahead by a hair and present it as the best.  <- best
- [hypotheses: the instructions] Prefer experiments that distinguish between explanations.  <- prefer
- [hypotheses: the answer format's descriptions] properties.whys.items.properties.revises.anyOf: the id of an earlier why that this one replaces with a better guess (for example Y1)  <- better
- [hypotheses: the answer format's descriptions] properties.report.anyOf.properties.limit: what limits the result at the recommendation, that is, why it is not better: the cause and the ledger ids that show it; if you did not find it, say so and what you would test next  <- better
- [hypotheses: the answer format's descriptions] properties.report.anyOf.properties.explanation: why this setting is best, building on limit and no_difference  <- best
- [plain: the instructions] The purpose of the work is the task's: to explain what decides the measure it names, and to say which settings give its best value.  <- best
- [plain: the instructions] A session that names a best setting and cannot say why it is best, or what stops the result from being better, has not done the work.  <- best, better
- [plain: the instructions] Your guesses are not fixed once made: every new result is a reason to look at them again, to drop one the results speak against, to replace one with a better guess, and to make new ones.  <- better
- [plain: the instructions] - goal: the goal your answer is best for.  <- best
- [plain: the instructions] - recommendation: the settings you recommend, as knob: value: a value for every knob of the brief, each within its range (a knob you leave as it was is stated with the value it has; a setting the brief fixes cannot be recommended).  <- recommended
- [plain: the instructions] - limit: what limits the result at your recommendation, that is, why it is not better: the cause, and the ledger ids that show it.  <- better
- [plain: the instructions] - explanation: why this setting is best, building on limit and no_difference.  <- best
- [plain: the instructions] Explore that, with the settings you may change and with the tools: the detailed record of a simulation often shows what one number hides, and what the brief says about the system is there to be reasoned from.  <- often
- [plain: the instructions] If no setting you can change makes a meaningful difference to the goal, do not pick the one that is ahead by a hair and present it as the best.  <- best
- [plain: the instructions] Prefer experiments that distinguish between explanations.  <- prefer
- [plain: the answer format's descriptions] properties.report.anyOf.properties.limit: what limits the result at the recommendation, that is, why it is not better: the cause and the ledger ids that show it; if you did not find it, say so and what you would test next  <- better
- [plain: the answer format's descriptions] properties.report.anyOf.properties.explanation: why this setting is best, building on limit and no_difference  <- best

**Lists of choices and their order**: 1 found, 0 marked.

- [brief three-hosts-2] the choices of fa.type, as the brief lists them: TcpBbr, TcpCubic, TcpNewReno, TcpVegas (default TcpCubic)

**How long each kind of queue is described**: 0 found, 0 marked.


**Placeholders left unfilled**: 0 found, 0 marked.


## Brief three-hosts-link-2: the texts as built for a new session

| Text | Characters |
|---|---|
| supervised: the instructions | 13,334 |
| supervised: the answer format's descriptions | 5,478 |
| hypotheses: the instructions | 24,188 |
| hypotheses: the answer format's descriptions | 8,662 |
| plain: the instructions | 15,260 |
| plain: the answer format's descriptions | 4,302 |
| the supervisor: its instructions | 1,606 |
| the brief: its task | 337 |
| the brief: its description | 893 |
| the brief: the meaning of its settings | 111 |

**Examples**: 47 found, 0 marked.

- [supervised: the instructions] Each has about (the ids of the records it starts from, for example E0, S2, C1, V1, a reading T7, an objection of the supervisor G4; the word brief only when nothing is measured yet), result (that result in one sentence, with its numbers), guess (what in the system would make it so), revises (the id of an earlier guess this one replaces or states more exactly; or null), and competes_with (the id of an earlier guess whose result this one explains by another cause, or null; it may cite that guess's records).
- [supervised: the instructions] Each has name (lower-case, for example <column>_max), of (a column a simulation records over time, or arithmetic over columns of one record: the columns the tools series and probe name in the brief), stat (one of the statistics the format lists), t_from and t_to (seconds; null: the measured seconds) and level (the number time_above and the like compare with; null otherwise).
- [supervised: the instructions] objections: if the records show that a ruling of the supervisor is wrong, object once: to (the ruling's id, for example V2) and because (the numbers it overlooked).
- [supervised: the instructions] report: null until you can answer the task; then the final report, which ends the session: goal (the goal your answer is best for; if the brief's goal is open, the one you chose and why), recommendation (a value for every knob of the brief), limit (what limits the result at your recommendation, and the ledger ids that show it; if you did not find it, say so), explanation (why, in a few sentences), claims (the statements your answer rests on, each with text and evidence: the ids of the checks, rulings, evidence tables and readings that support it, for example C2, V1, E3, T7).
- [supervised: the instructions] - findings: each new one, once: about (the ids of the records it rests on: evidence tables, simulations, checks, rulings or readings, for example E2, C3, T7) text (one sentence: what is unexplained, with its numbers) and name (at most 5 words, to show it by).
- [supervised: the instructions] - A guess of why whose about names a finding (for example F2) works on it (the chain's rule still holds for the records it rests on).
- [supervised: the answer format's descriptions] properties.findings.items.properties.about: the ids of the records it rests on: evidence tables, simulations, checks, rulings or readings (for example E2, C3, T7)
- [supervised: the answer format's descriptions] properties.whys.items.properties.about: the records whose result this is about: ids of evidence tables, simulations, checks or verdicts in the ledger (for example E2, C3), or the word brief
- [supervised: the answer format's descriptions] properties.whys.items.properties.revises.anyOf: the id of an earlier why that this one replaces with a better guess (for example Y1)
- [supervised: the answer format's descriptions] properties.hypotheses.items.properties.from_why: the id of the why this hypothesis comes from (one you chose to verify), for example Y2
- [supervised: the answer format's descriptions] properties.experiment.anyOf.properties.measurements.items.properties.name: a name of its own: lower-case letters, digits and _, for example <column>_mean
- [supervised: the answer format's descriptions] properties.experiment.anyOf.properties.measurements.items.properties.of: a column a simulation records over time, or arithmetic over columns of one record, for example <column> or <column_a> / <column_b>
- [supervised: the answer format's descriptions] properties.experiment.anyOf.properties.decision_rules.items.properties.decision_rule: a comparison the harness will check, e.g.
- [supervised: the answer format's descriptions] properties.experiment.anyOf.properties.decision_rules.items.properties.competes_with: the id of another live guess (for example Y3): not the hypothesis's own, nor one linked to it by revises
- [supervised: the answer format's descriptions] properties.objections.items.properties.to: the id of the supervisor's ruling, for example V2
- [supervised: the answer format's descriptions] properties.decisions.items.properties.id: the finding, for example F2
- [supervised: the answer format's descriptions] properties.report.anyOf.properties.claims.items.properties.evidence.items: a ledger id, e.g.
- [hypotheses: the instructions] Each names the records it is about (about: ids of evidence tables, simulations, checks or verdicts, for example E2, C3; a reading a tool returned, by its id, for example T7; for what you read in a run's series or trace, that run's id, for example r001; the word brief only when nothing has been measured yet), says the result in one sentence (result), your guess of why (guess), what in the system, not directly visible in the measures, would make it so (unseen), and how it could matter for the goal if it is true (matters).
- [hypotheses: the instructions] When results have come in since a why was stated, look at it again before you build on it: rethink names the why by its own id (id: Y1, Y2, ...; not the K number of a rethink), the new results you looked at it with (in_light_of: for example E2, C3; a reading a tool returned, by its id, for example T7; or a run id, for example r010, for that run's simulation and what the tools returned about it), what it is now (now: verify if it is still open and worth verifying, set_aside if it is not worth following now, refuted if the results speak against it, supported if they speak for it) and because of what in them.
- [hypotheses: the instructions] It may hold several simulations, for example a control and variations of one setting, so that one simulation can be compared with another.
- [hypotheses: the instructions] Each has a name (lower-case letters, digits and _, for example <column>_mean), of (a column a simulation records over time, or arithmetic over columns of one record: the columns are those the tools series and probe name in the brief), stat (mean, min, max, std, first, last, p05, p50, p95, slope, rate, time_above, time_below, first_time_above, first_time_below), a window (t_from, t_to in seconds of the simulation; null: the measured seconds) and level (the number time_above and the like compare with; null otherwise).
- [hypotheses: the instructions] The harness checks it itself from the measured values, so write decision_rule exactly in this form: numbers; measure@label, the value of an output in the simulation with that label (a measurement of your own that this experiment defines is named the same way, for example <column>_mean@label); + - * / and parentheses; abs(), min(), max(); exactly one of < <= > >= == in each comparison; comparisons joined by AND and OR, with parentheses to group them.
- [hypotheses: the instructions] - claims: the statements your answer rests on, each with evidence: the ids of the ledger records that support it (for example E3, C5; a reading a tool returned, for example T7; a run by its id, for example r010).
- [hypotheses: the instructions] If one part of your answer cannot be used (for example a verdict on a hypothesis that has not been tested, or a decision rule the harness cannot read), the harness leaves that part out, accepts the rest, and says in a note which part it refused and why; read the note and repair that part.
- [hypotheses: the instructions] - findings: each new one, once: about (the ids of the records it rests on: evidence tables, simulations, checks, verdicts or readings, for example E2, C3, T7) text (one sentence: what is unexplained, with its numbers) and name (at most 5 words, to show it by).
- [hypotheses: the instructions] - A guess of why whose about names a finding (for example F2) works on it.
- [hypotheses: the answer format's descriptions] properties.findings.items.properties.about: the ids of the records it rests on: evidence tables, simulations, checks, verdicts or readings (for example E2, C3, T7)
- [hypotheses: the answer format's descriptions] properties.rethink.items.properties.id: the earlier why's own id, for example Y1 (never a K number: those are the numbers of rethinks)
- [hypotheses: the answer format's descriptions] properties.rethink.items.properties.in_light_of: the results you look at it again with: ids of evidence tables, checks or verdicts that came in after it (for example E2, C3)
- [hypotheses: the answer format's descriptions] properties.whys.items.properties.about: the records whose result this is about: ids of evidence tables, simulations, checks or verdicts in the ledger (for example E2, C3), or the word brief
- [hypotheses: the answer format's descriptions] properties.whys.items.properties.revises.anyOf: the id of an earlier why that this one replaces with a better guess (for example Y1)
- [hypotheses: the answer format's descriptions] properties.hypotheses.items.properties.from_why: the id of the why this hypothesis comes from (one you chose to verify), for example Y2
- [hypotheses: the answer format's descriptions] properties.experiment.anyOf.properties.measurements.items.properties.name: a name of its own: lower-case letters, digits and _, for example <column>_mean
- [hypotheses: the answer format's descriptions] properties.experiment.anyOf.properties.measurements.items.properties.of: a column a simulation records over time, or arithmetic over columns of one record, for example <column> or <column_a> / <column_b>
- [hypotheses: the answer format's descriptions] properties.experiment.anyOf.properties.decision_rules.items.properties.decision_rule: a comparison the harness will check, e.g.
- [hypotheses: the answer format's descriptions] properties.decisions.items.properties.id: the finding, for example F2
- [hypotheses: the answer format's descriptions] properties.report.anyOf.properties.claims.items.properties.evidence.items: a ledger id, e.g.
- [plain: the instructions] It may hold several simulations, for example a control and variations of one setting, so that one simulation can be compared with another.
- [plain: the instructions] Each has a name (lower-case letters, digits and _, for example <column>_mean), of (a column a simulation records over time, or arithmetic over columns of one record: the columns are those the tools series and probe name in the brief), stat (mean, min, max, std, first, last, p05, p50, p95, slope, rate, time_above, time_below, first_time_above, first_time_below), a window (t_from, t_to in seconds of the simulation; null: the measured seconds) and level (the number time_above and the like compare with; null otherwise).
- [plain: the instructions] - claims: the statements your answer rests on, each with evidence: the ids of the ledger records that support it (for example E3; a reading a tool returned, for example T7; a run by its id, for example r010).
- [plain: the instructions] If one part of your answer cannot be used (for example an experiment that repeats a design you already ran), the harness leaves that part out, accepts the rest, and says in a note which part it refused and why; read the note and repair that part.
- [plain: the instructions] - findings: each new one, once: about (the ids of the records it rests on: evidence tables, simulations or readings, for example E2, T7) text (one sentence: what is unexplained, with its numbers) and name (at most 5 words, to show it by).
- [plain: the answer format's descriptions] properties.findings.items.properties.about: the ids of the records it rests on: evidence tables, simulations or readings (for example E2, T7)
- [plain: the answer format's descriptions] properties.experiment.anyOf.properties.measurements.items.properties.name: a name of its own: lower-case letters, digits and _, for example <column>_mean
- [plain: the answer format's descriptions] properties.experiment.anyOf.properties.measurements.items.properties.of: a column a simulation records over time, or arithmetic over columns of one record, for example <column> or <column_a> / <column_b>
- [plain: the answer format's descriptions] properties.decisions.items.properties.id: the finding, for example F2
- [plain: the answer format's descriptions] properties.report.anyOf.properties.claims.items.properties.evidence.items: a ledger id, e.g.

**Words of preference or expectation**: 35 found, 0 marked.

- [supervised: the instructions] The purpose is the task's: to explain what decides the measure it names, and to say which settings give its best value.  <- best
- [supervised: the instructions] report: null until you can answer the task; then the final report, which ends the session: goal (the goal your answer is best for; if the brief's goal is open, the one you chose and why), recommendation (a value for every knob of the brief), limit (what limits the result at your recommendation, and the ledger ids that show it; if you did not find it, say so), explanation (why, in a few sentences), claims (the statements your answer rests on, each with text and evidence: the ids of the checks, rulings, evidence tables and readings that support it, for example C2, V1, E3, T7).  <- best
- [supervised: the instructions] The kinds: codel: one queue, it drops packets that have waited longer than a target time; fifo: one queue, first in, first out, it drops a packet that arrives when it is full; fqcodel: a queue for each flow, served in turn, each dropping as codel does; pfifofast: three queues by a packet's priority, the higher served first; pie: one queue, it drops arriving packets at random, more often the longer packets wait; red: one queue, it drops arriving packets at random, more often the fuller it is; scheduler: a queue for each flow that passes it, each with an equal part of the link.  <- often
- [supervised: the answer format's descriptions] properties.whys.items.properties.revises.anyOf: the id of an earlier why that this one replaces with a better guess (for example Y1)  <- better
- [supervised: the answer format's descriptions] properties.report.anyOf.properties.limit: what limits the result at the recommendation, that is, why it is not better: the cause and the ledger ids that show it; if you did not find it, say so and what you would test next  <- better
- [supervised: the answer format's descriptions] properties.report.anyOf.properties.explanation: why this setting is best, building on limit and no_difference  <- best
- [hypotheses: the instructions] The purpose of the work is the task's: to explain what decides the measure it names, and to say which settings give its best value.  <- best
- [hypotheses: the instructions] A session that names a best setting and cannot say why it is best, or what stops the result from being better, has not done the work.  <- best, better
- [hypotheses: the instructions] Your guesses are not fixed once made: every new result is a reason to look at them again, to drop one the results speak against, to replace one with a better guess, and to make new ones.  <- better
- [hypotheses: the instructions] Make more than one guess for a result that matters: the first explanation that comes to mind is often not the one that holds.  <- often
- [hypotheses: the instructions] To replace a why with a better guess, state a new why and name the old one in revises (otherwise revises is null); the old one then counts as revised.  <- better
- [hypotheses: the instructions] - goal: the goal your answer is best for.  <- best
- [hypotheses: the instructions] - recommendation: the settings you recommend, as knob: value: a value for every knob of the brief, each within its range (a knob you leave as it was is stated with the value it has; a setting the brief fixes cannot be recommended).  <- recommended
- [hypotheses: the instructions] - limit: what limits the result at your recommendation, that is, why it is not better: the cause, and the ledger ids that show it.  <- better
- [hypotheses: the instructions] - explanation: why this setting is best, building on limit and no_difference.  <- best
- [hypotheses: the instructions] State that as a hypothesis and test it, with the settings you may change and with the tools: the detailed record of a simulation often shows what one number hides, and what the brief says about the system is there to be reasoned from.  <- often
- [hypotheses: the instructions] If no setting you can change makes a meaningful difference to the goal, do not pick the one that is ahead by a hair and present it as the best.  <- best
- [hypotheses: the instructions] Prefer experiments that distinguish between explanations.  <- prefer
- [hypotheses: the instructions] The kinds: codel: one queue, it drops packets that have waited longer than a target time; fifo: one queue, first in, first out, it drops a packet that arrives when it is full; fqcodel: a queue for each flow, served in turn, each dropping as codel does; pfifofast: three queues by a packet's priority, the higher served first; pie: one queue, it drops arriving packets at random, more often the longer packets wait; red: one queue, it drops arriving packets at random, more often the fuller it is; scheduler: a queue for each flow that passes it, each with an equal part of the link.  <- often
- [hypotheses: the answer format's descriptions] properties.whys.items.properties.revises.anyOf: the id of an earlier why that this one replaces with a better guess (for example Y1)  <- better
- [hypotheses: the answer format's descriptions] properties.report.anyOf.properties.limit: what limits the result at the recommendation, that is, why it is not better: the cause and the ledger ids that show it; if you did not find it, say so and what you would test next  <- better
- [hypotheses: the answer format's descriptions] properties.report.anyOf.properties.explanation: why this setting is best, building on limit and no_difference  <- best
- [plain: the instructions] The purpose of the work is the task's: to explain what decides the measure it names, and to say which settings give its best value.  <- best
- [plain: the instructions] A session that names a best setting and cannot say why it is best, or what stops the result from being better, has not done the work.  <- best, better
- [plain: the instructions] Your guesses are not fixed once made: every new result is a reason to look at them again, to drop one the results speak against, to replace one with a better guess, and to make new ones.  <- better
- [plain: the instructions] - goal: the goal your answer is best for.  <- best
- [plain: the instructions] - recommendation: the settings you recommend, as knob: value: a value for every knob of the brief, each within its range (a knob you leave as it was is stated with the value it has; a setting the brief fixes cannot be recommended).  <- recommended
- [plain: the instructions] - limit: what limits the result at your recommendation, that is, why it is not better: the cause, and the ledger ids that show it.  <- better
- [plain: the instructions] - explanation: why this setting is best, building on limit and no_difference.  <- best
- [plain: the instructions] Explore that, with the settings you may change and with the tools: the detailed record of a simulation often shows what one number hides, and what the brief says about the system is there to be reasoned from.  <- often
- [plain: the instructions] If no setting you can change makes a meaningful difference to the goal, do not pick the one that is ahead by a hair and present it as the best.  <- best
- [plain: the instructions] Prefer experiments that distinguish between explanations.  <- prefer
- [plain: the instructions] The kinds: codel: one queue, it drops packets that have waited longer than a target time; fifo: one queue, first in, first out, it drops a packet that arrives when it is full; fqcodel: a queue for each flow, served in turn, each dropping as codel does; pfifofast: three queues by a packet's priority, the higher served first; pie: one queue, it drops arriving packets at random, more often the longer packets wait; red: one queue, it drops arriving packets at random, more often the fuller it is; scheduler: a queue for each flow that passes it, each with an equal part of the link.  <- often
- [plain: the answer format's descriptions] properties.report.anyOf.properties.limit: what limits the result at the recommendation, that is, why it is not better: the cause and the ledger ids that show it; if you did not find it, say so and what you would test next  <- better
- [plain: the answer format's descriptions] properties.report.anyOf.properties.explanation: why this setting is best, building on limit and no_difference  <- best

**Lists of choices and their order**: 4 found, 0 marked.

- [supervised: the instructions] the kinds of queue, in the order the sentence names them: codel, fifo, fqcodel, pfifofast, pie, red, scheduler
- [hypotheses: the instructions] the kinds of queue, in the order the sentence names them: codel, fifo, fqcodel, pfifofast, pie, red, scheduler
- [plain: the instructions] the kinds of queue, in the order the sentence names them: codel, fifo, fqcodel, pfifofast, pie, red, scheduler
- [brief three-hosts-link-2] the choices of fa.type, as the brief lists them: TcpBbr, TcpCubic, TcpNewReno, TcpVegas (default TcpCubic)

**How long each kind of queue is described**: 3 found, 0 marked.

- [supervised: the instructions] words for each kind: codel 13, fifo 16, fqcodel 13, pfifofast 10, pie 14, red 14, scheduler 16
- [hypotheses: the instructions] words for each kind: codel 13, fifo 16, fqcodel 13, pfifofast 10, pie 14, red 14, scheduler 16
- [plain: the instructions] words for each kind: codel 13, fifo 16, fqcodel 13, pfifofast 10, pie 14, red 14, scheduler 16

**Placeholders left unfilled**: 0 found, 0 marked.


## Brief three-hosts-moves: the texts as built for a new session

| Text | Characters |
|---|---|
| supervised: the instructions | 13,333 |
| supervised: the answer format's descriptions | 5,478 |
| hypotheses: the instructions | 24,187 |
| hypotheses: the answer format's descriptions | 8,662 |
| plain: the instructions | 15,259 |
| plain: the answer format's descriptions | 4,302 |
| the supervisor: its instructions | 1,606 |
| the brief: its task | 356 |
| the brief: its description | 909 |
| the brief: the meaning of its settings | 233 |

**Examples**: 47 found, 0 marked.

- [supervised: the instructions] Each has about (the ids of the records it starts from, for example E0, S2, C1, V1, a reading T7, an objection of the supervisor G4; the word brief only when nothing is measured yet), result (that result in one sentence, with its numbers), guess (what in the system would make it so), revises (the id of an earlier guess this one replaces or states more exactly; or null), and competes_with (the id of an earlier guess whose result this one explains by another cause, or null; it may cite that guess's records).
- [supervised: the instructions] Each has name (lower-case, for example <column>_max), of (a column a simulation records over time, or arithmetic over columns of one record: the columns the tools series and probe name in the brief), stat (one of the statistics the format lists), t_from and t_to (seconds; null: the measured seconds) and level (the number time_above and the like compare with; null otherwise).
- [supervised: the instructions] objections: if the records show that a ruling of the supervisor is wrong, object once: to (the ruling's id, for example V2) and because (the numbers it overlooked).
- [supervised: the instructions] report: null until you can answer the task; then the final report, which ends the session: goal (the goal your answer is best for; if the brief's goal is open, the one you chose and why), recommendation (a value for every knob of the brief), limit (what limits the result at your recommendation, and the ledger ids that show it; if you did not find it, say so), explanation (why, in a few sentences), claims (the statements your answer rests on, each with text and evidence: the ids of the checks, rulings, evidence tables and readings that support it, for example C2, V1, E3, T7).
- [supervised: the instructions] - findings: each new one, once: about (the ids of the records it rests on: evidence tables, simulations, checks, rulings or readings, for example E2, C3, T7) text (one sentence: what is unexplained, with its numbers) and name (at most 5 words, to show it by).
- [supervised: the instructions] - A guess of why whose about names a finding (for example F2) works on it (the chain's rule still holds for the records it rests on).
- [supervised: the answer format's descriptions] properties.findings.items.properties.about: the ids of the records it rests on: evidence tables, simulations, checks, rulings or readings (for example E2, C3, T7)
- [supervised: the answer format's descriptions] properties.whys.items.properties.about: the records whose result this is about: ids of evidence tables, simulations, checks or verdicts in the ledger (for example E2, C3), or the word brief
- [supervised: the answer format's descriptions] properties.whys.items.properties.revises.anyOf: the id of an earlier why that this one replaces with a better guess (for example Y1)
- [supervised: the answer format's descriptions] properties.hypotheses.items.properties.from_why: the id of the why this hypothesis comes from (one you chose to verify), for example Y2
- [supervised: the answer format's descriptions] properties.experiment.anyOf.properties.measurements.items.properties.name: a name of its own: lower-case letters, digits and _, for example <column>_mean
- [supervised: the answer format's descriptions] properties.experiment.anyOf.properties.measurements.items.properties.of: a column a simulation records over time, or arithmetic over columns of one record, for example <column> or <column_a> / <column_b>
- [supervised: the answer format's descriptions] properties.experiment.anyOf.properties.decision_rules.items.properties.decision_rule: a comparison the harness will check, e.g.
- [supervised: the answer format's descriptions] properties.experiment.anyOf.properties.decision_rules.items.properties.competes_with: the id of another live guess (for example Y3): not the hypothesis's own, nor one linked to it by revises
- [supervised: the answer format's descriptions] properties.objections.items.properties.to: the id of the supervisor's ruling, for example V2
- [supervised: the answer format's descriptions] properties.decisions.items.properties.id: the finding, for example F2
- [supervised: the answer format's descriptions] properties.report.anyOf.properties.claims.items.properties.evidence.items: a ledger id, e.g.
- [hypotheses: the instructions] Each names the records it is about (about: ids of evidence tables, simulations, checks or verdicts, for example E2, C3; a reading a tool returned, by its id, for example T7; for what you read in a run's series or trace, that run's id, for example r001; the word brief only when nothing has been measured yet), says the result in one sentence (result), your guess of why (guess), what in the system, not directly visible in the measures, would make it so (unseen), and how it could matter for the goal if it is true (matters).
- [hypotheses: the instructions] When results have come in since a why was stated, look at it again before you build on it: rethink names the why by its own id (id: Y1, Y2, ...; not the K number of a rethink), the new results you looked at it with (in_light_of: for example E2, C3; a reading a tool returned, by its id, for example T7; or a run id, for example r010, for that run's simulation and what the tools returned about it), what it is now (now: verify if it is still open and worth verifying, set_aside if it is not worth following now, refuted if the results speak against it, supported if they speak for it) and because of what in them.
- [hypotheses: the instructions] It may hold several simulations, for example a control and variations of one setting, so that one simulation can be compared with another.
- [hypotheses: the instructions] Each has a name (lower-case letters, digits and _, for example <column>_mean), of (a column a simulation records over time, or arithmetic over columns of one record: the columns are those the tools series and probe name in the brief), stat (mean, min, max, std, first, last, p05, p50, p95, slope, rate, time_above, time_below, first_time_above, first_time_below), a window (t_from, t_to in seconds of the simulation; null: the measured seconds) and level (the number time_above and the like compare with; null otherwise).
- [hypotheses: the instructions] The harness checks it itself from the measured values, so write decision_rule exactly in this form: numbers; measure@label, the value of an output in the simulation with that label (a measurement of your own that this experiment defines is named the same way, for example <column>_mean@label); + - * / and parentheses; abs(), min(), max(); exactly one of < <= > >= == in each comparison; comparisons joined by AND and OR, with parentheses to group them.
- [hypotheses: the instructions] - claims: the statements your answer rests on, each with evidence: the ids of the ledger records that support it (for example E3, C5; a reading a tool returned, for example T7; a run by its id, for example r010).
- [hypotheses: the instructions] If one part of your answer cannot be used (for example a verdict on a hypothesis that has not been tested, or a decision rule the harness cannot read), the harness leaves that part out, accepts the rest, and says in a note which part it refused and why; read the note and repair that part.
- [hypotheses: the instructions] - findings: each new one, once: about (the ids of the records it rests on: evidence tables, simulations, checks, verdicts or readings, for example E2, C3, T7) text (one sentence: what is unexplained, with its numbers) and name (at most 5 words, to show it by).
- [hypotheses: the instructions] - A guess of why whose about names a finding (for example F2) works on it.
- [hypotheses: the answer format's descriptions] properties.findings.items.properties.about: the ids of the records it rests on: evidence tables, simulations, checks, verdicts or readings (for example E2, C3, T7)
- [hypotheses: the answer format's descriptions] properties.rethink.items.properties.id: the earlier why's own id, for example Y1 (never a K number: those are the numbers of rethinks)
- [hypotheses: the answer format's descriptions] properties.rethink.items.properties.in_light_of: the results you look at it again with: ids of evidence tables, checks or verdicts that came in after it (for example E2, C3)
- [hypotheses: the answer format's descriptions] properties.whys.items.properties.about: the records whose result this is about: ids of evidence tables, simulations, checks or verdicts in the ledger (for example E2, C3), or the word brief
- [hypotheses: the answer format's descriptions] properties.whys.items.properties.revises.anyOf: the id of an earlier why that this one replaces with a better guess (for example Y1)
- [hypotheses: the answer format's descriptions] properties.hypotheses.items.properties.from_why: the id of the why this hypothesis comes from (one you chose to verify), for example Y2
- [hypotheses: the answer format's descriptions] properties.experiment.anyOf.properties.measurements.items.properties.name: a name of its own: lower-case letters, digits and _, for example <column>_mean
- [hypotheses: the answer format's descriptions] properties.experiment.anyOf.properties.measurements.items.properties.of: a column a simulation records over time, or arithmetic over columns of one record, for example <column> or <column_a> / <column_b>
- [hypotheses: the answer format's descriptions] properties.experiment.anyOf.properties.decision_rules.items.properties.decision_rule: a comparison the harness will check, e.g.
- [hypotheses: the answer format's descriptions] properties.decisions.items.properties.id: the finding, for example F2
- [hypotheses: the answer format's descriptions] properties.report.anyOf.properties.claims.items.properties.evidence.items: a ledger id, e.g.
- [plain: the instructions] It may hold several simulations, for example a control and variations of one setting, so that one simulation can be compared with another.
- [plain: the instructions] Each has a name (lower-case letters, digits and _, for example <column>_mean), of (a column a simulation records over time, or arithmetic over columns of one record: the columns are those the tools series and probe name in the brief), stat (mean, min, max, std, first, last, p05, p50, p95, slope, rate, time_above, time_below, first_time_above, first_time_below), a window (t_from, t_to in seconds of the simulation; null: the measured seconds) and level (the number time_above and the like compare with; null otherwise).
- [plain: the instructions] - claims: the statements your answer rests on, each with evidence: the ids of the ledger records that support it (for example E3; a reading a tool returned, for example T7; a run by its id, for example r010).
- [plain: the instructions] If one part of your answer cannot be used (for example an experiment that repeats a design you already ran), the harness leaves that part out, accepts the rest, and says in a note which part it refused and why; read the note and repair that part.
- [plain: the instructions] - findings: each new one, once: about (the ids of the records it rests on: evidence tables, simulations or readings, for example E2, T7) text (one sentence: what is unexplained, with its numbers) and name (at most 5 words, to show it by).
- [plain: the answer format's descriptions] properties.findings.items.properties.about: the ids of the records it rests on: evidence tables, simulations or readings (for example E2, T7)
- [plain: the answer format's descriptions] properties.experiment.anyOf.properties.measurements.items.properties.name: a name of its own: lower-case letters, digits and _, for example <column>_mean
- [plain: the answer format's descriptions] properties.experiment.anyOf.properties.measurements.items.properties.of: a column a simulation records over time, or arithmetic over columns of one record, for example <column> or <column_a> / <column_b>
- [plain: the answer format's descriptions] properties.decisions.items.properties.id: the finding, for example F2
- [plain: the answer format's descriptions] properties.report.anyOf.properties.claims.items.properties.evidence.items: a ledger id, e.g.

**Words of preference or expectation**: 35 found, 0 marked.

- [supervised: the instructions] The purpose is the task's: to explain what decides the measure it names, and to say which settings give its best value.  <- best
- [supervised: the instructions] report: null until you can answer the task; then the final report, which ends the session: goal (the goal your answer is best for; if the brief's goal is open, the one you chose and why), recommendation (a value for every knob of the brief), limit (what limits the result at your recommendation, and the ledger ids that show it; if you did not find it, say so), explanation (why, in a few sentences), claims (the statements your answer rests on, each with text and evidence: the ids of the checks, rulings, evidence tables and readings that support it, for example C2, V1, E3, T7).  <- best
- [supervised: the instructions] The kinds: codel: one queue, it drops packets that have waited longer than a target time; fifo: one queue, first in, first out, it drops a packet that arrives when it is full; fqcodel: a queue for each flow, served in turn, each dropping as codel does; pfifofast: three queues by a packet's priority, the higher served first; pie: one queue, it drops arriving packets at random, more often the longer packets wait; red: one queue, it drops arriving packets at random, more often the fuller it is; scheduler: a queue for each flow that passes it, each with an equal part of the link.  <- often
- [supervised: the answer format's descriptions] properties.whys.items.properties.revises.anyOf: the id of an earlier why that this one replaces with a better guess (for example Y1)  <- better
- [supervised: the answer format's descriptions] properties.report.anyOf.properties.limit: what limits the result at the recommendation, that is, why it is not better: the cause and the ledger ids that show it; if you did not find it, say so and what you would test next  <- better
- [supervised: the answer format's descriptions] properties.report.anyOf.properties.explanation: why this setting is best, building on limit and no_difference  <- best
- [hypotheses: the instructions] The purpose of the work is the task's: to explain what decides the measure it names, and to say which settings give its best value.  <- best
- [hypotheses: the instructions] A session that names a best setting and cannot say why it is best, or what stops the result from being better, has not done the work.  <- best, better
- [hypotheses: the instructions] Your guesses are not fixed once made: every new result is a reason to look at them again, to drop one the results speak against, to replace one with a better guess, and to make new ones.  <- better
- [hypotheses: the instructions] Make more than one guess for a result that matters: the first explanation that comes to mind is often not the one that holds.  <- often
- [hypotheses: the instructions] To replace a why with a better guess, state a new why and name the old one in revises (otherwise revises is null); the old one then counts as revised.  <- better
- [hypotheses: the instructions] - goal: the goal your answer is best for.  <- best
- [hypotheses: the instructions] - recommendation: the settings you recommend, as knob: value: a value for every knob of the brief, each within its range (a knob you leave as it was is stated with the value it has; a setting the brief fixes cannot be recommended).  <- recommended
- [hypotheses: the instructions] - limit: what limits the result at your recommendation, that is, why it is not better: the cause, and the ledger ids that show it.  <- better
- [hypotheses: the instructions] - explanation: why this setting is best, building on limit and no_difference.  <- best
- [hypotheses: the instructions] State that as a hypothesis and test it, with the settings you may change and with the tools: the detailed record of a simulation often shows what one number hides, and what the brief says about the system is there to be reasoned from.  <- often
- [hypotheses: the instructions] If no setting you can change makes a meaningful difference to the goal, do not pick the one that is ahead by a hair and present it as the best.  <- best
- [hypotheses: the instructions] Prefer experiments that distinguish between explanations.  <- prefer
- [hypotheses: the instructions] The kinds: codel: one queue, it drops packets that have waited longer than a target time; fifo: one queue, first in, first out, it drops a packet that arrives when it is full; fqcodel: a queue for each flow, served in turn, each dropping as codel does; pfifofast: three queues by a packet's priority, the higher served first; pie: one queue, it drops arriving packets at random, more often the longer packets wait; red: one queue, it drops arriving packets at random, more often the fuller it is; scheduler: a queue for each flow that passes it, each with an equal part of the link.  <- often
- [hypotheses: the answer format's descriptions] properties.whys.items.properties.revises.anyOf: the id of an earlier why that this one replaces with a better guess (for example Y1)  <- better
- [hypotheses: the answer format's descriptions] properties.report.anyOf.properties.limit: what limits the result at the recommendation, that is, why it is not better: the cause and the ledger ids that show it; if you did not find it, say so and what you would test next  <- better
- [hypotheses: the answer format's descriptions] properties.report.anyOf.properties.explanation: why this setting is best, building on limit and no_difference  <- best
- [plain: the instructions] The purpose of the work is the task's: to explain what decides the measure it names, and to say which settings give its best value.  <- best
- [plain: the instructions] A session that names a best setting and cannot say why it is best, or what stops the result from being better, has not done the work.  <- best, better
- [plain: the instructions] Your guesses are not fixed once made: every new result is a reason to look at them again, to drop one the results speak against, to replace one with a better guess, and to make new ones.  <- better
- [plain: the instructions] - goal: the goal your answer is best for.  <- best
- [plain: the instructions] - recommendation: the settings you recommend, as knob: value: a value for every knob of the brief, each within its range (a knob you leave as it was is stated with the value it has; a setting the brief fixes cannot be recommended).  <- recommended
- [plain: the instructions] - limit: what limits the result at your recommendation, that is, why it is not better: the cause, and the ledger ids that show it.  <- better
- [plain: the instructions] - explanation: why this setting is best, building on limit and no_difference.  <- best
- [plain: the instructions] Explore that, with the settings you may change and with the tools: the detailed record of a simulation often shows what one number hides, and what the brief says about the system is there to be reasoned from.  <- often
- [plain: the instructions] If no setting you can change makes a meaningful difference to the goal, do not pick the one that is ahead by a hair and present it as the best.  <- best
- [plain: the instructions] Prefer experiments that distinguish between explanations.  <- prefer
- [plain: the instructions] The kinds: codel: one queue, it drops packets that have waited longer than a target time; fifo: one queue, first in, first out, it drops a packet that arrives when it is full; fqcodel: a queue for each flow, served in turn, each dropping as codel does; pfifofast: three queues by a packet's priority, the higher served first; pie: one queue, it drops arriving packets at random, more often the longer packets wait; red: one queue, it drops arriving packets at random, more often the fuller it is; scheduler: a queue for each flow that passes it, each with an equal part of the link.  <- often
- [plain: the answer format's descriptions] properties.report.anyOf.properties.limit: what limits the result at the recommendation, that is, why it is not better: the cause and the ledger ids that show it; if you did not find it, say so and what you would test next  <- better
- [plain: the answer format's descriptions] properties.report.anyOf.properties.explanation: why this setting is best, building on limit and no_difference  <- best

**Lists of choices and their order**: 4 found, 0 marked.

- [supervised: the instructions] the kinds of queue, in the order the sentence names them: codel, fifo, fqcodel, pfifofast, pie, red, scheduler
- [hypotheses: the instructions] the kinds of queue, in the order the sentence names them: codel, fifo, fqcodel, pfifofast, pie, red, scheduler
- [plain: the instructions] the kinds of queue, in the order the sentence names them: codel, fifo, fqcodel, pfifofast, pie, red, scheduler
- [brief three-hosts-moves] the choices of fa.type, as the brief lists them: TcpBbr, TcpCubic, TcpNewReno, TcpVegas (default TcpCubic)

**How long each kind of queue is described**: 3 found, 0 marked.

- [supervised: the instructions] words for each kind: codel 13, fifo 16, fqcodel 13, pfifofast 10, pie 14, red 14, scheduler 16
- [hypotheses: the instructions] words for each kind: codel 13, fifo 16, fqcodel 13, pfifofast 10, pie 14, red 14, scheduler 16
- [plain: the instructions] words for each kind: codel 13, fifo 16, fqcodel 13, pfifofast 10, pie 14, red 14, scheduler 16

**Placeholders left unfilled**: 0 found, 0 marked.


Marked in all: 1.

# Session s062, as sent (main's texts)

## Session s062 (brief after_fix2): the texts as sent

| Text | Characters |
|---|---|
| supervisor: instructions 1 (20 calls: turn 0 look ...) | 1,530 |
| researcher: instructions 2 (8 calls: turn 1 reply ...) | 12,155 |
| researcher: instructions 3 (2 calls: turn 4 restate ...) | 317 |
| the texts of the turns (30 calls) | 865,520 in all, the longest 85,472 |

**Examples**: 12 found, 2 marked.

- [researcher: instructions 2 (8 calls: turn 1 reply ...)] Each has about (the ids of the records it starts from, for example E0, S2, C1, V1, a reading T7, an objection of the supervisor G4; the word brief only when nothing is measured yet), result (that result in one sentence, with its numbers), guess (what in the system would make it so), revises (the id of an earlier guess this one replaces or states more exactly; or null), and competes_with (the id of an earlier guess whose result this one explains by another cause, or null; it may cite that guess's records).
- [researcher: instructions 2 (8 calls: turn 1 reply ...)] Each has name (lower-case, for example rwnd_max), of (a column a simulation records over time, or arithmetic over columns of one record: the columns the tools series and probe name in the brief), stat (one of the statistics the format lists), t_from and t_to (seconds; null: the measured seconds) and level (the number time_above and the like compare with; null otherwise).
- [researcher: instructions 2 (8 calls: turn 1 reply ...)] objections: if the records show that a ruling of the supervisor is wrong, object once: to (the ruling's id, for example V2) and because (the numbers it overlooked).
- [researcher: instructions 2 (8 calls: turn 1 reply ...)] report: null until you can answer the task; then the final report, which ends the session: goal (the goal your answer is best for; if the brief's goal is open, the one you chose and why), recommendation (a value for every knob of the brief), limit (what limits the result at your recommendation, and the ledger ids that show it; if you did not find it, say so), explanation (why, in a few sentences), claims (the statements your answer rests on, each with text and evidence: the ids of the checks, rulings, evidence tables and readings that support it, for example C2, V1, E3, T7).
- **MARKED** [researcher: instructions 2 (8 calls: turn 1 reply ...)] - do add_link: id, from and to (the two hosts it joins), rate (for example 1Gbps).  <- names: 1Gbps
- **MARKED** [researcher: instructions 2 (8 calls: turn 1 reply ...)] - do add_flow: id, kind (udp or tcp: the socket), from, to, and rate for udp (for example 100Mbps) or type for tcp (for example TcpCubic).  <- names: 100Mbps, TcpCubic, tcp
- [researcher: instructions 2 (8 calls: turn 1 reply ...)] - findings: each new one, once: about (the ids of the records it rests on: evidence tables, simulations, checks, rulings or readings, for example E2, C3, T7) text (one sentence: what is unexplained, with its numbers) and name (at most 5 words, to show it by).
- [researcher: instructions 2 (8 calls: turn 1 reply ...)] - A guess of why whose about names a finding (for example F2) works on it.
- [supervisor, call 1 (turn 0, look): the text of the turn] about (a list): the ids of the records it rests on: evidence tables, simulations, checks, verdicts or readings (for example E2, C3, T7)
- [supervisor, call 1 (turn 0, look): the text of the turn] name (text): at most 5 words, to show it by (for example: TCP gets nothing)
- [researcher, call 2 (turn 1, reply): the text of the turn] "metrics": "metrics(run_id): the output values of a simulation (run ids are in the evidence lines, e.g.
- [supervisor, call 3 (turn 1, review): the text of the turn] nearest_earlier (text): the id of the earlier guess or hypothesis that is nearest to this one in what it claims (for example Y2 or H3), or none

**Words of preference or expectation**: 14 found, 0 marked.

- [researcher: instructions 2 (8 calls: turn 1 reply ...)] Usually empty.  <- usually
- [researcher: instructions 2 (8 calls: turn 1 reply ...)] Usually empty.  <- usually
- [researcher: instructions 2 (8 calls: turn 1 reply ...)] report: null until you can answer the task; then the final report, which ends the session: goal (the goal your answer is best for; if the brief's goal is open, the one you chose and why), recommendation (a value for every knob of the brief), limit (what limits the result at your recommendation, and the ledger ids that show it; if you did not find it, say so), explanation (why, in a few sentences), claims (the statements your answer rests on, each with text and evidence: the ids of the checks, rulings, evidence tables and readings that support it, for example C2, V1, E3, T7).  <- best
- [researcher: instructions 2 (8 calls: turn 1 reply ...)] - "It does not change the recommendation" is not a reason to park a finding: the task asks why the settings you recommend are best, so explaining a measured result is part of the goal.  <- best
- [researcher, call 2 (turn 1, reply): the text of the turn] Explain why they are best.",  <- best
- [researcher, call 2 (turn 1, reply): the text of the turn] A difference inside it is not a finding, and a setting is not better for it.  <- better
- [supervisor, call 12 (turn 3, review): the text of the turn] The guess of why: TcpBic under scheduler can exceed TcpCubic by more than 1% by filling or probing the scheduler class better.  <- better
- [supervisor, call 12 (turn 3, review): the text of the turn] | its guess: TcpBic under scheduler can exceed TcpCubic by more than 1% by filling or probing the scheduler class better.  <- better
- [supervisor, call 14 (turn 3, ruling): the text of the turn] AT THE REVIEW BEFORE THE RUN you answered: Honest pass: r002 gives the base 482007923 bps, but the scheduler TcpBic run has not been measured, and the rule can fail if Bic exceeds 486828002.23 bps.; Consistent pass: The compared runs differ only in tcp.type under the same scheduler and q100, and the competing Y12 explains the same scheduler TCP goodput result by TcpBic filling or probing the scheduler class better.; Correct pass: If H7 is true, Bic does not exceed 1.01 times r002, so the rule holds; if Y12 is true, Bic exceeds that threshold, so the rule fails.  <- better
- [supervisor, call 16 (turn 4, review): the text of the turn] The result it starts from, as the researcher states it: All best scheduler runs are near 482 Mbps, but no alternative queue disc has been tested.  <- best
- [supervisor, call 16 (turn 4, review): the text of the turn] THE GUESS THIS RULE COMPETES WITH [Y14]: the result it explains: All best scheduler runs are near 482 Mbps, but no alternative queue disc has been tested.  <- best
- [researcher, call 22 (turn 5, restate): the text of the turn] guess: FQ-CoDel drops TCP more often and adds delay, so TCP keeps more bytes in flight to maintain the same fair share; the extra retransmissions are lost TCP segments, not a larger class share.  <- often
- [supervisor, call 25 (turn 6, review): the text of the turn] | its guess: FQ-CoDel drops TCP more often and adds delay, so TCP keeps more bytes in flight to maintain the same fair share; the extra retransmissions are lost TCP segments, not a larger class share.  <- often
- [supervisor, call 28 (turn 7, review): the text of the turn] It competes with Y19, whose guess is: FQ-CoDel drops TCP more often and adds delay, so TCP keeps more bytes in flight to maintain the same fair share; the extra retransmissions are lost TCP segments, not a larger class share.  <- often

**Lists of choices and their order**: 2 found, 2 marked.

- **MARKED** [researcher: instructions 2 (8 calls: turn 1 reply ...)] the kinds of queue, in the order the sentence names them: scheduler, fifo, pfifofast, codel, fqcodel, red, pie
- **MARKED** [brief after_fix2] the choices of tcp.type, as the brief lists them: TcpCubic, TcpNewReno, TcpLinuxReno, TcpBbr, TcpVegas, TcpBic (default TcpCubic)

**How long each kind of queue is described**: 1 found, 1 marked.

- **MARKED** [researcher: instructions 2 (8 calls: turn 1 reply ...)] a kind of queue described in a sentence of its own: A scheduler gives each flow that passes it a part of the link; fifo is one queue for all, first in, first out.

**Placeholders left unfilled**: 0 found, 0 marked.


Marked in all: 5.
