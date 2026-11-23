"""The task the model reads is written by the harness from the brief's aim and the settings it leaves open (the
operator's question of 2026-11-17: "is it okay that the task stays the same regardless of settings?"; in `trap` it
contradicted the aim, the open settings and the fixed UDP rate). No model and no simulation is needed:
  - a brief without a task of its own gets the sentence: the aim (given: largest or smallest measure, with its
    conditions; open: choose what performance means), the settings that may be changed, by name and number;
  - the sentence follows the brief: another aim, a knob made fixed, a condition added each change it;
  - a brief that states a task of its own keeps it (the briefs made before), and so do their sessions;
  - a {placeholder} of the description stands for a fixed setting's value or, for a knob, "the knob <name>"; one that
    names no setting of the brief is refused;
  - a session opened on such a brief is given the sentence; a brief saved from the page without a task has no task in
    its file, and one saved with a task keeps it.
    python3 test_task_text.py SCRATCH_DIR [HARNESS_DIR]
SCRATCH_DIR is made new."""
import copy, json, os, shutil, sys
from pathlib import Path
REAL = Path.home() / "project"
args = [a for a in sys.argv[1:] if not a.startswith("--")]
SCR, SRC = Path(args[0]).resolve(), Path(args[1]).resolve() if len(args) > 1 else REAL / "harness"
assert "scratch" in str(SCR) or "hs_" in str(SCR)
P = SCR / "home/project"
shutil.rmtree(SCR, ignore_errors=True); (P / "sessions").mkdir(parents=True); (P / "checks").mkdir()
shutil.copytree(SRC, P / "harness", ignore=shutil.ignore_patterns("__pycache__", "loop.log")); shutil.copytree(REAL / "briefs", P / "briefs")
os.environ["HOME"] = str(SCR / "home"); sys.path.insert(0, str(P / "harness"))
import tools, control
assert tools.ROOT == P
FAILED = []
def say(ok, text):
    print(f"  {'ok  ' if ok else 'FAIL'} {text}", flush=True)
    if not ok: FAILED.append(text[:60])
raw = lambda b: json.loads((P / f"briefs/{b}.json").read_text())
def made(b, bid="x"):
    b = copy.deepcopy(b); b["id"] = bid; return tools.check_brief(b, bid)

trap = raw("trap"); own = trap["task"]; t = copy.deepcopy(trap); del t["task"]; a = made(t)["task"]
say(a == "Find the settings that give the largest tcp_goodput_bps, while udp_loss_frac <= 0.01. You may change 5 settings (weightUdp, queuePkts, tcpVariant, duration, seed); every other setting is fixed. Explain why they are best.",
    f"trap without its own task: “{a}”")
say("maximum rate" not in a and "best ratio" not in a and "chose to mean" not in a and "udpRate" not in a, "it says nothing of a maximum rate, of the ratio alone, or of choosing what performance means; udpRate, which trap fixes, is not among the settings it names")
o = raw("two-hosts-open"); del o["task"]; b = made(o)["task"]
say(b.startswith("No aim is given. Choose what 'performance' should mean for this system and say why") and "You may change 6 settings (weightUdp, udpRate, queuePkts, tcpVariant, duration, seed)" in b, f"a brief with an open aim: “{b}”")
t2 = copy.deepcopy(t); t2["goal"]["target"] = {"measure": "udp_loss_frac", "direction": "min"}; t2["goal"]["conditions"] = ["tcp_goodput_bps >= 100000000", "link_util >= 0.9"]
t2["system"]["seed"] = 1; del t2["knobs"]["seed"]; c = made(t2)["task"]
say(c == "Find the settings that give the smallest udp_loss_frac, while tcp_goodput_bps >= 100000000 and link_util >= 0.9. You may change 4 settings (weightUdp, queuePkts, tcpVariant, duration); every other setting is fixed. Explain why they are best.",
    f"another aim, two conditions and the seed made fixed change the sentence: “{c}”")
t3 = copy.deepcopy(t2); t3["goal"]["conditions"] = []; [t3["system"].__setitem__(k, t3["knobs"].pop(k)["default"]) for k in ("queuePkts", "tcpVariant", "duration")]; d = made(t3)["task"]
say(d == "Find the settings that give the smallest udp_loss_frac. You may change 1 setting (weightUdp); every other setting is fixed. Explain why they are best.", f"no condition and one open setting: “{d}”")
say(made(trap)["task"] == own and tools.load_brief("trap")["task"] == own and all(tools.load_brief(p.stem)["task"] == raw(p.stem)["task"] for p in (P / "briefs").glob("*.json") if raw(p.stem).get("task")),
    f"a brief that states a task of its own keeps it, word for word (the {sum(bool(raw(p.stem).get('task')) for p in (P / 'briefs').glob('*.json'))} saved briefs that state one)")
bad = copy.deepcopy(t); bad["task"] = "  "
try: made(bad); r = None
except ValueError as e: r = str(e)
say(r and "'task' must be a text, or be left out" in r, f"a task that is there but empty is refused: “{r}”")

# ---- the description's placeholders
o2 = raw("two-hosts-open"); o2["description"] = o2["description"].replace("(the setting udpRate)", "({udpRate})"); k = made(o2)["description"]
o3 = copy.deepcopy(o2); o3["system"]["udpRate"] = "300Mbps"; del o3["knobs"]["udpRate"]; f = made(o3)["description"]
say("at a constant rate (the knob udpRate)" in k and "at a constant rate (300Mbps)" in f and "{" not in k + f, "one description serves both: “… at a constant rate (the knob udpRate)” where udpRate is a knob, “… (300Mbps)” where it is fixed")
o4 = copy.deepcopy(o2); o4["description"] += " {bandwidth}"
try: made(o4); r = None
except ValueError as e: r = str(e)
say(r and "{bandwidth}, which is not one of the brief's settings" in r, f"a placeholder that names no setting of the brief is refused: “{r}”")

# ---- a session, and a brief saved from the page
t["id"] = "trap-auto"; (P / "briefs/trap-auto.json").write_text(json.dumps(t)); sid = tools.open_session("x1", "trap-auto")
say(tools.BRIEF["task"] == a and tools.BRIEF["id"] == "trap-auto", "a session opened on a brief without a task is given the sentence written by the harness")
sid = tools.open_session("x2", "trap")
say(tools.BRIEF["task"] == own, "a session opened on trap itself is given trap's own text, as before")
form = copy.deepcopy(t); form["id"] = "from-page"; form["task"] = ""; r = control.save_brief({"brief": form}); disk = raw("from-page")
say(r["saved"] == "from-page" and "task" not in disk and tools.load_brief("from-page")["task"] == a, "a brief saved from the page with no task has no task in its file, and is read with the harness's sentence")
form["id"] = "from-page-own"; form["task"] = "My own words."; control.save_brief({"brief": form})
say(raw("from-page-own")["task"] == "My own words." and tools.load_brief("from-page-own")["task"] == "My own words.", "one saved with a task of its own keeps it")
print("RESULT:", f"FAIL {len(FAILED)}" if FAILED else "PASS"); [print("  FAILED", f) for f in FAILED]
