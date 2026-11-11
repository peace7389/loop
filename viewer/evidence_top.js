// The drawings of "How to read this page": the structure map with this session's counts, the turn loop, the legend of
// who produced what; and the box and arrow pieces every SVG diagram of the page is built from.
// ======================================================================================================
Object.assign(EV, {
  // A box of an SVG diagram: a rectangle with the producer's stripe on its left edge and HTML text inside
  box(x, y, w, h, by, html, attrs, cls) {
    return `<g ${attrs || ''} data-by="${by}"><rect class="bx ${cls || ''}" x="${x}" y="${y}" width="${w}" height="${h}" rx="6"/><rect class="stripe" x="${x}" y="${y}" width="4" height="${h}" rx="2"/>
      <foreignObject x="${x + 2}" y="${y}" width="${w - 2}" height="${h}"><div xmlns="http://www.w3.org/1999/xhtml" class="bt">${html}</div></foreignObject></g>`;
  },
  arrowDefs: () => `<defs><marker id="ev-ah" viewBox="0 0 10 10" refX="9" refY="5" markerUnits="userSpaceOnUse" markerWidth="9" markerHeight="9" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="var(--text-muted)"/></marker>
    <marker id="ev-ahot" viewBox="0 0 10 10" refX="9" refY="5" markerUnits="userSpaceOnUse" markerWidth="10" markerHeight="10" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="var(--text-primary)"/></marker></defs>`,

  // ---- the structure map: how a session is built, with this session's counts from its ledger; a click goes to that part
  structureMap() {
    const M = EV.M, c = M.counts, reused = M.sims.filter(s => s.same_as).length, base = M.exps.filter(x => x.by === 'harness').length, W = 116, H = 58;
    const node = (x, y, term, word, n, by, icon, to, small) => EV.box(x, y, W, H, by,
      `${icon} ${EV.term(term, word)}<br><b style="font-size:15px">${n}</b>${small ? ` <small>${small}</small>` : ''}`, `data-act="goto" data-id="${to}"`);
    const col = i => 8 + i * 134, a = (x1, y1, x2, y2) => `<path class="edge" d="M${x1},${y1} C${(x1 + x2) / 2},${y1} ${(x1 + x2) / 2},${y2} ${x2},${y2}" marker-end="url(#ev-ah)"/>`;
    const r = (i, y) => [col(i) + W, y + H / 2], l = (i, y) => [col(i) - 2, y + H / 2];
    const Y = { top: 6, mid: 72, bot: 138 };
    // brief → session → hypotheses / experiments / final report; experiment → tests; test → decision rule, simulations → check → verdict
    const edges = [[0, Y.mid, 1, Y.mid], [1, Y.mid, 2, Y.top], [1, Y.mid, 2, Y.mid], [1, Y.mid, 2, Y.bot], [2, Y.mid, 3, Y.mid], [3, Y.mid, 4, Y.top], [3, Y.mid, 4, Y.bot], [4, Y.top, 5, Y.mid], [4, Y.bot, 5, Y.mid], [5, Y.mid, 6, Y.mid]]
      .map(([i, y, j, z]) => a(...r(i, y), ...l(j, z))).join('') + `<path class="edge" d="M${col(2) + W / 2},${Y.top} C${col(2) + W / 2},-30 ${col(6) + W / 2},-30 ${col(6) + W / 2},${Y.mid - 2}" marker-end="url(#ev-ah)" stroke-dasharray="3 3"/>
        <path class="edge" d="M${col(2) + W},${Y.top + H / 2} C${col(3) - 20},${Y.top + H / 2} ${col(3) + W / 2},${Y.top + 20} ${col(3) + W / 2},${Y.mid - 2}" marker-end="url(#ev-ah)" stroke-dasharray="3 3"/>`;
    return `<svg viewBox="0 -34 ${col(6) + W + 8} ${Y.bot + H + 40}" width="100%" role="img" aria-label="How a session is built, with this session's counts">${EV.arrowDefs()}${edges}
      ${node(col(0), Y.mid, 'Brief', 'brief', M.brief ? 1 : 0, 'operator', EV_ICON.brief, 's-work||brief', M.brief ? '' : EV.nr)}
      ${node(col(1), Y.mid, 'Session', 'session', 1, 'harness', '▢', 's-overview', `${c.turn} ${c.turn === 1 ? 'turn' : 'turns'}`)}
      ${node(col(2), Y.top, 'Hypothesis', 'hypotheses', c.hypothesis, 'model', EV_ICON.hypothesis, 's-work|map', c.drop ? `${c.drop} dropped` : '')}
      ${node(col(2), Y.mid, 'Experiment', 'experiments', c.experiment, 'model', EV_ICON.experiment, 's-work|tree', base ? `incl. ${base} baseline` : '')}
      ${node(col(2), Y.bot, 'Final report', 'final report', c.report, 'model', EV_ICON.report, 's-overview', '')}
      ${node(col(3), Y.mid, 'Test', 'tests', c.test, 'model', EV_ICON.test, 's-tests', 'one hypothesis, one rule')}
      ${node(col(4), Y.top, 'Decision rule', 'decision rules', c.rule, 'model', '⊢', 's-tests', '')}
      ${node(col(4), Y.bot, 'Simulation', 'simulations', c.simulation, 'simulator', EV_ICON.simulation, 's-best', reused ? `${reused} returned from earlier` : '')}
      ${node(col(5), Y.mid, 'Check', 'checks', c.check, 'harness', EV_ICON.check, 's-tests', M.old ? EV.nr : `${M.checks.filter(q => q.result === 'held').length} held`)}
      ${node(col(6), Y.mid, 'Verdict', 'verdicts', c.verdict, 'model', EV_ICON.verdict, 's-work|map', '')}
      <text x="${(col(2) + col(6) + W) / 2}" y="-24" text-anchor="middle">a verdict judges a hypothesis</text></svg>`;
  },

  // ---- the turn loop: decide → run → check → look again, with the number of turns
  turnLoop() {
    const n = EV.M.counts.turn, R = 50, cx = 130, cy = 72, at = d => [cx + R * Math.cos(d * Math.PI / 180), cy + R * Math.sin(d * Math.PI / 180)];
    const pts = [[-90, 'decide', 'model'], [0, 'run', 'simulator'], [90, 'check', 'harness'], [180, 'look again', 'model']];
    const arc = (d1, d2) => { const [x1, y1] = at(d1 + 16), [x2, y2] = at(d2 - 16); return `<path class="edge" d="M${x1},${y1} A${R},${R} 0 0 1 ${x2},${y2}" marker-end="url(#ev-ah)"/>`; };
    return `<svg viewBox="0 0 260 144" width="260" role="img" aria-label="The turn loop">${EV.arrowDefs()}${pts.map(([d], i) => arc(d, pts[(i + 1) % 4][0] + (i === 3 ? 360 : 0))).join('')}
      ${pts.map(([d, t, by]) => { const [x, y] = at(d); return `<g data-by="${by}"><circle cx="${x}" cy="${y}" r="5" class="stripe"/><text x="${x + (d === 0 ? 9 : d === 180 ? -9 : 0)}" y="${y + (d === -90 ? -9 : d === 90 ? 17 : 4)}" text-anchor="${d === 0 ? 'start' : d === 180 ? 'end' : 'middle'}">${t}</text></g>`; }).join('')}
      <text x="${cx}" y="${cy - 2}" text-anchor="middle" style="font-size:20px;font-weight:700;fill:var(--text-primary)">${n}</text><text x="${cx}" y="${cy + 14}" text-anchor="middle">${n === 1 ? 'turn' : 'turns'}</text></svg>`;
  },

  // ---- who produced what: one colour per source, with this session's record counts; and the one symbol per record type
  legend() {
    const say = { model: 'what the AI wrote', harness: 'what the harness computed, found or decided', simulator: 'what a simulation measured', operator: 'what the person set: the brief, the scheduling policy' };
    const names = { brief: 'brief', hypothesis: 'hypothesis', drop: 'dropped hypothesis', experiment: 'experiment', test: 'test', simulation: 'simulation', evidence: 'evidence table', check: 'check',
                    verdict: 'verdict', report: 'final report', note: 'note', malformed: 'refused answer', request: 'request for information', result: 'its result', turn: 'turn record' };
    return `<table><tbody>${['model', 'harness', 'simulator', 'operator'].map(b => `<tr data-by="${b}"><td><i class="sw"></i><b>${b}</b></td><td class="num">${EV.M.bySource[b]} record${EV.M.bySource[b] === 1 ? '' : 's'}</td><td class="sm">${say[b]}</td></tr>`).join('')}</tbody></table>
      <p class="sm" style="margin-top:6px">${Object.entries(EV_ICON).map(([k, i]) => `<span style="white-space:nowrap;margin-right:10px">${i} ${names[k]}</span>`).join(' ')}</p>`;
  },
});
