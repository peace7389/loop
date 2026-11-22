"""Stage 1, item 7 (the coherence audit, 2026-11-22): an experiment's measurements are checked against what EACH of its designs records, on that
design's own network (they were checked against the brief's network: s048 t4, s050 t5 and t6 refused whole experiments that measured l1_q_tcp on a
scheduler; the other way round a measurement passed and then was never computed). A design whose change cannot be made is left to experiment_problem.
Usage: s1_measures.py LOOP_PY"""
import sys
from pathlib import Path
p = Path(sys.argv[1]); s = p.read_text()
def rep(a, b, n=1):
    global s
    assert s.count(a) == n, (a[:90], s.count(a))
    s = s.replace(a, b)
rep('''    series, fine = network.record_columns(brief["topology"]) if brief.get("topology") else TWO_HOSTS_COLUMNS
    outs, seen = tools.outputs(brief), set()''', '''    def cols_of(r):   # what one design records, on its own network (the coherence audit, 2026-11-22: the brief's network was used)
        if not brief.get("topology"):
            return TWO_HOSTS_COLUMNS
        e = edits_of(r, brief) if isinstance(r, dict) else []
        if e and structure_problem(e, brief):
            return None   # a change that cannot be made: experiment_problem refuses it with its own reason
        try:
            return network.record_columns(network.apply(brief["topology"], e) if e else brief["topology"])
        except (ValueError, KeyError, TypeError):
            return None
    designs = [(r.get("label"), cols_of(r)) for r in ex.get("runs") or [] if isinstance(r, dict)]
    designs = [(l, c) for l, c in designs if c] or [("the brief's network", network.record_columns(brief["topology"]) if brief.get("topology") else TWO_HOSTS_COLUMNS)]
    series, fine = designs[0][1]
    outs, seen = tools.outputs(brief), set()
    for r in ex.get("runs") or []:   # the names of the outputs of every design's network, which a measurement may not take
        if isinstance(r, dict) and edits_of(r, brief) and not structure_problem(edits_of(r, brief), brief):
            try:
                outs = {**outs, **network.outputs(network.apply(brief["topology"], edits_of(r, brief)))}
            except (ValueError, KeyError, TypeError):
                pass''')
rep('''        if not used or not (used <= set(series) or used <= set(fine)):
            return (f"measurement {n}: of must be a column a simulation records, or arithmetic over columns of one record. The series (every 0.1 s): {', '.join(series)}. "
                    f"The probe (every {tools.PROBE_EVERY} s; it only listens): {', '.join(fine)}")''',
    '''        lacking = [(l, c) for l, c in designs if not used or not (used <= set(c[0]) or used <= set(c[1]))]
        if lacking:
            l, (series, fine) = lacking[0]
            return (f"measurement {n}: of must be a column a simulation records, or arithmetic over columns of one record" + (f", in every design: design {l} does not record it" if len(designs) > 1 and len(lacking) < len(designs) else "")
                    + f". What {l if len(designs) > 1 or l != designs[0][0] else 'a simulation'} records: the series (every 0.1 s): {', '.join(series)}. "
                    f"The probe (every {tools.PROBE_EVERY} s; it only listens): {', '.join(fine)}")''')
p.write_text(s); print("patched", p)
