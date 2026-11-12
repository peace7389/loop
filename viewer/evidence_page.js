// A session's page, top to bottom: the header strip (always visible); the system (evidence_system.js); what the session is made of (evidence_glance.js); the overview (the introduction and the research
// overview from the final report, with its claims); the highlights; best so far; the work (tree | session flow |
// hypothesis map); the tests list; "How to read this page". The detail of whatever is selected is the right-hand pane:
// it stays in view beside all of these, so no click has to move the page.
// ======================================================================================================
Object.assign(EV, {
  headStrip() {
    const M = EV.M, row = EV.files.row || {}, m = M.meta || {}, e = EV.e, held = M.checks.filter(c => c.result === 'held').length, failed = M.checks.filter(c => c.result === 'failed').length, rec = M.report && M.report.recommendation;
    const bits = [`${EV_ICON.brief} ${EV.term('Brief', 'brief')} <b>${M.brief ? e(M.brief.id) : EV.nr}</b>`, `${EV.term('Session', 'session')} <b>${e(M.id)}</b>`, `model <b>${m.model ? e(m.model) : EV.nr}</b>`,
      row.running ? '<span class="pill live">running</span>' : `<b>${m.how ? e(m.how) : 'ending ' + EV.nr}</b>`, `<b>${m.simulations ?? (M.old ? M.sims.length : row.simulations ?? 0)}${row.allowed ? ' / ' + row.allowed : ''}</b> ${EV.term('Simulation', 'simulations')}`,
      `${EV.term('Test', 'tests')} <b class="ok">${held} held</b> / <b class="${failed ? 'bad' : ''}">${failed} failed</b>`,
      rec && typeof rec === 'object' ? `recommends <b>${e(Object.entries(rec).map(([k, v]) => `${k} ${v}`).join(', '))}</b>` : `<span class="mut">no recommendation${M.ended ? '' : ' yet'}</span>`];
    if (EV.s.op) bits.push(`<span data-by="operator"><i class="sw"></i>${EV.term('Scheduling policy', 'policy')} <b>${EV.policyText(row)}</b> · gap to the best <b>${EV.gapText(row) || '<span class="mut">not scored</span>'}</b></span>`);
    return `<div class="ev-head" id="ev-head">${bits.join(' <span class="mut">·</span> ')}</div>`;
  },

  // ---- the first thing a reader reads: what this session is, and what it concluded
  overview() {
    const M = EV.M, S = EV.s, e = EV.e, c = M.counts, rep = M.report, m = M.meta || {}, held = M.checks.filter(q => q.result === 'held').length, rules = M.checks.length;
    const recText = rep && typeof rep.recommendation === 'object' && rep.recommendation ? Object.entries(rep.recommendation).map(([k, v]) => `${k} ${v}`).join(', ') : rep ? String(rep.recommendation ?? 'not recorded') : null;
    const intro = !S.intro ? '' : `<div class="ev-intro"><p>A person wrote an assignment (the ${EV.term('Brief')}${M.brief ? ' “' + e(M.brief.id) + '”' : ''}). The AI made one attempt, in ${c.turn} ${EV.term('Turn', c.turn === 1 ? 'turn' : 'turns')}.
      Each turn it stated what it expected, ran ${EV.term('Simulation', 'simulations')}, and the harness checked whether it was right: ${rules ? `${held} of ${rules} ${EV.term('Decision rule', 'decision rules')} held` : 'the checks were ' + EV.nr}.
      ${rep ? `It ended with this recommendation: ${e(recText)}.` : M.ended ? 'It ended without a final report.' : 'It is still running.'}</p><button data-act="intro">dismiss</button></div>`;
    const txt = v => (Array.isArray(v) ? v.map(q => e(q)).join(' · ') : e(v ?? 'not recorded')), kv = o => (o && typeof o === 'object' ? Object.entries(o).map(([k, v]) => `<span class="pill">${e(TH_DATA.KNOB[k] || TH_DATA.PLAIN[k] || k)} <b>${e(EV.val(k, v))}</b></span>`).join(' ') : e(o ?? 'not recorded'));
    const state = { held: 'checks held', failed: 'a check failed', none: 'no evidence cited', unchecked: 'evidence without a check' };
    const claims = !rep ? '' : !M.claims.length ? '<p class="sm">The report states no claims.</p>' : `<h3>its claims<span class="sm noprint" style="text-transform:none;letter-spacing:0"> · click one to mark its evidence and open its test</span></h3><div class="chips">${M.claims.map(q => {
        const n = q.evidence.filter(id => (EV.marks['rec:' + id] || {}).tick).length;
        return `<button class="chip ${q.state}${S.claim === q.n ? ' on' : ''}" data-act="claim" data-id="${q.n}" title="${e(q.text)}"><b>claim ${q.n}</b><span class="ct">${e(q.text)}</span><br><span class="sm">${q.evidence.length} evidence item${q.evidence.length === 1 ? '' : 's'} · ${state[q.state]}${n ? ` · ${n} reviewed` : ''}</span></button>`; }).join('')}</div>
      <p class="sm">${M.claims.length} claims · ${M.claims.filter(q => q.state === 'held').length} backed by held checks · ${M.claims.filter(q => q.state === 'failed').length} backed by a failed check ·
        <span class="${M.claims.some(q => q.state === 'none') ? 'warnc' : ''}">${M.claims.filter(q => q.state === 'none').length} with no evidence</span>${M.claims.some(q => q.state === 'unchecked') ? ` · ${M.claims.filter(q => q.state === 'unchecked').length} citing evidence that has no check` : ''}
        ${S.claim ? ` · <button data-act="print" data-id="${S.claim}">print evidence sheet for claim ${S.claim}</button>` : ''}</p>`;
    const body = !rep ? `<p><b>No final report.</b> ${M.ended ? `The session ended: ${m.how ? e(m.how) : EV.nr}.` : 'The session is still running.'}</p>`
      : `<div class="ov" data-step="${M.repRec ? M.recStep[M.repRec.id] ?? 0 : 0}"><div><span>the goal</span>${txt(rep.goal)}</div><div><span>recommended settings</span>${kv(rep.recommendation)}</div><div><span>expected result</span>${kv(rep.expected)}</div>
          <div><span>explanation</span><div class="${S.more ? '' : 'clamp'}">${txt(rep.explanation)}</div><a class="noprint" data-act="more">${S.more ? 'less' : 'more'}</a></div>
          <div><span>holds when</span>${txt(rep.holds_when)}</div><div><span>breaks when</span>${txt(rep.breaks_when)}</div>${claims}</div>`;
    return `<div class="ev-card" id="s-overview"><h2>Overview <small>what this session is and what it concluded, from its ${EV.term('Final report', 'final report')}</small></h2>${intro}${body}
      <p class="sm noprint">open on the right: ${rep ? '<a data-act="open" data-t="report" data-id="report">the full final report</a> · ' : ''}<a data-act="open" data-t="brief" data-id="brief">the brief</a> · <a data-act="open" data-t="session" data-id="${e(M.id)}">the session's summary</a></p>${EV.shareBar()}</div>`;
  },

  // ---- the work: the left side is the tree, the session flow or the hypothesis map; the selection is shared
  workCard() {
    const S = EV.s, M = EV.M, left = S.left || 'tree', n = M.steps.length, k = S.step == null ? n - 1 : S.step, b = (id, t) => `<button data-act="left" data-id="${id}" class="${left === id ? 'on' : ''}">${t}</button>`;
    return `<div class="ev-card" id="s-work"><h2>The work <small>${left === 'tree' ? 'each turn with its experiment, the tests in that experiment, and the simulations each test uses' : left === 'lanes' ? 'time runs down, in the lane of whoever did each step' : 'left to right by the turn each hypothesis was stated'} · click an item to open it on the right</small></h2>
      <div class="ev-bar"><span>${b('tree', 'Tree')} ${b('lanes', 'Session flow')} ${b('map', 'Hypothesis map')}</span>${left === 'map' ? `<button data-act="path" class="${S.path ? 'on' : ''}">show the path to the answer</button>` : ''}
        <span class="end"><b>Replay</b> <button data-act="replay" data-id="first">« first</button> <button data-act="replay" data-id="prev">◀</button> <button data-act="replay" data-id="next">▶</button> <button data-act="replay" data-id="last">last »</button>
          <span class="sm">step ${n ? k + 1 : 0} of ${n}${S.step == null ? '' : ': later items are greyed'} · arrow keys</span></span></div>
      ${left === 'tree' ? EV.viewTree() : left === 'lanes' ? `<div class="ev-scroll ev-lanes">${EV.viewLanes()}</div>` : EV.viewMap()}</div>`;
  },

  // ---- how to read this page: open on a reader's first visit, closed afterwards
  howTo() {
    return `<details class="ev-card" id="s-how"${EV.s.how ? ' open' : ''}><summary><b>How to read this page</b> <span class="sm">how a session is built, the turn loop, who produced what, and the words used</span></summary>
      <div class="ev-top" style="margin-top:10px"><div><h3>how a session is built<span class="sm" style="text-transform:none;letter-spacing:0"> · this session's counts; click a box to go to that part</span></h3>${EV.structureMap()}</div>
        <div><h3>who produced it</h3>${EV.legend()}<h3>the turn loop</h3>${EV.turnLoop()}</div></div>
      <h3>the words</h3><table><tbody>${Object.entries(EV_DEF).map(([k, v]) => `<tr><td style="white-space:nowrap"><b>${EV.e(k)}</b></td><td>${EV.e(v)}</td></tr>`).join('')}</tbody></table>
      <p class="sm">“Work log”: the sequence of the model's steps and its stated reasons. “Operator columns”: anything operator-only, shown when the switch at the top is on.</p></details>`;
  },

  sessionTab() {
    return `${EV.headStrip()}${EV.banner ? EV.banner() : ''}${EV.systemCard()}${EV.glance()}
      <div class="ev-main"><div>${EV.overview()}${EV.highCard()}${EV.bestCard()}${EV.knobCard()}${EV.aloneCard()}${EV.workCard()}${EV.testsCard()}</div>
        <div class="ev-side"><div class="ev-card" id="p-detail">${EV.paneTabs()}${EV.s.pane === 'queue' ? EV.queueView() : ''}${EV.detail()}</div></div></div>${EV.howTo()}`;
  },
});
EV.act = Object.assign(EV.act || {}, { more() { EV.s.more = !EV.s.more; EV.draw(); } });
