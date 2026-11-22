"""Stage 5, part 4: the page, nothing more than the sheet asks: each test's competing guess as a link, and the three answers in the review rounds
list. Old sessions (rival sentences) draw as before. Usage: s5_page.py VIEWER_DIR"""
import sys
from pathlib import Path
V = Path(sys.argv[1])
def rep(f, a, b, n=1):
    p = V / f; s = p.read_text(); assert s.count(a) == n, (f, a[:100], s.count(a)); p.write_text(s.replace(a, b))
rep("evidence_data.js", "rules: (b.decision_rules || b.rules || []).map(q => ({ for: q.for, rule: q.decision_rule || q.rule, rival: q.rival || null, rival_predicts: q.rival_predicts || null })),",
    "rules: (b.decision_rules || b.rules || []).map(q => ({ for: q.for, rule: q.decision_rule || q.rule, rival: q.rival || null, rival_predicts: q.rival_predicts || null, competes: q.competes_with || null })),   // competes: the guess a rule competes with (stage 5)")
rep("evidence_data.js", "hyp: r.for, rule: r.rule, rival: r.rival, rival_predicts: r.rival_predicts, labels,", "hyp: r.for, rule: r.rule, rival: r.rival, rival_predicts: r.rival_predicts, competes: r.competes || null, labels,")
comp = "${T.competes ? `<p class=\"sm\">competes with the guess ${EV.whyLink(T.competes)} · under it the rule would have ${e(T.rival_predicts || 'not recorded')}</p>` : ''}"
rep("evidence_test.js", "${sec('Expected', `${T.rule ? EV.ruleList(T) : EV.ruleRead(T)}${T.rival ?", "${sec('Expected', `${T.rule ? EV.ruleList(T) : EV.ruleRead(T)}" + comp + "${T.rival ?")
rep("evidence_notebook.js", "${line('Expected', ['model'], `${EV.ruleList(T, 3)}${T.rival ?", "${line('Expected', ['model'], `${EV.ruleList(T, 3)}${T.competes ? `<div class=\"sm lc2\">competes with the guess ${EV.whyLink(T.competes)}</div>` : ''}${T.rival ?")
rep("evidence_cards.js", "${T.rule ? EV.ruleRead(T) : 'no decision rule'}${T.rival ?", "${T.rule ? EV.ruleRead(T) : 'no decision rule'}${T.competes ? `<br><span class=\"sm\">competes with the guess ${EV.whyLink(T.competes)} · would give: ${e(T.rival_predicts || 'not recorded')}</span>` : ''}${T.rival ?")
rep("evidence_notebook.js", "<code>${e(d.decision_rule || '')}</code> · its rival: <span data-own=\"model\">${e(d.rival || '')}</span> (the rule would ${d.rival_predicts === 'held' ? 'hold' : 'fail'} under it, it says)</div>",
    "<code>${e(d.decision_rule || '')}</code> · ${d.competes_with ? `competes with the guess ${EV.whyLink(d.competes_with)}` : `its rival: <span data-own=\"model\">${e(d.rival || '')}</span>`} (the rule would ${d.rival_predicts === 'held' ? 'hold' : 'fail'} under it, it says)</div>\n"
    "        ${r.honest ? `<div class=\"sm sup-q\">${['honest', 'consistent', 'correct'].map(q => `<span title=\"${e(r[q + '_why'] || '')}\">${q[0].toUpperCase() + q.slice(1)} <b class=\"${r[q] === 'pass' ? '' : 'warnc'}\">${e(r[q])}</b></span>`).join(' · ')}${r.if_tested ? ` <span class=\"mut\">(the rule gives ${e(r.if_tested)} under the tested guess, ${e(r.if_competitor)} under ${e(r.competes_with || 'its competitor')})</span>` : ''}${r.missing ? `<br><span class=\"warnc\">a competing cause that is none of its guesses:</span> <span data-own=\"supervisor\">${e(r.missing)}</span>` : ''}</div>` : ''}")
rep("evidence_notebook.js", "not_run: 'not run: the harness could not use the last repair' },", "not_run: 'not run: the harness could not use the last repair', held: 'held: not run in this turn, the hypothesis stays open' },")
print("page patched")
