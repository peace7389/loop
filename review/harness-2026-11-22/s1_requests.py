"""Stage 1, item 9 (the coherence audit, 2026-11-22): the arms "hypotheses" and "plain" answer at most 3 requests in a reply; the rest were dropped
silently (s048: 12 readings asked for were never run, the turn's text said "your last requests were answered"). The number is now one constant
(REQUESTS_MOST, LOOKS in the arm "supervised"), stated in the instructions, set in the answer format (maxItems), and a cut is noted.
Usage: s1_requests.py loop LOOP_PY | prompt PROMPT_TXT"""
import sys
from pathlib import Path
kind, p = sys.argv[1], Path(sys.argv[2]); s = p.read_text()
def rep(a, b, n=1):
    global s
    assert s.count(a) == n, (a[:90], s.count(a))
    s = s.replace(a, b)
if kind == "loop":
    rep('''LOOKS = 6   #''', '''REQUESTS_MOST = 3   # the arms "hypotheses" and "plain": the most requests answered in one reply (stated in prompt.txt; the answer format's maxItems; a cut is noted)
LOOKS = 6   #''')
    rep('''    schema, system = with_findings(schema), system + FINDINGS_TEXT[arm]   # findings, in every arm (2026-11-22)''',
        '''    schema, system = with_findings(schema), system + FINDINGS_TEXT[arm]   # findings, in every arm (2026-11-22)
    if isinstance(schema["properties"].get("requests"), dict):   # the most requests a reply may hold, in the answer format too (the coherence audit, 2026-11-22)
        schema["properties"]["requests"]["maxItems"] = LOOKS if arm == "supervised" else REQUESTS_MOST''')
    rep('''                rq = [] if mode not in (None, "free") else (parsed.get("requests") or [])[:LOOKS if arm == "supervised" else 3]''',
        '''                rq = [] if mode not in (None, "free") else (parsed.get("requests") or [])[:LOOKS if arm == "supervised" else REQUESTS_MOST]''')
    rep('''            for q in rq:  # each tool request and what came back are kept in the ledger''', '''            asked_for = [q for q in parsed.get("requests") or [] if isinstance(q, dict)]
            if len(asked_for) > len(rq):   # what was not answered, and why (the coherence audit, 2026-11-22: they were dropped silently)
                append(ledger, turn, "note", last, {"text": (f"requests are not answered in the last turns: {len(asked_for)} left unanswered" if mode not in (None, "free") else
                                                             f"only the first {len(rq)} requests of a reply are answered: {len(asked_for) - len(rq)} more were left unanswered ({', '.join(str(q.get('tool')) for q in asked_for[len(rq):])})")})
            for q in rq:  # each tool request and what came back are kept in the ledger''')
elif kind == "prompt":
    rep('''8. requests: if you need information to design the next step, ask for it through the tools described in the brief; the results''',
        '''8. requests: if you need information to design the next step, ask for it through the tools described in the brief, at most 3 in one reply; the results''')
p.write_text(s); print("patched", kind, p)
