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
//                        now.json names a step of this turn by an agent  that step (the supervisor, the judge; a restatement,
//                                                                        a repair by the researcher)
//                        the newest record is a turn's first record      the researcher is writing its reply
//                        anything else                                   the harness is preparing the next turn
//                      The AI's reply arrives whole, so while it is written the page cannot know which place it will
//                      fill: the mark then stands on every place that reply may fill, and the sentence says so.
//   the stage          in "What it needed to find out" a strip of the steps of a turn in the session's arm, the one being worked
//                      on with its moving icon and the time; before the first question exists the section shows only that.
//                      One AI: the researcher writes its reply, (the judge reads each new hypothesis,) ns-3 runs its simulations,
//                      the harness checks each decision rule, the next turn. The arm "supervised" (2026-11-22, the operator: "Shouldn't
//                      we reflect changes on this?"): the researcher writes its reply, the supervisor reads each new guess (a guess
//                      it or the harness did not accept is restated by the researcher), the supervisor reviews each test in up to 3
//                      rounds (a test sent back is repaired by the researcher), ns-3 runs its simulations, the harness checks each
//                      decision rule, the supervisor rules on each test (or, for results no ruling covers, notes what they leave
//                      unexplained), the next turn. Where the records cannot say it (a supervisor's reading is recorded only when
//                      its step is done), the step is the one the harness wrote in now.json as it began it
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
    // the step the harness wrote as it began it (now.json, since 2026-11-22), for the newest turn only: a step no record shows yet
    const nw = EV.files.now, mine = nw && typeof nw === 'object' && nw.turn === last.turn, tr = recs.filter(r => r.type === 'turn').pop(), mode = tr && tr.turn === last.turn ? tr.body.last_turn || null : null;
    if (mine && EV.LIVE_AGENT_STEPS.includes(nw.step)) return { phase: nw.step, turn: last.turn, about: nw.about || null, round: nw.round || null, rounds: nw.rounds || null, by: nw.by || null };
    // a reply begun after the newest record (a continued reply of the turn, or the first after a ruling asked for again) is being written (the coherence audit, 2026-11-22: it read "preparing the next turn")
    // again: now.json says whether the reply is asked again; the drafts of the turn only where there is none (s056 turn 12: a reply continued after its requests read "its first reply could not be used")
    const begun = mine && nw.step === 'reply' && last.ts && nw.at && last.ts <= nw.at;
    if (last.type === 'turn' || begun || (mine && nw.step === 'reply' && nw.again && EV.live.tries < 2)) return { phase: 'reply', turn: last.turn, mode, again: mine && nw.step === 'reply' ? !!nw.again : EV.live.tries > 0, cont: mine && nw.step === 'reply' && (nw.round || 1) > 1 ? nw.round : null };
    return { phase: 'between', turn: last.turn };
  },
  // the steps of a turn done by an agent, that the records show only when they are done (the harness names them in now.json)
  LIVE_AGENT_STEPS: ['judge', 'review', 'ground', 'restate', 'design', 'repair', 'ruling', 'objection', 'look'],
  // who works in a phase (its icon)
  liveBy: p => (['reply', 'restate', 'repair'].includes(p) ? 'model' : ['sims', 'baseline'].includes(p) ? 'simulator' : ['judge', 'review', 'ground', 'design', 'ruling', 'objection', 'look'].includes(p) ? 'supervisor' : 'harness'),
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
      : now.phase === 'baseline' ? 'The harness is running the baseline simulation, before the researcher’s first turn.'
      : now.phase === 'sims' ? `${t}the simulator is working on the ${now.n} simulation${now.n === 1 ? '' : 's'} of experiment ${e(now.exp)}.`
      : now.phase === 'reply' ? `${t}the researcher is writing its reply${now.cont ? ` (reply ${now.cont} of this turn: what it asked for is answered)` : ''}${now.again ? ' again (its first reply could not be used)' : ''}.`
      : now.phase === 'judge' ? `${t}the judge, a second AI, reads each new hypothesis against the guess it comes from.`
      : now.phase === 'review' ? `${t}the supervisor reads the new guesses and reviews the new tests, in one request.`
      : now.phase === 'ground' ? `${t}the supervisor reads a new guess against the records it cites.`
      : now.phase === 'restate' ? `${t}the researcher restates a guess the ${now.by === 'harness' ? 'harness' : 'supervisor'} did not accept (once, in this turn).`
      : now.phase === 'design' ? `${t}the supervisor reviews the test of ${e(now.about || 'a hypothesis')}${(now.round || 1) > 1 ? ' again' : ''} before any of its simulations runs (round ${now.round || 1} of ${now.rounds || 3}).`
      : now.phase === 'repair' ? `${t}the researcher repairs the test of ${e(now.about || 'a hypothesis')} that was sent back, for round ${now.round || 2} of ${now.rounds || 3}.`
      : now.phase === 'ruling' ? `${t}the supervisor rules on ${e(now.about || 'each test')}: what its checks mean.`
      : now.phase === 'objection' ? `${t}the supervisor looks again at its ruling on ${e(now.about || 'a hypothesis')}: the researcher objected to it.`
      : now.phase === 'look' ? (now.turn ? `${t}the supervisor notes what the results of ${e(now.about || 'the experiment')} leave unexplained.` : 'Before turn 1: the supervisor notes what the baseline leaves unexplained.')
      : `${t}the harness is preparing the next turn.`;
  },
  // the stage of a running session: the steps of a turn as a track (2026-11-22, the operator: "I think we should give it more quality in design and
  // structure"): a node for each step on one line, its short name and who does it under the node; the steps already done in this turn filled, the one
  // being worked on in the accent colour with its moving icon, what it works on (a test's rounds as dots) and the time, the steps to come dashed. The
  // steps are those of the session's arm. The sentence of what is happening stands in the banner, not here; each step's hover box says it in full, and a
  // step that has something to show opens it beside the page (the page does not move). big: where a section has nothing else yet
  liveStage(now, big) {
    if (!now) return ''; const M = EV.M, e = EV.e, fl = (M.meta && M.meta.flags) || {}, sup = fl.arm === 'supervised', x = M.recs.filter(r => r.type === 'experiment' && r.turn === now.turn).pop(), hid = now.about && M.byId[now.about] ? now.about : null;
    const go = { reply: now.turn > 0 ? ['log', now.turn] : null, baseline: x && x.turn === 0 ? ['exp', x.id] : null, sims: x && x.turn > 0 ? ['exp', x.id] : null, checks: x && x.turn > 0 && ['between', 'ruling', 'look'].includes(now.phase) ? ['exp', x.id] : null,
      design: hid && ['design', 'repair'].includes(now.phase) ? ['hyp', hid] : null, ruling: hid && ['ruling', 'objection'].includes(now.phase) ? ['hyp', hid] : null, look: x ? ['exp', x.id] : null };
    // a step of an agent opens what the agent wrote in it, its tokens (2026-11-22, the operator: "When user clicks past or ongoing stage here they should be able to see tokens directly")
    ['reply', 'ground', 'design', 'judge', 'ruling', 'look'].forEach(k => { go[k] = ['calls', `${now.turn}:${k}`]; });
    const opens = { log: 'the work log of this turn', exp: 'this experiment', hyp: 'this hypothesis', calls: 'what the agent wrote in this step, its tokens' }, R = now.round || 1, of = now.rounds || 3, ab = now.about || '';
    // [key, who, its name, under it, its sentence, the phases it stands for]
    let head = `Turn ${now.turn}`, steps;
    if (now.phase === 'start' || now.phase === 'baseline' || (now.phase === 'look' && !now.turn)) {
      head = 'Before turn 1';
      steps = [['baseline', now.phase === 'start' ? 'harness' : 'simulator', 'Baseline', now.phase === 'start' ? 'harness prepares' : 'ns-3, every default', 'The harness runs one simulation with every setting at its default, before the first turn', ['start', 'baseline']]]
        .concat(sup ? [['look', 'supervisor', 'Findings', 'supervisor', 'The supervisor notes what the baseline leaves unexplained', ['look']]] : [])
        .concat([['reply', 'model', 'First reply', 'researcher', 'The researcher writes its first reply', []]]);
    } else if (now.phase === 'reply' && now.mode) {
      steps = [['reply', 'model', 'Last reply', now.again ? 'researcher, again' : 'researcher', 'The last turn: the researcher writes its final report', ['reply']], ['end', 'harness', 'Final report', 'the session ends', 'The session ends with the final report', []]];
    } else {
      steps = [['reply', 'model', 'Reply', now.again ? 'researcher, again' : 'researcher', 'The researcher writes its reply: what it read, its guesses, its hypotheses and its test', ['reply']]]
        .concat(sup ? [
          ['ground', now.phase === 'restate' ? 'model' : 'supervisor', 'Guesses', now.phase === 'restate' ? 'researcher restates one' : 'supervisor reads', 'The supervisor reads each new guess against the records it cites; a guess it or the harness does not accept, the researcher restates once, in this turn', ['review', 'ground', 'restate']],
          ['design', now.phase === 'repair' ? 'model' : 'supervisor', 'Test review', now.phase === 'repair' ? `researcher repairs ${ab}` : now.phase === 'design' ? `supervisor, ${ab}` : `supervisor, up to ${of} rounds`, `The supervisor reviews each test before any of its simulations runs, in up to ${of} rounds; a test it sends back, the researcher repairs in this turn`, ['design', 'repair']]]
          : fl.judge === 'on' ? [['judge', 'supervisor', 'Link check', 'judge', 'The judge, a second AI, reads each new hypothesis against the guess it comes from', ['judge']]] : [])
        .concat([['sims', 'simulator', 'Simulations', 'ns-3', 'ns-3 runs the simulations of the experiment', ['sims']], ['checks', 'harness', 'Checks', 'harness', 'The harness checks each decision rule against the measured numbers', []]])
        .concat(sup ? [now.phase === 'look' ? ['look', 'supervisor', 'Findings', 'supervisor', 'The supervisor notes what the results leave unexplained (an experiment that tests nothing has no ruling)', ['look']]
                                            : ['ruling', 'supervisor', 'Rulings', now.phase === 'ruling' && ab ? `supervisor, ${ab}` : 'supervisor', 'The supervisor rules on each checked test: what its checks mean; it looks again at a ruling the researcher objects to', ['ruling', 'objection']]] : [])
        .concat([['next', 'harness', 'Next turn', now.phase === 'between' ? 'harness prepares' : 'harness', 'The harness prepares the next turn', ['between']]]);
    }
    const on = steps.findIndex(q => q[5].includes(now.phase));
    const dots = ['design', 'repair'].includes(now.phase) ? `<span class="lv-rounds" title="Round ${R} of ${of}">${Array.from({ length: of }, (_, i) => `<i${i < R ? ' class="r-on"' : ''}></i>`).join('')}</span>` : '';
    const li = ([key, by, name, under, say], i) => { const st = i < on ? 'done' : i === on ? 'on' : 'todo', g = st === 'todo' && go[key] && go[key][0] === 'calls' ? null : go[key];
      return `<li class="lv-st ${st}${g ? ' lv-go' : ''}" data-key="${key}" data-by="${by}" title="${e(say + (st === 'done' ? ' (done)' : st === 'on' ? ' (now)' : '') + (g ? `. Click to open ${opens[g[0]]}, beside the page` : ''))}"${g ? ` data-act="open" data-t="${g[0]}" data-id="${e(g[1])}" role="button" tabindex="0"` : ''}>`
        + `<span class="lv-node"><i class="sw"></i></span><b>${e(name)}</b><small>${e(under)}</small>${st === 'on' ? `${key === 'design' ? dots : ''}<small class="lv-tm">${EV.liveTimer()}</small>` : ''}</li>`; };
    return `<div class="lv-stage lv-track${big ? ' big' : ''}" data-phase="${now.phase}" data-arm="${sup ? 'supervised' : fl.arm || 'hypotheses'}"><span class="lv-turn">${head}</span><ol class="lv-steps" style="--n:${steps.length}">${steps.map(li).join('')}</ol></div>`;
  },
  // The work log of the turn that is being worked on begins with what is happening now. While the AI writes its reply it says: what the AI was given (the brief,
  // its record so far, and what is new to it since its last reply: the records of that time it did not write itself), which hypotheses wait for its verdict,
  // what the reply may bring, how many simulations are left, how long its earlier replies of this session took (from the times of the records: the turn's
  // first record to the first record of the reply), and that the reply arrives whole. Nothing here is the AI's text, and no draft is read.
  liveNowCard(n) {
    const now = EV.liveNow(), M = EV.M, e = EV.e; if (!now || now.turn !== n) return '';
    const head = (by, text) => `<h3><span class="st-by" data-by="${by}"><i class="sw"></i></span> Now · ${text}${EV.liveTimer()}</h3>`, wrap = (by, text, rows) => `<div class="lg-now" id="lg-now" data-phase="${now.phase}" data-turn="${n}">${head(by, text)}${rows.length ? `<dl class="lg-nkv">${rows.map(([k, v, key]) => `<dt>${k}</dt><dd data-ln="${key}">${v}</dd>`).join('')}</dl>` : ''}</div>`;
    if (now.phase === 'sims') return wrap('simulator', `ns-3 runs the ${now.n} simulation${now.n === 1 ? '' : 's'} of ${EV.link(now.exp)}`, [['Collected so far', `<span data-n="${EV.liveDone()}">${EV.liveDone()} of ${now.n}</span> · the harness checks the decision rules when all are in`, 'done']]);
    if (EV.LIVE_AGENT_STEPS.includes(now.phase)) return wrap(EV.liveBy(now.phase), EV.liveSay(now).replace(/^Turn \d+: /, '').replace(/\.$/, ''), []);
    if (now.phase !== 'reply') return wrap('harness', 'the harness prepares the next turn', []);
    const t = M.turns.find(q => q.n === n) || {}, added = (t.added || []).map(id => M.byId[id]).filter(Boolean), of = ty => added.filter(r => r.type === ty), pl = (k, w, many) => `${k} ${k === 1 ? w : many || w + 's'}`;
    const ck = of('check'), void_ = ck.filter(c => M.voidIds.has(c.id)).length, held = ck.filter(c => !M.voidIds.has(c.id) && c.body.result === 'held').length, failed = ck.length - void_ - held, notes = of('note'), res = of('result');
    const fresh = [...of('evidence').map(r => `the result table ${EV.link(r.id)} of ${EV.link(r.parent)} (${pl((r.body.lines || []).length, 'simulation')})`),
      ck.length ? `${pl(ck.length, 'check')} of its decision rules: <span data-ck="${held},${failed},${void_}">${[held ? EV.res('held', `${held} held`) : '', failed ? EV.res('failed', `${failed} failed`) : '', void_ ? `${void_} void` : ''].filter(Boolean).join(', ')}</span>` : '',
      res.length ? `${pl(res.length, 'answer')} to what it asked for (${res.map(r => EV.link(r.id)).join(', ')})` : '', notes.length ? `${pl(notes.length, 'note')} of the harness (${notes.slice(0, 4).map(r => EV.link(r.id)).join(', ')}${notes.length > 4 ? ', …' : ''})` : ''].filter(Boolean);
    const wait = M.hyps.filter(h => EV.seen(h.id) && h.state === 'open' && h.tests.some(q => { const c = M.testById[q].check; return c && EV.seen(c.id); }));
    const took = M.turns.filter(q => q.n >= 1 && q.n < n && q.rec).map(q => { const i = M.recs.indexOf(q.rec), nx = M.recs.slice(i + 1).find(r => r.turn === q.n), ms = nx && nx.ts && q.rec.ts ? new Date(nx.ts) - new Date(q.rec.ts) : NaN; return isFinite(ms) && ms >= 0 ? [q.n, ms] : null; }).filter(Boolean);
    const per = ((M.brief || {}).limits || {}).simulations_per_experiment;
    const arm = ((M.meta && M.meta.flags) || {}).arm || 'hypotheses';
    return wrap('model', `the researcher is writing its reply${now.cont ? ` (reply ${now.cont} of this turn)` : ''}${now.again ? ' again' : ''}`, [
      ['It was given', `the brief and its own record so far (${pl(M.recs.length, 'record')})<span data-new="${fresh.length}">${fresh.length ? `; new to it since its last reply: ${fresh.join('; ')}` : '; nothing new since its last reply'}</span>`, 'given'],
      arm === 'plain' ? null : [arm === 'supervised' ? 'Waiting for a ruling' : 'Waiting for its verdict', `<span data-wait="${e(wait.map(h => h.id).join(','))}">${wait.length ? `${wait.map(h => EV.link(h.id)).join(', ')} <span class="sm">· checked by the harness, ${arm === 'supervised' ? 'not ruled on by the supervisor yet' : 'not judged by the AI yet'}</span>` : `no hypothesis: none has a checked decision rule and no ${arm === 'supervised' ? 'ruling' : 'verdict'}`}</span>`, 'wait'],
      ['This reply', e(EV.liveMay(now)), 'may'],
      ['Simulations left', `<b data-left="${t.left ?? ''}">${t.left ?? EV.nr}</b>${per && !now.mode ? ` · at most ${e(per)} in one experiment` : ''}`, 'left'],
      ['Its earlier replies took', `<span data-took="${took.map(q => q.join(':')).join(',')}">${took.length ? took.slice(-6).map(([k, ms]) => `turn ${k}: ${EV.liveClock(ms)}`).join(' · ') : 'none yet: this is its first reply'}</span>`, 'took'],
      ['While it writes', 'nothing of the reply can be shown: it arrives whole. When it is there, this card says what it decided and why.', 'whole']].filter(Boolean));
  },
  // what the reply being written may fill: the reply arrives whole, so the page cannot say which
  liveMay: now => { const arm = ((EV.M && EV.M.meta && EV.M.meta.flags) || {}).arm || 'hypotheses';   // in the session's arm (the coherence audit, 2026-11-22: it was the single-AI arm's)
    return now.phase !== 'reply' ? '' : now.mode === 'report' ? 'This is the last turn: only the final report is accepted.'
      : now.mode === 'budget' ? (arm === 'hypotheses' ? 'This is the last turn, the simulations are used up: it may judge earlier tests, and the final report is due.' : arm === 'supervised' ? 'This is the last turn, the simulations are used up: the final report is due (the rulings are the supervisor’s).' : 'This is the last turn, the simulations are used up: the final report is due.')
      : arm === 'supervised' ? 'It may read results, state guesses and hypotheses, set up a test, object to a ruling, or give its final report.' : arm === 'plain' ? 'It may ask for information, set up an experiment, or give its final report.'
      : 'It may judge earlier tests, state a new hypothesis, set up a new test, or give its final report.'; },
  // what arrived at the last reading, in words, from the kinds of the new records
  liveArrived() {
    const f = EV.live.fresh, M = EV.M; if (!f || f.sid !== M.id) return '';
    const rs = M.recs.filter(r => f.ids.has(r.id)), n = t => rs.filter(r => r.type === t), pl = (k, w, many) => `${k} ${k === 1 ? w : many || w + 's'}`, ck = n('check'), bits = [];
    if (n('verdict').length) bits.push(pl(n('verdict').length, 'verdict')); if (n('drop').length) bits.push(`${n('drop').length} dropped`); if (n('hypothesis').length) bits.push(pl(n('hypothesis').length, 'hypothesis', 'hypotheses'));
    n('experiment').forEach(x => bits.push(`experiment ${x.id}`)); if (n('simulation').length) bits.push(pl(n('simulation').length, 'simulation'));
    if (ck.length) { const void_ = ck.filter(c => M.voidIds.has(c.id)).length, held = ck.filter(c => !M.voidIds.has(c.id) && c.body.result === 'held').length, failed = ck.filter(c => !M.voidIds.has(c.id) && c.body.result === 'failed').length;
      bits.push(`${pl(ck.length, 'check')} (${held} held, ${failed} failed${void_ ? `, ${void_} void` : ''})`); }
    const no = n('malformed').length + rs.filter(r => EV_DATA.refusal(r)).length; if (no) bits.push(`${no} refused`); if (n('report').length) bits.push('the final report');
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
    if (!row.running) return EV.live.ran[M.id] && !EV.off ? `<div class="ev-card ev-bar ev-run ev-ended" id="live-bar" data-phase="ended"><span class="pill">ended</span> <b>The session ended${m.how ? ': ' + e(m.how) : ''}.</b> <span class="sm">${/^(simulation limit reached|all simulations used)/.test(m.how || '') ? `It used all ${e(((M.brief || {}).limits || {}).simulations ?? 'the')} simulations the brief allows; the harness then gave it one last turn for its final report. ` : ''}${M.report ? 'Its final report is in “What it proposes”.' : 'It gave no final report.'}${M.report && !M.tests.some(T => !T.verdict) ? '' : ' A place that was never filled stays drawn empty.'}</span></div>` : '';
    const t = M.turns[M.turns.length - 1], arrived = EV.liveArrived(), owner = (EV.st || {}).owner, you = (EV.st || {}).you, mine = !!row.by && row.by === you;
    // who started it, and who can stop it (the account that started it, or the owner of the page; the server says which, "can_stop"; a server that does not say: whoever
    // sees it). Kept short, because a longer end would make the banner wrap when a note arrives, and the page would move: the one who started it sees the Stop button
    // alone (who started it is in its box); anybody else sees "started by <account>", with the Stop button only for the owner
    const who = row.by && !mine ? `<span class="sm" id="live-by" data-by-account="${e(row.by)}" title="${e(row.can_stop ? `Started by ${row.by}. As the owner of the page you can stop it.` : `Started by ${row.by}. Only ${row.by} or ${owner || 'the owner of the page'} can stop it.`)}">started by <b>${e(row.by)}</b></span> ` : '';
    // a session started with a command in a terminal on the server (not with this page's Start): the page did not start it, so it cannot stop it
    const stop = !row.stoppable ? `<span class="sm" id="live-by"${row.by ? ` data-by-account="${e(row.by)}"` : ''} title="This session was started with a command in a terminal on the server, not with this page's Start button. The page can stop only the sessions it started: this one is stopped in that terminal, or ends by itself.">started from a terminal${row.by ? ` by <b>${e(row.by)}</b>${mine ? ' (you)' : ''}` : ''} · this page cannot stop it</span>`
      : who + ((row.can_stop ?? true) ? `<button data-act="stop"${EV.stopping ? ' disabled' : ''}${mine ? ' title="You started this session"' : ''}>${EV.stopping ? 'Stopping…' : 'Stop'}</button>` : '');
    const left = t && t.left != null ? `${t.left} simulation${t.left === 1 ? '' : 's'} left` : '';
    return `<div class="ev-card ev-bar ev-run" id="live-bar" data-phase="${now ? now.phase : S.step != null ? 'replay' : 'closing'}"${now && now.turn ? ` data-turn="${now.turn}"` : ''}><span class="pill live">running</span>
      <span class="lv-say">${now ? `<span class="lv-step on lv-ico" data-by="${EV.liveBy(now.phase)}"><i class="sw"></i></span><b id="live-say">${EV.liveSay(now)}</b>${EV.liveTimer()}${EV.liveDoneHtml(now)}${EV.liveMay(now) ? ` <span id="live-may">${EV.liveMay(now)}</span>` : ''}` : `<b id="live-say">${S.step != null ? 'The replay is at an earlier step: the newest records are greyed.' : 'The final report is in: the harness is closing the session.'}</b>`}${left ? ` <span class="sm">· ${left}</span>` : ''}
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
  // The page never moves by itself. Until 2026-11-22 a small note under the banner said for a quarter of a minute that a turn had started or that
  // simulations were running; the operator: "Isn't it redundant ... while we already have on top?" The banner (Running now: ... turn N) and the
  // status card at the head of the session say both, so no note appears any more. A note still on the page from before is taken away.
  liveNote() { const old = document.getElementById('live-note'); if (old) old.remove(); },
  // the place the reader is at: the part of the page that stands at the top of the window, and how far from the top. When records arrive and the page is
  // drawn again, parts above it may have grown; the page is then set so that this part stands where it stood (EV.draw)
  liveAnchor() {
    if (window.scrollY < 1) return null; const sel = el => (el.id ? '#' + el.id : el.classList.contains('nb-group') ? `#s-notebook .nb-group[data-group="${el.dataset.group}"]` : `#s-notebook .nb-card[data-id="${el.dataset.id}"]`);
    const flows = el => { for (let a = el; a && a.id !== 'ev'; a = a.parentElement) if (/sticky|fixed/.test(getComputedStyle(a).position)) return false; return true; };  // a part that stays in the window (the header strip, the banner, the detail pane) says nothing about the reader's place
    const all = [...document.querySelectorAll('#ev .ev-card[id], #s-notebook .nb-group[data-group], #s-notebook .nb-card[data-id]')].filter(flows).map(el => [el, el.getBoundingClientRect().top]), over = all.filter(([, t]) => t <= 160), pick = over.length ? over[over.length - 1] : all.find(([, t]) => t > 160);
    return pick ? { sel: sel(pick[0]), top: pick[1] } : null;
  },
  // ---- what an agent wrote in one step of a turn, its tokens (2026-11-22, the operator: "When user clicks past or ongoing stage here they should be
  // able to see tokens directly"). The calls come from /api/agents (calls.jsonl: each call's step since 2026-11-22; an earlier call is placed by what it
  // was given); the call being made from live_call.json, which the harness rewrites about once a second while the agent writes. id: "<turn>:<step key>"
  CALL_STEPS: { reply: ['reply'], ground: ['review', 'ground', 'restate'], design: ['review', 'design', 'repair'], judge: ['judge'], ruling: ['ruling', 'objection'], look: ['look'] },
  CALL_SAYS: { review: 'first review of the new guesses and tests, in one request', reply: 'reply', restate: 'restatement of a guess', repair: 'repair of a test', ground: 'reading of a guess', design: 'review of a test', ruling: 'ruling', objection: 'second look after an objection', look: 'look for findings', judge: 'link check' },
  callStep(c) {
    if (c.step) return typeof c.step === 'string' ? c.step : c.step.step;   // calls.jsonl, and live_call.json since stage 3 (2026-11-22), keep {step, about, round, by}; the held build of 2026-11-22 spread it into the call
    const s = c.system || '', u = c.user || '';
    if (c.agent === 'judge') return 'judge';
    if (c.agent === 'researcher') return s.startsWith('You are the researcher. The supervisor, or the harness, sent back') ? 'repair' : s.startsWith('You are the researcher. One of your guesses') ? 'restate' : 'reply';
    return u.includes('THE RESEARCHER OBJECTS') ? 'objection' : u.includes("THE HARNESS'S CHECKS (facts)") ? 'ruling' : u.includes('THE RECORDS THE NEW GUESS CITES') ? 'ground' : u.includes('FINDINGS (findings, at most') ? 'look' : 'design';
  },
  async callsLoad(sid) {
    const L = EV.live; if (L.callsBusy) return; L.callsBusy = true;
    const was = L.calls && L.calls.sid === sid ? L.calls.list : null, mark = l => (l ? `${l.length}|${(l[l.length - 1] || {}).n}` : '');
    try { const r = await fetch(`../api/agents?session=${encodeURIComponent(sid)}`, { cache: 'no-store' }); const j = r.ok ? await r.json() : null; L.calls = { sid, list: (j && j.calls) || [], at: Date.now() }; }
    catch (x) { L.calls = { sid, list: [], at: Date.now(), err: true }; }
    L.callsBusy = false; const sel = EV.s.sel; if (sel && sel.t === 'calls' && EV.M && EV.M.id === sid && mark(was) !== mark(L.calls.list)) EV.draw();   // drawn again only when a call was added: a reload that brings nothing new leaves the page as it is
  },
  callBox(c, live) {
    const e = EV.e, u = c.usage || {}, rt = (u.completion_tokens_details || {}).reasoning_tokens, who = c.agent === 'researcher' ? 'model' : 'supervisor', step = EV.callStep(c);
    const ans = (() => { try { return JSON.stringify(JSON.parse(c.answer), null, 1); } catch (x) { return c.answer || ''; } })(), num = v => Number(v || 0).toLocaleString('en-US');
    const meta = live ? `writing now · ${EV.liveClock((c.seconds || 0) * 1000)} · ${num((c.reasoning || '').length)} characters of reasoning, ${num((c.answer || '').length)} of answer so far`
      : `${e(c.at ? c.at.slice(11, 16) : '')} · ${EV.liveClock((c.seconds || 0) * 1000)} · ${u.completion_tokens ? `${num(u.completion_tokens)} tokens written${rt ? `, ${num(rt)} of them reasoning` : ''}` : 'tokens not counted'}${c.finish_reason && c.finish_reason !== 'stop' ? ` · <b class="warnc">stopped: ${e(c.finish_reason)}</b>` : ''}`;
    return `<div class="cl-call${live ? ' cl-live' : ''}" data-n="${e(c.n)}"><p class="cl-h"><span class="st-by" data-by="${who}"><i class="sw"></i></span><b>${e(c.agent === 'researcher' ? 'the researcher' : 'the ' + c.agent)}</b> · ${e(EV.CALL_SAYS[step] || step)}${c.step && c.step.about ? ` of ${e(c.step.about)}` : ''}${c.step && c.step.round ? `, round ${e(c.step.round)}` : ''} <span class="sm">· call ${e(c.n)} · ${meta}</span></p>`
      + `<p class="cl-k">Its reasoning</p><pre class="cl-pre cl-reason"${live ? ' id="cl-live-r"' : ''}>${e(c.reasoning || (live ? '…' : 'none kept'))}</pre>`
      + `<p class="cl-k">Its answer</p><pre class="cl-pre cl-ans"${live ? ' id="cl-live-a"' : ''}>${e(live ? c.answer || '…' : ans || 'empty')}</pre>`
      + (!live && (c.system || c.user) ? `<details class="cl-given"><summary>What it was given · ${num((c.system || '').length + (c.user || '').length)} characters</summary><pre class="cl-pre">${e(c.system || '')}</pre><pre class="cl-pre">${e(c.user || '')}</pre></details>` : '') + '</div>';
  },
  callsCard(id) {
    const M = EV.M, e = EV.e, L = EV.live, [t, key] = String(id).split(':'), turn = Number(t), steps = EV.CALL_STEPS[key] || [key];
    if (window.EV_EXPORT) return '<h2>What the agents wrote</h2><p class="sm">An exported copy holds no calls of the model: they stay on the server.</p>';
    if (!L.calls || L.calls.sid !== M.id || L.callsStale) { L.callsStale = false; EV.callsLoad(M.id); }
    const list = L.calls && L.calls.sid === M.id ? L.calls.list.filter(c => c.turn === turn && steps.includes(EV.callStep(c))) : null;
    const lv = L.liveCall && L.liveCall.sid === M.id ? L.liveCall.c : null, here = lv && !lv.done && lv.turn === turn && steps.includes(EV.callStep(lv)) && !(list || []).some(c => c.n === lv.n);
    const title = { reply: 'The researcher’s reply', ground: 'The supervisor reads the guesses', design: 'The supervisor reviews the tests', judge: 'The judge reads the hypotheses', ruling: 'The supervisor rules', look: 'The supervisor looks for findings' }[key] || key;
    return `<h2>${e(title)} <small>turn ${e(turn)}</small></h2><p class="sm">What the agent wrote in this step, call by call: its reasoning before the answer, and the answer; what it was given is folded under each.${here ? ' The call being made grows as it is written.' : ''}</p>`
      + (list == null ? '<p class="sm">Reading the calls…</p>' : '') + (list || []).map(c => EV.callBox(c, false)).join('') + (here ? `<div id="cl-live">${EV.callBox(lv, true)}</div>` : '')
      + (list && !list.length && !here ? '<p class="sm">No call of this step in this turn yet.</p>' : '');
  },
  // the call being made: live_call.json read again every two seconds while a step's card is open; its text is put in place (the page does not move)
  liveCallTick() {
    const sel = EV.s.sel, M = EV.M, row = (EV.files && EV.files.row) || {}; if (!sel || sel.t !== 'calls' || !M || !row.running || EV.off) return;
    fetch(`../sessions/${M.id}/live_call.json?t=${Date.now()}`, { cache: 'no-store' }).then(r => (r.ok ? r.json() : null)).then(c => {
      // a harness that writes no live_call.json (the one deployed before stage 3): the list of calls is read again every 10 s while the card is open (the coherence audit, 2026-11-22: it never refreshed)
      if (!c) { const L = EV.live; if (EV.M && EV.M.id === M.id && L.calls && L.calls.sid === M.id && Date.now() - L.calls.at > 10000) EV.callsLoad(M.id); return; }
      if (!EV.M || EV.M.id !== M.id) return; if (typeof c.step === 'string') c.step = { step: c.step, about: c.about || null, round: c.round || null, by: c.by || null };   // the held build's flat step
      const was = EV.live.liveCall && EV.live.liveCall.c; EV.live.liveCall = { sid: M.id, c };
      if (c.done) { if (!was || !was.done || was.n !== c.n) { EV.live.callsStale = true; EV.draw(); } return; }
      const box = document.getElementById('cl-live'); if (!box) { if (!was || was.n !== c.n) EV.draw(); return; }
      const keep = pre => pre && pre.scrollHeight - pre.scrollTop - pre.clientHeight < 24;   // a box read at its end follows the text; one scrolled back stays where it is
      const r = document.getElementById('cl-live-r'), a = document.getElementById('cl-live-a'), fr = keep(r), fa = keep(a);
      if (r) { r.textContent = c.reasoning || '…'; if (fr) r.scrollTop = r.scrollHeight; } if (a) { a.textContent = c.answer || '…'; if (fa) a.scrollTop = a.scrollHeight; }
      const h = box.querySelector('.cl-h .sm'); if (h) h.textContent = ` · call ${c.n} · writing now · ${EV.liveClock((c.seconds || 0) * 1000)} · ${(c.reasoning || '').length.toLocaleString('en-US')} characters of reasoning, ${(c.answer || '').length.toLocaleString('en-US')} of answer so far`;
    }).catch(() => {});
  },
  // a new step named by the harness (now.json) while the records stay the same: the strip, the sentence of the banner and the "Now" card of the work log are
  // drawn again where they stand; nothing else changes and the page does not move
  liveRestage() {
    const now = EV.liveNow(); if (!now) return;
    document.querySelectorAll('#ev .lv-stage').forEach(el => { const t = document.createElement('div'); t.innerHTML = EV.liveStage(now, el.classList.contains('big')); if (t.firstElementChild) el.replaceWith(t.firstElementChild); });
    const bar = document.getElementById('live-bar'); if (bar) { const t = document.createElement('div'); t.innerHTML = EV.liveBanner(); if (t.firstElementChild) bar.replaceWith(t.firstElementChild); }
    const card = document.getElementById('lg-now'); if (card) { const t = document.createElement('div'); t.innerHTML = EV.liveNowCard(Number(card.dataset.turn)); if (t.firstElementChild) card.replaceWith(t.firstElementChild); else card.remove(); }
  },
  // every second: the time in the sentence; every two: has the ledger grown?
  liveTick() {
    const a = EV.liveAge(); if (a != null) document.querySelectorAll('#ev [data-live-t]').forEach(el => { el.textContent = EV.liveClock(a); });
    const L = EV.live, row = (EV.files && EV.files.row) || {}, h = L.head;
    if (EV.off || L.busy || document.hidden || EV.s.view !== 'session' || !row.running || !h || (L.n = (L.n || 0) + 1) % 2) return;
    EV.liveCallTick();
    L.busy = true;
    const now = EV.liveNow(), sid = EV.M && EV.M.id;  // while simulations run the ledger does not grow: the index of the runs does
    if (now && (now.phase === 'sims' || now.phase === 'baseline')) EV.get(`../sessions/${sid}/runs/index.json`).then(t => { if (!EV.M || EV.M.id !== sid) return; if (t == null) { if (EV.tilesTick) EV.tilesTick(now, sid); return; }  // no index yet: the session's first simulations are still running
      EV.files.index = EV_DATA.lines(t); if (EV.tilesTick) EV.tilesTick(now, sid); const el = document.getElementById('live-done'), n = EV.liveDone(); if (el && el.dataset.n !== String(n)) { el.dataset.n = n; el.textContent = `· the harness has collected ${n} of them so far`; } });
    if (sid) EV.json(`../sessions/${sid}/now.json`).then(nw => { if (!EV.M || EV.M.id !== sid || !nw) return; const k = j => j ? [j.turn, j.step, j.about, j.round, j.again, j.at].join('|') : '';
      if (k(nw) !== k(EV.files.now)) { EV.files.now = nw; EV.liveRestage(); } });
    fetch(h.url + '?t=' + Date.now(), { method: 'HEAD', cache: 'no-store' }).then(r => { if (r.ok && r.headers.get('Content-Length') !== h.len && EV.live.head === h) { EV.sig = ''; EV.live.keepUntil = performance.now() + 5000; return EV.load(); } }).catch(() => {}).finally(() => { L.busy = false; });
  },
});
EV.act = Object.assign(EV.act || {}, {
  // the note of a new turn: its button goes to that turn in the notebook (the reader's own click), the cross closes it
  livego(id) { const el = id === 'tiles' ? document.getElementById('live-tiles') || document.getElementById('s-find') : document.querySelector(`#s-notebook .nb-turn[data-turn="${id}"]`) || document.querySelector('#s-notebook .nb-now'); EV.act.liveclose(); if (el) el.scrollIntoView({ block: 'center', behavior: 'smooth' }); },
  liveclose() { clearTimeout(EV.live.noteT); EV.live.note = null; const q = document.getElementById('live-note'); if (q) q.remove(); },
});
if (!EV.off) setInterval(EV.liveTick, 1000);
