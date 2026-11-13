// Share. A link for every item: ?session=<id>&item=<record id> opens the page with that item selected and in view (the
// address bar follows the selection, and the trail of every opened card has "copy link"). Export: one folder, and a zip,
// that opens without a server (control.py's POST /api/export; never the drafts; operator-only data only when ticked).
// Print: the overview, the highlights, the best-so-far chart and the tests list; or the evidence sheet of one claim.
// ======================================================================================================
Object.assign(EV, {
  exp: { open: false, op: false, busy: false, msg: '', done: null },
  // the id that names an item in a link: a record id (a test: its check; before checks existed: experiment.hypothesis); a turn: turn-N
  itemOf(sel) {
    const M = EV.M; if (!sel || !M || sel.t === 'session') return '';
    if (sel.t === 'test') { const T = M.testById[sel.id]; return T && T.check ? T.check.id : String(sel.id); }
    return sel.t === 'log' ? 'turn-' + sel.id : sel.t === 'report' ? (M.repRec ? M.repRec.id : 'report') : String(sel.id);
  },
  selOf(M, item) {  // the item a link names, as a selection of this session (null: nothing by that id)
    const m = /^turn-(\d+)$/.exec(item || ''); if (m) return M.turns.some(t => t.n === Number(m[1])) ? { t: 'log', id: Number(m[1]) } : null;
    if (item === 'brief' || item === 'report') return { t: item, id: item }; if (M.testById[item]) return { t: 'test', id: item };
    const r = M.byId[item]; if (!r) return null; const b = r.body || {}, test = f => M.tests.find(f);
    if (r.type === 'check') { const T = test(t => t.check && t.check.id === item); return T ? { t: 'test', id: T.id } : { t: 'exp', id: r.parent }; }
    if (r.type === 'verdict') { const T = test(t => t.verdict && t.verdict.id === item); return T ? { t: 'test', id: T.id } : { t: 'hyp', id: b.for }; }
    if (r.type === 'simulation' || (r.type === 'evidence' && M.simById[item])) return { t: 'sim', id: item };
    return r.type === 'hypothesis' ? { t: 'hyp', id: item } : r.type === 'drop' ? { t: 'hyp', id: b.for } : r.type === 'experiment' ? { t: 'exp', id: item } : r.type === 'evidence' ? { t: 'exp', id: b.experiment || r.parent }
      : r.type === 'report' ? { t: 'report', id: 'report' } : { t: 'log', id: r.turn };
  },
  linkTo(sel) { const it = EV.itemOf(sel); return `${location.href.split('?')[0].split('#')[0]}?session=${encodeURIComponent(EV.s.sid)}${it ? '&item=' + encodeURIComponent(it) : ''}`; },
  copyBtn: sel => `<button class="cl" data-act="copy" data-link="${EV.e(EV.linkTo(sel))}" title="A link that opens this page with ${sel && sel.t !== 'session' ? 'this item selected' : 'this session'}">${EV.s.copied === EV.linkTo(sel) ? 'link copied' : 'copy link'}</button>`,
  reveal() {  // after a link: the selected row of the tree in view inside the tree; the page itself is not moved
    const box = document.querySelector('#s-tree .tree'), row = box && box.querySelector('.tr.sel'); if (row) box.scrollTop = Math.max(0, box.scrollTop + row.getBoundingClientRect().top - box.getBoundingClientRect().top - 90);
  },

  shareBar() {
    const S = EV.s, e = EV.e, x = EV.exp, X = window.EV_EXPORT;
    if (X) return `<p class="sm noprint">An exported copy of this session, made ${e(String(X.made).replace('T', ' '))}${X.operator ? ', with the operator-only data' : ', without operator-only data'}: nothing can be started or saved from it. ${EV.copyBtn(S.sel)} · <button data-act="printpage">Print</button></p>`;
    return `<p class="sm noprint">share: ${EV.copyBtn(S.sel)} to ${S.sel && S.sel.t !== 'session' ? 'the open item' : 'this session'} · <button data-act="printpage">Print</button> the overview, highlights, best so far and tests · <button data-act="expopen">${x.open ? 'close the export' : 'Export session…'}</button></p>
      ${x.open ? `<div class="who noprint" data-by="operator"><p class="sm">One folder, and a zip of it, holding this page and this session's files. It opens by double-clicking <code>index.html</code>, with no server, and never contains drafts.</p>
        <p><label style="font-weight:400"><input type="checkbox" data-ch="expop"${x.op ? ' checked' : ''}> include operator-only data (scheduling policy, score, review, answer key, sweep table)</label>
          <button data-act="expgo"${x.busy ? ' disabled' : ''}>${x.busy ? 'Exporting…' : 'Export'}</button>${x.msg ? ` <span class="bad">${e(x.msg)}</span>` : ''}</p>
        ${x.done ? `<p class="sm"><span class="rs">${EV.gkey('check')}exported</span> ${x.done.files} files, ${(x.done.bytes / 1e6).toFixed(1)} MB, ${x.done.operator ? 'with' : 'without'} operator-only data: <code>${e(x.done.folder)}/</code> ·
          <a href="../${e(x.done.zip)}" download>download the zip</a> · <a href="../${e(x.done.open)}" target="_blank" rel="noopener">open the exported page</a>${x.done.chart_library ? '' : ' · the chart library could not be fetched, so the exported page has no charts over time'}</p>` : ''}</div>` : ''}`;
  },
});
EV.chg = Object.assign(EV.chg || {}, { expop(t) { EV.exp.op = t.checked; } });
EV.act = Object.assign(EV.act || {}, {
  async copy(id, t) {
    const link = t.dataset.link; try { await navigator.clipboard.writeText(link); } catch (x) { window.prompt('Copy this link:', link); }
    EV.s.copied = link; EV.draw(); setTimeout(() => { if (EV.s.copied === link) { EV.s.copied = null; EV.draw(); } }, 2500);
  },
  expopen() { EV.exp.open = !EV.exp.open; EV.draw(); },
  async expgo() {
    const x = EV.exp; if (x.busy) return; x.busy = true; x.msg = ''; x.done = null; EV.draw();
    try { x.done = await EV.post('../api/export', { session: EV.s.sid, operator: !!x.op }); } catch (q) { x.msg = q.message; }
    x.busy = false; EV.draw();
  },
  printpage() { document.getElementById('ev').classList.remove('sheet'); window.print(); },
});
