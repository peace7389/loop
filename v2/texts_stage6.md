# v2, stage 6: the page (the box Follows, cannot tell, a refuted guess as the harness counts it, the confirmation of the answer)
Every text changed in this stage, before and after (exact). `why` names the item of the audit or of the plan.

## the page: the line of a review's or a ruling's questions (Follows first, cannot tell)

`viewer/evidence_notebook.js`

before:

```
  // the three questions of a review round or a ruling (honest, consistent, correct) on one line: each with pass or fail, its reason in its hover box.
  // get(q) -> [box, why]
  threeQ(get) { const e = EV.e;
    return ['honest', 'consistent', 'correct'].map(q => { const [box, why] = get(q) || []; return box ? `<span class="tq" data-q="${q}" title="${e(why || '')}">${q[0].toUpperCase() + q.slice(1)} <b class="${box === 'pass' ? '' : 'warnc'}">${e(box)}</b></span>` : ''; }).filter(Boolean).join(' · '); },
```

after:

```
  // the questions of a review round or a ruling on one line: each with pass, fail or cannot tell, its reason in its hover box. Follows (v2: does the
  // hypothesis follow from its guess) stands first where the record has it; a record made before that box existed shows the three it has.
  // get(q) -> [box, why]
  QS: ['follows', 'honest', 'consistent', 'correct'],
  CANNOT_SAYS: 'cannot tell: the supervisor could not answer this from what it was shown. At a review the test is sent back as if the box had failed; at a ruling the result is inconclusive.',
  boxCls(box) { return box === 'pass' ? '' : box === 'cannot tell' ? 'ctc' : 'warnc'; },
  boxWhy(box, why) { return (why || '') + (box === 'cannot tell' ? (why ? ' · ' : '') + EV.CANNOT_SAYS : ''); },
  threeQ(get) { const e = EV.e;
    return EV.QS.map(q => { const [box, why] = get(q) || []; return box ? `<span class="tq" data-q="${q}" data-box="${e(box)}" title="${e(EV.boxWhy(box, why))}">${q[0].toUpperCase() + q.slice(1)} <b class="${EV.boxCls(box)}">${e(box)}</b></span>` : ''; }).filter(Boolean).join(' · '); },
  // v2: the tested guess is not refuted through a hypothesis the review did not find to follow from it (loop.guess_refutations); a ruling recorded
  // before the box Follows existed has no such answer and counts as before. R: a ruling's body
  fitSpared(R, y) { const h = (EV.M.hyps || []).find(q => q.id === R.for); return !!h && h.from_why === y && R.follows != null && R.follows !== 'pass'; },
```

## the page: the same line in a notebook card's review rounds

`viewer/evidence_notebook.js`

before:

