// the live cards' plan of an experiment while it runs (EV.tilePlan), on s057 cut just after X4 (the scheduler run, whose settings are those of r002):
// a run with a network change is a fresh simulation, as the harness ran it (r010). node tile_plan_check.js EVIDENCE_TILES_JS
const fs = require('fs'), vm = require('vm');
const src = fs.readFileSync(process.argv[2], 'utf8');
const EV = { e: s => String(s) };
const ctx = vm.createContext({ EV, window: {}, document: { getElementById: () => ({ addEventListener: () => 0 }), querySelectorAll: () => [], querySelector: () => null, addEventListener: () => 0 }, performance: { now: () => 0 }, console, setInterval: () => 0, setTimeout: () => 0, requestAnimationFrame: () => 0, localStorage: { getItem: () => null, setItem: () => 0 } });
vm.runInContext(src, ctx);
const led = fs.readFileSync('/home/chunguck.kim/project/sessions/s057/ledger.jsonl', 'utf8').split('\n').filter(Boolean).map(l => JSON.parse(l));
const cut = led.slice(0, led.findIndex(r => r.id === 'X4') + 1);
const brief = JSON.parse(fs.readFileSync('/home/chunguck.kim/project/sessions/s057/session.json', 'utf8')).given;
EV.M = { id: 's057', brief, recs: cut, sims: cut.filter(r => r.type === 'simulation').map(r => ({ id: r.id, label: r.body.label, params: r.body.params, run: r.body.run_id, metrics: r.body.metrics, same_as: r.body.same_as || null, exp: r.parent, structure: r.body.structure || null })) };
const plan = EV.tilePlan({ exp: 'X4' });
const ok = plan && plan.fresh.length === 1 && plan.fresh[0].label === 'sched_cubic_q1000' && plan.fresh[0].run === 'r010' && plan.reused.length === 0;
console.log(JSON.stringify({ fresh: plan && plan.fresh.map(d => [d.label, d.run]), reused: plan && plan.reused }), ok ? 'PASS' : 'FAIL');
