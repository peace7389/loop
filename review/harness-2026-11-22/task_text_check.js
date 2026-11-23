// the page's task sentence against the harness's (part 10), for the briefs of the project: the same words; and the sentence before part 10 for a
// network brief, which the page still takes for the harness's. node task_text_check.js VIEWER_DIR HARNESS_SENTENCES_JSON
const fs = require('fs');
const src = fs.readFileSync(process.argv[2] + '/evidence_setting.js', 'utf8');
const m = src.match(/  taskText\(b, before\) \{[\s\S]*?\n    return `No aim is given[^\n]*\n/);
const EV = {}; eval('EV.taskText = function ' + m[0].trim().replace(/^taskText/, '').replace(/,\s*$/, ''));
const want = JSON.parse(fs.readFileSync(process.argv[3], 'utf8'));
let bad = 0;
for (const [n, x] of Object.entries(want)) {
  const b = JSON.parse(fs.readFileSync(`/home/chunguck.kim/project/briefs/${n}.json`, 'utf8'));
  const same = EV.taskText(b) === x.now, before = EV.taskText(b, true) === x.before;
  if (!same || !before) bad++;
  console.log(n, same ? 'same' : 'DIFFERS', before ? '(before: same)' : '(before: DIFFERS)');
}
console.log(bad ? 'FAIL' : 'PASS');
