// "Walk me through this session": a guided walk for a first-time reader. One step per section 1 to 6 of the page
// (the setting, the session at a glance, what it needed to find out, the work step by step, what it proposes, how it
// worked as a researcher; a session without a final report has no step for "what it proposes": five steps). Each step
// goes to its section and shows, at the head of that section, one sentence built from the session's own records by a
// fixed rule (no model writes it), with "back", "next" and "leave". The walk changes nothing: leaving it, at any
// step, puts the page back where it was (the same place, the same open item, the same replay step).
// The sentences:
//   1 the setting       how many settings the AI could change and how many were fixed, the limit, what it was not told
//   2 at a glance       turns, hypotheses, simulations, checks held and failed (void apart)
//   3 find out          how many tests, and their verdicts by kind
//   4 the work          the first failed test from which a later hypothesis follows ("this is where it changed course");
//                       else the first failed test; else the first test. What it expected is the first comparison of the
//                       test's decision rule; what it measured is that comparison's left side, from the simulation it names
//   5 what it proposes  the proposed adjustment, the first line of the expected result, the claims and how many cite a check
//   6 as a researcher   how many of the nine lines are present, partly, absent
// ======================================================================================================
Object.assign(EV, {
  WALK: [['s-system', 'The setting'], ['s-made', 'The session at a glance'], ['s-find', 'What it needed to find out'], ['s-notebook', 'The work, step by step'], ['s-proposes', 'What it proposes'], ['s-research', 'How it worked as a researcher']],
  walkSteps() { return EV.WALK.filter(q => q[0] !== 's-proposes' || EV.M.report); },
  // the first comparison of a rule, in words: what was expected, and what was measured on its left side
  walkExpected(T) {
    const tree = EV.readTree(T.rule); let n = tree; while (n && (n[0] === 'and' || n[0] === 'or' || n[0] === 'all')) n = n[0] === 'all' ? n[1] : n[1][0];
    if (!n || n[0] !== 'cmp') return null; const sims = Object.fromEntries(T.sims.map(s => [s.label, s])), one = T.sims.length === 1 ? T.sims[0] : null, val = (name, label) => { const s = sims[label] || (label == null ? one : null); return s && s.metrics ? s.metrics[name] : undefined; };
    const U = EV.readUnit(n[1]) || EV.readUnit(n[3]), a = EV.readValue(n[1], val), b = EV.readValue(n[3], val); if (a == null || b == null) return null;
    const left = n[1][0] === 'val' ? (TH_DATA.PLAIN[n[1][1]] || n[1][1]) : 'the measured side', word = { '>': 'above', '>=': 'at least', '<': 'below', '<=': 'at most', '==': 'equal to' }[n[2]];
    return { left, word, want: EV.readNum(b, U, 4), got: EV.readNum(a, U, 4), a, b };
  },
  walkSay(id) {
    const M = EV.M, e = EV.e, pl = (n, w, many) => `${n} ${n === 1 ? w : many || w + 's'}`, b = M.brief || {};
    if (id === 's-system') { const kn = Object.keys(b.knobs || {}).length, fx = Object.keys(b.system || {}).length, lim = (b.limits || {}).simulations;
      return M.brief ? `The AI could change ${pl(kn, 'setting')}, ${fx} ${fx === 1 ? 'was' : 'were'} fixed, and it had ${lim ?? 'an unrecorded number of'} simulations; the scheduling policy was not told to it.` : 'This session was recorded before briefs existed: its setting is not recorded.'; }
    if (id === 's-made') { const c = EV.glCounts(); return `In ${pl(c.turn, 'turn')} it stated ${pl(c.hyp, 'hypothesis', 'hypotheses')} and ran ${pl(c.sim, 'simulation')}; ${M.old ? 'the harness made no checks then' : `${pl(c.held, 'check')} held and ${c.failed} failed${c.void ? `, and ${c.void} were void` : ''}`}.`; }
    if (id === 's-find') { const by = {}; M.tests.forEach(T => { const k = T.check && T.check.void ? 'void' : T.verdict ? T.verdict.result : 'not judged'; by[k] = (by[k] || 0) + 1; });
      return M.tests.length ? `It put ${pl(M.tests.length, 'question')} to a test: ${['supported', 'refuted', 'inconclusive', 'void', 'not judged'].filter(k => by[k]).map(k => `${by[k]} ${k}`).join(', ')}.` : 'It put no question to a test.'; }
    if (id === 's-notebook') { const failed = M.tests.filter(T => T.check && T.check.result === 'failed'), turned = failed.find(T => EV.followers(T).ids.length), T = turned || failed[0] || M.tests.find(q => q.check) || null, x = T && EV.walkExpected(T);
      const end = !T ? '' : turned ? 'this is where it changed course' : T.check.result === 'failed' ? 'its check failed' : T.check.void ? 'its check was void' : 'its check held';
      return !T ? 'It ran no test that the harness checked.' : x ? `Turn ${T.turn}: it expected ${e(x.left)} ${x.word} ${e(x.want)} and measured ${e(x.got)}; ${end}.` : `Turn ${T.turn}: the first test of ${e(T.hyp)}; ${end}.`; }
    if (id === 's-proposes') { const R = EV.recParts(), X = EV.expRows(M.report), kn = b.knobs || {}, cited = M.claims.filter(q => q.cites.length > 0).length, top = X && X.top[0];
      const adj = !R ? 'nothing' : R.text ? e(R.text) : R.differ.length ? R.differ.map(([k, v]) => `${EV.LABEL[k] || k} ${k in kn ? EV.adjVal(k, kn[k].default) + ' → ' : ''}${EV.adjVal(k, v)}`).join(', ') : 'no change to the settings it started from';
      return `It proposes ${e(adj)}${top ? `, expecting ${e(TH_DATA.PLAIN[top[0]] || top[0])} ${EV.v4(top[0], top[1]).replace(/<[^>]+>/g, '')}` : ''}; ${M.claims.length ? `${cited} of its ${pl(M.claims.length, 'claim')} cite a check` : 'it states no claims'}.`; }
    const lines = EV.research(M), n = w => lines.filter(q => q.word === w).length, other = lines.length - n('present') - n('partly') - n('absent');
    return `Of ${lines.length} things a researcher does, the page counts ${n('present')} as present, ${n('partly')} as partly and ${n('absent')} as absent${other ? `; ${other} could not be counted` : ''}.`;
  },
  // drawn after the page: the box at the head of its section, which is brought into view
  afterWalk() {
    const S = EV.s, w = S.walk; document.querySelectorAll('.walk-on').forEach(el => el.classList.remove('walk-on')); if (!w || !EV.M) return;
    const steps = EV.walkSteps(), i = Math.min(w.i, steps.length - 1), [id, name] = steps[i], sec = document.getElementById(id); if (!sec) return;
    const box = document.createElement('div'); box.className = 'walk noprint'; box.id = 'walk-box'; box.dataset.i = i; box.dataset.of = steps.length; box.dataset.sec = id;
    box.innerHTML = `<div class="walk-n">Walk · step ${i + 1} of ${steps.length} · ${EV.e(name)}</div><p id="walk-say">${EV.walkSay(id)}</p>
      <div class="walk-b"><button data-act="walkgo" data-id="-1"${i ? '' : ' disabled'}>back</button><button data-act="walkgo" data-id="1" class="primary"${i < steps.length - 1 ? '' : ' disabled'}>next</button><button data-act="walkend">leave the walk</button></div>`;
    const after = sec.querySelector(':scope > .sec-q, :scope > summary, :scope > .ev-card > .sec-q') || sec.querySelector('h2'); if (after) after.insertAdjacentElement('afterend', box); else sec.prepend(box);
    sec.classList.add('walk-on'); if (w.moved !== i) { w.moved = i; sec.scrollIntoView({ block: 'start' }); }
  },
});
EV.act = Object.assign(EV.act || {}, {
  // the walk begins at the first section; where the page stood is kept, and comes back when the walk is left
  walk() { const S = EV.s; if (S.walk) return EV.act.walkend(); S.walk = { i: 0, y: window.scrollY, step: S.step, moved: null }; S.step = null; EV.draw(); },
  walkgo(d) { const w = EV.s.walk; if (!w) return; w.i = Math.max(0, Math.min(EV.walkSteps().length - 1, w.i + Number(d))); EV.draw(); },
  walkend() { const S = EV.s, w = S.walk; if (!w) return; S.walk = null; S.step = w.step; EV.draw(); window.scrollTo(0, w.y); },
});
document.addEventListener('keydown', ev => { if (ev.key === 'Escape' && EV.s.walk) EV.act.walkend(); });
