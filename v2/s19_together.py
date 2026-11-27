"""After v2.2.2 (2026-11-27, the operator: "remove unnecessary delay so that a session finishes earlier"). A session is the model writing (94 to
100 % of its time, at about 86 tokens a second), and requests of the same kind to the supervisor were sent one after another although none of
them is shown another's answer: in s067, three reviews of tests and three rulings in turn 1, two and two in turn 8, two rulings in turn 5:
6.5 of 65 minutes. They are now sent together. No text changes, and no rule: each request is built as before; the answers are fetched ahead,
kept by the exact text of their request, and the unchanged code that asks one after another takes each from there. A request whose text has
changed by the time its turn comes (an earlier answer changed what it is shown) is simply asked as before.
  - `called_together`: several calls of the model at once; the first is the one the page shows while it comes in; each is written to calls.jsonl
    with its own step and its own seconds, in the order they were asked for. With a scripted model (the harness checks) they are made one after
    another, in order.
  - `supervise`: takes an answer fetched ahead for exactly this request, if there is one.
  - the two places: the first reviews of the tests of a reply that are asked alone (two or more), and the rulings of an experiment's tests (two or more)."""
import sys; sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent))
from patchlib import sub, done

sub("harness/loop.py",
    '''import argparse, json, os, re, signal, sys, time
from pathlib import Path''',
    '''import argparse, json, os, re, signal, sys, threading, time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path''',
    "(code) threads")
sub("harness/loop.py",
    '''                if time.time() - LIVE["last"] >= 1.0:''',
    '''                if not getattr(QUIET, "on", False) and time.time() - LIVE["last"] >= 1.0:   # of several calls made together, one is shown as it comes in''',
    "(code) of several calls made together, the page's live record follows the first")
sub("harness/loop.py",
    '''def ask(model, system, user, schema, draft, temperature, max_tokens):
    body = {"model": model,''',
    '''QUIET = threading.local()   # .on: this thread's call is not the one live_call.json follows (calls made together)
TOGETHER = True   # the supervisor's requests of the same kind in one step are sent together (2026-11-27)


def ask(model, system, user, schema, draft, temperature, max_tokens):
    body = {"model": model,''',
    "(code) the switch")
sub("harness/loop.py",
    '''# ---- every call of the model, as it was made (2026-11-22, the operator: a page of their own to see what the agents are shown and what they write):''',
    '''ASK0 = ask   # the call of the model server itself: a scripted model (the harness checks) puts its own in ask's place, and is then asked one request after another

# ---- every call of the model, as it was made (2026-11-22, the operator: a page of their own to see what the agents are shown and what they write):''',
    "(code) how a scripted model is told from the model server")
sub("harness/loop.py",
    '''# ---- the judge (2026-11-17, the operator's decision): a second model call''',
    '''def called_together(specs):
    """Several calls of the model made at once (2026-11-27): specs = [(agent, model, system, user, schema, draft, temperature, max_tokens, step)].
    Returns, in the same order, what called() returns for each, or the exception it raised. The page's live record follows the first; every call
    is written to calls.jsonl when all are in, in order, with its own step and its own seconds. A scripted model is asked one after another."""
    def one(i, s):
        QUIET.on = i > 0
        t0 = time.time()
        try:
            return ask(*s[1:8]), t0, time.time()
        except Exception as e:
            return e, t0, time.time()
    if not specs:
        return []
    first = specs[0]
    LIVE["call"] = {"n": CALLS["n"] + 1, "turn": CALLS["turn"], "agent": first[0], "step": first[8], "started": time.strftime("%Y-%m-%dT%H:%M:%S"), "t0": time.time(), "reasoning": "", "answer": "",
                    "together": len(specs)}
    LIVE["last"] = 0.0
    live_write()
    if len(specs) == 1 or globals()["ask"] is not ASK0:
        got = [one(0, s) for s in specs]
    else:
        with ThreadPoolExecutor(len(specs)) as pool:
            got = list(pool.map(lambda x: one(*x), enumerate(specs)))
    out = []
    for s, (r, t0, t1) in zip(specs, got):
        out.append(r)
        if isinstance(r, Exception):
            continue
        content, reasoning, finish_reason, usage = r
        CALLS["n"] += 1
        by_agent = CALLS.setdefault("by", {})
        by_agent[s[0]] = by_agent.get(s[0], 0) + 1
        try:
            with (tools.SESSION / "calls.jsonl").open("a") as f:
                f.write(json.dumps({"n": CALLS["n"], "turn": CALLS["turn"], "agent": s[0], "step": s[8], "at": time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime(t1)), "seconds": round(t1 - t0, 1),
                                    "model": s[1], "draft": bool(s[5]), "temperature": s[6], "max_tokens": s[7], "system": s[2], "user": s[3],
                                    "reasoning": reasoning, "answer": content, "finish_reason": finish_reason, "usage": usage, "together": len(specs)}) + "\\n")
        except (OSError, TypeError, ValueError):
            pass   # the record of a call never stops the session
    r0 = got[0][0]
    if isinstance(r0, Exception):
        live_write(done=True, error=f"{type(r0).__name__}: {' '.join(str(r0).split())[:300]}")
    else:
        live_write(done=True, reasoning=r0[1], answer=r0[0], finish_reason=r0[2], usage=r0[3])
    return out


# ---- the judge (2026-11-17, the operator's decision): a second model call''',
    "(code) several calls at once, each recorded as one call")
