// Turn by turn: who did what (the operator's proposal of 2026-11-18). One column for each entity (the researcher, the supervisor or the judge,
// the harness, ns-3), one band for each turn, time runs down, and every object of the ledger (a guess, a hypothesis, a review, an experiment,
// its simulations, a check, a ruling ...) is a box of its own in the column of whoever made it. A box's id opens that record; a turn folds.
// Since 2026-11-22 (the operator: the page showed too much) it is not a card of its own but the folded detail at the end of "What it needed to
// find out": closed on a first visit, open in Full, and the browser remembers whether the reader opened it ("ev-turns").
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
  // a text of an agent or of the harness, with every record id in it that exists (and is on the page at this step of the replay) as a link
  tnText(t) { const M = EV.M; return EV.e(String(t == null ? '' : t).replace(/\s+/g, ' ').trim()).replace(/\b[A-Z]{1,2}\d+\b/g, id => (M.byId[id] && EV.seen(id) ? EV.link(id) : id)); },
  // one record: { what: its kind in words, says: what was said or done (in full), ground: [label, html] rows of what it rests on, more: [label, long text] kept folded, warn }
  tnSays(r) {
    const M = EV.M, b = r.body || {}, T = EV.tnText, e = EV.e, n = (k, w) => `${k} ${w}${k === 1 ? '' : 's'}`, ids = a => (a || []).map(x => (M.byId[x] && EV.seen(x) ? EV.link(x) : e(x))).join(', ');
    const cut = (t, k) => { t = String(t == null ? '' : t).replace(/\s+/g, ' ').trim(); return t.length > k ? t.slice(0, k - 1) + '…' : t; }, G = rows => rows.filter(q => q && q[1]);
    switch (r.type) {
      case 'why': return { what: 'guess of why', says: T(b.guess), ground: G([['the result it starts from', T(b.result)], ['read in', ids(b.about)], b.revises && ['replaces', ids([b.revises])]]) };
      case 'rethink': return { what: 'looks again at ' + (b.for || 'a guess'), says: `now ${e(b.now || '')}`, ground: G([['because', T(b.because)], ['in the light of', ids(b.in_light_of)]]) };
      case 'hypothesis': { const y = b.from_why && M.byId[b.from_why]; return { what: 'hypothesis', says: T(b.text), ground: G([['follows from the guess', b.from_why ? `${ids([b.from_why])}${y ? ': ' + T(cut(y.body.guess, 160)) : ''}` : ''], b.prediction && ['predicts', T(b.prediction)]]) }; }
      case 'judge': return { what: 'reads a new hypothesis against its guess', says: b.follows ? 'the hypothesis follows from the guess' : 'the hypothesis does not follow from the guess', ground: G([['because', T(b.because)], ['the hypothesis', T(cut(b.hypothesis, 160))], ['the guess', T(cut(b.guess, 160))]]), warn: !b.follows };
      case 'drop': return { what: 'gives up ' + (b.for || 'a hypothesis'), says: '', ground: G([['because', T(b.why || b.reason)]]) };
      case 'experiment': { const rules = (b.decision_rules || []).filter(d => d.decision_rule), ms = b.measurements || [];
        return { what: b.kind === 'test' ? 'test of ' + (b.tests || []).join(', ') : r.by === 'harness' ? 'baseline' : 'exploration', says: `${n((b.runs || []).length, 'simulation')}: ${e((b.runs || []).map(q => q.label).join(', '))}${b.question ? ' · ' + T(b.question) : ''}`,
          ground: G([...rules.map(d => ['rule for ' + (d.for || ''), `<code>${e(d.decision_rule)}</code>`]), ms.length && ['its own measurements', e(ms.map(m => `${m.name} = ${m.stat} of ${m.of}`).join('; '))], b.kind === 'test' && ['tests', ids(b.tests)]]) }; }
      case 'simulation': return { what: 'simulation', says: `${e(b.label || '')}${b.same_as ? ' (returned from ' + e(b.same_as) + ', not run again)' : ''}${b.error ? ' · no measurements' : ''}`, ground: [], warn: !!b.error };
      case 'evidence': return { what: 'result table', says: n((b.lines || []).length, 'line') + ', one for each simulation', ground: [], more: ['the lines', (b.lines || []).join('\n')] };
      case 'check': return { what: 'check for ' + (b.for || ''), says: b.result === 'held' ? 'HELD' : b.result === 'failed' ? 'FAILED' : e(String(b.result || '')), ground: G([['the rule', `<code>${e(b.decision_rule || '')}</code>`], ['with the measured numbers', `<code>${e(b.with_numbers || '')}</code>`], ['computed by the harness from', ids([b.experiment])]]), warn: b.result === 'failed' };
      case 'verdict': { const sup = r.by === 'supervisor';
        return { what: (sup ? (b.after ? 'second ruling on ' : 'ruling on ') : 'verdict on ') + (b.for || ''), says: e(b.result || ''), ground: G([['because', T(b.because)], sup && b.shows && ['the checks show', T(b.shows)], sup && b.fair === false && ['not a fair test', e(EV.SUP_DEFECT[b.defect] || b.defect || '')], b.changed && ['changed by the harness', T(b.changed)],
          b.after && ['after the objection', ids([b.after])], b.answer && ['its answer to the objection', T(b.answer)], b.checks && ['the checks', ids(b.checks)], b.next && ['next', T(b.next)]]), more: sup ? EV.tnShown(r.id) : null }; }
      case 'review': { const ok = b.decision === 'approved', ground = b.gate === 'ground';
        return { what: ground ? `reads the guess ${b.for || ''} against its records` : `reviews the test of ${b.for || ''} before it is run`, says: ok ? 'approved' : b.decision === 'contested' ? 'it still objects (the step goes on all the same)' : 'sent back',
          ground: G([b.defect && b.defect !== 'none' && ['the defect it names', e((ground ? { not_in_the_records: 'the result the guess starts from is not what the cited records show', repeats: 'the guess repeats an earlier one that has its ruling', ignores_a_ruling: 'the guess goes on as if a ruling against it had not been given' }[b.defect] : EV.SUP_DEFECT[b.defect]) || b.defect)],
            ['because', T(b.because)], ground && ['the records show', T(b.records_show)], ground && b.nearest_earlier && b.nearest_earlier !== 'none' && ['nearest earlier', T(b.nearest_earlier)],
            !ground && ['the rival it weighed', T(b.rival)], !ground && b.rival_outcome && ['under that rival the rule would', e(b.rival_outcome === 'held' ? 'hold too' : 'fail')], !ground && ['it would doubt the test if', T(b.doubt_if)], !ground && (b.rules || []).length && ['the rules it read', (b.rules || []).map(q => `<code>${e(q)}</code>`).join(' ; ')]]),
          more: EV.tnShown(r.id), warn: !ok }; }
      case 'objection': return { what: 'objects to the ruling ' + (b.to || ''), says: '', ground: G([['because', T(b.because)]]) };
      case 'request': return { what: 'asks to look', says: `${e(b.tool || '')}(${e(Object.entries(b.args || {}).filter(([, v]) => v != null).map(([k, v]) => `${k}: ${v}`).join(', '))})`, ground: [] };
      case 'result': { const t = String(b.result == null ? '' : b.result); return { what: 'returns what ' + (b.tool || 'the tool') + ' read', says: e(cut(t, 150)), ground: [], more: t.length > 150 ? ['all of it', t.slice(0, 6000) + (t.length > 6000 ? '\n… (' + (t.length - 6000) + ' more characters in the record)' : '')] : null, warn: /^error/.test(t) }; }
      case 'note': return r.by === 'model' ? { what: 'observations', says: T(b.observations || b.text), ground: [] } : b.part ? { what: 'refuses a part of the answer: ' + b.part, says: '', ground: G([['because', T(b.reason || b.text)], b.reason && b.text && b.text !== b.reason && ['what it told the researcher', T(b.text)]]), warn: true } : { what: 'note', says: T(b.text), ground: [] };
      case 'malformed': return { what: 'cannot use the answer', says: '', ground: G([['because', T(((b.refused || []).map(q => `${q.part}: ${q.reason}`).join(' | ')) || b.error)]]), warn: true };
      case 'report': return { what: 'final report', says: 'recommends ' + e(Object.entries(b.recommendation || {}).map(([k, v]) => `${k} ${v}`).join(', ')), ground: G([['what limits the result', T(b.limit)], ['why', T(b.explanation)], ...(b.claims || []).map(c => ['it rests on', `${T(c.text)} (${ids(c.evidence)})`])]) };
      default: return { what: r.type, says: T(b.text || ''), ground: [] };
    }
  },
  // what the supervisor was shown when it made this decision (supervisor.jsonl), kept folded
  tnShown(id) { const q = (EV.files.supervisor || {})[id]; return q && q.shown ? ['what the supervisor was shown for this', q.shown] : null; },
  tnmore(id) { const S = EV.s; S.tnOpen = S.tnOpen || {}; S.tnOpen[id] = !S.tnOpen[id]; EV.draw(); },
  tnfold(id) { const S = EV.s; S.tnShut = S.tnShut || {}; S.tnShut[id] = !S.tnShut[id]; EV.draw(); },
  turnsFold() {
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
      const open = EV.s.tnOpen || {};
      const first = {}; groups.forEach((g, gi) => { if (!(g.c in first)) first[g.c] = gi; });   // an agent's first box of the turn carries the link to its transcript
      const boxes = groups.map((g, gi) => { const items = g.rs.map(r => { const q = EV.tnSays(r), more = q.more && q.more[1] ? q.more : null;
          return `<div class="tn-item${q.warn ? ' warnc' : ''}" data-rid="${e(r.id)}" data-step="${st(r.id)}"${EV.freshAttr ? EV.freshAttr(r.id) : ''}><span class="tn-id">${EV.link(r.id)}</span> <b>${e(q.what)}</b>${q.says ? `<span class="tn-says">${q.says}</span>` : ''}${EV.tnXLine ? EV.tnXLine(r) : ''}
            ${q.ground.length ? `<dl class="tn-ground">${q.ground.map(([k, v]) => `<dt>${e(k)}</dt><dd>${v}</dd>`).join('')}</dl>` : ''}
            ${more ? `<button class="tn-more" data-act="tnmore" data-id="${e(r.id)}" aria-expanded="${!!open[r.id]}">${open[r.id] ? '▾' : '▸'} ${e(more[0])}</button>${open[r.id] ? `<pre class="tn-pre">${e(more[1])}</pre>` : ''}` : ''}</div>`; }).join('');
        return `<div class="tn-box" data-by="${g.c === 'judge' ? 'supervisor' : g.c}" data-kind="${g.type}" data-step="${Math.min(...g.rs.map(r => st(r.id)))}" style="grid-column:${cols.indexOf(g.c) + 1}">${EV.tnCallLink && first[g.c] === gi ? EV.tnCallLink(t, g.c) : ''}${items}</div>`; }).join('');
      const left = U ? `${U.body.simulations_left} simulations left` : t === 0 ? 'before the first turn: the harness runs the baseline' : '', k = Math.min(...rs.map(r => st(r.id)));
      return `<section class="tn-turn" data-turn="${t}" data-step="${k}"><button class="tn-band" data-act="tnfold" data-id="${t}" aria-expanded="${!shut[t]}" title="${shut[t] ? 'Show' : 'Fold'} this turn"><span class="lc-tw">${shut[t] ? '▸' : '▾'}</span> <b>${t === 0 ? 'Start' : 'Turn ' + t}</b> <span class="sm">${e(left)}</span>
          <span class="sm tn-count">${cols.map((c, i) => count[i] ? `${EV.TN_COLS[c][0]} ${count[i]}` : '').filter(Boolean).join(' · ')}</span></button>
        ${shut[t] ? '' : `<div class="tn-grid tn-rows" style="--n:${cols.length}">${boxes}</div>`}</section>`; }).join('');
    const S = EV.s, open = S.turnsOpen != null ? S.turnsOpen : S.full || EV.store('ev-turns') === '1', nt = turns.filter(t => t > 0).length, nr = recs.filter(r => r.type !== 'turn').length;
    return `<details id="s-turns"${open ? ' open' : ''}><summary><b>Turn by turn: who did what</b> <span class="sm">${nt} ${nt === 1 ? 'turn' : 'turns'}, ${nr} records: each in the column of whoever made it, what it says and on what ground</span><span class="cl noprint fl-btn" aria-hidden="true"><span class="fl-o">open</span><span class="fl-f">fold</span></span></summary>
      <p class="sm tn-op"><i class="sw" data-by="operator"></i><b>Operator</b> (you): the ${EV.link('brief')}, written before the first turn. Nothing below changes it. Time runs down; a box's id opens it; a turn's band folds the turn.</p>
      <p class="sm tn-mode noprint${S.tnOn ? ' on' : ''}" id="tn-mode"><span class="tn-m-on"><b>Scrolling the turns</b>: the page stays where it is. Click anywhere outside the turns (or press Esc) to scroll the whole page.</span><span class="tn-m-off"><b>Scrolling the page.</b> Click inside the turns to scroll them alone, with the board kept in view.</span></p>
      <div class="tn-scroll${S.tnOn ? ' tn-on' : ''}" id="tn-scroll">${head}${bands}</div></details>`;
  },
});
document.getElementById('ev').addEventListener('toggle', ev => { if (ev.target.id === 's-turns') { EV.s.turnsOpen = ev.target.open; if (!EV.s.full) EV.store('ev-turns', ev.target.open ? '1' : '0'); EV.tnMode(ev.target.open); } }, true);
// the lean page (2026-11-22, the operator: "user should be able to switch to whole page scrolling when they click outside of the detail section"): with
// the turns in a box of their own, the wheel scrolls them alone once the reader has clicked inside, and the whole page again after a click outside or Esc.
// Decided before the page's own click handlers run (capture), so a click that redraws the page keeps the mode; nothing moves the page by itself.
EV.tnMode = on => { EV.s.tnOn = !!on; const b = document.getElementById('tn-scroll'), m = document.getElementById('tn-mode'); if (b) b.classList.toggle('tn-on', EV.s.tnOn); if (m) m.classList.toggle('on', EV.s.tnOn); };
document.addEventListener('click', ev => { if (!document.getElementById('tn-scroll')) return; const inside = !!(ev.target.closest && ev.target.closest('#tn-scroll')); if (inside !== !!EV.s.tnOn) EV.tnMode(inside); }, true);
document.addEventListener('keydown', ev => { if (ev.key === 'Escape' && EV.s.tnOn) EV.tnMode(false); });
