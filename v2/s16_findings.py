"""After v2.1: why the researcher never raised a finding (the operator's question of 2026-11-27), and what is changed for it.
Facts: in all 99 full replies since findings exist (s052 to s066) the researcher's own answer holds `findings: []`; the supervisor raised 145.
The supervisor was asked for findings before the researcher had seen the result: at the baseline before turn 1, after every explore experiment,
and inside every ruling. Asked again on the real model, the first reply of s063, s065 and s066 holds a finding in 0 of 6 askings with the
supervisor's findings on its list, and in 4 of 6 with an empty list (`plans/2026-11-27-harness-review.md`, section A).
  A1. The supervisor looks for findings AFTER the researcher's reply to a result, for every experiment alike (the baseline, an explore
      experiment, a test): one look in a turn, about the experiments of the turns before, which the researcher's reply has just answered. The
      ruling no longer asks for findings. The look is shown the researcher's findings (this reply's too) and, new, the researcher's guesses, and is
      told that a result a guess is about is not unexplained (A4: every look raised a finding, also for what four guesses already addressed).
  A2. The sentence that invites a finding stood only above an empty list (shown in no reply of any session): it stands in every turn's request.
  A3. A finding raised in the turn of the report does not hold that report back (the researcher's own could not be parked in the same reply, its
      id is not known yet; the supervisor's now comes after the reply): it is named in the report's open questions, as every finding not closed."""
import sys; sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent))
from patchlib import sub, done

sub("harness/loop.py",
    '''BATCH_FIRST = True   # the arm "supervised"''',
    '''LOOK_AFTER_REPLY = True   # the arm "supervised" (2026-11-27, the operator: "Why doesn't the researcher propose findings?"): the supervisor looks for findings after the researcher's reply to a result, never before; the ruling asks for none
BATCH_FIRST = True   # the arm "supervised"''',
    "A1. the switch")

# the ruling no longer asks for findings
sub("harness/loop.py",
    '''            + f"\\n\\nTHE FINDINGS SO FAR:\\n{findings_for_supervisor(ledger)}\\n" + SUP_FINDINGS_ASK)   # findings (2026-11-22)''',
    '''            + ("" if LOOK_AFTER_REPLY else f"\\n\\nTHE FINDINGS SO FAR:\\n{findings_for_supervisor(ledger)}\\n" + SUP_FINDINGS_ASK))   # findings (2026-11-22); since 2026-11-27 the supervisor's findings come from its look after the researcher's reply''',
    "A1. the ruling's request ends without the findings so far and without the request for findings")
sub("harness/loop.py",
    '''RULING3_SCHEMA["properties"]["findings"]["items"] = FINDING_ITEM''',
    '''if LOOK_AFTER_REPLY:   # the ruling's answer has no findings
    for _s in (RULING_SCHEMA, RULING3_SCHEMA):
        _s["properties"].pop("findings", None)
        _s["required"] = [k for k in _s["required"] if k != "findings"]
RULING3_SCHEMA["properties"].get("findings", {})["items"] = FINDING_ITEM''',
    "A1. the ruling's answer format has no field findings")
sub("harness/loop.py",
    '''RULING_SCHEMA["properties"]["findings"]["items"] = FINDING_ITEM
''',
    '''RULING_SCHEMA["properties"].get("findings", {})["items"] = FINDING_ITEM
''',
    "A1. (the same, the older ruling)", )
sub("harness/loop.py",
    '''            take_sup_findings(ledger, turn, ruling.get("findings"), vid)   # what it found unexplained in these results (2026-11-22)''',
    '''            if not LOOK_AFTER_REPLY:
                take_sup_findings(ledger, turn, ruling.get("findings"), vid)   # what it found unexplained in these results (2026-11-22)''',
    "A1. (code) no finding is taken from a ruling")

