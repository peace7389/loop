// A session's page. Everything on it belongs to one of three levels of detail:
//   1 · at a glance   the header strip; the setting (evidence_system.js); the session at a glance (evidence_glance.js);
//                     what it needed to find out (evidence_find.js). Open, at the top, at full width.
//   2 · read          the work, step by step: the notebook (evidence_notebook.js); what it proposes (the final report as one
//                     argument); how it worked as a researcher (evidence_research.js); below level 1, in the left column,
//                     beside the detail pane.
//   3 · inspect       a test's flow chart, the exact decision rule and numbers, a simulation's settings and charts, the
//                     review queue: the detail pane on the right, opened by a click. Nothing of level 3 stands at level
//                     1 or 2 except as something to click.
// A session that is running is shown as it is made (evidence_live.js): the same sections, with empty places that fill.
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
    const kn = (M.brief && M.brief.knobs) || {}, kv = ([k, v]) => `${EV.label(k, (kn[k] || {}).meaning)} ${e(EV.adjVal(k, v))}`, rec = !R ? null : R.text ? e(R.text) : R.differ.length ? `<span data-exact="1">${R.differ.map(kv).join(', ')}</span>` : R.known ? "every knob at the brief's default" : EV.nr;
    const f = EV.stripField;
    const ended = row.running ? '<span class="pill live">running</span>' : !live ? `<span class="mut">at step ${S.step + 1} of ${M.steps.length}</span>` : m.how ? e(m.how) : `ending ${EV.nr}`;
    return `<div class="ev-head" id="ev-head">${f('brief', EV.term('Brief', 'Brief'), M.brief ? EV.briefName(M.brief.id) : EV.nr)}${f('session', EV.term('Session', 'Session'), e(M.id))}${f('how', 'How it ended', ended, live ? m.how : '')}
      ${f('sims', EV.term('Simulation', 'Simulations'), `${live ? m.simulations ?? (M.old ? M.sims.length : row.simulations ?? used) : used}${row.allowed ? ' of ' + row.allowed : ''}`)}
      ${f('rec', 'Recommends', rec == null ? `<span class="mut">no recommendation${M.ended && live ? '' : ' yet'}</span>` : rec, R && R.known && R.differ.length ? "The knobs of the recommendation that differ from the brief's defaults" : '')}
      ${S.op ? `<span data-by="operator" class="hf-op">${f('policy', '<i class="sw"></i>' + EV.term('Scheduling policy', 'Scheduling policy'), EV.policyText(row))}${f('gap', 'Gap to the best', EV.gapText(row) || '<span class="mut">not scored</span>')}</span>` : ''}
      <div class="hf hf-level noprint" data-f="level" title="Brief: the page as laid out for a first reading. Full: every folded section open."><span>Detail</span><b class="seg"><button data-act="level" data-id="brief" class="${S.full ? '' : 'on'}">Brief</button><button data-act="level" data-id="full" class="${S.full ? 'on' : ''}">Full</button></b></div>
      <div class="hf hf-walk noprint" data-f="walk" title="A guided walk for a first reading: one sentence about each section, from this session's own records"><span>Walk</span><b><button data-act="walk" class="${S.walk ? 'on' : ''}">${S.walk ? 'Leave the walk' : 'Walk me through this session'}</button></b></div></div>`;
  },

  // ---- the final report by the replay's step (absent before its step, not greyed), and its expected result as rows:
  // the target first; outputs that only repeat a setting are left out (the full final report in the detail pane shows them)
  repNow() { const M = EV.M; return M.report && (M.repRec ? EV.seen(M.repRec.id) : EV.s.step == null) ? M.report : null; },
  expRows(rep) {
    const M = EV.M, e = EV.e, g = EV.goalOf(M.brief), conds = (M.brief && M.brief.goal && M.brief.goal.conditions) || [], of = k => conds.find(q => new RegExp('^\\s*' + k + '\\b').test(q));
    if (!rep || !rep.expected || typeof rep.expected !== 'object') return null;
    const all = Object.entries(rep.expected).filter(([k]) => !['link_rate_bps', 'weight_udp'].includes(k)).sort(([a], [b]) => (g ? (b === g.target) - (a === g.target) : 0));
    const row = ([k, v]) => `<tr data-k="${e(k)}"><td>${e(TH_DATA.PLAIN[k] || k)} ${of(k) ? `<span class="sm" title="${e(of(k))}">the brief allows ${EV.readHtml(of(k)) || e(of(k))}</span>` : ''}</td><td class="num">${EV.v4(k, v)}</td></tr>`;
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
  // a claim's role, the part of the argument it stands in, and what that part says. The role "background" (how the system behaves) is shown as the DIAGNOSIS: the
  // word is the page's, for the reader (the operator's choice, 2026-11-15); the record's role keeps its name, and the AI is still told "background"
  ROLES: [['background', 'diagnosis', 'say how the system behaves'], ['supports', 'because', 'give reasons for the recommendation'], ['limits', 'but', 'say when the recommendation would change']],
  claimBtn(q) { const S = EV.s, e = EV.e, n = q.evidence.filter(id => (EV.marks['rec:' + id] || {}).tick).length;
    return `<button class="chip claim${S.claim === q.n ? ' on' : ''}" data-act="claim" data-id="${q.n}" data-kind="${q.kind}" data-role="${q.role || ''}" data-wd="c:${q.n}"><b>claim ${q.n}</b><span class="ct" data-own="model">${e(q.text)}</span><span class="sm cl-ev">${EV.claimMarks(q, EV.seen)}${q.evidence.length ? ` · ${q.evidence.length} evidence item${q.evidence.length === 1 ? '' : 's'}` : ''}${n ? ` · ${n} reviewed` : ''}</span></button>`; },
  // the setting a recommended value stands for, in the page's words and without its unit: "ratio 0.5 → 0.30295"
  adjVal: (k, v) => TASK_VIEW._rate(String(v)).replace(/^Tcp/, ''),
  proposesCard() {
    const M = EV.M, S = EV.s, e = EV.e, rep = EV.repNow(), m = M.meta || {}, live = S.step == null || S.step >= M.steps.length - 1, txt = EV.repTxt;
    const head = `<h2>What it proposes</h2><p class="sec-q">What does it recommend, on what evidence, and where does that stop being true?</p>`;
    const open = `<p class="sm noprint" style="margin-top:10px">open on the right: ${rep ? '<a data-act="open" data-t="report" data-id="report">the full final report</a> · ' : ''}<a data-act="open" data-t="brief" data-id="brief">the brief</a> · <a data-act="open" data-t="session" data-id="${e(M.id)}">the session's summary</a></p>`;
    // a running session: the parts of the report as empty places, which the final report fills when it arrives: six, and a seventh ("What limits the
    // result") in a session whose instructions ask the report for it (the harness since 2026-11-15; the session's own prompt says so)
    const asksLimit = typeof m.prompt === 'string' && m.prompt.includes('- limit:');
    const now = EV.liveNow(), due = !!now && now.phase === 'reply', parts = now ? `<div id="pr-slots" data-slot="report">${[['The aim', 'what it set out to find'], ['The proposed adjustment', 'the settings it recommends, beside where the session started'], ['The expected result', 'what it expects those settings to give'], ...(asksLimit ? [['What limits the result', 'why it is not better, and the settings that made no meaningful difference']] : []), ['Because', 'its claims, each with its evidence'], ['But', 'where the recommendation stops being true'], ['The explanation', 'in its own words']]
      .map(([t, says], i) => `<div class="pr-b pr-slot"><h3><span class="st-n">${i + 1}</span>${t}</h3><p class="sm"><span class="mut">empty</span> · ${says}</p></div>`).join('')}</div>` : '';
    if (!rep) return `<div class="ev-card" id="s-proposes">${head}${live ? `<p id="ov-none"><b>No final report${M.ended ? '' : ' yet'}.</b> ${M.ended ? `The session ended: ${m.how ? e(m.how) : EV.nr}.` : `The session is still running${due ? `: ${now.mode ? 'the final report is due in the reply being written' : 'the reply being written may hold it'}` : ''}.`}</p>${parts}` : '<p id="ov-none" class="sm">No final report by this step.</p>'}${open}${EV.shareBar()}</div>`;
    const R = EV.recParts(), X = EV.expRows(rep), kn = (M.brief && M.brief.knobs) || {}, g = (M.brief && M.brief.goal) || {}, lab = k => EV.label(k, (kn[k] || {}).meaning);
    // 1 · the aim, and who set it: the brief's goal in words when the operator gave one; the goal the AI states in its report when the brief left it open
    const aim = g.kind === 'given' ? `<p id="pr-aim" data-aim="given"><b>Find ${EV.aimWords(g) || 'not recorded'}.</b> <span class="st-by" data-by="operator"><i class="sw"></i>set by the operator</span></p><p class="sm lc4" id="ov-goal" data-own="model" title="The goal as the final report states it">${txt(rep.goal)}</p>`
      : `<p id="pr-aim" data-aim="${g.kind === 'open' ? 'open' : ''}"><span id="ov-goal" class="lc4" data-own="model">${txt(rep.goal)}</span></p><p class="sm"><span class="st-by" data-by="model"><i class="sw"></i>${g.kind === 'open' ? 'chosen by the AI' : 'as the final report states it'}</span>${g.kind === 'open' ? ` · the brief left the aim open, and the AI states its aim here, <b class="aim-end">at the end</b>` : M.brief ? '' : ` · the brief: ${EV.nr}`}</p>`;
    // 2 · the proposed adjustment: each recommended setting that differs, beside the value the session started from (the brief's default)
    const adj = !R ? EV.nr : R.text ? e(R.text) : `<p id="ov-rec" class="pr-adj" data-exact="1">${R.differ.map(([k, v]) => `<span class="rk" data-knob="${e(k)}">${lab(k)} <b>${k in kn ? e(EV.adjVal(k, kn[k].default)) + ' → ' : ''}${e(EV.adjVal(k, v))}</b></span>`).join('<span class="pr-sep">, </span>') || (R.known ? '<span class="sm">no setting differs from where the session started</span>' : EV.nr)}</p>
      ${R.known ? `<p class="sm" id="ov-def" data-exact="1">everything else unchanged${R.same.length || R.unnamed.length ? `: ${[...R.same.map(([k, v]) => `${EV.LABEL[k] || k} ${EV.setVal(k, v)}`), ...R.unnamed.map(k => `${EV.LABEL[k] || k} ${EV.setVal(k, kn[k].default)} (not named in the report)`)].map(e).join(' · ')}` : ''}</p>` : ''}`;
    // 3 · the expected result: the target's measure and those the conditions name
    const left = X ? X.all.length - X.top.length : 0;
    const exp = !X ? `<p class="lc4">${e(String(rep.expected ?? 'not recorded'))}</p>` : `<table class="xr" id="ov-exp-top"><tbody>${X.top.map(X.row).join('')}</tbody></table>${left ? `<p class="sm" id="ov-exp-more"><a data-act="open" data-t="report" data-id="report">${left} more in the final report</a></p>` : ''}`;
    // 4 and 5 · because, and but: the claims by their role; a report recorded without roles: one list
    const roles = M.claims.length > 0 && M.claims.every(q => q.role), of = r => M.claims.filter(q => q.role === r), group = ([r, , says]) => (of(r).length ? `<p class="pr-role sm" data-role="${r}">${EV.term('Claim', 'claims')} that ${says}</p><div class="claims">${of(r).map(EV.claimBtn).join('')}</div>` : '');
    // what limits the result (why it is not better) and the settings whose tested values made no meaningful difference: two parts of a report since
    // 2026-11-15, in the AI's words and by its own list; a report recorded before has neither, and then the page shows no such part
    // the short report of a supervised session (2026-11-18) states its aim, its recommendation, what limits the result, its explanation and its claims: the parts it is
    // not asked for (the expected values, the list of settings that made no difference, when it holds and breaks) have no block here
    const short = !!M.supervised && typeof rep.holds_when === 'string' && !rep.holds_when.trim() && !rep.breaks_when.trim() && !Object.keys(rep.expected || {}).length; let nth = 0; const nx = () => ++nth;
    const nd = short ? null : Array.isArray(rep.no_difference) ? rep.no_difference : null, hasLim = typeof rep.limit === 'string' && rep.limit.trim() !== '';
    const lim = hasLim || nd ? `${hasLim ? `<p id="pr-limit" data-own="model">${txt(rep.limit)}</p>` : ''}${nd ? `<p class="sm" id="pr-nodiff" data-exact="1">${nd.length ? `Made no meaningful difference, by its own list: ${nd.map(k => `<span class="nd-k" data-knob="${e(k)}">${lab(k)}</span>`).join(', ')}` : 'Its list of settings that made no meaningful difference is empty.'}</p>` : ''}` : '';
    const diag = roles && of('background').length ? EV.ROLES.filter(q => q[1] === 'diagnosis').map(group).join('') : '', nb = i => i + (diag ? 1 : 0) + (lim ? 1 : 0);  // the diagnosis: a part of its own, before the reasons
    // the line of the counts, and under it the print button, which is always there (greyed until a claim is chosen): choosing a claim changes no height
    const counts = `<p class="sm" id="pr-counts">${EV.claimCounts(M.claims)}</p><p class="sm noprint" id="pr-print"><button data-act="print" data-id="${S.claim || ''}"${S.claim ? '' : ' disabled title="Choose a claim first"'}>print the evidence sheet${S.claim ? ` of claim ${S.claim}` : ' of a claim'}</button></p>`;
    const mis = EV.moments(M).report, when = `<div class="ov-when"><h4>Holds when</h4><p data-own="model">${txt(rep.holds_when)}</p><h4>Breaks when</h4><p data-own="model">${txt(rep.breaks_when)}</p></div>`;
    const because = !M.claims.length ? '<p class="sm">The report states no claims.</p>' : roles ? (EV.ROLES.filter(q => q[1] === 'because').map(group).join('') || '<p class="sm">No claim is given as a reason.</p>') : `<p class="sm" id="pr-noroles">This report was recorded before claims had roles: its claims in one list.</p><div class="claims">${M.claims.map(EV.claimBtn).join('')}</div>`;
    const but = `${roles ? EV.ROLES.filter(q => q[1] === 'but').map(group).join('') || '<p class="sm">No claim says when the recommendation would change.</p>' : ''}${when}`;
    const blk = (n, key, title, body) => `<div class="pr-b" data-pr="${key}"><h3><span class="st-n">${n}</span>${title}</h3>${body}</div>`;
    return `<div class="ev-card" id="s-proposes">${head}<div id="s-report" data-by="model">
        ${blk(nx(), 'aim', 'The aim', aim)}${blk(nx(), 'adjust', 'The proposed adjustment', adj)}${short ? '' : blk(nx(), 'expected', 'The expected result', exp)}
        ${lim ? blk(nx(), 'limit', 'What limits the result', lim) : ''}${diag ? `<div class="pr-b" data-pr="diagnosis"><h3><span class="st-n">${nx()}</span>${EV.term('Diagnosis', 'Its diagnosis')}</h3>${diag}</div>` : ''}${blk(nx(), 'because', roles || !M.claims.length ? 'Because' : 'Its claims', because + counts)}${short ? '' : blk(nx(), 'but', 'But', but)}
        <details class="pr-b" data-pr="explanation" id="pr-expl"${S.more || S.full ? ' open' : ''}><summary><h3 style="display:inline"><span class="st-n">${nx()}</span>The explanation</h3> <span class="sm">folded · the model's own words</span></summary><div id="ov-expl" data-own="model">${txt(rep.explanation)}</div></details>
        ${mis ? `<p class="sm" data-step="${mis.step}">${EV.warn('a number in the report differs from its measurement', `It wrote “${mis.rows[0].written}”; measured ${mis.rows[0].measured}`)} · <a data-act="open" data-t="report" data-id="report">the report's numbers against the measurements</a></p>` : ''}</div>${open}${EV.shareBar()}</div>`;
  },

  // ---- how to read this page: open on a reader's first visit, closed afterwards
  howTo() {
    return `<details class="ev-card" id="s-how"${EV.s.how || EV.s.full ? ' open' : ''}><summary><b class="how-h">How to read this page</b> <span class="sec-q">What is a turn, a test, a check?</span></summary>
      <div class="ev-top" style="margin-top:10px"><div><h3>How a session is built<span class="sm"> · this session's counts; click a box to go to that part</span></h3>${EV.structureMap()}</div>
        <div><h3>Who produced it</h3>${EV.legend()}<h3>The turn loop</h3>${EV.turnLoop()}</div></div>
      <h3>The words</h3><table><tbody>${Object.entries(EV_DEF).map(([k, v]) => `<tr><td style="white-space:nowrap"><b>${EV.e(k)}</b></td><td>${EV.e(v)}</td></tr>`).join('')}</tbody></table>
      <h3>Using the page</h3><ul class="sm" id="how-use" style="margin:0;padding-left:18px">
        <li>A record's name is a letter and a number: <b>H</b> hypothesis, <b>X</b> experiment, <b>S</b> simulation, <b>E</b> result table, <b>C</b> check, <b>V</b> verdict, <b>N</b> note of the harness, <b>Q</b> request to a tool, <b>T</b> tool result, <b>R</b> final report. The number is its order in the session.</li>
        <li>Whatever can be clicked shows the pointer and a change of background under it. A click never moves the page: what is chosen opens in the pane on the right.</li>
        <li>A few clicks do move the page. A turn's name in “The session at a glance” brings the notebook to that turn. A row of “What it needed to find out” brings its notebook card into view.</li>
        <li>A box of “How a session is built” goes to its part of the page. So does a line of “How it worked as a researcher” that names a section. The guided walk goes from section to section.</li>
        <li>“What it needed to find out”: the board shows each hypothesis in the column of its turn; an arrow leads to a hypothesis that follows from it, in the colour of the result that led onward. Point at a box to read why it matters, what it follows from and what was found; click it to open its test.</li>
        <li>A test's detail: a box of its picture opens what it stands for directly under the picture (a simulation, the verdict, the hypothesis that followed); the test stays in view.</li>
        <li>“The same, test by test”, under the board: click a row to go to its card in the notebook. The notebook: click a card to open its test; a number in “Result” opens its simulation.</li>
        <li>“Looking closer”: click a line to open that view. Best so far, and the simulations of each turn: click a dot to open that simulation.</li>
        <li>“The system”: click an object to see its settings beside the picture. “What this session is made of”: click a mark to open it; point at a mark to read what it is.</li>
        <li>The session flow, the tree and the tests list: click an item or a row to open it. The session's summary: click any item on the left to open it there.</li>
        <li>An experiment's panel: click a test or a simulation to open it. A simulation's charts over time: point at a chart, and the same moment is marked in all of them.</li>
        <li>The Operator tab, the sweep: click a numbered circle to open that simulation; a dark circle stands for several at one place, and a click lists them under the map.</li>
        <li>A session that is running: the banner at the top says where the work is, and for how long. A dashed square, or the word “empty”, is a place whose record is not there yet; a pulsing dot marks the places the work can fill next.</li>
        <li>The page reads new records by itself and marks them for half a minute. It never moves by itself: what you are reading stays where it is, and when a new turn begins a small note under the banner says so (its button takes you there). A place that is never filled stays drawn empty after the session ended.</li>
        <li>A word with a dotted line under it is a setting, a measure or a part of the network. Point at it, or reach it with the Tab key, and a small box says what it is; the text itself is never changed.</li>
        <li>Point at a part of the picture in “The setting”, and its settings and the measures taken there are set off wherever they stand on the page. Point at a marked word, and its part of the picture is set off.</li>
        <li>Home: click a row to open that session; click a column title to sort. Compare sessions: tick two or more to see them side by side; click a first test that held to open it in its session.</li></ul>
      <p class="sm">“Work log”: the sequence of the model's steps and its stated reasons. “Operator columns”: anything operator-only, shown when the switch at the top is on.</p></details>`;
  },

  sessionTab() {
    return `${EV.headStrip()}${EV.legendBar()}${EV.banner ? EV.banner() : ''}${EV.settingCard()}${EV.M.supervised ? EV.agentsCard() : ''}${EV.glance()}${EV.turnsCard()}${EV.findCard()}
      <div class="ev-main"><div>${EV.notebookCard()}${EV.proposesCard()}${EV.researchCard()}${EV.closerCard()}</div>
        <div class="ev-side"><div class="ev-card" id="p-detail">${EV.paneTabs()}${EV.s.pane === 'queue' ? EV.queueView() : ''}${EV.detail()}</div></div></div>${EV.howTo()}`;
  },
});
EV.act = Object.assign(EV.act || {}, { more() { EV.s.more = !EV.s.more; EV.draw(); } });
