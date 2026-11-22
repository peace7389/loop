"""Stage 3 of the coherence audit (2026-11-22), the page, part a (viewer/ in the review branch) and the harness side of item 34:
27 notes that are not refusals; 28 the calls card refreshes while a session runs; 29 the harness's rounds as the harness's; 30 old sessions' test
reviews (no gate); 32 the banner and the Now card per arm; 33 continued replies and a re-asked ruling in the live view, every reply's observations;
34 one shape of a call's step, and the objection's own step; 36 who wrote a note. Usage: s3_page_a.py WT_DIR"""
import sys
from pathlib import Path
W = Path(sys.argv[1])
def rep(f, a, b, n=1):
    p = W / f; s = p.read_text(); assert s.count(a) == n, (f, a[:100], s.count(a)); p.write_text(s.replace(a, b))

# ---- 34, harness: live_call.json keeps the step as calls.jsonl does; the objection's call names its step
rep("harness/loop.py", '''    LIVE["call"] = {"n": CALLS["n"] + 1, "turn": CALLS["turn"], "agent": agent, **(CALLS.get("step") or {}), "started": time.strftime("%Y-%m-%dT%H:%M:%S"), "t0": t0, "reasoning": "", "answer": ""}''',
    '''    LIVE["call"] = {"n": CALLS["n"] + 1, "turn": CALLS["turn"], "agent": agent, "step": CALLS.get("step"), "started": time.strftime("%Y-%m-%dT%H:%M:%S"), "t0": t0, "reasoning": "", "answer": ""}   # step: as calls.jsonl has it (the coherence audit, 2026-11-22: it was spread into the call)''')
rep("harness/loop.py", '''                try:
                    again, saw = answer_objection(model, brief, ledger, was, o["because"])''',
    '''                try:
                    stage("objection", was["body"]["for"])   # its own step (the coherence audit, 2026-11-22: its call carried the step before it)
                    again, saw = answer_objection(model, brief, ledger, was, o["because"])''')
rep("harness/loop.py", '''    ruling (the supervisor rules on a test), look (the supervisor looks at results with no ruling for findings). Never stops the session."""''',
    '''    ruling (the supervisor rules on a test), objection (the supervisor looks again at a ruling the researcher objected to), look (the supervisor looks
    at results with no ruling for findings). Never stops the session."""''')

# ---- 27: a note on a refused part, and one on an accepted part
rep("viewer/evidence_turns.js", "case 'note': return r.by === 'model' ? { what: 'observations', says: T(b.observations || b.text), ground: [] } : b.part ? {",
    "case 'note': return r.by === 'model' ? { what: 'observations', says: T(b.observations || b.text), ground: [] } : EV_DATA.refusal(r) ? {")
# ---- 36: who wrote a record named by a letter, from the record itself; what a note says
rep("viewer/evidence_words.js", "const L = (/^[A-Z]+/.exec(name) || [''])[0], s = EV.ID_SAYS[L] || [r.type, '', ''], rb = r.body || {}, who = { model: 'the AI', harness: 'the harness', simulator: 'ns-3' }[s[2]];",
    "const L = (/^[A-Z]+/.exec(name) || [''])[0], s0 = EV.ID_SAYS[L] || [r.type, '', ''], rb = r.body || {}, s = [s0[0], s0[1], EV_DATA.by(r) || s0[2]], who = { model: 'the AI', harness: 'the harness', simulator: 'ns-3', supervisor: 'the supervisor' }[s[2]];   // who: the record's own author (the coherence audit, 2026-11-22: a note was always the harness's)")
rep("viewer/evidence_words.js", "txt = r.type === 'note' ? (rb.part ? `It refused the part “${rb.part}” of the AI’s answer: ${rb.reason || rb.text || 'no reason recorded'}` : rb.text || rb.reason || rb.error || '')",
    "txt = r.type === 'note' ? (EV_DATA.refusal(r) ? `It refused the part “${rb.part}” of the AI’s answer: ${rb.reason || rb.text || 'no reason recorded'}` : rb.observations || rb.text || rb.reason || rb.error || '')")

# ---- 29: the harness's rounds; 30: old sessions' test reviews; reviews keep their author
rep("viewer/evidence_data.js", "const reviews = of('review').map(r => ({ id: r.id, turn: r.turn, ...r.body })),", "const reviews = of('review').map(r => ({ id: r.id, turn: r.turn, by: r.by, ...r.body })),")
rep("viewer/evidence_data.js", "const g0 = rs.filter(r => r.type === 'review' && r.body.gate === 'ground'), g1 = rs.filter(r => r.type === 'review' && r.body.gate !== 'ground');",
    "const g0 = rs.filter(r => r.type === 'review' && r.body.gate === 'ground'), g1 = rs.filter(r => r.type === 'review' && r.body.gate !== 'ground' && r.by !== 'harness'), gh = rs.filter(r => r.type === 'review' && r.body.gate !== 'ground' && r.by === 'harness');   // gh: rounds the harness refused with its own checks (the coherence audit, 2026-11-22: drawn as the supervisor's)")
