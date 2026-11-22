"""One scripted session of harness/loop.py: the model server is replaced by a list of answers, everything else is the
real loop (the ledger, the refusals, the simulator). Run with HOME set to a scratch home whose project/ holds the
harness, the briefs and a link to ns-3.49, never the real one:
    HOME=<scratch>/home python3 -I scripted.py ANSWERS.json --brief ID --session ID [--policy cap] [any loop.py flag]
ANSWERS.json: a list; each item is one answer of the model (an object, sent as JSON), or a string sent as it is.
For the arm "supervised" it may be {"answers": [...], "supervisor": [...]}: the second list holds the supervisor's answers in the order it is
asked. When that list is used up (or absent) the scripted supervisor finds no defect and rules as the checks say. What the supervisor was shown
is written to supervisor_sent.json.
When the list is used up the model server "fails", and the session ends with "model server error"."""
import json, sys
from pathlib import Path
assert "scratch" in str(Path.home()), "scripted sessions run in a scratch copy only (HOME must be the scratch home)"
sys.path.insert(0, str(Path.home() / "project/harness"))
import loop  # noqa: E402
import os  # noqa: E402
for k, v in json.loads(os.environ.get("SCRIPTED_SET") or "{}").items():   # a check may set a constant of the loop for its session, e.g. {"AFTER_ROUNDS": "dropped"} (2026-11-22)
    setattr(loop, k, v)
answers = json.loads(Path(sys.argv[1]).read_text())
sup_answers, sup_users = (answers.get("supervisor") or [], []) if isinstance(answers, dict) else ([], [])
answers = answers["answers"] if isinstance(answers, dict) else answers
import re
def supervisor(user, schema):
    """The scripted supervisor's answer to one request: the next of its list, or, when that is used up, no defect and a ruling as the checks say."""
    need = schema["required"]
    if need == ["findings"]:   # its look at results no ruling covers (findings, 2026-11-22): the next answer of its list only if that is one of this kind
        return sup_answers.pop(0) if sup_answers and set(sup_answers[0]) == {"findings"} else {"findings": []}
    if sup_answers:
        return sup_answers.pop(0)
    if "doubt_if" in need:   # the review of a test before it runs (since 2026-11-22 it judges the researcher's rival, in rounds): approved
        return {"reads": "what the script reads", "stronger_rival": "none stronger than the researcher's", "rival_is_weak": False, "under_rival": "the rule would fail under it",
                "rival": "the script's rival", "rival_outcome": "failed", "doubt_if": "nothing the script can name", "defect": "none", "because": "the script's supervisor finds no defect", "feedback": ""}
    if "rival_outcome" in need:   # the one question about boxes that contradicted each other (2026-11-22): answered without a contradiction
        return {"because": "the script's second answer", "rival_outcome": "failed", "defect": "none"}
    if "records_show" in need:
        return {"records_show": "what the script reads in them", "nearest_earlier": "none", "defect": "none", "because": "the script's supervisor finds no defect"}
    if "stands" in need:
        return {"answer": "the script's second look", "stands": True, "result": "inconclusive", "because": "the script's supervisor keeps its ruling"}
    facts = user.split("THE HARNESS'S CHECKS (facts):", 1)[1].split("\n\n", 1)[0]
    return {"shows": "what the checks say", "fair": True, "defect": "none", "result": "refuted" if ":  FAILED" in facts else "supported", "because": "the script's supervisor rules as the checks say", "retest": ""}
def with_needs(a):
    """A scripted test experiment written before 2026-11-17 has no needs: they are filled in from its rules, so that such a script goes on
    testing what it was written for. For each tested hypothesis: the simulations its rules name (a design no rule names goes to the first
    hypothesis), the one knob that differs between them (none for one simulation), the first measure its rules name."""
    ex = a.get("experiment") if isinstance(a, dict) else None
    if not isinstance(ex, dict) or ex.get("kind") != "test" or "needs" in ex or "varied" not in ex:   # no varied: the short format (2026-11-22), whose needs the harness derives
        return a
    runs = {r["label"]: r.get("params") or {} for r in ex.get("runs") or []}; needs = []; seen = set()
    for h in ex.get("tests") or []:
        rules = [d.get("decision_rule") or "" for d in ex.get("decision_rules") or [] if d.get("for") == h]
        labs = [l for l in dict.fromkeys(l for r in rules for l in re.findall(r"@([A-Za-z0-9_]+)", r)) if l in runs]; seen |= set(labs)
        m = re.search(r"([A-Za-z_][A-Za-z0-9_]*)@", " ".join(rules))
        needs.append({"for": h, "to_know": "what its rule compares", "measure": m.group(1) if m else "", "simulations": labs})
    idle = [l for l in runs if l not in seen]
    if needs and idle: needs[0]["simulations"] += idle
    for n in needs:
        ls = n["simulations"]; differ = sorted({k for x in ls for y in ls for k in set(runs[x]) | set(runs[y]) if runs[x].get(k) != runs[y].get(k)})
        other = any((next(r for r in ex["runs"] if r["label"] == x).get("structure") or []) != (next(r for r in ex["runs"] if r["label"] == y).get("structure") or []) for x in ls for y in ls)
        named = [k for k in ex.get("varied") or [] if k in differ]   # the knob the script itself says it varies, before a setting it only happens to state differently
        n["varies"] = "none" if len(ls) <= 1 else "structure" if other and not differ else (named or differ)[0] if differ else "none"
    return {**a, "experiment": {**ex, "needs": needs}}
