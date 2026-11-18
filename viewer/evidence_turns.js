// Turn by turn: who did what (the operator's proposal of 2026-11-18). One column for each entity (the researcher, the supervisor or the judge,
// the harness, ns-3), one band for each turn, time runs down, and every object of the ledger (a guess, a hypothesis, a review, an experiment,
// its simulations, a check, a ruling ...) is a box of its own in the column of whoever made it. A box's id opens that record; a turn folds.
Object.assign(EV, {
  TN_COLS: {
    model: ['Researcher', 'the AI that proposes', 'guesses, hypotheses, tests and their rules, requests to look, objections, the report'],
    supervisor: ['Supervisor', 'the AI asked apart', 'reads each guess against its records, reviews each test before it runs, rules on each tested hypothesis'],
    judge: ['Judge', 'the AI asked apart', 'reads whether each hypothesis follows from the guess it names'],
    harness: ['Harness', 'the program, fixed rules', 'what it accepts and refuses, what the tools return, the result tables, the checks computed from the numbers'],
    simulator: ['ns-3', 'runs the simulations', 'each simulation and what it measured: the only source of measured numbers'] },
  TN_TOGETHER: ['simulation', 'request', 'result', 'note'],   // kinds that come many at a time: those that follow each other share one box; every other object has a box of its own
  // the column of a record: who made it. A verdict is the supervisor's in a two-agent session and the researcher's otherwise
  tnCol(r) { return r.type === 'judge' ? 'judge' : r.type === 'review' ? 'supervisor' : r.type === 'simulation' ? 'simulator' : r.type === 'verdict' ? (r.by === 'supervisor' ? 'supervisor' : 'model') : r.by === 'model' ? 'model' : EV_BY[r.type] === 'model' && r.by !== 'harness' ? 'model' : 'harness'; },
  // one record in words: [what it is, what it says, warn]
  tnSays(r) {
    const b = r.body || {}, cut = (s, n) => { s = String(s == null ? '' : s).replace(/\s+/g, ' ').trim(); return s.length > n ? s.slice(0, n - 1) + '…' : s; }, n = (k, w) => `${k} ${w}${k === 1 ? '' : 's'}`;
    switch (r.type) {
      case 'why': return ['guess of why', cut(b.guess, 190)];
      case 'rethink': return ['looks again at ' + (b.for || 'a guess'), `now ${b.now || ''}: ${cut(b.because, 150)}`];
      case 'hypothesis': return ['hypothesis' + (b.from_why ? ' from ' + b.from_why : ''), cut(b.text, 190)];
      case 'judge': return ['reads a new hypothesis against its guess', `${b.follows ? 'the hypothesis follows from the guess' : 'the hypothesis does not follow from the guess'}: ${cut(b.because, 150)}`, !b.follows];
      case 'drop': return ['gives up ' + (b.for || 'a hypothesis'), cut(b.reason, 150)];
      case 'experiment': { const rules = (b.decision_rules || []).map(d => d.decision_rule).filter(Boolean);
        return [b.kind === 'test' ? 'test of ' + (b.tests || []).join(', ') : r.by === 'harness' ? 'baseline' : 'exploration', `${n((b.runs || []).length, 'simulation')} planned${rules.length ? ' · decided by: ' + cut(rules.join(' ; '), 150) : b.question ? ' · ' + cut(b.question, 150) : ''}`]; }
      case 'simulation': return ['simulation', `${b.label || ''}${b.same_as ? ' (returned from ' + b.same_as + ', not run again)' : ''}${b.error ? ' · no measurements' : ''}`, !!b.error];
      case 'evidence': return ['result table', n((b.lines || []).length, 'line') + ', one for each simulation'];
      case 'check': return ['check for ' + (b.for || ''), `${b.result === 'held' ? 'HELD' : b.result === 'failed' ? 'FAILED' : String(b.result || '')}: ${cut(b.with_numbers || b.decision_rule, 140)}`];
      case 'verdict': return [(r.by === 'supervisor' ? (b.after ? 'second ruling on ' : 'ruling on ') : 'verdict on ') + (b.for || ''), `${b.result || ''}: ${cut(b.because, 150)}`];
      case 'review': { const ok = b.decision === 'approved', what = b.gate === 'ground' ? `reads the guess ${b.for || ''} against its records` : `reviews the test of ${b.for || ''} before any simulation`;
        return [what, `${ok ? 'approved' : b.decision === 'contested' ? 'still objects (it is run all the same)' : 'sent back'}${ok ? '' : ': ' + cut(b.because, 150)}`, !ok]; }
      case 'objection': return ['objects to the ruling ' + (b.to || ''), cut(b.because, 160)];
      case 'request': return ['asks to look', `${b.tool || ''}(${cut(Object.entries(b.args || {}).filter(([, v]) => v != null).map(([k, v]) => `${k}: ${v}`).join(', '), 110)})`];
      case 'result': return ['returns what ' + (b.tool || 'the tool') + ' read', cut(b.result, 120), /^error/.test(String(b.result || ''))];
      case 'note': return r.by === 'model' ? ['observations', cut(b.observations || b.text, 190)] : b.part ? ['refuses a part of the answer: ' + b.part, cut(b.reason || b.text, 190), true] : ['note', cut(b.text, 190)];
      case 'malformed': return ['cannot use the answer', cut(((b.refused || []).map(q => `${q.part}: ${q.reason}`).join(' | ')) || b.error, 190), true];
      case 'report': return ['final report', 'recommends ' + cut(Object.entries(b.recommendation || {}).map(([k, v]) => `${k} ${v}`).join(', '), 170)];
      default: return [r.type, cut(b.text || '', 150)];
    }
  },
  tnfold(id) { const S = EV.s; S.tnShut = S.tnShut || {}; S.tnShut[id] = !S.tnShut[id]; EV.draw(); },
  turnsCard() {
    const M = EV.M, e = EV.e, recs = (M.recs || []).filter(r => r.type !== 'draft' && r.type !== 'scratch'); if (!recs.length) return '';
    const cols = ['model', ...(M.supervised ? ['supervisor'] : recs.some(r => r.type === 'judge') ? ['judge'] : []), 'harness', 'simulator'], shut = EV.s.tnShut || {};
    const head = `<div class="tn-head tn-grid" style="--n:${cols.length}">${cols.map(c => { const [name, who, owns] = EV.TN_COLS[c];
      return `<div class="tn-col" data-by="${c === 'judge' ? 'supervisor' : c}" title="${e(name + ' (' + who + '). Its boxes: ' + owns + '.')}"><b><i class="sw" data-by="${c === 'judge' ? 'supervisor' : c}"></i>${e(name)}</b> <span class="sm">${e(who)}</span><small>${e(owns)}</small></div>`; }).join('')}</div>`;
    const st = id => M.recStep[id] ?? 0, turns = [...new Set(recs.map(r => r.turn))].sort((a, b) => a - b);
    const bands = turns.map(t => {
      const rs = recs.filter(r => r.turn === t), U = rs.find(r => r.type === 'turn'), body = rs.filter(r => r.type !== 'turn'), groups = [];
      // boxes in the order of the ledger; the simulations of an experiment, the requests of a turn and what the tools return share a box where they follow each other
      body.forEach(r => { const c = EV.tnCol(r), g = groups[groups.length - 1]; if (g && g.c === c && g.type === r.type && EV.TN_TOGETHER.includes(r.type)) g.rs.push(r); else groups.push({ c, type: r.type, rs: [r] }); });
      const count = cols.map(c => groups.filter(g => g.c === c).reduce((a, g) => a + g.rs.length, 0));
      const boxes = groups.map(g => { const items = g.rs.map(r => { const [what, says, warn] = EV.tnSays(r);
          return `<div class="tn-item${warn ? ' warnc' : ''}" data-step="${st(r.id)}"${EV.freshAttr ? EV.freshAttr(r.id) : ''}><span class="tn-id">${EV.link(r.id)}</span> <b>${e(what)}</b>${says ? `<span class="tn-says" title="${e(says)}">${e(says)}</span>` : ''}</div>`; }).join('');
        return `<div class="tn-box" data-by="${g.c === 'judge' ? 'supervisor' : g.c}" data-kind="${g.type}" data-step="${Math.min(...g.rs.map(r => st(r.id)))}" style="grid-column:${cols.indexOf(g.c) + 1}">${items}</div>`; }).join('');
      const left = U ? `${U.body.simulations_left} simulations left` : t === 0 ? 'before the first turn: the harness runs the baseline' : '', k = Math.min(...rs.map(r => st(r.id)));
      return `<section class="tn-turn" data-turn="${t}" data-step="${k}"><button class="tn-band" data-act="tnfold" data-id="${t}" aria-expanded="${!shut[t]}" title="${shut[t] ? 'Show' : 'Fold'} this turn"><span class="lc-tw">${shut[t] ? '▸' : '▾'}</span> <b>${t === 0 ? 'Start' : 'Turn ' + t}</b> <span class="sm">${e(left)}</span>
          <span class="sm tn-count">${cols.map((c, i) => count[i] ? `${EV.TN_COLS[c][0]} ${count[i]}` : '').filter(Boolean).join(' · ')}</span></button>
        ${shut[t] ? '' : `<div class="tn-grid tn-rows" style="--n:${cols.length}">${boxes}</div>`}</section>`; }).join('');
    return `<div class="ev-card" id="s-turns"><h2>Turn by turn: who did what <small>time runs down · each record is a box in the column of whoever made it · a box's id opens it</small></h2>
      <p class="sm tn-op"><i class="sw" data-by="operator"></i><b>Operator</b> (you): the ${EV.link('brief')}, written before the first turn. Nothing below changes it.</p>
      ${head}${bands}</div>`;
  },
});