rep("viewer/evidence_data.js", "${r.body.for} ${r.body.decision === 'approved' ? 'approved' : r.body.decision === 'sent_back' ? 'sent back' : 'run, it still objects'}`).join(', '), open: { t: 'log', turn: n } }, g1.map(r => r.id));",
    "${r.body.for} ${r.body.decision === 'approved' ? 'approved' : r.body.decision === 'sent_back' ? 'sent back' : r.body.decision === 'dropped' ? 'refused in the last round' : 'run, it still objects'}`).join(', '), open: { t: 'log', turn: n } }, g1.map(r => r.id));\n"
    "        if (gh.length) push({ turn: n, lane: 'harness', kind: 'refused', warn: true, label: 'the harness refuses a repaired test with its own checks: ' + gh.map(r => `${r.body.for} round ${r.body.round || '?'} ${r.body.decision === 'not_run' ? '(not run)' : '(sent back)'}`).join(', '), open: { t: 'log', turn: n } }, gh.map(r => r.id));")
rep("viewer/evidence_notebook.js", "g1 = (M.reviews || []).filter(r => r.gate !== 'ground'),", "g1 = (M.reviews || []).filter(r => r.gate !== 'ground' && r.by !== 'harness'),   // the harness's own refusals of a repair are not the supervisor's review (the coherence audit, 2026-11-22)\n          ")
rep("viewer/evidence_test.js", "const DEC = { approved: 'approved', sent_back: 'sent back', contested: 'contested: run all the same', dropped: 'not approved after the last round' };",
    "const DEC = { approved: 'approved', sent_back: 'sent back', contested: 'contested: run all the same', dropped: 'not approved after the last round', not_run: 'not run: the last repair could not be used' };")
rep("viewer/evidence_test.js", "if (r.type === 'review' && b.gate === 'design' && b.for === h.id) steps.push(",
    "if (r.type === 'review' && (b.gate === 'design' || (!b.gate && b.for)) && b.for === h.id) steps.push(   // no gate: a test review of a session before gates were named (s047, s050, s051; the coherence audit, 2026-11-22)\n        ")

# ---- 33: every reply's observations in a turn
rep("viewer/evidence_data.js", '''      const withObs = rs.find(r => r.body && r.body.observations && ['verdict', 'drop', 'hypothesis', 'experiment', 'report', 'note'].includes(r.type));
      t.observations = withObs ? withObs.body.observations : null;''',
    '''      // what the researcher said it read: one text for each of its replies in the turn (the coherence audit, 2026-11-22: a continued reply's were dropped)
      t.obsList = [...new Set(rs.filter(r => r.body && r.body.observations && ['verdict', 'drop', 'hypothesis', 'experiment', 'report', 'note', 'why', 'objection', 'rethink'].includes(r.type)).map(r => String(r.body.observations)))];
      t.observations = t.obsList.length ? t.obsList.join(' ') : null;''')
rep("viewer/evidence_cards.js", "const why = [t.observations ? `<p><b>observations</b> ${e(t.observations)}</p>${EV.numCheck(t.observations, EV.simsOfTurn(n - 1))}`",
    "const why = [t.observations ? `${(t.obsList || [t.observations]).map((o, i, all) => `<p><b>observations${all.length > 1 ? `, reply ${i + 1}` : ''}</b> ${e(o)}</p>`).join('')}${EV.numCheck(t.observations, EV.simsOfTurn(n - 1))}`")

# ---- 33: the live view during a continued reply, or a first reply after a re-asked ruling
rep("viewer/evidence_live.js", "    if (last.type === 'turn' || (mine && nw.step === 'reply' && nw.again && EV.live.tries < 2)) return { phase: 'reply', turn: last.turn, mode, again: EV.live.tries > 0 || !!(mine && nw.again) };",
    "    // a reply begun after the newest record (a continued reply of the turn, or the first after a ruling asked for again) is being written (the coherence audit, 2026-11-22: it read \"preparing the next turn\")\n"
    "    const begun = mine && nw.step === 'reply' && last.ts && nw.at && last.ts <= nw.at;\n"
    "    if (last.type === 'turn' || begun || (mine && nw.step === 'reply' && nw.again && EV.live.tries < 2)) return { phase: 'reply', turn: last.turn, mode, again: EV.live.tries > 0 || !!(mine && nw.again), cont: mine && nw.step === 'reply' && (nw.round || 1) > 1 ? nw.round : null };")
