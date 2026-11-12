// The session's summary, the tests list (one row per test, grouped under its experiment), the final report in full
// with each claim's evidence, and the printable evidence sheet of one claim.
// ======================================================================================================
Object.assign(EV, {
  summaryKV() {
    const M = EV.M, m = M.meta || {}, f = m.flags || null, row = EV.files.row || {}, e = EV.e, c = M.counts;
    const mins = m.started && m.ended ? Math.round((new Date(m.ended) - new Date(m.started)) / 6e4) + ' min' : row.running ? 'running now' : EV.nr;
    const allowed = M.brief && M.brief.limits ? M.brief.limits.simulations : f ? f.budget : null, unusable = M.steps.filter(s => s.kind === 'answer' && s.warn).length;
    const kinds = {}; M.exps.forEach(x => { const k = x.by === 'harness' ? 'baseline' : x.kind || 'not recorded'; kinds[k] = (kinds[k] || 0) + 1; });
    const st = {}; M.hyps.forEach(h => { st[h.state] = (st[h.state] || 0) + 1; });
    const kv = [['model', m.model || EV.nr], ['flags', f ? Object.entries(f).map(([k, v]) => `${k} ${v}`).join(' · ') : EV.nr], ...(EV.s.op ? [[EV.term('Scheduling policy', 'scheduling policy') + ' (operator column)', EV.policyText(EV.files.row)]] : []),
      ['started', m.started ? m.started.replace('T', ' ') : M.recs[0] && M.recs[0].ts ? M.recs[0].ts.replace('T', ' ') : EV.nr], ['duration', mins],
      [EV.term('Simulation', 'simulations') + ' used / allowed', `${m.simulations ?? row.simulations ?? EV.nr} / ${allowed ?? EV.nr}`], [EV.term('Turn', 'turns'), `${m.turns ?? c.turn}${unusable ? ` · ${unusable} unusable` : ''}`],
      ['model calls', m.calls ?? EV.nr], ['replies cut off', m.cut_off ?? EV.nr], ['how it ended', row.running ? 'running now' : m.how || EV.nr]];
    return `<div class="kv">${kv.map(([k, v]) => `<div><span>${k}</span><b style="font-size:13.5px">${String(v).startsWith('<') ? v : e(v)}</b></div>`).join('')}</div>
      <p class="sm" style="margin-top:6px">${EV.term('Hypothesis', 'hypotheses')} by state: ${EV.STATES.filter(s => st[s]).map(s => `${st[s]} ${s}`).join(' · ') || 'none'} · ${EV.term('Experiment', 'experiments')} by kind: ${Object.entries(kinds).map(([k, n]) => `${n} ${k}`).join(' · ') || 'none'}</p>`;
  },

  testsCard() {
    const M = EV.M, e = EV.e;
    // the main list: one row per test, grouped under a light heading per experiment; an exploration is a heading with its question
    const list = M.exps.map(x => { const ts = M.tests.filter(T => T.exp === x.id), n = x.sims.length;
      const head = `<tr class="grp pick" data-act="open" data-t="exp" data-id="${x.id}"><td colspan="5">${EV_ICON.experiment} experiment ${x.id} · ${x.turn ? 'turn ' + x.turn : 'before the first turn'} · ${n} simulation${n === 1 ? '' : 's'} · ${
        ts.length ? ts.length + (ts.length === 1 ? ' test' : ' tests') : x.by === 'harness' ? 'the baseline, no tests' : 'no tests: it explores “' + e(x.question || 'not recorded') + '”'}</td></tr>`;
      return head + ts.map(T => { const h = M.hypById[T.hyp], v = T.verdict, txt = h ? h.text : '';
        return `<tr class="pick" data-act="open" data-t="test" data-id="${e(T.id)}"><td>${EV_ICON.test} <b>${e(T.hyp)}</b> <span class="sm">${e(txt.length > 90 ? txt.slice(0, 88) + '…' : txt)}</span></td><td class="sm">${e(EV.compared(T))}</td>
          <td>${T.check ? `<span class="${T.check.result === 'held' ? 'ok' : 'bad'}">${e(T.check.result)}</span>` : T.rule ? '<span class="mut">not checked</span>' : '–'}</td><td class="noprint mgc">${EV.marginCell(T.check)}</td>
          <td>${v ? `${v.id} ${e(v.result)}${EV.contradicts(v, T.check ? [T.check] : []) ? ' <span class="warnc" title="the verdict disagrees with its check">⚠</span>' : ''}` : '<span class="mut">no verdict</span>'}</td></tr>`; }).join(''); }).join('');
    return `<div class="ev-card" id="s-tests"><h2>${EV.term('Test', 'Tests')} <small>one hypothesis put to one decision rule; grouped under the ${EV.term('Experiment', 'experiment')} they were run in · click a row to open it on the right</small></h2>
        ${M.exps.length ? `<div class="ev-scroll"><table><thead><tr><th>test of</th><th>what was compared</th><th>${EV.term('Check', 'check')}</th><th class="noprint" title="${e(EV.MARGIN_NOTE)}">margin</th><th>${EV.term('Verdict', 'verdict')}</th></tr></thead><tbody>${list}</tbody></table></div>
        <p class="sm noprint" id="mg-note"><b>margin</b>: ${e(EV.MARGIN_NOTE)} The bar is cut at ±100%.</p>` : '<p class="sm">none</p>'}</div>`;
  },

  // one line that says what an evidence item is
  evLine(id) {
    const M = EV.M, r = M.byId[id], e = EV.e, b = r && r.body || {}; if (!r) return `<span class="bad">${e(id)} is not in the ledger</span>`;
    if (r.type === 'check') return `${e(b.for)}: <code>${e(b.decision_rule || b.rule)}</code> → ${e(b.with_numbers)} → <b class="${b.result === 'held' ? 'ok' : 'bad'}">${e(b.result)}</b>`;
    if (r.type === 'verdict') return `on ${e(b.for)}: <b>${e(b.result)}</b> · ${e(String(b.because || '').slice(0, 160))}`;
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
      <div class="ev-top"><div><h3>recommendation</h3>${kv(rep.recommendation)}</div><div><h3>expected performance</h3>${kv(rep.expected)}</div></div>
      <h3>goal, as it states it</h3>${txt(rep.goal)}<h3>explanation</h3>${txt(rep.explanation)}<h3>holds when</h3>${txt(rep.holds_when)}<h3>breaks when</h3>${txt(rep.breaks_when)}
      ${rep.open_questions ? `<h3>open questions</h3>${txt(rep.open_questions)}` : ''}
      <h3>the report's numbers against the measurements</h3>${EV.numCheck(all, M.sims) || '<p class="sm">no number in the report names or equals a measurement</p>'}
      <h3>claims and their evidence</h3>${M.claims.map(c => `<div class="who" data-by="model"><p><b>claim ${c.n}</b> <span class="chip ${c.state}" style="padding:0 6px">${{ held: 'checks held', failed: 'a check failed', none: 'no evidence cited', unchecked: 'evidence without a check' }[c.state]}</span> ${e(c.text)}</p>
        ${c.evidence.map(id => `<div class="sm" style="margin:3px 0 0 8px">${EV.link(id)} ${EV.evLine(id)}${EV.reviewBox('rec:' + id)}</div>`).join('') || '<p class="sm warnc">cites no evidence</p>'}
        <p class="sm"><button data-act="print" data-id="${c.n}">print the evidence sheet for claim ${c.n}</button></p></div>`).join('') || '<p class="sm">The report states no claims.</p>'}`;
  },

  // the evidence sheet of one claim: everything it cites, in full, with the reviewer's marks; printed on its own
  printSheet(n) {
    const M = EV.M, e = EV.e, c = M.claims[n - 1]; if (!c) return;
    const full = id => { const r = M.byId[id], b = r && r.body || {}, mk = EV.marks['rec:' + id] || {};
      const more = !r ? '' : r.type === 'check' ? (() => { const x = M.expById[r.parent]; return x ? `<table><thead><tr><th>simulation</th><th>settings</th><th>measured</th></tr></thead><tbody>${x.sims.map(s => `<tr><td>${s.id} ${e(s.label)}</td><td>${e(Object.entries(s.params).map(([k, v]) => k + ' ' + v).join(', '))}</td><td>${e(Object.entries(s.metrics || {}).map(([k, v]) => k + ' ' + v).join(', '))}</td></tr>`).join('')}</tbody></table>` : ''; })()
        : r.type === 'verdict' ? `<p>because: ${e(b.because)}</p><p>next: ${e(b.next)}</p>` : r.type === 'evidence' ? `<ul>${(b.lines || []).map(l => `<li>${e(l)}</li>`).join('')}</ul>` : r.type === 'simulation' ? `<p>${e(JSON.stringify(b.params))}</p><p>${e(JSON.stringify(b.metrics))}</p>` : '';
      return `<h3>${e(id)} · ${e(r ? r.type : 'not in the ledger')} · recorded ${e(r ? r.ts : '')}</h3><p>${EV.evLine(id)}</p>${more}<p>reviewer: ${mk.tick ? '✓ reviewed' : 'not reviewed'}${mk.note ? ' · note: ' + e(mk.note) : ''}</p>`; };
    document.getElementById('ev-print').innerHTML = `<h1>Evidence sheet · session ${e(M.id)} · claim ${n}</h1><p>${e(c.text)}</p><p>${c.evidence.length} evidence items · ${c.state}</p>${c.evidence.map(full).join('')}`;
    const root = document.getElementById('ev'); root.classList.add('sheet'); window.onafterprint = () => root.classList.remove('sheet');  // print the sheet alone, then the page is itself again
    window.print();
  },
});
