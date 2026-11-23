// the summary's "model calls" on three kinds of session: by agent (s056), supervised before the count by agent (s053), one agent (s024)
const fs = require('fs');
const src = fs.readFileSync(process.argv[2], 'utf8');
const expr = src.match(/\['model calls', (.*?)\], \['replies cut off'/)[1];
for (const sid of ['s056', 's053', 's024']) {
  const m = JSON.parse(fs.readFileSync(`/home/chunguck.kim/project/sessions/${sid}/session.json`, 'utf8')), f = m.flags, EV = { nr: 'not recorded' };
  console.log(sid, '->', eval(expr));
}
