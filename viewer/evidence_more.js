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
    const kv = [['model', m.model || EV.nr], ['flags', f ? Object.entries(f).map(([k, v]) => (k === 'supervisor' && v && typeof v === 'object' ? `supervisor: the same model, asked apart at temperature ${v.temperature}` : `${k} ${v}`)).join(' · ') : EV.nr], ...(EV.s.op ? [[EV.term('Scheduling policy', 'scheduling policy') + ' (operator column)', EV.policyText(EV.files.row)]] : []),
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
  // ---- the final report in full, in the detail pane. The same parts, in the same order and under the same names as "What it proposes" on the page (the aim,
  // the proposed adjustment, the expected result, its diagnosis, because, but, the explanation), each in a box of its own; here nothing is cut. Formats, one
  // each: a setting or a measure is a row "name | value" (the name plain, the value bold, written as everywhere else on the page: "Bbr", "10 s", "83.81 %");
  // the AI's own sentences stand one sentence a line, their special terms set off (EV.hl); a claim is a card: its number, what it cites as marks, its sentence,
  // then one row for each record it cites (the record's link, what it is, its result, and the reviewer's tick and note at the right).
  // a long text of the AI as lines, one sentence each (the words and their order are not changed; a list stays a list)
  repLines(v) { const cut = t => String(t).split(/(?<=[a-z0-9)%\]][.!?])\s+(?=[A-Z(])/).reduce((o, q) => { if (o.length && /\b(?:vs|e\.g|i\.e|approx|etc|cf|resp)\.$/i.test(o[o.length - 1])) o[o.length - 1] += ' ' + q; else o.push(q); return o; }, []);
    if (v == null || v === '') return '<p class="mut">not recorded</p>';
    return Array.isArray(v) ? `<ul class="rp-list" data-own="model">${v.map(q => `<li>${EV.hl(q)}</li>`).join('')}</ul>` : `<div class="rp-text" data-own="model">${cut(v).map(q => `<span class="rp-s">${EV.hl(q)}</span>`).join(' ')}</div>`; },
  // one cited record as a row: [what it is, its result as a badge, labelled lines under it]
  evRow(id) {
    const M = EV.M, r = M.byId[id], e = EV.e, b = r && r.body || {}, kv = (k, v) => (v ? `<div class="rp-kv"><span class="rp-k">${k}</span><div class="rp-v lc2">${v}</div></div>` : '');
    let what = '', res = '', more = '';
    if (!r) what = `<span class="bad">${e(id)} is not in the ledger</span>`;
    else if (r.type === 'check') { const T = M.tests.find(q => q.check && q.check.id === id), c = M.checks.find(q => q.id === id) || { result: b.result };
      what = `check of ${e(b.for)}`; res = EV.checkRes(c);
      more = T ? kv('Rule', EV.ruleRead(T)) + kv('Measured', EV.checkRead(T)) : kv('Rule', `<code>${e(b.decision_rule || b.rule)}</code>`) + kv('Measured', e(b.with_numbers)); }
    else if (r.type === 'verdict') { what = `verdict on ${e(b.for)}`; res = EV.verdictRes(b.result); more = kv('Because', b.because ? `<span data-own="model" title="${e(b.because)}">${EV.hl(b.because)}</span>` : ''); }
    else if (r.type === 'evidence') { const n = (b.lines || []).length, x = b.experiment || r.parent; what = `result table of ${e(x)}`; res = `<span class="sm">${n} simulation${n === 1 ? '' : 's'}</span>`; }
    else if (r.type === 'simulation') { what = `simulation “${e(b.label)}”`; more = kv('Settings', `<span data-exact="1">${Object.entries(b.params || {}).map(([k, v]) => `${e(EV.LABEL[k] || k)} <b>${e(EV.setVal(k, v))}</b>`).join(' · ')}</span>`); }
    else what = e(r.type);
    return `<div class="rp-ev" data-ev="${e(id)}"><span class="rp-id">${EV.link(id)}</span><div class="rp-what"><span class="rp-w">${what}</span>${res ? ` <span class="rp-res">${res}</span>` : ''}${more}</div><div class="rp-rev noprint">${EV.reviewBox('rec:' + id)}</div></div>`;
  },
  reportBody() {
    const M = EV.M, S = EV.s, e = EV.e, rep = M.report, m = M.meta || {};
    if (!rep) return `<h2>${EV_ICON.report} ${EV.term('Final report', 'Final report')}</h2><p class="sm">${EV.nr}: ${M.ended ? 'the session ended without one' + (m.how ? ` (${e(m.how)})` : '') : 'the session is still running'}.</p>`;
    const kn = (M.brief && M.brief.knobs) || {}, g = (M.brief && M.brief.goal) || {}, rec = rep.recommendation, X = EV.expRows(rep), lines = EV.repLines;
    const same = (a, b) => (typeof a === 'number' || typeof b === 'number' ? Number(a) === Number(b) : EV.knNum(a) === EV.knNum(b) || String(a) === String(b));
    // a block is written as [key, title, body, note, class]; they are numbered in the order shown, once all are known
    const blk = (...q) => q, box = ([key, title, body, note, cls], i) => `<div class="rp-b${cls ? ' ' + cls : ''}" data-rp="${key}"><h3><span class="st-n">${i + 1}</span>${title}${note ? ` <small>${note}</small>` : ''}</h3>${body}</div>`;
    // 1 · the aim, and who set it
    const by = (who, t) => `<span class="st-by" data-by="${who}"><i class="sw"></i>${t}</span>`;
    const aim = g.kind === 'given' ? `<p data-aim="given"><b>Find ${EV.aimWords(g) || 'not recorded'}.</b> ${by('operator', 'set by the operator')}</p><div class="rp-kv"><span class="rp-k">As the AI states it</span><div class="rp-v">${lines(rep.goal)}</div></div>`
      : `${lines(rep.goal)}<p class="sm">${by('model', g.kind === 'open' ? 'chosen by the AI' : 'as the final report states it')}${g.kind === 'open' ? ` · the brief left the aim open, and the AI states its aim here, <b class="aim-end">at the end</b>` : ''}</p>`;
    // 2 · the proposed adjustment: every setting the AI may change, the value the session started from beside the one it recommends; a changed one is set off
    const keys = rec && typeof rec === 'object' ? [...EV.SET_ORDER.filter(k => k in kn || k in rec), ...Object.keys(rec).filter(k => !EV.SET_ORDER.includes(k))] : [];
    const adjRow = k => { const has = k in rec, was = k in kn ? EV.setVal(k, kn[k].default) : null, chg = has && (!(k in kn) || !same(rec[k], kn[k].default));
      return `<tr data-knob="${e(k)}" data-chg="${chg ? 1 : 0}"><td class="rp-n">${EV.label(k, (kn[k] || {}).meaning)}</td><td class="rp-was">${was == null ? '<span class="mut">–</span>' : e(was)}</td><td class="rp-arrow">${chg ? '→' : ''}</td><td class="rp-now">${!has ? '<span class="mut" title="The report names no value for this setting: it stays as at the start">not named</span>' : chg ? `<b>${e(EV.setVal(k, rec[k]))}</b>` : '<span class="mut">unchanged</span>'}</td></tr>`; };
    const nchg = keys.filter(k => k in rec && (!(k in kn) || !same(rec[k], kn[k].default))).length;
    const adj = rec == null ? '<p class="mut">not recorded</p>' : typeof rec !== 'object' ? lines(String(rec))
      : `<table class="rp-t rp-adj" data-exact="1"><thead><tr><th>setting</th><th>at the start</th><th></th><th>it recommends</th></tr></thead><tbody>${keys.map(adjRow).join('')}</tbody></table>`;
    // 3 · the expected result: every measure it names; the two that only repeat a setting stand last, lighter
    const rpt = Object.entries(typeof rep.expected === 'object' && rep.expected || {}).filter(([k]) => ['link_rate_bps', 'weight_udp'].includes(k));
    const exp = !X ? lines(rep.expected) : `<table class="rp-t rp-exp"><thead><tr><th>measure</th><th class="num">it expects</th></tr></thead><tbody>${X.all.map(X.row).join('')}${rpt.map(([k, v]) => `<tr data-k="${e(k)}" class="rp-rpt" title="This only repeats a setting"><td>${e(TH_DATA.PLAIN[k] || k)}</td><td class="num">${EV.v4(k, v)}</td></tr>`).join('')}</tbody></table>`;
    // 4 to 6 · the claims by their part in the argument; a report recorded without roles: one list
    const claim = c => `<div class="rp-claim${S.claim === c.n ? ' on' : ''}" data-claim="${c.n}" data-role="${e(c.role || '')}"><div class="rp-ch"><b class="rp-cn" data-wd="c:${c.n}">claim ${c.n}</b><span class="rp-cm sm">${EV.claimMarks(c, EV.seen)}</span><button class="cl noprint" data-act="print" data-id="${c.n}" title="Print the evidence sheet of claim ${c.n}: everything it cites, in full, with the reviewer's marks">print its evidence sheet</button></div>
        <p class="rp-ct" data-own="model">${EV.hl(c.text)}</p>
        ${c.evidence.length ? `<details class="rp-evs" data-cites="${c.n}"${(EV.citesOpen[`${M.id}:${c.n}`] ?? EV.store('ev-cites') === '1') ? ' open' : ''}><summary class="rp-evh sm" title="Click: show or hide the records this claim cites, each with the reviewer's tick and note">It cites ${c.evidence.length} record${c.evidence.length === 1 ? '' : 's'} <span class="mut">· ${c.evidence.map(e).join(', ')}</span></summary>${c.evidence.map(EV.evRow).join('')}</details>` : '<div class="rp-evs"><p class="sm mut">It cites nothing.</p></div>'}</div>`;
    const roles = M.claims.length > 0 && M.claims.every(q => q.role), of = r => M.claims.filter(q => q.role === r), says = r => EV.ROLES.find(q => q[0] === r)[2];
    const group = (r, none) => (of(r).length ? of(r).map(claim).join('') : `<p class="sm mut">${none}</p>`);
    const when = `<div class="rp-when"><div><h4>Holds when</h4>${lines(rep.holds_when)}</div><div><h4>Breaks when</h4>${lines(rep.breaks_when)}</div></div>`;
    const claims = !M.claims.length ? [blk('claims', 'Its claims', '<p class="sm mut">The report states no claims.</p>'), blk('but', 'But', when)]
      : roles ? [...(of('background').length ? [blk('diagnosis', EV.term('Diagnosis', 'Its diagnosis'), group('background', ''), `${EV.term('Claim', 'claims')} that ${says('background')}`)] : []),
          blk('because', 'Because', group('supports', 'No claim is given as a reason.'), `claims that ${says('supports')}`), blk('but', 'But', group('limits', 'No claim says when the recommendation would change.') + when, `claims that ${says('limits')}`)]
        : [blk('claims', 'Its claims', M.claims.map(claim).join(''), 'recorded before claims had roles'), blk('but', 'But', when)];
    const all = [rep.explanation, rep.holds_when, rep.breaks_when, ...(rep.claims || []).map(c => c.text)].flat().filter(Boolean).join('\n');
    const head = `<h2>${EV_ICON.report} ${EV.term('Final report', 'Final report')} <small>turn ${M.repRec ? M.repRec.turn : EV.nr} · ${EV.link((M.repRec || {}).id || '')}</small></h2>
      <p class="sm rp-sum" data-exact="1">${typeof rec === 'object' && rec ? `<span class="rp-chip"><b>${nchg}</b> of ${keys.length} settings changed</span>` : ''}${X ? `<span class="rp-chip"><b>${X.all.length + rpt.length}</b> measures expected</span>` : ''}<span class="rp-chip"><b>${M.claims.length}</b> claim${M.claims.length === 1 ? '' : 's'}${M.claims.length ? ': ' + EV.CLAIM_KINDS.map(([k, t]) => [M.claims.filter(q => q.kind === k).length, t]).filter(q => q[0]).map(([c, t]) => `${c} ${t}`).join(', ') : ''}</span></p>`;
    // what limits the result, and the settings that made no meaningful difference (reports since 2026-11-15; none in an earlier report)
    const short = !!M.supervised && typeof rep.holds_when === 'string' && !rep.holds_when.trim() && !rep.breaks_when.trim() && !Object.keys(rep.expected || {}).length;   // the short report of a supervised session
    const nd = short ? null : Array.isArray(rep.no_difference) ? rep.no_difference : null, hasLim = typeof rep.limit === 'string' && rep.limit.trim() !== '';
    const limit = hasLim || nd ? [blk('limit', 'What limits the result', `${hasLim ? lines(rep.limit) : ''}${nd ? `<p class="sm" id="rp-nodiff" data-exact="1">${nd.length ? `Made no meaningful difference, by its own list: ${nd.map(k => EV.label(k, (kn[k] || {}).meaning)).join(', ')}` : 'Its list of settings that made no meaningful difference is empty.'}</p>` : ''}`, 'why it is not better, in its own words')] : [];
    const B = [blk('aim', 'The aim', aim), blk('adjust', 'The proposed adjustment', adj), ...(short ? [] : [blk('expected', 'The expected result', exp)]), ...limit, ...(short ? claims.filter(q => q[0] !== 'but') : claims), blk('explanation', 'The explanation', lines(rep.explanation), 'in its own words'),
      ...(rep.open_questions ? [blk('open', 'Open questions', lines(rep.open_questions))] : []),
      blk('numbers', 'Its numbers against the measurements', EV.numCheck(all, M.sims) || '<p class="sm mut">No number in the report names or equals a measurement.</p>', 'compared by the page', 'rp-page')].map(box);
    return `<div class="rp" id="rp">${head}${B[0]}<div class="rp-two">${B[1]}${B[2]}</div>${B.slice(3).join('')}</div>`;
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

// A claim's citations and the review queue's list are folded until asked for (2026-11-17, the operator: hidden by default, for simplicity). Which are open
// is kept while the page is open (citations) or in the browser (the queue), so that drawing the page again does not close what the reader opened.
EV.citesOpen = EV.citesOpen || {};
document.getElementById('ev').addEventListener('toggle', ev => { const d = ev.target; if (!d || !d.matches) return;
  if (d.matches('details.rp-evs[data-cites]') && EV.M) { EV.citesOpen[`${EV.M.id}:${d.dataset.cites}`] = d.open; EV.store('ev-cites', d.open ? '1' : '0'); }
  else if (d.matches('details#q-fold')) EV.store('ev-qlist', d.open ? '1' : '0'); }, true);
