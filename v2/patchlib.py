"""Helpers of the v2 patch scripts: every change of a text is made by exact replacement (it fails if the text is not there exactly once) and is
written, before and after, into v2/texts_<stage>.md, so that the operator can read every text that changed."""
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
LOG = []
def sub(f, old, new, why, count=1):
    p = ROOT / f; s = p.read_text()
    assert s.count(old) == count, (f, s.count(old), old[:90])
    p.write_text(s.replace(old, new)); LOG.append((f, why, old, new))
def done(stage, title):
    out = [f"# {title}\n", "Every text changed in this stage, before and after (exact). `why` names the item of the audit or of the plan.\n"]
    for f, why, old, new in LOG:
        out.append(f"\n## {why}\n\n`{f}`\n\nbefore:\n\n```\n{old}\n```\n\nafter:\n\n```\n{new}\n```\n")
    (ROOT / "v2" / f"texts_{stage}.md").write_text("".join(out)); print(f"{stage}: {len(LOG)} changes written to v2/texts_{stage}.md")