rep("viewer/evidence_live.js", "      : now.phase === 'reply' ? `${t}the researcher is writing its reply${now.again ? ' again (its first reply could not be used)' : ''}.`",
    "      : now.phase === 'reply' ? `${t}the researcher is writing its reply${now.cont ? ` (reply ${now.cont} of this turn: what it asked for is answered)` : ''}${now.again ? ' again (its first reply could not be used)' : ''}.`")
# ---- 32: what a reply may bring, and what waits, in the arm of the session
rep("viewer/evidence_live.js", "  liveMay: now => (now.phase !== 'reply' ? '' : now.mode === 'report' ? 'This is the last turn: only the final report is accepted.' : now.mode === 'budget' ? 'This is the last turn, the simulations are used up: it may judge earlier tests, and the final report is due.' : 'It may judge earlier tests, state a new hypothesis, set up a new test, or give its final report.'),",
    "  liveMay: now => { const arm = ((EV.M && EV.M.meta && EV.M.meta.flags) || {}).arm || 'hypotheses';   // in the session's arm (the coherence audit, 2026-11-22: it was the single-AI arm's)\n"
    "    return now.phase !== 'reply' ? '' : now.mode === 'report' ? 'This is the last turn: only the final report is accepted.'\n"
    "      : now.mode === 'budget' ? (arm === 'hypotheses' ? 'This is the last turn, the simulations are used up: it may judge earlier tests, and the final report is due.' : arm === 'supervised' ? 'This is the last turn, the simulations are used up: the final report is due (the rulings are the supervisor’s).' : 'This is the last turn, the simulations are used up: the final report is due.')\n"
    "      : arm === 'supervised' ? 'It may read results, state guesses and hypotheses, set up a test, object to a ruling, or give its final report.' : arm === 'plain' ? 'It may ask for information, set up an experiment, or give its final report.'\n"
    "      : 'It may judge earlier tests, state a new hypothesis, set up a new test, or give its final report.'; },")
rep("viewer/evidence_live.js", "    return wrap('model', `the researcher is writing its reply${now.again ? ' again' : ''}`, [",
    "    const arm = ((M.meta && M.meta.flags) || {}).arm || 'hypotheses';\n"
    "    return wrap('model', `the researcher is writing its reply${now.cont ? ` (reply ${now.cont} of this turn)` : ''}${now.again ? ' again' : ''}`, [")
rep("viewer/evidence_live.js", "      ['Waiting for its verdict', `<span data-wait=\"${e(wait.map(h => h.id).join(','))}\">${wait.length ? `${wait.map(h => EV.link(h.id)).join(', ')} <span class=\"sm\">· checked by the harness, not judged by the AI yet</span>` : 'no hypothesis: none has a checked decision rule and no verdict'}</span>`, 'wait'],",
    "      arm === 'plain' ? null : [arm === 'supervised' ? 'Waiting for a ruling' : 'Waiting for its verdict', `<span data-wait=\"${e(wait.map(h => h.id).join(','))}\">${wait.length ? `${wait.map(h => EV.link(h.id)).join(', ')} <span class=\"sm\">· checked by the harness, ${arm === 'supervised' ? 'not ruled on by the supervisor yet' : 'not judged by the AI yet'}</span>` : `no hypothesis: none has a checked decision rule and no ${arm === 'supervised' ? 'ruling' : 'verdict'}`}</span>`, 'wait'],")
rep("viewer/evidence_live.js", "      ['While it writes', 'nothing of the reply can be shown: it arrives whole. When it is there, this card says what it decided and why.', 'whole']]);",
    "      ['While it writes', 'nothing of the reply can be shown: it arrives whole. When it is there, this card says what it decided and why.', 'whole']].filter(Boolean));")
# ---- 34: one shape of a call's step; the objection's step; 28: the calls card refreshes while the session runs
rep("viewer/evidence_live.js", "  LIVE_AGENT_STEPS: ['judge', 'ground', 'restate', 'design', 'repair', 'ruling', 'look'],", "  LIVE_AGENT_STEPS: ['judge', 'ground', 'restate', 'design', 'repair', 'ruling', 'objection', 'look'],")
rep("viewer/evidence_live.js", "['judge', 'ground', 'design', 'ruling', 'look'].includes(p) ? 'supervisor' : 'harness'),", "['judge', 'ground', 'design', 'ruling', 'objection', 'look'].includes(p) ? 'supervisor' : 'harness'),")
rep("viewer/evidence_live.js", "      : now.phase === 'ruling' ? `${t}the supervisor rules on ${e(now.about || 'each test')}: what its checks mean.`",
    "      : now.phase === 'ruling' ? `${t}the supervisor rules on ${e(now.about || 'each test')}: what its checks mean.`\n"
    "      : now.phase === 'objection' ? `${t}the supervisor looks again at its ruling on ${e(now.about || 'a hypothesis')}: the researcher objected to it.`")
