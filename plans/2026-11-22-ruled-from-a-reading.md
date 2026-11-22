# For discussion: a hypothesis that a free reading already answers (arm "supervised") — 2026-11-22

Please help me decide how the harness should close a hypothesis that a free reading has already answered. Context below; the questions are at the end.

## Context
`harness/loop.py` runs a research loop on ns-3 simulations. Both agents are the local model Qwen/Qwen3.8-Flash-Next-FP8: a **researcher** that
proposes guesses, hypotheses and tests, and in the arm "supervised" a **supervisor** asked apart from it. The researcher can also make free
**readings** of simulations already run (a probe, a series, a derived metric such as the highest `tcp_rwnd` on run r001); a reading costs no
simulation. A hypothesis closes in one of two ways today:
- **ruled**: its test ran new simulations, the harness checked the decision rule (held or failed), and the supervisor ruled supported, refuted
  or inconclusive;
- **dropped** by the researcher, with a reason.

Rules that apply here (since 2026-11-22):
- A test must name a simulation whose result is not known yet. A rule that names only results already in the ledger is refused by the harness
  ("it cannot fail and is no test").
- Before any simulation runs, the supervisor reviews each test, in up to 3 rounds. A test sent back is repaired by the researcher in the same
  turn. One reason to send a test back: "already answered by the ledger".
- There is no way to rule on a hypothesis from a reading. Only the researcher can drop it.

## The case (session s052, running now)
- Turn 1: the researcher stated **H1**: "A probe of r001 will show max(tcp_rwnd)=0 and max(tcp_rtt_ms)=0 over the whole run, because the TCP
  sender never received a SYN-ACK." r001 is the baseline, run before turn 1. In the same reply it asked for four readings of r001; none
  computed a value of tcp_rwnd (the probe recorded it, among 12 quantities).
- Turn 2: it made readings **T5** (highest tcp_rwnd on r001: **65,535**) and **T6** (highest tcp_rtt_ms: **1**). H1's prediction was false.
  In the same reply it proposed a test of H1 on r001.
  - The supervisor sent the test back: "already answered by the ledger".
  - The researcher's repair, `tcp_retrans@default == 0`, was refused by the harness: it names only known results.
  - Its third repair broke down: the answer ran to its token limit and could not be read.
  - H1 stayed open.
- Turn 3: the researcher dropped H1: "T5 and T6 show max tcp_rwnd=65535 and max tcp_rtt=1.0 ms ... refuting H1's predicted zeros."
- Result: H1 is recorded as **dropped**, although its own prediction was tested and refuted, with numbers, by readings taken after it was stated.
  It costs a turn of review rounds and shows up in the figures as dropped, not refuted.

## Options
- **A. Ruled from a reading** (my proposal): in the repair step, the researcher may answer "already answered by T5, T6" instead of a new rule.
  The supervisor then rules on the hypothesis from those readings (supported, refuted or inconclusive). The ruling is recorded as "ruled from a
  reading", costs no simulation, and is counted apart from rulings on tests.
  - **Safeguard:** only readings taken *after* the hypothesis was stated count. Then the prediction was made blind, which is what makes it a
    test. A hypothesis written about a reading already seen could not collect a cheap "supported".
- **B. Tests on simulations already run, in every turn** (today only in the free turns after the budget): a rule over known runs is accepted.
  Weaker: the rule can be written after the numbers are seen.
- **C. Leave it**: the researcher drops it. The page would only show "dropped: refuted by its reading T5" from the drop's reason.
- **D. Prevent it**: when a hypothesis is stated, the harness or the supervisor flags one whose prediction is about a simulation already run
  (H1 predicted something about the baseline). The researcher would make a reading instead, or predict about a new simulation.

## Questions
1. Is a hypothesis about a simulation already run a legitimate hypothesis (its outcome was not known when it was stated), or should it be
   prevented when stated (D)?
2. If it stays: close it by a ruling from readings taken after it (A), or by the researcher's drop (C)?
3. Is "only readings taken after the hypothesis was stated" the right safeguard against cheap verdicts? Is anything else needed, such as the
   ruling being only "refuted" or "inconclusive" and never "supported"?
4. How should it count in the figures, so that sessions stay comparable with s050 and s051 (which had no such rulings)?
