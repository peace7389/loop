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
//   the time           how long the newest record has been the newest: the server's own clock (the Date header of its
//                      answer) against the time the ledger was last written (Last-Modified), counted on from there.
//   what just arrived  the records that were not there at the last reading are marked for a short while.
//   the quick reading  every two seconds the size of the ledger is asked for (a HEAD request); the session is read
//                      again only when it has grown. The form of a turn is the harness's, told to the AI in its prompt;
//                      what fills it, how many turns there are and when it stops are the AI's.
// Nothing here is written by a model, and no draft is read: of a draft record only its type is looked at, to say
// that a reply was asked for a second time.
// ======================================================================================================
Object.assign(EV, {
  live: { seen: {}, ran: {}, fresh: null, head: null, tries: 0, busy: false },
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
  // what the reply being written may fill: the reply arrives whole, so the page cannot say which
  liveMay: now => (now.phase !== 'reply' ? '' : now.mode === 'report' ? 'This is the last turn: only the final report is accepted.' : now.mode === 'budget' ? 'This is the last turn, the simulations are used up: it may judge earlier tests, and the final report is due.' : 'It may judge earlier tests, ask a new question, set up a new test, or give its final report.'),
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
    if (!row.running) return EV.live.ran[M.id] && !EV.off ? `<div class="ev-card ev-bar ev-run ev-ended" id="live-bar" data-phase="ended"><span class="pill">ended</span> <b>The session ended${m.how ? ': ' + e(m.how) : ''}.</b> <span class="sm">${M.report ? 'Its final report is in “What it proposes”.' : 'It gave no final report.'} A place that was never filled stays drawn empty.</span></div>` : '';
    const t = M.turns[M.turns.length - 1], arrived = EV.liveArrived(), stop = row.stoppable ? `<button data-act="stop"${EV.stopping ? ' disabled' : ''}>${EV.stopping ? 'Stopping…' : 'Stop'}</button>` : '<span class="sm">started from a terminal: it is stopped there</span>';
    const left = t && t.left != null ? `${t.left} simulation${t.left === 1 ? '' : 's'} left` : '';
    return `<div class="ev-card ev-bar ev-run" id="live-bar" data-phase="${now ? now.phase : S.step != null ? 'replay' : 'closing'}"${now && now.turn ? ` data-turn="${now.turn}"` : ''}><span class="pill live">running</span>
      <span class="lv-say">${now ? `${EV.nowDot()}<b id="live-say">${EV.liveSay(now)}</b>${EV.liveTimer()}${EV.liveMay(now) ? ` <span id="live-may">${EV.liveMay(now)}</span>` : ''}` : `<b id="live-say">${S.step != null ? 'The replay is at an earlier step: the newest records are greyed.' : 'The final report is in: the harness is closing the session.'}</b>`}${left ? ` <span class="sm">· ${left}</span>` : ''}
        ${arrived ? `<span class="sm" id="live-arrived">· just arrived: ${e(arrived)}</span>` : ''}</span>
      <span class="end"><label class="sm" style="font-weight:400" title="Off: the page never moves by itself. On: when new records arrive, the notebook comes to the place where the work is."><input type="checkbox" data-ch="follow"${S.follow ? ' checked' : ''}> follow the work</label> ${stop}${EV.stopMsg ? ` <span class="bad">${e(EV.stopMsg)}</span>` : ''}</span></div>`;
  },
  // after the page is drawn: the banner's height (the detail pane stays below it), the marks of what just arrived, and, with "follow the work" on, the place of the work
  liveAfter() {
    const bar = document.getElementById('live-bar'), root = document.getElementById('ev'), hd = document.getElementById('ev-head'); if (!root) return;
    if (bar && hd) { root.style.setProperty('--head-h0', hd.offsetHeight + 'px'); root.style.setProperty('--head-h', hd.offsetHeight + bar.offsetHeight + 8 + 'px'); }
    const f = EV.live.fresh; if (f && EV.M && f.sid === EV.M.id && EV.s.step == null) { const age = (performance.now() - f.at) / 1000;
      if (age <= 30) document.querySelectorAll('#s-notebook [data-step], #s-find tr[data-step]').forEach(el => { if (f.steps.has(Number(el.dataset.step)) && !el.closest('[data-fresh]')) el.dataset.fresh = Math.round(age); });
      document.querySelectorAll('#ev [data-fresh]').forEach(el => { el.style.animationDelay = `-${el.dataset.fresh}s`; }); }
    if (EV.s.follow && EV.live.moved !== (f && f.at) && f) { EV.live.moved = f.at; const el = document.querySelector('#s-notebook .nb-now') || document.querySelector('#s-notebook [data-fresh]'); if (el) el.scrollIntoView({ block: 'center' }); }
  },
  // every second: the time in the sentence; every two: has the ledger grown?
  liveTick() {
    const a = EV.liveAge(); if (a != null) document.querySelectorAll('#ev [data-live-t]').forEach(el => { el.textContent = EV.liveClock(a); });
    const L = EV.live, row = (EV.files && EV.files.row) || {}, h = L.head;
    if (EV.off || L.busy || document.hidden || EV.s.view !== 'session' || !row.running || !h || (L.n = (L.n || 0) + 1) % 2) return;
    L.busy = true;
    fetch(h.url + '?t=' + Date.now(), { method: 'HEAD', cache: 'no-store' }).then(r => { if (r.ok && r.headers.get('Content-Length') !== h.len && EV.live.head === h) { EV.sig = ''; return EV.load(); } }).catch(() => {}).finally(() => { L.busy = false; });
  },
});
EV.chg = Object.assign(EV.chg || {}, { follow(t) { EV.s.follow = t.checked; EV.store('ev-follow', t.checked ? '1' : '0'); } });
EV.s.follow = EV.store('ev-follow') === '1';
if (!EV.off) setInterval(EV.liveTick, 1000);
