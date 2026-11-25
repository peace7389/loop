"""v2, stage 7: what a fairness audit needs. No text an agent reads is changed.
  - the instructions and the answer format of a session are built in one function (loop.built_texts), which main calls and which the text audit
    (harness/text_audit.py) calls to write the texts out without a session; the lines are those main had, in the same order;
  - session_figures.fairness_figures (chain refusals, cannot tell, approvals by round, is the answer stated in turn 1) was added beside this script."""
import sys; sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent))
from patchlib import sub, done, ROOT
L = "harness/loop.py"
s = (ROOT / L).read_text()
a = s.index('    if arm == "plain":\n        schema, system = plain_format(schema), plain_prompt(system)\n')
end = '        schema["properties"]["requests"]["maxItems"] = LOOKS if arm == "supervised" else REQUESTS_MOST\n'
b = s.index(end, a) + len(end)
old = s[a:b]
lines = old.split("\n")
comp = [l for l in lines if l.startswith("    competitors = ")]; on = [l for l in lines if l.strip() == 'COMP["on"] = competitors']; short = [l for l in lines if l.startswith("    short = ")]; asks = [l for l in lines if l.startswith("    asks_budget = ")]
note = [l for l in lines if l.startswith("    # the short format of the arm")]
assert len(comp) == len(on) == len(short) == len(asks) == len(note) == 1, (len(comp), len(on), len(short), len(asks), len(note))
body = [l for l in lines if l not in (comp[0], on[0], short[0], asks[0], note[0])]
assert body[0] == '    if arm == "plain":' and body[-1] == ""
new_main = "\n".join([comp[0], on[0], note[0], short[0], asks[0], "    schema, system = built_texts(schema, system, brief, arm, competitors, short)   # the instructions and the format, as every text audit reads them too", ""])
func = ('def built_texts(schema, system, brief, arm, competitors, short):\n'
        '    """The instructions and the answer format of a session as the loop sends them: main calls it, and harness/text_audit.py to write the texts out\n'
        '    without a session. schema: answer_format(schema.json, the brief); system: prompt.txt. COMP["on"] is set by the caller (competitors)."""\n'
        + "\n".join(body[:-1]) + "\n    return schema, system\n\n\n")
sub(L, old, new_main, "no text changed: main builds the instructions and the format through loop.built_texts")
sub(L, "def main():\n    ap = argparse.ArgumentParser()\n", func + "def main():\n    ap = argparse.ArgumentParser()\n", "no text changed: the lines main had, as a function of their own (same order)")
done("stage7", "v2, stage 7: the instructions and the format built in one function (no text changed)")
