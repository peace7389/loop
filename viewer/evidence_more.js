// The session's summary, the tests list (one row per test, grouped under its experiment), the final report in full
// with each claim's evidence, and the printable evidence sheet of one claim.
// ======================================================================================================
Object.assign(EV, {
  summaryKV() {
    const M = EV.M, m = M.meta || {}, f = m.flags || null, row = EV.files.row || {}, e = EV.e, c = M.counts;
    const mins = m.started && m.ended ? Math.round((new Date(m.ended) - new Date(m.started)) / 6e4) + ' min' : row.running ? 'running now' : EV.nr;
    const unusable = M.steps.filter(s => s.kind === 'answer' && s.warn).length;  // the model, the simulations used and how it ended stand in the header strip, not here again
    // in the replay only what is recorded by its step: the figures written at the session's end (duration, calls, replies cut off) are absent
    const live = EV.s.step == null, seen = EV.seen, at = live ? null : EV_DATA.stateAt(M, EV.s.step);
    const kinds = {}; M.exps.filter(x => seen(x.id)).forEach(x => { const k = x.by === 'harness' ? 'baseline' : x.kind || 'not recorded'; kinds[k] = (kinds[k] || 0) + 1; });
    const st = {}; M.hyps.filter(h => seen(h.id)).forEach(h => { const s = at ? at[h.id] || 'open' : h.state; st[s] = (st[s] || 0) + 1; });
    const kv = [['model', m.model || EV.nr], ['flags', f ? Object.entries(f).map(([k, v]) => `${k} ${v}`).join(' · ') : EV.nr], ...(EV.s.op ? [[EV.term('Scheduling policy', 'scheduling policy') + ' (operator column)', EV.policyText(EV.files.row)]] : []),
      ['started', m.started ? m.started.replace('T', ' ') : M.recs[0] && M.recs[0].ts ? M.recs[0].ts.replace('T', ' ') : EV.nr], ...(live ? [['duration', mins], [EV.term('Turn', 'turns'), `${m.turns ?? c.turn}${unusable ? ` · ${unusable} unusable` : ''}`], ['model calls', m.calls ?? EV.nr], ['replies cut off', m.cut_off ?? EV.nr]]
        : [[EV.term('Turn', 'turns') + ' by this step', String(EV.glCounts().turn)]])];
    return `<div class="kv" id="sum-kv">${kv.map(([k, v]) => `<div><span>${k}</span><b>${String(v).startsWith('<') ? v : e(v)}</b></div>`).join('')}</div>
      <p class="sm" style="margin-top:6px">${EV.term('Hypothesis', 'hypotheses')} by state: ${EV.STATES.filter(s => st[s]).map(s => `${st[s]} ${s}`).join(' · ') || 'none'} · ${EV.term('Experiment', 'experiments')} by kind: ${Object.entries(kinds).map(([k, n]) => `${n} ${k}`).join(' · ') || 'none'}</p>`;
  },

  testsCard() {
    const M = EV.M, e = EV.e, st = id => M.recStep[id] ?? 0, end = M.steps.length - 1, at = (k, html) => `<span data-step="${k}">${html}</span>`;
    // the main list: one row per test, grouped under a light heading per experiment; an exploration is a heading with its question.
    // It follows the replay as the tree does: a heading and a row carry the step of their experiment, a check and a verdict
    // the step of their own record, and what says that something never came ("no verdict") the last step
    const list = M.exps.map(x => { const ts = M.tests.filter(T => T.exp === x.id), n = x.sims.length;
      const head = `<tr class="grp pick" data-act="open" data-t="exp" data-id="${x.id}" data-step="${st(x.id)}"><td>${EV_ICON.experiment} experiment ${x.id} · ${x.turn ? 'turn ' + x.turn : 'before the first turn'} · ${n} simulation${n === 1 ? '' : 's'} · ${
        ts.length ? ts.length + (ts.length === 1 ? ' test' : ' tests') : x.by === 'harness' ? 'the baseline, no tests' : 'no tests: it explores “' + e(x.question || 'not recorded') + '”'}</td></tr>`;
      // a test is two lines: its hypothesis as its question (the first 30 words, then "more"; a session without questions: the hypothesis text, cut after two lines);
      // under it what was compared, the check, the margin and the verdict
      return head + ts.map(T => { const h = M.hypById[T.hyp], v = T.verdict, mc = EV.marginCell(T.check), cmp = EV.compared(T);
        return `<tr class="pick" data-act="open" data-t="test" data-id="${e(T.id)}" data-step="${st(x.id)}"><td><div class="tt-h${h && h.question ? '' : ' lc2'}">${EV_ICON.test} <b>${e(T.hyp)}</b> ${h && h.question ? EV.question(h) : e(h ? h.text : '')}</div>
          <div class="tt-m sm${T.check && T.check.void ? ' vd' : ''}"><span class="tt-c" title="${e(cmp)}">${e(cmp)}</span><span class="tt-k">${T.check ? at(st(T.check.id), '<span class="tt-l">check</span> ' + EV.checkRes(T.check)) : at(end, T.rule ? '<span class="mut">not checked</span>' : '<span class="mut">no decision rule</span>')}</span>
            <span class="mgc noprint">${mc ? `<span class="tt-l" title="${e(EV.MARGIN_NOTE)}">margin</span> ${mc}` : T.check && T.check.void && EV.seen(T.check.id) ? '<span class="vd-note">this decision rule compared a simulation with itself</span>' : ''}</span>
            <span class="tt-v">${v ? at(st(v.id), `<span class="tt-l">verdict</span> ${v.id} ${EV.verdictRes(v.result)}${EV.rests(v)}${EV.contradicts(v, T.check ? [T.check] : []) ? ' ' + EV.warn('', 'the verdict disagrees with its check') : ''}`) : at(end, '<span class="mut">no verdict</span>')}</span></div></td></tr>`; }).join(''); }).join('');
    return `<div class="ev-card" id="s-tests"><h2>${EV.term('Test', 'Tests')} <small>one hypothesis put to one decision rule; grouped under the ${EV.term('Experiment', 'experiment')} they were run in</small></h2>
        ${M.exps.length ? `<div class="ev-scroll"><table style="table-layout:fixed"><tbody>${list}</tbody></table></div>
        <p class="sm noprint" id="mg-note"><b>margin</b>: ${e(EV.MARGIN_NOTE)} The bar is cut at ±100%.</p>` : '<p class="sm">none</p>'}</div>`;
  },

  // one line that says what an evidence item is
  evLine(id) {
    const M = EV.M, r = M.byId[id], e = EV.e, b = r && r.body || {}; if (!r) return `<span class="bad">${e(id)} is not in the ledger</span>`;
    if (r.type === 'check') { const T = M.tests.find(q => q.check && q.check.id === id); if (T) return `${e(b.for)}: ${EV.ruleRead(T)} → ${EV.checkRead(T)}`;
      return `${e(b.for)}: <code>${e(b.decision_rule || b.rule)}</code> → ${e(b.with_numbers)} → ${EV.checkRes(M.checks.find(q => q.id === id) || { result: b.result })}`; }
    if (r.type === 'verdict') return `on ${e(b.for)}: ${EV.verdictRes(b.result)} · ${e(String(b.because || '').slice(0, 160))}`;
    if (r.type === 'evidence') return `the table of ${e(b.experiment || r.parent)}: ${(b.lines || []).length} simulation line${(b.lines || []).length === 1 ? '' : 's'}`;
    if (r.type === 'simulation') return `“${e(b.label)}” ${e(Object.entries(b.params || {}).map(([k, v]) => k + ' ' + v).join(', ').slice(0, 140))}`;
    return e(r.type);
  },
  reportBody() {
    const M = EV.M, e = EV.e, rep = M.report, m = M.meta || {};
    if (!rep) return `<h2>${EV_ICON.report} ${EV.term('Final report', 'Final report')}</h2><p class="sm">${EV.nr}: ${M.ended ? 'the session ended without one' + (m.how ? ` (${e(m.how)})` : '') : 'the session is still running'}.</p>`;
    const kv = o => (o && typeof o === 'object' ? `<table><tbody>${Object.entries(o).map(([k, v]) => `<tr><td>${e(TH_DATA.KNOB[k] || TH_DATA.PLAIN[k] || k)}</td><td class="num">${e(EV.val(k, v))}</td></tr>`).join('')}</tbody></table>` : `<p>${e(o ?? 'not recorded')}</p>`);
    const txt = v => (Array.isArray(v) ? `<ul style="margin:0;padding-left:18px">${v.map(q => `<li>${e(q)}</li>`).join('')}</ul>` : `<p>${e(v ?? 'not recorded')}</p>`);
    const all = [rep.explanation, rep.holds_when, rep.breaks_when, ...(rep.claims || []).map(c => c.text)].flat().filter(Boolean).join('\n');
    return `<h2>${EV_ICON.report} ${EV.term('Final report', 'Final report')} <small>turn ${M.repRec ? M.repRec.turn : EV.nr} · ${EV.link((M.repRec || {}).id || '')}</small></h2>
      <div class="ev-top"><div><h3>Recommendation</h3>${kv(rep.recommendation)}</div><div><h3>Expected performance</h3>${kv(rep.expected)}</div></div>
      <h3>Goal, as it states it</h3>${txt(rep.goal)}<h3>Explanation</h3>${txt(rep.explanation)}<h3>Holds when</h3>${txt(rep.holds_when)}<h3>Breaks when</h3>${txt(rep.breaks_when)}
      ${rep.open_questions ? `<h3>Open questions</h3>${txt(rep.open_questions)}` : ''}
      <h3>The report's numbers against the measurements</h3>${EV.numCheck(all, M.sims) || '<p class="sm">no number in the report names or equals a measurement</p>'}
      <h3>Claims and their evidence</h3>${M.claims.map(c => `<div class="who" data-by="model"><p><b>claim ${c.n}</b> ${e(c.text)} <span class="sm">${EV.claimMarks(c, EV.seen)}</span></p>
        ${c.evidence.map(id => `<div class="sm" style="margin:3px 0 0 8px">${EV.link(id)} ${EV.evLine(id)}${EV.reviewBox('rec:' + id)}</div>`).join('') || '<p class="sm warnc">cites no evidence</p>'}
        <p class="sm"><button data-act="print" data-id="${c.n}">print the evidence sheet for claim ${c.n}</button></p></div>`).join('') || '<p class="sm">The report states no claims.</p>'}`;
  },

  // the evidence sheet of one claim: everything it cites, in full, with the reviewer's marks; printed on its own
  printSheet(n) {
    const M = EV.M, e = EV.e, c = M.claims[n - 1]; if (!c) return;
    const full = id => { const r = M.byId[id], b = r && r.body || {}, mk = EV.marks['rec:' + id] || {};
      const more = !r ? '' : r.type === 'check' ? (() => { const x = M.expById[r.parent]; return x ? `<table><thead><tr><th>simulation</th><th>settings</th><th>measured</th></tr></thead><tbody>${x.sims.map(s => `<tr><td>${s.id} ${e(s.label)}</td><td>${e(Object.entries(s.params).map(([k, v]) => k + ' ' + v).join(', '))}</td><td>${e(Object.entries(s.metrics || {}).map(([k, v]) => k + ' ' + v).join(', '))}</td></tr>`).join('')}</tbody></table>` : ''; })()
        : r.type === 'verdict' ? `<p>because: ${e(b.because)}</p><p>next: ${e(b.next)}</p>` : r.type === 'evidence' ? `<ul>${(b.lines || []).map(l => `<li>${e(l)}</li>`).join('')}</ul>` : r.type === 'simulation' ? `<p>${e(JSON.stringify(b.params))}</p><p>${e(JSON.stringify(b.metrics))}</p>` : '';
      return `<h3>${e(id)} · ${e(r ? r.type : 'not in the ledger')} · recorded ${e(r ? r.ts : '')}</h3><p>${EV.evLine(id)}</p>${more}<p>reviewer: ${mk.tick ? EV.gkey('check') + 'reviewed' : 'not reviewed'}${mk.note ? ' · note: ' + e(mk.note) : ''}</p>`; };
    document.getElementById('ev-print').innerHTML = `<h1>Evidence sheet · session ${e(M.id)} · claim ${n}</h1><p>${e(c.text)}</p><p>${c.evidence.length} evidence items · ${EV.claimMarks(c)}</p>${c.evidence.map(full).join('')}`;
    const root = document.getElementById('ev'); root.classList.add('sheet'); window.onafterprint = () => root.classList.remove('sheet');  // print the sheet alone, then the page is itself again
    window.print();
  },
});
