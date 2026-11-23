"""The comparison arm "plain" (loop.py --arm plain; 2026-11-17, for the open question "does the hypothesis format
help at all?"): the same loop, brief, budget and final report without the hypothesis format.
  - its instructions are prompt.txt without the lines on hypotheses, decision rules and verdicts, and name none of
    them; every other paragraph is the ordinary one, word for word;
  - its answer format has no hypotheses, drop or verdicts, and an experiment only explores;
  - a scripted session in that arm: explore experiments run, the evidence is recorded, no hypothesis, check or verdict
    record exists, the final report (with limit and no_difference) is accepted and ends the session; session.json says
    which arm it was and holds the instructions it was given;
  - a session in the ordinary arm says nothing of an arm and gets prompt.txt in its short format (2026-11-22: the flag format "short",
    loop.short_prompt; test_short_format.py); an existing session keeps its arm.
    python3 -I test_arms.py SCRATCH_DIR [HARNESS_DIR]
SCRATCH_DIR is made new. Simulations are real ns-3 runs of 2 measured seconds."""
import json, os, shutil, subprocess, sys
from pathlib import Path
HERE, REAL = Path(__file__).resolve().parent, Path.home() / "project"
args = [a for a in sys.argv[1:] if not a.startswith("--")]
SCR, SRC = Path(args[0]).resolve(), Path(args[1]).resolve() if len(args) > 1 else REAL / "harness"
assert "scratch" in str(SCR)
P = SCR / "home/project"
shutil.rmtree(SCR, ignore_errors=True); (P / "sessions").mkdir(parents=True); (P / "checks").mkdir()
shutil.copytree(SRC, P / "harness", ignore=shutil.ignore_patterns("__pycache__", "loop.log")); shutil.copytree(REAL / "briefs", P / "briefs"); os.symlink(REAL / "ns-3.49", P / "ns-3.49")
ENV = {**os.environ, "HOME": str(SCR / "home")}
FAILED = []
def say(ok, text):
    print(f"  {'ok  ' if ok else 'FAIL'} {text}", flush=True)
    if not ok: FAILED.append(text[:50])
def session(sid, brief, answers, *flags):
    f = SCR / f"{sid}.answers.json"; f.write_text(json.dumps(answers))
    r = subprocess.run([sys.executable, "-I", str(HERE / "scripted.py"), str(f), "--brief", brief, "--session", sid, *flags], env=ENV, capture_output=True, text=True, timeout=1200)
    led = [json.loads(l) for l in (P / "sessions" / sid / "ledger.jsonl").read_text().splitlines() if l.strip()] if (P / "sessions" / sid / "ledger.jsonl").is_file() else []
    return led, (json.loads((P / "sessions" / sid / "session.json").read_text()) if (P / "sessions" / sid / "session.json").is_file() else {}), r
of = lambda led, ty: [r for r in led if r["type"] == ty]
KN = dict(udpRate="2Gbps", queuePkts=100, tcpVariant="TcpCubic", duration=2, seed=1)
def d(label, w, **over): return {"label": label, "params": {"weightUdp": w, **KN, **over}}
def plain(**k): return {"observations": "read", "experiment": None, "report": None, "requests": [], "budget_request": None, "done": False, **k}
REP = {"goal": "the larger UDP goodput", "recommendation": {"weightUdp": 0.7, **KN}, "expected": {"udp_goodput_bps": 685000000.0}, "no_difference": [], "limit": "UDP's part of the link: E1.",
       "explanation": "UDP's goodput follows its part of the link.", "holds_when": "as tested", "breaks_when": "other rates", "claims": [{"text": "A larger part gives UDP more.", "role": "supports", "evidence": ["E1"]}], "open_questions": []}
print("THE ARM WITHOUT THE HYPOTHESIS FORMAT")
os.environ["HOME"] = str(SCR / "home"); sys.path.insert(0, str(P / "harness"))
import loop
full = (P / "harness/prompt.txt").read_text(); text = loop.plain_prompt(full); paras, fparas = text.split("\n\n"), full.split("\n\n")
words = [w for w in ("hypothes", "decision rule", "decision_rule", "verdict", "HELD", "FAILED") if w in text]
same = [p for p in paras if p in fparas]
say(not words and len(paras) == len(fparas) and len(same) == len(paras) - 5 and all(x in text for x in ("The purpose of the work is to understand why", "Ask why before you ask which", "Tell a meaningful difference from a marginal one", "- limit:", "- no_difference:")),
    f"its instructions name no hypothesis, decision rule, verdict or check; they have the {len(paras)} paragraphs of prompt.txt, {len(same)} of them word for word and five reworded where they named those (the ledger's line, the list of the answer's parts, the refused part, asking why, meaningful against marginal); the purpose and the report's parts are all there")
