// What opens beside the flow charts: the trail above it, the work-log card of a turn, the brief; and the check of the
// model's numbers against the measurements. A test and a hypothesis are in evidence_test.js; the experiment panel and
// the result panel of a simulation in evidence_panels.js.
// ======================================================================================================
Object.assign(EV, {
  // a record id as a link that opens it beside the charts
  link(id) {
    const M = EV.M, r = M.byId[id], e = EV.e; if (id === 'brief') return `<a data-act="open" data-t="brief" data-id="brief">${EV_ICON.brief} brief</a>`;
    if (!r) return `<span class="mut">${e(id)}</span>`;
    const b = r.body || {}, ct = r.type === 'check' && M.tests.find(t => t.check && t.check.id === id);  // a check opens the test it belongs to
    const to = { hypothesis: ['hyp', id], verdict: ['hyp', b.for], drop: ['hyp', b.for], experiment: ['exp', id], check: ct ? ['test', ct.id] : ['exp', r.parent], simulation: ['sim', id], report: ['report', 'report'],
      evidence: M.simById[id] ? ['sim', id] : ['exp', b.experiment || r.parent] }[r.type] || ['log', r.turn];
    return `<a data-act="open" data-t="${to[0]}" data-id="${e(to[1])}" title="${e(r.type)}">${EV_ICON[r.type] || ''} ${e(id)}</a>`;
  },
  // where the opened item sits: Brief › Session › Turn › Experiment › Simulation, each part opens that level
  trail(sel) {
    const M = EV.M, e = EV.e, part = (t, id, text) => `<a data-act="open" data-t="${t}" data-id="${e(id)}">${text}</a>`;
    const sim = sel.t === 'sim' ? M.simById[sel.id] : null, hyp = sel.t === 'hyp' ? M.hypById[sel.id] : null;
    const own = hyp ? hyp.tests.map(q => M.testById[q]).filter(q => EV.seen(q.exp)).pop() : null, T = sel.t === 'test' ? M.testById[sel.id] : own;  // a hypothesis is shown with its test
    const simTests = sim ? (sel.test && M.testById[sel.test] ? [M.testById[sel.test]] : M.tests.filter(q => q.sims.includes(sim))) : T ? [T] : [];  // a simulation: the test it was opened from, else every test that names it
    const x = sim ? M.expById[sim.exp] : sel.t === 'exp' ? M.expById[sel.id] : T ? M.expById[T.exp] : null;
    const turn = sim ? sim.turn : x ? x.turn : hyp ? hyp.turn : sel.t === 'log' ? sel.id : sel.t === 'report' && M.repRec ? M.repRec.turn : null;
    const bits = [part('brief', 'brief', `${EV_ICON.brief} ${EV.term('Brief', 'Brief')}${M.brief ? ' ' + e(M.brief.id) : ''}`), part('session', M.id, `${EV.term('Session', 'Session')} ${e(M.id)}`)];
    if (sel.t !== 'brief' && sel.t !== 'session' && turn != null) bits.push(part('log', turn, `${EV_ICON.turn} ${EV.term('Turn', 'Turn')} ${turn}`));
    if (hyp && !T) bits.push(part('hyp', hyp.id, `${EV_ICON.hypothesis} ${EV.term('Hypothesis', 'Hypothesis')} ${e(hyp.id)}`));
    if (x) bits.push(part('exp', x.id, `${EV_ICON.experiment} ${EV.term('Experiment', 'Experiment')} ${e(x.id)}`));
    if (simTests.length) bits.push(simTests.map((q, i) => part('test', q.id, `${i ? '' : EV_ICON.test + ' ' + EV.term('Test', simTests.length > 1 ? 'Tests' : 'Test') + ' of '}${e(q.hyp)}`)).join(', '));
    if (sim) bits.push(part('sim', sim.id, `${EV_ICON.simulation} ${EV.term('Simulation', 'Simulation')} ${e(sim.id)}`));
    if (sel.t === 'report') bits.push(part('report', 'report', `${EV_ICON.report} ${EV.term('Final report', 'Final report')}`));
    return `<div class="trail">${bits.join(' › ')} <span class="noprint" style="float:right">${EV.copyBtn(sel)}</span></div>`;
  },
  stepOf(sel) {  // the step of the session flow at which the opened item was recorded (for the replay)
    const M = EV.M;
    if (sel.t === 'log') { const t = M.turns.find(q => q.n === sel.id); return t && t.steps.length ? t.steps[0].k : null; }
    if (sel.t === 'report') return M.repRec ? M.recStep[M.repRec.id] : null;
    if (sel.t === 'test') return M.testById[sel.id] ? M.recStep[M.testById[sel.id].exp] ?? null : null;  // a test is planned with its experiment
    return sel.t === 'brief' || sel.t === 'session' ? 0 : M.recStep[sel.id] ?? null;
  },

  detail() {
    const S = EV.s, M = EV.M, sel = S.sel, e = EV.e;
    if (!sel || sel.t === 'session') return `${sel ? EV.trail(sel) : ''}<h2>${EV.term('Session', 'Session')} ${e(M.id)} <small>click any item on the left to open it here</small></h2>${EV.summaryKV()}${EV.vcSession()}`;
    const k = EV.stepOf(sel);
    if (S.step != null && k != null && k > S.step) return `<p class="sm">The item opened here was recorded after step ${S.step + 1}; while the replay is at that step it is not shown.</p>`;
    const body = sel.t === 'log' ? EV.logCard(sel.id) : sel.t === 'hyp' ? EV.hypCard(sel.id) : sel.t === 'test' ? EV.testPanel(sel.id) : sel.t === 'exp' ? EV.expPanel(sel.id) : sel.t === 'sim' ? EV.simPanel(sel.id)
      : sel.t === 'brief' ? EV.briefCard() : sel.t === 'report' ? EV.reportBody() : '<p class="sm">Nothing to open.</p>';
    return EV.trail(sel) + body + EV.reviewBox(`${sel.t}:${sel.id}`);
  },

  // ---- the model's numbers against the measurements of the same experiment (TH_DATA.numbers, shared with the run page)
  numRows(M, text, sims) {  // each number of a text that names or equals a measurement: agrees, differs, or belongs to another experiment
    const mine = sims.filter(s => s.metrics), ids = new Set(mine.map(s => s.id)); if (!text || !mine.length) return [];
    const others = Object.fromEntries(mine.concat(M.sims.filter(s => s.metrics && !ids.has(s.id))).map(s => [s.id, s.metrics]));
    const show = (k, v) => (typeof v !== 'number' ? '–' : /_bps$/.test(k) || k === 'total' ? (v / 1e6).toLocaleString('en-US', { minimumFractionDigits: 3, maximumFractionDigits: 3 }) + ' Mbps' : /_frac$|_util$/.test(k) ? String(v) : v.toLocaleString('en-US'));
    const val = (mm, k) => (k === 'total' ? mm.udp_goodput_bps + mm.tcp_goodput_bps : mm[k]);  // the measurement shown is the one of the simulation it matched
    return TH_DATA.numbers(text, mine[0].metrics, others).map(q => ({ ...q, where: q.status === 'agrees' ? mine[0].id : q.other, status: q.status === 'other' ? (ids.has(q.other) ? 'agrees' : 'other') : q.status }))
      .map(q => (q.status !== 'differs' && q.where && others[q.where] ? { ...q, measured: show(q.key, val(others[q.where], q.key)) } : q));
  },
  numCheck(text, sims) {
    const rows = EV.numRows(EV.M, text, sims); if (!rows.length) return ''; const off = rows.filter(q => q.status === 'differs').length, e = EV.e;
    return `<details${off ? ' open' : ''}><summary>${off ? `${EV.warn(`${off} of ${rows.length}`)} numbers differ from the measurements` : `${EV.gkey('check')}${rows.length} number${rows.length === 1 ? '' : 's'} agree with the measurements`}</summary>
      <table><thead><tr><th data-by="model">it wrote</th><th>measure</th><th class="num" data-by="simulator">measured</th><th></th></tr></thead><tbody>${rows.map(q => `<tr><td>${e(q.written)}</td><td>${e(q.what)}</td><td class="num">${e(q.measured)}</td>
        <td>${q.status === 'agrees' ? `${EV.gkey('check')}${EV.link(q.where)}` : q.status === 'other' ? `from another experiment: ${EV.link(q.where)}` : EV.warn('differs')}</td></tr>`).join('')}</tbody></table></details>`;
  },
  simsOfTurn(n) { return EV.M.exps.filter(x => x.turn === n).flatMap(x => x.sims); },

  // ---- the work-log card: what the model had, what it decided, why in its own words
  logCard(n) {
    const M = EV.M, e = EV.e, t = M.turns.find(q => q.n === n); if (!t) return `<p class="sm">Turn ${e(n)}: ${EV.nr}.</p>`;
    if (n === 0) return `<h2>Before the first turn <small>the harness</small></h2><p>The harness showed the model the brief and ran the baseline: ${t.exp ? EV.link(t.exp.id) : EV.nr}.</p>`;
    const shown = t.added ? t.added.filter(id => M.byId[id] && (M.byId[id].type === 'malformed' || (M.byId[id].type === 'note' && M.byId[id].body.part))) : null;
    const had = `<div class="who" data-by="harness"><h3>1 · What it had</h3><div class="kv"><div><span>${EV.term('Simulation', 'simulations')} left</span><b>${t.left ?? EV.nr}</b></div><div><span>open hypotheses</span><b>${t.open ?? EV.nr}</b></div>
        <div><span>kind of turn</span><b>${t.rec ? e(t.last ? 'last turn (' + t.last + ')' : 'ordinary') : EV.nr}</b></div></div>
      <p class="sm">records added since its previous turn: ${t.added ? (t.added.length ? t.added.map(EV.link).join(', ') : 'none') : EV.nr}</p>
      <p class="sm">refusal notes it was shown: ${shown ? (shown.length ? shown.map(id => `${EV.link(id)} <span class="warnc">${e(M.byId[id].body.part || 'whole answer')}</span>: ${e(M.byId[id].body.reason || M.byId[id].body.error || '')}`).join('<br>') : 'none') : EV.nr}</p></div>`;
    const x = t.exp, fixed = x ? Object.keys(x.sims[0] ? x.sims[0].params : {}).filter(k => x.sims.every(s => JSON.stringify(s.params[k]) === JSON.stringify(x.sims[0].params[k]))) : [];
    const refused = t.malformed.map(m => `<li class="warnc" data-step="${M.recStep[m.id] ?? 0}">${EV_ICON.malformed} whole answer refused (${EV.link(m.id)}): ${e((m.body.refused || []).map(q => q.part + ': ' + q.reason).join(' | ') || m.body.error)}</li>`)
      .concat(t.refusals.map(m => `<li class="warnc" data-step="${M.recStep[m.id] ?? 0}">${EV_ICON.malformed} refused part (${EV.link(m.id)}) ${e(m.body.part)}: ${e(m.body.reason || m.body.text)}</li>`));
    const dec = [...t.verdicts.map(v => `<li>${EV.term('Verdict', 'verdict')} ${EV.link(v.id)} on ${EV.link(v.body.for)}: ${EV.verdictRes(v.body.result)}</li>`),
      ...t.drops.map(d => `<li>${EV_ICON.drop} dropped ${EV.link(d.body.for)}</li>`),
      ...t.hyps.map(h => `<li>new ${EV.term('Hypothesis', 'hypothesis')} ${EV.link(h.id)}: ${e(h.text)}${h.prediction ? `<br><span class="sm">prediction: ${e(h.prediction)}</span>` : ''}<br><span class="sm">follows from: ${h.follows ? h.follows.map(EV.link).join(', ') : EV.nr}</span></li>`),
      ...(x ? [`<li>${EV.term('Experiment', 'experiment')} ${EV.link(x.id)}: a batch of ${x.sims.length} simulations (${e(x.sims.map(s => s.label).join(', '))}); varied <b>${e(x.varied.join(', ') || 'not recorded')}</b>; fixed ${e(fixed.join(', ') || 'none')}; control <b>${e(x.control || 'not recorded')}</b>
          <ul>${M.tests.filter(T => T.exp === x.id).map(T => `<li>${EV.tlink(T)}: ${T.rule ? `<code>${e(T.rule)}</code>` : 'no decision rule'}${T.rival ? `<br><span class="sm">${EV.term('Rival', 'rival')}: ${e(T.rival)} · would give: ${e(T.rival_predicts || 'not recorded')}</span>` : ''}</li>`).join('') || `<li class="mut">no tests: it explores “${e(x.question || 'not recorded')}”</li>`}</ul></li>`] : []),
      ...t.requests.map(q => `<li>? asked for ${e(q.body.tool || 'information')} (${EV.link(q.id)})</li>`), ...(t.report ? [`<li data-step="${M.recStep[t.report.id] ?? 0}">the ${EV.link(t.report.id)} ${EV.term('Final report', 'final report')}</li>`] : []), ...refused];
    const why = [t.observations ? `<p><b>observations</b> ${e(t.observations)}</p>${EV.numCheck(t.observations, EV.simsOfTurn(n - 1))}` : `<p class="sm">observations: ${EV.nr}</p>`,
      ...t.verdicts.map(v => { const h = M.hypById[v.body.for], xs = h ? h.exps.map(id => M.expById[id]).filter(q => q.turn < n) : [], sims = xs.length ? xs[xs.length - 1].sims : [];
        return `<p><b>${v.id} because</b> ${e(v.body.because || '')}</p>${EV.numCheck(v.body.because, sims)}<p class="sm"><b>next</b> ${e(v.body.next || EV.nr)}</p>`; })];
    return `<h2>${EV_ICON.turn} Work log, turn ${n} <small>built from the model's recorded answer and the harness's turn record</small></h2>${had}
      <div class="who" data-by="model"><h3>2 · What it decided</h3><ul style="margin:0;padding-left:18px">${dec.join('') || '<li class="mut">nothing usable</li>'}</ul></div>
      <div class="who" data-by="model"><h3>3 · Why, in its own words</h3>${why.join('')}</div>`;
  },

  briefCard() {
    const M = EV.M, e = EV.e, b = M.brief, x0 = M.exps.find(x => x.by === 'harness');
    if (!b) return `<h2>${EV_ICON.brief} ${EV.term('Brief', 'Brief')}</h2><p class="sm">${EV.nr}: this session was made before briefs existed.</p>`;
    const kv = o => `<table><tbody>${Object.entries(o || {}).map(([k, v]) => `<tr><td>${e(k)}</td><td>${e(typeof v === 'object' ? Object.entries(v).map(([a, c]) => `${a}: ${Array.isArray(c) ? c.join(', ') : c}`).join(' · ') : v)}</td></tr>`).join('')}</tbody></table>`;
    return `<h2>${EV_ICON.brief} ${EV.term('Brief', 'Brief')} ${e(b.id)} <small>written by the ${EV.term('Operator', 'operator')}</small></h2><p>${e(b.task || '')}</p>
      <h3>Fixed settings</h3>${kv(b.system)}<h3>Knobs and ranges</h3>${kv(b.knobs)}<h3>Goal</h3><p>${e(EV.goal(b.goal))}</p><h3>Limits</h3>${kv(b.limits)}
      <p class="sm">the baseline the harness ran before the first turn: ${x0 ? EV.link(x0.id) + ' · ' + x0.sims.map(s => EV.link(s.id)).join(', ') : EV.nr}</p>`;
  },
});
