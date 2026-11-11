// The test panel: one hypothesis put to one decision rule. View 3 (the flow chart of the test), the line that says
// which experiment it was run in and with which other tests, the chart of the measure its rule judges, the simulations
// the rule names with the settings that differ between them highlighted, the check and the verdict.
// A hypothesis opened from the map shows the same body for each of its tests.
// ======================================================================================================
Object.assign(EV, {
  testBody(T) {
    const M = EV.M, S = EV.s, e = EV.e, x = M.expById[T.exp], others = M.tests.filter(q => q.exp === T.exp && q !== T), wide = !!S.wide[T.id];
    const simK = Math.max(M.recStep[x.id] ?? 0, ...T.sims.map(s => M.recStep[s.id] ?? 0)), kc = T.check ? M.recStep[T.check.id] ?? simK : simK, v = T.verdict, kv = v ? M.recStep[v.id] ?? kc : kc;
    const vary = EV.varying(T.sims), same = [...new Set(T.sims.flatMap(s => Object.keys(s.params)))].filter(k => !vary.includes(k)), ms = EV.measuresOf(T.rule);
    const show = (k, val) => { const [u, f] = EV.unit(k); return typeof val !== 'number' ? '–' : (+f(val).toPrecision(7)).toLocaleString('en-US') + (u ? ' ' + u : ''); };
    const table = !T.sims.length ? `<p class="sm">the simulations this rule names: ${EV.nr}</p>` : `<table><thead><tr><th></th>${T.sims.map(s => `<th class="num"><a data-act="open" data-t="sim" data-id="${e(s.id)}" data-test="${e(T.id)}">${s.same_as ? '○' : EV_ICON.simulation} ${e(s.id)}</a><br>${e(s.label)}${s.label === T.control ? '<br>◇ control' : ''}</th>`).join('')}</tr></thead><tbody>
        ${vary.map(k => `<tr class="diff"><td>${e(TH_DATA.KNOB[k] || k)} <span class="warnc">≠</span></td>${T.sims.map(s => `<td class="num">${e(s.params[k] ?? '–')}</td>`).join('')}</tr>`).join('')}
        ${ms.map(k => `<tr><td>${e(TH_DATA.PLAIN[k] || k)}</td>${T.sims.map(s => `<td class="num">${show(k, (s.metrics || {})[k])}</td>`).join('')}</tr>`).join('')}</tbody></table>
        <p class="sm">${vary.length ? 'In bold: the settings that differ between them. ' : T.sims.length > 1 ? 'These simulations were given the same settings. ' : ''}The same in all: ${e(same.map(k => `${k} ${T.sims[0].params[k]}`).join(' · ') || 'nothing')}.</p>`;
    return `${EV.viewTest(T)}
      <p class="sm">run in ${EV.link(x.id)} (turn ${x.turn})${others.length ? ' together with tests of ' + others.map(q => EV.tlink(q, e(q.hyp))).join(', ') : ', the only test in it'}</p>
      <div class="ev-top" style="margin-top:6px"><div data-step="${simK}">${T.sims.length ? EV.canvas('test', T.id, wide) : ''}
          <p class="sm"><button data-act="wide" data-id="${e(T.id)}">${wide ? `back to the ${T.sims.length} simulation${T.sims.length === 1 ? '' : 's'} this rule names` : `the same chart over all ${x.sims.length} simulations of ${e(x.id)}`}</button></p></div>
        <div data-step="${simK}"><h3>the simulations this rule names</h3>${table}</div></div>
      <h3>the ${EV.term('Decision rule', 'decision rule')}, in full</h3><p>${T.rule ? `<code>${e(T.rule)}</code>` : EV.nr}</p>
      ${T.rival ? `<p class="sm">${EV.term('Rival', 'rival')}: ${e(T.rival)} · under the rival the rule would have ${e(T.rival_predicts || 'not recorded')}</p>` : ''}
      <p class="sm" data-step="${kc}">${EV.term('Check', 'check')} by the harness: ${T.check ? `${EV_ICON.check} ${e(T.check.id)} · ${e(T.check.numbers)} → <b class="${T.check.result === 'held' ? 'ok' : 'bad'}">${e(T.check.result)}</b>` : EV.nr}</p>
      ${v ? `<div data-step="${kv}"><h3>${EV.term('Verdict', 'verdict')} ${e(v.id)}: ${e(v.result)}${EV.contradicts(v, T.check ? [T.check] : []) ? ' <span class="warnc">⚠ disagrees with its check</span>' : ''}</h3><p>${e(v.because || '')}</p>${EV.numCheck(v.because, x.sims)}<p class="sm"><b>next</b> ${e(v.next || 'not recorded')}</p></div>` : ''}`;
  },

  testPanel(id) {
    const M = EV.M, e = EV.e, T = M.testById[id]; if (!T) return `<p class="sm">${e(id)}: ${EV.nr}</p>`;
    const h = M.hypById[T.hyp], more = h ? h.tests.filter(q => q !== id && EV.seen(M.testById[q].exp)) : [];
    return `<h2>${EV_ICON.test} ${EV.term('Test', 'Test')} of ${e(T.hyp)}<small>one hypothesis put to one decision rule · run in experiment ${e(T.exp)}, turn ${T.turn}</small></h2>
      <p>${EV.link(T.hyp)} ${e(h ? h.text : '')}</p>
      <p class="sm">prediction: ${e((h && h.prediction) || 'not recorded')} · follows from: ${h && h.follows ? h.follows.map(EV.link).join(', ') : EV.nr}${more.length ? ' · this hypothesis was also tested in ' + more.map(q => EV.tlink(M.testById[q], e(M.testById[q].exp))).join(', ') : ''}</p>${EV.testBody(T)}`;
  },

  // a hypothesis (opened from the map or a card): its statement, then View 3 of each of its tests
  hypCard(id) {
    const M = EV.M, e = EV.e, h = M.hypById[id]; if (!h) return `<p class="sm">${e(id)}: ${EV.nr}</p>`;
    const ts = h.tests.map(q => M.testById[q]).filter(T => EV.seen(T.exp));  // during the replay: only the tests planned by then
    return `<h2>${EV_ICON.hypothesis} ${EV.term('Hypothesis', 'Hypothesis')} ${e(h.id)}<small>stated in turn ${h.turn} · ${e(EV.s.step == null ? h.state : EV_DATA.stateAt(M, EV.s.step)[h.id] || 'open')}</small></h2><p>${e(h.text)}</p>
      <p class="sm">prediction: ${e(h.prediction || 'not recorded')} · follows from: ${h.follows ? h.follows.map(EV.link).join(', ') : EV.nr}${h.drop && EV.seen(h.drop.id) ? ` · dropped in turn ${h.drop.turn}: ${e(h.drop.why || '')}` : ''}</p>
      ${ts.length ? ts.map(T => `<h3>${EV_ICON.test} its ${EV.term('Test', 'test')} in experiment ${e(T.exp)}, turn ${T.turn}</h3>${EV.testBody(T)}`).join('') : '<p class="sm">This hypothesis was not put to a test.</p>'}`;
  },
});
