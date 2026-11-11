// The review queue: the items a person should check, in order: each claim of the final report with its evidence, the
// verdicts that contradict a check, the texts whose numbers differ from the measurements, the refused items, the
// hypotheses that ended without a verdict, then every remaining test. Each item: open, tick, note (kept by control.py
// in checks/reviews/<session>.json, as before), the progress, and the sign-off (a name; control.py adds the date),
// which Home shows on the session's row. An item's key is the one its panel uses, so a tick made in a panel counts here.
// ======================================================================================================
Object.assign(EV, {
  queue(M) {
    if (M._q) return M._q; const items = [], at = {}, cut = (s, n) => { s = String(s || ''); return s.length > n ? s.slice(0, n - 1) + '…' : s; };
    const add = (key, kind, text, open, more) => { if (key in at) { if (!at[key].kinds.includes(kind)) at[key].kinds.push(kind); return; } at[key] = { key, kinds: [kind], text, open, ...more }; items.push(at[key]); };
    M.claims.forEach(c => add('claim:' + c.n, 'claim', `claim ${c.n}: ${cut(c.text, 120)}`, c.tests[0] ? { t: 'test', id: c.tests[0] } : c.exps[0] ? { t: 'exp', id: c.exps[0] } : { t: 'report', id: 'report' }, { claim: c.n, evidence: c.evidence }));
    M.tests.filter(t => EV.contradicts(t.verdict, t.check ? [t.check] : [])).forEach(t => add('test:' + t.id, 'verdict contradicts its check', `test of ${t.hyp}: verdict ${t.verdict.id} says ${t.verdict.result}, its check ${t.check.result}`, { t: 'test', id: t.id }));
    EV.mismatches(M).forEach(x => add(x.key, 'numbers differ', `${x.where}: ${x.rows.length} number${x.rows.length === 1 ? '' : 's'} differ from the measurements`, x.open));
    M.turns.forEach(t => { if (t.malformed.length + t.refusals.length) add('log:' + t.n, 'refused', `turn ${t.n}: ${t.malformed.length ? 'the whole answer was refused' : 'part of the answer was refused (' + t.refusals.map(m => m.body.part).join(', ') + ')'}`, { t: 'log', id: t.n }); });
    M.hyps.filter(h => h.state === 'ended without a verdict').forEach(h => add('hyp:' + h.id, 'ended without a verdict', `${h.id}: ${cut(h.text, 110)}`, { t: 'hyp', id: h.id }));
    M.tests.forEach(t => add('test:' + t.id, 'test', `test of ${t.hyp} in ${t.exp}: ${t.check ? t.check.result : 'not checked'}${t.verdict ? ', ' + t.verdict.result : ''} · ${cut((M.hypById[t.hyp] || {}).text, 70)}`, { t: 'test', id: t.id }));
    return (M._q = items);
  },
  checked: (M, ticked) => { const keys = new Set(EV.queue(M).map(q => q.key)); return [ticked.filter(k => keys.has(k)).length, keys.size]; },

  paneTabs() {
    const S = EV.s, [a, n] = EV.checked(EV.M, Object.keys(EV.marks).filter(k => EV.marks[k].tick)), so = EV.marks.signoff;
    return `<div class="ev-bar" style="margin-bottom:8px"><span><button data-act="pane" data-id="detail" class="${S.pane !== 'queue' ? 'on' : ''}">Detail</button> <button data-act="pane" data-id="queue" class="${S.pane === 'queue' ? 'on' : ''}">Review queue</button></span>
      <span class="sm">checked ${a} of ${n} <span class="prog"><i style="width:${n ? 100 * a / n : 0}%"></i></span>${so ? ` · <span class="ok">signed off by ${EV.e(so.note)}</span>` : ''}</span></div>`;
  },
  queueView() {
    const M = EV.M, S = EV.s, e = EV.e, q = EV.queue(M), so = EV.marks.signoff, on = i => S.sel && `${S.sel.t}:${S.sel.id}` === `${i.open.t}:${i.open.id}` && (!i.claim || S.claim === i.claim);
    const row = (i, n) => { const m = EV.marks[i.key] || {};
      return `<div class="qi review${on(i) ? ' on' : ''}" data-item="${e(i.key)}"><input type="checkbox" data-ch="review"${m.tick ? ' checked' : ''}${EV.off ? ' disabled' : ''} title="checked"><div><a data-act="qopen" data-id="${n}">${i.kinds.filter(k => k !== 'test' && k !== 'claim').map(k => `<span class="pill ${k === 'refused' || k === 'numbers differ' || k === 'verdict contradicts its check' ? 'warnc' : ''}">${e(k)}</span> `).join('')}${e(i.text)}</a>
        ${i.evidence ? `<br><span class="sm">its evidence: ${i.evidence.map(EV.link).join(', ') || '<span class="warnc">none cited</span>'}</span>` : ''}</div><input type="text" data-ch="review" placeholder="note" value="${e(m.note || '')}"${EV.off ? ' disabled' : ''}></div>`; };
    return `<div id="p-queue"><div class="qlist">${q.map(row).join('') || '<p class="sm">Nothing to check yet.</p>'}</div>
      <div class="ev-bar" style="margin:8px 0${EV.off && !so ? ';display:none' : ''}"><b>Sign off</b>${so ? `<span class="ok">signed off by ${e(so.note)} on ${e(String(so.at || '').slice(0, 10))}</span>${EV.off ? '' : ' <button data-act="unsign">withdraw</button>'}`
        : `<input type="text" id="so-name" placeholder="your name" style="width:180px"> <button data-act="sign">Sign off this review</button><span class="sm">stored with the review; Home then shows it on this session's row</span>`}${S.soMsg ? ` <span class="bad">${e(S.soMsg)}</span>` : ''}</div>
      <p class="sm" style="border-top:1px solid var(--border);padding-top:8px">The item opened from the queue is shown below.</p></div>`;
  },
  async signOff(name) {
    const S = EV.s; S.soMsg = '';
    try { await EV.post('../api/review', { session: S.sid, item: 'signoff', tick: !!name, note: name || '' });
      if (name) EV.marks.signoff = { tick: true, note: name, at: new Date().toISOString().slice(0, 10) }; else delete EV.marks.signoff; } catch (x) { S.soMsg = x.message; }
    EV.draw();
  },
});
EV.act = Object.assign(EV.act || {}, {
  pane(id) { EV.s.pane = id; EV.draw(); },
  qopen(id) { const i = EV.queue(EV.M)[Number(id)]; if (!i) return; EV.s.sel = { ...i.open }; EV.s.claim = i.claim || null; EV.draw(); },
  sign() { const el = document.getElementById('so-name'), name = el ? el.value.trim() : ''; if (!name) { EV.s.soMsg = 'A sign-off needs a name.'; return EV.draw(); } EV.signOff(name); },
  unsign() { EV.signOff(''); },
});
