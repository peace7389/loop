// EV_DATA: a session's files read into the structure the evidence page draws (see ~/EVIDENCE_VIEW.md).
// It reads ledger.jsonl WITHOUT its draft records (they are dropped when the file is parsed; drafts.jsonl is never
// requested), session.json, report.json and the session's runs/index.json. Nothing is filled in: a field a session
// did not record stays null and the page says "not recorded".
// ======================================================================================================
const EV_DEF = {  // the definitions, word for word; shown on hover wherever the term appears
  'Brief': 'The assignment a person writes before a session: fixed settings, knobs, goal and limits.',
  'Session': 'One complete attempt by the model at one brief, from an empty record to its final report.',
  'Turn': 'One exchange: the harness shows the record so far, and the model answers.',
  'Hypothesis': 'The model\'s claim about how the system behaves.',
  'Experiment': 'The batch of simulations the model plans in one turn, to test hypotheses or to explore a question.',
  'Test': 'One hypothesis put to one decision rule, using some of an experiment\'s simulations.',
  'Decision rule': 'The numeric condition, stated before the simulations, that decides whether a hypothesis is accepted or rejected.',
  'Rival': 'A competing explanation that the decision rule would rule out.',
  'Simulation': 'One run of the network simulator with one set of knob values.',
  'Check': 'The harness applying a decision rule to the measured numbers: held or failed.',
  'Verdict': 'The model\'s judgment of a hypothesis after its check: supported, refuted or inconclusive.',
  'Final report': 'The model\'s answer: recommended settings, expected result, explanation, when it holds, when it breaks, and evidence for each claim.',
  'Operator': 'The person running the project; operator-only items are never shown to the model.',
  'Scheduling policy': 'How the sender\'s scheduler divides the link between the two flows; chosen by the operator and not told to the model.',
};
const EV_ICON = { brief: '▤', hypothesis: '', drop: '✂', experiment: '▣', test: '⚗', simulation: '', evidence: '≡', check: '', verdict: '⚖', report: '',
                  note: '✎', malformed: '', request: '?', result: '↩', turn: '↻' };  // one fixed symbol per record type; those left empty here are drawn marks, set in evidence_marks.js
const EV_BY = { hypothesis: 'model', drop: 'model', experiment: 'model', verdict: 'model', report: 'model', request: 'model', simulation: 'simulator',
                evidence: 'harness', check: 'harness', malformed: 'harness', note: 'harness', result: 'harness', turn: 'harness' };

