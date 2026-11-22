// Every session's page model, in full where it is drawn from: each track step (turn, lane, kind, label, what it opens) and each turn's fields.
const fs = require('fs'), vm = require('vm'), path = require('path');
const [V, SD] = process.argv.slice(2);
const ctx = { console, window: {}, document: undefined, EV: {} }; vm.createContext(ctx);
vm.runInContext(fs.readFileSync(path.join(V, 'evidence_data.js'), 'utf8') + '\nthis.EV_DATA = EV_DATA;', ctx);
for (const sid of fs.readdirSync(SD).filter(d => /^s\d+$/.test(d)).sort()) {
  const d = path.join(SD, sid); if (!fs.existsSync(path.join(d, 'ledger.jsonl'))) continue;
  const f = { id: sid, ledger: ctx.EV_DATA.lines(fs.readFileSync(path.join(d, 'ledger.jsonl'), 'utf8')), session: fs.existsSync(path.join(d, 'session.json')) ? JSON.parse(fs.readFileSync(path.join(d, 'session.json'), 'utf8')) : null };
  const M = ctx.EV_DATA.build(f);
  M.steps.forEach(s => console.log(sid, 'step', s.turn, s.lane, s.kind, JSON.stringify(s.label || ''), JSON.stringify(s.open || null)));
  M.turns.forEach(t => console.log(sid, 'turn', t.n, 'exp', t.exp && t.exp.id, 'report', t.report && t.report.id, 'refusals', t.refusals.length, 'notes', t.notes.length, 'obs', JSON.stringify(t.observations || '').length, 'verdicts', t.verdicts.length, 'rulings', t.rulings.length));
  console.log(sid, 'counts', JSON.stringify(M.counts), 'tests', M.tests.length, 'hyps', M.hyps.length);
}
