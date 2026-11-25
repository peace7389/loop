# v2, stage 10: the page shows the harness's own mark of a check decided by less than the tolerance
Every text changed in this stage, before and after (exact). `why` names the item of the audit or of the plan.

## the page: a check decided by less than the tolerance is the harness's own mark (the record), not the page's reckoning

`viewer/evidence_read.js`

before:

```
    const tol = EV.tolerance();
    return cmps.map(n => { if (n[2] === '==') return null;
```

after:

```
    const tol = EV.tolerance();
    // v2: the harness's own mark. Since 2026-11-15 a check's record says which of its comparisons were decided by less than the tolerance, by the rule
    // of the harness that ran the session; the page shows that and works nothing out. A session recorded before has no such field: worked out below.
    const own = (((M.byId || {})[c.id] || {}).body || {}).within_tolerance, since = String((M.meta && M.meta.started) || (M.recs[0] || {}).ts || '') >= '2026-11-16';
    if (since) return (Array.isArray(own) ? own : []).filter(q => typeof q.percent === 'number').map(q => { const n = cmps.find(x => x[2] === q.op) || cmps[0]; return { a: q.left, b: q.right, op: q.op, pct: q.percent, unit: n ? EV.readUnit(n[1]) || EV.readUnit(n[3]) : '' }; });
    return cmps.map(n => { if (n[2] === '==') return null;
```
