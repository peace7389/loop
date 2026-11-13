// The Operator tab (reads checks/ only: the scheduling policy, the sweep as a heat map (evidence_heat.js), the score with
// the knobs that differ between the sweep's best row and the recommendation marked, and the checklist, which the operator
// judges here: yes, no or unjudged and a note for each item, stored by control.py in the score file). The operator's own
// simulation and sweep are in evidence_oprun.js; the Compare tab in evidence_compare.js.
// ======================================================================================================
Object.assign(EV, {
  sweeps: {},
  gap: sc => (typeof sc.gap_on_target !== 'number' ? 'not recorded' : /_bps$/.test(sc.goal.target) ? (sc.gap_on_target / 1e6).toFixed(3) + ' Mbps' : String(+sc.gap_on_target.toPrecision(4))),
  csv(text) {  // a CSV table as objects (quoted fields allowed)
    const rows = [], re = /("([^"]|"")*"|[^,\n]*)(,|\n|$)/g; let row = [], m;
    const t = String(text || '').replace(/\r/g, '').trim() + '\n';
    while ((m = re.exec(t)) && m.index < t.length) { row.push(m[1].startsWith('"') ? m[1].slice(1, -1).replace(/""/g, '"') : m[1]); if (m[3] !== ',') { rows.push(row); row = []; } if (!m[0]) re.lastIndex++; }
    const [h, ...rest] = rows; return h ? rest.filter(r => r.length === h.length).map(r => Object.fromEntries(h.map((k, i) => [k, r[i]]))) : [];
  },
  sweepId() { const f = EV.files, k = f.key && f.key.per_scheduling_policy && f.key.per_scheduling_policy[f.policy]; return (f.score && f.score.sweep) || (k && k.sweep) || null; },
  async afterOperator() {
    const id = EV.sweepId(); if (!id || id in EV.sweeps) return EV.afterRun ? EV.afterRun() : undefined;  // the sweep table is there (or there is none): the run and sweep forms
    EV.sweeps[id] = null; const t = await EV.get(`../checks/sweeps/${id}/table.csv`); EV.sweeps[id] = t ? EV.csv(t) : 'none'; EV.draw();
  },

  operatorTab() {
    const f = EV.files, e = EV.e, sc = f.score, M = EV.M, id = EV.sweepId(), rows = id ? EV.sweeps[id] : null, goal = (sc && sc.goal) || (M.brief && M.brief.goal && M.brief.goal.target ? { target: M.brief.goal.target.measure, direction: M.brief.goal.target.direction, conditions: M.brief.goal.conditions } : null);
    const knobs = rows && rows !== 'none' && rows.length ? Object.keys(rows[0]).filter(k => M.brief && M.brief.knobs && k in M.brief.knobs && new Set(rows.map(r => r[k])).size > 1) : [];
    const pick = i => `<select data-ch="heat" data-i="${i}">${knobs.map(k => `<option${EV.s.heat[i] === k ? ' selected' : ''}>${e(k)}</option>`).join('')}</select>`;
    const notes = f.key && f.key.per_scheduling_policy && f.key.per_scheduling_policy[f.policy];
    // the knobs whose values differ between the sweep's best row and the recommendation: marked in both tables
    const same = (p, q) => (p !== '' && q !== '' && !isNaN(+p) && !isNaN(+q) ? +p === +q : String(p) === String(q)), differ = sc && sc.best_row && sc.recommendation ? Object.keys(sc.recommendation).filter(k => k in sc.best_row && !same(sc.best_row[k], sc.recommendation[k])) : [];
    const kv = o => `<table><tbody>${Object.entries(o || {}).map(([k, v]) => `<tr${differ.includes(k) ? ' class="diff" data-differs="' + e(k) + '"' : ''}><td>${e(k)}${differ.includes(k) ? ' <span title="differs between the sweep’s best row and the recommendation">≠</span>' : ''}</td><td class="num">${e(EV.val(k, typeof v === 'string' && v !== '' && !isNaN(+v) ? +v : v))}</td></tr>`).join('')}</tbody></table>`;
    const jk = j => (j === 'yes' ? 'held' : j === 'no' ? 'failed' : 'not-checked'), ro = EV.off ? ' disabled' : '';
    return `<div class="ev-card"><h2>${EV.term('Operator', 'Operator')} view of session ${e(M.id)} <small>read from checks/ only; never shown to the model</small></h2>
        <p>${EV.term('Scheduling policy', 'Scheduling policy')}: <b>${EV.policyText(f.row)}</b> · sweep ${e(id || 'not recorded')}${notes && notes.notes ? `</p><details><summary>the answer key's notes for this policy</summary><p class="sm">${e(notes.notes)}</p></details>` : '</p>'}</div>
      <div class="ev-card"><h2>The sweep <small>${knobs.length ? `across ${pick(0)} up ${pick(1)}` : ''}</small></h2>${!id ? `<p class="sm">sweep: ${EV.nr}</p>` : rows === 'none' ? `<p class="sm">the sweep table: ${EV.nr}</p>` : !rows ? '<p class="sm">Loading the sweep table…</p>' : !goal ? `<p class="sm">goal: ${EV.nr}</p>` : EV.heat(rows, goal)}</div>
      <div class="ev-top"><div class="ev-card"><h2>Score</h2>${!sc ? `<p class="sm">score: ${EV.nr} (harness/score.py ${e(M.id)} writes it once the session has ended)</p>` : `
          <div class="kv"><div><span>gap to the best row, on ${e(sc.goal.target)}</span><b>${e(EV.gap(sc))}</b></div><div><span>as part of the best</span><b>${(100 * sc.gap_as_part_of_best).toFixed(3)}%</b></div>
            <div><span>conditions hold at the recommendation</span><b>${Object.values(sc.conditions_hold_at_the_recommendation || {}).every(Boolean) ? EV.res('held', 'yes') : EV.res('failed', 'no')}</b></div><div><span>simulations used / allowed</span><b>${sc.simulations_used} / ${sc.simulations_allowed}</b></div></div>
          ${sc.against_the_best ? `<p id="op-tol"><b>${e(sc.against_the_best)}</b> <span class="sm">· tolerance ${e(sc.tolerance_per_cent)}% (${e(sc.tolerance_from)}): two results closer than this count as equal</span></p>` : ''}
          <p class="sm">A negative gap means the recommendation, simulated by the operator, did better than every row of the sweep.</p>
          <div class="ev-top" id="op-score"><div><h3>The sweep's best row</h3>${kv(sc.best_row)}</div><div><h3>The recommendation, simulated</h3>${kv(sc.recommendation)}${kv(sc.at_the_recommendation)}</div></div>
          <p class="sm">${differ.length ? `In bold with ≠: ${differ.length === 1 ? 'the knob whose value differs' : 'the knobs whose values differ'} between the two (${e(differ.join(', '))}).` : 'No knob differs between the two.'}</p>`}</div>
        <div class="ev-card" id="op-list"><h2>Checklist <small>judged by the operator: yes, no or unjudged, and a note; kept in the score file</small></h2>${sc && sc.checklist ? `<table><tbody>${sc.checklist.map(c => `<tr data-n="${c.n}"><td>${c.n}</td><td>${e(c.item)}
            <input type="text" data-ch="judge" data-k="note" placeholder="the operator's note" value="${e(c.note || '')}" style="width:100%;margin-top:4px"${ro}></td>
            <td style="white-space:nowrap"><span class="jm">${EV.gkey(jk(c.judgement))}</span><select data-ch="judge" data-k="judgement"${ro}>${['unjudged', 'yes', 'no'].map(j => `<option${c.judgement === j ? ' selected' : ''}>${j}</option>`).join('')}</select></td></tr>`).join('')}</tbody></table><p class="sm" id="op-list-msg"></p>`
          : `<p class="sm">checklist: ${EV.nr}${sc ? '' : ' (a session is judged once it has a score)'}</p>`}</div></div>
      ${EV.runCard ? EV.runCard() + EV.sweepCard() : ''}`;
  },
});
// a judgement or a note of the checklist: saved at once through control.py, and the row is brought up to date in place (no redraw: the next field keeps the cursor)
EV.chg = Object.assign(EV.chg || {}, { async judge(el) {
  const tr = el.closest('tr'), n = Number(tr.dataset.n), msg = document.getElementById('op-list-msg'), body = { session: EV.s.sid, n, judgement: tr.querySelector('select').value, note: tr.querySelector('input').value };
  try { const r = await EV.post('../api/judge', body), c = ((EV.files.score || {}).checklist || []).find(q => q.n === n); if (c) { c.judgement = r.judgement; if (r.note) c.note = r.note; else delete c.note; }
    tr.querySelector('.jm').innerHTML = EV.gkey(r.judgement === 'yes' ? 'held' : r.judgement === 'no' ? 'failed' : 'not-checked'); msg.textContent = `item ${n}: saved`; msg.className = 'sm'; }
  catch (x) { msg.textContent = `item ${n} was not saved: ${x.message}`; msg.className = 'sm warnc'; }
} });
