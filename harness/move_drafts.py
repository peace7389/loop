"""Operator tool, used once per session: move the text of the draft records out of a session's ledger.jsonl into
drafts.jsonl. Every other line of the ledger stays byte for byte as it was; a draft record keeps its id, turn, parent
and time, and its body becomes {chars, tokens, model, finish_reason}. Usage: move_drafts.py SESSION [SESSION ...]
It prints counts only, never text."""
import json, sys
from pathlib import Path

ROOT = Path.home() / "project/sessions"

def move(sid):
    led, out = ROOT / sid / "ledger.jsonl", ROOT / sid / "drafts.jsonl"
    lines, kept, texts = led.read_text().splitlines(), [], []
    for line in lines:
        r = json.loads(line) if line.strip() else None
        if not r or r.get("type") not in ("draft", "scratch") or not any(k in r["body"] for k in ("text", "reasoning")):
            kept.append(line)  # not a draft with text: the line is kept exactly
            continue
        b = r["body"]
        text = b.get("text") if b.get("text") is not None else b.get("reasoning") or ""
        texts.append({"id": r["id"], "turn": r["turn"], "text": text})
        r["body"] = {"chars": len(text), "tokens": b.get("tokens"), "model": b.get("model"), "finish_reason": b.get("finish_reason")}
        kept.append(json.dumps(r))
    if not texts:
        return print(f"{sid}: no draft text in the ledger; nothing moved")
    with out.open("a") as f:
        for t in texts:
            f.write(json.dumps(t) + "\n")
    led.write_text("\n".join(kept) + "\n")
    print(f"{sid}: {len(texts)} drafts moved to drafts.jsonl ({sum(len(t['text']) for t in texts):,} characters); ledger {len(lines)} lines before, {len(kept)} after")

if __name__ == "__main__":
    for sid in sys.argv[1:]:
        move(sid)