const EV_DATA = {
  lines(text) {  // a .jsonl file as records; draft records are dropped here and never kept
    return String(text || '').split('\n').filter(Boolean).map(l => { try { return JSON.parse(l); } catch (e) { return null; } })
      .filter(r => r && r.type !== 'draft' && r.type !== 'scratch');
  },
  by(r) { const b = r.body || {}; return r.by || (r.type === 'note' ? (b.requests || b.text === 'model declared done' ? 'model' : 'harness') : EV_BY[r.type] || 'model'); },
  num(o) { return Object.fromEntries(Object.entries(o || {}).filter(([, v]) => typeof v === 'number')); },
  labels(rule) { return [...new Set([...String(rule || '').matchAll(/[A-Za-z_][A-Za-z0-9_]*@([A-Za-z0-9_]+)/g)].map(m => m[1]))]; },  // the labels a decision rule names, each once

  build(f) {
    const D = EV_DATA, recs = f.ledger || [], byId = Object.fromEntries(recs.map(r => [r.id, r])), pos = Object.fromEntries(recs.map((r, i) => [r.id, i]));
    const of = t => recs.filter(r => r.type === t), meta = f.session || null, brief = meta && meta.given ? meta.given : null;
    const multi = recs.some(r => r.type === 'simulation');  // the format with experiments of several simulations
    const ended = !!(meta && meta.how) || recs.some(r => r.type === 'report') || !f.running;
    recs.forEach(r => { if (r.turn == null) r.turn = 0; });  // records of the first session that carry no turn number: drawn before the first turn

    // ---- simulations and experiments
    let sims = [], exps = [];
    if (multi) {
      sims = of('simulation').map(r => ({ id: r.id, label: r.body.label, run: r.body.run_id, params: r.body.params || {}, metrics: r.body.metrics || null, error: r.body.error || null,
                                          same_as: r.body.same_as || null, exp: r.parent, ts: r.ts, turn: r.turn }));
      exps = of('experiment').map(r => { const b = r.body, own = sims.filter(s => s.exp === r.id);
        return { id: r.id, turn: r.turn, ts: r.ts, by: D.by(r), kind: b.kind, tests: b.tests || [], question: b.question || '', varied: b.varied || [], control: b.control || null,
                 runs: b.runs || [], rules: (b.decision_rules || b.rules || []).map(q => ({ for: q.for, rule: q.decision_rule || q.rule, rival: q.rival || null, rival_predicts: q.rival_predicts || null })),
                 sims: own, evidence: recs.find(e => e.type === 'evidence' && e.parent === r.id) || null,
                 // a void check: its decision rule names two or more labels of which at least two are the same simulation (the same run), so
                 // it compared a simulation with itself. Its result here is "void" (what the harness recorded stays in "recorded"): it
                 // counts neither as held nor as failed anywhere on the page. harness/session_figures.py counts the same for Home.
                 checks: recs.filter(c => c.type === 'check' && c.parent === r.id).map(c => { const rule = c.body.decision_rule || c.body.rule, ls = D.labels(rule), runs = ls.map(l => (own.find(s => s.label === l) || {}).run).filter(Boolean),
                   isVoid = ls.length >= 2 && new Set(runs).size < runs.length, same = isVoid ? ls.filter(l => { const q = (own.find(s => s.label === l) || {}).run; return q && runs.indexOf(q) !== runs.lastIndexOf(q); }) : [];
                   return { id: c.id, for: c.body.for, rule, numbers: c.body.with_numbers, result: isVoid ? 'void' : c.body.result, recorded: c.body.result, void: isVoid, same,
                            rival: c.body.rival || null, rival_predicts: c.body.rival_predicts || null, ts: c.ts }; }) }; });
    } else {  // the first format: one simulation per experiment, the measurement in the evidence record, no check by the harness
      of('evidence').forEach((e, i) => { const x = byId[e.parent] || null, xb = (x && x.body) || {}, h = x && byId[x.parent] && byId[x.parent].type === 'hypothesis' ? x.parent : null;
        const s = { id: e.id, label: 'run', run: e.body.run_id, params: xb.params || {}, metrics: e.body.error ? null : D.num(e.body), error: e.body.error || null, same_as: null, exp: x ? x.id : 'X0', ts: e.ts, turn: e.turn };
        sims.push(s);
        exps.push({ id: x ? x.id : 'X0', turn: e.turn, ts: x ? x.ts : e.ts, by: x ? 'model' : 'harness', kind: h ? 'test' : 'explore', tests: h ? [h] : [], question: e.body.note || '', varied: [], control: null,
                    runs: [{ label: 'run', params: xb.params || {}, clamped: xb.clamped || {} }], rules: h && (xb.pass_if || e.body.pass_if) ? [{ for: h, rule: xb.pass_if || e.body.pass_if, rival: null, rival_predicts: null }] : [],
                    sims: [s], evidence: e, checks: [], old: true }); });
    }
    const expById = Object.fromEntries(exps.map(x => [x.id, x])), simById = Object.fromEntries(sims.map(s => [s.id, s]));

    // ---- hypotheses, with what they follow from and how they ended
    const checks = exps.flatMap(x => x.checks.map(c => ({ ...c, exp: x.id })));
    const hyps = of('hypothesis').map(r => { const v = recs.filter(q => q.type === 'verdict' && q.body.for === r.id).pop() || null, d = recs.find(q => q.type === 'drop' && q.body.for === r.id) || null;
      const own = checks.filter(c => c.for === r.id), tested = exps.filter(x => x.tests.includes(r.id)).map(x => x.id);
      const state = v ? v.body.result : d ? 'dropped' : ended ? 'ended without a verdict' : 'open';
      return { id: r.id, turn: r.turn, ts: r.ts, text: String(r.body.text || '').replace(/^\s*H\d+\s*:\s*/, ''), prediction: r.body.prediction || null,
               question: typeof r.body.question === 'string' && r.body.question.trim() ? r.body.question.trim() : null,  // the hypothesis as one plain question; null: not recorded (sessions before this field)
               follows: Array.isArray(r.body.follows_from) ? r.body.follows_from : null,  // null: not recorded (sessions before this field)
               state, verdict: v && { id: v.id, turn: v.turn, ts: v.ts, result: v.body.result, because: v.body.because, next: v.body.next, observations: v.body.observations || null,
                                      voidOnly: (() => { const cs = own.filter(c => pos[c.id] < pos[v.id]), last = cs.filter(c => c.exp === (cs[cs.length - 1] || {}).exp); return last.length > 0 && last.every(c => c.void); })() },
               drop: d && { id: d.id, turn: d.turn, why: d.body.why }, checks: own, exps: tested }; });
    const hypById = Object.fromEntries(hyps.map(h => [h.id, h]));
    // ---- the tests: one hypothesis put to one decision rule. Nothing records a test as such: its simulations are the
    // labels after @ in its decision rule (one simulation in the experiment: that one), its check is the harness's check
    // of that rule, its verdict the hypothesis's verdict when no later test of the same hypothesis came before it.
    const tests = exps.flatMap(x => { const nth = {};
      const made = x.rules.map(r => { const labels = D.labels(r.rule);
        const n = nth[r.for] = (nth[r.for] || 0) + 1, same = x.checks.filter(c => c.for === r.for);
        return { id: `${x.id}.${r.for}${n > 1 ? '.' + n : ''}`, exp: x.id, turn: x.turn, ts: x.ts, hyp: r.for, rule: r.rule, rival: r.rival, rival_predicts: r.rival_predicts, labels,
                 sims: labels.length ? labels.map(l => x.sims.find(s => s.label === l)).filter(Boolean) : x.sims.length === 1 ? x.sims.slice() : [],
                 missing: labels.filter(l => !x.sims.some(s => s.label === l)), control: x.control && labels.includes(x.control) ? x.control : null,
                 check: same.find(c => c.rule === r.rule) || same[n - 1] || null }; });
      return made.concat(x.tests.filter(h => !x.rules.some(r => r.for === h)).map(h => ({ id: `${x.id}.${h}`, exp: x.id, turn: x.turn, ts: x.ts, hyp: h, rule: null, rival: null, rival_predicts: null,
                                                                                         labels: [], sims: [], missing: [], control: null, check: null }))); });
    tests.forEach(t => { const v = hypById[t.hyp] && hypById[t.hyp].verdict;
      t.verdict = v && v.turn > t.turn && !tests.some(q => q.hyp === t.hyp && q.turn > t.turn && q.turn < v.turn) ? v : null; });
    hyps.forEach(h => { h.tests = tests.filter(t => t.hyp === h.id).map(t => t.id); });
    const testById = Object.fromEntries(tests.map(t => [t.id, t]));
    // the hypothesis an earlier record belongs to (for the arrows of the hypothesis map), and what kind of record it is
    const source = id => { const r = byId[id]; if (!r) return null;
      if (r.type === 'verdict') return { hyp: r.body.for, label: r.body.result };
      if (r.type === 'check') return { hyp: r.body.for, label: 'check ' + r.body.result };
      const x = r.type === 'evidence' ? expById[r.body.experiment || (multi ? r.parent : (byId[r.parent] || {}).id)] : r.type === 'simulation' ? expById[r.parent] : null;
      return { hyp: x && x.tests[0] ? x.tests[0] : null, label: 'observation' }; };

    // ---- the final report and its claims
    const repRec = of('report').pop() || null, report = repRec ? repRec.body : f.report || null;
    const claims = ((report && report.claims) || []).map((c, i) => { const ids = c.evidence || [];
      const cited = ids.flatMap(id => { const r = byId[id]; if (!r) return [];
        if (r.type === 'check') return checks.filter(q => q.id === id);
        if (r.type === 'verdict') return checks.filter(q => q.for === r.body.for);
        return []; });  // an evidence table or a simulation is evidence without a check of its own
      const hs = [...new Set(ids.map(id => (source(id) || {}).hyp).filter(Boolean))];
      const state = !ids.length ? 'none' : cited.some(q => q.result === 'failed') ? 'failed' : cited.some(q => q.result === 'held') ? 'held' : 'unchecked';
      // role (below): what the claim does in the argument (supports, background, limits); null: not recorded (reports before this field).
      // the checks the claim cites itself, in the order cited, and what kind of claim that makes it. A failed check is a
      // result, not a fault: a claim can rest on a refutation. Only a claim with no evidence at all is a warning.
      const cites = ids.filter(id => byId[id] && byId[id].type === 'check').map(id => ({ id, result: (checks.find(q => q.id === id) || { result: byId[id].body.result }).result })), hd = cites.some(q => q.result === 'held'), fl = cites.some(q => q.result === 'failed');
      const kind = !ids.length ? 'none' : !cites.length ? 'nocheck' : hd && fl ? 'both' : fl ? 'failed' : hd ? 'held' : 'nocheck';
      return { n: i + 1, text: c.text, role: ['supports', 'background', 'limits'].includes(c.role) ? c.role : null, evidence: ids, cites, kind, hyps: hs, tests: [...new Set(ids.flatMap(id => tests.filter(t => (t.check && t.check.id === id) || (t.verdict && t.verdict.id === id)).map(t => t.id)))], exps: [...new Set(cited.map(q => q.exp).concat(ids.map(id => { const r = byId[id] || {}; return r.type === 'evidence' ? (r.body.experiment || (expById[r.parent] ? r.parent : (byId[r.parent] || {}).id)) : r.type === 'simulation' ? r.parent : null; }).filter(Boolean)))], state }; });

    // ---- the turns, and the steps of the session flow (one box each, in the order they were recorded)
    const turnNos = [...new Set(recs.map(r => r.turn))].sort((a, b) => a - b), steps = [], recStep = {};
    const push = (s, ids) => { s.k = steps.length; steps.push(s); (ids || []).forEach(id => { if (!(id in recStep)) recStep[id] = s.k; }); return s; };
    const turns = turnNos.map(n => { const rs = recs.filter(r => r.turn === n), T = rs.find(r => r.type === 'turn') || null;
      const t = { n, rec: T, left: T ? T.body.simulations_left : null, open: T ? T.body.open_hypotheses : null, added: T ? T.body.added : null, last: T ? T.body.last_turn : null,
                  verdicts: rs.filter(r => r.type === 'verdict'), drops: rs.filter(r => r.type === 'drop'), hyps: rs.filter(r => r.type === 'hypothesis').map(r => hypById[r.id]),
                  exp: exps.find(x => x.turn === n && (multi ? byId[x.id] && byId[x.id].turn === n : true)) || null, report: rs.find(r => r.type === 'report') || null,
                  requests: rs.filter(r => r.type === 'request'), malformed: rs.filter(r => r.type === 'malformed'),
                  refusals: rs.filter(r => r.type === 'note' && r.body.part), notes: rs.filter(r => r.type === 'note' && !r.body.part), observations: null, steps: [] };
      const withObs = rs.find(r => r.body && r.body.observations && ['verdict', 'drop', 'hypothesis', 'experiment', 'report', 'note'].includes(r.type));
      t.observations = withObs ? withObs.body.observations : null;
      const first = steps.length;
      if (n === 0) {
        push({ turn: 0, lane: 'harness', kind: 'start', label: 'brief and baseline shown', open: { t: 'brief' } }, rs.filter(r => r.type === 'experiment').map(r => r.id));
        if (t.exp) push({ turn: 0, lane: 'simulator', kind: 'sims', exp: t.exp.id, label: `${t.exp.sims.length} simulation${t.exp.sims.length === 1 ? '' : 's'}`, sims: t.exp.sims, open: { t: 'exp', id: t.exp.id } }, rs.map(r => r.id));
      } else {
        const parts = [];
        if (t.verdicts.length) parts.push('verdicts ' + t.verdicts.map(v => `${v.id} (${v.body.for} ${v.body.result})`).join(', '));
        if (t.drops.length) parts.push('dropped ' + t.drops.map(d => d.body.for).join(', '));
        if (t.hyps.length) parts.push('new hypotheses ' + t.hyps.map(h => h.id).join(', '));
        const nt = t.exp ? tests.filter(q => q.exp === t.exp.id).length : 0;
        if (t.exp) parts.push(`experiment ${t.exp.id} (${t.exp.sims.length} simulation${t.exp.sims.length === 1 ? '' : 's'}, ${nt ? nt + (nt === 1 ? ' test' : ' tests') : 'no tests: it explores'})`);
        const asked = [...new Set(t.requests.map(q => q.body.tool).concat(t.notes.flatMap(q => (q.body.requests || []).map(x => x.tool))))];
        if (asked.length) parts.push('asked for information (' + asked.join(', ') + ')');
        if (t.report) parts.push('final report');
        const waiting = !parts.length && !ended && rs.every(r => r.type === 'turn'), useless = !parts.length && !waiting;  // the newest turn of a running session: no answer yet
        push({ turn: n, lane: 'model', kind: 'answer', warn: useless, label: `turn ${n}: ` + (waiting ? 'waiting for the answer' : useless ? 'an answer the harness could not use' : parts.join('; ')), open: { t: 'log', turn: n } },
             rs.filter(r => ['turn', 'verdict', 'drop', 'hypothesis', 'request', 'result'].includes(r.type) || (r.type === 'experiment')).map(r => r.id).concat(t.report && !t.exp ? [] : []));
        t.malformed.forEach(m => push({ turn: n, lane: 'harness', kind: 'refused', warn: true, label: 'refused: ' + ((m.body.refused || []).map(q => `${q.part}: ${q.reason}`).join(' | ') || m.body.error), open: { t: 'log', turn: n } }, [m.id]));
        t.refusals.forEach(m => push({ turn: n, lane: 'harness', kind: 'refused', warn: true, label: `${m.body.part === 'report' ? 'report refused' : 'refused part (' + m.body.part + ')'}: ${m.body.reason || m.body.text}`, open: { t: 'log', turn: n } }, [m.id]));
        if (t.exp) {
          push({ turn: n, lane: 'harness', kind: 'accepted', label: 'plan accepted', open: { t: 'exp', id: t.exp.id } }, t.notes.map(r => r.id));
          push({ turn: n, lane: 'simulator', kind: 'sims', exp: t.exp.id, label: `${t.exp.sims.length} simulation${t.exp.sims.length === 1 ? '' : 's'}`, sims: t.exp.sims, open: { t: 'exp', id: t.exp.id } }, t.exp.sims.map(q => q.id).concat(t.exp.evidence ? [t.exp.evidence.id] : []));
          if (t.exp.checks.length) push({ turn: n, lane: 'harness', kind: 'checks', exp: t.exp.id, label: `${t.exp.checks.length} check${t.exp.checks.length === 1 ? '' : 's'}: ${t.exp.checks.filter(c => c.result === 'held').length} held, ${t.exp.checks.filter(c => c.result === 'failed').length} failed${t.exp.checks.some(c => c.void) ? `, ${t.exp.checks.filter(c => c.void).length} void` : ''}`,
                                         open: { t: 'exp', id: t.exp.id } }, t.exp.checks.map(c => c.id));
        }
        if (t.report) push({ turn: n, lane: 'harness', kind: 'report', label: 'report accepted', open: { t: 'report' } }, [t.report.id]);
      }
      rs.forEach(r => { if (!(r.id in recStep)) recStep[r.id] = Math.max(first, steps.length - 1); });
      t.steps = steps.slice(first); return t; });

    const count = t => of(t).length;
    return { id: f.id, meta, brief, old: !multi, ended, recs, byId, pos, recStep, voidIds: new Set(checks.filter(c => c.void).map(c => c.id)), sims, simById, exps, expById, tests, testById, checks, hyps, hypById, source, report, repRec, claims, turns, steps,
             counts: { hypothesis: count('hypothesis'), experiment: multi ? count('experiment') : exps.length, simulation: multi ? count('simulation') : sims.length,
                       rule: exps.reduce((a, x) => a + x.rules.length, 0), test: tests.length, check: count('check'), verdict: count('verdict'), report: count('report'), turn: turns.filter(t => t.n > 0).length,
                       drop: count('drop'), refused: count('malformed') + recs.filter(r => r.type === 'note' && r.body.part).length },
             bySource: Object.fromEntries(['model', 'harness', 'simulator', 'operator'].map(b => [b, recs.filter(r => D.by(r) === b).length])) };
  },

  // every hypothesis state as it was after step k (for the replay)
  stateAt(M, k) {
    const seen = id => M.recStep[id] <= k, out = {};
    M.hyps.forEach(h => { if (!seen(h.id)) return; out[h.id] = h.verdict && seen(h.verdict.id) ? h.verdict.result : h.drop && seen(h.drop.id) ? 'dropped' : h.state === 'ended without a verdict' && k >= M.steps.length - 1 ? h.state : 'open'; });
    return out;
  },
};
