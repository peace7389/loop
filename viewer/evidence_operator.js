// The Operator tab (reads checks/ only: the scheduling policy, the sweep as a heat map over two chosen knobs with the
// session's simulations as numbered points and the best cell marked, the score, the checklist) and the Compare tab
// (every session of the selected brief: flags, simulations used, how it ended, gap to the best, checklist).
// ======================================================================================================
Object.assign(EV, {
  sweeps: {}, cmp: {},
  gap: sc => (typeof sc.gap_on_target !== 'number' ? 'not recorded' : /_bps$/.test(sc.goal.target) ? (sc.gap_on_target / 1e6).toFixed(3) + ' Mbps' : String(+sc.gap_on_target.toPrecision(4))),
  csv(text) {  // a CSV table as objects (quoted fields allowed)
    const rows = [], re = /("([^"]|"")*"|[^,\n]*)(,|\n|$)/g; let row = [], m;
    const t = String(text || '').replace(/\r/g, '').trim() + '\n';
    while ((m = re.exec(t)) && m.index < t.length) { row.push(m[1].startsWith('"') ? m[1].slice(1, -1).replace(/""/g, '"') : m[1]); if (m[3] !== ',') { rows.push(row); row = []; } if (!m[0]) re.lastIndex++; }
    const [h, ...rest] = rows; return h ? rest.filter(r => r.length === h.length).map(r => Object.fromEntries(h.map((k, i) => [k, r[i]]))) : [];
  },
  sweepId() { const f = EV.files, k = f.key && f.key.per_scheduling_policy && f.key.per_scheduling_policy[f.policy]; return (f.score && f.score.sweep) || (k && k.sweep) || null; },
  async afterOperator() {
    const id = EV.sweepId(); if (!id || id in EV.sweeps) return;
    EV.sweeps[id] = null; const t = await EV.get(`../checks/sweeps/${id}/table.csv`); EV.sweeps[id] = t ? EV.csv(t) : 'none'; EV.draw();
  },

  heat(rows, goal) {
    const M = EV.M, S = EV.s, e = EV.e, [kx, ky] = S.heat, tg = goal.target, max = goal.direction !== 'min';
    const conds = (goal.conditions || []).map(c => c.match(/^\s*(\w+)\s*(<=|>=|<|>|==)\s*([-\d.eE]+)\s*$/)).filter(Boolean);
    const meets = r => conds.every(([, k, op, v]) => { const a = +r[k], b = +v; return op === '<=' ? a <= b : op === '>=' ? a >= b : op === '<' ? a < b : op === '>' ? a > b : a === b; });
    const isNum = k => rows.every(r => r[k] !== '' && !isNaN(+r[k])), sort = k => [...new Set(rows.map(r => r[k]))].sort((a, b) => (isNum(k) ? +a - +b : a < b ? -1 : 1));
    const X = sort(kx), Y = sort(ky).reverse(), cell = {};
    rows.forEach(r => { if (r.error || !meets(r) || r[tg] === '') return; const key = r[kx] + '|' + r[ky], c = cell[key];
      if (!c || (max ? +r[tg] > +c[tg] : +r[tg] < +c[tg])) cell[key] = r; });
    const vals = Object.values(cell).map(r => +r[tg]), lo = Math.min(...vals), hi = Math.max(...vals);
    const ramp = ['#cde2fb', '#9ec5f4', '#6da7ec', '#3987e5', '#256abf', '#184f95', '#0d366b'], col = v => ramp[hi > lo ? Math.min(6, Math.floor(7 * (v - lo) / (hi - lo + 1e-9))) : 6];
    const cw = Math.max(7, Math.floor(820 / X.length)), ch = 34, L = 74, T = 8, W = L + cw * X.length + 10, H = T + ch * Y.length + 44, [u, f] = EV.unit(tg);
    const best = Object.values(cell).sort((a, b) => (max ? b[tg] - a[tg] : a[tg] - b[tg]))[0];
    const fmt = v => (+f(+v).toPrecision(6)).toLocaleString('en-US') + (u ? ' ' + u : '');
    let svg = `<defs><pattern id="ev-hatch" width="6" height="6" patternTransform="rotate(45)" patternUnits="userSpaceOnUse"><rect width="6" height="6" fill="var(--surface-0)"/><line x1="0" y1="0" x2="0" y2="6" stroke="var(--grid)" stroke-width="2"/></pattern></defs>`;
    Y.forEach((yv, j) => { svg += `<text x="${L - 6}" y="${T + j * ch + ch / 2 + 4}" text-anchor="end">${e(yv)}</text>`;
      X.forEach((xv, i) => { const r = cell[xv + '|' + yv], x = L + i * cw, y = T + j * ch;
        svg += `<rect class="cell" x="${x}" y="${y}" width="${cw}" height="${ch}" fill="${r ? col(+r[tg]) : 'url(#ev-hatch)'}"><title>${e(`${kx} ${xv} · ${ky} ${yv}: ${r ? `best ${tg} ${fmt(r[tg])} (${Object.keys(r).filter(k => !['i', kx, ky, tg].includes(k) && M.brief && M.brief.knobs && k in M.brief.knobs).map(k => k + ' ' + r[k]).join(', ')})` : 'no simulation of the sweep meets ' + (goal.conditions || []).join(' and ')}`)}</title></rect>`;
        if (r && r === best) svg += `<rect x="${x - 1}" y="${y - 1}" width="${cw + 2}" height="${ch + 2}" fill="none" stroke="var(--text-primary)" stroke-width="2.5"/><text x="${x + cw / 2}" y="${y - 2}" text-anchor="middle" style="font-weight:700;fill:var(--text-primary)">★ best</text>`; }); });
    const step = Math.ceil(X.length / Math.floor((cw * X.length) / 46));
    X.forEach((xv, i) => { if (i % step === 0) svg += `<text x="${L + i * cw + cw / 2}" y="${T + Y.length * ch + 14}" text-anchor="middle">${e(xv)}</text>`; });
    svg += `<text x="${L + (cw * X.length) / 2}" y="${H - 6}" text-anchor="middle">${e(kx)}</text><text x="10" y="${T + (ch * Y.length) / 2}" transform="rotate(-90 10 ${T + (ch * Y.length) / 2})" text-anchor="middle">${e(ky)}</text>`;
    const where = (k, cats, v, size, off) => { if (v == null) return null; const s = String(v), i = cats.indexOf(s); if (i >= 0) return off + i * size + size / 2; if (!isNum(k)) return null;
      const n = cats.map(Number), j = n.findIndex(q => q > +v); if (j <= 0) return null; return off + (j - 1 + (+v - n[j - 1]) / (n[j] - n[j - 1])) * size + size / 2; };
    M.sims.filter(s => !s.same_as && s.metrics).forEach((s, n) => { const x = where(kx, X, s.params[kx], cw, L), y = where(ky, Y.slice().reverse(), s.params[ky], ch, 0);
      if (x == null || y == null) return; const yy = T + ch * Y.length - y;
      svg += `<g data-act="open" data-t="sim" data-id="${e(s.id)}"><circle cx="${x}" cy="${yy}" r="7.5" fill="var(--surface-1)" stroke="var(--by-simulator)" stroke-width="2"/><text x="${x}" y="${yy + 3.5}" text-anchor="middle" style="font-size:9.5px;font-weight:700;fill:var(--text-primary)">${n + 1}</text><title>${e(`${n + 1}: ${s.id} · ${s.label} · ${kx} ${s.params[kx]} · ${ky} ${s.params[ky]} · ${tg} ${fmt(s.metrics[tg])}`)}</title></g>`; });
    return `<div class="ev-scroll"><svg class="heat" width="${W}" height="${H}" role="img" aria-label="Sweep heat map">${svg}</svg></div>
      <p class="sm">colour: the best ${e(tg)} in the cell over the other knobs, among sweep rows that meet ${e((goal.conditions || []).join(' and ') || 'no condition')} · <span style="display:inline-flex;vertical-align:middle">${ramp.map(c => `<i style="display:inline-block;width:18px;height:10px;background:${c}"></i>`).join('')}</span> ${fmt(lo)} → ${fmt(hi)}
        · hatched: no row meets the conditions · numbered circles: this session's simulations in order (hover for details, click to open on the Session tab) · ★ the sweep's best cell</p>`;
  },

  operatorTab() {
    const f = EV.files, e = EV.e, sc = f.score, M = EV.M, id = EV.sweepId(), rows = id ? EV.sweeps[id] : null, goal = (sc && sc.goal) || (M.brief && M.brief.goal && M.brief.goal.target ? { target: M.brief.goal.target.measure, direction: M.brief.goal.target.direction, conditions: M.brief.goal.conditions } : null);
    const knobs = rows && rows !== 'none' && rows.length ? Object.keys(rows[0]).filter(k => M.brief && M.brief.knobs && k in M.brief.knobs && new Set(rows.map(r => r[k])).size > 1) : [];
    const pick = i => `<select data-ch="heat" data-i="${i}">${knobs.map(k => `<option${EV.s.heat[i] === k ? ' selected' : ''}>${e(k)}</option>`).join('')}</select>`;
    const notes = f.key && f.key.per_scheduling_policy && f.key.per_scheduling_policy[f.policy];
    const kv = o => `<table><tbody>${Object.entries(o || {}).map(([k, v]) => `<tr><td>${e(k)}</td><td class="num">${e(EV.val(k, typeof v === 'string' && v !== '' && !isNaN(+v) ? +v : v))}</td></tr>`).join('')}</tbody></table>`;
    return `<div class="ev-card"><h2>${EV.term('Operator', 'Operator')} view of session ${e(M.id)}<small>read from checks/ only; never shown to the model</small></h2>
        <p>${EV.term('Scheduling policy', 'Scheduling policy')}: <b>${e(f.policy || 'not recorded')}</b> · sweep ${e(id || 'not recorded')}${notes && notes.notes ? `</p><details><summary>the answer key's notes for this policy</summary><p class="sm">${e(notes.notes)}</p></details>` : '</p>'}</div>
      <div class="ev-card"><h2>The sweep<small>${knobs.length ? `across ${pick(0)} up ${pick(1)}` : ''}</small></h2>${!id ? `<p class="sm">sweep: ${EV.nr}</p>` : rows === 'none' ? `<p class="sm">the sweep table: ${EV.nr}</p>` : !rows ? '<p class="sm">Loading the sweep table…</p>' : !goal ? `<p class="sm">goal: ${EV.nr}</p>` : EV.heat(rows, goal)}</div>
      <div class="ev-top"><div class="ev-card"><h2>Score</h2>${!sc ? `<p class="sm">score: ${EV.nr} (harness/score.py ${e(M.id)} writes it once the session has ended)</p>` : `
          <div class="kv"><div><span>gap to the best row, on ${e(sc.goal.target)}</span><b>${e(EV.gap(sc))}</b></div><div><span>as part of the best</span><b>${(100 * sc.gap_as_part_of_best).toFixed(3)}%</b></div>
            <div><span>conditions hold at the recommendation</span><b>${Object.values(sc.conditions_hold_at_the_recommendation || {}).every(Boolean) ? '<span class="ok">yes</span>' : '<span class="bad">no</span>'}</b></div><div><span>simulations used / allowed</span><b>${sc.simulations_used} / ${sc.simulations_allowed}</b></div></div>
          <p class="sm">A negative gap means the recommendation, simulated by the operator, did better than every row of the sweep.</p>
          <div class="ev-top"><div><h3>the sweep's best row</h3>${kv(sc.best_row)}</div><div><h3>the recommendation, simulated</h3>${kv(sc.recommendation)}${kv(sc.at_the_recommendation)}</div></div>`}</div>
        <div class="ev-card"><h2>Checklist<small>judged by the operator</small></h2>${sc && sc.checklist ? `<table><tbody>${sc.checklist.map(c => `<tr><td>${c.n}</td><td>${e(c.item)}</td><td class="${c.judgement === 'yes' ? 'ok' : c.judgement === 'no' ? 'bad' : 'mut'}">${e(c.judgement)}</td></tr>`).join('')}</tbody></table>` : `<p class="sm">checklist: ${EV.nr}</p>`}</div></div>`;
  },

  compareTab() {
    const e = EV.e, S = EV.s, list = EV.st.sessions.filter(x => (x.brief || '') === (S.brief || ''));
    const need = list.filter(x => !EV.cmp[x.id] || EV.cmp[x.id].sig !== `${x.records}|${x.running}`);
    if (need.length && !EV.cmpBusy) { EV.cmpBusy = true;
      Promise.all(need.map(async x => { const [m, sc] = await Promise.all([EV.json(`../sessions/${x.id}/session.json`), EV.json(`../checks/scores/${x.id}.json`)]); EV.cmp[x.id] = { sig: `${x.records}|${x.running}`, m, sc }; }))
        .then(() => { EV.cmpBusy = false; if (EV.s.view === 'compare') EV.draw(); }); }
    const rows = list.map(x => { const c = EV.cmp[x.id] || {}, m = c.m || {}, sc = c.sc, fl = m.flags, cl = sc && sc.checklist || [];
      const n = j => cl.filter(q => q.judgement === j).length;
      return `<tr class="pick" data-act="pick" data-id="${e(x.id)}"><td><b>${e(x.id)}</b></td><td>${e(x.policy || 'not recorded')}</td><td class="sm">${fl ? e(Object.entries(fl).map(([k, v]) => k + ' ' + v).join(' · ')) : EV.nr}</td>
        <td class="num">${m.simulations ?? x.simulations ?? '–'} / ${(m.given && m.given.limits && m.given.limits.simulations) ?? (fl && fl.budget) ?? '–'}</td><td class="num">${m.turns ?? x.turns ?? '–'}</td><td>${x.running ? 'running now' : e(m.how || 'not recorded')}</td>
        <td class="num">${sc ? e(EV.gap(sc)) : '<span class="mut">not scored</span>'}</td><td>${sc ? `${n('yes')} yes · ${n('no')} no · ${n('unjudged')} unjudged` : '–'}</td></tr>`; }).join('');
    return `<div class="ev-card"><h2>Compare sessions<small>every session of the brief ${e(S.brief || 'before briefs')}; click a row to open that session</small></h2>
      <table><thead><tr><th>session</th><th>${EV.term('Scheduling policy', 'scheduling policy')}</th><th>flags</th><th class="num">simulations used / allowed</th><th class="num">turns</th><th>how it ended</th><th class="num">gap to the best</th><th>checklist</th></tr></thead><tbody>${rows}</tbody></table>
      <p class="sm">The gap is the sweep's best row minus the recommendation simulated by the operator, on the brief's target; negative = better than every row of the sweep.</p></div>`;
  },
});
