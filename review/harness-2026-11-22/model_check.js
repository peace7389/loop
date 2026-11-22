// Builds the page's model (EV_DATA.build) for every session with the given viewer, and prints per session: turns with more than one experiment,
// refusal counts, the track's review steps by lane. Usage: node model_check.js VIEWER_DIR SESSIONS_DIR [s053 ...]
const fs = require('fs'), vm = require('vm'), path = require('path');
const [V, SD, ...only] = process.argv.slice(2);
const ctx = { console, window: {}, document: undefined, EV: {} }; vm.createContext(ctx);
vm.runInContext(fs.readFileSync(path.join(V, 'evidence_data.js'), 'utf8') + '\nthis.EV_DATA = EV_DATA;', ctx);
const ids = only.length ? only : fs.readdirSync(SD).filter(d => /^s\d+$/.test(d)).sort();
let bad = 0;
for (const sid of ids) {
  const d = path.join(SD, sid); if (!fs.existsSync(path.join(d, 'ledger.jsonl'))) continue;
  const f = { id: sid, ledger: ctx.EV_DATA.lines(fs.readFileSync(path.join(d, 'ledger.jsonl'), 'utf8')), session: fs.existsSync(path.join(d, 'session.json')) ? JSON.parse(fs.readFileSync(path.join(d, 'session.json'), 'utf8')) : null };
  try {
    const M = ctx.EV_DATA.build(f);
    const multi = M.turns.filter(t => (t.xs || []).length > 1).map(t => `t${t.n}:${t.xs.map(x => x.id).join('+')}`);
    const lanes = M.steps.filter(s => s.kind === 'review' || (s.kind === 'refused' && /harness refuses a repaired/.test(s.label))).map(s => s.lane[0]).join('');
    const sims = M.steps.filter(s => s.kind === 'sims').length;
    console.log(`${sid} ok turns=${M.turns.length} exps=${M.exps.length} sims-steps=${sims} refused=${M.counts.refused} multi=[${multi.join(' ')}] review-lanes=${lanes}`);
  } catch (e) { bad++; console.log(`${sid} ERROR ${e && e.stack ? e.stack.split('\n').slice(0, 3).join(' | ') : e}`); }
}
console.log(bad ? `${bad} sessions failed` : 'every session built');
