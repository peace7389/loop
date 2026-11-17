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
      `${icon} ${EV.term(term, word)}<br><b style="font-size:var(--f-card)">${n}</b>${small ? ` <small>${small}</small>` : ''}`, `data-act="goto" data-id="${to}"`);
    const col = i => 8 + i * 134, a = (x1, y1, x2, y2) => `<path class="edge" d="M${x1},${y1} C${(x1 + x2) / 2},${y1} ${(x1 + x2) / 2},${y2} ${x2},${y2}" marker-end="url(#ev-ah)"/>`;
    const r = (i, y) => [col(i) + W, y + H / 2], l = (i, y) => [col(i) - 2, y + H / 2];
    const Y = { top: 6, mid: 72, bot: 138 };
    // brief → session → hypotheses / experiments / final report; experiment → tests; test → decision rule, simulations → check → verdict
    const edges = [[0, Y.mid, 1, Y.mid], [1, Y.mid, 2, Y.top], [1, Y.mid, 2, Y.mid], [1, Y.mid, 2, Y.bot], [2, Y.mid, 3, Y.mid], [3, Y.mid, 4, Y.top], [3, Y.mid, 4, Y.bot], [4, Y.top, 5, Y.mid], [4, Y.bot, 5, Y.mid], [5, Y.mid, 6, Y.mid]]
      .map(([i, y, j, z]) => a(...r(i, y), ...l(j, z))).join('') + `<path class="edge" d="M${col(2) + W / 2},${Y.top} C${col(2) + W / 2},-30 ${col(6) + W / 2},-30 ${col(6) + W / 2},${Y.mid - 2}" marker-end="url(#ev-ah)" stroke-dasharray="3 3"/>
        <path class="edge" d="M${col(2) + W},${Y.top + H / 2} C${col(3) - 20},${Y.top + H / 2} ${col(3) + W / 2},${Y.top + 20} ${col(3) + W / 2},${Y.mid - 2}" marker-end="url(#ev-ah)" stroke-dasharray="3 3"/>`;
    return `<svg viewBox="0 -34 ${col(6) + W + 8} ${Y.bot + H + 40}" width="100%" role="img" aria-label="How a session is built, with this session's counts">${EV.arrowDefs()}${edges}
      ${node(col(0), Y.mid, 'Brief', 'brief', M.brief ? 1 : 0, 'operator', EV_ICON.brief, 's-system||brief', M.brief ? '' : EV.nr)}
      ${node(col(1), Y.mid, 'Session', 'session', 1, 'harness', '▢', 's-made', `${c.turn} ${c.turn === 1 ? 'turn' : 'turns'}`)}
      ${node(col(2), Y.top, 'Hypothesis', 'hypotheses', c.hypothesis, 'model', EV_ICON.hypothesis, 's-map|map', c.drop ? `${c.drop} dropped` : '')}
      ${node(col(2), Y.mid, 'Experiment', 'experiments', c.experiment, 'model', EV_ICON.experiment, 's-notebook', base ? `incl. ${base} baseline` : '')}
      ${node(col(2), Y.bot, 'Final report', 'final report', c.report, 'model', EV_ICON.report, 's-proposes', '')}
      ${node(col(3), Y.mid, 'Test', 'tests', c.test, 'model', EV_ICON.test, 's-find', 'one rule each')}
      ${node(col(4), Y.top, 'Decision rule', 'decision rules', c.rule, 'model', '⊢', 's-notebook', '')}
      ${node(col(4), Y.bot, 'Simulation', 'simulations', c.simulation, 'simulator', EV_ICON.simulation, 's-best|best', reused ? `${reused} returned from earlier` : '')}
      ${node(col(5), Y.mid, 'Check', 'checks', c.check, 'harness', EV_ICON.check, 's-notebook', M.old ? EV.nr : `${M.checks.filter(q => q.result === 'held').length} held${M.voidIds.size ? ' · ' + M.voidIds.size + ' void' : ''}`)}
      ${node(col(6), Y.mid, 'Verdict', 'verdicts', c.verdict, 'model', EV_ICON.verdict, 's-verdicts|verdicts', '')}
      <text x="${(col(2) + col(6) + W) / 2}" y="-24" text-anchor="middle">a verdict judges a hypothesis</text></svg>`;
  },

  // ---- the turn loop: decide → run → check → look again, with the number of turns
  turnLoop() {
    const n = EV.M.counts.turn, R = 50, cx = 130, cy = 72, at = d => [cx + R * Math.cos(d * Math.PI / 180), cy + R * Math.sin(d * Math.PI / 180)];
    const pts = [[-90, 'decide', 'model'], [0, 'run', 'simulator'], [90, 'check', 'harness'], [180, 'look again', 'model']];
    const arc = (d1, d2) => { const [x1, y1] = at(d1 + 16), [x2, y2] = at(d2 - 16); return `<path class="edge" d="M${x1},${y1} A${R},${R} 0 0 1 ${x2},${y2}" marker-end="url(#ev-ah)"/>`; };
    return `<svg viewBox="0 0 260 144" width="260" role="img" aria-label="The turn loop">${EV.arrowDefs()}${pts.map(([d], i) => arc(d, pts[(i + 1) % 4][0] + (i === 3 ? 360 : 0))).join('')}
      ${pts.map(([d, t, by]) => { const [x, y] = at(d); return `<g data-by="${by}"><circle cx="${x}" cy="${y}" r="5" class="stripe"/><text x="${x + (d === 0 ? 9 : d === 180 ? -9 : 0)}" y="${y + (d === -90 ? -9 : d === 90 ? 17 : 4)}" text-anchor="${d === 0 ? 'start' : d === 180 ? 'end' : 'middle'}">${t}</text></g>`; }).join('')}
      <text x="${cx}" y="${cy - 2}" text-anchor="middle" style="font-size:var(--f-page);font-weight:700;fill:var(--text-primary)">${n}</text><text x="${cx}" y="${cy + 14}" text-anchor="middle">${n === 1 ? 'turn' : 'turns'}</text></svg>`;
  },

  // ---- the page's one legend: colour has three meanings only, and each is named here once. Who produced a thing (a thin
  // left edge, a small square); the outcome of a test (a card's edge and a word; the warning mark is kept for a refused
  // answer, a verdict against its check and a number that differs from its measurement); the flow, in the picture and the charts.
  // Each item of the legend has a box of its own (pointed at, or reached with the Tab key): [the name, the group it belongs to, what it means in a sentence or two, where it is seen on the page]
  LEGEND_SAYS: {
    model: ['AI', 'who produced it', 'Written by the AI: its hypotheses, plans, decision rules, verdicts and final report.', 'a small mark before a line, or the left edge of a box'],
    harness: ['harness', 'who produced it', 'Made by the harness, the program that runs the session: it checks each decision rule against the measurements, counts, and refuses what it cannot use.', 'a small mark before a line, or the left edge of a box'],
    simulator: ['ns-3', 'who produced it', 'Measured by ns-3, the network simulator, in a simulation: goodput, loss, drops.', 'a small mark before a measured value'],
    operator: ['operator', 'who produced it', 'Set by the person who set the session up: the brief, the fixed settings, the scheduling policy.', 'a small mark before a line, or the left edge of a box'],
    held: ['expected and found', 'outcome of a test', 'The decision rule held: what the AI expected was measured. A verdict “supported” has the same colour.', 'the edge of a card, a box of the board, a ✓ before a result'],
    failed: ['expected and not found', 'outcome of a test', 'The decision rule failed: what the AI expected was not measured. That is a finding, not an error. A verdict “refuted” has the same colour.', 'the edge of a card, a box of the board, a ✗ before a result'],
    warn: ['needs a look', 'outcome of a test', 'Kept for three things: an answer, or a part of one, that the harness refused; a verdict that disagrees with its check; a number in the AI’s text that differs from its measurement.', 'a ⚠ before the line'],
    udp: ['UDP', 'flow', 'The UDP flow: packets sent at a steady rate and never sent again when lost.', 'this colour in the picture of the network and in the charts'],
    tcp: ['TCP', 'flow', 'The TCP flow: a transfer that always has data to send; it sends lost packets again and slows down when the path is full.', 'this colour in the picture of the network and in the charts'],
    'key-supported': ['supported', 'a box of the board', 'The AI judged this hypothesis supported. The verdict is the AI’s own; the check of its decision rule is the harness’s.'],
    'key-refuted': ['refuted', 'a box of the board', 'The AI judged this hypothesis refuted. That is a result, not an error.'],
    'key-inconclusive': ['inconclusive', 'a box of the board', 'The AI judged that its test did not settle this hypothesis.'],
    'key-dropped': ['dropped', 'a box of the board', 'The AI gave this hypothesis up before it was tested.'],
    'key-ended': ['never judged', 'a box of the board', 'The session ended before the AI gave its verdict on this hypothesis.'],
    'key-ck': ['checked, not judged yet', 'a box of the board', 'The harness has checked the decision rule and the AI has not given its verdict yet. Only the edge of the box is coloured: by whether the check held or failed.'],
    'key-ans': ['cited by the final report', 'a box of the board', 'The final report cites this hypothesis’s test for one of its claims. The box has a ring, and a pale line runs from it to the answer.'],
    'key-good': ['from one that was supported', 'an arrow of the board', 'The later hypothesis names the earlier one’s result as what it follows from, and the earlier one was supported; before a verdict: its check held.'],
    'key-bad': ['from one that was refuted', 'an arrow of the board', 'The later hypothesis names the earlier one’s result as what it follows from, and the earlier one was refuted; before a verdict: its check failed.'],
    'key-mixed': ['from results of both kinds', 'an arrow of the board', 'The later hypothesis follows from several results: some as expected, some not.'],
    'key-neutral': ['from an inconclusive result', 'an arrow of the board', 'The later hypothesis follows from a result that settled nothing: an inconclusive verdict, or a check that was void.'],
    'key-weak': ['from an experiment’s result table', 'an arrow of the board', 'The later hypothesis names only the table of measurements of an experiment, not the result of a hypothesis.'],
    'key-brief': ['from the brief or the baseline', 'an arrow of the board', 'The later hypothesis follows from what the brief says or from the baseline measurement, not from a result of this session. The arrow has no colour.'],
    now: ['now', 'a running session', 'Where the work of the running session is, and what has just arrived.', 'a pulsing dot, and a tinted ground for half a minute'],
  },
  legendBar() { const wd = k => ` data-wd="l:${k}" tabindex="0"`, by = (who, name) => `<span class="lg" data-by="${who}"${wd(who)}><i class="sw" data-icon="${who}" data-col="${name}"></i>${name}</span>`, sw = (v, name, k) => `<span class="lg"${wd(k)}><i class="sw" data-col="${name}" style="background:var(${v})"></i>${name}</span>`, eg = (v, col, name) => `<span class="lg"${wd(col)}><i class="eg" data-col="${col}" style="background:var(${v})"></i>${name}</span>`;
    return `<div class="ev-legend noprint" id="ev-legend"><span class="lg-grp"><b>who produced it</b>${by('model', 'AI')}${by('harness', 'harness')}${by('simulator', 'ns-3')}${by('operator', 'operator')}</span>
      <span class="lg-grp"><b>outcome of a test</b>${eg('--good', 'held', 'expected and found')}${eg('--critical', 'failed', 'expected and not found: a result, not a warning')}<span class="lg"${wd('warn')}><i class="sw" data-col="warning" style="background:var(--warning)"></i>${EV.gkey('warn')}needs a look</span></span>
      <span class="lg-grp"><b>flow</b>${sw('--series-1', 'UDP', 'udp')}${sw('--series-2', 'TCP', 'tcp')}</span>${EV.liveNow && EV.M && EV.liveNow() ? `<span class="lg-grp" id="lg-now"><b>now</b><span class="lg"${wd('now')}><i class="sw" data-col="now" style="background:var(--live)"></i>where the work is · what just arrived</span></span>` : ''}</div>`; },

  // ---- who produced what: this session's record counts per source (the colours are in the page's legend); and the one symbol per record type
  legend() {
    const say = { model: 'what the AI wrote', harness: 'what the harness computed, found or decided', simulator: 'what ns-3, the network simulator, measured in a simulation', operator: 'what the person set: the brief, the scheduling policy' };
    const names = { brief: 'brief', hypothesis: 'hypothesis', drop: 'dropped hypothesis', experiment: 'experiment', test: 'test', simulation: 'simulation', evidence: 'evidence table', check: 'check',
                    verdict: 'verdict', report: 'final report', note: 'note', malformed: 'refused answer', request: 'request for information', result: 'its result', turn: 'turn record' };
    return `<table><tbody>${['model', 'harness', 'simulator', 'operator'].map(b => `<tr><td><b>${b === 'model' ? 'AI (model)' : b === 'simulator' ? 'ns-3' : b}</b></td><td class="num">${EV.M.bySource[b]} record${EV.M.bySource[b] === 1 ? '' : 's'}</td><td class="sm">${say[b]}</td></tr>`).join('')}</tbody></table>
      <p class="sm" style="margin-top:6px">${Object.entries(EV_ICON).map(([k, i]) => `<span style="white-space:nowrap;margin-right:10px">${i} ${names[k]}</span>`).join(' ')}</p>`;
  },
});
