# What changed overnight (2026-11-22 night to 2026-11-23 morning), in plain words

## The picture

The loop is a researcher AI that studies a simulated network (ns-3), and, in the arm "supervised", a second AI that checks each of its steps:
whether a guess starts from what was measured, whether a test can tell the guess from a competing explanation before anything is run, and
what the measured result means. Last night the whole harness and the page were audited line by line (plans/2026-11-22-coherence-audit.md:
six root causes, 36 problems), and every problem found was fixed in five stages, checked, and deployed.

## The five stages, one sentence each

1. **Records and crashes**: nothing the AIs write can shift ids, crash the session or be lost (a broken measurement is recorded as broken).
2. **One source per rule**: each kind of researcher is told only what it can do, and every number the instructions state is checked against
   the harness's own constant at the start.
3. **The page**: it shows every experiment of a turn, who did what (the harness's refusals are no longer drawn as the supervisor's), and the
   live view of a running session.
4. **Speed and focus**: one request reviews all new guesses and tests of a reply (s055: 4 guesses and a test in 106 s, where each used to take
   about 50 s); the supervisor's feedback names one problem; a decision rule makes at most 3 comparisons.
5. **Competitors are guesses**: a test names, as its competitor, another guess the researcher wrote; the supervisor reviews and rules with three
   questions (Honest: can it fail? Consistent: does it test the claim and only that? Correct: does it come out differently under the two guesses?);
   a guess that does not fit the result of a fair test is refuted, and nothing more comes from it.

## What the real sessions showed

**s055** (brief after_fix, arm "supervised", 00:46 to 02:09, done by the model in 11 turns, 11 simulations, recommends the FIFO with a queue of 1000):
- The researcher wrote competing guesses on its own (Y4 competes with Y1), and the rulings refuted the guesses that did not fit fair results (Y1 by
  V1, Y2 by V2, eight in all), which its own ledger text then said.
- A test whose competing cause the researcher had not written was held instead of run; in the next turn the researcher wrote that guess, the
  test ran and was supported (H4).
- Eight of its simulations were answered from earlier ones at no cost: tests on simulations already run were decided by measurements the
  researcher defined itself.
- It found four faults no scripted check could find, each replayed by a new check, fixed and deployed at 02:19 (review/harness-2026-11-22/REVIEW.md
  on the branch). One of them cost it the experiment that mattered: in turn 10 it proposed the scheduler (the change that lets TCP through), but
  a restated guess had both revised and competed with the guess it was tested against, and the test was refused. That can no longer happen.

**s056** (the same brief and settings, 02:19 to 04:15, on the build of 02:19; report in its last turn after 14 turns and 12 simulations, recommends
the FIFO with a queue of 1000, where TCP still gets almost nothing):
- The parts of the night worked again: competing guesses in every turn, 12 rulings (two refuted the guess that did not fit), two tests held and
  then given up by the researcher with what it learned, 15 simulations answered from earlier ones at no cost.
- But it lost the scheduler test a second time, in turn 4: the supervisor had never been told that this brief lets the network change, called the
  scheduler "outside the permitted settings", and the researcher believed it. It then spent its budget on differences of one or two packets.
- It found five more faults, each replayed by a check, fixed, checked on all 34 harness checks and deployed at 04:16 (REVIEW.md, parts 5 to 7):
  the supervisor is now told when the network may change and within which limits; a repair may name the simulations of a repair the harness
  refused; the harness's own advice for a rule of more than 3 comparisons no longer contradicts the supervisor (it said "keep one comparison", the
  supervisor then held the test for testing only part of its claim); a change that is written correctly but asks for more than the brief allows
  is told so, instead of being shown an unrelated example; and in the one request that reviews a reply's new guesses, the supervisor had compared
  11 of 23 new guesses with themselves (twice judging a guess "a repeat of itself"). Asked again on the real model with the fix, it did so for 0
  of 6 (6 of 6 before).
- One fault of the page: while a reply continued after the researcher's questions to the tools, the banner said the first reply "could not be
  used". Fixed and deployed with the rest.

**s057** (the same brief and settings, 04:16 to 05:42, on the build of 04:16; report after 10 turns and 12 simulations) found the fix the brief
was made for:
- In turn 4 the researcher guessed that a scheduler giving each flow its own share would let TCP through, wrote the competing guess that UDP's
  overload caps TCP whatever the queue does, and proposed the test; the supervisor approved it in its first round. With the scheduler TCP got
  476 Mbit/s, where every FIFO setting had given it at most 5.8 kbit/s; the ruling supported the guess and refuted its competitor.
