// The test panel: one hypothesis put to one decision rule. View 3 (the flow chart of the test), the line that says
// which experiment it was run in and with which other tests, the chart of the measure its rule judges, the simulations
// the rule names with the settings that differ between them highlighted, the check and the verdict.
// A hypothesis opened from the map shows the same body for each of its tests.
// ======================================================================================================
Object.assign(EV, {
  // the order of a test, from the records' times: the decision rule (recorded with its experiment), then the simulations it names
  // (a simulation returned from an earlier one first ran when that one did), then the check
  orderLine(T, simK, kc) {
    const M = EV.M, e = EV.e, x = M.expById[T.exp], tm = EV.time, first = s => { const o = s.same_as && M.simById[s.same_as]; return o ? o.ts : s.ts; }; if (!T.rule || !x.ts) return '';
    const ts = T.sims.map(first).filter(Boolean).sort(), early = T.sims.filter(s => first(s) && first(s) < x.ts);
    return `<p class="sm" id="t-order" data-step="${Math.max(simK, kc)}" data-rule="${e(x.ts)}" data-first="${e(ts[0] || '')}" data-before="${early.length ? '0' : '1'}"><b>order</b> · the decision rule was recorded at ${e(tm(x.ts))}${ts.length ? `, ${early.length ? 'after' : 'before'} ${early.length ? `${early.length} of ` : ''}its ${T.sims.length} simulation${T.sims.length === 1 ? '' : 's'} (${ts.length > 1 && ts[0] !== ts[ts.length - 1] ? `first run ${e(tm(ts[0]))} to ${e(tm(ts[ts.length - 1]))}` : `run at ${e(tm(ts[0]))}`})` : ''}${
      early.length ? `: ${e(early.map(s => s.id + (s.same_as ? ', returned from ' + s.same_as : '')).join('; '))} had already run` : ''}${T.check && T.check.ts ? `; the check was made at ${e(tm(T.check.ts))}` : ''}</p>`;
  },
  testBody(T) {
    const M = EV.M, S = EV.s, e = EV.e, x = M.expById[T.exp], others = M.tests.filter(q => q.exp === T.exp && q !== T), wide = !!S.wide[T.id];
    const simK = Math.max(M.recStep[x.id] ?? 0, ...T.sims.map(s => M.recStep[s.id] ?? 0)), kc = T.check ? M.recStep[T.check.id] ?? simK : simK, v = T.verdict, kv = v ? M.recStep[v.id] ?? kc : kc;
    const vary = EV.varying(T.sims), same = [...new Set(T.sims.flatMap(s => Object.keys(s.params)))].filter(k => !vary.includes(k)), ms = EV.measuresOf(T.rule);
    const show = (k, val) => { const [u, f] = EV.unit(k); return typeof val !== 'number' ? '–' : (+f(val).toPrecision(7)).toLocaleString('en-US') + (u ? ' ' + u : ''); };
    // one row per simulation; one column per setting that differs and per measure the rule judges: the table grows downward, not sideways
    const table = !T.sims.length ? `<p class="sm">the simulations this rule names: ${EV.nr}</p>` : `<table class="tt" id="tt-${e(T.id)}"><thead><tr><th>simulation</th>${vary.map(k => `<th class="num">${e(TH_DATA.KNOB[k] || k)} <span class="warnc" title="differs between these simulations">≠</span></th>`).join('')}${ms.map(k => `<th class="num">${e(TH_DATA.PLAIN[k] || k)}</th>`).join('')}</tr></thead><tbody>
        ${T.sims.map(s => `<tr data-sim="${e(s.id)}"${S.inset && S.inset.id === s.id ? ' class="sel"' : ''}><td><a data-act="open" data-t="sim" data-id="${e(s.id)}" data-test="${e(T.id)}">${EV.gkey(s.same_as ? 'sim-returned' : 'sim')}${e(s.id)}</a> ${e(s.label)}${s.label === T.control ? ' <span class="mut">· control</span>' : ''}</td>${vary.map(k => `<td class="num dv">${e(s.params[k] ?? '–')}</td>`).join('')}${ms.map(k => `<td class="num">${show(k, (s.metrics || {})[k])}</td>`).join('')}</tr>`).join('')}</tbody></table>
        <p class="sm">${vary.length ? 'In bold: the settings that differ between them. ' : T.sims.length > 1 ? 'These simulations were given the same settings. ' : ''}The same in all: ${e(same.map(k => `${k} ${T.sims[0].params[k]}`).join(' · ') || 'nothing')}.</p>`;
    // The test in full, under the headings of its notebook card (Plan, Expected, Result, Verdict, So next), each said once and never cut; then its
    // chart; then, folded, the exact records (the rule as written, the check's raw numbers, the times); last the same test as one picture, whose
    // boxes shorten long texts (each stands in full above).
    const sec = (k, body, step, own) => `<div class="td-l" data-td="${k === 'Verdict' ? 'conclusion' : k.toLowerCase().replace(' ', '-')}"${step != null ? ` data-step="${step}"` : ''}><span class="td-k">${k}</span><div class="td-v"${own ? ` data-own="${own}"` : ''}>${body}</div></div>`, fol = EV.followers(T), kf = Math.max(kv, ...fol.ids.map(id => M.recStep[id] ?? 0));
    const ins = S.sel && S.sel.t === 'test' && S.sel.id === T.id && S.inset && S.inset.t === 'sim' && x.sims.some(q => q.id === S.inset.id) && EV.seen(S.inset.id) ? S.inset.id : null;  // a simulation opened inside this test
    const sameText = same.map(k => `${EV.LABEL[k] || k} ${EV.setVal(k, T.sims[0].params[k])}`).join(' · ') || 'nothing';
    const here = S.sel && S.sel.t === 'test' && S.sel.id === T.id ? S.inset : null, insHyp = here && here.t === 'hyp' && M.hypById[here.id] && EV.seen(here.id) ? here.id : null, insV = here && here.t === 'verdict' && v && EV.seen(v.id);
    const inset = ins ? `<div class="td-inset" id="td-inset" data-sim="${e(ins)}"><p class="sm td-inset-h">One simulation of this test, opened here <button class="cl noprint" data-act="insetoff" style="float:right">close</button></p>${EV.simPanel(ins)}</div>`
      : insHyp ? `<div class="td-inset" id="td-inset" data-hyp="${e(insHyp)}"><p class="sm td-inset-h">The hypothesis that followed, shown here <button class="cl noprint" data-act="insetoff" style="float:right">close</button></p>${EV.hypPop(insHyp).replace(/<p class="sm hp-foot">[^]*?<\/p>/, '')}<p class="sm"><a data-act="open" data-t="hyp" data-id="${e(insHyp)}">open ${e(insHyp)} in this pane instead</a></p></div>`
      : here && here.t === 'rule' && here.id === T.id && T.rule ? `<div class="td-inset" id="td-inset" data-part="rule"><p class="sm td-inset-h">The decision rule, in full <button class="cl noprint" data-act="insetoff" style="float:right">close</button></p><p>${EV.ruleRead(T)}</p>${EV.ruleBars(T, 0, !(T.check && EV.seen(T.check.id) && !T.check.void))}${T.rival ? `<p class="sm">${EV.term('Rival', 'rival')}: <span data-own="model">${e(T.rival)}</span> · under the rival the rule would have ${e(T.rival_predicts || 'not recorded')}</p>` : ''}<p class="sm">as it was written: <code>${e(T.rule)}</code></p></div>`
      : here && here.t === 'check' && here.id === T.id && T.check && EV.seen(T.check.id) ? `<div class="td-inset" id="td-inset" data-part="check"><p class="sm td-inset-h">Did the rule hold? The check, in full <button class="cl noprint" data-act="insetoff" style="float:right">close</button></p><p>${EV.checkRead(T)}</p>${EV.ruleBars(T)}<p class="sm">the harness's own numbers: ${e(T.check.id)} · <code>${e(T.check.numbers)}</code></p></div>`
      : insV ? `<div class="td-inset" id="td-inset" data-verdict="${e(v.id)}"><p class="sm td-inset-h">The verdict, in full <button class="cl noprint" data-act="insetoff" style="float:right">close</button></p><p>${e(v.id)} ${EV.verdictRes(v.result)}, given in turn ${v.turn}</p><p data-own="model">${e(v.because || '')}</p><p class="sm">next: <span data-own="model">${e(v.next || 'not recorded')}</span></p></div>` : '';
    // The chain of boxes (hypothesis, rule, simulations, check, verdict, next) is a picture of what the sections under it say in full: it is folded, and the
    // browser remembers when a reader opens it ("ev-chain"). A part opened from it (the rule or the check in full) opens it.
    return `<details class="td-fold td-chain noprint" id="td-chain"${EV.store('ev-chain') === '1' || inset ? ' open' : ''}><summary><span class="td-fold-s">the test as a chain of boxes</span> <span class="sm">hypothesis, decision rule, simulations, check, verdict, next step: a picture of what stands below</span></summary>${EV.viewTest(T)}${inset}</details>
      <div class="td" id="td-${e(T.id)}">
        ${sec('Plan', `${table.replace(/<p class="sm">[^]*?<\/p>\s*$/, '')}${T.sims.length ? `<details class="td-fold" data-exact="1"><summary>${vary.length ? `only ${vary.map(k => TH_DATA.KNOB[k] || k).join(', ')} differ${vary.length === 1 ? 's' : ''} between them` : T.sims.length > 1 ? 'these simulations were given the same settings' : 'its settings'} · <span class="td-fold-s">the ${same.length} other settings</span></summary><p class="sm">The same in all: ${e(sameText)}.</p></details>` : ''}<p class="sm td-with">run in ${EV.link(x.id)} (turn ${x.turn})${others.length ? ' together with tests of ' + others.map(q => EV.tlink(q, e(q.hyp))).join(', ') : ', the only test in it'}</p>`, simK)}
        ${sec('Expected', `${T.rule ? EV.ruleList(T) : EV.ruleRead(T)}${T.rival ? `<p class="sm">${EV.term('Rival', 'rival')}: <span data-own="model">${e(T.rival)}</span> · under the rival the rule would have ${e(T.rival_predicts || 'not recorded')}</p>` : ''}`, M.recStep[x.id] ?? 0)}
        ${sec('Result', T.check ? `${(bars => (bars ? `<p class="td-res"><span class="hp-badge ck-${T.check.void ? 'void' : e(T.check.result)}" data-rr="check" title="${e(T.check.numbers == null ? '' : T.check.numbers + ' : ' + (T.check.recorded || T.check.result))}">${EV.checkRes(T.check)}</span> <span class="sm">the rule as a whole · ${e(T.check.id)}, checked by the harness</span></p>` : EV.checkRead(T)))(EV.ruleBars(T))}${EV.closeNote(T)}${T.check.void ? `<p class="void-note" data-void="${e(T.check.id)}">${EV.gkey('void')}<b>${EV.VOID}.</b> ${e(T.check.same.join(', '))} are one simulation (run ${e((T.sims.find(q => q.label === T.check.same[0]) || {}).run || 'not recorded')}): the same settings and seed under ${T.check.same.length} labels. The harness recorded “${e(T.check.recorded)}”; the page counts this check neither as held nor as failed.</p>` : ''}${EV.ruleBars(T)}${EV.nbGap ? EV.nbGap(T) : ''}` : `<span class="mut">${T.rule ? (M.ended ? 'not checked' : 'not yet') : 'no decision rule'}</span>`, kc)}
        ${sec('Verdict', v ? `${e(v.id)} ${EV.verdictRes(v.result)}${EV.rests(v)}${EV.contradicts(v, T.check ? [T.check] : []) ? ' ' + EV.warn('disagrees with its check') : ''}<p data-own="model">${e(v.because || '')}</p>${EV.numCheck(v.because, x.sims)}` : `<span class="mut">${M.ended ? 'no verdict was given here' : 'not judged yet'}</span>`, kv)}
        ${sec('So next', v ? `<span data-own="model">${e(v.next || 'not recorded')}</span>${fol.ids.length ? `<p class="sm" data-step="${kf}">followed by ${fol.ids.map(EV.link).join(', ')}</p>` : ''}` : '<span class="mut">no verdict, so no next step</span>', kv)}</div>
      <div data-step="${simK}" style="margin-top:8px">${T.sims.length ? EV.canvas('test', T.id, wide) : ''}
          <p class="sm"><button data-act="wide" data-id="${e(T.id)}">${wide ? `back to the ${T.sims.length} simulation${T.sims.length === 1 ? '' : 's'} this rule names` : `the same chart over all ${x.sims.length} simulations of ${e(x.id)}`}</button></p></div>
      <details class="td-exact" id="tx-${e(T.id)}"><summary><b>The exact records</b> <span class="sm">the rule as it was written, the check's own numbers, the times</span></summary>
        <p class="sm">The ${EV.term('Decision rule', 'decision rule')}, as written: ${T.rule ? `<code>${e(T.rule)}</code>` : EV.nr}</p>
        <p class="sm" data-step="${kc}">${EV.term('Check', 'check')} by the harness: ${T.check ? `${e(T.check.id)} · <code>${e(T.check.numbers)}</code> → ${EV.checkRes(T.check)}` : EV.nr}</p>
        ${EV.orderLine(T, simK, kc)}</details>`;
  },

  testPanel(id) {
    const M = EV.M, e = EV.e, T = M.testById[id]; if (!T) return `<p class="sm">${e(id)}: ${EV.nr}</p>`;
    const h = M.hypById[T.hyp], more = h ? h.tests.filter(q => q !== id && EV.seen(M.testById[q].exp)) : [];
    // The head says the outcome at once: the harness's check and the AI's verdict, each on a badge (only what is recorded by the step the page is at). The hypothesis
    // stands by its plain wording; its full statement, its prediction and what it follows from are one click away (folded), for they are long and say the same again.
    const c = T.check && EV.seen(T.check.id) ? T.check : null, v = T.verdict && EV.seen(T.verdict.id) ? T.verdict : null;
    const full = `<p>${EV.link(T.hyp)} <span data-own="model">${e(h ? h.text : '')}</span></p>
          <p class="sm">its prediction: <span data-own="model">${e((h && h.prediction) || 'not recorded')}</span></p><p class="sm">follows from: ${h && h.follows ? h.follows.map(EV.link).join(', ') || 'nothing earlier' : EV.nr}${more.length ? ' · this hypothesis was also tested in ' + more.map(q => EV.tlink(M.testById[q], e(M.testById[q].exp))).join(', ') : ''}</p>`;
    return `<h2 class="td-head">${EV_ICON.test} ${EV.term('Test', 'Test')} of ${e(T.hyp)}${c ? ` <span class="hp-badge ck-${c.void ? 'void' : e(c.result)}" data-head="check">${EV.checkRes(c)}</span>` : ''}${v ? ` <span class="hp-badge ${EV.stCls(v.result)}" data-head="verdict">${EV.verdictRes(v.result)}</span>` : ''} <small>experiment ${e(T.exp)} · turn ${T.turn}</small></h2>
      <div class="td td-top"><div class="td-l" data-td="question"><span class="td-k">Hypothesis</span><div class="td-v">${h && h.question ? `<p class="hq-line">${EV.question(h)}</p><details class="td-fold" id="td-full"><summary><span class="td-fold-s">its full statement, its prediction, what it follows from</span></summary>${full}</details>` : full}</div></div>
        <div class="td-l" data-td="why"><span class="td-k">Why</span><div class="td-v"${h && h.why ? ' data-own="model"' : ''}>${h && h.why ? e(h.why) : '<span class="mut">not recorded: sessions before 14 November 2026 were not asked for it</span>'}</div></div></div>${EV.testBody(T)}`;
  },

  // a hypothesis (opened from the map or a card): its statement, then View 3 of each of its tests
  hypCard(id) {
    const M = EV.M, e = EV.e, h = M.hypById[id]; if (!h) return `<p class="sm">${e(id)}: ${EV.nr}</p>`;
    const ts = h.tests.map(q => M.testById[q]).filter(T => EV.seen(T.exp));  // during the replay: only the tests planned by then
    return `<h2>${EV_ICON.hypothesis} ${EV.term('Hypothesis', 'Hypothesis')} ${e(h.id)} <small>stated in turn ${h.turn} · ${e(EV.s.step == null ? h.state : EV_DATA.stateAt(M, EV.s.step)[h.id] || 'open')}</small></h2>${h.question ? `<p class="hq-line">${EV.question(h)}</p>` : ''}${h.why ? `<p id="h-why"><span class="sm">why it asks:</span> <span data-own="model">${e(h.why)}</span></p>` : ''}<p>${e(h.text)}</p>
      <p class="sm">prediction: ${e(h.prediction || 'not recorded')} · follows from: ${h.follows ? h.follows.map(EV.link).join(', ') : EV.nr}${h.drop && EV.seen(h.drop.id) ? ` · dropped in turn ${h.drop.turn}: ${e(h.drop.why || '')}` : ''}</p>
      ${ts.length ? ts.map(T => `<h3>${EV_ICON.test} Its ${EV.term('Test', 'test')} in experiment ${e(T.exp)}, turn ${T.turn}</h3>${EV.testBody(T)}`).join('') : '<p class="sm">This hypothesis was not put to a test.</p>'}`;
  },
});
EV.act = Object.assign(EV.act || {}, { insetoff() { EV.s.inset = null; EV.draw(); } });
// the fold of the chain of boxes: a click on its line opens or closes it; the browser remembers which, and the chain is drawn to the pane's width when it opens
document.getElementById('ev').addEventListener('click', ev => {
  if (!(ev.target.closest && ev.target.closest('#td-chain > summary'))) return;
  setTimeout(() => { const d = document.getElementById('td-chain'); if (!d) return; EV.store('ev-chain', d.open ? '1' : '0'); if (d.open && EV.flowFit) EV.flowFit(); }, 0);
});
