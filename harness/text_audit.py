"""Operator tool: the texts the agents are sent, written out and tested for pointers to an answer (v2, stage 7). Usage:
    text_audit.py BRIEF [BRIEF ...] [--out FILE]     the texts as the loop builds them for a new session on each brief, in each arm
    text_audit.py --session SESSION [--out FILE]     the texts the agents of a session were in fact sent (its calls.jsonl)

A text points to an answer when it names a value, an object or an order that a researcher who only reads it would try first. The tests are
mechanical and find candidates; whether a candidate is a pointer is the auditor's judgement (checks/fairness/CHECKLIST.md, item 2):
  examples    every sentence with "for example", "e.g." or "such as"; marked where the example is a rate, a value one of the brief's settings can
              take, a kind of queue or an object of the brief's network (an example of an id, such as "Y3", is listed and not marked);
  preference  every sentence with a word of preference or expectation (usually, typically, best, better, prefer, most likely, start with, first try);
  order       every list of choices the texts state (a sentence that names three or more kinds of queue; each setting of the brief that has
              choices): is it in alphabetical order?
  depth       the kinds of queue, each with the number of words it is described in: one described at more than twice the middle length is marked,
              and so is a kind described in a sentence of its own, apart from the list;
  left        a placeholder left unfilled (<<NAME>> or {name});
  sizes       the characters of every text.
In the texts of a session only what the harness wrote is tested: the instructions of each agent, and of the texts of each turn the lines that are
not records of the ledger. What the model wrote (its reasoning, its answers) is never read here.
Operator only: it prints a report (Markdown) or writes it to --out; no agent is shown it."""
import argparse, json, re, statistics, sys
from pathlib import Path
import network, tools

EXAMPLE = re.compile(r"\bfor example\b|\be\.g\.|\bsuch as\b", re.I)
PREFER = re.compile(r"\b(usually|typically|often|best|better|prefer(?:s|red|ably)?|most likely|start with|first try|try first|recommended)\b", re.I)
RATE = re.compile(r"\b\d+(?:\.\d+)?\s?[kMG]bps\b")
LEFT = re.compile(r"<<[A-Z_]+>>|\{[a-z_.]+\}")
KINDS = ("codel", "fifo", "fqcodel", "pfifofast", "pie", "red", "scheduler")


def sentences(text):
    """The sentences of a text, a list item counted as one (split after a full stop, a question mark, or at a new line)."""
    return [s.strip() for s in re.split(r"(?<=[.?!])\s+|\n+", text) if s.strip()]


def tokens_of(brief):
    """What a pointer could name in this brief: the values its settings can take that are words, the kinds of queue, the objects of its network."""
    vals = {str(c) for k in (brief.get("knobs") or {}).values() for c in k.get("choices") or []}
    vals |= {v[3:] for v in vals if v.startswith("Tcp")}
    t = brief.get("topology") or {}
    objs = {str(o["id"]) for part in ("hosts", "links", "flows") for o in t.get(part) or [] if len(str(o.get("id", ""))) > 1}
    return vals, set(KINDS), objs


