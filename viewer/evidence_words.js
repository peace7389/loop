// The words that need explaining: a setting, a measure, a part of the network. Wherever one stands on a session's
// page (in the AI's own words, in the page's lines, in a table) it gets a dotted line under it, and its first occurrence
// in a card, a row or a claim is set a little heavier. Pointing at it, or reaching it with the Tab key, opens a small
// box beside it; nothing else changes and the page does not move (scrolled, the box follows its word). The text itself is never changed: the AI wrote
// "weightUdp", and "weightUdp" stays; the box says what it is.
// A word is found by a fixed list, not by guessing:
//   a setting   its field name (weightUdp), and its plain name where that is more than one word ("queue length");
//               the short plain names ("ratio", "seed", "measured time") only where the page itself wrote a setting's
//               values (data-exact)
//   a measure   its field name (udp_loss_frac) and its plain name ("UDP loss")
//   a part      the names of the picture's objects that are one of a kind: UDP queue, TCP queue, scheduler, UDP source,
//               TCP source
// What the box shows is taken from what is recorded, nothing is written for it:
//   a setting   the brief's own line about it (the words the AI was given), its range and where the session started,
//               or that the operator fixed it and at what; the values this session tried, by the replay's step
//   a measure   the harness's line about it (the words the AI was given), its unit, its value in the baseline, what the
//               brief's goal says about it, and where in the picture it is measured
//   a part      its card from "The setting" (EV.objCard): where it sits, what it is set to, who may change that; the
//               scheduling policy stays operator-only there as everywhere
// A hypothesis has a box of the same kind (key "h:<id>", EV.hypPop in evidence_find.js): pointing at its box on the board,
// or at its name in the table under it, opens its card.
// A brief's name has one too (key "b:<id>"): what it asks, the task in the operator's words, how many settings it opens.
// The labels and terms the page already explains on hover (EV.label, EV.term) open the same box instead of the
// browser's own tooltip; their title stays in the page for a reader who cannot point.
// The picture and the words belong together: pointing at a part of the picture in "The setting" sets off, everywhere on
// the page, the settings that part is set by and the measures taken there (the link: link rate, link delay, link use);
// pointing at a marked word sets off the parts of the picture where it is set or measured. Which settings and measures
// belong to a part is what objects.json records for it (the settings its rows show, its "measured" list); nothing is guessed.
// ======================================================================================================
Object.assign(EV, {
  WD_PARTS: [['UDP queue', 'sender', 'tc'], ['TCP queue', 'sender', 'tc'], ['Scheduler', 'sender', 'tc'], ['UDP source', 'sender', 'apps'], ['TCP source', 'sender', 'apps']],
  WD_IN: '#s-system, #s-made, #s-find, #s-notebook, #s-proposes, #s-research, #p-detail',  // where words are marked
  WD_SKIP: 'svg, script, style, textarea, select, option, input, abbr, .wd, .wd-pop, button:not(.chip), .review, [data-nowd]',
  // the list of this session: name (lower case) -> key; and the two patterns (everywhere; where the page wrote a setting's values)
  wdList() {
    const M = EV.M; if (M._wd) return M._wd; const b = M.brief || {}, given = (M.meta && M.meta.given) || {}, names = {}, short = {}, add = (o, n, k) => { if (n && !(String(n).toLowerCase() in o)) o[String(n).toLowerCase()] = k; };
    Object.keys({ ...(b.system || {}), ...(b.knobs || {}) }).forEach(k => { const plain = EV.LABEL[k]; if (/[A-Z_]/.test(k)) add(names, k, 'k:' + k); else add(short, k, 'k:' + k); if (plain && plain.includes(' ') && plain !== 'measured time') add(names, plain, 'k:' + k); else add(short, plain, 'k:' + k); });
    Object.keys({ ...TH_DATA.PLAIN, ...(given.outputs || {}) }).forEach(k => { add(names, k, 'm:' + k); if (!['link_rate_bps', 'weight_udp'].includes(k)) add(names, TH_DATA.PLAIN[k], 'm:' + k); });
    EV.WD_PARTS.forEach(([n]) => add(names, n, 'o:' + n));
    const re = o => { const all = Object.keys(o).sort((p, q) => q.length - p.length).map(n => n.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')); return all.length ? new RegExp(`(?<![A-Za-z0-9_])(${all.join('|')})(?![A-Za-z0-9_])`, 'gi') : null; };
    return (M._wd = { names, both: { ...short, ...names }, re: re(names), reExact: re({ ...short, ...names }) });
  },
  // after the page is drawn: the words of the list are wrapped where they stand; the text is the same before and after
  wordsMark() {
    document.querySelectorAll('#s-system .sy-det.on td, #s-system .sy-det.on > p').forEach(el => { if (!el.title && el.scrollWidth > el.clientWidth) el.title = el.textContent.replace(/\s+/g, ' ').trim(); });  // a row shortened to one line: in full on hover
    const M = EV.M, root = document.getElementById('ev'); if (!M || !root || EV.wordsOff) return; const W = EV.wdList(); if (!W.re) return;
    root.querySelectorAll(EV.WD_IN).forEach(box => {
      const tw = document.createTreeWalker(box, NodeFilter.SHOW_TEXT, { acceptNode: n => (n.nodeValue.length < 3 || !n.parentElement || n.parentElement.closest(EV.WD_SKIP) ? NodeFilter.FILTER_REJECT : NodeFilter.FILTER_ACCEPT) }), nodes = [], first = new Map();
      while (tw.nextNode()) nodes.push(tw.currentNode);
      nodes.forEach(n => { const exact = !!n.parentElement.closest('[data-exact]'), re = exact ? W.reExact : W.re, text = n.nodeValue; re.lastIndex = 0; let m, at = 0, frag = null;
        while ((m = re.exec(text))) { const key = W.both[m[1].toLowerCase()]; if (!key) continue; frag = frag || document.createDocumentFragment();
          if (m.index > at) frag.appendChild(document.createTextNode(text.slice(at, m.index)));
          const s = document.createElement('span'), block = n.parentElement.closest('.nb-card, tr, button.chip, .pr-b, li, p, .nb-head') || box, seen = first.get(block) || first.set(block, new Set()).get(block);
          s.className = 'wd'; s.dataset.wd = key; s.textContent = m[1]; if (!seen.has(key)) { seen.add(key); s.classList.add('wd1'); s.tabIndex = 0; }
          frag.appendChild(s); at = m.index + m[1].length; }
        if (frag) { if (at < text.length) frag.appendChild(document.createTextNode(text.slice(at))); n.parentNode.replaceChild(frag, n); } });
      // what the page already explains on hover: the same box
      box.querySelectorAll('abbr[title]').forEach(a => { const t = a.title, f = /\(field: (\w+)\)\s*$/.exec(t), mm = /^(\w+): /.exec(t), d = Object.keys(EV_DEF).find(k => EV_DEF[k] === t);
        const key = f && ('k:' + f[1]) in EV.wdKeys(W) ? 'k:' + f[1] : mm && ('m:' + mm[1]) in EV.wdKeys(W) ? 'm:' + mm[1] : d ? 'd:' + d : null; if (key) a.dataset.wd = key; });
    });
  },
  wdKeys(W) { return W.keys || (W.keys = Object.fromEntries(Object.values(W.both).map(k => [k, 1]))); },
  // ---- a brief: its name is a file name and says little. What it asks, in a few words built from its goal ('' where it has none; null
  // while its file is on its way): shown beside the name on Home, in the lists of briefs, and in its box
  briefFile(id) { const M = EV.M; return M && M.brief && M.brief.id === id ? M.brief : EV.briefOf(id); },
  briefSays(id) { const b = EV.briefFile(id), g = b && b.goal; return b === undefined ? null : !g ? '' : g.kind === 'open' ? 'the AI chooses its own aim' : g.kind === 'given' ? `find ${EV.aimWords(g)}` : ''; },
  briefSaysPlain(id) { return String(EV.briefSays(id) || '').replace(/<[^>]+>/g, ''); },
  briefName(id) { return id ? `<span class="wd" data-wd="b:${EV.e(id)}" tabindex="0">${EV.e(id)}</span>` : 'before briefs'; },
  // A brief's box, in the looks of every box: its name with "brief" on a chip; the facts as grey labels with their values (the aim; where the aim is open and
  // this session's final report is recorded, the aim the AI chose, in its own words; how many settings the AI may change, how many are fixed, the limit); then,
  // behind a bar, the task as the AI was given it.
  briefPop(id) {
    const e = EV.e, b = EV.briefFile(id), head = `<p class="wd-h"><b>${e(id)}</b><span class="wd-kind">brief</span></p>`; if (!b) return `${head}<p class="sm">${b === undefined ? 'reading its file…' : 'Its file cannot be read here.'}</p>`;
    const says = EV.briefSays(id), kn = Object.keys(b.knobs || {}).length, fx = Object.keys(b.system || {}).length, lim = b.limits || {}, pl = (n, w) => `${n} ${w}${n === 1 ? '' : 's'}`;
    // an open aim, in the session that is open: the aim the AI chose, once its final report is recorded (at an earlier step of the replay it is not there)
    const M = EV.M, mine = M && M.brief && M.brief.id === id && EV.s.view === 'session' && (b.goal || {}).kind === 'open', rep = mine && EV.repNow ? EV.repNow() : null, chose = rep && rep.goal ? (Array.isArray(rep.goal) ? rep.goal.join(' · ') : String(rep.goal)) : '';
    const rows = [says ? [`${EV.flag()}The aim`, `<span data-bp="says">${says[0].toUpperCase() + says.slice(1)}</span>`] : null,
      chose ? [`<span class="st-by" data-by="model"><i class="sw"></i>The AI chose</span>`, `<span class="bp-chose" data-own="model" data-bp="chose">${e(chose)}</span><span class="bp-when" data-bp="when">stated at the end of session ${e(M.id)}, in its final report${M.repRec ? ` (turn ${e(M.repRec.turn)})` : ''}: the harness asks for the aim only there</span>`] : null,
      ['The AI may change', `<span data-bp="counts" data-knobs="${kn}" data-fixed="${fx}">${pl(kn, 'setting')}</span>`], ['Fixed by the operator', pl(fx, 'setting')], lim.simulations != null ? ['Limit', `${e(lim.simulations)} simulations`] : null].filter(Boolean);
    return `${head}<dl class="wd-kv">${rows.map(([k, v]) => `<dt>${k}</dt><dd>${v}</dd>`).join('')}</dl>
      <div class="wd-told"><p class="wd-src"><span class="st-by" data-by="operator"><i class="sw"></i>The task</span>, as the AI was given it</p><blockquote class="wd-q bp-task" data-own="operator" data-bp="task">${e(b.task || '')}</blockquote></div>`;
  },
  // ---- an experiment (one batch of simulations run together), pointed at in the glance or in the notebook: which turn, what it was for (the hypotheses it
  // tests, or the question it explores, or that it is the harness's baseline), its simulations in words built from their settings, how many were not run
  // again, how long they took, and how each test's check ended. Only what is recorded by the step the page is at.
  expPop(id) {
    const M = EV.M, e = EV.e, x = M.expById[id]; if (!x) return ''; const seen = EV.seen, sims = x.sims.filter(q => seen(q.id)), tests = M.tests.filter(T => T.exp === id), base = x.by === 'harness' || id === 'X0';
    const ev = M.recs.find(r => r.type === 'evidence' && r.parent === id && seen(r.id)), xr = M.recs.find(r => r.id === id), took = ev && xr && ev.ts && xr.ts ? Math.round((new Date(ev.ts) - new Date(xr.ts)) / 1000) : null;
    const designs = sims.length ? sims : (x.runs || []).map(r => ({ params: r.params || {} })), plan = designs.length ? EV.nbPlan1({ exp: id, sims: designs, labels: [], rule: 'x' }) : '', back = sims.filter(q => q.same_as).length;
    const hypQ = h => { const o = M.hyps.find(q => q.id === h); return o ? o.question || o.text || '' : ''; };
    const how = T => { const c = T.check && seen(T.check.id) ? T.check : null; return !T.rule ? 'no decision rule: nothing to check' : !c ? (sims.length ? 'not checked yet' : 'waits for its simulations') : c.void ? 'its check is void' : c.result === 'held' ? `${EV.res('held', 'its check held')}` : c.result === 'failed' ? `${EV.res('failed', 'its check failed')}` : e(c.result || 'not checked'); };
    return `<p class="wd-h"><b>Experiment ${e(id)}</b> <span class="sm">${base ? 'the harness’s baseline' : 'one batch of simulations, run together'}${x.turn ? ` · turn ${e(x.turn)}` : ''}</span></p>
      ${base ? '<p>Run by the harness before the AI’s first turn, with every setting at its default: the starting point every later result is compared with.</p>' : tests.length ? `<p class="sm" style="margin-bottom:2px">it tests</p>${tests.map(T => `<p data-xp="test" style="margin:0 0 3px"><b>${e(T.hyp)}</b> <span data-own="model">${e(hypQ(T.hyp))}</span> <span class="sm">· ${how(T)}</span></p>`).join('')}` : `<p class="wd-lead">An exploration: simulations run to look, with no hypothesis and no decision rule stated first, so the harness has nothing to check.</p><div class="wd-told"><p class="wd-src"><span class="st-by" data-by="model"><i class="sw"></i>What it wanted to find out</span>, in the AI’s words</p><blockquote class="wd-q" data-own="model">${e(x.question || 'not recorded')}</blockquote></div>`}
      <p data-xp="sims"${sims.length ? '' : ' class="mut"'}>${plan}${sims.length ? '' : ' · not back yet'}</p>
      ${!tests.length && !base && sims.length && sims.length <= 3 ? `<dl class="wd-kv" data-xp="found">${sims.filter(q => q.metrics).map(q => `<dt>${e(q.label || q.id)} measured</dt><dd>UDP <b>${EV.v4('udp_goodput_bps', q.metrics.udp_goodput_bps)}</b> · TCP <b>${EV.v4('tcp_goodput_bps', q.metrics.tcp_goodput_bps)}</b> · UDP loss <b>${EV.v4('udp_loss_frac', q.metrics.udp_loss_frac)}</b></dd>`).join('')}</dl>` : ''}
      ${(cl => (cl.length ? `<p class="sm" data-xp="cited">Its results are cited by ${cl.map(q => 'claim ' + q.n).join(', ')} of the final report.</p>` : ''))(EV.repNow() ? M.claims.filter(q => (q.exps || []).includes(id) && !(q.tests || []).length) : [])}
      ${back ? `<p class="sm" data-xp="back">${back} of them ${back === 1 ? 'has' : 'have'} the settings and seed of an earlier simulation: ${back === 1 ? 'it was' : 'they were'} not run again, the earlier result${back === 1 ? ' was' : 's were'} returned and did not count against the limit.</p>` : ''}
      <p class="sm">${took != null ? `its results came back ${took} s after it was set up · ` : ''}click to open it: each simulation with its settings and measures</p>`;
  },
  // ---- what the box says, by key
  wdBody(key) {
    if (key[0] === 'b') return EV.briefPop(key.slice(2));
    // an item of the legend (the legend stands on every page, also where no session is open): its name, the group on a chip, what it means, where it is seen
    if (key[0] === 'l') { const s = EV.LEGEND_SAYS[key.slice(2)], x = EV.e; return s ? `<p class="wd-h"><b>${x(s[0])}</b><span class="wd-kind">${x(s[1])}</span></p><p class="wd-lead">${x(s[2])}</p>${s[3] ? `<dl class="wd-kv"><dt>Seen as</dt><dd data-lg="where">${x(s[3])}</dd></dl>` : ''}` : ''; }
    // A box reads from top to bottom, and each kind of thing in it has a look of its own: the name, with its kind on a chip; one or two plain sentences that
    // say what it is (the page's words, the largest text under the name); the facts as small grey labels with their values; then, smaller and behind a bar, the
    // line the AI was given, with whose line it is; last, under a rule, the field's name.
    const M = EV.M, e = EV.e, b = M.brief || {}, given = (M.meta && M.meta.given) || {}, [kind, name] = [key[0], key.slice(2)], head = (title, what) => `<p class="wd-h"><b>${e(title)}</b><span class="wd-kind">${what}</span></p>`;
    const lead = (text, own) => { const t = String(text || '').trim(); return t ? `<p class="wd-lead"${own ? ' data-wd-says="1"' : ''}>${e(t[0].toUpperCase() + t.slice(1))}${/[.!?]$/.test(t) ? '' : '.'}</p>` : ''; };
    const quote = (text, by, whose) => `<div class="wd-told"><p class="wd-src"><span class="st-by" data-by="${by}"><i class="sw"></i>${whose}</span>, as the AI was given it</p><blockquote class="wd-q" data-own="${by}" data-wd-says="1">${e(text)}</blockquote></div>`;
    const facts = rows => { const r = rows.filter(Boolean); return r.length ? `<dl class="wd-kv">${r.map(([k, v]) => `<dt>${k}</dt><dd>${v}</dd>`).join('')}</dl>` : ''; }, foot = field => `<p class="wd-foot">its name in the records: <code>${e(field)}</code></p>`;
    if (kind === 'v') { const [value, what, measure, where, state, rule, measured] = name.split('¦'), sign = t => (state ? EV.res(state === 'held' ? 'held' : 'failed', t) : e(t));
      // a mark of a rule's bar. The value, large, with what it is on a chip; then each thing under its own name: the measure, the simulation, the rule, and
      // (for a threshold) what was measured. The sign of held or failed stands with the rule on the measured point, with the measured value on a threshold.
      return `<p class="vp-v" data-wd-value="1"><b>${e(value || '')}</b><span class="wd-kind">${e(what || '')}</span></p>${facts([measure ? ['Measure', `<span data-vp="measure">${e(measure)}</span>`] : null, where ? [/^from \d+ simulations$/.test(where) ? 'Simulations' : 'Simulation', `<span data-vp="where">${e(where.replace(/^(at|from) /, ''))}</span>`] : null,
        rule ? ['Rule', `<span data-vp="rule" data-state="${e(state)}">${measured ? e(rule) : sign(rule)}</span>`] : null, measured ? ['Measured', `<span data-vp="measured">${sign(measured)}</span>`] : null])}`; }
    if (kind === 'r') { const r = M.byId[name]; if (!r || !EV.seen(name)) return ''; const L = (/^[A-Z]+/.exec(name) || [''])[0], s = EV.ID_SAYS[L] || [r.type, '', ''], rb = r.body || {}, who = { model: 'the AI', harness: 'the harness', simulator: 'ns-3' }[s[2]];
      // a record named by a letter and a number (a note, a request, a tool's result, a turn's record, a result table): what the letter stands for, who wrote it, when, and what it says
      const n = (rb.lines || []).length, txt = r.type === 'note' ? (rb.part ? `It refused the part “${rb.part}” of the AI’s answer: ${rb.reason || rb.text || 'no reason recorded'}` : rb.text || rb.reason || rb.error || '')
        : r.type === 'request' ? `${rb.tool || 'a tool'}${rb.args ? ' ' + JSON.stringify(rb.args) : ''}` : r.type === 'evidence' ? `${n} line${n === 1 ? '' : 's'}, one for each simulation of ${rb.experiment || r.parent || 'its experiment'}` : r.type === 'turn' ? `${rb.simulations_left ?? 'not recorded'} simulations left, ${rb.open_hypotheses ?? 'not recorded'} open hypotheses` : '';
      return `${head(name, s[0])}${lead(s[1], false)}${facts([['Its name', `<span data-rp="name"><b>${e(L)}</b> for ${e(s[0])}, number <b>${e(name.slice(L.length))}</b> of this session</span>`], who ? ['Written by', `<span class="st-by" data-by="${s[2]}"><i class="sw"></i>${who}</span>`] : null, r.turn != null ? ['When', r.turn ? `turn ${e(r.turn)}` : 'before the first turn'] : null, txt ? ['It says', `<span class="lc4" data-rp="says">${e(txt)}</span>`] : null])}`; }
    if (kind === 'z') {  // "N not accepted" on a turn: what that means, and each part the harness left out with its reason
      const t = M.turns.find(q => String(q.n) === name); if (!t) return '';
      const rows = [...t.malformed.filter(m => EV.seen(m.id)).map(m => [(m.body.refused || []).map(q => q.part).join(', ') || 'the whole answer', (m.body.refused || []).map(q => q.reason).join(' · ') || m.body.error || 'it could not be read']),
        ...t.refusals.filter(m => EV.seen(m.id)).map(m => [m.body.part, m.body.reason || m.body.text || 'no reason recorded'])], by = {};
      rows.forEach(([part, why]) => { const k = part + '¦' + why; by[k] = (by[k] || 0) + 1; });
      return `${head(`${rows.length} not accepted`, 'turn ' + e(name))}${lead('The harness checks each part of the AI’s answer before it uses it: a guess of why, a hypothesis, an experiment, a verdict. A part that breaks a rule of the work is left out, and the rest of the answer is used')}
        <p class="sm">The AI is told the reason and can do that part again in its next answer. This is about the form of an answer; it is not a judgement of a hypothesis (“refuted”).</p>
        ${facts(Object.entries(by).slice(0, 6).map(([k, n]) => { const [part, why] = k.split('¦'); return [`${e(part)}${n > 1 ? ' ×' + n : ''}`, `<span data-zp="why">${e(why.length > 230 ? why.slice(0, 228) + '…' : why)}</span>`]; }))}${Object.keys(by).length > 6 ? `<p class="sm">and ${Object.keys(by).length - 6} more kinds: open the turn to read them all</p>` : ''}`; }
    if (kind === 'y') return EV.whyPop(name);    // a guess of why: what became of it, its hypotheses, the claims that rest on those
    if (kind === 'c') return EV.claimPop(name);  // a claim of the final report: the hypotheses it rests on and the guesses behind them
    if (kind === 'x') return EV.expPop(name);  // an experiment: what it was for, its simulations, what came of it
    if (kind === 'h') return EV.hypPop(name);
    if (kind === 'f') return EV.fndPop ? EV.fndPop(name) : '';   // a finding's bar (evidence_findings.js)  // a hypothesis: its card (evidence_find.js)
    if (kind === 'n') return EV.namePop(name);  // a simulation's name: what its parts mean, read against the experiment's designs
    if (kind === 't') return EV.testPop(name);  // a test, on the glance's "H1 held": expected against found
    if (kind === 'j') return EV.verdictPop(name);  // a verdict, on the glance's "H1 supported": the AI's judgement and its reason
    if (kind === 'a') return EV.answerPop();  // the answer, the last box of the board: its proposal and its reasons
    if (kind === 'e') return EV.edgePop(name);  // an arrow of the board: the result that led onward
    if (kind === 'd') return `${head(name, 'word of this page')}${lead(EV_DEF[name], false)}`;
    if (kind === 'o') { const p = EV.WD_PARTS.find(q => q[0] === name), id = p && EV.OB ? EV.sysId(p[1], p[2], p[0]) : null; return id ? `<div class="wd-obj">${EV.objCard(id)}</div><p class="sm">from the picture in “The setting”</p>` : `${head(name, 'part of the network')}<p class="sm">Its settings are in the picture of “The setting”.</p>`; }
    if (kind === 'k') { const kn = (b.knobs || {})[name], fixed = (b.system || {})[name], plain = EV.LABEL[name] || name;
      const vs = [...new Set(M.sims.filter(q => EV.seen(q.id) && q.params && q.params[name] != null && (M.expById[q.exp] || {}).by !== 'harness').map(q => q.params[name]))], num = vs.length > 0 && vs.every(x => typeof x === 'number');
      const tried = !vs.length ? null : ['Tried here', `<span data-wd-tried="${vs.length}" data-exact="1">${vs.length === 1 ? 'one value: ' + e(EV.setVal(name, vs[0])) : num ? `${vs.length} values, from ${e(EV.setVal(name, Math.min(...vs)))} to ${e(EV.setVal(name, Math.max(...vs)))}` : `${vs.length} values: ${e(vs.map(v => EV.setVal(name, v)).join(', '))}`}</span>`];
      return `${head(plain, 'setting')}${lead(EV.SET_SAYS[name], !(kn && kn.meaning))}
        ${kn ? facts([['Decided by', '<span class="st-by" data-by="model"><i class="sw"></i>the AI may change it</span>'], ['Range', `<span data-wd-range="1" data-exact="1">${e(EV.setRange(name, kn))}</span>`], ['Started from', `<b data-wd-default="1" data-exact="1">${e(EV.setVal(name, kn.default))}</b>`], tried])
          : fixed !== undefined ? facts([['Decided by', '<span class="st-by" data-by="operator"><i class="sw"></i>fixed by the operator</span>'], ['Value', `<b data-wd-fixed="1" data-exact="1">${e(EV.setVal(name, fixed))}</b>`]]) : ''}
        ${name === 'tcpVariant' ? EV.tcpList(kn ? kn.choices || [kn.default] : fixed !== undefined ? [fixed] : []) : ''}${kn && kn.meaning ? quote(kn.meaning, 'operator', 'The brief’s line') : ''}${foot(name)}`; }
    // a measure
    const says = (given.outputs || {})[name], s0 = M.simById.S0 && EV.seen('S0') ? M.simById.S0 : null, g = b.goal || {}, cond = (g.conditions || []).find(c => new RegExp('^\\s*' + name + '\\b').test(c)), unit = /_bps$/.test(name) ? ['Mbps or Gbps', 'recorded in bits per second'] : ['udp_loss_frac', 'link_util'].includes(name) ? ['% (per cent)', 'recorded as a fraction of 1'] : /^drops_/.test(name) ? ['packets', 'a count'] : /retrans/.test(name) ? ['segments', 'a count'] : name === 'weight_udp' ? ['none', 'a share between 0 and 1'] : null;
    const where = EV.OB ? [EV.OB.channel, ...EV.OB.hosts.flatMap(h => ['apps', 'stack', 'tc', 'dev'].flatMap(l => (h[l] || []).map(o => ({ ...o, host: h.title }))))].find(o => (o.measured || []).includes(name)) : null;
    return `${head(TH_DATA.PLAIN[name] || name, 'measure')}${lead(EV.MEASURE_SAYS[name] || (EV.NET_SAYS || {})[name], false)}
      ${facts([s0 && s0.metrics && s0.metrics[name] != null ? ['In the baseline', `<b data-wd-base="1">${EV.v4(name, s0.metrics[name])}</b>`] : null, unit ? ['Unit', `<span data-wd-unit="1">${e(unit[0])}</span> <span class="sm">· ${e(unit[1])}</span>`] : null, where ? ['Measured at', `${e(where.name)}${where.host ? ', ' + e(where.host.toLowerCase()) : ''}`] : null,
        g.kind === 'given' && g.target && g.target.measure === name ? ['<span class="st-by" data-by="operator"><i class="sw"></i>The brief’s target</span>', `<span data-wd-goal="target">the ${g.target.direction === 'min' ? 'smallest' : 'largest'} is wanted</span>`] : null,
        cond ? ['<span class="st-by" data-by="operator"><i class="sw"></i>The brief’s condition</span>', `<span data-wd-goal="condition">${(m => (m ? `${EV.READ_WORDS[m[1]]} ${e(EV.readNum(Number(m[2]), name, 0))}` : EV.readHtml(cond) || e(cond)))(/^\s*\w+\s*(<=|>=|<|>|==)\s*([-\d.eE]+)\s*$/.exec(cond))}</span>`] : null])}${says ? quote(says, 'harness', 'The harness’s line') : ''}${foot(name)}`;
  },
  // ---- the picture and the words. The keys of a part: the settings its rows show (as this session's brief names them) and its measures
  wdOfPart(id) {
    const f = EV.OB && EV.sysFind(id), b = (EV.M && EV.M.brief) || {}; if (!f) return [];
    const V = EV.sysVals(), names = f.o.rows.flatMap(([, text]) => [...String(text).matchAll(/\{(\w+)\}/g)].map(m => V.key(m[1])));
    return [...new Set([...names.filter(k => k in (b.knobs || {}) || k in (b.system || {})).map(k => 'k:' + k), ...(f.o.measured || []).map(k => 'm:' + k)])];
  },
  wdParts() {  // every part of the picture: its id and its keys (read once per session)
    const M = EV.M, O = EV.OB; if (!O || !M) return []; if (M._parts) return M._parts;
    const ids = ['link', ...O.hosts.flatMap(h => O.layers.flatMap(l => (h[l.key] || []).map((o, i) => `${h.key}-${l.key}-${i}`)))];
    return (M._parts = ids.map(id => ({ id, keys: EV.wdOfPart(id) })).filter(q => q.keys.length));
  },
  wdLinkOff() { document.querySelectorAll('#ev .wd-hot, #ev .wd-hot-row, #ev .ohot').forEach(el => el.classList.remove('wd-hot', 'wd-hot-row', 'ohot')); },
  // a part of the picture is pointed at: its settings and measures are set off wherever they stand
  wdLinkPart(id) {
    EV.wdLinkOff(); const keys = new Set(EV.wdOfPart(id)); if (!keys.size) return;
    document.querySelectorAll('#ev [data-wd]:not(.wd-pop)').forEach(el => { if (!keys.has(el.dataset.wd)) return; el.classList.add('wd-hot'); const row = el.closest('#s-system tr'); if (row) row.classList.add('wd-hot-row'); });
  },
  // a marked word is pointed at: the parts of the picture where it is set or measured are set off
  wdLinkWord(key) { EV.wdLinkOff(); EV.wdParts().filter(q => q.keys.includes(key)).forEach(q => { const g = [...document.querySelectorAll('#s-system svg.sy g[data-id]')].find(el => el.dataset.id === q.id); if (g) g.classList.add('ohot'); }); },
  // ---- the box: one for the page, shown beside the word that is pointed at or has the keyboard's focus
  wdShow(el) {
    const root = document.getElementById('ev'); EV.wdHide(); if (!el.isConnected || (!EV.M && el.dataset.wd[0] !== 'b')) return;
    const pop = document.createElement('div'); pop.id = 'wd-pop'; pop.className = 'wd-pop'; pop.setAttribute('role', 'tooltip'); pop.dataset.wd = el.dataset.wd; pop.dataset.kind = 'eatj'.includes(el.dataset.wd[0]) ? 'h' : el.dataset.wd[0]; pop.innerHTML = EV.wdBody(el.dataset.wd); if (!pop.innerHTML.trim()) return; root.appendChild(pop);
    // the browser's own tooltip of the word and of what it stands in is held back while the box is open
    EV._wdTitles = []; for (let a = el; a && a !== root; a = a.parentElement) if (a.title) { EV._wdTitles.push([a, a.title]); a.removeAttribute('title'); }
    EV._wdEl = el; EV.wdPlace();
  },
  // beside its word: below it where there is room, else above; when the page is scrolled the box follows its word, and goes once the word has left the window
  wdPlace() {
    const el = EV._wdEl, pop = document.getElementById('wd-pop'); if (!el || !pop) return; const r = el.getBoundingClientRect(); if (r.bottom < 0 || r.top > innerHeight) return EV.wdHide();
    const w = pop.offsetWidth, h = pop.offsetHeight, below = r.bottom + 6 + h <= innerHeight || r.top - 6 - h < 0;
    // a box too tall to stand under its word or over it stands beside it (to the right where there is room, else to the left), so that it never lies over what it explains
    if (r.bottom + 6 + h > innerHeight && r.top - 6 - h < 0) { const right = r.right + 8 + w <= innerWidth, left = r.left - 8 - w >= 0;
      if (right || left) { pop.style.left = (right ? r.right + 8 : r.left - 8 - w) + 'px'; pop.style.top = Math.max(4, Math.min(r.top, innerHeight - h - 4)) + 'px'; return; } }
    pop.style.left = Math.max(8, Math.min(r.left, innerWidth - w - 8)) + 'px'; pop.style.top = Math.max(4, below ? Math.min(r.bottom + 6, innerHeight - h - 4) : r.top - 6 - h) + 'px';
  },
  wdHide() { clearTimeout(EV._wdT); const pop = document.getElementById('wd-pop'); if (pop) pop.remove(); (EV._wdTitles || []).forEach(([a, t]) => { if (a.isConnected && !a.title) a.title = t; }); EV._wdTitles = []; EV._wdEl = null; },
});
(() => { const root = document.getElementById('ev'), of = ev => (ev.target.closest ? ev.target.closest('[data-wd]:not(.wd-pop)') : null);
  const part = ev => (ev.target.closest ? ev.target.closest('#s-system svg.sy g[data-id]') : null);
  root.addEventListener('mouseover', ev => { const g = part(ev); if (g) { if (EV._wdPart !== g.dataset.id) { EV._wdPart = g.dataset.id; EV.wdLinkPart(g.dataset.id); } return; }
    const el = of(ev); if (!el || el === EV._wdEl) return; if (EV._wdKey !== el.dataset.wd) { EV._wdKey = el.dataset.wd; EV.wdLinkWord(el.dataset.wd); } clearTimeout(EV._wdT); EV._wdT = setTimeout(() => EV.wdShow(el), 140); });
  root.addEventListener('mouseout', ev => { const g = part(ev); if (g && !(ev.relatedTarget && g.contains(ev.relatedTarget))) { EV._wdPart = null; EV.wdLinkOff(); }
    const el = of(ev); if (el && !(ev.relatedTarget && el.contains(ev.relatedTarget))) { EV._wdKey = null; EV.wdLinkOff(); EV.wdHide(); } });
  root.addEventListener('focusin', ev => { const el = of(ev); if (el) EV.wdShow(el); });
  root.addEventListener('focusout', ev => { if (of(ev)) EV.wdHide(); });
  document.addEventListener('keydown', ev => { if (ev.key === 'Escape') EV.wdHide(); });
  window.addEventListener('scroll', () => EV.wdPlace(), { passive: true });
})();
