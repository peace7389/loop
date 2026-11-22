// What opens beside the flow charts: the trail above it, the work-log card of a turn, the brief; and the check of the
// model's numbers against the measurements. A test and a hypothesis are in evidence_test.js; the experiment panel and
// the result panel of a simulation in evidence_panels.js.
// ======================================================================================================
Object.assign(EV, {
  // A record's name is a letter and a number: the letter says what kind of record it is, the number is its order among its kind in this session.
  // [the kind in plain words, what such a record is, who writes it]
  ID_SAYS: { F: ['finding', 'one thing the results did not explain, raised by the researcher or the supervisor; it stays on the researcher’s list until it is closed', 'model'],
             A: ['decision on a finding', 'the researcher’s decision on a finding: worked on, parked, closed or the same as another', 'model'],
             Z: ['tally of the findings', 'at the end, for each finding: how it ended, how long it stayed open, and what looked at it', 'harness'], Y: ['guess of why', 'the AI’s informed guess of why a result came out as it did; a hypothesis comes from one', 'model'], J: ['judge’s reading', 'a second model call read a guess and the hypothesis said to come from it, and said whether testing the one would tell if the other is true; it can be wrong', 'harness'], K: ['guess looked at again', 'the AI looked at an earlier guess again in the light of later results', 'model'],
    H: ['hypothesis', 'a statement of the AI that a test can refute', 'model'], X: ['experiment', 'one batch of simulations', 'model'], S: ['simulation', 'one run of ns-3', 'simulator'],
    E: ['result table', 'the measures of one experiment’s simulations, as the harness showed them to the AI', 'harness'], C: ['check', 'the harness’s check of one decision rule against the measurements', 'harness'],
    V: ['verdict', 'the AI’s judgement of a hypothesis', 'model'], N: ['note', 'a note the harness wrote into the record: most often which part of an answer it refused, and why', 'harness'],
    Q: ['request', 'a question the AI put to one of the harness’s tools', 'model'], T: ['tool result', 'what a tool answered to a request of the AI', 'harness'], U: ['turn record', 'what the AI had when a turn began', 'harness'], R: ['final report', 'the AI’s answer', 'model'] },
  // a record id as a link that opens it beside the charts
  link(id) {
    const M = EV.M, r = M.byId[id], e = EV.e; if (id === 'brief') return `<a data-act="open" data-t="brief" data-id="brief">${EV_ICON.brief} brief</a>`;
    if (!r) return `<span class="mut">${e(id)}</span>`;
    const b = r.body || {}, ct = r.type === 'check' && M.tests.find(t => t.check && t.check.id === id);  // a check opens the test it belongs to
    const to = { why: ['why', id], rethink: ['why', b.for], hypothesis: ['hyp', id], verdict: ['hyp', b.for], drop: ['hyp', b.for], experiment: ['exp', id], check: ct ? ['test', ct.id] : ['exp', r.parent], simulation: ['sim', id], report: ['report', 'report'],
      evidence: M.simById[id] ? ['sim', id] : ['exp', b.experiment || r.parent], finding: ['finding', id], decision: ['finding', b.for] }[r.type] || ['log', r.turn];
    // a note, a request, a tool's result, a turn's record, a result table: their names ("N3", "E2") say nothing by themselves, so a box says what the letter stands for and what the record holds
    const box = ['note', 'request', 'result', 'turn', 'evidence'].includes(r.type);
    return `<a data-act="open" data-t="${to[0]}" data-id="${e(to[1])}"${r.type === 'hypothesis' ? ` data-wd="h:${e(id)}"` : r.type === 'why' || r.type === 'rethink' ? ` data-wd="y:${e(to[1])}"` : box ? ` data-wd="r:${e(id)}"` : ` title="${e((EV.ID_SAYS[(/^[A-Z]+/.exec(id) || [''])[0]] || [r.type])[0])}"`}>${EV_ICON[r.type] || ''} ${e(id)}</a>`;
  },
  // where the opened item sits: Brief › Session › Turn › Experiment › Simulation, each part opens that level
  trail(sel) {
    const M = EV.M, e = EV.e, part = (t, id, text) => `<a data-act="open" data-t="${t}" data-id="${e(id)}">${text}</a>`;
    const sim = sel.t === 'sim' ? M.simById[sel.id] : null, hyp = sel.t === 'hyp' ? M.hypById[sel.id] : null;
    const own = hyp ? hyp.tests.map(q => M.testById[q]).filter(q => EV.seen(q.exp)).pop() : null, T = sel.t === 'test' ? M.testById[sel.id] : own;  // a hypothesis is shown with its test
    const simTests = sim ? (sel.test && M.testById[sel.test] ? [M.testById[sel.test]] : M.tests.filter(q => q.sims.includes(sim))) : T ? [T] : [];  // a simulation: the test it was opened from, else every test that names it
    const x = sim ? M.expById[sim.exp] : sel.t === 'exp' ? M.expById[sel.id] : T ? M.expById[T.exp] : null;
    const why = sel.t === 'why' ? (M.whyById || {})[sel.id] : null;
    const turn = why ? why.turn : sim ? sim.turn : x ? x.turn : hyp ? hyp.turn : sel.t === 'log' ? sel.id : sel.t === 'report' && M.repRec ? M.repRec.turn : null;
    const bits = [part('brief', 'brief', `${EV_ICON.brief} ${EV.term('Brief', 'Brief')}${M.brief ? ' ' + e(M.brief.id) : ''}`), part('session', M.id, `${EV.term('Session', 'Session')} ${e(M.id)}`)];
    if (sel.t !== 'brief' && sel.t !== 'session' && turn != null) bits.push(part('log', turn, `${EV_ICON.turn} ${EV.term('Turn', 'Turn')} ${turn}`));
    if (why) bits.push(part('why', why.id, `Guess of why ${e(why.id)}`));
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
    if (!sel || sel.t === 'session') return `${sel ? EV.trail(sel) : ''}<h2>${EV.term('Session', 'Session')} ${e(M.id)} <small>its summary</small></h2>${EV.summaryKV()}${EV.vcSession()}`;
    const k = EV.stepOf(sel);
    if (S.step != null && k != null && k > S.step) return `<p class="sm">The item opened here was recorded after step ${S.step + 1}; while the replay is at that step it is not shown.</p>`;
    const body = sel.t === 'log' ? EV.logCard(sel.id) : sel.t === 'hyp' ? EV.hypCard(sel.id) : sel.t === 'why' ? EV.whyCard(sel.id) : sel.t === 'test' ? EV.testPanel(sel.id) : sel.t === 'exp' ? EV.expPanel(sel.id) : sel.t === 'sim' ? EV.simPanel(sel.id)
      : sel.t === 'brief' ? EV.briefCard() : sel.t === 'report' ? EV.reportBody() : sel.t === 'meas' && EV.measCard ? EV.measCard(sel.id) : sel.t === 'finding' && EV.fndCard ? EV.fndCard(sel.id) : '<p class="sm">Nothing to open.</p>';
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
    return `<details${off ? ' open' : ''}><summary>${off ? `${EV.warn(`${off} of the ${rows.length}`)} number${rows.length === 1 ? '' : 's'} in this text differ${off === 1 ? 's' : ''} from the measurements` : `${EV.gkey('check')}${rows.length === 1 ? 'the 1 number in this text matches' : `the ${rows.length} numbers in this text match`} the measurements`}</summary>
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
      .concat((() => { const li = m => `<li class="warnc" data-step="${M.recStep[m.id] ?? 0}">${EV_ICON.malformed} refused part (${EV.link(m.id)}) ${e(m.body.part)}: ${e(m.body.reason || m.body.text)}</li>`;
        // as in the notebook: one answer that judges again what was judged ("H1 is not an open hypothesis", seventeen times) is one line that says how many, what and why
        const shape = m => `${m.body.part}|${m.body.reason || m.body.text}`.replace(/\bH\d+\b/g, 'H#'), by = {}; t.refusals.filter(m => EV.seen(m.id)).forEach(m => { (by[shape(m)] = by[shape(m)] || []).push(m); });
        const done = new Set(); return t.refusals.map(m => { const g = EV.seen(m.id) ? by[shape(m)] : null; if (!g || g.length < 3) return li(m); if (done.has(shape(m))) return ''; done.add(shape(m));
          const ids = g.map(q => (/\bH\d+\b/.exec(q.body.part) || [])[0]).filter(Boolean), again = g.every(q => /verdict for H\d+/.test(q.body.part)) && /is not an open hypothesis/.test(g[0].body.reason || '');
          return `<li class="lg-refs" data-n="${g.length}" data-step="${Math.min(...g.map(q => M.recStep[q.id] ?? 0))}"><details><summary><span class="warnc">${EV_ICON.malformed} <b>${g.length} parts of this answer were refused, for one reason:</b></span> ${again ? `it gave verdicts again for ${e(ids[0])}${ids.length > 1 ? ' to ' + e(ids[ids.length - 1]) : ''}, which already had theirs; the earlier verdicts stand` : `“<span data-own="harness">${e(g[0].body.part)}</span>” and ${g.length - 1} more like it: <span data-own="harness">${e(g[0].body.reason || g[0].body.text)}</span>`}. <span class="sm">Not an error of the system: the harness left these parts out and used the rest of the answer${t.report ? ', the final report' : ''}.</span></summary><ul>${g.map(li).join('')}</ul></details></li>`; }); })());
    // a supervised session: the verdicts of the turn are the supervisor's and stand in a part of their own, with the ground of each and what it was shown
    const bySup = r => EV_DATA.by(r) === 'supervisor', own = t.verdicts.filter(v => !bySup(v)), supRecs = M.recs.filter(r => r.turn === n && bySup(r) && EV.seen(r.id)), shownTo = (EV.files || {}).supervisor || {};
    const saw = r => (shownTo[r.id] && shownTo[r.id].shown ? `<details class="sup-saw" data-saw="${e(r.id)}"><summary class="sm">what the supervisor was shown for this</summary><pre class="sup-pre">${e(shownTo[r.id].shown)}</pre></details>` : '');
    const supLine = r => { const b = r.body, D = EV.SUP_DEFECT;
      if (r.type === 'verdict') return `<li data-sup="${e(r.id)}" data-step="${M.recStep[r.id] ?? 0}"><b>${b.after ? 'second look after the objection ' + EV.link(b.after) : 'ruling'}</b> ${EV.link(r.id)} on ${EV.link(b.for)}: ${EV.verdictRes(b.result)}${b.after ? ` · ${b.stands ? 'the ruling stands' : 'the ruling is changed'}` : ''}${b.fair === false ? ` · not a fair test: ${e(D[b.defect] || b.defect || '')}` : ''}<br><span data-own="supervisor">${e(b.because || '')}</span>${b.shows ? `<br><span class="sm">the numbers show: ${e(b.shows)}</span>` : ''}${b.next ? `<br><span class="sm">a fair test: ${e(b.next)}</span>` : ''}${b.answer ? `<br><span class="sm">to the objection: ${e(b.answer)}</span>` : ''}${b.doubt_if ? `<br><span class="sm">before the simulations it said it would doubt the test if: ${e(b.doubt_if)}</span>` : ''}${b.changed_by_harness ? `<br><span class="sm warnc">changed by the harness: ${e(b.changed_by_harness)}</span>` : ''}${saw(r)}</li>`;
      if (b.gate === 'ground') return `<li data-sup="${e(r.id)}" data-step="${M.recStep[r.id] ?? 0}"><b>the guess ${b.for ? EV.whyLink(b.for) : `“${e(String(b.guess || '').slice(0, 140))}”`} read against its records</b>: ${b.decision === 'approved' ? 'sound' : b.decision === 'sent_back' ? '<span class="warnc">not accepted</span>' : '<span class="warnc">accepted on its second statement, it still objects</span>'}${b.defect !== 'none' ? ` · ${e(D[b.defect] || b.defect)}` : ''}<br><span class="sm">the records show: <span data-own="supervisor">${e(b.records_show || '')}</span></span><br><span data-own="supervisor">${e(b.because || '')}</span>${b.nearest_earlier && b.nearest_earlier !== 'none' ? `<br><span class="sm">nearest earlier: ${e(b.nearest_earlier)}</span>` : ''}${saw(r)}</li>`;
      return `<li data-sup="${e(r.id)}" data-step="${M.recStep[r.id] ?? 0}"><b>the test of ${EV.link(b.for)} reviewed before any simulation</b>: ${b.decision === 'approved' ? 'approved' : `<span class="warnc">${e(EV.supDecision[b.decision] || b.decision)}</span>`}${b.defect !== 'none' ? ` · ${e(D[b.defect] || b.defect)}` : ''}<br><span data-own="supervisor">${e(b.because || '')}</span><br><span class="sm">its rival: ${e(b.rival || '')} (under it the rule would ${b.rival_outcome === 'held' ? 'hold too' : b.rival_outcome === 'failed' ? 'fail' : 'come out in a way it could not tell'})</span><br><span class="sm">it would doubt the test if: ${e(b.doubt_if || '')}</span>${saw(r)}</li>`; };
    const supPart = M.supervised ? `<div class="who" data-by="supervisor" id="lg-sup"><h3>4 · What the supervisor said, and on what ground</h3>${supRecs.length ? `<ul style="margin:0;padding-left:18px">${supRecs.map(supLine).join('')}</ul>` : '<p class="sm mut">nothing in this turn: no new guess, no test and no objection came before it</p>'}<p class="sm">The supervisor is a second AI, asked apart from the researcher. It is shown the guess, the hypothesis, the decision rules, the planned simulations and the measured numbers, never the researcher’s observations or reasons.</p></div>` : '';
    const objs = M.recs.filter(r => r.turn === n && r.type === 'objection' && EV.seen(r.id));
    const dec = [...objs.map(o => `<li data-step="${M.recStep[o.id] ?? 0}">${EV_ICON.objection} objects to the ruling ${EV.link(o.body.to)} on ${EV.link(o.body.for)}: <span data-own="model">${e(o.body.because)}</span></li>`), ...own.map(v => `<li>${EV.term('Verdict', 'verdict')} ${EV.link(v.id)} on ${EV.link(v.body.for)}: ${EV.verdictRes(v.body.result)}${EV.rests((M.hypById[v.body.for] || {}).verdict && M.hypById[v.body.for].verdict.id === v.id ? M.hypById[v.body.for].verdict : null)}</li>`),
      ...t.drops.map(d => `<li>${EV_ICON.drop} dropped ${EV.link(d.body.for)}</li>`),
      ...t.hyps.map(h => `<li>new ${EV.term('Hypothesis', 'hypothesis')} ${EV.link(h.id)}: ${e(h.text)}${h.question ? `<br><span class="sm">its question: ${e(h.question)}</span>` : ''}${h.prediction ? `<br><span class="sm">prediction: ${e(h.prediction)}</span>` : ''}<br><span class="sm">follows from: ${h.follows ? h.follows.map(EV.link).join(', ') : EV.nr}</span></li>`),
      ...(x ? [`<li>${EV.term('Experiment', 'experiment')} ${EV.link(x.id)}: a batch of ${x.sims.length} simulations (${e(x.sims.map(s => s.label).join(', '))}); varied <b>${e(x.varied.join(', ') || 'not recorded')}</b>; fixed ${e(fixed.join(', ') || 'none')}; control <b>${e(x.control || 'not recorded')}</b>
          <ul>${M.tests.filter(T => T.exp === x.id).map(T => `<li>${EV.tlink(T)}: ${T.rule ? EV.ruleRead(T) : 'no decision rule'}${T.rival ? `<br><span class="sm">${EV.term('Rival', 'rival')}: ${e(T.rival)} · would give: ${e(T.rival_predicts || 'not recorded')}</span>` : ''}</li>`).join('') || `<li class="mut">no tests: it explores “${e(x.question || 'not recorded')}”</li>`}</ul></li>`] : []),
      ...t.requests.map(q => `<li>? asked for ${e(q.body.tool || 'information')} (${EV.link(q.id)})</li>`), ...(t.report ? [`<li data-step="${M.recStep[t.report.id] ?? 0}">the ${EV.link(t.report.id)} ${EV.term('Final report', 'final report')}</li>`] : []), ...refused];
    const why = [t.observations ? `<p><b>observations</b> ${e(t.observations)}</p>${EV.numCheck(t.observations, EV.simsOfTurn(n - 1))}` : `<p class="sm">observations: ${EV.nr}</p>`,
      ...own.map(v => { const h = M.hypById[v.body.for], xs = h ? h.exps.map(id => M.expById[id]).filter(q => q.turn < n) : [], sims = xs.length ? xs[xs.length - 1].sims : [];
        return `<p><b>${v.id} because</b> ${e(v.body.because || '')}</p>${EV.numCheck(v.body.because, sims)}<p class="sm"><b>next</b> ${e(v.body.next || EV.nr)}</p>`; })];
    // the turn that is being worked on: what is happening now stands first, and while its reply is being written the two parts the reply will fill say so
    const live = EV.liveNowCard ? EV.liveNowCard(n) : '', writing = !!live && EV.liveNow().phase === 'reply' && !dec.length, wait = '<span class="mut" data-wait-reply="1">not there yet: the reply is being written</span>';
    return `<h2>${EV_ICON.turn} Work log, turn ${n} <small>built from the model's recorded answer and the harness's turn record</small></h2>${live}${had}
      <div class="who" data-by="model"><h3>2 · What it decided</h3><ul style="margin:0;padding-left:18px">${dec.join('') || (writing ? `<li style="list-style:none;margin-left:-18px">${wait}</li>` : '<li class="mut">nothing usable</li>')}</ul></div>
      <div class="who" data-by="model"><h3>3 · Why, in its own words</h3>${writing ? `<p class="sm">${wait}</p>` : why.join('')}</div>${supPart}`;
  },

  briefCard() {
    const M = EV.M, e = EV.e, b = M.brief, x0 = M.exps.find(x => x.by === 'harness');
    if (!b) return `<h2>${EV_ICON.brief} ${EV.term('Brief', 'Brief')}</h2><p class="sm">${EV.nr}: this session was made before briefs existed.</p>`;
    // a setting by its plain name (what it means is in the name's box, and is not repeated here); a knob's range in words, then where the session starts
    const fixed = `<table data-exact="1" id="bc-fixed"><tbody>${Object.entries(b.system || {}).map(([k, v]) => `<tr data-k="${e(k)}"><td>${EV.label(k)}</td><td>${e(EV.setVal(k, v))}</td></tr>`).join('')}</tbody></table>`;
    const knobs = `<table data-exact="1" id="bc-knobs"><tbody>${Object.entries(b.knobs || {}).map(([k, s]) => `<tr data-k="${e(k)}"><td>${EV.label(k, s.meaning)}</td><td>${e(EV.setRange(k, s))}</td><td class="sm">from ${e(EV.setVal(k, s.default))}</td></tr>`).join('')}</tbody></table>`;
    const lim = b.limits || {}, limits = `<p id="bc-limits">${[lim.simulations != null ? `<b>${e(lim.simulations)}</b> simulations in all` : '', lim.simulations_per_experiment != null ? `<b>${e(lim.simulations_per_experiment)}</b> in one turn` : '', ...Object.entries(lim).filter(([k]) => !['simulations', 'simulations_per_experiment'].includes(k)).map(([k, v]) => `${e(k)} ${e(v)}`)].filter(Boolean).join(' · ') || EV.nr}</p>`;
    const g = b.goal || {}, goal = g.kind === 'given' && EV.aimWords(g) ? `Find ${EV.aimWords(g)}.${g.tolerance != null ? ` <span class="sm">· tolerance ${e(g.tolerance)}%: two results closer than this count as equal</span>` : ''}` : g.kind === 'open' ? 'Open: the AI chooses its own aim and has to justify it.' : e(EV.goal(b.goal));
    // The aim stands first, in a box of its own colour: the board's aim box opens this card, and what a reader then wants is the aim, whole. A given aim: the brief's,
    // set by the operator. An open aim: that the brief left it open, and, once the final report is recorded (by the step the page is at), the aim the AI chose in
    // its own words, uncut, with when it stated it (at the end: the harness asks for the aim only in the final report) and a link to that report.
    const rep = g.kind === 'open' && EV.repNow ? EV.repNow() : null, chose = rep && rep.goal ? rep.goal : null, by = (who, t) => `<span class="st-by" data-by="${who}"><i class="sw"></i>${t}</span>`;
    const aim = `<div class="bc-aim" id="bc-aim" data-aim="${e(g.kind || '')}"><h3>${EV.flag()}The aim</h3><p id="bc-goal">${goal}${g.kind === 'given' ? ' ' + by('operator', 'set by the operator') : ''}</p>${g.kind !== 'open' ? '' : chose
      ? `<p class="bc-who">${by('model', 'chosen by the AI')} <span class="aim-when">· stated <b>at the end</b>, in its ${M.repRec ? EV.link(M.repRec.id) : ''} final report${M.repRec ? ` (turn ${e(M.repRec.turn)})` : ''}: the harness asks for the aim only there</span></p><div id="bc-chose">${EV.repLines(chose)}</div>`
      : `<p class="sm mut" id="bc-chose" data-none="1">${M.ended && (EV.s.step == null || EV.s.step >= M.steps.length - 1) ? 'It stated no aim: the session ended without a final report.' : 'It has not stated its aim yet: it does so at the end, in its final report.'}</p>`}</div>`;
    return `<h2>${EV_ICON.brief} ${EV.term('Brief', 'Brief')} ${e(b.id)} <small>written by the ${EV.term('Operator', 'operator')}</small></h2>${aim}
      <h3>The task, as the AI was given it <small id="bc-task-by" class="sm" style="font-weight:400">${b.task && b.task === EV.taskText(b) ? 'written by the harness from the aim and the settings the AI may change' : 'written by hand in the brief'}</small></h3><p id="bc-task" data-own="${b.task && b.task === EV.taskText(b) ? 'harness' : 'operator'}">${e(b.task || '')}</p>
      <h3>Fixed by the operator</h3>${fixed}<h3>The AI may change</h3>${knobs}<h3>The limits</h3>${limits}
      <p class="sm">the baseline the harness ran before the first turn: ${x0 ? EV.link(x0.id) + ' · ' + x0.sims.map(s => EV.link(s.id)).join(', ') : EV.nr}</p>`;
  },
});