# the look
sub("harness/loop.py",
    '''    user = (_system_for_supervisor(brief) + f"\\nWHAT HAS JUST BEEN MEASURED ({xid}):\\n{_measured(ledger, xid)}\\n\\nWHAT WAS MEASURED BEFORE:\\n"
            f"{_measured([r for r in ledger if not (r['type'] == 'evidence' and r['body']['experiment'] == xid)])}\\n\\nEVERY READING OF THE SESSION:\\n{_looked(ledger)}\\n\\n"
            f"THE FINDINGS SO FAR:\\n{findings_for_supervisor(ledger)}\\n\\n" + SUP_FINDINGS_ASK)''',
    '''    xids = list(xid) if isinstance(xid, (list, tuple)) else [xid]
    if LOOK_AFTER_REPLY:   # the experiments of earlier turns, after the researcher's reply to them; ledger: what stood when that reply was given, and what the reply itself stated
        user = (_system_for_supervisor(brief) + f"\\nTHE RESULTS YOU ARE ASKED ABOUT ({', '.join(xids)}); the researcher has seen them and has replied:\\n" + "\\n".join(_measured(ledger, x) for x in xids)
                + f"\\n\\nWHAT ELSE HAD BEEN MEASURED:\\n{_measured([r for r in ledger if not (r['type'] == 'evidence' and r['body']['experiment'] in xids)])}\\n\\nEVERY READING OF THE SESSION:\\n{_looked(ledger)}\\n\\n"
                + guesses_text(ledger).replace(" (a competing cause may already be one of them)", "")
                + f"THE FINDINGS SO FAR:\\n{findings_for_supervisor(ledger)}\\n\\n" + SUP_FINDINGS_ASK
                + " Only about the results you are asked about. A result that one of the guesses above is about is not unexplained in this sense, whether or not that guess has been tested.")
        d = (ask_fn or supervise)(model, user, FINDINGS_SCHEMA)
        return list(d.get("findings") or [])[:SUP_FINDINGS], user
    user = (_system_for_supervisor(brief) + f"\\nWHAT HAS JUST BEEN MEASURED ({xid}):\\n{_measured(ledger, xid)}\\n\\nWHAT WAS MEASURED BEFORE:\\n"
            f"{_measured([r for r in ledger if not (r['type'] == 'evidence' and r['body']['experiment'] == xid)])}\\n\\nEVERY READING OF THE SESSION:\\n{_looked(ledger)}\\n\\n"
            f"THE FINDINGS SO FAR:\\n{findings_for_supervisor(ledger)}\\n\\n" + SUP_FINDINGS_ASK)''',
    "A1, A4. the supervisor's look: after the reply, for one or several experiments, with the researcher's guesses, and only about those results")
sub("harness/loop.py",
    '''        if arm == "supervised" and fresh and any(r["id"] == "E0" for r in ledger):   # findings (2026-11-22)''',
    '''        looked = set() if fresh else {r["id"] for r in ledger if r["type"] == "experiment"}   # the experiments the supervisor has looked at for findings, or will not (a session taken up again)
        if arm == "supervised" and fresh and not LOOK_AFTER_REPLY and any(r["id"] == "E0" for r in ledger):   # findings (2026-11-22)''',
    "A1. (code) no look at the baseline before turn 1")
sub("harness/loop.py",
    '''                if arm == "supervised" and ex.get("kind") != "test":   # results with no ruling (an explore experiment)''',
    '''                if arm == "supervised" and ex.get("kind") != "test" and not LOOK_AFTER_REPLY:   # results with no ruling (an explore experiment)''',
    "A1. (code) no look at an explore experiment in the turn it ran")
sub("harness/loop.py",
    '''            settle_findings(remap_refs(parsed), ledger, turn, due_before, made, [x for x in whys_made if x[1]], goes_on=stay_next)
''',
    '''            settle_findings(remap_refs(parsed), ledger, turn, due_before, made, [x for x in whys_made if x[1]], goes_on=stay_next)
            if arm == "supervised" and LOOK_AFTER_REPLY and not stay_next:
                # the supervisor's look (2026-11-27): the experiments of earlier turns, whose results this turn's reply has now answered. It is shown the ledger as
                # it stood for that reply and what the reply stated (its guesses, findings and decisions), not what this turn's own experiment measured
                due = [r["id"] for r in ledger if r["type"] == "experiment" and r["turn"] < turn and r["id"] not in looked and any(e["type"] == "evidence" and e["body"]["experiment"] == r["id"] for e in ledger)]
                if due:
                    looked.update(due)
                    then = [r for r in ledger if r["turn"] < turn or r["type"] in ("why", "hypothesis", "finding", "decision", "drop")]
                    try:
                        stage("look", due[-1])
                        items, saw = sup_findings_of(model, brief, then, due)
                        take_sup_findings(ledger, turn, items, due[-1])
                        sup_log(due[-1], "findings", saw, {"findings": items, "about": due})
                    except (ValueError, KeyError, TypeError) as e:
                        append(ledger, turn, "note", due[-1], {"text": f"the supervisor's look at {', '.join(due)} could not be read ({type(e).__name__}): no finding of its own"})
''',
    "A1. (code) the look after the reply, once in a turn, for the experiments of the turns before")

# A2
sub("harness/loop.py",
    '''        ask = ((f"Give one decision (decisions) for each finding marked DUE: {', '.join(due)}. " if due else "No finding needs a decision this turn. ")''',
    '''        ask = ("A result that is not explained and not on this list: state it in findings (about, text). "   # 2026-11-27 (A2): it stood only above an empty list
               + (f"Give one decision (decisions) for each finding marked DUE: {', '.join(due)}. " if due else "No finding needs a decision this turn. ")''',
    "A2. every turn's list of findings invites a new one (the sentence stood only above an empty list)")

# A3
sub("harness/loop.py",
    '''and len(held_turns - {turn}) < FINDING_HOLDS and (unseen := findings_unseen(ledger)):''',
    '''and len(held_turns - {turn}) < FINDING_HOLDS and (unseen := [f for f in findings_unseen(ledger) if f not in {r["id"] for r in ledger if r["type"] == "finding" and r["turn"] == turn}]):   # 2026-11-27 (A3): not one raised in this turn''',
    "A3. (code) a finding raised in the turn of the report does not hold the report back")
done("stage16_findings", "after v2.1 (2026-11-27): the supervisor looks for findings after the researcher's reply; every turn invites a finding")
