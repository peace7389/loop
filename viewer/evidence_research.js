// "How it worked as a researcher": what a researcher does, beside what this session did. Each line is a count the
// page makes from the records by a fixed rule (the rule is on hover), with a word (present, partly, absent) and a link
// to its evidence. The page states no overall verdict: it shows the counts, and a person decides; a reviewer's tick
// and note stand beside each line and are stored with the review (item "rs:<line>"). "Partly" and "absent" are
// findings, not errors: they have no warning colour. A session recorded before a field existed says "not recorded";
// where a line cannot apply (no test failed, an open goal) it says "not applicable", with the reason.
// The rules (EV.research computes them, from the records the replay's step has reached):
//   question    tests whose hypothesis has a `question`, of all tests
//   first       decision rules whose experiment was recorded before every simulation the rule names first ran (a
//               simulation returned from an earlier one first ran when that one did), of all decision rules
//   rival       decision rules that name a rival, of all; and their checks by result, void checks counted apart
//   accepts     failed tests whose verdict is "refuted", of the failed tests
//   course      hypotheses whose `follows_from` names a failed check or a verdict "refuted"
//   beyond      knobs of the brief with more than one value across the designs of the model's experiments, of all knobs
//   repeat      void tests (the check compared a simulation with itself), and simulations returned from earlier ones
//   limits      whether the final report states `holds_when` and `breaks_when`
//   claims      claims of the final report that cite at least one check, of all claims
// With the operator columns on, two more: the scheduling policy beside the first judged hypothesis that names the
// scheduler (its words are matched by EV.SCHED_WORDS), and the sentence about choosing at random that the best-so-far
// chart computes. The same lines are columns of the Compare tab.
// ======================================================================================================
Object.assign(EV, {
  SCHED_WORDS: /schedul|unused|left ?over|spare|borrow|work.?conserving|idle/i,
  RS_DOES: { question: 'Asks a question before testing', first: 'Commits to a prediction first', rival: 'Makes predictions that could fail', accepts: 'Accepts a result against its expectation', course: 'Changes course because of evidence',
             beyond: 'Looks beyond the obvious setting', repeat: 'Does not repeat itself', limits: 'States the limits of its answer', claims: 'Supports each claim', policy: 'Identified the scheduling policy', random: 'Against choosing at random' },
  RS_RULE: { question: 'Counted: the tests whose hypothesis records a question, of all tests.', first: 'Counted: the decision rules whose experiment was recorded before every simulation the rule names first ran (a simulation returned from an earlier one first ran when that one did), of all decision rules. From the records’ timestamps.',
             rival: 'Counted: the decision rules that name a rival, of all decision rules; then their checks by result, void checks apart.', accepts: 'Counted: the failed tests whose verdict is “refuted”, of the failed tests.',
             course: 'Counted: the hypotheses whose “follows from” names a failed check or a verdict “refuted”.', beyond: 'Counted: the knobs of the brief with more than one value across the designs of the model’s experiments, of all knobs.',
             repeat: 'Counted: the tests whose check compared a simulation with itself (void), and the simulations returned from earlier ones. Present: none of either; absent: half the tests or more are void; partly: otherwise.',
             limits: 'Read: whether the final report states “holds when” and “breaks when”.', claims: 'Counted: the claims of the final report that cite at least one check, of all claims.',
             policy: 'Operator-only. The scheduling policy, and the first judged hypothesis whose text or question names the scheduler (the words: scheduler, unused, leftover, spare, borrow, work-conserving, idle). Whether it identified the policy is for a person to judge.',
             random: 'Operator-only. The sentence the best-so-far chart computes from the sweep.' },
  // the word of a line that is "n of m"
  rsWord: (n, of) => (of === 0 ? 'absent' : n === of ? 'present' : n === 0 ? 'absent' : 'partly'),
  research(M, seen, op) {
    seen = seen || (() => true); const e = EV.e, pl = (n, w, many) => `${n} ${n === 1 ? w : many || w + 's'}`, st = id => M.recStep[id] ?? 0;
    const tests = M.tests.filter(T => seen(T.exp)), rules = tests.filter(T => T.rule), chk = T => (T.check && seen(T.check.id) ? T.check : null), ver = T => (T.verdict && seen(T.verdict.id) ? T.verdict : null);
    const tl = T => EV.tlink(T, e(T.hyp)), few = (list, f, n = 6) => list.slice(0, n).map(f).join(', ') + (list.length > n ? `, and ${list.length - n} more` : ''), nr = (key, why) => ({ key, word: 'not recorded', text: `not recorded${why ? ': ' + why : ''}`, n: null, of: null });
    const out = [];
    // 1 · asks a question before testing
    out.push(!M.recs.some(r => r.type === 'hypothesis' && r.body && 'question' in r.body) ? nr('question', 'this session was recorded before hypotheses had a question') : !tests.length ? { key: 'question', word: 'absent', text: 'no test yet', n: 0, of: 0 }
      : (() => { const n = tests.filter(T => M.hypById[T.hyp] && M.hypById[T.hyp].question).length; return { key: 'question', n, of: tests.length, word: EV.rsWord(n, tests.length), text: `${n} of ${pl(tests.length, 'test')} state their question`, links: '<a data-act="goto" data-id="s-find">what it needed to find out</a>' }; })());
    // 2 · commits to a prediction first: the rule's record against the first run of each simulation it names
    const first = s => { const o = s.same_as && M.simById[s.same_as]; return o ? o.ts : s.ts; }, timed = rules.filter(T => T.sims.length && M.expById[T.exp].ts && T.sims.every(first));
    out.push(!rules.length ? { key: 'first', word: 'absent', text: 'no decision rule yet', n: 0, of: 0 } : !timed.length ? nr('first', 'the records carry no times')
      : (() => { const ok = timed.filter(T => T.sims.every(s => first(s) >= M.expById[T.exp].ts)), late = timed.filter(T => !ok.includes(T));
        return { key: 'first', n: ok.length, of: timed.length, word: EV.rsWord(ok.length, timed.length), text: `${ok.length} of ${pl(timed.length, 'decision rule')} written before their simulations${late.length ? `; ${late.length} name${late.length === 1 ? 's' : ''} a simulation that had already run` : ''}`,
          links: `the order of the first test: ${tl(timed[0])}${late.length ? ` · those that name an earlier simulation: ${few(late, tl)}` : ''}` }; })());
    // 3 · makes predictions that could fail
    const rivalRec = M.recs.some(r => r.type === 'experiment' && r.body && (r.body.decision_rules || r.body.rules || []).some(q => 'rival' in q));
    out.push(!rules.length ? { key: 'rival', word: 'absent', text: 'no decision rule yet', n: 0, of: 0 } : !rivalRec ? nr('rival', 'this session was recorded before decision rules named a rival')
      : (() => { const n = rules.filter(T => T.rival).length, cs = rules.map(chk).filter(Boolean), held = cs.filter(c => c.result === 'held').length, failed = rules.filter(T => chk(T) && chk(T).result === 'failed'), voids = cs.filter(c => c.void).length;
        return { key: 'rival', n, of: rules.length, held, failed: failed.length, void: voids, word: EV.rsWord(n, rules.length), text: `${n} of ${rules.length} name a rival; ${held} held, ${failed.length} failed${voids ? `; ${voids} void, counted apart` : ''}`, links: failed.length ? `the tests that failed: ${few(failed, tl)}` : 'no test failed' }; })());
    // 4 · accepts a result against its expectation
    const failed = tests.filter(T => chk(T) && chk(T).result === 'failed');
    out.push(M.old ? nr('accepts', 'this session has no checks by the harness') : !failed.length ? { key: 'accepts', word: 'not applicable', text: 'not applicable: no test failed', n: 0, of: 0 }
      : (() => { const by = {}; failed.forEach(T => { const k = ver(T) ? ver(T).result : 'not judged'; (by[k] = by[k] || []).push(T); }); const n = (by.refuted || []).length, kinds = Object.keys(by);
        return { key: 'accepts', n, of: failed.length, word: EV.rsWord(n, failed.length), text: `${pl(failed.length, 'failed test')}, ${kinds.length === 1 ? `${failed.length === 1 ? '' : failed.length === 2 ? 'both ' : 'all '}${kinds[0] === 'not judged' ? 'not judged' : 'judged ' + kinds[0]}` : kinds.map(k => `${by[k].length} ${k === 'not judged' ? k : 'judged ' + k}`).join(', ')}`, links: few(failed, tl) }; })());
    // 5 · changes course because of evidence
    const hyps = M.hyps.filter(h => seen(h.id)), badIds = new Set([...failed.map(T => chk(T).id), ...M.recs.filter(r => r.type === 'verdict' && r.body.result === 'refuted' && seen(r.id)).map(r => r.id)]);
    out.push(hyps.length && hyps.every(h => h.follows == null) ? nr('course', 'this session was recorded before hypotheses said what they follow from') : !badIds.size ? { key: 'course', word: 'not applicable', text: 'not applicable: no test failed and no hypothesis was refuted', n: 0, of: 0 }
      : (() => { const fol = hyps.filter(h => (h.follows || []).some(id => badIds.has(id)));
        return { key: 'course', n: fol.length, of: null, word: fol.length ? 'present' : 'absent', text: `${fol.length ? pl(fol.length, 'later hypothesis', 'later hypotheses') : 'no later hypothesis'} follow${fol.length === 1 ? 's' : ''} from a failed test or a refuting verdict`, links: fol.length ? few(fol, h => `<a data-act="open" data-t="hyp" data-id="${e(h.id)}">${e(h.id)}</a>`) : '' }; })());
    // 6 · looks beyond the obvious setting
    const kn = M.brief && M.brief.knobs ? Object.keys(M.brief.knobs) : null, designs = M.sims.filter(s => seen(s.id) && (M.expById[s.exp] || {}).by !== 'harness');
    out.push(!kn ? nr('beyond', 'this session has no brief') : (() => { const varied = kn.filter(k => new Set(designs.filter(s => k in s.params).map(s => String(EV.knNum(s.params[k])) === 'NaN' ? String(s.params[k]) : String(EV.knNum(s.params[k])))).size > 1);
      return { key: 'beyond', n: varied.length, of: kn.length, varied, word: EV.rsWord(varied.length, kn.length), text: `varied ${varied.length} of ${pl(kn.length, 'setting')}${varied.length ? ': ' + varied.map(k => EV.label(k, M.brief.knobs[k].meaning)).join(', ') : ''}`, links: '<a data-act="goto" data-id="s-knob|knob">the simulations of each turn, along one setting</a>' }; })());
    // 7 · does not repeat itself
    const voids = tests.filter(T => chk(T) && chk(T).void), back = M.sims.filter(s => s.same_as && seen(s.id));
    out.push(M.old ? nr('repeat', 'this session has no checks by the harness') : { key: 'repeat', n: voids.length, of: tests.length, void: voids.length, returned: back.length, word: !voids.length && !back.length ? 'present' : tests.length && voids.length * 2 >= tests.length ? 'absent' : 'partly',
      text: `${pl(voids.length, 'void test')}; ${pl(back.length, 'simulation')} returned from earlier ones`, links: [voids.length ? `void: ${few(voids, tl)}` : '', back.length ? `returned: ${few(back, s => `<a data-act="open" data-t="sim" data-id="${e(s.id)}">${e(s.id)}</a>`)}` : ''].filter(Boolean).join(' · ') });
    // 8 and 9 · states the limits of its answer; supports each claim
    const rep = M.report && (M.repRec ? seen(M.repRec.id) : true) ? M.report : null, has = v => (Array.isArray(v) ? v.length > 0 : typeof v === 'string' && v.trim() !== ''), toRep = '<a data-act="goto" data-id="s-proposes">what it proposes</a>';
    out.push(!rep ? { key: 'limits', word: 'absent', text: 'no final report', n: 0, of: 2 } : (() => { const h = has(rep.holds_when), b = has(rep.breaks_when);
      return { key: 'limits', n: h + b, of: 2, word: EV.rsWord(h + b, 2), text: h && b ? 'holds when and breaks when are stated' : h ? 'holds when is stated; breaks when is not' : b ? 'breaks when is stated; holds when is not' : 'neither holds when nor breaks when is stated', links: toRep }; })());
    out.push(!rep ? { key: 'claims', word: 'absent', text: 'no final report', n: 0, of: 0 } : !M.claims.length ? { key: 'claims', word: 'absent', text: 'the report states no claims', n: 0, of: 0, links: toRep }
      : (() => { const n = M.claims.filter(q => q.cites.length > 0).length; return { key: 'claims', n, of: M.claims.length, word: EV.rsWord(n, M.claims.length), text: `${n} of ${pl(M.claims.length, 'claim')} cite a check`, links: toRep }; })());
    if (!op) return out;
    // operator-only: the policy beside the first judged hypothesis that names the scheduler; the comparison with choosing at random
    const row = op.row || {}, sch = hyps.filter(h => EV.SCHED_WORDS.test(`${h.text} ${h.question || ''}`) && h.verdict && seen(h.verdict.id)).sort((a, b) => st(a.verdict.id) - st(b.verdict.id))[0], T0 = sch ? tests.find(T => T.hyp === sch.id) : null;
    out.push({ key: 'policy', op: true, word: sch ? 'present' : 'absent', n: sch ? 1 : 0, of: null, hyp: sch ? sch.id : null, text: `the policy was ${EV.policyText(row)} · ${sch ? `the first judged hypothesis about the scheduler: ${e(sch.id)}, ${e(sch.verdict.result)}` : 'not judged from the records'}`,
      links: sch ? `${T0 ? 'the test that decided it: ' + tl(T0) : `<a data-act="open" data-t="hyp" data-id="${e(sch.id)}">${e(sch.id)}</a>`} · “${e(EV.hshort(sch).slice(0, 110))}”` : '' });
    const open = M.brief && M.brief.goal && M.brief.goal.kind === 'open', rnd = open || !op.random ? null : op.random(M), d = rnd && rnd.band ? EV.bestData(M) : null;
    out.push({ key: 'random', op: true, n: null, of: null, word: open ? 'not applicable' : d ? 'present' : 'not recorded', text: open ? 'not applicable: the goal is chosen by the AI' : d ? EV.randomSentence(rnd, d).replace(/<\/?p[^>]*>/g, '').replace(/ id="[^"]*"/g, '') : rnd && rnd.loading ? 'reading the sweep table…' : `not recorded: ${row.score ? 'the sweep table is missing' : 'the session is not scored'}`,
      links: open ? '' : '<a data-act="goto" data-id="s-best|best">best so far</a>' });
    return out;
  },
  researchCard() {
    const M = EV.M, S = EV.s, e = EV.e, lines = EV.research(M, EV.seen, S.op ? { row: EV.files.row, random: EV.files.score ? EV.randomOf : null } : null);
    const row = q => `<tr data-line="${q.key}" data-word="${q.word}"${q.n != null ? ` data-n="${q.n}"` : ''}${q.of != null ? ` data-of="${q.of}"` : ''}${q.op ? ' data-by="operator"' : ''}><td class="rs-does" title="${e(EV.RS_RULE[q.key])}">${q.op ? '<i class="sw"></i>' : ''}${e(EV.RS_DOES[q.key])}</td>
      <td class="rs-did"><span class="rs-text">${q.text}</span>${q.links ? `<div class="sm rs-links">${q.links}</div>` : ''}</td><td class="rs-word"><span class="rs-w" data-w="${q.word.replace(' ', '-')}">${q.word}</span></td><td class="rs-rev noprint">${EV.reviewBox('rs:' + q.key)}</td></tr>`;
    return `<div class="ev-card" id="s-research"><h2>How it worked as a researcher <small>counted by the page from the records; for a person to judge</small></h2><p class="sec-q">Did it work the way a researcher does?</p>
      <table class="rsc"><thead><tr><th>What a researcher does</th><th>What this session did</th><th></th><th class="noprint">Reviewer</th></tr></thead><tbody>${lines.map(row).join('')}</tbody></table>
      <p class="sm">Each count follows a fixed rule, shown when the pointer rests on a line's name. <span class="rs-w" data-w="present">present</span>, <span class="rs-w" data-w="partly">partly</span> and <span class="rs-w" data-w="absent">absent</span> are findings, not errors, and the page gives no overall verdict.${S.op ? ' The last two lines are operator-only.' : ''}</p></div>`;
  },
  // the same lines as columns of the Compare tab: one row per ticked session
  researchCompare(list) {
    const e = EV.e, S = EV.s, keys = Object.keys(EV.RS_DOES).filter(k => S.op || !['policy', 'random'].includes(k)), all = list.map(q => EV.research(q.M, null, S.op ? { row: q.x, random: null } : null));
    const cell = q => (q ? `<td data-line="${q.key}" data-word="${q.word}"${q.n != null ? ` data-n="${q.n}"` : ''}${q.of != null ? ` data-of="${q.of}"` : ''} title="${e(String(q.text).replace(/<[^>]+>/g, ''))}"><span class="rs-w" data-w="${q.word.replace(' ', '-')}">${q.word}</span>${q.n != null ? `<div class="sm">${q.of != null ? `${q.n} of ${q.of}` : q.n}</div>` : ''}</td>` : '<td></td>');
    return `<div class="ev-card" id="cmp-research"><h2>How each worked as a researcher <small>counted by the page from the records; for a person to judge</small></h2><div class="ev-scroll"><table class="rsc"><thead><tr><th>session</th>${keys.map(k => `<th title="${e(EV.RS_RULE[k])}">${e(EV.RS_DOES[k])}</th>`).join('')}</tr></thead>
      <tbody>${list.map((q, i) => `<tr data-s="${e(q.x.id)}"><td><i class="sw" style="background:${EV.color(q.slot)}"></i><b>${e(q.x.id)}</b></td>${keys.map(k => cell(all[i].find(l => l.key === k))).join('')}</tr>`).join('')}</tbody></table></div>
      <p class="sm">The same lines as on each session's page (the comparison with choosing at random is on the session's own page). The rule of a column is on its heading.</p></div>`;
  },
});