def test_text(name, text, brief, out, harness_lines_only=False):
    """The candidates of one text, appended to out as (test, marked, where, sentence)."""
    if harness_lines_only:   # of a turn's text: not the ledger's records, which hold the model's own words
        text = "\n".join(l for l in text.split("\n") if not re.match(r"\s*\[[A-Za-z]+\d*\]", l))
    vals, kinds, objs = tokens_of(brief) if brief else (set(), set(KINDS), set())
    word = lambda w, s: re.search(r"(?<![A-Za-z0-9_])" + re.escape(w) + r"(?![A-Za-z0-9_])", s) is not None
    for s in sentences(text):
        if EXAMPLE.search(s):
            tail = s[EXAMPLE.search(s).start():]
            hit = [m.group(0) for m in RATE.finditer(tail)] + sorted(v for v in vals if word(v, tail)) + sorted(k for k in kinds if word(k, tail)) + sorted(o for o in objs if word(o, tail))
            out.append(("examples", bool(hit), name, s if not hit else f"{s}  <- names: {', '.join(hit)}"))
        if PREFER.search(s):
            out.append(("preference", False, name, f"{s}  <- {', '.join(sorted({m.group(0).lower() for m in PREFER.finditer(s)}))}"))
        for m in LEFT.finditer(s):
            out.append(("left", True, name, f"{m.group(0)} in: {s[:160]}"))
    # the kinds of queue, wherever a sentence lists three or more of them: their order; and how long each is described
    for s in sentences(text):
        first = sorted((m.start(), k) for k in KINDS for m in [re.search(r"(?<![A-Za-z0-9_])" + k + r"(?![A-Za-z0-9_])", s)] if m)
        names = [k for _, k in first]
        if len(names) >= 3:
            out.append(("order", names != sorted(names), name, f"the kinds of queue, in the order the sentence names them: {', '.join(names)}"))
    apart = [s for s in sentences(text) if re.match(r"(?:A|An|The) (" + "|".join(KINDS) + r")\b", s)]
    for s in apart:
        out.append(("depth", True, name, f"a kind of queue described in a sentence of its own: {s[:200]}"))
    m = re.search(r"The kinds[^:]*:(.*?)(?:\n|$)", text)
    if m:
        parts = [(q.group(1), len(q.group(2).split())) for q in re.finditer(r"(?:^|;)\s*([a-z]+):\s*([^;]*)", m.group(1).strip().rstrip("."))]
        if parts:
            mid = statistics.median(n for _, n in parts)
            long = [f"{k} ({n} words)" for k, n in parts if n > 2 * mid]
            out.append(("depth", bool(long), name, "words for each kind: " + ", ".join(f"{k} {n}" for k, n in parts) + (f"  <- more than twice the middle length ({mid:g}): {', '.join(long)}" if long else "")))


def test_brief(brief, out):
    for k, spec in (brief.get("knobs") or {}).items():
        ch = spec.get("choices")
        if ch:
            out.append(("order", [str(c) for c in ch] != sorted(str(c) for c in ch), f"brief {brief['id']}", f"the choices of {k}, as the brief lists them: {', '.join(map(str, ch))} (default {spec.get('default')})"))


def built(brief_id):
    """The texts of a new session on this brief in each arm, as loop.main builds them (loop.built_texts): {arm: system text}, and the brief's own texts."""
    import loop
    H = tools.HARNESS
    texts = {}
    for arm, competitors in (("supervised", True), ("hypotheses", False), ("plain", False)):
        brief = {**tools.load_brief(brief_id), **tools.MANIFEST}
        if brief.get("topology"):
            brief["outputs"] = network.outputs(brief["topology"]); brief["tools"] = network.tools_told(brief["tools"])
        loop.COMP["on"] = competitors
        schema = loop.answer_format(json.loads((H / "schema.json").read_text()), brief)
        short = loop.SHORT_FORMAT and arm == "hypotheses"
        try:
            schema, system = loop.built_texts(schema, (H / "prompt.txt").read_text(), brief, arm, competitors, short)
        except Exception as e:   # an arm this brief cannot run in (the loop would stop at its start with the same words)
            texts[f"{arm}: the instructions"] = None; texts[f"{arm}: NOT BUILT"] = str(e)
            continue
        texts[f"{arm}: the instructions"] = system
        descr = []
        def walk(node, path=""):
            if isinstance(node, dict):
                if isinstance(node.get("description"), str): descr.append(f"{path}: {node['description']}")
                for k, v in node.items(): walk(v, f"{path}.{k}" if path else k)
            elif isinstance(node, list):
                for v in node: walk(v, path)
        walk(schema)
        texts[f"{arm}: the answer format's descriptions"] = "\n".join(descr)
    loop.COMP["on"] = False
    texts["the supervisor: its instructions"] = loop.SUPERVISOR
    b = tools.load_brief(brief_id)
    texts["the brief: its task"] = b["task"]; texts["the brief: its description"] = b["description"]
    texts["the brief: the meaning of its settings"] = "\n".join(f"{k}: {v.get('meaning', '')}" for k, v in (b.get("knobs") or {}).items())
    return b, texts


