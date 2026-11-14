// A session's page. Everything on it belongs to one of three levels of detail:
//   1 · at a glance   the header strip; the setting (evidence_system.js); the session at a glance (evidence_glance.js);
//                     what it needed to find out (evidence_find.js). Open, at the top, at full width.
//   2 · read          the work, step by step: the notebook (evidence_notebook.js); what it proposes (the final report as one
//                     argument); below level 1, in the left column, beside the detail pane.
//   3 · inspect       a test's flow chart, the exact decision rule and numbers, a simulation's settings and charts, the
//                     review queue: the detail pane on the right, opened by a click. Nothing of level 3 stands at level
//                     1 or 2 except as something to click.
// The analysis views are folded under "Looking closer" (evidence_closer.js); "How to read this page" is last. The switch
// "Brief / Full" in the header strip opens every folded section at once; the browser remembers it.
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
  stripField: (id, label, value, title) => `<div class="hf" data-f="${id}"${title ? ` title="${EV.e(title)}"` : ''}><span>${label}</span><b>${value}</b></div>`,
  strip: (fields, id) => `<div class="ev-head" id="${id}">${fields.map(q => EV.stripField(...q)).join('')}</div>`,  // the same strip, from a list of [field, label, value, hover]: the set-up page shows the one its session will have
  headStrip() {
    const M = EV.M, S = EV.s, row = EV.files.row || {}, m = M.meta || {}, e = EV.e, seen = EV.seen, live = S.step == null || S.step >= M.steps.length - 1, R = EV.recParts();
    const used = M.sims.filter(q => !q.same_as && q.exp !== 'X0' && seen(q.id)).length;  // the checks' tally stands in "The session at a glance", the model in the session's summary
    const kv = ([k, v]) => `${e(k)} ${e(TASK_VIEW._rate(String(v)))}`, rec = !R ? null : R.text ? e(R.text) : R.differ.length ? R.differ.map(kv).join(', ') : R.known ? "every knob at the brief's default" : EV.nr;
    const f = EV.stripField;
    const ended = row.running ? '<span class="pill live">running</span>' : !live ? `<span class="mut">at step ${S.step + 1} of ${M.steps.length}</span>` : m.how ? e(m.how) : `ending ${EV.nr}`;
    return `<div class="ev-head" id="ev-head">${f('brief', EV.term('Brief', 'Brief'), M.brief ? e(M.brief.id) : EV.nr)}${f('session', EV.term('Session', 'Session'), e(M.id))}${f('how', 'How it ended', ended, live ? m.how : '')}
      ${f('sims', EV.term('Simulation', 'Simulations'), `${live ? m.simulations ?? (M.old ? M.sims.length : row.simulations ?? used) : used}${row.allowed ? ' of ' + row.allowed : ''}`)}
      ${f('rec', 'Recommends', rec == null ? `<span class="mut">no recommendation${M.ended && live ? '' : ' yet'}</span>` : rec, R && R.known && R.differ.length ? "The knobs of the recommendation that differ from the brief's defaults" : '')}
      ${S.op ? `<span data-by="operator" class="hf-op">${f('policy', '<i class="sw"></i>' + EV.term('Scheduling policy', 'Scheduling policy'), EV.policyText(row))}${f('gap', 'Gap to the best', EV.gapText(row) || '<span class="mut">not scored</span>')}</span>` : ''}
      <div class="hf hf-level noprint" data-f="level" title="Brief: the page as laid out for a first reading. Full: every folded section open."><span>Detail</span><b class="seg"><button data-act="level" data-id="brief" class="${S.full ? '' : 'on'}">Brief</button><button data-act="level" data-id="full" class="${S.full ? 'on' : ''}">Full</button></b></div></div>`;
  },

  // ---- the final report by the replay's step (absent before its step, not greyed), and its expected result as rows:
  // the target first; outputs that only repeat a setting are left out (the full final report in the detail pane shows them)
  repNow() { const M = EV.M; return M.report && (M.repRec ? EV.seen(M.repRec.id) : EV.s.step == null) ? M.report : null; },
  expRows(rep) {
    const M = EV.M, e = EV.e, g = EV.goalOf(M.brief), conds = (M.brief && M.brief.goal && M.brief.goal.conditions) || [], of = k => conds.find(q => new RegExp('^\\s*' + k + '\\b').test(q));
    if (!rep || !rep.expected || typeof rep.expected !== 'object') return null;
    const all = Object.entries(rep.expected).filter(([k]) => !['link_rate_bps', 'weight_udp'].includes(k)).sort(([a], [b]) => (g ? (b === g.target) - (a === g.target) : 0));
    const row = ([k, v]) => `<tr data-k="${e(k)}"><td>${e(TH_DATA.PLAIN[k] || k)} ${of(k) ? `<span class="sm">the brief allows ${e(of(k))}</span>` : ''}</td><td class="num">${e(EV.val(k, v))}</td></tr>`;
    // the short list of the Overview: the goal's target and the measures the brief's conditions name; a brief without a goal: the first three rows
    return { all, top: g ? all.filter(([k]) => k === g.target || of(k)) : all.slice(0, 3), row };
  },

  // ---- section 5, "What it proposes": the final report as one argument, in this order: the aim (and who set it); the
  // proposed adjustment (each recommended setting beside the value the session started from); the expected result in
  // short; because (the claims that support the recommendation, then those that say how the system behaves); but (the
  // claims that say when it would be wrong, then "holds when" and "breaks when"); the explanation, folded. Every line is
  // the model's own text or a recorded value; the page only orders them. A claim's part in the argument is its "role"
  // (supports, background, limits), which the harness requires since READABLE_PAGE.md; a report recorded without roles
  // shows its claims in one list. A session without a final report says so here, with how it ended.
  repTxt: v => (Array.isArray(v) ? v.map(q => EV.e(q)).join(' · ') : EV.e(v ?? 'not recorded')),
  ROLES: [['supports', 'because', 'reasons for the recommendation'], ['background', 'because', 'how the system behaves'], ['limits', 'but', 'when the recommendation would change']],
  claimBtn(q) { const S = EV.s, e = EV.e, n = q.evidence.filter(id => (EV.marks['rec:' + id] || {}).tick).length;
    return `<button class="chip claim${S.claim === q.n ? ' on' : ''}" data-act="claim" data-id="${q.n}" data-kind="${q.kind}" data-role="${q.role || ''}"><b>claim ${q.n}</b><span class="ct">${e(q.text)}</span><span class="sm cl-ev">${EV.claimMarks(q, EV.seen)}${q.evidence.length ? ` · ${q.evidence.length} evidence item${q.evidence.length === 1 ? '' : 's'}` : ''}${n ? ` · ${n} reviewed` : ''}</span></button>`; },
  // the setting a recommended value stands for, in the page's words and without its unit: "ratio 0.5 → 0.30295"
  adjVal: (k, v) => TASK_VIEW._rate(String(v)).replace(/^Tcp/, ''),
  proposesCard() {
    const M = EV.M, S = EV.s, e = EV.e, rep = EV.repNow(), m = M.meta || {}, live = S.step == null || S.step >= M.steps.length - 1, txt = EV.repTxt;
    const head = `<h2>What it proposes</h2><p class="sec-q">What does it recommend, on what evidence, and where does that stop being true?</p>`;
    const open = `<p class="sm noprint" style="margin-top:10px">open on the right: ${rep ? '<a data-act="open" data-t="report" data-id="report">the full final report</a> · ' : ''}<a data-act="open" data-t="brief" data-id="brief">the brief</a> · <a data-act="open" data-t="session" data-id="${e(M.id)}">the session's summary</a></p>`;
    if (!rep) return `<div class="ev-card" id="s-proposes">${head}${live ? `<p id="ov-none"><b>No final report.</b> ${M.ended ? `The session ended: ${m.how ? e(m.how) : EV.nr}.` : 'The session is still running.'}</p>` : '<p id="ov-none" class="sm">No final report by this step.</p>'}${open}${EV.shareBar()}</div>`;
    const R = EV.recParts(), X = EV.expRows(rep), kn = (M.brief && M.brief.knobs) || {}, g = (M.brief && M.brief.goal) || {}, lab = k => EV.label(k, (kn[k] || {}).meaning);
    // 1 · the aim, and who set it: the brief's goal in words when the operator gave one; the goal the AI states in its report when the brief left it open
    const aim = g.kind === 'given' ? `<p id="pr-aim" data-aim="given"><b>Find ${EV.aimWords(g) || 'not recorded'}.</b> <span class="st-by" data-by="operator"><i class="sw"></i>set by the operator</span></p><p class="sm lc4" id="ov-goal" title="The goal as the final report states it">${txt(rep.goal)}</p>`
      : `<p id="pr-aim" data-aim="${g.kind === 'open' ? 'open' : ''}"><span id="ov-goal" class="lc4">${txt(rep.goal)}</span></p><p class="sm"><span class="st-by" data-by="model"><i class="sw"></i>${g.kind === 'open' ? 'chosen by the AI' : 'as the final report states it'}</span>${g.kind === 'open' ? ' · the brief left the aim open' : M.brief ? '' : ` · the brief: ${EV.nr}`}</p>`;
    // 2 · the proposed adjustment: each recommended setting that differs, beside the value the session started from (the brief's default)
    const adj = !R ? EV.nr : R.text ? e(R.text) : `<p id="ov-rec" class="pr-adj">${R.differ.map(([k, v]) => `<span class="rk" data-knob="${e(k)}">${lab(k)} <b>${k in kn ? e(EV.adjVal(k, kn[k].default)) + ' → ' : ''}${e(EV.adjVal(k, v))}</b></span>`).join('<span class="pr-sep">, </span>') || (R.known ? '<span class="sm">no setting differs from where the session started</span>' : EV.nr)}</p>
      ${R.known ? `<p class="sm" id="ov-def">everything else unchanged${R.same.length || R.unnamed.length ? `: ${[...R.same.map(([k, v]) => `${EV.LABEL[k] || k} ${EV.setVal(k, v)}`), ...R.unnamed.map(k => `${EV.LABEL[k] || k} ${EV.setVal(k, kn[k].default)} (not named in the report)`)].map(e).join(' · ')}` : ''}</p>` : ''}`;
    // 3 · the expected result: the target's measure and those the conditions name
    const left = X ? X.all.length - X.top.length : 0;
    const exp = !X ? `<p class="lc4">${e(String(rep.expected ?? 'not recorded'))}</p>` : `<table class="xr" id="ov-exp-top"><tbody>${X.top.map(X.row).join('')}</tbody></table>${left ? `<p class="sm" id="ov-exp-more"><a data-act="open" data-t="report" data-id="report">${left} more in the final report</a></p>` : ''}`;
    // 4 and 5 · because, and but: the claims by their role; a report recorded without roles: one list
    const roles = M.claims.length > 0 && M.claims.every(q => q.role), of = r => M.claims.filter(q => q.role === r), group = ([r, , says]) => (of(r).length ? `<p class="pr-role sm" data-role="${r}">${says}</p><div class="claims">${of(r).map(EV.claimBtn).join('')}</div>` : '');
    const counts = `<p class="sm" id="pr-counts">${EV.claimCounts(M.claims)}${S.claim ? ` · <button data-act="print" data-id="${S.claim}">print evidence sheet for claim ${S.claim}</button>` : ''}</p>`;
    const mis = EV.moments(M).report, when = `<div class="ov-when"><h4>Holds when</h4><p>${txt(rep.holds_when)}</p><h4>Breaks when</h4><p>${txt(rep.breaks_when)}</p></div>`;
    const because = !M.claims.length ? '<p class="sm">The report states no claims.</p>' : roles ? (EV.ROLES.filter(q => q[1] === 'because').map(group).join('') || '<p class="sm">No claim is given as a reason.</p>') : `<p class="sm" id="pr-noroles">This report was recorded before claims had roles: its claims in one list.</p><div class="claims">${M.claims.map(EV.claimBtn).join('')}</div>`;
    const but = `${roles ? EV.ROLES.filter(q => q[1] === 'but').map(group).join('') || '<p class="sm">No claim says when the recommendation would change.</p>' : ''}${when}`;
    const blk = (n, key, title, body) => `<div class="pr-b" data-pr="${key}"><h3><span class="st-n">${n}</span>${title}</h3>${body}</div>`;
    return `<div class="ev-card" id="s-proposes">${head}<div id="s-report" data-by="model">
        ${blk(1, 'aim', 'The aim', aim)}${blk(2, 'adjust', 'The proposed adjustment', adj)}${blk(3, 'expected', 'The expected result', exp)}
        ${blk(4, 'because', roles || !M.claims.length ? 'Because' : 'Its claims', because + counts)}${blk(5, 'but', 'But', but)}
        <details class="pr-b" data-pr="explanation" id="pr-expl"${S.more || S.full ? ' open' : ''}><summary><h3 style="display:inline"><span class="st-n">6</span>The explanation</h3> <span class="sm">folded · the model's own words</span></summary><div id="ov-expl">${txt(rep.explanation)}</div></details>
        ${mis ? `<p class="sm" data-step="${mis.step}">${EV.warn('a number in the report differs from its measurement', `It wrote “${mis.rows[0].written}”; measured ${mis.rows[0].measured}`)} · <a data-act="open" data-t="report" data-id="report">the report's numbers against the measurements</a></p>` : ''}</div>${open}${EV.shareBar()}</div>`;
  },

  // ---- how to read this page: open on a reader's first visit, closed afterwards
  howTo() {
    return `<details class="ev-card" id="s-how"${EV.s.how || EV.s.full ? ' open' : ''}><summary><b class="how-h">How to read this page</b> <span class="sec-q">What is a turn, a test, a check?</span></summary>
      <div class="ev-top" style="margin-top:10px"><div><h3>How a session is built<span class="sm"> · this session's counts; click a box to go to that part</span></h3>${EV.structureMap()}</div>
        <div><h3>Who produced it</h3>${EV.legend()}<h3>The turn loop</h3>${EV.turnLoop()}</div></div>
      <h3>The words</h3><table><tbody>${Object.entries(EV_DEF).map(([k, v]) => `<tr><td style="white-space:nowrap"><b>${EV.e(k)}</b></td><td>${EV.e(v)}</td></tr>`).join('')}</tbody></table>
      <h3>Using the page</h3><ul class="sm" id="how-use" style="margin:0;padding-left:18px">
        <li>Whatever can be clicked shows the pointer and a change of background under it. A click never moves the page: what is chosen opens in the pane on the right.</li>
        <li>Four clicks do move the page, and say so here: a turn's name in “The session at a glance” and a row of “What it needed to find out” bring the notebook to that place; a box of “How a session is built” goes to its part; the guided walk goes from section to section.</li>
        <li>“What it needed to find out”: click a row to go to its card in the notebook. The notebook: click a card to open its test; a number in “Result” opens its simulation.</li>
        <li>“Looking closer”: click a line to open that view. Best so far, and the simulations of each turn: click a dot to open that simulation.</li>
        <li>“The system”: click an object to see its settings beside the picture. “What this session is made of”: click a mark to open it; point at a mark to read what it is.</li>
        <li>The session flow, the hypothesis map, the tree and the tests list: click an item or a row to open it. The session's summary: click any item on the left to open it there.</li>
        <li>An experiment's panel: click a test or a simulation to open it. A simulation's charts over time: point at a chart, and the same moment is marked in all of them.</li>
        <li>The Operator tab, the sweep: click a numbered circle to open that simulation; a dark circle stands for several at one place, and a click lists them under the map.</li>
        <li>Home: click a row to open that session; click a column title to sort. Compare sessions: tick two or more to see them side by side; click a first test that held to open it in its session.</li></ul>
      <p class="sm">“Work log”: the sequence of the model's steps and its stated reasons. “Operator columns”: anything operator-only, shown when the switch at the top is on.</p></details>`;
  },

  sessionTab() {
    return `${EV.headStrip()}${EV.banner ? EV.banner() : ''}${EV.settingCard()}${EV.glance()}${EV.findCard()}
      <div class="ev-main"><div>${EV.notebookCard()}${EV.proposesCard()}${EV.closerCard()}</div>
        <div class="ev-side"><div class="ev-card" id="p-detail">${EV.paneTabs()}${EV.s.pane === 'queue' ? EV.queueView() : ''}${EV.detail()}</div></div></div>${EV.howTo()}`;
  },
});
EV.act = Object.assign(EV.act || {}, { more() { EV.s.more = !EV.s.more; EV.draw(); } });
