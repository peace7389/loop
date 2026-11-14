// "Looking closer": the analysis views of a session, each folded to one line that says what it holds. In Brief a view
// opens with one click on its line; Full (the switch in the header strip) opens them all. Nothing is removed from the
// page: best so far, the simulations of each turn along one setting, the target where one setting alone differs, the
// verdicts against their checks, the tests as a list with their margins, the session flow, the hypothesis map, the tree.
// Which views a reader opened is remembered by the browser (ev-closer), as a card's fold is.
// ======================================================================================================
Object.assign(EV, {
  // [key, name, the one line that says what it holds, the view]
  CLOSER: [
    ['best', 'Best so far', 'the best result that meets the conditions, simulation by simulation', () => EV.bestCard()],
    ['knob', 'The simulations of each turn, along one setting', 'which values the session tried, turn by turn', () => EV.knobCard()],
    ['alone', 'The target where one setting alone differs', 'how far the target moved when a single setting changed', () => EV.aloneCard()],
    ['verdicts', 'Verdicts against checks', 'each verdict beside the result of its check, and the checks in order', () => EV.verdictsCard()],
    ['tests', 'The tests as a list, with margins', 'one row per test: what was compared, by how much the check held or failed', () => EV.testsCard()],
    ['flow', 'Session flow', 'every step in order, in the lane of whoever did it', () => EV.flowCard()],
    ['map', 'Hypothesis map', 'which hypothesis follows from which, and how each ended', () => EV.mapCard()],
    ['tree', 'The session as a tree', 'turn, experiment, test and simulation, one inside the other', () => EV.treeCard()],
  ],
  isOpen: k => !!(EV.s.full || (EV.s.closer || {})[k]),
  closerCard() {
    const e = EV.e, rows = EV.CLOSER.map(([k, name, says, view]) => { const open = EV.isOpen(k);
      return `<div class="lc-row${open ? ' open' : ''}" data-view="${k}"><button data-act="closer" data-id="${k}" aria-expanded="${open}"${EV.s.full ? ' disabled title="Full shows every view; switch to Brief to fold them"' : ''}><span class="lc-tw">${open ? '▾' : '▸'}</span>${e(name)}</button><span class="sm">${e(says)}</span></div>${open ? view() : ''}`; }).join('');
    return `<div class="ev-sec" id="s-closer"><div class="ev-card lc-head"><h2>Looking closer</h2><p class="sec-q">How did the search go?</p>
      <p class="sm">${EV.CLOSER.length} analysis views, folded. ${EV.s.full ? 'Full shows them all.' : 'Click one to open it; “Full” in the header strip opens them all.'}</p></div>${rows}</div>`;
  },
  verdictsCard() { return `<div class="ev-card noprint" id="s-verdicts"><h2>Verdicts against checks <small>how often the model's verdict agreed with what its check found</small></h2>${EV.vcSession().replace(/ id="vc-session"/, ' id="vc-closer"').replace(/ id="(vc-[a-z]+)"/g, ' data-vc="$1"')}</div>`; },
  flowCard() { return `<div class="ev-card" id="s-work"><h2>Session flow <small>time runs down, in the lane of whoever did each step</small></h2><div class="ev-scroll ev-lanes">${EV.viewLanes()}</div></div>`; },
  mapCard() { const S = EV.s; return `<div class="ev-card" id="s-map"><h2>Hypothesis map <small>left to right by the turn each hypothesis was stated</small></h2>
      <div class="ev-bar"><button data-act="path" class="${S.path ? 'on' : ''}">show the path to the answer</button></div>${EV.viewMap()}</div>`; },
  treeCard() { return `<div class="ev-card noprint" id="s-alt"><h2>The session as a tree <small>turn, experiment, test, simulation</small></h2><div id="s-tree">${EV.viewTree()}</div></div>`; },
  // the replay's buttons: at step k everything recorded later is greyed, in every view
  replayBar() { const S = EV.s, n = EV.M.steps.length, k = S.step == null ? n - 1 : S.step;
    return `<span class="end noprint" id="replay-bar"><b>Replay</b> <button data-act="replay" data-id="first">« first</button> <button data-act="replay" data-id="prev">◀</button> <button data-act="replay" data-id="next">▶</button> <button data-act="replay" data-id="last">last »</button>
      <span class="sm">step ${n ? k + 1 : 0} of ${n}${S.step == null ? '' : ': later items are greyed'} · arrow keys</span></span>`; },
});
EV.act = Object.assign(EV.act || {}, {
  closer(id) { const S = EV.s; S.closer = S.closer || {}; S.closer[id] = !S.closer[id]; EV.store('ev-closer', Object.keys(S.closer).filter(k => S.closer[k]).join(',')); EV.draw(); },
  level(id) { EV.s.full = id === 'full'; EV.store('ev-full', EV.s.full ? '1' : '0'); EV.draw(); },
});