- It then measured what matters under the scheduler: Cubic fills TCP's share better than BBR (476 against 190 Mbit/s), a 4-packet queue loses
  TCP packets, and the default queue of 100 is best (482 Mbit/s, a 2.1 ms round trip against 17.2 ms at 1000). Its report recommends exactly that,
  names its limit (the scheduler's share of the link), and says the queue of 100 is the best tested, not proven best.
- The fixes of the night held in it: no new guess was compared with itself (19 read in batches), and the supervisor never called the change of
  the network not allowed.
- It still showed four faults, each replayed by a check, fixed, checked on all harness checks and deployed at 05:42 (REVIEW.md, parts 8 to 11):
  the task the harness writes into the brief said "every other setting is fixed" on a brief whose network may change (both AIs read it); the
  researcher misnumbered its new guesses and lost a test (each request now says which ids they will get); a guess could not name a competitor
  written after it; a refuted guess was not marked as one no test may compete with. And two of the page, both live: while a simulation with a
  network change ran, the page took it for an earlier one with the same settings, and its card read "of 0" seconds.

**s058** (the same brief and settings, 05:43 to 07:12, on the build of 05:42; done by the model after 11 turns and 11 of its 12 simulations), the
first session given the corrected task sentence:
- It proposed the scheduler in its very first turn, beside the larger FIFO queue: the larger queue was refuted (5.8 kbit/s), the scheduler
  supported (482 Mbit/s).
- It then checked, each time against a competing guess, that no TCP type and no queue length does better under the scheduler, that another queue
  discipline (pfifofast) does not help TCP at all, and why the TCP types differ only in delay and retransmissions. 12 rulings (6 supported, 6
  refuted); 16 simulations answered from earlier ones at no cost.
- Its report recommends the scheduler with a queue of 100 and Cubic, and names the limit: the scheduler caps TCP at about half the link,
  because the fixed 2 Gbit/s UDP flow takes the other half.
- Every request named the ids its new guesses and hypotheses would get, and the researcher's numbering held throughout. It showed two
  small faults of wording, fixed, checked and deployed at 07:37 (REVIEW.md, parts 12 and 13): a rule that named a measurement an earlier
  experiment had defined was refused as "not one of the outputs" (it now says where the measurement was defined and what may be named), and a
  guess that cited another guess as a record was told "not in the ledger" (it now says that a guess starts from records, never guesses).

After the night, no session is running: the page is free for a new one.

## How it was checked

- Every harness check (34) on each build and on the build that runs live; new checks for each stage (test_stage1 to test_stage5).
- Every new answer format sent once to the real model server, and each new kind of supervisor call made for real with its own token limit.
- Each fault a real session showed was first made to happen again: by a scripted check, and where it was the model's reading, by asking the
  real model the same request again, as it was and with the fix (the scheduler review of s056, the guesses compared with themselves).
- The page checks (36 of them, each driving the page in a browser): before the night 27 passed on the live page; on the final page (07:20) all 36 pass.
  The nine that failed were each examined: two were real faults of the page and are fixed (the top strip wrapped with the operator's columns;
  colour was used to say who wrote a part, against the rule that a small icon says it), one was a fault in a check of the harness's own, two were
  races in the checks, and the rest still described the page before the operator's own changes and were brought up to date.
- The live system itself: the server, the page, an exported session opened with no server, the agents page and the calls card of a running
  session, each looked at after the deploy.
- Old sessions (s047 to s053) read and draw as before.

## Where to look

- The live page: port 8600, the session list (s055, s056, s057, s058). For s057's key moment, its hypothesis H5 (the scheduler) and its simulation
  S11 (the network drawn with the scheduler).
- The plan and its status: plans/2026-11-22-coherence-audit.md. The deploys (00:31, 00:46, 02:19, 04:16, 05:42, 07:37): HARNESS_SPEC.md 8.3 and 16, HISTORY.md
  (rows of 2026-11-23, lessons D9, D10).
- Every change with its reason and its checks: branch review/harness-2026-11-22, review/harness-2026-11-22/REVIEW.md.
