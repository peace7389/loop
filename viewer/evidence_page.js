// A session's page, top to bottom: the header strip (always visible, labelled fields on one line); the overview, first and at
// full width, so that a reader meets the conclusion first (the introduction, then from the final report the goal, the
// recommended settings against the brief's defaults, the explanation, the expected result, when it holds and breaks, its
// claims); "The system"; "What this session is made of"; then the highlights; best so far; the work (tree | session flow |
// hypothesis map); the tests list; "How to read this page". The detail of whatever is selected is the right-hand pane:
// it stays in view beside all of these, so no click has to move the page.
// ======================================================================================================
Object.assign(EV, {
  // the recommendation against the brief's defaults (the comparison is the page's; both sides are recorded): the knobs
  // that differ, those at the brief's default, and the brief's knobs the report does not name. null: no recommendation by this step
  recParts() {
    const M = EV.M, rec = M.report && M.repRec && EV.seen(M.repRec.id) ? M.report.recommendation : M.report && !M.repRec && EV.s.step == null ? M.report.recommendation : null, kn = M.brief && M.brief.knobs;
    if (rec == null) return null; if (typeof rec !== 'object') return { text: String(rec) };
    const same = (a, b) => (typeof a === 'number' || typeof b === 'number' ? Number(a) === Number(b) : EV.knNum(a) === EV.knNum(b) || String(a) === String(b)), all = Object.entries(rec);
    return !kn ? { differ: all, same: [], unnamed: [], known: false } : { differ: all.filter(([k, v]) => !(k in kn) || !same(v, kn[k].default)), same: all.filter(([k, v]) => k in kn && same(v, kn[k].default)), unnamed: Object.keys(kn).filter(k => !(k in rec)), known: true };
  },
  // ---- the header strip: labelled fields on one line, each a small label above its value; only what is recorded by the replay's step
  headStrip() {
    const M = EV.M, S = EV.s, row = EV.files.row || {}, m = M.meta || {}, e = EV.e, seen = EV.seen, live = S.step == null || S.step >= M.steps.length - 1, R = EV.recParts();
    const held = M.checks.filter(c => c.result === 'held' && seen(c.id)).length, failed = M.checks.filter(c => c.result === 'failed' && seen(c.id)).length, used = M.sims.filter(q => !q.same_as && q.exp !== 'X0' && seen(q.id)).length;
    const kv = ([k, v]) => `${e(k)} ${e(TASK_VIEW._rate(String(v)))}`, rec = !R ? null : R.text ? e(R.text) : R.differ.length ? R.differ.map(kv).join(', ') : R.known ? "every knob at the brief's default" : EV.nr;
    const f = (id, label, value, title) => `<div class="hf" data-f="${id}"${title ? ` title="${e(title)}"` : ''}><span>${label}</span><b>${value}</b></div>`;
    const ended = row.running ? '<span class="pill live">running</span>' : !live ? `<span class="mut">at step ${S.step + 1} of ${M.steps.length}</span>` : m.how ? e(m.how) : `ending ${EV.nr}`;
    return `<div class="ev-head" id="ev-head">${f('brief', EV.term('Brief', 'Brief'), M.brief ? e(M.brief.id) : EV.nr)}${f('session', EV.term('Session', 'Session'), e(M.id))}${f('how', 'How it ended', ended, live ? m.how : '')}
      ${f('sims', EV.term('Simulation', 'Simulations'), `${live ? m.simulations ?? (M.old ? M.sims.length : row.simulations ?? used) : used}${row.allowed ? ' of ' + row.allowed : ''}`)}${f('checks', EV.term('Check', 'Checks'), M.old ? EV.nr : EV.tally(held, failed))}
      ${f('model', 'Model', m.model ? e(m.model) : EV.nr)}${f('rec', 'Recommends', rec == null ? `<span class="mut">no recommendation${M.ended && live ? '' : ' yet'}</span>` : rec, R && R.known && R.differ.length ? "The knobs of the recommendation that differ from the brief's defaults" : '')}
      ${S.op ? `<span data-by="operator" class="hf-op">${f('policy', '<i class="sw"></i>' + EV.term('Scheduling policy', 'Scheduling policy'), EV.policyText(row))}${f('gap', 'Gap to the best', EV.gapText(row) || '<span class="mut">not scored</span>')}</span>` : ''}</div>`;
  },

  // ---- the first thing a reader reads: what this session concluded. Two columns: the goal, the recommended settings and
  // the explanation; beside them the expected result. Below: when it holds, when it breaks; then the claims.
  // In the replay the report is absent before its step, not greyed.
  overview() {
    const M = EV.M, S = EV.s, e = EV.e, seen = EV.seen, rep = M.report && (M.repRec ? seen(M.repRec.id) : S.step == null) ? M.report : null, m = M.meta || {}, live = S.step == null || S.step >= M.steps.length - 1, R = EV.recParts(), g = EV.goalOf(M.brief);
    const held = M.checks.filter(q => q.result === 'held' && seen(q.id)).length, rules = M.checks.filter(q => seen(q.id)).length, turns = M.turns.filter(t => t.n > 0 && (t.steps[0] ? t.steps[0].k : 0) <= (S.step ?? Infinity)).length;
    const intro = !S.intro ? '' : `<div class="ev-intro"><p>A person wrote an assignment (the ${EV.term('Brief', 'brief', 1)}${M.brief ? ' “' + e(M.brief.id) + '”' : ''}). The AI made one attempt, in ${turns} ${EV.term('Turn', turns === 1 ? 'turn' : 'turns', 1)}${live ? '' : ' so far'}.
      Each turn it stated what it expected, ran ${EV.term('Simulation', 'simulations', 1)}, and the harness checked whether it was right: ${M.old ? 'the checks were ' + EV.nr : `${held} of ${rules} ${EV.term('Decision rule', 'decision rules', 1)} held`}.
      ${M.report || !live ? '' : M.ended ? 'It ended without a final report.' : 'It is still running.'}</p><button data-act="intro">dismiss</button></div>`;
    const txt = v => (Array.isArray(v) ? v.map(q => e(q)).join(' · ') : e(v ?? 'not recorded')), name = k => e(TH_DATA.KNOB[k] || k), val = (k, v) => e(TASK_VIEW._rate(String(EV.val(k, v)))).replace(/^Tcp/, '');
    const recHtml = !R ? EV.nr : R.text ? e(R.text) : `<div class="rec" id="ov-rec">${R.differ.map(([k, v]) => `<span class="rk" data-knob="${e(k)}"><span>${name(k)}</span><b>${val(k, v)}</b></span>`).join('') || (R.known ? '<span class="sm">no knob differs from the brief’s default</span>' : EV.nr)}</div>
      ${R.same.length ? `<p class="sm" id="ov-def">at the brief's default: ${R.same.map(([k, v]) => `${name(k)} ${val(k, v)}`).join(' · ')}</p>` : ''}${R.unnamed.length ? `<p class="sm">not named in the report: ${R.unnamed.map(name).join(', ')}</p>` : ''}`;
    // the expected result: the target first; outputs that only repeat a setting are left out here (the full final report shows them)
    const exp = rep && rep.expected && typeof rep.expected === 'object' ? Object.entries(rep.expected).filter(([k]) => !['link_rate_bps', 'weight_udp'].includes(k)).sort(([a], [b]) => (g ? (b === g.target) - (a === g.target) : 0)) : null;
    const cond = k => { const c = M.brief && M.brief.goal && (M.brief.goal.conditions || []).find(q => new RegExp('^\\s*' + k + '\\b').test(q)); return c ? `<span class="sm">the brief allows ${e(c)}</span>` : ''; };
    const expHtml = !exp ? e(String((rep && rep.expected) ?? 'not recorded')) : `<table class="xr" id="ov-exp"><tbody>${exp.map(([k, v]) => `<tr data-k="${e(k)}"><td>${e(TH_DATA.PLAIN[k] || k)} ${cond(k)}</td><td class="num">${e(EV.val(k, v))}</td></tr>`).join('')}</tbody></table>`;
    const claims = !rep ? '' : !M.claims.length ? '<p class="sm">The report states no claims.</p>' : `<h3>Its claims</h3><div class="claims">${M.claims.map(q => { const n = q.evidence.filter(id => (EV.marks['rec:' + id] || {}).tick).length;
        return `<button class="chip claim${S.claim === q.n ? ' on' : ''}" data-act="claim" data-id="${q.n}" data-kind="${q.kind}"><b>claim ${q.n}</b><span class="ct">${e(q.text)}</span><span class="sm cl-ev">${EV.claimMarks(q, EV.seen)}${q.evidence.length ? ` · ${q.evidence.length} evidence item${q.evidence.length === 1 ? '' : 's'}` : ''}${n ? ` · ${n} reviewed` : ''}</span></button>`; }).join('')}</div>
      <p class="sm">${EV.claimCounts(M.claims)}${S.claim ? ` · <button data-act="print" data-id="${S.claim}">print evidence sheet for claim ${S.claim}</button>` : ''}</p>`;
    const body = !rep ? (live ? `<p id="ov-none"><b class="warnc">No final report.</b> ${M.ended ? `The session ended: ${m.how ? e(m.how) : EV.nr}.` : 'The session is still running.'}</p>` : '<p id="ov-none" class="sm">No final report by this step.</p>')
      : `<div class="ov"><div class="ov-top"><div><h3>The goal</h3><p id="ov-goal">${txt(rep.goal)}</p><h3>Recommended settings</h3>${recHtml}
            <h3>Explanation</h3><div id="ov-expl" class="${S.more ? '' : 'clamp'}">${txt(rep.explanation)}</div><a class="noprint sm" data-act="more">${S.more ? 'less' : 'more'}</a></div>
          <div><h3>Expected result</h3>${expHtml}</div></div>
        <div class="ov-when"><div><h3>Holds when</h3><p>${txt(rep.holds_when)}</p></div><div><h3>Breaks when</h3><p>${txt(rep.breaks_when)}</p></div></div>${claims}</div>`;
    return `<div class="ev-card" id="s-overview"><h2>Overview <small>what this session concluded, from its ${EV.term('Final report', 'final report')}</small></h2>${intro}${body}
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
      <div class="ev-top" style="margin-top:10px"><div><h3>How a session is built<span class="sm"> · this session's counts; click a box to go to that part</span></h3>${EV.structureMap()}</div>
        <div><h3>Who produced it</h3>${EV.legend()}<h3>The turn loop</h3>${EV.turnLoop()}</div></div>
      <h3>The words</h3><table><tbody>${Object.entries(EV_DEF).map(([k, v]) => `<tr><td style="white-space:nowrap"><b>${EV.e(k)}</b></td><td>${EV.e(v)}</td></tr>`).join('')}</tbody></table>
      <p class="sm">“Work log”: the sequence of the model's steps and its stated reasons. “Operator columns”: anything operator-only, shown when the switch at the top is on.</p></details>`;
  },

  sessionTab() {
    return `${EV.headStrip()}${EV.banner ? EV.banner() : ''}${EV.overview()}${EV.systemCard()}${EV.glance()}
      <div class="ev-main"><div>${EV.highCard()}${EV.bestCard()}${EV.knobCard()}${EV.aloneCard()}${EV.workCard()}${EV.testsCard()}</div>
        <div class="ev-side"><div class="ev-card" id="p-detail">${EV.paneTabs()}${EV.s.pane === 'queue' ? EV.queueView() : ''}${EV.detail()}</div></div></div>${EV.howTo()}`;
  },
});
EV.act = Object.assign(EV.act || {}, { more() { EV.s.more = !EV.s.more; EV.draw(); } });