sub("harness/loop.py",
    '''    user += "\\n\\nYOUR ANSWER: one JSON object with these fields, in this order:\\n" + fields_text(schema)   # what each field holds (the coherence audit, 2026-11-22)
    content = called("supervisor", model, SUPERVISOR, user, schema, True, 0, max_tokens)[0]
    try:''',
    '''    if user in AHEAD:   # the answer fetched ahead for exactly this request (2026-11-27: requests of one kind are sent together)
        got = AHEAD.pop(user)
        if isinstance(got, Exception):
            raise got
        content = got
    else:
        content = called("supervisor", model, SUPERVISOR, user + SUP_FIELDS(schema), schema, True, 0, max_tokens)[0]
    try:''',
    "(code) supervise takes an answer fetched ahead for exactly its request")
sub("harness/loop.py",
    '''def supervise(model, user, schema, max_tokens=9000):''',
    '''SUP_FIELDS = lambda schema: "\\n\\nYOUR ANSWER: one JSON object with these fields, in this order:\\n" + fields_text(schema)   # what each field holds (the coherence audit, 2026-11-22)
AHEAD = {}   # a request's text -> the supervisor's answer fetched ahead for it (or the exception that call raised)


class _Asked(Exception):
    """Raised by the stand-in that takes a request instead of sending it (asked_first)."""


def asked_first(fn):
    """The first request fn(ask_fn) would send to the supervisor, taken and not sent: (user, schema, max_tokens), or None when it sends none or
    cannot be built. fn is a function of the harness that takes ask_fn (review_design, rule_on, ...)."""
    got = []
    def take(model, user, schema, max_tokens=9000):
        got.append((user, schema, max_tokens))
        raise _Asked()
    try:
        fn(take)
    except _Asked:
        return got[0]
    except Exception:
        return None
    return None


def supervise_ahead(model, requests):
    """Sends several requests to the supervisor together: requests = [(user, schema, max_tokens, step)]. Each answer waits in AHEAD under the
    request's text; supervise() takes it when the code that asks one after another comes to that very request."""
    specs = [("supervisor", model, SUPERVISOR, u + SUP_FIELDS(sc), sc, True, 0, mt, st) for u, sc, mt, st in requests]
    for (u, _sc, _mt, _st), r in zip(requests, called_together(specs)):
        AHEAD[u] = r if isinstance(r, Exception) else r[0]


def supervise(model, user, schema, max_tokens=9000):''',
    "(code) the requests taken, sent together, and kept by their text")