rep("viewer/evidence_live.js", "design: hid && ['design', 'repair'].includes(now.phase) ? ['hyp', hid] : null, ruling: hid && now.phase === 'ruling' ? ['hyp', hid] : null,",
    "design: hid && ['design', 'repair'].includes(now.phase) ? ['hyp', hid] : null, ruling: hid && ['ruling', 'objection'].includes(now.phase) ? ['hyp', hid] : null,")
rep("viewer/evidence_live.js", "'The supervisor rules on each checked test: what its checks mean', ['ruling']]] : [])",
    "'The supervisor rules on each checked test: what its checks mean; it looks again at a ruling the researcher objects to', ['ruling', 'objection']]] : [])")
rep("viewer/evidence_live.js", "ruling: ['ruling'], look: ['look'] },", "ruling: ['ruling', 'objection'], look: ['look'] },")
rep("viewer/evidence_live.js", "ruling: 'ruling', look: 'look for findings', judge: 'link check' },", "ruling: 'ruling', objection: 'second look after an objection', look: 'look for findings', judge: 'link check' },")
rep("viewer/evidence_live.js", "    if (c.step && c.step.step) return c.step.step;",
    "    if (c.step) return typeof c.step === 'string' ? c.step : c.step.step;   // calls.jsonl, and live_call.json since stage 3 (2026-11-22), keep {step, about, round, by}; the held build of 2026-11-22 spread it into the call")
rep("viewer/evidence_live.js", "    return u.includes(\"THE HARNESS'S CHECKS (facts)\") ? 'ruling'",
    "    return u.includes('THE RESEARCHER OBJECTS') ? 'objection' : u.includes(\"THE HARNESS'S CHECKS (facts)\") ? 'ruling'")
rep("viewer/evidence_live.js", "    try { const r = await fetch(`../api/agents?session=${encodeURIComponent(sid)}`, { cache: 'no-store' }); const j = r.ok ? await r.json() : null; L.calls = { sid, list: (j && j.calls) || [], at: Date.now() }; }\n"
    "    catch (x) { L.calls = { sid, list: [], at: Date.now(), err: true }; }\n"
    "    L.callsBusy = false; const sel = EV.s.sel; if (sel && sel.t === 'calls' && EV.M && EV.M.id === sid) EV.draw();",
    "    const was = L.calls && L.calls.sid === sid ? L.calls.list : null, mark = l => (l ? `${l.length}|${(l[l.length - 1] || {}).n}` : '');\n"
    "    try { const r = await fetch(`../api/agents?session=${encodeURIComponent(sid)}`, { cache: 'no-store' }); const j = r.ok ? await r.json() : null; L.calls = { sid, list: (j && j.calls) || [], at: Date.now() }; }\n"
    "    catch (x) { L.calls = { sid, list: [], at: Date.now(), err: true }; }\n"
    "    L.callsBusy = false; const sel = EV.s.sel; if (sel && sel.t === 'calls' && EV.M && EV.M.id === sid && mark(was) !== mark(L.calls.list)) EV.draw();   // drawn again only when a call was added: a reload that brings nothing new leaves the page as it is")
rep("viewer/evidence_live.js", "    fetch(`../sessions/${M.id}/live_call.json?t=${Date.now()}`, { cache: 'no-store' }).then(r => (r.ok ? r.json() : null)).then(c => {\n"
    "      if (!c || !EV.M || EV.M.id !== M.id) return; const was = EV.live.liveCall && EV.live.liveCall.c; EV.live.liveCall = { sid: M.id, c };",
    "    fetch(`../sessions/${M.id}/live_call.json?t=${Date.now()}`, { cache: 'no-store' }).then(r => (r.ok ? r.json() : null)).then(c => {\n"
    "      // a harness that writes no live_call.json (the one deployed before stage 3): the list of calls is read again every 10 s while the card is open (the coherence audit, 2026-11-22: it never refreshed)\n"
    "      if (!c) { const L = EV.live; if (EV.M && EV.M.id === M.id && L.calls && L.calls.sid === M.id && Date.now() - L.calls.at > 10000) EV.callsLoad(M.id); return; }\n"
    "      if (!EV.M || EV.M.id !== M.id) return; if (typeof c.step === 'string') c.step = { step: c.step, about: c.about || null, round: c.round || null, by: c.by || null };   // the held build's flat step\n"
    "      const was = EV.live.liveCall && EV.live.liveCall.c; EV.live.liveCall = { sid: M.id, c };")
rep("viewer/evidence_live.js", "here = lv && !lv.done && lv.turn === turn && steps.includes(lv.step) && !(list || []).some(c => c.n === lv.n);",
    "here = lv && !lv.done && lv.turn === turn && steps.includes(EV.callStep(lv)) && !(list || []).some(c => c.n === lv.n);")
print("patched")