fmt = loop.plain_format(loop.answer_format(json.loads((P / "harness/schema.json").read_text()), loop.tools.load_brief("two-hosts-open"))); ex = fmt["properties"]["experiment"]["anyOf"][0]
whole = loop.answer_format(json.loads((P / "harness/schema.json").read_text()), loop.tools.load_brief("two-hosts-open"))
say(list(fmt["properties"]) == ["observations", "experiment", "report", "requests", "budget_request", "done"] == fmt["required"] and ex["properties"]["kind"]["enum"] == ["explore"] and "tests" not in ex["properties"] and "decision_rules" not in ex["properties"]
    and fmt["properties"]["report"] == whole["properties"]["report"], f"its answer format: {list(fmt['properties'])}; an experiment only explores ({list(ex['properties'])}); the final report's format is the ordinary one")
led, meta, r = session("p1", "two-hosts-open", [plain(experiment={"kind": "explore", "question": "What does UDP get at two parts of the link?", "varied": ["weightUdp"], "control": "a", "runs": [d("a", 0.3), d("b", 0.7)]}),
                                                 plain(report=REP, done=True)], "--arm", "plain")
kinds = sorted({q["type"] for q in led})
say(r.returncode == 0 and len(of(led, "simulation")) == 3 and len(of(led, "evidence")) == 2 and not of(led, "hypothesis") and not of(led, "check") and not of(led, "verdict") and of(led, "experiment")[-1]["body"]["kind"] == "explore",
    f"a session in the arm: the baseline and an exploring experiment of two simulations ran, their evidence is recorded, and there is no hypothesis, check or verdict record (record types: {kinds})" + (f" {r.stderr[-600:]}" if r.returncode else ""))
say(len(of(led, "report")) == 1 and meta.get("how") == "done by the model" and meta.get("flags", {}).get("arm") == "plain" and meta.get("prompt") == text + getattr(loop, "FINDINGS_TEXT", {}).get("plain", "") and meta.get("report"),
    f"its final report is accepted and ends the session (“{meta.get('how')}”); session.json says the arm ({meta.get('flags', {}).get('arm')}) and holds the instructions it was given")
sent = json.loads((P / "sessions/p1/format_sent.json").read_text())
say("hypotheses" not in sent["properties"] and "verdicts" not in sent["properties"], "the format sent to the model server with its requests is the arm's")
led2, meta2, r2 = session("o1", "two-hosts-open", [plain(hypotheses=[], drop=[], verdicts=[])], )
SHORT = getattr(loop, "SHORT_FORMAT", True)   # the deployed harness keeps the short format off (2026-11-22)
say("arm" not in meta2.get("flags", {}) and (meta2["flags"].get("format") == "short") == SHORT and meta2.get("prompt") == (loop.short_prompt(full) if SHORT else full) + getattr(loop, "FINDINGS_TEXT", {}).get("hypotheses", ""),
    "a session in the ordinary arm records no arm; it is given prompt.txt (in the short format and recording it where SHORT_FORMAT is on, 2026-11-22)")
led3, meta3, r3 = session("p1x", "two-hosts-open", [plain()], "--arm", "plain", "--budget", "100")
say(r3.returncode != 0 and not (P / "sessions/p1x").exists(), "a start that cannot be made (a budget over the brief's limit) leaves no folder, in this arm too")
r4 = subprocess.run([sys.executable, "-I", str(HERE / "scripted.py"), str(SCR / "o1.answers.json"), "--session", "o1", "--arm", "plain"], env=ENV, capture_output=True, text=True, timeout=300)
say(r4.returncode != 0 and "works in the arm hypotheses, not plain" in r4.stderr, f"an existing session keeps its arm: asking for the other one is refused (“{r4.stderr.strip().splitlines()[-1][-80:] if r4.stderr.strip() else ''}”)")
print("RESULT:", f"FAIL {len(FAILED)}" if FAILED else "PASS"); [print("  FAILED", f) for f in FAILED]