def sent(sid):
    """The texts a session's agents were sent: each distinct system text by agent and step, and each turn's text (calls.jsonl; only what was given)."""
    D = tools.SESSIONS / sid
    brief = json.loads((D / "session.json").read_text()).get("given") or {}
    systems, users = {}, []
    for l in (D / "calls.jsonl").read_text().splitlines():
        if not l.strip(): continue
        r = json.loads(l)
        step = r.get("step"); step = (step.get("step") if isinstance(step, dict) else step) or ""
        systems.setdefault((r.get("agent"), r.get("system") or ""), []).append(f"turn {r.get('turn')} {step}".strip())
        users.append((f"{r.get('agent')}, call {r.get('n')} (turn {r.get('turn')}{', ' + str(step) if step else ''}): the text of the turn", r.get("user") or ""))
    texts = {}
    for i, ((agent, system), where) in enumerate(systems.items(), 1):
        texts[f"{agent}: instructions {i} ({len(where)} call{'s' if len(where) != 1 else ''}: {where[0]}{' ...' if len(where) > 1 else ''})"] = system
    return brief, texts, users


def report(title, brief, texts, users, lines):
    out = []
    lines.append(f"\n## {title}\n")
    lines.append("| Text | Characters |\n|---|---|")
    for name, t in texts.items():
        if t is None: continue
        if name.endswith("NOT BUILT"):
            lines.append(f"| {name} | {t} |"); continue
        lines.append(f"| {name} | {len(t):,} |")
        test_text(name, t, brief, out)
    if users:
        lines.append(f"| the texts of the turns ({len(users)} calls) | {sum(len(u) for _, u in users):,} in all, the longest {max(len(u) for _, u in users):,} |")
        seen = set()
        for name, u in users:
            got = []; test_text(name, u, brief, got, harness_lines_only=True)
            for g in got:
                if g[0] in ("examples", "preference", "left") and g[3] not in seen:
                    seen.add(g[3]); out.append(g)
    if brief: test_brief(brief, out)
    for test, says in (("examples", "Examples"), ("preference", "Words of preference or expectation"), ("order", "Lists of choices and their order"), ("depth", "How long each kind of queue is described"), ("left", "Placeholders left unfilled")):
        rows = [o for o in out if o[0] == test]
        marked = sum(1 for o in rows if o[1])
        lines.append(f"\n**{says}**: {len(rows)} found, {marked} marked.\n")
        for _, mark, where, s in rows:
            lines.append(f"- {'**MARKED** ' if mark else ''}[{where}] {s}")
    return sum(1 for o in out if o[1])


def main():
    ap = argparse.ArgumentParser(description="Write out the texts the agents are sent and test them for pointers to an answer.")
    ap.add_argument("briefs", nargs="*", help="brief ids: the texts as built for a new session on each")
    ap.add_argument("--session", action="append", default=[], help="a session: the texts its agents were sent (repeatable)")
    ap.add_argument("--out", help="write the report (Markdown) to this file instead of printing it")
    a = ap.parse_args()
    if not a.briefs and not a.session:
        ap.error("name a brief or --session")
    lines = ["# The texts the agents are sent: what the mechanical tests find\n", "Made by `harness/text_audit.py`. A marked line is a candidate, to be judged by reading it; an unmarked one is listed so that it can be read."]
    marked = 0
    for bid in a.briefs:
        b, texts = built(bid)
        marked += report(f"Brief {bid}: the texts as built for a new session", b, texts, None, lines)
    for sid in a.session:
        if not (tools.SESSIONS / sid / "calls.jsonl").is_file():
            ap.error(f"session {sid} has no calls.jsonl (written since 2026-11-22)")
        b, texts, users = sent(sid)
        marked += report(f"Session {sid} (brief {b.get('id')}): the texts as sent", b, texts, users, lines)
    lines.append(f"\nMarked in all: {marked}.")
    text = "\n".join(lines) + "\n"
    if a.out:
        Path(a.out).write_text(text); print(f"{a.out}: {marked} marked")
    else:
        sys.stdout.write(text)


if __name__ == "__main__":
    main()
