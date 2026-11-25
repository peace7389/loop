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
| 2026-11-17 | After the usage limit: the interrupted work completed (the page of 15 November checked as a whole and published; the report's parts "what limits the result" and "made no difference" tested and shown). The page shared with the lab: any account of the server through its own SSH tunnel, one session at a time, the page says who runs it. The task is now written by the harness, after the operator found that `trap`'s task contradicted its aim and settings. Briefs with the seed fixed. Two comparison arms built: the loop without the hypothesis format, and random search. A network as data (the program `net`, a drag-and-drop builder, structure the AI may change), the page on the lab network with a personal link for the professor. The chain of reasoning fixed by the answer format (guesses of why, needs, half of what is left; a guess can be looked at again or replaced); first session on it: s041. An audit of s033 and s041 at the operator's word found three defects in the chain (a test on known results, guesses never taken up, a hypothesis that need not follow from its guess): repaired, the last by a judge (a second model call). The builder redrawn on JointJS, hosts as in the two-host picture, the tools in a palette. |
| 2026-11-17, late | The network builder reviewed against ns-3 at the operator's word ("building section should reflect ns-3 architecture") and brought nearer to it in two stages: a link is a channel and two devices, each with its own rate and transmit queue where wanted; a queue on either sending side, or both; several flows in one queue of a scheduler. Second build of `net` with five predictions met (`checks/net2`). Session s043, the first under the mandatory look-again. |
| 2026-11-18 | The operator could not find a NIC among the builder's tools, thought a single queue for UDP and TCP needed the "Shared queue" tool, and asked whether ns-3 has separate UDP and TCP applications (it has not). The builder now names ns-3's objects: application (OnOff, BulkSend) and socket (UDP, TCP) as two choices, so TCP can send at a constant rate; the Link tool says it brings a NIC at each end. Brief `two-hosts-one-queue` for the supervisor's question: one queue under the scheduler behaves exactly as a plain shared queue (UDP at 2 Gbps leaves TCP 0). |
| 2026-11-18, late | The rest of what ns-3 has for the builder's objects, at the operator's "Do it": an application's times, a device's largest packet and loss, TCP's options, ns-3's queue discs, the ns-3 attribute beside every setting. A review of the loop's objects (the verdict repeats the check, the judge never refused) and the operator's decision to split the AI into a researcher and an independent supervisor. |
| 2026-11-22 | The lean page (the setting, what it needed to find out, the detail), the network as a schema of its ns-3 objects, Agent transcripts for everyone, measurement marks on the board; every reading and the researcher's own observations kept in its ledger. Sessions s048 to s051 (s051 stopped: 8 turns without a simulation). |
| 2026-11-22, evening | Deployed (the operator: "A, B and D, nothing else"): readings as evidence and two free turns after the budget (part 1); findings, unexplained results tracked until they are closed (A); the supervisor's review of a test in rounds, with the researcher's own rival and a repair in the same turn (B); a guess is never refused for good: a warning, or one restatement, then accepted (D). Under review, not deployed: new measurement statistics and taps (part 2), the short answer format (part 3), follow-through on findings (C, shelved). |
| 2026-11-22, night | The page, during s052 (the operator's requests one by one): the steps of a turn as a track in the session's arm (reply, guesses, test review in rounds, simulations, checks, rulings, next turn), read from now.json once the harness writes it; a finding's bar keeps to the lines between turns, shows a treasure chest and the finding's name only, and opens a short hover box and a new detail (its course turn by turn); derived metrics (the researcher's own measurements) marked ƒx and shown under the turn they were made in when they measure the baseline; the network's schema and its "Made of" list light together on hover; "who produced it" in the order they act. Built, checks running, not deployed: the harness writes now.json and a finding gets a name (review branch, eighth part). For discussion: ruling a hypothesis from a reading (plans/2026-11-22-ruled-from-a-reading.md). |
| 2026-11-22, 19:20 | Session s052 (the operator's, arm "supervised", brief again_again: the network of s050) stopped in turn 3 on a harness fault of B: a repaired test carried a network change that could not be applied, and the repair path did not catch it (recorded as "stopped from outside"). 4 simulations, H2 inconclusive, H1 dropped (its own reading refuted it), H3 and H5 approved but never run. Fixed on the review branch (ninth part: a repair is checked as the normal path checks an experiment; a harness fault is recorded as one), not deployed yet. |
| 2026-11-22, 19:46 | Deployed: s052's fault fixed (a repair never stops the session), a harness fault recorded as one, now.json (the page's track lights the step the harness is at), a finding's name, exported sessions open again. The page: the parts of a network grouped by host in the new-session form; a hypothesis's detail as its course turn by turn. |
| 2026-11-22, night | The coherence audit (five line-by-line audits of the harness and the page): six root causes, 36 problems; the operator approved all five stages, built on the review branch one after another, each checked on its own build and on the build to deploy (plans/2026-11-22-coherence-audit.md). |
| 2026-11-23, 00:31 | Deployed: the five stages (records and crashes; one source per rule; the page; the rest of the fixes from s052 and s053, with one batched first review of a reply's guesses and tests; competitors are guesses, reviewed and ruled by three questions). Session s054 (the operator's, arm "supervised", the new brief after_fix: the network of s052 with TCP goodput as the goal) had started at 00:28 on the harness before them, and was stopped at 00:30 so that they could go in. At 00:46 a fix a real call of the model found (the ids of the batched review); session s055 started on the new build at 00:46. |
| 2026-11-23, 02:09 | Session s055 (arm "supervised", after_fix, on the new build) ended, done by the model after 11 turns and 11 simulations: batched reviews, competing guesses written by the researcher, guesses refuted by rulings, a held test run the next turn. It found four faults, fixed and deployed at 02:19; one of them had refused its scheduler test in turn 10, and it recommended the FIFO. Session s056 started at 02:19. |
| 2026-11-23, 04:16 | Session s056 (after_fix, arm "supervised", competitors, on the build of 02:19) ended at 04:15: all simulations used, report given in the last turn, 14 turns, 12 simulations, 75 model calls (39 of the supervisor, 36 of the researcher); it recommends the FIFO at queue 1000 with Cubic (TCP about 5.8 kbit/s). Its scheduler test (turn 4) was lost: the supervisor called the change outside the permitted settings, and the repair that followed could not name the refused repair's simulations. Deployed: its faults, each replayed by a scripted check and the batched review's on the real model: the supervisor is told when the network may change; a repair may name a refused repair's simulations; a rule over 3 comparisons keeps every part of its claim; a limit of the network is no format error; the batched review marks the reply's new guesses. Session s057 started on it. |
| 2026-11-23, 05:42 | Session s057 (after_fix, arm "supervised", competitors, on the build of 04:16) ended at 05:42: all simulations used, report given in the last turn, 10 turns, 12 simulations, 53 model calls (30 of the supervisor, 23 of the researcher). In turn 4 the researcher proposed the scheduler with a competing guess, the supervisor approved the test in its first round, and TCP went from at most 5.8 kbit/s to 476 Mbit/s (supported; the competitor refuted); it recommends the scheduler with a queue of 100 and Cubic (482 Mbit/s). Session s058 started on the new build. Deployed: its faults, each replayed by a check: the task sentence of a brief whose network may change says so; each reply request says the ids its new parts will get; a guess may compete with a later guess of its answer; a refuted guess is marked as no competitor; the page's running cards. |
| 2026-11-23, 07:37 | Session s058 (after_fix, arm "supervised", competitors, on the build of 05:42, the first with the corrected task sentence) ended at 07:12, done by the model after 11 turns and 11 of its 12 simulations: the scheduler in its first turn (TCP 482 Mbit/s, supported; the larger FIFO queue refuted), then no TCP type, queue length or other queue discipline (pfifofast) does better; it recommends the scheduler with a queue of 100 and Cubic. Deployed: two refusals that now say what was wrong (a measurement of an earlier experiment; a guess cited as a record). |
| 2026-11-23, 10:00 | Tagged `v1` (pushed): commit 69508e2, the build of 07:37 that s058 and s059 ran on, so that the operator can name it. The master copy of HARNESS_SPEC.md in ~/ADRS was 52 lines behind the repo's copy (the night's deploy notes were written into the repo's copy), and `snapshot.sh` would have copied it back over them: brought up to date. |
| 2026-11-23, 10:25 | Session s059 (brief three-hosts: four hosts, a scheduler on a 100 Mbit/s link, the largest TCP goodput while UDP loses at most 10 %; arm "supervised", competitors, budget 12 of the brief's 20, on v1) ended at 10:24, done by the model after 8 turns and 11 simulations, 12 rulings (9 supported, 3 refuted). Its first guess, that the scheduler is not work-conserving, was refuted in turn 1 (TCP 17.6 Mbit/s at a part of 0.05); the condition's edge found by tests (TCP's part 0.179 keeps UDP's loss at 0.0986, 0.180 gives 0.1002); neither BBR nor a longer queue raises TCP there. Report: TCP's part 0.185 with queue 1000 and Cubic, 26.0 Mbit/s, UDP's loss 0.0999; the report itself says the longer queue only holds UDP's packets past the measured window (at queue 100 the same part loses 0.1067). Turn 3 lost its experiment to a rule naming an earlier experiment's simulation, fixed in turn 4 as the refusal said. Deployed at 10:25 (the server restarted, its request log saved in ~/control_logs): a session's "of N simulations" in the list and the top strip is the budget it was granted (s059 showed "9 of 20" while the researcher had 12; s002 and s003 corrected as well). |
| 2026-11-23, 11:35 | Deployed, the page (all 36 page checks pass on it): the detail a hypothesis box opens shows the night's rules: the two guesses a test was to tell apart, each with its standing (refuted by a ruling, or replaced), the ruling's fairness and its three questions asked again with the result in hand, and which guess the result fits and which it refutes (a guess's standing follows the harness's own rule, equal on s047, s050, s055 to s058); the supervisor's words are marked as the supervisor's, and the arm that never asks a hypothesis for a why or a prediction no longer reads them as missing. The board shows a turn that ran tests of hypotheses stated earlier (a test held or refused, then run) with that experiment in its column: s059's turn 4 had looked empty although it ran X5 for H6 to H8. |
| 2026-11-23, 15:04 | Session s060 (the operator's, brief asdg, 11:28) stopped at its first call with a model server error: asdg leaves the AI no setting and keeps the network fixed, and its answer format then held two empty lists of choices, which the model server cannot take (reproduced: asdg 500, three-hosts and after_fix 200). Deployed: a brief that leaves the AI nothing to change is refused, when it is saved and when a session starts, with the reason (asdg is the only one on disk); the answer format has no empty list of choices (a brief whose only change is the structure is accepted and works); the new-session page says it under the form. All harness checks and the builder's page checks pass (test_step_c and ev_build updated: their test briefs leave the AI one setting). |
| 2026-11-23, 16:06 | Deployed at 15:35 (the operator's choice, to run their session on it): a link a change adds has the brief's cap and delay (`structure.new_link`), one simulation for one network however its changes are written, and the brief three-hosts-link (FIFO at r, a new link at most 100 Mbit/s with 1 ms; 16 simulations, at most 4 in one experiment). Session s061 on it (arm "supervised", competitors, budget 16) ended at 16:06, done by the model after 6 turns: it added a link lac between a and c and reports that with BBR (fa 96.4 Mbit/s, 17.9 as given; fb loses nothing), 3 rulings supported, 2 refuted. Its record counts 12 simulations, of which 4 are different ones (the row below). |
| 2026-11-24, 12:12 | An audit of the simulation and of its picture on the page (the operator: "How is simulation and its representation on the viewer done currently? How sound and accurate is it"): the two programs and the harness's run path read line by line, recorded simulations run again directly, and the page's picture and numbers compared with the files of s024, s058, s059 and s061. Sound: a recorded simulation run again gives the same files byte for byte; the measures add up on the wire (s061 baseline: 79.76 Mbit/s of UDP payload and 17.86 of TCP are 100.0 Mbit/s with headers); seeds 1 to 5 and 5, 20, 60 measured seconds move the baseline by under 0.3 %; the picture of every one of the 227 recorded simulations of network sessions rebuilds its `network.txt` exactly. Faults found and repaired the same day, each with a check: (1) since the deploy of 11-23 15:35 a simulation on a changed network was never recognised as one that had run (the planned one keyed by the network its changes build, the earlier one by the list as written): s061 ran three simulations four times; `harness_checks/test_reuse_structure.py`. (2) `measure` took the sample at 2.0 s, the last step of the second that is not measured: in s059 a mean of fa's rate came out 0.79 % above the goodput of the same simulation, in a test whose limit was 1 %; now the samples after 2.0 s (`rate` keeps its starting count). (3) On the page: "How ns-3 was started" showed the two-host program with the settings as options for a network session (now `net` with the run's network.txt, linked); a side of a link without a described queue was said to have "only the device's own queue" (ns-3's plain queue of 100 packets stands there, and its drops are measured); a plain queue on a link's second host was given the other side's measure; a link the AI added said "fixed by the operator"; the card of an added link showed no measure. Harness checks run on the changed files, all passing: test_structure, test_network, test_repair_structure, test_stage1, test_format_fix, test_notebook_p3, test_step_c, test_varied, test_measure and the new test_reuse_structure (the others were not run); page checks page, net, replay_n1, live, words, usable, shared, lean, build pass on the tree that went live. Left open for the operator (spec 15, item 13): the loss over a short window (lesson B4), one seed against a limit, and a list of things the page still says wrongly or leaves out. |
| 2026-11-24, 13:14 | Deployed, the page (the operator: "I want users to be able to view clearly the simulation setting, simulation records, simulation outcomes, and more connection between hypothesis, simulation setting, simulation outcome, hypothesis accepted or refuted"). Before, a click on a hypothesis gave its course as a list of steps with its simulations folded away, and a simulation's pane named neither the network change it ran with nor a hypothesis. Now (`viewer/evidence_chain.js`): the pane of a hypothesis shows each of its tests as one block, top to bottom: the simulations as rows, left what was set (the network and the settings, what differs in bold), right what came out (the measures its rule reads); then what the rule required of those numbers; then the result: the harness's check, the ruling or verdict, and what it did to the guesses. The pane of a simulation begins with its setting, the hypotheses whose rule names it (each with its result and the numbers it read here) and its records (the run's files, linked). A simulation is told apart by its network too (the test of s061 H1 said "every setting at its default" of both sides), and an added link's measures have plain names. New check `ev_evidence.py`: on s024, s058, s059 and s061, 130 printed measures equal the runs' metrics.json, the network said equals the run's network.txt, the badges equal the ledger, and stepped back nothing later shows. At 13:21 and 13:26, from the operator's two questions ("Can I check the full setting of simulation on the viewer?", then "where?" with the pane of a test pasted, which had none of it): a fold "The full setting" in a simulation's pane (every value of the network and the run as it ran, beside the brief's; 1,128 values of 74 simulations equal their runs' network.txt), and the block also at the head of the pane a box of the board opens, with that pane's older sections folded under it. The first version had the block only in the card an id of a hypothesis opens, which is not where a reader of the board arrives: I had tried it by its address, not by a click (lesson C7). |
| 2026-11-24, 14:53 | The page, at the operator's word, each live within minutes and each added to `ev_evidence.py`: "The full setting" open by default with a button to fold it, and showing a changed queue (it had counted 1 difference where the simulation had replaced the queue by a scheduler: now the queue's kind and the new parts are rows); names, values and objects in looks of their own ("making value and category name distinct"); the pane of a simulation in four numbered parts, Setting, Outcome, Over time, Records, with the outcome in the same look, each measure under its flow or link and the hypothesis that read it beside it, and without the two older tables that said the same again ("add the outcome of the simulation and remove redundancy"); the description of each object in a box on its band ("show it only as hover over"). On s047, s058, s059 and s061: 1,202 values of the setting equal the runs' network.txt and 930 of the outcome their metrics.json. The texts the two agents are sent (the operator: "find out any defects or defiances from the intentions or correct working ... none of agents be steered into specific directions unfairly by biased prompts"): read as sent in s056 to s061 by three readers apart from each other, the main findings checked against the code; the sheet is `plans/2026-11-24-prompt-audit.md`. In short: each brief's hidden answer is pointed at by a sentence the researcher is given (the one other queue kind that is explained, the one change that is described at length and that the limits leave open, the sentence that names what "is not described"), and in s058, s059 and s061 it was stated in turn 1; the supervisor's requests lean to approving and to a clear ruling, and ask it about a competing guess whose words they do not show; several statements of the instructions are not true of the code. Nothing was changed in the texts (it would end the comparison with v1): the operator decides. Repaired, with `harness_checks/test_locked_replace.py`: a locked object could be taken out and put back under its id with other values (the fixed UDP flow at 1 Mbit/s; no session did), and the supervisor's request on an objection printed its ruling's placeholders unfilled (no objection was ever made). Harness checks on the changed files: test_structure, test_network, test_repair_structure, test_reuse_structure, test_stage1, test_stage4, test_stage5, test_supervised pass. |
| 2026-11-24, 15:02 | Deployed, the board (the operator: "How about add simulations on each turn between hypothesis flow and findings bars? I think simulations results are more directly showing the hypothesis flow ... when users hover over one of simulations, we emphasize relevant hypothesis and findings (if applicable) and vice versa"): a lane of small bars, one for each simulation in the column of its turn, its height the measure the aim is about; a returned result dashed, a stroke above one that does not meet the aim's conditions; pointing at a bar opens its box and lights its hypotheses and findings, pointing at a box or a finding's bar lights its simulations; a click opens the simulation. `ev_evidence.py` part `lane` on s024, s047, s058, s059, s061: one bar for each of 111 simulations in its turn's column, the larger value the higher bar, the lighting exact both ways, nothing later when stepped back. At 15:08, at the operator's word ("remove it and put index like 'S4' and put some color"): the line of words over the lane is gone, and a simulation is a small box with its id, in the colour of the flow the aim's measure belongs to, deeper the larger that measure; then all of one size, that of the longest id ("I want all to be equal size for neatness"). Committed at the operator's word before the full run of the page checks had ended (4194820). |
| 2026-11-24, 19:37 | Deployed, the board, at the operator's word. At 15:44: pointing at a simulation, a box or a finding no longer draws thick black borders round what belongs to it ("not readable"); the rest of the board fades and what belongs keeps its look, with a thin edge in the page's accent. At 19:37: the key shows the depth of a simulation's colour as one strip from pale to deep, with 0 at one end and the largest value of the session so far at the other ("Why dont we show it using gradation instead?"), in place of a pale and a deep sample box. With it, five faults of the same day's work that the full run of the page checks found hours after they went live (the run takes over an hour): (1) the hover boxes of "Scheduler", "UDP queue" and "TCP queue" in the two-host sessions opened empty, because the new boxes of a simulation's objects used the same key letter (`o:`): they now have their own (`g:`); (2) in a window of 900 px the board of the older sessions was 37 px too wide, because the key's new row had a long middle column: the row says "is a simulation, by its id" and the long items of the key may wrap; (3) the letter in the key's icon was 10 px: 12 px; (4) "The full setting" listed the part of a flow at a queue the simulation had removed, as a setting of the run: left out, as in the run's `network.txt`; (5) a heading set in capitals by a style: as written. Checks: `ev_evidence.py` (the strip's deep end is the colour of the deepest box, its value the largest of the runs' files; no sample boxes), `ev_words.py` (the new kind of box), `ev_lean.py` and `ev_chain.py` brought in line with the taller board; evidence, words, board, lean and polish pass on the deployed files; the full run on them was still going at the time of the commit. |
| 2026-11-25, 13:04 | Deployed, the set-up page (the operator: "I want a researcher and a supervisor setting as default in new session page"): "who rules on the tests" starts with a researcher and a supervisor, in both forms (two hosts, the network builder); one AI is the second choice and, chosen, is marked as changed like every other run choice. "Start a new session from this setup" now keeps who ruled in the session it copies (it had always opened with one AI, also from a supervised session). A session started through `POST /api/session` without an arm is one AI as before. Check: `ev_usable.py arm` (it fails on the page as it was). Also repaired, two checks that the full run of 2026-11-24 20:43 reported: the board's key has a row for the simulations since 15:02 (the check still asked for two rows), and "Now" of the live view passed when run alone (a slip of timing under the full run). |
| 2026-11-25, 13:51 | Session s062, the operator's (12:52 to 13:51, the live harness of main, a researcher and a supervisor, competing guesses): the operator's brief `after_fix2`, at most 12 simulations, 4 in one experiment. Ended "done by the model" after 8 turns and 11 simulations, no reply cut off: 12 hypotheses, 11 ruled on (7 supported, 3 refuted, 1 inconclusive), 35 reviews, 17 notes of the harness. Its report recommends the queue on the sender's side of l1 replaced by a scheduler, queue length 100, TcpCubic. Not read or judged by anyone yet. |
| 2026-11-25 | v2, sessions that are fair to measure, built on its branch (the operator, after s062: "s062 ran on main, which still has the scheduler hint; v2 is only on its branch. Please finish v2"; not deployed until the operator says). Stages 3 to 8 this day: one purpose in the task and in every arm, a parked finding does not hold the report back, statements true of the code; the brief three-hosts-moves with its reference runs (four kinds of move meet the condition: 18 to 96 Mbit/s); the answer measured again with three seeds at five times the time (`confirm.py`: s059's answer does not meet its condition over 25 s); the page's four boxes, "cannot tell" and the confirmation; the fairness figures, the audit's form and checklist, the text audit; checks of wrong input. The text audit found, in v2's own texts, the scheduler still named before the list of the kinds of queue and an example rate; the checks of wrong input found a refusal that suggested a repair; all fixed. On the texts s062 was sent, the same audit marks the two sentences the operator called the scheduler hint, and its figures say the answer was simulated and named in turn 1. Old sessions read word for word as before on the page. The operator's decisions on what was left ("Do as you recommend"): three-hosts-moves as built; a brief after_fix-2 (alphabetical TCP types, its TCP flow locked); a review that cannot be read is asked for once more and then counts as "cannot tell" in every box (its test had run unreviewed, with no answer to Follows). Spec 8.10, 10.10, 10.11, 12.1, 15 item 14. |
| 2026-11-25, 16:30 | v2 deployed at the operator's word ("do do do") and tagged `v2`: main moved forward to the branch (the files that went live are the files every check ran on), the control server restarted, no session running. Checked on the live page and harness, reading only: the four briefs of the run plan build in every arm and the text audit marks nothing in them; the set-up page starts with a researcher and a supervisor; on s058, s061 and s062 the page's refuted guesses are the harness's. Before the deploy, at the operator's remark that the long runs were not all necessary, the 90-minute page suite was replaced by the checks of what v2 touches (about 25 minutes) and run afterwards as a follow-up; those checks found that the page worked out "decided by less than the tolerance" by the rule before v2 (now: the harness's own mark from the check's record). From the tag on, the texts the agents are sent and the harness's rules are not changed. Next: one session for each of after_fix-2, three-hosts-2, three-hosts-link-2, three-hosts-moves, each with a fairness audit and its answer measured again. |
| 2026-11-25, 17:56 | Session s063, the operator's, the first on v2 (16:36 to 17:56; a researcher and a supervisor, competing guesses; the operator's brief `after_fix-3`, the same as `after_fix-2`: 12 simulations, 4 in one experiment). Ended "done by the model" after 9 turns and 11 simulations. Its report: the queue on the sender's side of l1 replaced by a scheduler, queue length 100, TcpCubic; measured again apart from the session (`confirm.py`, three seeds, 50 s each): 482.0 Mbit/s in each, as the session measured. What v2's parts did: the box Follows stood in every review of the supervisor (5 passed, 10 failed: it fails a hypothesis that adds a number or a clause its guess does not force); 8 boxes were answered "cannot tell", and the two rulings with one came out inconclusive and refuted nothing; of 10 hypotheses 5 were tested (all approved in round 1) and 5 never ran (held by the supervisor, or their repair could not be read by the harness: a label that did not exist, a measure that is no output); 2 guesses were refused by the rule of the chain. The scheduler is named in the words of turn 1 and simulated in the first experiment (turn 2), without the sentences v2 removed: in this brief only the queue can change. The figures and the audit's form are in `checks/fairness/s063.*`; the checklist is not judged yet. |
| 2026-11-25, 18:46 | v2.1, at the operator's word after reading s063: the supervisor's Honest fails only if every value a rule compares already stands in the records (it had failed every comparison of a new run with an earlier one: H8, and the rulings of H9 and H10), and Follows asks whether someone who held the guess would expect the result in direction and rough size, a stated threshold following if the guess expects the result beyond it (it had failed any hypothesis with a number or from a hedged guess: 10 of 15 reviews, 5 of 10 hypotheses never ran). The 15 reviews of s063 were asked again as they were sent, three times with each wording: Follows passes 13 of 45 as it was and 26 of 45 with v2.1; a test would run in 11 and in 17; H8 in 0 of 3 and 3 of 3; no review comes out worse. The same replay showed that the supervisor does not repeat itself: with nothing changed, the same four boxes all three times in 7 of 15 reviews, most of the difference in Correct. The fairness audit of s063 was judged (`checks/fairness/s063.md`): fair with a reservation (one kind of move in its brief; the two questions as v2 worded them; two rules the texts do not state). Deployed and tagged `v2.1`. Next, by the operator: three-hosts-moves. |
| 2026-11-25, 19:11 | Deployed, from the operator's sheet of the evening and from a crash. Session s064 (the operator's, 18:50, brief `three_hosts_neutralprompts`, a researcher and a supervisor) ended in turn 1, before any simulation of its own, with "harness error: KeyError: 'no_cause'": the supervisor refused a guess for saying that something makes no difference without naming a cause, and the refusal looked that reason up in the list of a session without competing guesses, which does not have it (in the harness since 2026-11-23; no session had met it). Repaired; the check `test_stage5`, section U, plays the case. Follows is asked in two parts: strictly, the hypothesis is about a measure the guess speaks about, in the direction the guess requires; and the number is the researcher's choice, failing only where it lies clearly outside what the guess could give. The review's record keeps the part that failed (`follows_part`). Honest was already as the sheet asks. Put to the real model on the 15 reviews of s063: the new field is answered in every call; on the first pass Follows passes in 10 of 15, and each of its 5 failures names "measure or direction". |

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
- **The fixed chain of reasoning on `trap-2`** (session s041, 2026-11-17, the first real session on it: 6 turns, 11 of
  20 simulations, ended by the model with 9 left). Turn 1: three guesses of why TCP stays near 300 Mbps (one of them
  the 1 MB buffers), one hypothesis, an experiment of 3 simulations where the sessions before spent 12. Every
  experiment after it lists, for each hypothesis, the simulations made for it, and they differ in one setting. It found
  the same limit as s033 (1 MiB / 20 ms = 419.4 Mbps; BBR reaches 418.9) and recommends BBR, with the ratio and the
  queue length as making no difference. So on this brief the chain did not change WHAT was found; it changed how the
  budget was spent (11 simulations, none without a hypothesis; s033: 15) and how each result can be traced to a
  reason. One session each. In turn 2 three guesses were refused because they cited a time series by its run id; the
  harness now takes a run id for that run's simulation.
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
- **The mandatory look-again on `trap-2`** (session s043, 2026-11-17: 6 turns, 17 of 20 simulations, 6 hypotheses,
  6 readings by the judge, none refused, a report). After every tested hypothesis the model gave a review of the guess
  it came from before going on: 9 reviews (turn 2: two guesses refuted, one kept; turns 4 to 6: six supported or
  kept), where s042 had skipped the review of turn 3. The recommendation and the limit are those of s033, s041 and
  s042 (BBR, 418.9 Mbps, held by TCP's 1 MB buffer over a 20 ms round trip): the brief has one thing to find. In
  turn 2 three hypotheses were refused because `follows_from` named a run id (r001); the harness now takes a run id
  there as it does in `about`.
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

**A11. A hypothesis and its simulations were tied loosely; the tie is now a part of the answer.**
*Evidence:* the operator, 2026-11-17: "after the AI formed a hypothesis, it clearly chooses what it needs to know and
subsequently forms simulations. I worry that the connection is loose or just superficially implemented." Counted on
eight sessions: of 101 decision rules 70 compared simulations that differ in one setting, 14 in several, 17 judged one
simulation against a number; 28 of 228 test simulations were named by no rule (s035 X1: a sweep of 11, its rules name 3).
*What we changed:* the chain is fixed by the answer format: a result, guesses of why it came out so (`whys`), which of
them are worth verifying, a hypothesis from such a guess (`from_why`), what must be known to decide it (`needs`: the
one setting that differs, the measure, the simulations), and only those simulations. The harness refuses a simulation
no hypothesis needs and a comparison in which more than one setting differs. The instructions open with the role:
not many settings tried for a slight lead, but looking into the system and asking why.
*Status:* partly: s041 kept to it without trouble (section 3); whether it finds more than before is not shown.

**A12. "Simulation limit reached" read like an error, and the budget went in three large experiments.**
*Evidence:* the operator, 2026-11-17: "doesn't it mean the AI doesn't even know it has a limit and just extravagantly
runs simulations?" It was told the limit every turn; 12 of 39 sessions still ended that way, typically after
experiments of 12, 12, 12, 3 and 1.
*What we changed:* one experiment may use at most half of the simulations that are left, said in each turn's text;
the ending reads "all simulations used, report given in the last turn".
*Status:* partly: s041 ended by itself with 9 of 20 left; one session.

**A13. The first guesses must not fix the work.**
*Evidence:* the operator, 2026-11-17: "I want the cause and effect in the stages of the chain strong and grounded by
whys, but I don't want it fixed by the initially formed whys."
*What we changed:* a guess has a standing that can change: the AI looks at an earlier guess again in the light of
later results (`rethink`: still to verify, set aside, or refuted) or replaces it with a better one (`revises`). No new
hypothesis may come from a guess that was stated before the latest results until it has been looked at again; a
guess that was set aside can be taken up the same way. The page shows each guess with its standing now.
*Status:* open: tested with a scripted session; no real session has run on it yet.

**A14. "The chain did not change the finding" was the wrong sentence: the brief could not show it, and two links were hollow.**
*Evidence:* the operator, 2026-11-17: "Look into the system to find out defects or illogical implementation." Read
record by record, s033 and s041 end with the same recommendation because `trap-2` has one thing to find (TCP cannot
pass 1 MB / 20 ms = 419 Mbps) and both reach it; "11 simulations instead of 15" says little, the brief allows 4 an
experiment and the spending rule never applied. Underneath: (1) in both sessions the central hypothesis was "tested"
by a rule on a simulation whose result was already in the ledger: it could not fail, the harness wrote "held", the
report cited it (12 such rules in s026 to s041, all held, all cited); (2) s041 marked all 11 guesses "to verify",
set none aside and never took up two, one of them the true cause; (3) a hypothesis did not have to follow from the
guess it named (H2 of s041).
*What we changed:* a decision rule that names only results already measured is refused as no test; the report waits
once until every guess marked "to verify" has a hypothesis or a rethink; a second model call (the judge) reads each
new hypothesis against its guess and refuses one that does not follow, when two readings agree.
*Status:* partly: tested; on s041's nine pairs the judge refuses H2 every time and H3 once in three rounds, so it
can be wrong at the border. Whether the chain finds more needs a brief with more than one hidden cause.

**A15. The review of the step from one hypothesis to the next could be skipped without anyone noticing.**
*Evidence:* the operator, 2026-11-17: "the most significant upgrade is making the AI review the transition between
hypotheses. Make sure it is correctly implemented and visualize it nicely." Session s042 (the first with rethink and
the judge: 10 guesses, 12 rethinks, 14 hypotheses, 14 readings of the judge, 12 of 20 simulations, the same ceiling)
shows the hole in turn 3: its three rethinks named K4, K5, K6, the numbers of rethink records, were refused, and the
harness let it go on to four new hypotheses. A rethink was required only when a hypothesis came from the old guess.
*What we changed:* a guess whose hypothesis was just checked must be looked at again in the next answer before any new
hypothesis or experiment is accepted, and before the report; the turn's text says so first; an id of a guess can only
be written as Y and a number. On the page, "From one hypothesis to the next" stands under the board: one line for each
step in five columns (the results it had, its guess, the judge's reading, the hypothesis, what its test showed), each
turn's look-again at its head, and a turn that went on without it marked (s042, turn 3).
*Status:* partly: tested with scripted sessions; no real session has run under the rule yet.
**A16. What the AI writes about its own test repeats the test; a second voice needs a different view, not a second name.**
*Evidence:* a review of the 43 ledgers on 2026-11-18: of 474 verdicts none contradicted its check (378 repeat it); the judge, the same model given the same words, found 20 of 20 hypotheses to follow from their guesses; a rethink called a guess supported after its only hypothesis was refuted (s043); full format and plain arm scored the same gap on the one scored brief. *What we changed:* the arm "supervised": the researcher proposes and does not rule on its own tests; a supervisor, asked in a request of its own and never shown the researcher's reasons, reads each new guess against the records it cites, reviews each test before any simulation, and rules on what the checks mean. The checks stay facts: a ruling that does not fit them is recorded as inconclusive. *Status:* built and tested with a scripted supervisor; not yet measured whether the same model, asked this way, objects where it should.


**A17. A refusal that takes down everything built on it costs whole turns.**
*Evidence:* s049 turn 2: one refused citation took the turn's guesses, hypotheses and experiment with it; s051: 8 turns and no simulation, guesses
refused by the supervisor took 6 hypotheses and an experiment with them. *What we changed:* findings and decisions never refuse another part (A); a
refused test is repaired in the same turn (B); a refused guess is restated once in the same turn and then accepted, contested if it still fails (D).
*Status:* partly (scripted checks; no real session yet).

**A18. A reviewer that invents its own rival disagrees with itself.**
*Evidence:* s047: the supervisor's two answers about a test (the defect, and what the rule would do under its rival) disagreed 12 times, and the
harness sided with one of them; all 3 inconclusive verdicts of s047, and H1 and H4 of s050, came from such tests. *What we changed:* the researcher
states the rival; the supervisor judges it, each answer after its reasoning; answers that contradict each other are asked about once more (B).
*Status:* partly.

**A19. Something noticed and parked is forgotten unless it stays in view and needs a decision.**
*Evidence:* s048 and s049: six guesses set aside, none taken up again; threads that ask "why" parked as "less urgent for the goal". *What we
changed:* findings (A): each stays on a list at the top of every turn, needs a decision, and a report is held while one was never looked at.
*Status:* open (no session with findings yet).

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

**B4. A loss counted over a short window rewards a long queue.**
*Evidence:* `<flow>_loss_frac` counts the packets sent in the measured seconds that arrive up to 1 s after the stop, so
packets still waiting at the stop count as arrived. s059's reported answer (three-hosts: part 0.185, queue 1000) loses
9.990 % in 5 measured seconds, 10.511 % in 20 and 10.640 % in 80 (queue 100: 10.674 % in each): it meets "at most
10 %" only inside the window. Part 0.179 loses 9.86 % at every duration. The session's report said so itself.
*Status:* open, the operator's choice: longer measured seconds in such briefs, the harness measuring a recommendation
again at several times the duration, or a loss counted from the drops.

**B5. A result against a limit is not guarded by the tolerance.**
*Evidence:* the seed moves a result by about 0.2 % (three-hosts-link's baseline, seeds 1 to 5); the 1 % tolerance marks a
comparison of two results as decided by little, but 9.99 % against "at most 10 %" counts as met without a mark.
*Status:* open.

**B6. A text that describes the answer finds it.**
*Evidence:* the audit of 2026-11-24 (`plans/2026-11-24-prompt-audit.md`). On after_fix the scheduler was never tried in
s055 and s056, tried in turn 4 of s057 and in turn 1 of s058, the first session whose task sentence named the structure;
the instructions explain two queue kinds of seven, the plain queue the brief already has and the scheduler, which is the answer. On three-hosts-link the limits leave one
change that can be built and the instructions describe that one at four times the length; s061 made it in turn 1.
*Status:* open: the texts are unchanged until the operator says which to change; a brief must leave more than one move
open before a session on it can show that the AI found something.

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

**C6. A tool is named after the simulator's object, not after a pairing the page invented.**
*Evidence:* 2026-11-18: "UDP application" and "TCP application" were OnOff-on-UDP and BulkSend-on-TCP under names ns-3 does not have; the operator asked whether ns-3 really has two kinds of application, and could not find the NIC, which ns-3 makes together with the link. *What we changed:* the tools carry ns-3's names with the plain words under them; the card offers the choices ns-3 offers. *Status:* the operator's rule ("since I am using actual ns-3 as simulation component, viewer should match that"); N3 to N6 of `TOPOLOGY.md` are still narrower than ns-3.

**C7. A new view is tried by the click a reader makes, not by its address.**
*Evidence:* 2026-11-24: the block "from a hypothesis to its result" was built into the card that `?item=H1` opens and
checked there; a box of the board opens the pane of a test, where it was missing, and the operator asked "where?".
*What we changed:* the block stands in both panes; `ev_evidence.py` clicks a box of the board and looks for it.

**C8. A change to the page is not deployed on the checks of its own part alone.**
*Evidence:* 2026-11-24: the hover boxes of a simulation's objects took the key letter `o:`, which the parts of the
two-host network already had, and the key's new row widened a column; the checks of the new part passed, and the
checks of words and of the board found both only in the full run, hours after the change was live.
*What we changed:* before a page change goes live, the checks of words, board, polish and lean run with those of the
changed part (minutes, on a scratch copy); the full run follows.

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


**D9. A stand-in for the model answers as the harness expects; only a real call shows how the model fills a new format.**
*Evidence:* the batched first review passed every scripted check; its first real call named the test item "H1 UDP goodput rises with its part",
where the harness looked for "H1": every test of every batch would have been asked again alone, with nothing to show it but the time.
*What we changed:* the ids the model gives back are constrained to their exact values (an enum in the answer format); before a deploy, every new
answer format is sent once to the real model server, and each new kind of call is made once for real with its own token limit.
*Status:* confirmed (the call made again returned "H1").

**D10. A comparison of a few fields does not see what a misplaced comment removed.**
*Evidence:* a patch put a comment after a replaced field in the middle of a one-line statement of the page's model: the turn's report after it was
commented out, every "report accepted" step was gone, the script still parsed, and the comparison of the page's model over all sessions (a few
counts) showed nothing. The page checks' replays found it: one step fewer in each session.
*What we changed:* the page's model is compared in full before and after a change (every step of the track and every field of a turn, all sessions).
*Status:* confirmed.
**D11. One thing keyed in two places is keyed two ways after the next change.**
*Evidence:* the deploy of 2026-11-23 15:35 made a planned simulation's key the network its changes build and left the
search for an earlier one on the list as written; every scripted check passed, because none ran the same changed
network in two experiments, and the first real session (s061) spent 9 of its 12 simulations on repeats.
*What we changed:* both sides use `net_key`; the check reads real ledgers and fails if a repeat is not found.

**D12. A text is audited by reading it once and by a test that can be run again; the second finds what the rewrite left.**
*Evidence:* the audit by reading of 2026-11-24 led to v2's neutral paragraph on changes of the network (alphabetical kinds, the same depth). The
mechanical audit written a day later (`text_audit.py`) marked, in that rewritten paragraph, "each ns-3's queue disc of that name except the
scheduler" (the scheduler named before the list) and "for example 1Gbps"; on the texts s062 was sent it marked the sentences the operator had
called the hint. A check of wrong input found a third place, a refusal that said "or use a plain queue".
*Status:* confirmed on one rewrite.
*What we changed:* `harness/text_audit.py` and `harness_checks/test_fairness.py` (a planted example, order and sentence are each marked);
`test_bad_input.py` reads every refusal of a wrong network change for a suggested change.

## 5. Open questions

1. Does the loop help at all, against the same budget without hypotheses and against random search? (B1)
2. Do the instructions of 2026-11-15 change what the model does? One session says yes (s033, section 3); a few more
   on `trap-2`, and the same sessions without the two paragraphs, would say how often.
3. Should the final report have fields of its own for what limits the result and for the settings that made no
   difference? (They are asked for in the explanation.)
4. The warm-up as a setting. (The seed and the task text were settled on 2026-11-17: A5, A10.)
5. Should the page say "not accepted" everywhere? (How a hypothesis and its simulations belong together is shown
   since 2026-11-17: "Its simulations" in the pane a hypothesis opens, "for H3" on a running simulation's tile, and
   boxes on hover for a guess, a hypothesis and a claim.)
6. Does the chain of A11 and A13 find more than the loop before it, or only spend less? Sessions on a brief that is
   harder than `trap-2` would say.