```
${r.honest ? `<div class="sm sup-q">${['honest', 'consistent', 'correct'].map(q => `<span title="${e(r[q + '_why'] || '')}">${q[0].toUpperCase() + q.slice(1)} <b class="${r[q] === 'pass' ? '' : 'warnc'}">${e(r[q])}</b></span>`).join(' · ')}
```

after:

```
${r.honest ? `<div class="sm sup-q">${EV.QS.filter(q => r[q]).map(q => `<span data-q="${q}" data-box="${e(r[q])}" title="${e(EV.boxWhy(r[q], r[q + '_why']))}">${q[0].toUpperCase() + q.slice(1)} <b class="${EV.boxCls(r[q])}">${e(r[q])}</b></span>`).join(' · ')}
```

## the page: the look of a box answered cannot tell (neither pass nor fail)

`viewer/index.html`

before:

```
.ev .warnc { color: var(--warning); font-weight: 700; }
```

after:

```
.ev .warnc { color: var(--warning); font-weight: 700; } .ev .ctc { color: var(--text-secondary); font-weight: 700; font-style: italic; }
```

## the page: a guess refuted by a ruling, by the rule of loop.guess_refutations (item 4)

`viewer/evidence_notebook.js`

before:

```
if (!out && v && v.body.fair && !v.body.fits_contradicted && (v.body.fits || {})[y] === 'does not fit') out = { v, how: 'fits' }; });
```

after:

```
if (!out && v && v.body.fair && !v.body.fits_contradicted && (v.body.fits || {})[y] === 'does not fit' && !EV.fitSpared(v.body, y)) out = { v, how: 'fits', own: v.body.follows == null ? null : h.from_why === y }; });
```

## the page: the refuted guess keeps how it was refuted

`viewer/evidence_notebook.js`

before:

```
if (g) now = { worth: 'refuted', by: g.v.id, turn: g.v.turn, ruling: g.how }; }
```

after:

```
if (g) now = { worth: 'refuted', by: g.v.id, turn: g.v.turn, ruling: g.how, own: g.own }; }
```

## the page: the sentence of a refuted guess says how (as the harness's mark does since stage 2d)

`viewer/evidence_notebook.js`

before:

```
const how = now.ruling === 'fits' ? `refuted by the ruling ${now.by} in turn ${now.turn}: a fair test's result did not fit it` :
```

after:

```
const how = now.ruling === 'fits' ? `refuted by the ruling ${now.by} in turn ${now.turn}: ${now.own === true ? 'a fair test of a hypothesis that follows from it gave a result that does not fit it' : now.own === false ? 'it competed for the result of a fair test, and the result does not fit it' : "a fair test's result did not fit it"}` :
```

## the page: what a ruling's result means for a guess (cannot tell; a hypothesis that did not follow)

`viewer/evidence_notebook.js`

before:

```
    return ys.map(y => `<p data-fit="${e(y)}" data-fits="${f[y] === 'fits' ? 'yes' : 'no'}">${EV.whyLink(y)} ${f[y] === 'fits' ? 'fits the result' : applied && gone(y) ?
```

after:

```
    return ys.map(y => `<p data-fit="${e(y)}" data-fits="${f[y] === 'fits' ? 'yes' : f[y] === 'cannot tell' ? 'cannot tell' : 'no'}">${EV.whyLink(y)} ${f[y] === 'fits' ? 'fits the result' : f[y] === 'cannot tell' ? '<b class="ctc">cannot tell</b> <span class="sm">· the supervisor could not say whether the result fits it, so it is not refuted by this ruling</span>' : applied && EV.fitSpared(R, y) ? 'does not fit the result <span class="sm">· its hypothesis was not found to follow from it (the box Follows of the review), so the guess is not refuted by this result</span>' : applied && gone(y) ?
```

## the page: the step of a ruling names a guess as refuted by the same rule

`viewer/evidence_test.js`

before:

```
Object.keys(b.fits || {}).filter(y => b.fits[y] === 'does not fit' && !(w => w && EV.whyNow(w).worth === 'revised')((M.whyById || {})[y]))
```

after:

```
Object.keys(b.fits || {}).filter(y => b.fits[y] === 'does not fit' && !EV.fitSpared(b, y) && !(w => w && EV.whyNow(w).worth === 'revised')((M.whyById || {})[y]))
```

## control.py: a session's row follows its confirmation file

`harness/control.py`

before:

```
        led, idx, score, review = d / "ledger.jsonl", d / "runs/index.json", CHECKS / "scores" / f"{d.name}.json", CHECKS / "reviews" / f"{d.name}.json"
        sig = tuple(p.stat().st_mtime if p.exists() else 0 for p in (led, idx, d / "session.json", score, review))
```

after:

```
        led, idx, score, review = d / "ledger.jsonl", d / "runs/index.json", CHECKS / "scores" / f"{d.name}.json", CHECKS / "reviews" / f"{d.name}.json"
        confirm = CHECKS / "confirm" / f"{d.name}.json"   # v2: the answer measured again by harness/confirm.py (operator only)
        sig = tuple(p.stat().st_mtime if p.exists() else 0 for p in (led, idx, d / "session.json", score, review, confirm))
```

## control.py: a session's row says whether its answer was confirmed

`harness/control.py`

before:

```
                "review": {"n": len(marks), "ticked": sorted(k for k, m in marks.items() if m.get("tick") and k != "signoff"),
```

after:

```
                "confirm": confirm.is_file(),
                "review": {"n": len(marks), "ticked": sorted(k for k, m in marks.items() if m.get("tick") and k != "signoff"),
```

## export_session.py: an exported session carries no operator file, so no confirmation

`harness/export_session.py`

before:

```
"policy_hidden": False, "score": None, "review": {"n": 0, "ticked": [], "signed": None}}
```

after:

```
"policy_hidden": False, "score": None, "confirm": False, "review": {"n": 0, "ticked": [], "signed": None}}
```

## the page: a session is read again when its confirmation appears

`viewer/evidence.js`

before:

```
const base = `../sessions/${S.sid}/`, sig = JSON.stringify([S.sid, row.records, row.running, row.how, S.view, row.score, row.policy]);
```

after:

```
const base = `../sessions/${S.sid}/`, sig = JSON.stringify([S.sid, row.records, row.running, row.how, S.view, row.score, row.policy, row.confirm]);
```

## the page: the confirmation file is read with the session

`viewer/evidence.js`

before:

```
    const [led, meta, rep, idx, score, marks] = await Promise.all([EV.liveGet(base + 'ledger.jsonl'), EV.json(base + 'session.json'), EV.json(base + 'report.json'), EV.get(base + 'runs/index.json'),
      row.score ? EV.json(`../checks/scores/${S.sid}.json`) : null, row.review && row.review.n ? EV.json(`../checks/reviews/${S.sid}.json`) : null]);
```

after:

```
    const [led, meta, rep, idx, score, marks, confirm] = await Promise.all([EV.liveGet(base + 'ledger.jsonl'), EV.json(base + 'session.json'), EV.json(base + 'report.json'), EV.get(base + 'runs/index.json'),
      row.score ? EV.json(`../checks/scores/${S.sid}.json`) : null, row.review && row.review.n ? EV.json(`../checks/reviews/${S.sid}.json`) : null, row.confirm ? EV.json(`../checks/confirm/${S.sid}.json`) : null]);
```

## the page: the confirmation file is kept with the session's files

`viewer/evidence.js`

before:

```
    EV.files = { row, score, index: EV_DATA.lines(idx),
```

after:

```
    EV.files = { row, score, confirm, index: EV_DATA.lines(idx),
```

## the page: the confirmation of the answer, as a block of its own

`viewer/evidence_notebook.js`

before:

```
  // v2: the tested guess is not refuted through a hypothesis
```

after:

```
  // v2: the answer measured again by the operator's tool (harness/confirm.py: three seeds at five times the measured time), under the recommended
  // configuration of the final report. Not during the replay before its last step: the confirmation was made after the session ended.
  confirmBlock() { const c = (EV.files || {}).confirm, e = EV.e; if (!c || !c.target || EV.s.step != null) return '';
    const g = c.goal || {}, runs = c.runs || [], ok = runs.filter(r => !r.error), n = ok.length, own = (c.the_session_measured || []).filter(q => !q.returned && q.target != null).map(q => q.target);
    const conds = (g.conditions || []).map((t, i) => { const held = ok.filter(r => (r.conditions[i] || {}).holds).length; return `<span class="cf-c" data-held="${held}" data-of="${n}" title="${e(ok.map(r => `seed ${r.seed}: ${(r.conditions[i] || {}).with_numbers} ${(r.conditions[i] || {}).holds ? 'holds' : 'does not hold'}`).join(' · '))}"><code>${e(t)}</code> ${held === n ? `holds in all ${n}` : `<b class="warnc">holds in ${held} of ${n}</b>`}</span>`; }).join(' · ');
    return `<div class="cf noprint" id="rp-confirm" data-by="operator" data-all="${c.conditions_hold_in_all ? 1 : 0}"><p class="sm"><i class="sw"></i> <b>Measured again by the operator, apart from the session</b>: ${n} simulation${n === 1 ? '' : 's'} of this answer (seed${n === 1 ? '' : 's'} ${e(ok.map(r => r.seed).join(', '))}), ${e(c.how.seconds)} s measured each; the session measured ${e(c.how.the_session_measured_over)} s with one seed.</p>
      <p class="sm" data-exact="1">${EV.label(g.target)}: <b>${EV.v4(g.target, c.target.mean)}</b>${c.target.smallest !== c.target.largest ? ` (${EV.v4(g.target, c.target.smallest)} to ${EV.v4(g.target, c.target.largest)})` : ' in each'}${own.length ? ` · in the session: ${own.map(v => EV.v4(g.target, v)).join(', ')}` : ' · the session did not simulate this answer itself'}${conds ? `<br>${conds}` : ''}</p></div>`; },
  // v2: the tested guess is not refuted through a hypothesis
```

## the page: the confirmation under the recommended configuration (the final report beside the page)

`viewer/evidence_more.js`

before:

```
blk('adjust', 'Recommended configuration', cfg),
```

after:

```
blk('adjust', 'Recommended configuration', cfg + EV.confirmBlock()),
```

## the page: the confirmation under the recommended configuration (the report on the page)

`viewer/evidence_page.js`

before:

```
${blk(nx(), 'adjust', 'Recommended configuration', cfg)}
```

after:

```
${blk(nx(), 'adjust', 'Recommended configuration', cfg + EV.confirmBlock())}
```
