// What a session is made of, as one picture at the top of its page: a column per turn, a row per kind of item, one mark
// per item. Down a column stand a hypothesis, its decision rule, the simulations of the turn's experiment, the check and
// the verdict: together one test. A mark opens its item in the pane on the right (the page does not move); pointing at
// it marks what belongs with it and says in words what it is. During the replay nothing recorded after the chosen step
// is drawn here at all: a later item is an empty dot, with no text, state or title; the key and the sentence under the
// table name only what is recorded by then. The card is not printed (the page prints four parts, and this is not one).
// It folds like the card "The system": a "fold" button in its heading, and the browser remembers it.
// A place whose record is not there is drawn as an empty place (a dashed square, EV.slot): a check or a verdict a test
// does not have, the final report; in a running session also the simulations an experiment waits for and the places the
// reply being written may fill, marked as where the work is (evidence_live.js). Not during the replay.
// Under each turn's name its header says how many simulations were left at its start ("not recorded" before s008).
// ======================================================================================================
Object.assign(EV, {
  // the hypotheses, tests and simulations that belong with an item (the selected one, or the one pointed at)
  glInfo(sel) {
    const M = EV.M, o = { hyps: new Set(), tests: new Set(), sims: new Set() }; if (!sel || !M) return o;
    const test = (T, withSims) => { o.tests.add(T.id); o.hyps.add(T.hyp); if (withSims) T.sims.forEach(q => o.sims.add(q.id)); };
    if (sel.t === 'test' && M.testById[sel.id]) test(M.testById[sel.id], true);
    else if (sel.t === 'hyp' && M.hypById[sel.id]) { o.hyps.add(sel.id); M.hypById[sel.id].tests.forEach(q => test(M.testById[q], true)); }
    else if (sel.t === 'sim' && M.simById[sel.id]) { o.sims.add(sel.id); M.tests.filter(T => T.sims.some(q => q.id === sel.id)).forEach(T => test(T, false)); }
    else if (sel.t === 'exp' && M.expById[sel.id]) { M.expById[sel.id].sims.forEach(q => o.sims.add(q.id)); M.tests.filter(T => T.exp === sel.id).forEach(T => test(T, false)); }
    return o;
  },

  // one sentence that says what an item is and what it consists of; only what is recorded by the replay's step
  glSay(sel) {
    const M = EV.M, e = EV.e, seen = EV.seen, K = EV.gkey, by = (m, id) => (sel && sel.t === id ? m : null);
    const cut = (s, n) => { s = String(s || ''); return s.length > n ? s.slice(0, n - 1) + '…' : s; }, pl = (n, w) => `${n} ${w}${n === 1 ? '' : 's'}`;
    const now = (m, id) => (m && seen(id(m)) ? m : null), step = EV.s.step;  // nothing recorded after the replay's step is described, even while it is still selected
    const T = now(by(M.testById[sel && sel.id], 'test'), q => q.exp), h = now(by(M.hypById[sel && sel.id], 'hyp'), q => q.id), s = now(by(M.simById[sel && sel.id], 'sim'), q => q.id), x = now(by(M.expById[sel && sel.id], 'exp'), q => q.id);
    const t = by(M.turns.find(q => sel && q.n === sel.id && (step == null || (q.steps[0] ? q.steps[0].k : 0) <= step)), 'log');
    const xSay = q => (M.tests.some(u => u.exp === q.id) ? pl(M.tests.filter(u => u.exp === q.id).length, 'test') : q.by === 'harness' ? 'the baseline, run by the harness' : 'no tests: it explores “' + e(cut(q.question, 70)) + '”');
    if (T) { const hy = M.hypById[T.hyp], c = T.check && seen(T.check.id) ? T.check : null, v = T.verdict && seen(T.verdict.id) ? T.verdict : null;
      return `<b>Test of ${e(T.hyp)}</b> in experiment ${e(T.exp)}, turn ${T.turn}: ` + [`${K('hyp')}hypothesis “${e(cut(EV.hshort(hy), 64))}”`, T.rule ? K('rule') + 'its decision rule' : null, `${K('sim')}${pl(T.sims.length, 'simulation')}`,
        c ? `<span class="gn">${K(EV.ck(c.result))}check ${e(c.result)}</span>` : null, v ? `<span class="gn">${K(EV.vk(v.result))}verdict ${e(v.result)}</span>, given in turn ${v.turn}` : null].filter(Boolean).join(' → '); }
    if (h) { const st = EV.s.step == null ? h.state : EV_DATA.stateAt(M, EV.s.step)[h.id] || 'open', n = h.tests.filter(q => seen(M.testById[q].exp)).length;
      return `<b>${K('hyp')}Hypothesis ${e(h.id)}</b>, stated in turn ${h.turn}: “${e(cut(EV.hshort(h), 96))}” · ${e(st)} · ${n ? 'put to ' + pl(n, 'test') : 'not put to a test'}`; }
    if (s) { const names = M.tests.filter(q => q.sims.includes(s)).map(q => q.hyp);
      return `<b>${K(s.same_as ? 'sim-returned' : 'sim')}Simulation ${e(s.id)}</b> “${e(s.label || '')}” of experiment ${e(s.exp)}${s.turn ? ', turn ' + s.turn : ''} · ${names.length ? `named by the decision rule${names.length === 1 ? '' : 's'} of ${e(names.join(', '))}` : 'named by no decision rule'}${s.same_as ? ` · returned from ${e(s.same_as)}, not run again` : ''}${s.error ? ' · <span class="bad">no measurements</span>' : ''}`; }
    if (x) return `<b>Experiment ${e(x.id)}</b>${x.turn ? ', turn ' + x.turn : ', before the first turn'}: ${pl(x.sims.length, 'simulation')} · ${xSay(x)}`;
    if (t) { const n = k => k.filter(r => seen(r.id)).length, bits = [[n(t.verdicts), 'verdict'], [n(t.rulings || []), 'ruling' + (n(t.rulings || []) === 1 ? '' : 's') + ' by the supervisor', '', ''], [n(t.hyps), 'new hypothes', 'is', 'es'], [n(t.drops), 'dropped hypothes', 'is', 'es'], [n(t.malformed) + n(t.refusals), 'refusal']]
        .filter(q => q[0]).map(([k, w, one, many]) => `${k} ${w}${one === undefined ? (k === 1 ? '' : 's') : k === 1 ? one : many}`);
      if (t.exp && seen(t.exp.id)) bits.push(`experiment ${e(t.exp.id)} with ${pl(t.exp.sims.length, 'simulation')}`); if (t.report && seen(t.report.id)) bits.push('the final report');
      return t.n ? `<b>Turn ${t.n}</b>: ${bits.join(' · ') || ((w => w && w.phase === 'reply' && w.turn === t.n)(EV.liveNow && EV.liveNow()) ? '<span data-writing="1">the AI is writing its reply</span>' : 'nothing the harness could use')}${t.left == null ? '' : ` · ${pl(t.left, 'simulation')} left at its start`}` : `<b>Start</b>: the brief, and the baseline the harness ran before the model's first turn`; }
    if (sel && sel.t === 'report' && M.report && M.repRec && seen(M.repRec.id)) { const r = M.report.recommendation;
      return `<b>${K('report')}Final report</b>: ${pl(M.claims.length, 'claim')}${r && typeof r === 'object' ? ' · recommends ' + e(Object.entries(r).map(([k, v]) => `${k} ${v}`).join(', ')) : ''}`; }
    return 'Read a column downwards: the hypotheses the AI stated in that turn, the checks of their rules, the simulations run, and the verdicts it gave then. Point at a name to see what belongs with it.';
  },

  // how many of each kind the records hold by the replay's step
  glCounts() {
    const M = EV.M, S = EV.s, seen = EV.seen, ck = r => M.checks.filter(q => q.result === r && seen(q.id)).length;
    return { turn: M.turns.filter(t => t.n > 0 && (S.step == null || (t.steps[0] ? t.steps[0].k : 0) <= S.step)).length, hyp: M.hyps.filter(h => seen(h.id)).length, rule: M.tests.filter(T => T.rule && seen(T.exp)).length, sim: M.sims.filter(q => seen(q.id)).length,
      exp: M.exps.filter(x => seen(x.id)).length, check: M.checks.filter(q => seen(q.id)).length, held: ck('held'), failed: ck('failed'), void: ck('void'), verdict: M.recs.filter(r => r.type === 'verdict' && seen(r.id)).length, report: M.repRec && seen(M.repRec.id) ? 1 : 0 };
  },

  glance() {
    const fold = !EV.s.full && EV.glFolded === true, foldBtn = EV.s.full ? '' : `<button class="cl noprint" data-act="glfold" style="float:right">${fold ? 'unfold' : 'fold'}</button>`, n = EV.glCounts(), pl = (k, w, many) => `${k} ${k === 1 ? w : many || w + 's'}`;
    // the card is unfolded whenever the page is loaded: a fold holds only while this page stays open (EV.glFolded), the browser does not keep it
    // folded, its line carries its content: the counts, from the records
    if (fold) return `<div class="ev-card noprint" id="s-made"><h2>The session at a glance <small id="gl-fold" data-counts="${[n.turn, n.hyp, n.check, n.held, n.failed, n.sim].join(',')}">${pl(n.turn, 'turn')} · ${pl(n.hyp, 'hypothesis', 'hypotheses')} · ${EV.M.old ? 'checks ' + EV.nr : `${pl(n.check, 'check')}, ${EV.tally(n.held, n.failed, n.void)}`} · ${pl(n.sim, 'simulation')}</small> ${foldBtn}</h2></div>`;
    const M = EV.M, S = EV.s, e = EV.e, seen = EV.seen, live = S.step == null, sel = S.sel || {}, info = EV.glInfo(S.sel), st = live ? null : EV_DATA.stateAt(M, S.step);
    // a running session (evidence_live.js): where the work is, the places a reply may fill, the simulations an experiment still waits for
    const now = EV.liveNow(), reply = c => !!now && now.phase === 'reply' && !now.mode && c.t.n === now.turn, pend = c => (now && (now.phase === 'sims' || now.phase === 'baseline') && c.x && c.x.id === now.exp ? Math.max(0, (c.x.runs.length || 1) - c.x.sims.length) : 0);
    const claim = S.claim ? M.claims[S.claim - 1] : null, hitT = new Set(claim ? claim.tests : []), hitH = new Set(claim ? claim.hyps : []);
    const gap = '<i class="gm"></i>';   // an empty place
    const mark = (m, t, id, rec, title, cls) => { if (!seen(rec)) return '<i class="gm gp"></i>';  // m: the kind of mark (EV.GK), with "-again" for one drawn before
      const on = t === 'hyp' ? info.hyps.has(id) : t === 'test' ? info.tests.has(id) : t === 'sim' ? info.sims.has(id) : sel.t === t, hit = t === 'hyp' ? hitH.has(id) : t === 'test' && hitT.has(id);
      return `<a class="gm ${EV.GC[m.replace('-again', '')] || ''}${m.endsWith('-again') ? ' ag' : ''} ${cls || ''}${on ? ' on' : ''}${hit ? ' hit' : ''}" data-act="open" data-t="${t}" data-id="${e(id)}" data-m="${m}"${EV.freshAttr(rec)} title="${e(title)}">${EV.gk(m)}</a>`; };
    // ---- the columns: every turn recorded by the replay's step. A cell holds names and words, not shapes: a hypothesis is its name (a chip tinted by
    // how it ended, as its box on the board), a test is "H1 held" or "H1 failed", the simulations of a turn are a number, a verdict is "H1 supported"
    // in the turn it was GIVEN (the table reads left to right in time), the final report is the word "written".
    const cols = M.turns.filter(t => live || (t.steps[0] ? t.steps[0].k : 0) <= S.step).map(t => { const x = t.exp && seen(t.exp.id) ? t.exp : null; return { t, x, ts: x ? M.tests.filter(T => T.exp === x.id) : [] }; });
    const anyLeft = cols.some(c => c.t.n && c.t.left != null), room = document.getElementById('ev').clientWidth - 76, CW = Math.max(138, Math.min(300, Math.floor((room - 360) / Math.max(1, cols.length)) - 30)), per = Math.max(1, Math.floor((room - 360) / (CW + 30))), bands = []; cols.forEach((c, i) => { if (i % per === 0) bands.push([]); bands[bands.length - 1].push(c); });
    const stOf = h => (st ? st[h.id] || 'open' : h.state), tint = s => (['supported', 'refuted', 'inconclusive', 'dropped'].includes(s) ? ' st-' + s : ''), last = cols[cols.length - 1];
    const chip = (m, t, id, rec, text, title, cls, wd) => { if (!seen(rec)) return '';  // nothing recorded after the replay's step is drawn; wd: the card that opens when the chip is pointed at
      const on = t === 'hyp' ? info.hyps.has(id) : t === 'test' ? info.tests.has(id) : sel.t === t, hit = t === 'hyp' ? hitH.has(id) : t === 'test' && hitT.has(id);
      return `<a class="gm gc ${cls || ''}${on ? ' on' : ''}${hit ? ' hit' : ''}" data-act="open" data-t="${t}" data-id="${e(id)}" data-m="${m}"${EV.freshAttr(rec)}${wd ? ` data-wd="${e(wd)}"` : ''} title="${e(title)}">${text}</a>`; };
    const unjudged = live ? M.tests.filter(T => seen(T.exp) && !(T.verdict && seen(T.verdict.id))) : [];
    const cell = {
      hyp: c => c.t.hyps.filter(h => seen(h.id)).map(h => { const s = stOf(h); return chip(s === 'dropped' ? 'dropped' : 'hyp', 'hyp', h.id, h.id, e(h.id), `${h.id} · ${s === 'open' ? (M.ended ? 'not judged' : 'not judged yet') : s}: ${EV.hshort(h)}`, tint(s).trim(), 'h:' + h.id); }).join('')
        + (reply(c) ? EV.slot('hyp', 'A new hypothesis, if this reply states one', true) : ''),
      check: c => c.ts.map(T => { const k = T.check && seen(T.check.id) ? T.check : null, r = k ? (['held', 'failed', 'void'].includes(k.result) ? k.result : 'not-checked') : null;
        return k ? chip(r, 'test', T.id, k.id, `${e(T.hyp)} ${EV.gkey(r)}${r === 'not-checked' ? 'not checked' : r}`, k.void ? `${k.id} · ${EV.VOID}` : `${k.id} · the check of ${T.hyp} ${k.result}`, r === 'held' ? 'ok' : r === 'failed' ? 'bad' : 'mu', 't:' + T.id)
          : chip('rule', 'test', T.id, T.exp, e(T.hyp), T.rule ? `the test of ${T.hyp}: its decision rule is stated` : `the test of ${T.hyp}: no decision rule`, '', 't:' + T.id) + (live && T.rule ? EV.slot('check', pend(c) ? 'Its check: made when its simulations are back' : M.ended ? 'Not checked' : 'Not checked yet', pend(c) > 0) : ''); }).join(''),
      sim: c => (!c.x ? (reply(c) ? EV.slot('sim', 'Simulations, if this reply sets up an experiment', true) : '') : `<a class="gx gc${sel.t === 'exp' && sel.id === c.x.id ? ' on' : ''}" data-act="open" data-t="exp" data-id="${e(c.x.id)}" data-sims="${c.x.sims.filter(q => seen(q.id)).length}" data-wd="x:${e(c.x.id)}">${e(c.x.id)} · <b>${c.x.sims.filter(q => seen(q.id)).length}</b> simulation${c.x.sims.filter(q => seen(q.id)).length === 1 ? '' : 's'}</a>${c.x.sims.some(q => q.same_as && seen(q.id)) ? `<span class="sm gx-note" data-for="${e(c.x.id)}">${c.x.sims.filter(q => q.same_as && seen(q.id)).length} not run again</span>` : ''}`
        + (pend(c) ? `<i class="gm slot wk" data-slot="sim" data-n="${pend(c)}" title="${pend(c)} simulation${pend(c) === 1 ? '' : 's'} of ${e(c.x.id)}: the simulator is working on ${pend(c) === 1 ? 'it' : 'them'}"></i>` : '')),
      verdict: c => c.t.verdicts.concat(c.t.rulings || []).filter(v => seen(v.id)).map(v => { const T = M.tests.filter(q => q.verdict && q.verdict.id === v.id).pop(), r = v.body.result, odd = T && EV.contradicts(T.verdict, T.check ? [T.check] : []);
        return chip(EV.vk(r), T ? 'test' : 'hyp', T ? T.id : v.body.for, v.id, `${e(v.body.for)} ${e(r)}`, `${v.id} · ${v.body.for} ${r}, given in turn ${v.turn}${odd ? ' · disagrees with its check' : ''}`, `st-${EV.vk(r)}${odd ? ' odd' : ''}`, 'j:' + v.id); }).join('')
        + (c === last ? unjudged.map(T => `<i class="gm slot${now && now.phase === 'reply' && now.mode !== 'report' && T.check ? ' wk' : ''}" data-slot="verdict" data-hyp="${e(T.hyp)}" title="${e(!M.ended ? `${T.hyp}: not judged yet` : M.hypById[T.hyp] && M.hypById[T.hyp].verdict ? `${T.hyp}: no verdict here, the hypothesis was tested again first` : `${T.hyp}: no verdict was given`)}">${e(T.hyp)}</i>`).join('') : ''),
      report: c => (c.t.report && seen(c.t.report.id) ? chip('report', 'report', 'report', c.t.report.id, 'written', 'the final report') : live && !M.report && c === last ? EV.slot('report', M.ended ? 'No final report was given' : 'The final report: not written yet', !!now && now.phase === 'reply') : ''),
    };
    // the turn that is being worked on: its whole column stands out, in the way its column does on the board of "What it needed to find out" (a tinted ground with an edge, and "now" beside its name)
    const nowc = c => (now && now.turn === c.t.n ? ' class="gl-nowc"' : '');
    const row = (by, term, word, count, note, k, cs, first) => `<tr data-by="${by}" data-row="${k}"><th><i class="sw gby" title="produced by ${by === 'model' ? 'the AI' : by === 'simulator' ? 'ns-3' : 'the ' + by}"></i>${EV.term(term, word)}${first ? ` <b>${count}</b> <span class="sm">${note}</span>` : ''}</th>${cs.map(c => `<td${nowc(c)}><div class="gs" style="width:${CW}px">${cell[k](c)}</div></td>`).join('')}</tr>`;
    const head = cs => cs.map(c => { const r = c.t.malformed.concat(c.t.refusals).filter(q => seen(q.id)).length;
      return `<td${nowc(c)}><a class="gt${sel.t === 'log' && sel.id === c.t.n ? ' on' : ''}" data-act="turn" data-t="log" data-id="${c.t.n}" title="${c.t.n ? `Turn ${c.t.n}: open its work log and go to it in the notebook` : 'The start: go to it in the notebook'}">${c.t.n ? 'turn ' + c.t.n : 'start'}</a>${now && now.turn === c.t.n ? `<b class="gl-now-t"> · now</b>${EV.nowDot('The work is here: ' + EV.liveSay(now))}` : ''}${r ? `<span class="grf warnc" data-refused="${r}" data-wd="z:${c.t.n}" tabindex="0">${r} not accepted</span>` : ''}${
        c.t.n && anyLeft ? `<div class="gleft" data-left="${c.t.left ?? ''}" title="${c.t.left == null ? 'How many simulations were left at the start of this turn is not recorded (sessions before s008)' : `${c.t.left} simulation${c.t.left === 1 ? ' was' : 's were'} left at the start of turn ${c.t.n}`}">${c.t.left == null ? EV.nr : c.t.left + ' left'}</div>` : ''}</td>`; }).join('');
    EV._gl = '';
    const table = (cs, i) => `<table class="gl gl2" data-band="${i}"><thead><tr data-by="harness"><th><i class="sw gby" title="produced by the harness"></i>${EV.term('Turn', 'Turns')}${i ? '' : ` <b>${n.turn}</b> <span class="sm">one answer of the AI each</span>`}</th>${head(cs)}</tr></thead><tbody>
        ${row('model', 'Hypothesis', 'Hypotheses', n.hyp, 'its hypotheses, by name', 'hyp', cs, !i)}
        ${row('harness', 'Check', 'Checks', n.check, M.old ? 'no checks by the harness' : 'each rule, checked by the harness', 'check', cs, !i)}
        ${row('simulator', 'Simulation', 'Simulations', n.sim, `in ${n.exp} ${n.exp === 1 ? 'experiment' : 'experiments'}`, 'sim', cs, !i)}
        ${row('model', 'Verdict', 'Verdicts', n.verdict, 'its verdicts, in the turn it gave them', 'verdict', cs, !i)}
        ${row('model', 'Final report', 'Final report', n.report, 'its answer', 'report', cs, !i)}</tbody></table>`;
    const tables = bands.map(table).join(''), blank = tables.includes('data-slot=');
    const tints = ['supported', 'refuted', 'inconclusive'].filter(k => M.recs.some(r => r.type === 'verdict' && r.body.result === k && seen(r.id))).map(k => `<span><i class="gm gc st-${k}" style="display:inline-flex">H</i> a hypothesis judged ${k}</span>`).join('');
    const key = `${tints}${M.hyps.some(h => h.drop && seen(h.drop.id)) ? '<span><i class="gm gc st-dropped" style="display:inline-flex">H</i> dropped</span>' : ''}${M.checks.some(q => q.result === 'void' && seen(q.id)) ? `<span>${EV.gkey('void')}${EV.VOID}</span>` : ''}${M.exps.some(x => x.by === 'harness' && seen(x.id)) ? '<span>X0: the harness\'s baseline, outside the budget</span>' : ''}${!anyLeft && cols.some(c => c.t.n) ? `<span id="gl-left">simulations left at each turn: ${EV.nr}</span>` : ''}`;
    const more = `${blank ? `<span id="gl-slot"><i class="gm slot" data-slot="eg" style="display:inline-flex"></i> ${M.ended ? 'never given' : 'not there yet'}</span>` : ''}${now ? `<span id="gl-now">${EV.nowDot()} where the work is now${now.phase === 'reply' ? ': the places this reply may fill' : ''} · a further turn appears only if the AI goes on</span>` : ''}`;
    return `<div class="ev-card noprint" id="s-made"><h2>The session at a glance <small>turn by turn, left to right in time: its hypotheses, the checks of their rules, its verdicts · ${M.old ? 'checks ' + EV.nr : `<span id="gl-tally">${EV.term('Check', 'checks')} ${EV.tally(n.held, n.failed, n.void)}</span>`}${bands.length > 1 ? ` · <span id="gl-bands">the ${cols.length} turns continue over ${bands.length} bands of rows</span>` : ''}</small> ${foldBtn}</h2><p class="sec-q">What happened overall?</p>
      <div class="gl-scroll" data-bands="${bands.length}">${tables}</div>
      <p class="gl-say" id="gl-say" data-own="model">${EV.glSay(S.sel)}</p>
      <p class="sm gl-key">${key}${more}<i class="gl-br"></i><span class="gl-note">click a name to open it beside the page</span><span class="gl-note" id="gl-form">the rows are the harness’s form of a turn, told to the AI in its prompt; what fills them is the AI’s</span></p></div>`;
  },

  // pointing at a mark: what belongs with it is marked, and the line below says what it is; away from the marks, the selected item again
  glHover(ev) {
    const m = ev.target.closest ? ev.target.closest('#s-made [data-act="open"]') : null, key = m ? m.dataset.t + ':' + m.dataset.id : ''; if (key === EV._gl || !EV.M) return; EV._gl = key;
    const say = document.getElementById('gl-say'); if (!say) return;
    const sel = m ? { t: m.dataset.t, id: m.dataset.t === 'log' ? Number(m.dataset.id) : m.dataset.id } : null, o = EV.glInfo(sel);
    document.querySelectorAll('#s-made a.gm').forEach(a => a.classList.toggle('hov', !!sel && (a.dataset.t === 'hyp' ? o.hyps.has(a.dataset.id) : a.dataset.t === 'test' ? o.tests.has(a.dataset.id) : a.dataset.t === 'sim' && o.sims.has(a.dataset.id))));
    say.innerHTML = EV.glSay(sel || EV.s.sel);
  },
});
EV.act = Object.assign(EV.act || {}, { glfold() { EV.glFolded = !EV.glFolded; EV.draw(); },
  // a turn's name: its work log opens in the detail pane, and the notebook comes to that turn (a stated exception to "a click never moves the page")
  turn(id) { const n = Number(id); EV.s.sel = { t: 'log', id: n }; EV.draw(); const el = document.querySelector(n ? `#s-notebook .nb-turn[data-turn="${n}"]` : '#s-notebook .nb-start'); if (el) el.scrollIntoView({ block: 'start' }); } });
document.getElementById('ev').addEventListener('mouseover', EV.glHover);
