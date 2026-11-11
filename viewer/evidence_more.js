// The sections below the flow charts (stage 6 of RESTRUCTURE_PLAN.md): 1 brief, 2 session summary, 3 hypotheses,
// 4 experiments, 5 final report with each claim's evidence; and the printable evidence sheet of one claim.
// Everything a click opens appears in the panel on the right, which stays in view.
// ======================================================================================================
Object.assign(EV, {
  summaryKV() {
    const M = EV.M, m = M.meta || {}, f = m.flags || null, row = EV.files.row || {}, e = EV.e, c = M.counts;
    const mins = m.started && m.ended ? Math.round((new Date(m.ended) - new Date(m.started)) / 6e4) + ' min' : row.running ? 'running now' : EV.nr;
    const allowed = M.brief && M.brief.limits ? M.brief.limits.simulations : f ? f.budget : null, unusable = M.steps.filter(s => s.kind === 'answer' && s.warn).length;
    const kinds = {}; M.exps.forEach(x => { const k = x.by === 'harness' ? 'baseline' : x.kind || 'not recorded'; kinds[k] = (kinds[k] || 0) + 1; });
    const st = {}; M.hyps.forEach(h => { st[h.state] = (st[h.state] || 0) + 1; });
    const kv = [['model', m.model || EV.nr], ['flags', f ? Object.entries(f).map(([k, v]) => `${k} ${v}`).join(' · ') : EV.nr], [EV.term('Scheduling policy', 'scheduling policy') + ' (operator only)', EV.files.policy || EV.nr],
      ['started', m.started ? m.started.replace('T', ' ') : M.recs[0] && M.recs[0].ts ? M.recs[0].ts.replace('T', ' ') : EV.nr], ['duration', mins],
      [EV.term('Simulation', 'simulations') + ' used / allowed', `${m.simulations ?? EV.nr} / ${allowed ?? EV.nr}`], [EV.term('Turn', 'turns'), `${m.turns ?? c.turn}${unusable ? ` · ${unusable} unusable` : ''}`],
      ['model calls', m.calls ?? EV.nr], ['replies cut off', m.cut_off ?? EV.nr], ['how it ended', row.running ? 'running now' : m.how || EV.nr]];
    return `<div class="kv">${kv.map(([k, v]) => `<div><span>${k}</span><b style="font-size:13.5px">${String(v).startsWith('<') ? v : e(v)}</b></div>`).join('')}</div>
      <p class="sm" style="margin-top:6px">${EV.term('Hypothesis', 'hypotheses')} by state: ${EV.STATES.filter(s => st[s]).map(s => `${st[s]} ${s}`).join(' · ') || 'none'} · ${EV.term('Experiment', 'experiments')} by kind: ${Object.entries(kinds).map(([k, n]) => `${n} ${k}`).join(' · ') || 'none'}</p>`;
  },

  sections() {
    const M = EV.M, e = EV.e, left = new Set((M.meta && M.meta.left_open) || []);
    const hyps = M.hyps.map(h => `<div class="hc" data-act="open" data-t="hyp" data-id="${h.id}"><svg width="12" height="12" style="display:inline;vertical-align:-1px"><rect class="bx ${EV.stCls(h.state)}" x="1" y="1" width="10" height="10" rx="3"/></svg>
        <b>${EV_ICON.hypothesis} ${h.id}</b> · ${e(h.state)}${left.has(h.id) || h.state === 'ended without a verdict' ? ' <span class="warnc">left open at the end</span>' : ''}<br><span class="sm">${e(h.text.length > 220 ? h.text.slice(0, 218) + '…' : h.text)}</span>
        <br><span class="sm">tested by ${h.exps.join(', ') || 'no experiment'} · ${h.verdict ? `verdict ${h.verdict.id} (turn ${h.verdict.turn}): ${e(h.verdict.result)}` : h.drop ? 'dropped' : 'no verdict'}</span></div>`).join('');
    const exps = M.exps.map(x => { const held = x.checks.filter(c => c.result === 'held').length, vs = x.tests.map(h => [h, M.hypById[h] && M.hypById[h].verdict]).filter(q => q[1]);
      return `<tr class="pick" data-act="open" data-t="exp" data-id="${x.id}"><td>${EV_ICON.experiment} <b>${x.id}</b></td><td>${x.by === 'harness' ? 'baseline' : e(x.kind || '–')}</td><td>${x.tests.length ? x.tests.join(', ') : e(x.question || '–')}</td><td>${e(x.varied.join(', ') || '–')}</td>
        <td class="num">${x.sims.length}${x.sims.some(s => s.same_as) ? ` <span class="sm">(${x.sims.filter(s => s.same_as).length} ○)</span>` : ''}</td>
        <td>${x.checks.length ? `<span class="ok">${held} held</span> · <span class="${x.checks.length - held ? 'bad' : 'mut'}">${x.checks.length - held} failed</span>` : x.rules.length ? 'not checked' : '–'}</td>
        <td>${vs.map(([h, v]) => `${h} ${e(v.result)}${EV.contradicts(v, x.checks.filter(c => c.for === h)) ? ' <span class="warnc" title="the verdict disagrees with its check">⚠</span>' : ''}`).join(', ') || '–'}</td></tr>`; }).join('');
    return `<div class="ev-card" id="s-brief">${EV.briefCard().replace('<h2>', '<h2>1 · ')}</div>
      <div class="ev-card" id="s-summary"><h2>2 · ${EV.term('Session', 'Session')} summary</h2>${EV.summaryKV()}</div>
      <div class="ev-card" id="s-hyps"><h2>3 · ${EV.term('Hypothesis', 'Hypotheses')}<small>click one to open it on the right</small></h2>${hyps ? `<div class="hcs">${hyps}</div>` : '<p class="sm">none</p>'}</div>
      <div class="ev-card" id="s-exps"><h2>4 · ${EV.term('Experiment', 'Experiments')}<small>click a row to open it on the right</small></h2>${M.exps.length ? `<div class="ev-scroll"><table><thead><tr><th>#</th><th>kind</th><th>tests, or question</th><th>varied</th><th class="num">${EV.term('Simulation', 'simulations')}</th><th>${EV.term('Decision rule', 'decision rules')}</th><th>${EV.term('Verdict', 'verdicts')}</th></tr></thead><tbody>${exps}</tbody></table></div>` : '<p class="sm">none</p>'}</div>
      <div class="ev-card" id="s-report">${EV.reportBody().replace('<h2>', '<h2>5 · ')}</div>`;
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
    return `<h2>${EV_ICON.report} ${EV.term('Final report', 'Final report')}<small>turn ${M.repRec ? M.repRec.turn : EV.nr} · ${EV.link((M.repRec || {}).id || '')}</small></h2>
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
    window.print();
  },
});
