"""After the deploy, part 10 (s057, 2026-11-23 04:50): the task the harness writes into a brief said "You may change 2 settings (l1.queue.length,
tcp.type); every other setting is fixed." on the brief after_fix, whose network the AI may change (a scheduler instead of the FIFO is the change the
brief was made for). Both agents read it: the researcher's instructions say a few paragraphs later that the structure may change too, the
supervisor's said nothing of it until part 5, and in s056 it called the scheduler "outside the permitted settings". (The researcher proposed the
scheduler all the same in s055, s056 and s057; the sentence contradicted its instructions.) On a brief whose network may change the sentence now
says so; the page writes the same sentence, and still knows the earlier one as the harness's (sessions before keep it).
python3 -I p10_task.py tools TOOLS_PY | viewer VIEWER_DIR"""
import sys
from pathlib import Path
what, f = sys.argv[1], Path(sys.argv[2])
CLAUSE = " and the structure of the network (its hosts, links, flows and queues, within the brief's limits)"

def rep(s, a, b, n=1):
    assert s.count(a) == n, (a[:90], s.count(a))
    return s.replace(a, b)

if what == "tools":
    s = f.read_text()
    s = rep(s, '''    may = f"You may change {len(knobs)} setting{'' if len(knobs) == 1 else 's'} ({', '.join(knobs)}); every other setting is fixed."''',
            '''    net = bool(b.get("topology") and (b.get("structure") or {}).get("may_change"))   # a network the AI may change (part 10: three sessions on after_fix kept to the two settings)
    may = (f"You may change {len(knobs)} setting{'' if len(knobs) == 1 else 's'} ({', '.join(knobs)})"
           + (''' + repr(CLAUSE) + ''' if net else "") + "; every other setting is fixed.")''')
    f.write_text(s)
    print("patched", f)
elif what == "viewer":
    p = f / "evidence_setting.js"; s = p.read_text()
    s = rep(s, '''  taskText(b) { const kn = Object.keys((b && b.knobs) || {}), g = (b && b.goal) || {}, may = `You may change ${kn.length} setting${kn.length === 1 ? '' : 's'} (${kn.join(', ')}); every other setting is fixed.`;''',
            '''  // before: the sentence as it was written until 2026-11-23, without the network's structure (the sessions before keep it, and it is the harness's too)
  taskText(b, before) { const kn = Object.keys((b && b.knobs) || {}), g = (b && b.goal) || {}, net = !before && !!(b && b.topology && b.structure && b.structure.may_change), may = `You may change ${kn.length} setting${kn.length === 1 ? '' : 's'} (${kn.join(', ')})${net ? "''' + CLAUSE + '''" : ''}; every other setting is fixed.`;''')
    p.write_text(s)
    p = f / "evidence_cards.js"; s = p.read_text()
    s = rep(s, "b.task && b.task === EV.taskText(b) ?", "b.task && (b.task === EV.taskText(b) || b.task === EV.taskText(b, true)) ?", 2)
    p.write_text(s)
    print("patched", f)
