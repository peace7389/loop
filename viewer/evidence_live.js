// A session that is running, shown as it is made. The page already holds the skeleton of a session: the rows of "The
// session at a glance", the columns of "What it needed to find out", the six lines of a notebook card, the six parts of
// "What it proposes", the lines of "How it worked as a researcher". This file adds what a running session needs:
//   the empty places   a place whose record is not there yet is drawn as an empty place (a dashed square, or the word
//                      "empty"), and fills with its record when the record arrives. A place that is never filled stays
//                      drawn empty after the session ended ("no verdict was given").
//   where the work is  one sentence in the banner, which stays at the top of the window, and a mark on the places the
//                      work can fill next. It is read from the records alone (EV.liveNow), by this rule:
//                        no record yet                                   the harness is preparing the session
//                        an experiment without its results               the simulator is working on its simulations
//                        the newest record is a turn's first record      the AI is writing its reply
//                        anything else                                   the harness is preparing the next turn
//                      The AI's reply arrives whole, so while it is written the page cannot know which place it will
//                      fill: the mark then stands on every place that reply may fill, and the sentence says so.
//   the stage          in "What it needed to find out" a strip of the steps of a turn (the AI writes its reply, the simulator
//                      runs its simulations, the harness checks each decision rule, the next turn), the one being worked
//                      on with its moving icon and the time; before the first question exists the section shows only that
//   the time           how long the newest record has been the newest: the server's own clock (the Date header of its
//                      answer) against the time the ledger was last written (Last-Modified), counted on from there.
//   what just arrived  the records that were not there at the last reading are marked for a short while.
//   the simulations    while an experiment's simulations run, the sentence also says how many of them the harness has
//                      collected so far: the runs its index (runs/index.json) lists that no record holds yet
//   the tiles          one tile per simulation of the experiment that is being run, read from the simulator's own files
//                      (evidence_tiles.js)
//   the quick reading  every two seconds the size of the ledger is asked for (a HEAD request); the session is read
//                      again only when it has grown. The form of a turn is the harness's, told to the AI in its prompt;
//                      what fills it, how many turns there are and when it stops are the AI's.
// Nothing here is written by a model, and no draft is read: of a draft record only its type is looked at, to say
// that a reply was asked for a second time.
// ======================================================================================================
Object.assign(EV, {
  live: { seen: {}, ran: {}, fresh: null, head: null, tries: 0, busy: false, turnOf: {}, expOf: {}, note: null, keepUntil: 0 },
  // the ledger, with the two times the server sends with it
  async liveGet(url) {
    if (EV.off) return EV.get(url);
    try { const r = await fetch(url + '?t=' + Date.now(), { cache: 'no-store' }); if (!r.ok) return null; const text = await r.text(), H = k => r.headers.get(k);
      EV.live.head = { url, len: H('Content-Length'), age: H('Date') && H('Last-Modified') ? Math.max(0, new Date(H('Date')) - new Date(H('Last-Modified'))) : null, at: performance.now() }; return text; } catch (x) { return null; }
  },
  // after a session is read: which records are new since the last reading, and whether its newest turn was asked twice
  liveLoaded(text) {
    const L = EV.live, M = EV.M, sid = M.id, row = EV.files.row || {}, ids = M.recs.map(r => r.id), old = L.seen[sid];
    if (row.running) L.ran[sid] = true;
    if (old && L.ran[sid]) { const add = ids.filter(id => !old.has(id)); if (add.length) L.fresh = { sid, ids: new Set(add), steps: new Set(add.map(id => M.recStep[id])), at: performance.now() }; }
    if (L.fresh && L.fresh.sid !== sid) L.fresh = null;
    L.seen[sid] = new Set(ids); L.tries = 0;
    const lines = String(text || '').split('\n'); for (let i = lines.length - 1; i >= 0; i--) { const m = /"type": ?"(\w+)"/.exec(lines[i]); if (!m) continue; if (m[1] === 'turn') break; if (m[1] === 'draft') L.tries++; }
  },
  // where the work of a running session is; null: not running, ended, or the replay is at an earlier step
  liveNow() {
    const M = EV.M, row = (EV.files && EV.files.row) || {}; if (!M || !row.running || M.ended || EV.s.step != null || EV.off) return null;
    const recs = M.recs, last = recs[recs.length - 1]; if (!last) return { phase: 'start', turn: 0 };
    const x = recs.filter(r => r.type === 'experiment').pop(), open = x && !recs.some(r => r.type === 'evidence' && r.parent === x.id);
    if (open) return { phase: x.by === 'harness' || x.id === 'X0' ? 'baseline' : 'sims', turn: x.turn, exp: x.id, n: (x.body.runs || []).length };
    if (last.type === 'turn') return { phase: 'reply', turn: last.turn, mode: last.body.last_turn || null, again: EV.live.tries > 0 };
    return { phase: 'between', turn: last.turn };
  },
  // the simulations of the experiment that is being run which the harness has collected so far: the runs its index lists that no record holds yet
  // (the harness reads its simulations in the order it started them, so this is how many are in, not how many have ended)
  liveDone() { const M = EV.M, have = new Set(M.sims.map(s => s.run)); return (EV.files.index || []).filter(q => q && q.id && !have.has(q.id)).length; },
  liveDoneHtml(now) { return now && (now.phase === 'sims' || now.phase === 'baseline') ? ` <span class="sm" id="live-done" data-n="${EV.liveDone()}" data-of="${now.n}">· the harness has collected ${EV.liveDone()} of them so far</span>` : ''; },
  liveClock(ms) { const s = Math.max(0, Math.round(ms / 1000)); return s < 60 ? `${s} s` : `${Math.floor(s / 60)} min ${s % 60} s`; },
  liveAge() { const h = EV.live.head; return h && h.age != null ? h.age + (performance.now() - h.at) : null; },
  liveTimer() { const a = EV.liveAge(); return a == null ? '' : ` <span class="lv-t" data-live-t="1" title="How long the newest record has been the newest, by the server's clock">${EV.liveClock(a)}</span>`; },
  // the sentence that says where the work is
  liveSay(now) {
    const e = EV.e, t = now.turn ? `Turn ${now.turn}: ` : '';
    return now.phase === 'start' ? 'The harness is preparing the session.'
      : now.phase === 'baseline' ? 'The harness is running the baseline simulation, before the AI’s first turn.'
      : now.phase === 'sims' ? `${t}the simulator is working on the ${now.n} simulation${now.n === 1 ? '' : 's'} of experiment ${e(now.exp)}.`
      : now.phase === 'reply' ? `${t}the AI is writing its reply${now.again ? ' again (its first reply could not be used)' : ''}.`
      : `${t}the harness is preparing the next turn.`;
  },
  // the stage of a running session, as a strip of the steps of a turn: the AI writes its reply, ns-3 runs its simulations, the harness checks
  // each decision rule, then the next turn. The step being worked on carries its moving icon and the time. big: where a section has nothing else yet
  liveStage(now, big) {
    // A step that has something to show opens it beside the page (the page does not move): "the AI writes its reply" opens the work log of the turn, which begins
    // with what is happening now (EV.liveNowCard); the simulations and the checks open the turn's experiment once it is recorded. A step that has nothing yet is not a button.
    if (!now) return ''; const x = EV.M.recs.filter(r => r.type === 'experiment' && r.turn === now.turn).pop(), go = { reply: now.turn > 0 ? ['log', now.turn] : null, baseline: x ? ['exp', x.id] : null, sims: x ? ['exp', x.id] : null, checks: x && now.phase === 'between' ? ['exp', x.id] : null };
    const step = (key, by, text, on) => `<span class="lv-step${on ? ' on' : ''}${go[key] ? ' lv-go' : ''}" data-key="${key}" data-by="${by}"${go[key] ? ` data-act="open" data-t="${go[key][0]}" data-id="${EV.e(go[key][1])}" role="button" tabindex="0" title="${key === 'reply' ? 'Open the work log of this turn' : 'Open this experiment'}, beside the page"` : ''}><i class="sw"></i>${text}${on ? EV.liveTimer() : ''}</span>`, to = '<span class="lv-arrow">→</span>', wrap = inner => `<div class="lv-stage${big ? ' big' : ''}" data-phase="${now.phase}">${inner}</div>`;
    if (now.phase === 'start' || now.phase === 'baseline') return wrap(`<span class="lv-turn">Before turn 1</span>${step('baseline', 'harness', now.phase === 'start' ? 'the harness prepares the session' : 'the harness runs the baseline simulation', true)}${to}${step('reply', 'model', 'the AI writes its first reply', false)}`);
    return wrap(`<span class="lv-turn">Turn ${now.turn}</span>${step('reply', 'model', `the AI writes its reply${now.again ? ' again' : ''}`, now.phase === 'reply')}${to}${now.phase === 'reply' && now.mode ? '<span class="lv-step lv-next">the session ends with its final report</span>'
      : `${step('sims', 'simulator', 'ns-3 runs its simulations', now.phase === 'sims')}${to}${step('checks', 'harness', now.phase === 'between' ? 'the harness prepares the next turn' : 'the harness checks each decision rule', now.phase === 'between')}${to}<span class="lv-step lv-next">the next turn</span>`}`);
  },
  // The work log of the turn that is being worked on begins with what is happening now. While the AI writes its reply it says: what the AI was given (the brief,
  // its record so far, and what is new to it since its last reply: the records of that time it did not write itself), which hypotheses wait for its verdict,
  // what the reply may bring, how many simulations are left, how long its earlier replies of this session took (from the times of the records: the turn's
  // first record to the first record of the reply), and that the reply arrives whole. Nothing here is the AI's text, and no draft is read.
  liveNowCard(n) {
    const now = EV.liveNow(), M = EV.M, e = EV.e; if (!now || now.turn !== n) return '';
    const head = (by, text) => `<h3><span class="st-by" data-by="${by}"><i class="sw"></i></span> Now · ${text}${EV.liveTimer()}</h3>`, wrap = (by, text, rows) => `<div class="lg-now" id="lg-now" data-phase="${now.phase}" data-turn="${n}">${head(by, text)}${rows.length ? `<dl class="lg-nkv">${rows.map(([k, v, key]) => `<dt>${k}</dt><dd data-ln="${key}">${v}</dd>`).join('')}</dl>` : ''}</div>`;
    if (now.phase === 'sims') return wrap('simulator', `ns-3 runs the ${now.n} simulation${now.n === 1 ? '' : 's'} of ${EV.link(now.exp)}`, [['Collected so far', `<span data-n="${EV.liveDone()}">${EV.liveDone()} of ${now.n}</span> · the harness checks the decision rules when all are in`, 'done']]);
    if (now.phase !== 'reply') return wrap('harness', 'the harness prepares the next turn', []);
    const t = M.turns.find(q => q.n === n) || {}, added = (t.added || []).map(id => M.byId[id]).filter(Boolean), of = ty => added.filter(r => r.type === ty), pl = (k, w, many) => `${k} ${k === 1 ? w : many || w + 's'}`;
    const ck = of('check'), void_ = ck.filter(c => M.voidIds.has(c.id)).length, held = ck.filter(c => !M.voidIds.has(c.id) && c.body.result === 'held').length, failed = ck.length - void_ - held, notes = of('note'), res = of('result');
    const fresh = [...of('evidence').map(r => `the result table ${EV.link(r.id)} of ${EV.link(r.parent)} (${pl((r.body.lines || []).length, 'simulation')})`),
      ck.length ? `${pl(ck.length, 'check')} of its decision rules: <span data-ck="${held},${failed},${void_}">${[held ? EV.res('held', `${held} held`) : '', failed ? EV.res('failed', `${failed} failed`) : '', void_ ? `${void_} void` : ''].filter(Boolean).join(', ')}</span>` : '',
      res.length ? `${pl(res.length, 'answer')} to what it asked for (${res.map(r => EV.link(r.id)).join(', ')})` : '', notes.length ? `${pl(notes.length, 'note')} of the harness (${notes.slice(0, 4).map(r => EV.link(r.id)).join(', ')}${notes.length > 4 ? ', …' : ''})` : ''].filter(Boolean);
    const wait = M.hyps.filter(h => EV.seen(h.id) && h.state === 'open' && h.tests.some(q => { const c = M.testById[q].check; return c && EV.seen(c.id); }));
    const took = M.turns.filter(q => q.n >= 1 && q.n < n && q.rec).map(q => { const i = M.recs.indexOf(q.rec), nx = M.recs.slice(i + 1).find(r => r.turn === q.n), ms = nx && nx.ts && q.rec.ts ? new Date(nx.ts) - new Date(q.rec.ts) : NaN; return isFinite(ms) && ms >= 0 ? [q.n, ms] : null; }).filter(Boolean);
    const per = ((M.brief || {}).limits || {}).simulations_per_experiment;
    return wrap('model', `the AI is writing its reply${now.again ? ' again' : ''}`, [
      ['It was given', `the brief and its own record so far (${pl(M.recs.length, 'record')})<span data-new="${fresh.length}">${fresh.length ? `; new to it since its last reply: ${fresh.join('; ')}` : '; nothing new since its last reply'}</span>`, 'given'],
      ['Waiting for its verdict', `<span data-wait="${e(wait.map(h => h.id).join(','))}">${wait.length ? `${wait.map(h => EV.link(h.id)).join(', ')} <span class="sm">· checked by the harness, not judged by the AI yet</span>` : 'no hypothesis: none has a checked decision rule and no verdict'}</span>`, 'wait'],
      ['This reply', e(EV.liveMay(now)), 'may'],
      ['Simulations left', `<b data-left="${t.left ?? ''}">${t.left ?? EV.nr}</b>${per && !now.mode ? ` · at most ${e(per)} in one experiment` : ''}`, 'left'],
      ['Its earlier replies took', `<span data-took="${took.map(q => q.join(':')).join(',')}">${took.length ? took.slice(-6).map(([k, ms]) => `turn ${k}: ${EV.liveClock(ms)}`).join(' · ') : 'none yet: this is its first reply'}</span>`, 'took'],
      ['While it writes', 'nothing of the reply can be shown: it arrives whole. When it is there, this card says what it decided and why.', 'whole']]);
  },
  // what the reply being written may fill: the reply arrives whole, so the page cannot say which
  liveMay: now => (now.phase !== 'reply' ? '' : now.mode === 'report' ? 'This is the last turn: only the final report is accepted.' : now.mode === 'budget' ? 'This is the last turn, the simulations are used up: it may judge earlier tests, and the final report is due.' : 'It may judge earlier tests, state a new hypothesis, set up a new test, or give its final report.'),
  // what arrived at the last reading, in words, from the kinds of the new records
  liveArrived() {
    const f = EV.live.fresh, M = EV.M; if (!f || f.sid !== M.id) return '';
    const rs = M.recs.filter(r => f.ids.has(r.id)), n = t => rs.filter(r => r.type === t), pl = (k, w, many) => `${k} ${k === 1 ? w : many || w + 's'}`, ck = n('check'), bits = [];
    if (n('verdict').length) bits.push(pl(n('verdict').length, 'verdict')); if (n('drop').length) bits.push(`${n('drop').length} dropped`); if (n('hypothesis').length) bits.push(pl(n('hypothesis').length, 'hypothesis', 'hypotheses'));
    n('experiment').forEach(x => bits.push(`experiment ${x.id}`)); if (n('simulation').length) bits.push(pl(n('simulation').length, 'simulation'));
    if (ck.length) { const void_ = ck.filter(c => M.voidIds.has(c.id)).length, held = ck.filter(c => !M.voidIds.has(c.id) && c.body.result === 'held').length, failed = ck.filter(c => !M.voidIds.has(c.id) && c.body.result === 'failed').length;
      bits.push(`${pl(ck.length, 'check')} (${held} held, ${failed} failed${void_ ? `, ${void_} void` : ''})`); }
    const no = n('malformed').length + rs.filter(r => r.type === 'note' && r.body.part).length; if (no) bits.push(`${no} refused`); if (n('report').length) bits.push('the final report');
    return bits.join(', ');
  },
  // an empty place of the glance: a dashed square; working: the work can fill it next
  slot: (what, title, working) => `<i class="gm slot${working ? ' wk' : ''}" data-slot="${what}" title="${EV.e(title)}"></i>`,
  nowDot: title => `<i class="nowdot" title="${EV.e(title || 'The work is here')}"></i>`,
  // whether an item is among those that arrived at the last reading (its class, with how long ago, so that a redraw does not start the mark again)
  freshAttr(id) { const f = EV.live.fresh, M = EV.M; if (!f || !M || f.sid !== M.id || !f.ids.has(id)) return ''; const age = (performance.now() - f.at) / 1000; return age > 30 ? '' : ` data-fresh="${Math.round(age)}"`; },

  // ---- the banner of a running session: where the work is, what arrived last, "follow the work", Stop. After the session
  // ended on a page that saw it running: one line that says how it ended.
  liveBanner() {
    const M = EV.M, row = EV.files.row || {}, e = EV.e, S = EV.s, now = EV.liveNow(), m = M.meta || {};
    if (!row.running) return EV.live.ran[M.id] && !EV.off ? `<div class="ev-card ev-bar ev-run ev-ended" id="live-bar" data-phase="ended"><span class="pill">ended</span> <b>The session ended${m.how ? ': ' + e(m.how) : ''}.</b> <span class="sm">${m.how === 'simulation limit reached' ? `It used all ${e(((M.brief || {}).limits || {}).simulations ?? 'the')} simulations the brief allows; the harness then gave it one last turn for its final report. ` : ''}${M.report ? 'Its final report is in “What it proposes”.' : 'It gave no final report.'}${M.report && !M.tests.some(T => !T.verdict) ? '' : ' A place that was never filled stays drawn empty.'}</span></div>` : '';
    const t = M.turns[M.turns.length - 1], arrived = EV.liveArrived(), owner = (EV.st || {}).owner, you = (EV.st || {}).you, mine = !!row.by && row.by === you;
    // who started it, and who can stop it (the account that started it, or the owner of the page; the server says which, "can_stop"; a server that does not say: whoever
    // sees it). Kept short, because a longer end would make the banner wrap when a note arrives, and the page would move: the one who started it sees the Stop button
    // alone (who started it is in its box); anybody else sees "started by <account>", with the Stop button only for the owner
    const who = row.by && !mine ? `<span class="sm" id="live-by" data-by-account="${e(row.by)}" title="${e(row.can_stop ? `Started by ${row.by}. As the owner of the page you can stop it.` : `Started by ${row.by}. Only ${row.by} or ${owner || 'the owner of the page'} can stop it.`)}">started by <b>${e(row.by)}</b></span> ` : '';
    const stop = !row.stoppable ? `<span class="sm"${row.by ? ` id="live-by" data-by-account="${e(row.by)}" title="Started by ${e(row.by)}, from a terminal"` : ''}>started from a terminal: it is stopped there</span>`
      : who + ((row.can_stop ?? true) ? `<button data-act="stop"${EV.stopping ? ' disabled' : ''}${mine ? ' title="You started this session"' : ''}>${EV.stopping ? 'Stopping…' : 'Stop'}</button>` : '');
    const left = t && t.left != null ? `${t.left} simulation${t.left === 1 ? '' : 's'} left` : '';
    return `<div class="ev-card ev-bar ev-run" id="live-bar" data-phase="${now ? now.phase : S.step != null ? 'replay' : 'closing'}"${now && now.turn ? ` data-turn="${now.turn}"` : ''}><span class="pill live">running</span>
      <span class="lv-say">${now ? `<span class="lv-step on lv-ico" data-by="${now.phase === 'reply' ? 'model' : now.phase === 'sims' ? 'simulator' : 'harness'}"><i class="sw"></i></span><b id="live-say">${EV.liveSay(now)}</b>${EV.liveTimer()}${EV.liveDoneHtml(now)}${EV.liveMay(now) ? ` <span id="live-may">${EV.liveMay(now)}</span>` : ''}` : `<b id="live-say">${S.step != null ? 'The replay is at an earlier step: the newest records are greyed.' : 'The final report is in: the harness is closing the session.'}</b>`}${left ? ` <span class="sm">· ${left}</span>` : ''}
        ${arrived ? `<span class="sm" id="live-arrived" title="Just arrived: ${e(arrived)}">· just arrived: ${e(arrived)}</span>` : ''}</span>
      <span class="end">${stop}${EV.stopMsg ? ` <span class="bad">${e(EV.stopMsg)}</span>` : ''}</span></div>`;
  },
  // after the page is drawn: the banner's height (the detail pane stays below it), the marks of what just arrived, and, with "follow the work" on, the place of the work
  liveAfter() {
    const bar = document.getElementById('live-bar'), root = document.getElementById('ev'), hd = document.getElementById('ev-head'); if (!root) return;
    if (bar && hd) { root.style.setProperty('--head-h0', hd.offsetHeight + 'px'); root.style.setProperty('--head-h', hd.offsetHeight + bar.offsetHeight + 8 + 'px'); }
    const f = EV.live.fresh; if (f && EV.M && f.sid === EV.M.id && EV.s.step == null) { const age = (performance.now() - f.at) / 1000;
      if (age <= 30) document.querySelectorAll('#s-notebook [data-step], #s-find tr[data-step]').forEach(el => { if (f.steps.has(Number(el.dataset.step)) && !el.closest('[data-fresh]')) el.dataset.fresh = Math.round(age); });
      document.querySelectorAll('#ev [data-fresh]').forEach(el => { el.style.animationDelay = `-${el.dataset.fresh}s`; }); }
    EV.liveNote();
  },
  // The page never moves by itself. When a new turn begins, a small note under the banner says so for a quarter of a minute; its button takes the
  // reader to that turn in the notebook, at the reader's own click. The note is drawn again with the page, without starting afresh.
  liveNote() {
    const L = EV.live, M = EV.M, now = EV.liveNow(), old = document.getElementById('live-note'); if (old) old.remove(); if (!M || !now) return;
    const was = L.turnOf[M.id]; L.turnOf[M.id] = now.turn; if (was != null && now.turn > was) L.note = { sid: M.id, turn: now.turn, until: performance.now() + 15000, fresh: true };
    // and when an experiment's simulations start: they take seconds, and their pictures are in another part of the page
    const sim = now.phase === 'sims' ? now.exp : null, simWas = L.expOf[M.id]; L.expOf[M.id] = sim; if (was != null && sim && sim !== simWas) L.note = { sid: M.id, exp: sim, n: now.n, until: performance.now() + 15000, fresh: true };
    const n = L.note; if (!n || n.sid !== M.id || performance.now() > n.until) { L.note = null; return; }
    const el = document.createElement('div'); el.id = 'live-note'; el.className = `live-note noprint${n.fresh ? ' in' : ''}`; n.fresh = false; el.setAttribute('role', 'status'); el.dataset.turn = n.turn;
    el.innerHTML = (n.exp ? `<span class="lv-ico" data-by="simulator"><i class="sw"></i></span><span><b>ns-3 is running the ${n.n} simulation${n.n === 1 ? '' : 's'} of ${EV.e(n.exp)}</b> <span class="sm">· ${now.phase === 'sims' && now.exp === n.exp ? 'their pictures grow as they run' : 'they have ended: their pictures stay'}</span></span><button class="cl" data-act="livego" data-id="tiles" title="To the pictures of these simulations, in “What it needed to find out”">watch them</button>`
      : `${EV.nowDot()}<span><b>Turn ${n.turn} has started</b> <span class="sm">· ${now.turn === n.turn && now.phase === 'reply' ? 'the AI is writing its reply' : 'its records are arriving'}</span></span><button class="cl" data-act="livego" data-id="${n.turn}" title="To this turn in the notebook">show it</button>`) + `<button class="cl" data-act="liveclose" data-id="1" aria-label="close this note" title="close">×</button>`; if (n.exp) el.dataset.exp = n.exp;
    document.getElementById('ev').appendChild(el); clearTimeout(L.noteT); L.noteT = setTimeout(() => { const q = document.getElementById('live-note'); if (q) q.remove(); L.note = null; }, n.until - performance.now());
  },
  // the place the reader is at: the part of the page that stands at the top of the window, and how far from the top. When records arrive and the page is
  // drawn again, parts above it may have grown; the page is then set so that this part stands where it stood (EV.draw)
  liveAnchor() {
    if (window.scrollY < 1) return null; const sel = el => (el.id ? '#' + el.id : el.classList.contains('nb-group') ? `#s-notebook .nb-group[data-group="${el.dataset.group}"]` : `#s-notebook .nb-card[data-id="${el.dataset.id}"]`);
    const flows = el => { for (let a = el; a && a.id !== 'ev'; a = a.parentElement) if (/sticky|fixed/.test(getComputedStyle(a).position)) return false; return true; };  // a part that stays in the window (the header strip, the banner, the detail pane) says nothing about the reader's place
    const all = [...document.querySelectorAll('#ev .ev-card[id], #s-notebook .nb-group[data-group], #s-notebook .nb-card[data-id]')].filter(flows).map(el => [el, el.getBoundingClientRect().top]), over = all.filter(([, t]) => t <= 160), pick = over.length ? over[over.length - 1] : all.find(([, t]) => t > 160);
    return pick ? { sel: sel(pick[0]), top: pick[1] } : null;
  },
  // every second: the time in the sentence; every two: has the ledger grown?
  liveTick() {
    const a = EV.liveAge(); if (a != null) document.querySelectorAll('#ev [data-live-t]').forEach(el => { el.textContent = EV.liveClock(a); });
    const L = EV.live, row = (EV.files && EV.files.row) || {}, h = L.head;
    if (EV.off || L.busy || document.hidden || EV.s.view !== 'session' || !row.running || !h || (L.n = (L.n || 0) + 1) % 2) return;
    L.busy = true;
    const now = EV.liveNow(), sid = EV.M && EV.M.id;  // while simulations run the ledger does not grow: the index of the runs does
    if (now && (now.phase === 'sims' || now.phase === 'baseline')) EV.get(`../sessions/${sid}/runs/index.json`).then(t => { if (!EV.M || EV.M.id !== sid) return; if (t == null) { if (EV.tilesTick) EV.tilesTick(now, sid); return; }  // no index yet: the session's first simulations are still running
      EV.files.index = EV_DATA.lines(t); if (EV.tilesTick) EV.tilesTick(now, sid); const el = document.getElementById('live-done'), n = EV.liveDone(); if (el && el.dataset.n !== String(n)) { el.dataset.n = n; el.textContent = `· the harness has collected ${n} of them so far`; } });
    fetch(h.url + '?t=' + Date.now(), { method: 'HEAD', cache: 'no-store' }).then(r => { if (r.ok && r.headers.get('Content-Length') !== h.len && EV.live.head === h) { EV.sig = ''; EV.live.keepUntil = performance.now() + 5000; return EV.load(); } }).catch(() => {}).finally(() => { L.busy = false; });
  },
});
EV.act = Object.assign(EV.act || {}, {
  // the note of a new turn: its button goes to that turn in the notebook (the reader's own click), the cross closes it
  livego(id) { const el = id === 'tiles' ? document.getElementById('live-tiles') || document.getElementById('s-find') : document.querySelector(`#s-notebook .nb-turn[data-turn="${id}"]`) || document.querySelector('#s-notebook .nb-now'); EV.act.liveclose(); if (el) el.scrollIntoView({ block: 'center', behavior: 'smooth' }); },
  liveclose() { clearTimeout(EV.live.noteT); EV.live.note = null; const q = document.getElementById('live-note'); if (q) q.remove(); },
});
if (!EV.off) setInterval(EV.liveTick, 1000);
