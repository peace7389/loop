const fs = require('fs'), vm = require('vm'), path = require('path');
const V = process.argv[2]; const ctx = { console, window: {}, document: { addEventListener() {}, querySelector() { return null; }, getElementById() { return null; } }, location: { search: '', href: '' }, localStorage: { getItem() { return null; }, setItem() {} }, navigator: {}, setTimeout, fetch: () => Promise.reject() };
vm.createContext(ctx);
const src = fs.readFileSync(path.join(V, 'adrs_view.js'), 'utf8'); const i = src.indexOf('const TH_DATA'); 
try { vm.runInContext(src + '\nthis.TH_DATA = TH_DATA;', ctx); } catch (e) { console.log('load:', e.message.slice(0, 120)); }
const T = ctx.TH_DATA; if (!T) { console.log('no TH_DATA'); process.exit(1); }
const m = { udp_goodput_bps: 979015520, tcp_goodput_bps: 5792, udp_loss_frac: 0.510492 };
for (const text of ['l1.queue.length=1000 gives tcp_goodput_bps=5792 and tcp_retrans=18', 'TCP goodput was 0.006 Mbps', 'UDP goodput 979.0 Mbps', 'udp_goodput_bps=979015520', 'tcp_goodput_bps=7000', 'UDP goodput 979'])
  console.log(JSON.stringify(text), '->', JSON.stringify(T.numbers(text, m, {}).map(q => [q.written, q.status])));
