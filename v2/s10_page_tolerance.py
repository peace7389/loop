"""v2, stage 10: found by the page checks on the final tree. The page worked out for itself which checks were decided by less than the tolerance,
by the rule the harness had before v2 (a side with a measured value was a result, whatever number of the rule stood with it). On a session of v2
it would have marked checks the harness did not mark and did not tell the researcher about (C5: only between two measured results). The page now
shows the harness's own mark: since 2026-11-15 a check's record holds it (within_tolerance). A session recorded before that has no such field,
and the page works it out as before, by the rule of that time. Sessions recorded so far read as they did."""
import sys; sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent))
from patchlib import sub, done
R = "viewer/evidence_read.js"
sub(R, """    const tol = EV.tolerance();
    return cmps.map(n => { if (n[2] === '==') return null;""",
    """    const tol = EV.tolerance();
    // v2: the harness's own mark. Since 2026-11-15 a check's record says which of its comparisons were decided by less than the tolerance, by the rule
    // of the harness that ran the session; the page shows that and works nothing out. A session recorded before has no such field: worked out below.
    const own = (((M.byId || {})[c.id] || {}).body || {}).within_tolerance, since = String((M.meta && M.meta.started) || (M.recs[0] || {}).ts || '') >= '2026-11-16';
    if (since) return (Array.isArray(own) ? own : []).filter(q => typeof q.percent === 'number').map(q => { const n = cmps.find(x => x[2] === q.op) || cmps[0]; return { a: q.left, b: q.right, op: q.op, pct: q.percent, unit: n ? EV.readUnit(n[1]) || EV.readUnit(n[3]) : '' }; });
    return cmps.map(n => { if (n[2] === '==') return null;""",
    "the page: a check decided by less than the tolerance is the harness's own mark (the record), not the page's reckoning")
done("stage10", "v2, stage 10: the page shows the harness's own mark of a check decided by less than the tolerance")