if "supervised" not in sys.argv:   # the arm "supervised" has a short reply without needs: there the harness derives them itself, and the script must not
    answers = [with_needs(a) for a in answers]
formats, users = [], []
def ask(model, system, user, schema, draft, temperature, max_tokens):
    if system == getattr(loop, "SUPERVISOR", None):   # a request to the supervisor of the arm "supervised": its own script, its own record of what it was shown
        sup_users.append(user)
        return json.dumps(supervisor(user, schema)), "", "stop", {"completion_tokens": 0}
    formats.append(schema); users.append(user)
    if not answers:
        raise loop.ModelServerError("the script has no more answers")
    a = answers.pop(0)
    # a script written before 2026-11-17 states hypotheses without the why they come from: one why is put before them (about the brief,
    # worth verifying), numbered after the last why the ledger shows, and each hypothesis is said to come from it
    if isinstance(a, dict) and a.get("hypotheses") and "whys" not in a and not any(h.get("from_why") for h in a["hypotheses"]) and "whys" in (schema.get("properties") or {}):
        n = max([int(x) for x in re.findall(r"^\[Y(\d+)\]", user, flags=re.M)], default=0) + 1
        about = ["brief"]   # each hypothesis keeps the follows_from its script states, and the harness judges that as before
        a = {**a, "whys": [{"about": about, "result": "what the records show so far", "guess": "the script's guess", "unseen": "something in the system", "matters": "it decides the answer", "worth": "verify", "reason": "it serves the goal"}],
             "hypotheses": [{**h, "from_why": f"Y{n}"} for h in a["hypotheses"]]}
    # a script written before the review of each step was required (2026-11-17) gives no rethink: one is put in for every guess the turn's text
    # says is due ("LOOK AGAIN FIRST: ... Y4 (H4: C4 held; ...)"), in the light of the first check named with it
    if isinstance(a, dict) and "rethink" not in a and "rethink" in (schema.get("properties") or {}) and "LOOK AGAIN FIRST:" in user:
        due = re.findall(r"(Y\d+) \(([^)]*)\)", user.split("LOOK AGAIN FIRST:", 1)[1].split("Before anything new", 1)[0])
        a = {**a, "rethink": [{"id": y, "in_light_of": re.findall(r"C\d+", what)[:1], "now": "supported", "because": "the script's review of the step"} for y, what in due]}
    return (a if isinstance(a, str) else json.dumps(a)), "", "stop", {"completion_tokens": 0}
class Models:
    def json(self): return {"data": [{"id": "scripted"}]}
loop.ask, loop.count_tokens, loop.requests.get = ask, (lambda model, text: 100), (lambda *a, **k: Models())
# the judge of a scripted session: every hypothesis follows from its guess, except one whose text says UNRELATED (test_chain.py)
loop.judge_link = lambda model, brief, why, hyp: (("UNRELATED" not in hyp.get("text", "")), "the script's judge: its text says so" if "UNRELATED" in hyp.get("text", "") else "the script's judge")
sys.argv = ["loop.py", "--draft", "off"] + sys.argv[2:]
try:
    loop.main()
finally:
    if formats:  # the answer format the session sent with each request, for the test to read
        (loop.tools.SESSION / "format_sent.json").write_text(json.dumps(formats[0], indent=1) + "\n")
        (loop.tools.SESSION / "users_sent.json").write_text(json.dumps(users) + "\n")
    if sup_users:
        (loop.tools.SESSION / "supervisor_sent.json").write_text(json.dumps(sup_users) + "\n")   # what the model was given in each turn (the brief, the budget, the tolerance, the ledger)
