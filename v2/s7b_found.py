"""v2, stage 7b: two things the text audit (harness/text_audit.py) found in the texts of v2 itself.
  - the answer format's line on the records of a finding named "checks, verdicts" in every arm: the arm "plain" is never told of either, and the
    arm "supervised" has rulings; each arm's line now names what that arm's own text on findings names;
  - the briefs of v2 listed the TCP types with the default first; a list of choices is in alphabetical order, as the kinds of queue are."""
import sys, json; sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent))
from patchlib import sub, done, ROOT
L = "harness/loop.py"
sub(L, '''    schema, system = with_findings(schema), system + FINDINGS_TEXT[arm]   # findings, in every arm (2026-11-22)
    stated_rules(system, arm)''',
    '''    schema, system = with_findings(schema), system + FINDINGS_TEXT[arm]   # findings, in every arm (2026-11-22)
    if arm in FINDING_ABOUT:   # v2: the format's line on a finding's records names what this arm has, as the arm's own text on findings does
        item = json.loads(json.dumps(schema["properties"]["findings"]["items"]))
        item["properties"]["about"]["description"] = FINDING_ABOUT[arm]
        schema["properties"]["findings"] = {**schema["properties"]["findings"], "items": item}
    stated_rules(system, arm)''', "the answer format's line on a finding's records, by arm (found by the text audit)")
sub(L, '''def built_texts(schema, system, brief, arm, competitors, short):''',
    '''FINDING_ABOUT = {"plain": "the ids of the records it rests on: evidence tables, simulations or readings (for example E2, T7)",
                 "supervised": "the ids of the records it rests on: evidence tables, simulations, checks, rulings or readings (for example E2, C3, T7)"}


def built_texts(schema, system, brief, arm, competitors, short):''', "the two lines (the arm hypotheses keeps the line it had)")
for b in ("three-hosts-2", "three-hosts-link-2", "three-hosts-moves"):
    p = ROOT / "briefs" / f"{b}.json"; d = json.loads(p.read_text()); old = p.read_text()
    for k, spec in d["knobs"].items():
        if spec.get("choices"):
            spec["choices"] = sorted(spec["choices"])
    new = json.dumps(d, indent=1) + "\n" if old.startswith("{\n") else json.dumps(d) + "\n"
    a = json.dumps(json.loads(old)["knobs"]["fa.type"]["choices"]); z = json.dumps(d["knobs"]["fa.type"]["choices"])
    p.write_text(new)
    from patchlib import LOG
    LOG.append((f"briefs/{b}.json", "the choices of fa.type in alphabetical order (found by the text audit; the default stays TcpCubic)", a, z))
done("stage7b", "v2, stage 7b: what the text audit found in v2's own texts")
