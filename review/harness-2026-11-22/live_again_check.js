// the live note's "again" with now.json (s056 turn 12): unit check of EV.liveNow on the branch's evidence_live.js and on the live page's
const fs = require('fs'), vm = require('vm');
for (const [name, file] of [['branch', process.argv[2]], ['live', process.argv[3]]]) {
  const EV = { s: { step: null }, off: true };
  const ctx = vm.createContext({ EV, window: {}, document: { getElementById: () => null, querySelectorAll: () => [] }, performance: { now: () => 0 }, console, setInterval: () => 0, setTimeout: () => 0 });
  vm.runInContext(fs.readFileSync(file, 'utf8'), ctx);
  const recs = [{ id: 'U12', type: 'turn', turn: 12, body: { last_turn: 'free' }, ts: '2026-11-23T03:50:00' }, { id: 'D12', type: 'draft', turn: 12, body: {}, ts: '2026-11-23T03:52:00' },
                { id: 'Q54', type: 'request', turn: 12, body: {}, ts: '2026-11-23T03:53:00' }, { id: 'T54', type: 'result', turn: 12, body: {}, ts: '2026-11-23T03:53:01' }];
  const text = recs.map(r => JSON.stringify(r)).join('\n');
  const run = (now) => { EV.off = false; EV.M = { id: 's056', recs, ended: false }; EV.files = { row: { running: true }, now }; EV.live.seen = {}; EV.liveSeen ? 0 : 0;
    const L = EV.live; L.tries = 0; const lines = text.split('\n'); for (let i = lines.length - 1; i >= 0; i--) { const m = /"type": ?"(\w+)"/.exec(lines[i]); if (!m) continue; if (m[1] === 'turn') break; if (m[1] === 'draft') L.tries++; }
    return EV.liveNow(); };
  const cont = run({ turn: 12, step: 'reply', round: 2, again: false, at: '2026-11-23T03:57:28' });
  const retry = run({ turn: 12, step: 'reply', round: null, again: true, at: '2026-11-23T03:57:28' });
  const none = run(null);
  console.log(name, 'continued reply:', JSON.stringify({ again: cont && cont.again, cont: cont && cont.cont }), '| asked again:', JSON.stringify({ again: retry && retry.again }), '| no now.json:', JSON.stringify(none && { phase: none.phase, again: none.again }));
}
