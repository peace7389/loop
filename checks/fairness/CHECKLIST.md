# The checklist of a fairness audit (v2)

One audit for each session, in `checks/fairness/<session>.md`, begun with `harness/fairness.py SESSION` (the figures and this list) and judged by
reading the session's records and the texts it was sent (`harness/text_audit.py --session SESSION`). Each item is answered yes, no or "cannot
tell", with the records that show it. Operator only: no agent is shown this folder.

- Turn 1: does the answer, or a part of it, already stand in turn 1 (simulated or named)? Turn 1 depends on the texts alone. If it does: which sentence of the instructions, the brief or the answer format could have given it?
- The texts as sent (`text_audit.py --session`): does any of them name a value, an object, a kind or an order that is part of the answer, or describe one choice at greater length than the others?
- The brief: does it leave more than one move open, and do its limits single none out?
- The rule of the chain: was a refused guess an explanation not yet tried that had no other way in (the open way: a competitor of an earlier guess)?
- The box Follows: where it failed or could not be told, was the test sent back with a reason the researcher could act on? Was any guess counted as refuted through a hypothesis that did not follow from it (the code allows none)?
- "Cannot tell": does each such answer of the supervisor state what was missing, and was it counted as the rules say (a test sent back at the review, an inconclusive result at the ruling)?
- The reviews: was a test approved in round 1 that the ruling then found unfair, and could the review have seen it? Was a sound test sent back?
- The rulings: does each follow from the numbers of its checks (none changed by the harness, or the change explained)? Does a ruling rest on a difference inside the tolerance?
- The competing guess: was each test's competitor a real other cause, shown to the supervisor at the ruling, and was a guess refuted only where a fair result did not fit it?
- Parked findings: is each reason a fair one (a difference inside the tolerance, or about no measure the task names)? Did a parked finding hide something the answer rests on?
- What the harness refused: was the researcher refused anything by a rule the texts had not stated, or by a limit the texts state differently from the code?
- The simulations: were enough left for the comparison that decides the answer, and did a limit of the brief stop a test the session needed?
- The answer measured again (`harness/confirm.py`): do the conditions hold in all three simulations, and is the target what the session measured and what the report expects?
- The report: does its explanation rest on tests that were fair, and does it say what limits the result?