# the first reviews of a reply's tests that are asked alone
sub("harness/loop.py",
    '''        held, gone, gone_h = [], [], []
        for hid in ex["tests"]:
            test = test_of(ex, hid)''',
    '''        held, gone, gone_h = [], [], []
        ahead = {}   # hypothesis -> the text of its first review's request, sent ahead with the others (2026-11-27)
        AHEAD.clear()
        if TOGETHER:
            h_text = lambda hid: next((r["body"].get("text") for r in ledger if r["type"] == "hypothesis" and r["id"] == hid), "")
            alone = [hid for hid in ex["tests"] if test_key(ex, hid, h_text(hid)) not in prereviewed or restated_since(ledger, turn, ex, hid)]
            reqs = [(hid, asked_first(lambda take, hid=hid: review_design(model, brief, ledger, ex, hid, ask_fn=take))) for hid in alone] if len(alone) > 1 else []
            reqs = [(hid, r) for hid, r in reqs if r]
            if len(reqs) > 1:
                for hid, _r in reqs:
                    stage("design", hid, 1)
                supervise_ahead(model, [(u, sc, mt, {"step": "design", "about": hid, "round": 1, "by": None}) for hid, (u, sc, mt) in reqs])
                ahead = {hid: u for hid, (u, _sc, _mt) in reqs}
        for hid in ex["tests"]:
            test = test_of(ex, hid)''',
    "(code) the first reviews of a reply's tests that are asked alone are sent together")
sub("harness/loop.py",
    '''            try:
                if pre is None:
                    stage("design", hid, 1)
                rev, saw = review_or_cannot(''',
    '''            try:
                if pre is None and ahead.get(hid) not in AHEAD:
                    stage("design", hid, 1)
                rev, saw = review_or_cannot(''',
    "(code) a review whose answer waits is not announced as a step a second time")

# the rulings of an experiment's tests
sub("harness/loop.py",
    '''        xid = next(r["id"] for r in reversed(ledger) if r["type"] == "experiment")
        for hid in ex["tests"]:
            rule_one(xid, hid)
''',
    '''        xid = next(r["id"] for r in reversed(ledger) if r["type"] == "experiment")
        AHEAD.clear()
        if TOGETHER and len(ex["tests"]) > 1:   # the rulings of this experiment's tests, sent together (2026-11-27); rule_one then takes each answer in its turn
            reqs = [(hid, asked_first(lambda take, hid=hid: rule_request(xid, hid, take))) for hid in ex["tests"]]
            reqs = [(hid, r) for hid, r in reqs if r]
            if len(reqs) > 1:
                for hid, _r in reqs:
                    stage("ruling", hid)
                supervise_ahead(model, [(u, sc, mt, {"step": "ruling", "about": hid, "round": None, "by": None}) for hid, (u, sc, mt) in reqs])
                ruling_ahead.update({hid: u for hid, (u, _sc, _mt) in reqs})
        for hid in ex["tests"]:
            rule_one(xid, hid)
        AHEAD.clear()
        ruling_ahead.clear()
''',
    "(code) the rulings of an experiment's tests are sent together")
sub("harness/loop.py",
    '''    def rule_one(xid, hid):
        """The supervisor's ruling on one checked test: the hypothesis's verdict."""
        if True:''',
    '''    ruling_ahead = {}   # hypothesis -> the text of its ruling's request, sent ahead with the others
    def rule_request(xid, hid, ask_fn):
        """The request for the ruling on one checked test, as rule_one makes it (for asked_first: ask_fn takes it instead of sending it)."""
        if not any(r["type"] == "check" and r["body"]["experiment"] == xid and r["body"]["for"] == hid and r["body"]["result"] in ("held", "failed") for r in ledger):
            return None
        doubt = next((r["body"].get("doubt_if") or "" for r in reversed(ledger) if r["type"] == "review" and r.get("by") == "supervisor" and r["body"].get("gate") != "ground" and r["body"].get("for") == hid), "")
        last_rev = next((r["body"] for r in reversed(ledger) if r["type"] == "review" and r.get("by") == "supervisor" and r["body"].get("gate") == "design" and r["body"].get("for") == hid), None)
        return rule_on(model, brief, ledger, xid, hid, doubt, ask_fn=ask_fn, contested=objected.get(hid), review=last_rev if competitors else None)

    def rule_one(xid, hid):
        """The supervisor's ruling on one checked test: the hypothesis's verdict."""
        if True:''',
    "(code) the ruling's request, as rule_one makes it, for sending ahead")
sub("harness/loop.py",
    '''            try:
                stage("ruling", hid)
                last_rev = next(''',
    '''            try:
                if ruling_ahead.get(hid) not in AHEAD:
                    stage("ruling", hid)
                last_rev = next(''',
    "(code) a ruling whose answer waits is not announced as a step a second time")
done("stage19_together", "after v2.2.2 (2026-11-27): the supervisor's requests of one kind are sent together (no text and no rule changes)")
