// A session's page. Everything on it belongs to one of three levels of detail:
//   1 · at a glance   the header strip; the setting (evidence_system.js); the session at a glance (evidence_glance.js);
//                     what it needed to find out (evidence_find.js). Open, at the top, at full width.
//   2 · read          the work, step by step: the notebook (evidence_notebook.js); what it proposes (the final report);
//                     below level 1, in the left column, beside the detail pane.
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

  // ---- the first thing a reader reads: the answer, in one band. Four columns: the goal (four lines at most), the
  // recommended settings, the expected result in short, the claims in numbers. The claims themselves, the explanation
  // and the full expected result are in the card "The final report", which stands beside the detail pane.
  overview() {
    const M = EV.M, S = EV.s, e = EV.e, rep = EV.repNow(), m = M.meta || {}, live = S.step == null || S.step >= M.steps.length - 1, R = EV.recParts(), X = EV.expRows(rep);
    const name = k => e(TH_DATA.KNOB[k] || k), val = (k, v) => e(TASK_VIEW._rate(String(EV.val(k, v)))).replace(/^Tcp/, '');
    const recHtml = !R ? EV.nr : R.text ? e(R.text) : `<div class="rec" id="ov-rec">${R.differ.map(([k, v]) => `<span class="rk" data-knob="${e(k)}"><span>${name(k)}</span><b>${val(k, v)}</b></span>`).join('') || (R.known ? '<span class="sm">no knob differs from the brief’s default</span>' : EV.nr)}</div>
      ${R.same.length ? `<p class="sm" id="ov-def">at the brief's default: ${R.same.map(([k, v]) => `${name(k)} ${val(k, v)}`).join(' · ')}</p>` : ''}${R.unnamed.length ? `<p class="sm">not named in the report: ${R.unnamed.map(name).join(', ')}</p>` : ''}`;
    const left = X ? X.all.length - X.top.length : 0;
    const expHtml = !X ? `<p class="lc4">${e(String((rep && rep.expected) ?? 'not recorded'))}</p>` : `<table class="xr" id="ov-exp-top"><tbody>${X.top.map(X.row).join('')}</tbody></table>${left ? `<p class="sm" id="ov-exp-more">${left} more in the final report</p>` : ''}`;
    const n = k => M.claims.filter(q => q.kind === k).length;
    const counts = !M.claims.length ? '<p class="sm">The report states no claims.</p>' : `<div id="ov-claims" data-counts="${EV.CLAIM_KINDS.map(([k]) => n(k)).join(',')}"><div><b>${M.claims.length}</b> claim${M.claims.length === 1 ? '' : 's'}</div>${EV.CLAIM_KINDS.map(([k, t]) => `<div${k === 'none' && n(k) ? ' class="warnc"' : ''}><b>${n(k)}</b> ${t}</div>`).join('')}</div>
      <p class="sm">Each claim, with the evidence it cites, is in The final report, beside the detail pane.</p>`;
    const body = !rep ? (live ? `<p id="ov-none"><b>No final report.</b> ${M.ended ? `The session ended: ${m.how ? e(m.how) : EV.nr}.` : 'The session is still running.'}</p>` : '<p id="ov-none" class="sm">No final report by this step.</p>')
      : `<div class="ov ov-band"><div><h3>The goal</h3><p id="ov-goal" class="lc4">${EV.repTxt(rep.goal)}</p></div><div><h3>Recommended settings</h3>${recHtml}</div>
          <div><h3>Expected result</h3>${expHtml}</div><div><h3>Its claims</h3>${counts}</div></div>`;
    // without a final report there is no card "The final report": the line that opens the brief and the summary stays here
    const open = rep ? '' : `<p class="sm noprint">open on the right: <a data-act="open" data-t="brief" data-id="brief">the brief</a> · <a data-act="open" data-t="session" data-id="${e(M.id)}">the session's summary</a></p>`;
    return `<div id="s-overview">${body}${open}</div>`;
  },
  repTxt: v => (Array.isArray(v) ? v.map(q => EV.e(q)).join(' · ') : EV.e(v ?? 'not recorded')),

  // ---- "The final report", at the head of the left column, so that it stands beside the detail pane: a click on a
  // claim opens its test there, in view. The model's own words: its claims with the evidence each one cites, the
  // explanation (six lines, then "more"), the full expected result, when it holds, when it breaks.
  // A session without a final report has no such card; in the replay it appears at the step of the final report.
  reportCard() {
    const M = EV.M, S = EV.s, e = EV.e, rep = EV.repNow(), X = EV.expRows(rep), txt = EV.repTxt; if (!rep) return '';
    const claims = !M.claims.length ? '<p class="sm">The report states no claims.</p>' : `<h3>Its claims</h3><div class="claims">${M.claims.map(q => { const n = q.evidence.filter(id => (EV.marks['rec:' + id] || {}).tick).length;
        return `<button class="chip claim${S.claim === q.n ? ' on' : ''}" data-act="claim" data-id="${q.n}" data-kind="${q.kind}"><b>claim ${q.n}</b><span class="ct">${e(q.text)}</span><span class="sm cl-ev">${EV.claimMarks(q, EV.seen)}${q.evidence.length ? ` · ${q.evidence.length} evidence item${q.evidence.length === 1 ? '' : 's'}` : ''}${n ? ` · ${n} reviewed` : ''}</span></button>`; }).join('')}</div>
      <p class="sm">${EV.claimCounts(M.claims)}${S.claim ? ` · <button data-act="print" data-id="${S.claim}">print evidence sheet for claim ${S.claim}</button>` : ''}</p>`;
    const expHtml = !X ? `<p>${e(String(rep.expected ?? 'not recorded'))}</p>` : `<table class="xr" id="ov-exp"><tbody>${X.all.map(X.row).join('')}</tbody></table>`;
    return `<div id="s-report" data-by="model"><h3 class="rep-h">The final report <span class="sm">the model's own words: its claims with the evidence each one cites, then its explanation</span></h3>${claims}
      <h3>Explanation</h3><div id="ov-expl" class="${S.more || S.full ? '' : 'clamp'}">${txt(rep.explanation)}</div>${S.full ? '' : `<a class="noprint sm" data-act="more">${S.more ? 'less' : 'more'}</a>`}
      <h3>Expected result</h3>${expHtml}<div class="ov-when"><h3>Holds when</h3><p>${txt(rep.holds_when)}</p><h3>Breaks when</h3><p>${txt(rep.breaks_when)}</p></div>
      <p class="sm noprint" style="margin-top:10px">open on the right: <a data-act="open" data-t="report" data-id="report">the full final report</a> · <a data-act="open" data-t="brief" data-id="brief">the brief</a> · <a data-act="open" data-t="session" data-id="${e(M.id)}">the session's summary</a></p></div>`;
  },

  // ---- "What it proposes": the answer, after the work that led to it. The band of four columns (the goal, the
  // recommended settings, the expected result in short, the claims in numbers), then the model's own words. A session
  // without a final report says so here, with how it ended.
  proposesCard() {
    return `<div class="ev-card" id="s-proposes"><h2>What it proposes</h2><p class="sec-q">What does it recommend, on what evidence, and where does that stop being true?</p>${EV.overview()}${EV.reportCard()}${EV.shareBar()}</div>`;
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
