// View 1 (the session flow in three lanes) and View 2 (the hypothesis map), drawn as plain SVG. Every box carries
// data-step (the step of the session flow at which it was recorded), so the replay can grey everything later.
// ======================================================================================================
Object.assign(EV, {
  LANES: { model: [0, 232], harness: [240, 166], simulator: [414, 150], supervisor: [572, 176] },  // x and width of each lane (the supervisor's only in a supervised session)

  // ---- View 1: one box per step in the lane of whoever did it, joined in time order; a band marks each turn
  viewLanes() {
    const M = EV.M, S = EV.s, e = EV.e, L = M.supervised ? EV.LANES : Object.fromEntries(Object.entries(EV.LANES).filter(([b]) => b !== 'supervisor')), W = M.supervised ? 748 : 564, out = [], arrows = [];
    const info = EV.selInfo(), selSteps = new Set([...info.recs].map(id => M.recStep[id]).filter(k => k != null));  // the boxes that hold a part of the selected item
    const hit = new Set(); if (S.claim) { const c = M.claims[S.claim - 1]; (c ? c.evidence : []).forEach(id => { if (id in M.recStep) hit.add(M.recStep[id]); }); }
    const icon = { start: EV_ICON.brief, answer: '✎', refused: EV_ICON.malformed, accepted: EV_ICON.experiment, sims: EV_ICON.simulation, checks: EV_ICON.check, report: EV_ICON.report, review: EV_ICON.review, ruling: EV_ICON.verdict };
    let y = 30, prev = null;
    const head = Object.entries(L).map(([b, [x, w]]) => `<g data-by="${b}"><rect class="stripe" x="${x}" y="4" width="10" height="10" rx="3"/><text x="${x + 15}" y="13" style="font-weight:600;fill:var(--text-primary)">the ${b}</text></g>`).join('');
    const lines = Object.entries(L).map(([, [x, w]]) => `<line x1="${x + w / 2}" y1="22" x2="${x + w / 2}" y2="@H" stroke="var(--grid)" stroke-dasharray="2 4"/>`).join('');
    M.turns.forEach(t => {
      if (!t.steps.length) return;
      const k0 = t.steps[0].k, shut = !!S.collapsed[t.n];
      const left = t.n === 0 ? 'before the first turn' : t.left == null ? 'simulations left: ' + 'not recorded' : `${t.left} simulation${t.left === 1 ? '' : 's'} left${t.last ? ' · last turn' : ''}`;
      out.push(`<g data-act="fold" data-id="${t.n}" data-step="${k0}"><rect class="band" x="0" y="${y}" width="${W}" height="20" rx="4"/><text x="8" y="${y + 14}" style="font-weight:600;fill:var(--text-primary)">${shut ? '▸' : '▾'} ${t.n === 0 ? 'start' : EV_ICON.turn + ' turn ' + t.n}</text>
        <text x="${W - 8}" y="${y + 14}" text-anchor="end">${e(left)}${shut ? ` · ${t.steps.length} steps folded` : ''}</text><title>${shut ? 'Show' : 'Fold'} this turn</title></g>`);
      y += 28; if (shut) { prev = null; return; }
      t.steps.forEach(s => {
        const [x, w] = L[s.lane], cpl = Math.floor((w - 16) / 6.6), ic = icon[s.kind] || '', text = s.label, short = text.length > 188 ? text.slice(0, 184) + '…' : text;
        const tl = Math.max(1, Math.ceil((short.length + 2) / cpl) + (short.match(/;/g) || []).length * 0.4), per = Math.floor((w - 14) / 10), sims = s.sims || [];
        const th = Math.round(10 + 15 * tl), h = th + (sims.length ? Math.ceil(sims.length / per) * 10 + 6 : 0);
        const cls = [s.warn ? 'warn' : '', selSteps.has(s.k) || (info.turn === s.turn && s.kind === 'answer') ? 'sel' : '', hit.has(s.k) ? 'hit' : ''].join(' ');
        const dots = sims.map((q, i) => { const cx = x + 10 + (i % per) * 10, cy = y + th + 4 + Math.floor(i / per) * 10;
          return `<g data-act="open" data-t="sim" data-id="${e(q.id)}"><circle cx="${cx}" cy="${cy}" r="6" fill="transparent"/>${info.sims.has(q.id) ? `<circle cx="${cx}" cy="${cy}" r="5.6" fill="none" stroke="var(--text-primary)" stroke-width="1.6"/>` : ''}<circle cx="${cx}" cy="${cy}" r="3.6" class="${q.same_as ? '' : 'stripe'}" style="${q.same_as ? 'fill:none;stroke:var(--text-secondary);stroke-width:1.4' : ''}${q.error ? ';stroke:var(--critical);stroke-width:2' : ''}"/>
            <title>${e(`${q.id} · ${q.label || ''} · run ${q.run || 'not recorded'}${q.same_as ? ` · returned from ${q.same_as}, not run again` : ''}${q.error ? ' · no measurements: ' + q.error : ''}`)}</title></g>`; }).join('');
        out.push(`<g data-step="${s.k}">${EV.box(x, y, w, h, s.lane, ic + ' ' + e(short), `data-act="step" data-id="${s.k}"`, cls).replace('</g>', `<title>${e(text)}</title></g>`)}${dots}</g>`);
        if (prev) arrows.push(`<path class="edge" data-step="${s.k}" d="M${prev.cx},${prev.y2} C${prev.cx},${(prev.y2 + y) / 2} ${x + w / 2},${(prev.y2 + y) / 2} ${x + w / 2},${y - 2}" marker-end="url(#ev-ah)"/>`);
        prev = { cx: x + w / 2, y2: y + h }; y += h + 14;
      });
    });
    return `<svg width="${W}" height="${y + 6}" role="img" aria-label="Session flow: the steps of the session in time order, in the lane of whoever did each">${EV.arrowDefs()}${head}${lines.replace(/@H/g, y)}${arrows.join('')}${out.join('')}</svg>
      <p class="sm">A hollow dot is a simulation whose result was returned from an earlier one with the same settings and seed (not run again). Dashed orange edge: a refused step. Click a turn's band to fold it.</p>`;
  },

  // ---- View 2, the board of "What it needed to find out": one box per hypothesis, in the column of the turn it was stated
  // in (time runs left to right; hypotheses of one turn stand one under the other), and an arrow from each hypothesis
  // a later one follows from. An arrow says by its colour and its word which result led onward: a verdict "supported"
  // or a check that held (the colour of "held"), a verdict "refuted" or a check that failed (the colour of "failed"),
  // "inconclusive" or a void check (dashed, neutral), both kinds (dark). A dotted arrow is the weak link: the later
  // hypothesis names only the result table of the experiment that tested the earlier one. A box is tinted by how its
  // hypothesis ended and opens its test. In a running session the turn being written has one empty box.
  STATES: ['open', 'supported', 'refuted', 'inconclusive', 'dropped', 'ended without a verdict'],
  stCls: s => 'st-' + (s === 'ended without a verdict' ? 'ended' : s),
  mapEdges() {  // [from hypothesis id or 'brief', to hypothesis id, labels, the record ids it came from, kind]
    const M = EV.M, out = {};
    M.hyps.forEach(h => (h.follows || []).forEach(f => {
      const src = f === 'brief' ? { hyp: 'brief', label: 'brief' } : M.source(f) || { hyp: null, label: 'not recorded' };
      const from = src.hyp && src.hyp !== h.id && M.hypById[src.hyp] ? src.hyp : 'brief', key = from + '>' + h.id;
      (out[key] = out[key] || { from, to: h.id, labels: [], ids: [] }); out[key].ids.push(f);
      const lab = f === 'brief' ? 'brief' : M.voidIds.has(f) ? 'check void' : src.label; if (!out[key].labels.includes(lab)) out[key].labels.push(lab); }));
    const good = ['supported', 'check held'], bad = ['refuted', 'check failed'];
    return Object.values(out).map(x => { const g = x.labels.some(l => good.includes(l)), b = x.labels.some(l => bad.includes(l)), strong = x.labels.filter(l => l !== 'observation' && l !== 'brief' && l !== 'not recorded');
      return { ...x, strong, kind: x.from === 'brief' ? 'brief' : g && b ? 'mixed' : g ? 'good' : b ? 'bad' : strong.length ? 'neutral' : 'weak' }; });
  },
  viewMap() {
    const M = EV.M, S = EV.s, e = EV.e, info = EV.selInfo(), now = EV.liveNow(), slotTurn = now && now.phase === 'reply' && !now.mode ? now.turn : null;
    if (!M.hyps.length && slotTurn == null) return `<p class="sm">No hypothesis ${M.ended ? 'was stated in this session.' : 'has been stated yet.'}</p>`;
    // the board opens with what was asked (the aim, with its conditions) and closes with what the AI concluded (its answer: the final report's proposal; or that
    // there is none; in a running session an empty place). During the replay the last box stands only once the report is recorded.
    // Every turn has its column, also one that stated no hypothesis: a turn that only explored shows its exploration (the experiment and what it wanted to find out),
    // and the turn a running session is in shows where the work is (its last turn: that only the final report is accepted now). Without them the board would stop at
    // the last turn that stated a hypothesis, as if nothing had happened since.
    const explores = M.turns.filter(t => t.n > 0 && t.exp && EV.seen(t.exp.id) && !M.tests.some(T => T.exp === t.exp.id)).map(t => ({ x: t.exp, turn: t.n })), lastTurn = now && now.phase === 'reply' && now.mode ? now.turn : null;
    const repNow = EV.repNow(), endBox = !!repNow || S.step == null, cols = [...new Set(M.hyps.map(h => h.turn).concat(explores.map(q => q.turn), slotTurn == null ? [] : [slotTurn], now && now.turn > 0 ? [now.turn] : []))].sort((a, b) => a - b), n = cols.length + 1 + (endBox ? 1 : 0);
    // the boxes are as wide as the page allows (132 to 250 px); a board wider than the page is drawn smaller, as a whole
    // on the lean page (EV.LEAN, beside the detail pane) it is drawn smaller down to 85 %, and below that its card scrolls sideways: its words stay readable
    // where even 132 px do not fit, the boxes are small and hold the hypothesis's id and the sign of how it ended (its question is on hover and in the table below)
    const host = document.getElementById('s-map'), avail = Math.max(600, host && host.clientWidth ? host.clientWidth : (document.getElementById('ev').clientWidth || 1400) - 76),  // the room the board really has: its own container (page, less the page's and the card's margins)
      fit = gx => Math.floor((avail - 12 - (n - 1) * gx) / n), small = fit(56) < 132, GX = small ? 40 : n > 6 ? 56 : 84, NW = small ? Math.max(58, Math.min(96, fit(40))) : Math.min(250, fit(GX)), NH = small ? 30 : 54, GY = small ? 8 : 12, pos = { brief: { x: 6, y: 8 } };
    const chars = Math.floor((NW - 14) / 6.7) * 2 - 6, rowsOf = t => M.hyps.filter(h => h.turn === t).length + explores.filter(q => q.turn === t).length + (t === slotTurn || t === lastTurn ? 1 : 0);
    cols.forEach((t, i) => M.hyps.filter(h => h.turn === t).forEach((h, j) => { pos[h.id] = { x: 6 + (i + 1) * (NW + GX), y: 8 + j * (NH + GY) }; }));
    const edges = M.mapEdges = EV.mapEdges(), recorded = !M.hyps.length || M.hyps.some(h => h.follows);  // "not recorded" is said only of hypotheses that are there and name nothing
    const st = S.step == null ? null : EV_DATA.stateAt(M, S.step);
    const ringed = new Set(EV.repNow() ? M.claims.flatMap(c => c.hyps) : []), claimH = new Set(S.claim && M.claims[S.claim - 1] ? M.claims[S.claim - 1].hyps : []);  // the ring: once the final report is there
    const onPath = new Set(), hot = new Set();
    if (S.path) { const todo = [...ringed]; while (todo.length) { const id = todo.pop(); if (onPath.has(id)) continue; onPath.add(id);
      edges.filter(x => x.to === id).forEach(x => { hot.add(x.from + '>' + x.to); todo.push(x.from); }); } }
    const W = 12 + n * NW + (n - 1) * GX, H = 16 + Math.max(1, ...cols.map(rowsOf)) * (NH + GY);
    const MK = { good: 'ev-ag', bad: 'ev-ab' }, order = { weak: 0, brief: 1, neutral: 2, mixed: 3, good: 4, bad: 4 };
    // the arrows that carry a result arrive at their box one under the other, each with its sign just before the box
    const into = {}; edges.filter(x => x.strong.length && pos[x.from] && pos[x.to]).sort((p, q) => pos[p.from].y - pos[q.from].y || pos[p.from].x - pos[q.from].x).forEach(x => { (into[x.to] = into[x.to] || []).push(x); });
    const entry = x => { const l = into[x.to] || [], i = l.indexOf(x), gap = Math.min(13, (NH - 10) / Math.max(1, l.length)); return i < 0 ? 0 : (i - (l.length - 1) / 2) * gap; }, signsOut = [];
    // an arrow to the next column is one curve; an arrow that passes over columns runs in the gap between two rows of boxes, so that it never
    // passes behind a box (it would look as if it came from that box)
    const rowsMax = Math.max(1, ...cols.map(rowsOf)), lane = y => { let best = 0; for (let j = 0; j <= rowsMax; j++) if (Math.abs(8 + j * (NH + GY) - GY / 2 - y) < Math.abs(8 + best * (NH + GY) - GY / 2 - y)) best = j; return 8 + best * (NH + GY) - GY / 2; };
    const route = (x1, y1, x2, y2, pad) => { if (x2 - x1 <= GX + 2) return `M${x1},${y1} C${x1 + GX / 2},${y1} ${x2 - GX / 2 - pad},${y2} ${x2},${y2}`; const yl = lane((y1 + y2) / 2), a = x1 + GX * 0.8, b = x2 - GX * 0.8 - pad;
      return `M${x1},${y1} C${x1 + GX * 0.45},${y1} ${x1 + GX * 0.35},${yl} ${a},${yl} H${b} C${b + GX * 0.45},${yl} ${x2 - GX * 0.45 - pad},${y2} ${x2},${y2}`; };
    const svgE = edges.slice().sort((p, q) => order[p.kind] - order[q.kind]).map(x => { const a = pos[x.from], b = pos[x.to]; if (!a || !b) return '';
      const x1 = a.x + NW, y1 = a.y + NH / 2, x2 = b.x - 2, y2 = b.y + NH / 2 + entry(x), k = Math.max(M.recStep[x.to] ?? 0, x.from === 'brief' ? 0 : M.recStep[x.from] ?? 0), isHot = hot.has(x.from + '>' + x.to);
      const SIGN = { supported: 'supported', refuted: 'refuted', inconclusive: 'inconclusive', 'check held': 'held', 'check failed': 'failed', 'check void': 'void' }, signs = x.strong.map(l => SIGN[l]).filter(Boolean), t = 0.62, bz = (a0, a1, a2, a3) => (1 - t) ** 3 * a0 + 3 * (1 - t) ** 2 * t * a1 + 3 * (1 - t) * t * t * a2 + t ** 3 * a3;
      const lx = x2 - 9 - signs.length * 7, ly = y2;
      const srcT2 = x.from === 'brief' ? null : (M.tests.find(q => q.check && x.ids.includes(q.check.id)) || M.tests.filter(q => q.hyp === x.from).pop() || null);
      if (signs.length) signsOut.push(`<g data-step="${k}" class="esign" data-edge="${e(x.from + '>' + x.to)}" data-wd="e:${e(x.from + '>' + x.to)}" ${srcT2 ? `data-act="open" data-t="test" data-id="${e(srcT2.id)}"` : `data-act="open" data-t="hyp" data-id="${e(x.from)}"`}><rect class="elbg" x="${lx - signs.length * 7 - 2}" y="${ly - 8}" width="${signs.length * 14 + 4}" height="16" rx="8"/>${signs.map((q, i) => EV.gks(q, lx - signs.length * 7 + i * 14 + 1, ly - 6, 12)).join('')}</g>`);
      const says = x.kind === 'weak' ? `${x.to} names only the result table of the experiment that tested ${x.from} (${x.ids.join(', ')})` : x.kind === 'brief' ? `${x.to} follows from the brief or the baseline (${x.ids.join(', ')})` : `${x.to} follows from ${x.from}: ${x.labels.join(', ')} (${x.ids.join(', ')})`;
      // an arrow opens the test whose result it carries (the brief, for an arrow from the brief); pointing at it, or at its sign, opens its card
      const srcT = x.from === 'brief' ? null : (M.tests.find(q => q.check && x.ids.includes(q.check.id)) || M.tests.filter(q => q.hyp === x.from).pop() || null), open = x.from === 'brief' ? 'data-act="open" data-t="brief" data-id="brief"' : srcT ? `data-act="open" data-t="test" data-id="${e(srcT.id)}"` : `data-act="open" data-t="hyp" data-id="${e(x.from)}"`, d = route(x1, y1, x2, y2, signs.length ? 14 : 0), wd = `data-wd="e:${e(x.from + '>' + x.to)}"`;
      return `<g data-step="${k}" data-edge="${e(x.from + '>' + x.to)}" data-kind="${x.kind}" ${open} ${wd}><path class="edge ${x.kind}${isHot ? ' hot' : ''}" d="${d}" marker-end="url(#${isHot ? 'ev-ahot' : MK[x.kind] || 'ev-ah'})"/><path class="edge-hit" d="${d}"/>
</g>`; }).join('');
    const g0 = (M.brief && M.brief.goal) || {}, aimText = g0.kind === 'given' ? `find ${String(EV.aimWords(g0) || '').replace(/<[^>]+>/g, '')}` : g0.kind === 'open' ? 'open: the AI chooses its own aim' : 'not recorded', cutTo = (t, k) => (t.length > k ? t.slice(0, k - 1) + '…' : t);
    // an open aim: the brief leaves it to the AI, and the AI states the aim it chose in its final report (nowhere before). Once that report is recorded
    // the box says it, in the AI's own words, and says where it was stated; until then (a running session, an earlier step of the replay) it says only that the aim is open
    const rep0 = g0.kind === 'open' ? EV.repNow() : null, chose = rep0 && rep0.goal ? (Array.isArray(rep0.goal) ? rep0.goal.join(' · ') : String(rep0.goal)) : '';
    const AH = chose && !small ? Math.min(Math.max(NH, H - 24), NH * 2 + GY) : NH;  // as tall as two boxes where there is room, like the answer's box
    // what fits: the head and the note under the aim take their lines first (two each in a narrow box), the aim's own words get the rest and are cut there by the
    // browser, at a whole line; the whole aim is on the box's card and in "What it proposes"
    // An aim the AI chose is stated at the END of the session (the harness asks for it only in the final report), although its box stands at the start: the head says
    // so ("chosen by the AI at the end"), so that nobody reads the hypotheses as written against an aim that was already on record
    const linesIn = Math.floor((AH - 4) / 15.2), headLines = Math.max(1, Math.ceil((37 * 6.7 + 20) / (NW - 14))), aimRoom = Math.max(1, linesIn - headLines);
    const aimHtml = small ? `${EV.flag()}<b>the aim</b>` : chose ? `${EV.flag()}<b>The aim</b> <span class="aim-when">· chosen by the AI <b>at the end</b></span><small data-own="model" id="map-chose" style="display:-webkit-box;-webkit-box-orient:vertical;-webkit-line-clamp:${aimRoom};overflow:hidden">${e(chose)}</small>`
      : `${EV.flag()}<b>The aim</b> <span class="mut">· the brief</span><br><small>${e(cutTo(aimText, chars))}</small>`;
    const brief = EV.box(6, 8, NW, AH, chose ? 'model' : 'operator', aimHtml, `data-act="open" data-t="brief" data-id="brief"${M.brief ? ` data-wd="b:${e(M.brief.id)}"` : ''} data-aim="${e(aimText)}"${chose ? ` data-chose="${e(chose)}"` : ''}`, 'st-aim' + (onPath.has('brief') ? ' hit' : ''));
    const nodes = M.hyps.map(h => { const p = pos[h.id], s = st ? st[h.id] || 'open' : h.state, label = EV.hshort(h), short = label.length > chars ? label.slice(0, chars - 2) + '…' : label;
      const T = h.tests.filter(q => EV.seen(M.testById[q].exp)).pop();  // a node opens the test of its hypothesis
      // A hypothesis the AI has not judged yet may already have its result: the harness checks the decision rule as soon as the simulations are back, and the AI gives
      // its verdict only in its next reply. Until then the box says the check's result, with its sign, and has an edge in that result's colour (the fill is kept for the verdict).
      const unjudged = s === 'open' || s === 'ended without a verdict', ck = unjudged && T ? (c => (c && EV.seen(c.id) ? (M.voidIds.has(c.id) || c.void ? 'void' : c.result) : null))(M.testById[T].check) : null, ckCls = ck === 'held' ? ' ck-held' : ck === 'failed' ? ' ck-failed' : '';
      // ... and, under the question (then one line), why the check came out so: what was measured against the rule, in the words of the table under the board
      // ("46.7 %, not at least 98 %"); the whole of it is in the hypothesis's card
      const whyT = ck === 'held' || ck === 'failed' ? M.testById[T] : null, why = whyT && whyT.rule ? EV.readHtml(whyT.rule, { sims: Object.fromEntries(whyT.sims.map(q => [q.label, q])), plain: true, words: true, max: 2 }) : '';
      const cls = `${EV.stCls(s)}${ckCls}${info.hyps.has(h.id) ? ' sel' : ''}${claimH.has(h.id) || onPath.has(h.id) ? ' hit' : ''}`;
      const word = ['supported', 'refuted', 'inconclusive'].includes(s) ? EV.verdictRes(s) : ck === 'held' || ck === 'failed' ? `${EV.res(ck, 'check ' + ck)}` : e(s === 'open' ? (M.ended ? 'not judged' : 'not judged yet') : s);
      return `<g data-step="${M.recStep[h.id] ?? 0}"${EV.freshAttr(h.id)} data-node="${h.id}"${ck ? ` data-check="${ck}"` : ''} data-wd="h:${h.id}" tabindex="0" aria-label="${e(h.id + ': ' + (h.question || h.text))}">${ringed.has(h.id) ? `<rect class="ring" x="${p.x - 4}" y="${p.y - 4}" width="${NW + 8}" height="${NH + 8}" rx="9"/>` : ''}
        ${EV.box(p.x, p.y, NW, NH, 'model', small ? `<b>${h.id}</b> ${['supported', 'refuted', 'inconclusive'].includes(s) ? EV.gkey(s) : s === 'dropped' ? EV.gkey('dropped') : ck === 'held' || ck === 'failed' ? EV.gkey(ck) : ''}` : `<b>${h.id}</b> · ${word}<br><small data-own="model"${why ? ' class="bx-1"' : ''}>${e(short)}</small>${why ? `<span class="bx-why" data-why="${ck}">${why}</span>` : ''}`, T ? `data-act="open" data-t="test" data-id="${e(T)}"` : `data-act="open" data-t="hyp" data-id="${h.id}"`, cls)}${EV.measMark ? EV.measMark(p.x + NW, p.y + NH, 'h:' + h.id) : ''}</g>`; }).join('');
    // a running session: the place of the next question, in the column of the turn that is being written
    const under = t => M.hyps.filter(h => h.turn === t).length + explores.filter(q => q.turn === t).length, colX = t => 6 + (cols.indexOf(t) + 1) * (NW + GX);
    const sx = slotTurn == null ? null : { x: colX(slotTurn), y: 8 + under(slotTurn) * (NH + GY) };
    // an exploration: its experiment, in the column of its turn under that turn's hypotheses; pointing at it opens the experiment's box, a click opens the experiment
    const exAt = {}, expl = explores.map((q, i) => { const j = M.hyps.filter(h => h.turn === q.turn).length + explores.filter((o, k) => o.turn === q.turn && k < i).length, bx = colX(q.turn), by = 8 + j * (NH + GY), text = String(q.x.question || 'not recorded'); exAt[q.x.id] = { x: bx, y: by };
      return `<g data-step="${M.recStep[q.x.id] ?? 0}" data-explore="${e(q.x.id)}" data-wd="x:${e(q.x.id)}" tabindex="0">${EV.box(bx, by, NW, NH, 'model', small ? `<b>${e(q.x.id)}</b>` : `<b>${e(q.x.id)}</b> · <span class="mut">explores</span><br><small data-own="model">${e(text.length > chars ? text.slice(0, chars - 2) + '…' : text)}</small>`, `data-act="open" data-t="exp" data-id="${e(q.x.id)}"`, 'st-explore')}${EV.measMark ? EV.measMark(bx + NW, by + NH, 'x:' + q.x.id) : ''}</g>`; }).join('');
    // a running session in its last turn: no new hypothesis can come, so the turn's column says what the turn is for
    const lastBox = lastTurn == null ? '' : (lx => `<g id="map-last" data-slot="report"><rect class="bx slotbox" x="${lx}" y="${8 + under(lastTurn) * (NH + GY)}" width="${NW}" height="${NH}" rx="6"/><foreignObject x="${lx + 2}" y="${8 + under(lastTurn) * (NH + GY)}" width="${NW - 2}" height="${NH}"><div xmlns="http://www.w3.org/1999/xhtml" class="bt">${EV.nowDot()}<b>${small ? 'last' : 'the last turn'}</b>${small ? '' : `<br><small>${now.mode === 'report' ? 'only the final report is accepted now' : 'the simulations are used up: the final report is due'}</small>`}</div></foreignObject></g>`)(colX(lastTurn));
    const slot = sx ? `<g id="map-next" data-slot="question"><rect class="bx slotbox" x="${sx.x}" y="${sx.y}" width="${NW}" height="${NH}" rx="6"/><foreignObject x="${sx.x + 2}" y="${sx.y}" width="${NW - 2}" height="${NH}"><div xmlns="http://www.w3.org/1999/xhtml" class="bt">${EV.nowDot()}<span class="mut">empty</span>${small ? '' : '<br><small>the next hypothesis, if this reply states one</small>'}</div></foreignObject></g>` : '';
    // the last box: the answer
    const ex = 6 + (cols.length + 1) * (NW + GX), R0 = repNow ? EV.recParts() : null, kn0 = (M.brief && M.brief.knobs) || {}, adj = !R0 ? '' : R0.text ? String(R0.text) : R0.differ.map(([k, v]) => `${EV.LABEL[k] || k} ${k in kn0 ? EV.adjVal(k, kn0[k].default) + ' → ' : ''}${EV.adjVal(k, v)}`).join(', ') || 'no setting changed';
    const adjTo = !R0 ? '' : R0.text ? String(R0.text) : R0.differ.map(([k, v]) => `${EV.LABEL[k] || k} ${EV.adjVal(k, v)}`).join(', ') || 'no setting changed';  // in the box: the proposed values alone (where each starts from is on the card)
    const because0 = repNow ? ((M.claims.find(q => q.role === 'supports') || M.claims[0] || {}).text || 'it states no claim') : '';  // its first reason: the first claim that supports the recommendation (a report without roles: its first claim)
    const endHtml = repNow ? (small ? `${EV.bulb()}<b>answer</b>` : `${EV.bulb()}<b>Its answer</b> <span class="mut">· ${M.claims.length} ${EV.term('Claim', M.claims.length === 1 ? 'claim' : 'claims')}</span><br><small data-own="model">proposes ${e(cutTo(adjTo, Math.floor(chars / 2) - 9))}</small><br><small><span class="mut">because</span> <span data-own="model">${e(cutTo(because0, Math.max(40, chars * 2 - 12)))}</span></small>`) : M.ended ? (small ? '<b>no answer</b>' : `<b>No final report</b><br><small>${e(cutTo((M.meta && M.meta.how) || 'the session ended without one', chars))}</small>`) : '';
    const EH = repNow && !small ? Math.min(Math.max(NH, H - 24), NH * 2 + GY) : NH;  // the answer's box holds its first reason too: it is as tall as two boxes where there is room
    const end = !endBox ? '' : endHtml ? `<g id="map-end" data-end="${repNow ? 'report' : 'none'}"${repNow && M.repRec ? ` data-step="${M.recStep[M.repRec.id] ?? 0}"` : ''}>${EV.box(ex, 8, NW, EH, 'model', endHtml, repNow ? 'data-act="open" data-t="report" data-id="report" data-wd="a:report"' : 'data-act="goto" data-id="s-proposes"', repNow ? 'st-answer' : '')}</g>`
      : `<g id="map-end" data-end="empty" data-slot="report"><rect class="bx slotbox" x="${ex}" y="8" width="${NW}" height="${NH}" rx="6"/><foreignObject x="${ex + 2}" y="8" width="${NW - 2}" height="${NH}"><div xmlns="http://www.w3.org/1999/xhtml" class="bt"><b>Its answer</b><br><small class="mut">empty: the final report is not written yet</small></div></foreignObject></g>`;
    // from each hypothesis the report's claims rest on, a quiet line to the answer
    const toEnd = !repNow ? '' : [...ringed].filter(id => pos[id]).map(id => { const a = pos[id], x1 = a.x + NW, y1 = a.y + NH / 2; return `<g data-to-answer="${e(id)}" data-step="${M.repRec ? M.recStep[M.repRec.id] ?? 0 : 0}"><path class="edge answer" d="${route(x1, y1, ex - 2, 8 + EH / 2, 0)}" marker-end="url(#ev-ah)"/></g>`; }).join('');
    const heads = `<text x="6" y="${H + 4}">start</text>${endBox ? `<text x="${ex}" y="${H + 4}">the end</text>` : ''}` + cols.map((t, i) => `<text x="${6 + (i + 1) * (NW + GX)}" y="${H + 4}"${now && now.turn === t ? ' class="map-now-t"' : ''}>turn ${t}${now && now.turn === t ? ' · now' : ''}</text>`).join('');
    // a running session: the whole column of the turn that is being worked on stands on a ground of the accent colour, so that where the work is shows at a glance
    const nowCol = now ? cols.indexOf(now.turn) : -1, band = nowCol < 0 ? '' : `<rect class="map-now" id="map-now" data-turn="${now.turn}" x="${(6 + (nowCol + 1) * (NW + GX) - Math.min(14, GX * 0.25)).toFixed(1)}" y="1" width="${(NW + 2 * Math.min(14, GX * 0.25)).toFixed(1)}" height="${H + 8}" rx="10"/>`;
    // a light rule in the middle of each gap between two columns (the start, each turn, the end), under the arrows: where one turn stops and the next begins
    const seps = Array.from({ length: cols.length + (endBox ? 1 : 0) }, (_, i) => { const x = (6 + (i + 1) * (NW + GX) - GX / 2).toFixed(1); return `<line class="map-sep" x1="${x}" y1="2" x2="${x}" y2="${H + 6}"/>`; }).join('');
    const defs = `${EV.arrowDefs()}<defs>${[['ev-ag', '--good'], ['ev-ab', '--critical']].map(([id, c]) => `<marker id="${id}" viewBox="0 0 10 10" refX="9" refY="5" markerUnits="userSpaceOnUse" markerWidth="9" markerHeight="9" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="var(${c})"/></marker>`).join('')}</defs>`;
    const kinds = new Set(edges.filter(x => EV.seen(x.to)).map(x => x.kind)), key = (k, cls, text) => (kinds.has(k) ? `<span class="mk" data-k="${k}"><svg width="30" height="10" style="display:inline;vertical-align:0"><path class="edge ${cls}" d="M1,5 H28"/></svg> ${text}</span>` : '');
    return `<div class="ev-map" data-cols="${n}"${small ? ' data-small="1"' : ''}><svg viewBox="0 0 ${W} ${H + 10}" width="${W}" height="${H + 10}" style="${EV.LEAN ? `width:100%;max-width:${W}px;min-width:${Math.round(W * 0.85)}px` : 'max-width:100%'};height:auto" role="img" aria-label="The hypotheses by the turn they were stated in, and which follows from which">${defs}${band}${seps}${svgE}${toEnd}${!repNow ? '' : explores.filter(q => M.claims.some(c => (c.exps || []).includes(q.x.id) && !(c.tests || []).length)).map(q => `<g data-to-answer="${e(q.x.id)}" data-step="${M.repRec ? M.recStep[M.repRec.id] ?? 0 : 0}"><path class="edge answer" d="${route(exAt[q.x.id].x + NW, exAt[q.x.id].y + NH / 2, ex - 2, 8 + EH / 2, 0)}" marker-end="url(#ev-ah)"/></g>`).join('')}${brief}${EV.measMark ? EV.measMark(6 + NW, 8 + AH, 'x:X0') : ''}${nodes}${expl}${slot}${lastBox}${end}${signsOut.join('')}${heads}</svg></div>${EV.LEAN && avail < Math.round(W * 0.85) ? `<p class="sm map-on noprint">→ the board goes on to the right, to ${cols.length ? 'turn ' + e(String(cols[cols.length - 1])) : 'its end'} and the answer: scroll it sideways</p>` : ''}
      <div class="sm map-key" id="map-key">${(() => { const stOf = h => (st ? st[h.id] || 'open' : h.state), sq = cls => `<svg width="12" height="12" style="display:inline;vertical-align:-1px"><rect class="bx ${cls}" x="1" y="1" width="10" height="10" rx="3"/></svg>`, ln = cls => `<svg width="26" height="10" style="display:inline;vertical-align:0"><path class="edge ${cls}" d="M1,5 H25"/></svg>`;
        // The key is a small table of two rows: a BOX is a hypothesis and its look says how the AI judged it; an ARROW leads to a hypothesis and its colour says
        // what that one follows from. A look has a mark and a word or two; its whole sentence is in the box that opens when it is pointed at (EV.LEGEND_SAYS,
        // "key-…"). Only the looks this board has are listed. One line under the table says what pointing and clicking do.
        const it = (k, mark, text, attr) => `<span class="mk" ${attr} data-wd="l:key-${k}" tabindex="0">${mark} ${text}</span>`;
        const SAY = { supported: 'supported', refuted: 'refuted', inconclusive: 'inconclusive', dropped: 'dropped', 'ended without a verdict': 'never judged' };
        const boxes = EV.STATES.filter(q => q !== 'open' && M.hyps.some(h => stOf(h) === q)).map(q => it(q.split(' ')[0], sq(EV.stCls(q)), SAY[q] || e(q), `data-s="${e(q)}"`)).join('')
          + (M.hyps.some(h => ['open', 'ended without a verdict'].includes(stOf(h)) && h.tests.some(q => { const c = M.testById[q].check; return c && EV.seen(c.id); })) ? it('ck', sq('ck-held') + ' ' + sq('ck-failed'), 'checked, not judged yet', 'id="mk-ck"') : '')
          + (ringed.size ? it('ans', '<svg width="30" height="14" style="display:inline;vertical-align:-2px"><rect class="bx" x="3" y="3" width="8" height="8" rx="2"/><rect class="ring" x="1" y="1" width="12" height="12" rx="4" style="stroke-width:1.6"/><path class="edge answer" d="M14,7 H29"/></svg>', 'cited by the final report', 'id="mk-ans"') : '')
          + (small ? '<span class="mk">many turns: a box holds only the name and how it ended</span>' : '');
        const key = (k, cls, text) => (kinds.has(k) ? it(k, ln(cls), text, `data-k="${k}"`) : '');
        const arrows = key('good', 'good', 'one that was supported') + key('bad', 'bad', 'one that was refuted') + key('mixed', 'mixed', 'results of both kinds') + key('neutral', 'neutral', 'an inconclusive result')
          + key('weak', 'weak', 'an experiment’s result table') + key('brief', 'brief', 'the brief or the baseline');
        const row = (g, name, is, items) => `<div class="mk-grp" data-g="${g}"><b class="mk-h">${name}</b><span class="mk-is${items ? '' : ' mk-all'}">${is}</span>${items ? `<span class="mk-items">${items}</span>` : ''}</div>`;
        return row('box', 'A box', 'is a hypothesis, as the AI judged it', boxes)
          + (recorded ? (arrows ? row('arrow', 'An arrow', 'leads to a hypothesis that follows from', arrows) : '')
            : row('arrow', 'Arrows', `none: what each hypothesis follows from is ${EV.nr} (this session was recorded before that field existed)`, ''))
          // the ruler mark, where the board has one (2026-11-22, the operator): the measurements the researcher made up for that box
          + (EV.measAll && EV.measAll().some(q => EV.seen(q.id) && (q.at || []).length) ? row('meas', 'A ruler', 'on a box: measurements the researcher made up for it',
              `${it('meas', `<svg class="ms-key" viewBox="0 0 31 15" width="31" height="15" style="display:inline" aria-hidden="true"><rect x="0.5" y="0.5" width="30" height="14" rx="4"/><path d="M4 11h12M5.5 11V8M8.5 11V5M11.5 11V8M14.5 11V5"/><text x="19" y="11.5">3</text></svg>`, 'how many · click it to open them', '')}`) : '')
          + '<p class="mk-do noprint">point at a box, an arrow or its sign to read it · click to open it</p>'; })()}</div>`;
  },
});
