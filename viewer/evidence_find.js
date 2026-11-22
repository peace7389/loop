// "What it needed to find out": first the board (EV.viewMap in evidence_views.js): one box per hypothesis in the column
// of its turn, and an arrow, coloured by the result that led onward, to each hypothesis that follows from it. Under
// it, folded ("The same, test by test"; open in Full, and the browser remembers it), the table: one row per test, in the order the tests were stated. Four columns, each a recorded
// text or a measured number: the question (the hypothesis's question; a session that recorded none: the hypothesis
// text, cut to two lines), the outcome (the model's verdict; "void" where the check compared a simulation with itself),
// what was measured (the check's numbers in words: "483 Mbps, not over 700 Mbps"), and what it led to (a mark for each
// later hypothesis that follows from the test, which goes to that hypothesis's row). A failed check is a result: it has
// no warning colour. A row opens its notebook card and brings it into view (one of the page's stated exceptions to
// "a click never moves the page"). At most nine rows are shown, then "n more". The replay greys the rows recorded after
// its step; a check or a verdict recorded later is absent from its row. In a running session a row whose simulations are
// running says so, and while a reply is written that may ask a new question the table ends with one empty row.
// Last, folded too, "Turn by turn: who did what" (evidence_turns.js): the detail of the same work, every record of each turn in the
// column of whoever made it (closed on a first visit; open in Full; the browser remembers it).
// The lean page (EV.LEAN, since 2026-11-22) draws the board, the parts of a running session and turn by turn only: not "From one hypothesis to
// the next", not the table "The same, test by test".
// ======================================================================================================
Object.assign(EV, {
  // the lean page: while "Turn by turn" is open, the board stays in view under the header strip and only the turns move (2026-11-22, the operator: the big
  // picture stays while the details are searched). A board taller than 45 % of the window is not held there: it would leave too little room for the turns.
  pinFit() { const mp = document.querySelector('#s-map.map-pin'); if (!mp) return; const h = mp.offsetHeight; mp.classList.toggle('map-tall', h > 0.45 * innerHeight); document.getElementById('ev').style.setProperty('--map-h', h + 'px'); },
  // The card that opens when a hypothesis's box on the board is pointed at (through the box of evidence_words.js, key
  // "h:<id>"). Made for reading at a glance: the name and how it ended; the question, larger; then labelled lines, always
  // in this order, each a recorded text or a measured number: why it asked (the hypothesis's `why`; "not recorded" for a
  // session from before the field), what it follows from (each result named, with its sign), what was expected (the
  // decision rule of its last test, for reading), the result (the check's numbers in words, held or failed), the
  // conclusion (the verdict and the first sentence of its reason), what it led to. Only what the replay's step has reached.
  hypPop(id) {
    const M = EV.M, e = EV.e, seen = EV.seen, h = M.hypById[id]; if (!h || !seen(h.id)) return '';
    const st = EV.s.step == null ? h.state : EV_DATA.stateAt(M, EV.s.step)[h.id] || 'open', ts = h.tests.map(q => M.testById[q]).filter(T => seen(T.exp)), T = ts[ts.length - 1] || null;
    const c = T && T.check && seen(T.check.id) ? T.check : null, v = h.verdict && seen(h.verdict.id) ? h.verdict : null;
    const word = ['supported', 'refuted', 'inconclusive'].includes(st) ? EV.verdictRes(st) : e(st === 'open' ? (M.ended ? 'not judged' : 'not judged yet') : st);
    const from = [...new Set((h.follows || []).map(EV.fromLine).filter(Boolean))];
    const fromWhy = h.from_why && seen(h.from_why) ? (M.whyById || {})[h.from_why] : null, citedBy = EV.repNow() ? M.claims.filter(q => (q.hyps || []).includes(id)) : [];  // the links of the chain on both sides: the guess before it, the claims after it
    const led = (M.mapEdges || EV.mapEdges()).filter(x => x.from === id && x.kind !== 'weak' && seen(x.to)).map(x => e(x.to)), [first] = v ? EV.nbFirst(v.because) : [''];
    // The card reads as three parts with a look each: where the question came from (plain lines); the test, on a tinted ground, with what was expected and what
    // was found as short lines, one per comparison of the rule (the first three; each found line carries its sign); and what came of it (the verdict, what it led to).
    const line = (k, body, own, cls) => `<div class="hp-l${cls ? ' ' + cls : ''}" data-hp="${k === 'Verdict' ? 'conclusion' : k.toLowerCase().replace(/ /g, '-')}"><span class="hp-k">${k}</span><div class="hp-v"${own ? ` data-own="${own}"` : ''}>${body}</div></div>`, none = t => `<span class="mut">${t}</span>`;
    const parts = T && T.rule ? EV.ruleParts(T, !!c && !c.void) : [], more = n => (n > 3 ? `<li class="hp-more">and ${n - 3} more comparison${n - 3 === 1 ? '' : 's'}: in its test</li>` : '');
    const expected = parts.length ? `<ul class="hp-list" data-exact="1">${parts.slice(0, 3).map(q => `<li><span class="hp-what">${e(q.left)}</span> <b>${e(q.word)}</b> ${e(q.right)}</li>`).join('')}${more(parts.length)}</ul>` : T && T.rule ? EV.ruleRead(T, 4) : h.prediction ? e(h.prediction) : none('no decision rule yet');
    const found = !c ? none(T ? (M.ended ? 'not checked' : 'not yet') : M.ended ? 'not put to a test' : 'not tested yet') : c.void || !parts.some(q => q.held != null) ? `${EV.checkRes(c)}${c.void ? '' : ' · ' + (EV.measuredWords(T) || '')}`
      : `<p class="hp-res">${EV.checkRes(c)} <span class="sm">· the rule as a whole</span></p><ul class="hp-list">${parts.slice(0, 3).map(q => (q.held == null ? '<li class="mut">no value</li>' : `<li data-held="${q.held ? 1 : 0}">${EV.res(q.held ? 'held' : 'failed', `${q.a} ${q.held ? '' : 'not '}${q.word} ${q.b}`)}</li>`)).join('')}${more(parts.length)}</ul>`;
    return `<div class="hp" data-hyp="${e(h.id)}"><p class="hp-h"><b class="hp-id">${e(h.id)}</b><span class="hp-badge ${EV.stCls(st)}">${word}</span><span class="hp-turn">stated in turn ${h.turn}</span></p>
      <p class="hp-q" data-own="model">${e(h.question || h.text)}</p>
      ${fromWhy ? line('From guess', `<span class="hp-chip">${e(fromWhy.id)}</span> <span data-own="model">${e(fromWhy.guess)}</span>`, '', 'hp-clamp') : ''}
      ${line('Why', h.why ? e(h.why) : none('not recorded: sessions before 14 November 2026 were not asked for it'), h.why ? 'model' : '', 'hp-clamp')}
      ${line('Follows from', from.length ? from.join('<br>') : h.follows ? none('nothing earlier: a first hypothesis') : none('not recorded'), '', 'hp-clamp')}
      <div class="hp-test">${line('Expected', expected, parts.length || (T && T.rule) ? '' : h.prediction ? 'model' : '', parts.length ? '' : 'hp-clamp')}</div><div class="hp-test">${line('Result', found, '', c && !c.void && parts.some(q => q.held != null) ? '' : 'hp-clamp')}</div>
      ${line('Verdict', v ? `<span class="hp-badge ${EV.stCls(v.result)}">${EV.verdictRes(v.result)}</span>${first ? ` <span class="hp-because">${e(first)}</span>` : ''}` : none(M.ended ? 'no verdict was given' : 'not judged yet'), v ? 'model' : '', 'hp-clamp')}
      ${citedBy.length ? line('Cited by', citedBy.map(q => `<span class="hp-chip">claim ${q.n}</span>`).join(' ') + ' <span class="sm">of the final report</span>') : ''}
      ${line('Led to', led.length ? '→ ' + led.map(x => `<span class="hp-chip">${x}</span>`).join(', ') : none(M.ended ? 'no later hypothesis names its result' : 'nothing yet'))}
      <p class="sm hp-foot">${ts.length > 1 ? `Put to ${ts.length} decision rules: the last one is shown. ` : ''}Click the box to open its test beside the page.</p></div>`;
  },
  // ---- the card of a TEST (a hypothesis put to one decision rule), on the glance's "H1 held" and "H1 failed": what was tested, the outcome of the harness's
  // check on a badge in the colour of that outcome, then expected against found, one short line per comparison, the simulations in words, the rival, and what
  // the AI concluded from it. And the card of a VERDICT, on "H1 supported" and "H1 refuted": the AI's judgement on a badge, its reason in its own words, the
  // check it rests on (marked when the two disagree), and what it decided to do next. Only what is recorded by the step the page is at.
  testPop(id) {
    const M = EV.M, e = EV.e, seen = EV.seen, T = M.testById[id]; if (!T || !seen(T.exp)) return ''; const h = M.hypById[T.hyp], c = T.check && seen(T.check.id) ? T.check : null, v = T.verdict && seen(T.verdict.id) ? T.verdict : null;
    const line = (k, body, own, cls) => `<div class="hp-l${cls ? ' ' + cls : ''}" data-hp="${k === 'Verdict' ? 'conclusion' : k.toLowerCase().replace(/ /g, '-')}"><span class="hp-k">${k}</span><div class="hp-v"${own ? ` data-own="${own}"` : ''}>${body}</div></div>`, none = t => `<span class="mut">${t}</span>`;
    const res = c ? (c.void || M.voidIds.has(c.id) ? 'void' : c.result) : null, parts = T.rule ? EV.ruleParts(T, !!c && res !== 'void') : [], more = n => (n > 3 ? `<li class="hp-more">and ${n - 3} more comparison${n - 3 === 1 ? '' : 's'}: in its test</li>` : '');
    const badge = !c ? `<span class="hp-badge">${T.rule ? (M.ended ? 'not checked' : 'waits for its simulations') : 'no decision rule'}</span>` : `<span class="hp-badge ck-${e(res)}">${EV.checkRes(c)}</span>`;
    const expected = parts.length ? `<ul class="hp-list" data-exact="1">${parts.slice(0, 3).map(q => `<li><span class="hp-what">${e(q.left)}</span> <b>${e(q.word)}</b> ${e(q.right)}</li>`).join('')}${more(parts.length)}</ul>` : T.rule ? EV.ruleRead(T, 4) : none('no decision rule was stated');
    const found = !c ? none(M.ended ? 'not checked' : 'not yet') : res === 'void' || !parts.some(q => q.held != null) ? `${EV.checkRes(c)}${res === 'void' ? ` <span class="sm">· ${e(EV.VOID)}</span>` : ''}`
      : `<ul class="hp-list">${parts.slice(0, 3).map(q => (q.held == null ? '<li class="mut">no value</li>' : `<li data-held="${q.held ? 1 : 0}">${EV.res(q.held ? 'held' : 'failed', `${q.a} ${q.held ? '' : 'not '}${q.word} ${q.b}`)}</li>`)).join('')}${more(parts.length)}</ul>`;
    const [first] = v ? EV.nbFirst(v.because) : [''];
    return `<div class="hp" data-test="${e(T.id)}"><p class="hp-h"><b class="hp-id">Test of ${e(T.hyp)}</b>${badge}<span class="hp-turn">experiment ${e(T.exp)} · turn ${e(T.turn)}</span></p>
      <p class="hp-q" data-own="model">${e(h ? h.question || h.text : '')}</p>
      <div class="hp-test">${line('Expected', expected, '', parts.length ? '' : 'hp-clamp')}</div><div class="hp-test">${line('Result', found)}</div>
      ${line('Simulations', `<span data-exact="1">${EV.nbPlan(T)}</span>`, '', 'hp-clamp')}
      ${T.rival ? line('Rival', `${e(T.rival)}${T.rival_predicts ? ` <span class="sm">· under it the rule would have ${e(T.rival_predicts)}</span>` : ''}`, 'model', 'hp-clamp') : ''}
      ${line('Verdict', v ? `<span class="hp-badge ${EV.stCls(v.result)}">${EV.verdictRes(v.result)}</span>${first ? ` <span class="hp-because">${e(first)}</span>` : ''}` : none(M.ended ? 'no verdict was given' : 'not judged yet: the AI gives it in its next reply'), v ? 'model' : '', 'hp-clamp')}
      <p class="sm hp-foot">Click to open the test beside the page.</p></div>`;
  },
  verdictPop(vid) {
    const M = EV.M, e = EV.e, seen = EV.seen, r = M.byId[vid]; if (!r || r.type !== 'verdict' || !seen(vid)) return ''; const b = r.body, h = M.hypById[b.for], T = M.tests.filter(q => q.verdict && q.verdict.id === vid).pop() || null, c = T && T.check && seen(T.check.id) ? T.check : null;
    const line = (k, body, own, cls) => `<div class="hp-l${cls ? ' ' + cls : ''}" data-hp="${k === 'Verdict' ? 'conclusion' : k.toLowerCase().replace(/ /g, '-')}"><span class="hp-k">${k}</span><div class="hp-v"${own ? ` data-own="${own}"` : ''}>${body}</div></div>`, none = t => `<span class="mut">${t}</span>`;
    const odd = T && c && EV.contradicts(T.verdict, [c]), res = c ? (c.void || M.voidIds.has(c.id) ? 'void' : c.result) : null;
    return `<div class="hp" data-verdict="${e(vid)}"><p class="hp-h"><b class="hp-id">Verdict on ${e(b.for)}</b><span class="hp-badge ${EV.stCls(b.result)}">${EV.verdictRes(b.result)}</span><span class="hp-turn">the AI, in turn ${e(r.turn)}</span></p>
      <p class="hp-q" data-own="model">${e(h ? h.question || h.text : '')}</p>
      ${line('Because', b.because ? e(b.because) : none('no reason recorded'), b.because ? 'model' : '', 'hp-clamp6')}
      <div class="hp-test">${line('Its check', c ? `<span class="hp-badge ck-${e(res)}">${EV.checkRes(c)}</span>${res !== 'void' && EV.measuredWords(T) ? ` <span class="sm">${EV.measuredWords(T)}</span>` : ''}${odd ? `<p class="hp-odd">${EV.warn('the verdict disagrees with the harness’s check')}</p>` : ''}` : none('no check is recorded for it'), '', 'hp-clamp')}</div>
      ${line('So next', b.next ? e(b.next) : none('nothing stated'), b.next ? 'model' : '', 'hp-clamp')}
      <p class="sm hp-foot">Click to open ${T ? 'its test' : 'the hypothesis'} beside the page.</p></div>`;
  },
  // ---- why a simulation has its name. The name is the AI's own label and says nothing by itself, so the page reads it against the experiment's designs: for
  // each word of the name (its parts between "_"), the settings on which every simulation that carries the word agrees while another simulation of the
  // experiment differs ("bbr": TCP type Bbr; "w05": ratio 0.05; "low": UDP rate 100 Mbps). A word that sets no setting apart is said to be the AI's own. This is
  // a reading from the recorded designs, not the AI's statement, and the box says so.
  namePop(key) {
    const M = EV.M, e = EV.e, i = key.indexOf(':'), xid = key.slice(0, i), label = key.slice(i + 1), x = M.expById[xid], runs = (x && x.runs) || [], me = runs.find(q => q.label === label); if (!me) return '';
    const kn = (M.brief && M.brief.knobs) || {}, keys = [...new Set([...Object.keys(kn), ...runs.flatMap(q => Object.keys(q.params || {}))])], val = (q, k) => (q.params && k in q.params ? q.params[k] : (kn[k] || {}).default);
    const num = v => (typeof v === 'number' ? v : /^[0-9.]+\s*[kMG]?bps$/.test(String(v)) ? EV.knNum(v) : NaN), same = (a, b) => (isNaN(num(a)) || isNaN(num(b)) ? String(a) === String(b) : num(a) === num(b)), show = (k, v) => `${TH_DATA.KNOB[k] || k} ${k === 'tcpBufBytes' && /^\d+$/.test(String(v)) ? EV.bytes(+v) : TASK_VIEW._rate(String(EV.val(k, v))).replace(/^Tcp/, '') + (k === 'duration' ? ' s' : '')}`;
    const words = label.split('_').filter(Boolean), toks = q => String(q.label || '').split('_');
    const rows = words.map(w => { const G = runs.filter(q => toks(q).includes(w)), O = runs.filter(q => !toks(q).includes(w));
      const ks = O.length ? keys.filter(k => G.every(q => same(val(q, k), val(G[0], k))) && O.some(q => !same(val(q, k), val(G[0], k)))) : [];
      return [w, ks.length ? ks.map(k => show(k, val(me, k))).join(', ') : null, G.length, O.length]; });
    const differs = keys.filter(k => kn[k] && 'default' in kn[k] && !same(val(me, k), kn[k].default)).map(k => show(k, val(me, k))), sim = M.sims.find(q => q.exp === xid && q.label === label && EV.seen(q.id));
    return `<p class="wd-h"><b>${e(label)}</b><span class="wd-kind">a simulation’s name</span></p>
      <p class="wd-lead">The AI chose this name. Read against the ${runs.length} simulation${runs.length === 1 ? '' : 's'} of ${e(xid)}, its parts mean:</p>
      <dl class="wd-kv nm-kv" data-exact="1">${rows.map(([w, says, g, o]) => `<dt><code>${e(w)}</code></dt><dd data-nm="${e(w)}">${says ? `<b>${e(says)}</b> <span class="nm-n">${g === 1 ? 'only this one' : `${g} of ${g + o} carry it`}</span>` : `<span class="mut">${o ? 'the AI’s own word: no setting sets apart the simulations that carry it' : 'every simulation of this experiment carries it'}</span>`}</dd>`).join('')}</dl>
      <dl class="wd-kv" data-exact="1"><dt>Set</dt><dd data-nm-set="1">${differs.length ? e(differs.join(' · ')) : 'every setting at the brief’s default'}</dd>${sim && sim.same_as ? `<dt>Not run again</dt><dd>the settings and seed of ${e(sim.same_as)}: its result was returned</dd>` : ''}</dl>
      <p class="wd-foot">read by the page from the recorded designs, not stated by the AI</p>`;
  },
  // one result a hypothesis follows from, in words: a check with what was measured, a verdict, an experiment's result table, the brief
  fromLine(f) {
    const M = EV.M, e = EV.e, r = M.byId[f]; if (f === 'brief') return 'the brief'; if (!r) return null;
    if (r.type === 'verdict') return `${EV.gkey(EV.vk(r.body.result))}${e(r.body.for)} was ${r.body.result === 'inconclusive' ? 'left inconclusive' : e(r.body.result)}`;
    if (r.type === 'check') { const k = M.voidIds.has(f) ? 'void' : r.body.result, T = M.tests.find(q => q.check && q.check.id === f), m = T && k !== 'void' ? EV.measuredWords(T) : null; return `${EV.gkey(EV.ck(k))}the check of ${e(r.body.for)} ${k === 'void' ? 'was void' : e(k)}${m ? `: ${m}` : ''}`; }
    const x = r.type === 'evidence' ? r.body.experiment || r.parent : r.type === 'simulation' ? r.parent : null; return x === 'X0' ? 'the baseline' : x ? `the results of experiment ${e(x)}` : null;
  },
  // the card of an arrow of the board (key "e:<from>><to>"): the result of the earlier hypothesis that the later one names, with what was measured,
  // how it was judged and what the AI said it would do next. A dotted arrow: only that experiment's result table is named.
  edgePop(key) {
    const M = EV.M, e = EV.e, seen = EV.seen, [from, to] = key.split('>'), x = (M.mapEdges || EV.mapEdges()).find(q => q.from === from && q.to === to); if (!x || !seen(to)) return '';
    const lines = [...new Set(x.ids.filter(f => f === 'brief' || seen(f)).map(EV.fromLine).filter(Boolean))], h = M.hypById[from], v = h && h.verdict && seen(h.verdict.id) && x.ids.some(f => f === h.verdict.id || (M.byId[f] || {}).type === 'check') ? h.verdict : null;
    return `<div class="hp" data-edge="${e(key)}"><p class="hp-h"><b>${from === 'brief' ? 'the brief' : e(from)} → ${e(to)}</b> <span class="sm">· what ${e(to)} follows from</span></p>
      <div class="hp-l" data-hp="result"><span class="hp-k">${x.kind === 'weak' ? 'It names' : 'The result'}</span><div class="hp-v">${lines.join('<br>') || '<span class="mut">not recorded</span>'}${x.kind === 'weak' ? '<br><span class="mut">only the result table of that experiment, not a check or a verdict</span>' : ''}</div></div>
      ${v ? `<div class="hp-l" data-hp="judged"><span class="hp-k">Verdict</span><div class="hp-v" data-own="model">${EV.verdictRes(v.result)} · ${e(EV.nbFirst(v.because)[0])}</div></div><div class="hp-l" data-hp="next"><span class="hp-k">Its next step</span><div class="hp-v" data-own="model">${e(v.next || 'not recorded')}</div></div>` : ''}
      <p class="sm hp-foot">${from === 'brief' ? 'Click to open the brief beside the page.' : `Click to open the test of ${e(from)} beside the page.`}</p></div>`;
  },
  // the card of the answer (the last box of the board; key "a:report"): what it proposes, what it expects, and its reasons: the claims that support the
  // system behaves (its "diagnosis"), those that give reasons for the recommendation ("because"), those that say when it would change, with "holds when" and "breaks when" ("but")
  answerPop() {
    const M = EV.M, e = EV.e, rep = EV.repNow(); if (!rep) return ''; const R = EV.recParts(), X = EV.expRows(rep), kn = (M.brief && M.brief.knobs) || {}, roles = M.claims.length > 0 && M.claims.every(q => q.role);
    // The card in four looks. What it proposes: each changed setting on a chip, "from → to", on the answer's own warm ground. What it expects: each measure a
    // small name over its value. Its claims, by their part in the argument (diagnosis, because, but): one row each, the AI's sentence at the left (cut at three
    // lines here, in full in the report; a setting's name, a "name=value" and a number with its unit are set off) and what it cites at the right. "Breaks when" is
    // not repeated here: the claims under "But" say it, and the report has it in full.
    const chips = !R ? '<span class="mut">not recorded</span>' : R.text ? e(R.text) : R.differ.map(([k, v]) => `<span class="ap-chip">${e(EV.LABEL[k] || k)} ${k in kn ? `<span class="ap-from">${e(EV.adjVal(k, kn[k].default))} →</span> ` : ''}<b>${e(EV.adjVal(k, v))}</b></span>`).join('') || '<span class="mut">no setting changed</span>';
    const stats = X && X.top.length ? X.top.map(([k, v]) => `<span class="ap-stat"><span class="ap-sn">${e(TH_DATA.PLAIN[k] || k)}</span><b>${EV.v4(k, v)}</b></span>`).join('') : '';
    const cites = q => (q.cites.some(c => EV.seen(c.id)) ? EV.claimMarks(q, EV.seen) : (q.exps || []).some(x => EV.seen(x)) ? `<span class="cm" data-kind="nocheck">results of ${e(q.exps.filter(x => EV.seen(x)).join(', '))}</span>` : EV.claimMarks(q, EV.seen));
    const claim = q => `<div class="ap-c"><span class="ap-t" data-own="model">${EV.hl(q.text)}</span><span class="ap-m sm">${cites(q)}</span></div>`, of = r => M.claims.filter(q => q.role === r);
    const line = (k, body, cls) => (body ? `<div class="hp-l${cls ? ' ' + cls : ''}" data-hp="${k.toLowerCase().replace(/ /g, '-')}"><span class="hp-k">${k}</span><div class="hp-v ap-v">${body}</div></div>` : '');
    const part = (k, list, says) => (list.length ? `<div class="hp-l ap-part" data-hp="${k.toLowerCase().replace(/ /g, '-')}"><span class="hp-k"><b>${k}</b><span class="ap-says">${says}</span></span><div class="hp-v ap-v">${list.map(claim).join('')}</div></div>` : '');
    return `<div class="hp ap"><p class="hp-h">${EV.bulb()}<b>Its answer</b><span class="wd-kind">final report · ${M.claims.length} claim${M.claims.length === 1 ? '' : 's'}</span></p>
      <div class="ap-top">${line('Proposes', `<div class="ap-chips" data-exact="1">${chips}</div>`)}${line('Expects', stats ? `<div class="ap-stats">${stats}</div>` : '')}</div>
      ${roles ? part('Diagnosis', of('background'), 'how the system behaves') + part('Because', of('supports'), 'reasons') + part('But', of('limits'), 'limits') : part('Its claims', M.claims, '')}
      <p class="sm hp-foot">Click the box to open the final report beside the page: every claim in full, with its evidence, and when it holds and breaks.</p></div>`;
  },
  FIND_ROWS: 9,
  // the check's numbers in words. One comparison: "483 Mbps, not over 700 Mbps"; several: joined by "and" / "or"
  measuredWords(T) {
    const c = T.check; if (!c) return null; if (c.void) return '<span class="mut">compared a simulation with itself</span>';
    const h = EV.readHtml(T.rule, { sims: Object.fromEntries(T.sims.map(s => [s.label, s])), plain: true, words: true, max: 4 });
    return h ? `<span class="rr" data-rr="measured" title="${EV.e(c.numbers == null ? '' : c.numbers + ' : ' + (c.recorded || c.result))}">${h}</span>` : `<code>${EV.e(c.numbers ?? '')}</code>`;
  },
  findCard() {
    const M = EV.M, S = EV.s, e = EV.e, st = id => M.recStep[id] ?? 0, end = M.steps.length - 1, at = (k, html) => `<span data-step="${k}">${html}</span>`;
    const now = EV.liveNow(), wait = T => !!now && now.phase === 'sims' && T.exp === now.exp;  // a running session: the tests whose simulations the simulator is working on
    const first = {}; M.tests.forEach(T => { if (!(T.hyp in first)) first[T.hyp] = T.id; });  // the row a hypothesis is first tested in
    const all = M.tests, open = S.full || S.findAll || all.length <= EV.FIND_ROWS, shown = open ? all : all.slice(0, EV.FIND_ROWS), sel = S.sel || {};
    const row = T => { const h = M.hypById[T.hyp], c = T.check, v = T.verdict, fol = T._fol || (T._fol = EV.followers(T)), fk = Math.max(v ? st(v.id) : 0, ...fol.ids.map(id => st(id)));
      const q = h && h.question ? e(h.question) : h ? `<span class="lc2">${e(h.text)}</span>` : EV.nr;
      const out = c && c.void ? at(st(c.id), `<span class="rs" data-void="1" title="${e(EV.VOID)}">${EV.gkey('void')}void</span>${v ? ` <span class="sm" data-step="${st(v.id)}">judged ${e(v.result)}</span>` : ''}`)
        : v ? at(st(v.id), EV.verdictRes(v.result)) : at(end, `<span class="mut">${M.ended ? 'none' : 'none yet'}</span>`);
      const led = fol.ids.filter(id => first[id]).map(id => `<a data-act="findrow" data-id="${e(first[id])}" title="${e(`${id} follows from this test${fol.via ? ' (through the table ' + fol.via + ' of its experiment)' : ''}: go to its row`)}">→ ${e(id)}</a>`).join(' ');
      return `<tr class="pick fr${sel.t === 'test' && sel.id === T.id ? ' sel' : ''}" id="fr-${e(T.id)}" data-act="find" data-id="${e(T.id)}" data-step="${st(T.exp)}"${EV.freshAttr(T.exp)}><td class="fq"><span class="fh" data-wd="h:${e(T.hyp)}">${e(T.hyp)}</span><span data-own="model">${q}</span>${h && h.why ? `<div class="sm fwhy lc2" title="${e(h.why)}"><span class="mut">why:</span> <span data-own="model">${e(h.why)}</span></div>` : ''}</td>
        <td class="fo">${out}</td><td class="fm">${c ? at(st(c.id), EV.measuredWords(T)) : at(end, wait(T) ? `<span class="nowp" data-now="sims">${EV.nowDot()}its simulations are running</span>` : `<span class="mut">${T.rule ? (M.ended ? 'not checked' : 'not yet') : 'no decision rule'}</span>`)}</td>
        <td class="fl">${led ? at(fk, `${c && c.result === 'failed' ? '<span class="fturn" title="Its check failed, and a later hypothesis follows from it">changed course</span> ' : ''}${led}`) : ''}</td></tr>`; };
    const recorded = all.filter(T => EV.seen(T.exp)), more = recorded.length - shown.filter(T => EV.seen(T.exp)).length;  // "n more" counts only what is recorded by the replay's step
    // while the AI writes a reply that may ask a new question: one empty row, which says so
    const next = now && now.phase === 'reply' && !now.mode ? `<tr class="fr-slot" id="fr-next" data-slot="question"><td class="fq">${EV.nowDot()}<span class="mut">The next hypothesis, if this reply states one</span></td><td class="fo"><span class="mut">empty</span></td><td class="fm"><span class="mut">empty</span></td><td class="fl"></td></tr>` : '';
    // the board (evidence_views.js): the hypotheses by turn, and which result led to which; under it, folded, the same test by test
    const listOpen = S.findOpen != null ? S.findOpen : S.full || EV.store('ev-find') === '1', stage = now ? EV.liveStage(now, !M.hyps.length) : '', mapH = M.hyps.length ? EV.viewMap() : '', cut = EV.LEAN ? mapH.indexOf('<div class="sm map-key"') : -1, board = M.hyps.length ? `<div id="s-map"${cut > 0 ? ' class="map-pin"' : ''}>${cut > 0 ? mapH.slice(0, cut) + '</div><div id="s-map-under">' + mapH.slice(cut) : mapH}${EV.repNow() && M.claims.some(c => c.hyps.length) ? `<p class="sm noprint map-path"><button data-act="path" class="${S.path ? 'on' : ''}">${S.path ? 'hide' : 'show'} the path to the answer</button> the hypotheses the final report's claims rest on, and what they follow from</p>` : ''}</div>` : '';
    return `<div class="ev-card" id="s-find"><h2>What it needed to find out</h2><p class="sec-q">Which hypotheses did it set itself, and what did it learn?</p>${stage}${now && EV.tilesHtml ? EV.tilesHtml(now) : ''}${board}${!EV.LEAN && EV.transView ? EV.transView() : ''}${now && !M.hyps.length ? '<p class="sm" id="find-none" style="text-align:center;max-width:none">No hypothesis yet. Its hypotheses will stand here, each in the column of its turn, with what each result led to.</p>' : ''}
      ${EV.LEAN || (now && !M.hyps.length) ? '' : all.length || next ? `<details id="find-list"${listOpen ? ' open' : ''}><summary><b>The same, test by test</b> <span class="sm">${recorded.length} ${recorded.length === 1 ? 'test' : 'tests'}: the hypothesis, the outcome, what was measured, what it led to</span><span class="cl noprint fl-btn" aria-hidden="true"><span class="fl-o">open</span><span class="fl-f">fold</span></span></summary><table class="ft"><thead><tr><th>The hypothesis</th><th>Outcome</th><th>Measured</th><th>Led to</th></tr></thead><tbody>${shown.map(row).join('')}${next}</tbody></table>
        ${more > 0 ? `<p class="sm noprint" id="find-more"><button data-act="findall">${more} more</button> ${recorded.length} tests in all</p>` : S.findAll && !S.full && all.length > EV.FIND_ROWS ? `<p class="sm noprint"><button data-act="findall">show the first ${EV.FIND_ROWS}</button></p>` : ''}
        <p class="sm">One row per ${EV.term('Test', 'test')}: one hypothesis put to one decision rule. A row opens its card in the notebook below. “Measured” is the ${EV.term('Check', 'check')}'s numbers; a check that failed is a result, not a fault.</p></details>`
        : `<p class="sm">${M.ended ? 'This session put no hypothesis to a test.' : 'No test yet.'}</p>`}${EV.turnsFold ? EV.turnsFold() : ''}</div>`;
  },
});
addEventListener('resize', () => { if (EV.pinFit) EV.pinFit(); });
// opening or folding turn by turn changes the held board's height (its padding and its rule): measured again once it is drawn
document.addEventListener('toggle', ev => { if (ev.target.id === 's-turns' && EV.pinFit) requestAnimationFrame(() => EV.pinFit()); }, true);
EV.act = Object.assign(EV.act || {}, {
  findall() { EV.s.findAll = !EV.s.findAll; EV.draw(); },
  // a row: its test opens in the detail pane, and its notebook card comes into view
  find(id) { EV.s.sel = { t: 'test', id }; EV.draw(); const el = [...document.querySelectorAll('#s-notebook .nb-card')].find(q => q.dataset.id === id); if (el) el.scrollIntoView({ block: 'center' }); },
  // a "led to" mark: to the row of the hypothesis that follows (every row is shown if it is past the ninth)
  findrow(id) { const S = EV.s; if (!document.getElementById('fr-' + id)) { S.findAll = true; EV.draw(); } const el = document.getElementById('fr-' + id); if (!el) return;
    el.scrollIntoView({ block: 'nearest' }); el.classList.add('flash'); setTimeout(() => el.classList.remove('flash'), 1600); },
});
document.getElementById('ev').addEventListener('toggle', ev => { if (ev.target.id === 'find-list') { EV.s.findOpen = ev.target.open; if (!EV.s.full) EV.store('ev-find', ev.target.open ? '1' : '0'); } }, true);
