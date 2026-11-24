// EV_CHAIN (2026-11-24; the operator: "view clearly the simulation setting, simulation records, simulation outcomes, and more connection between
// hypothesis, simulation setting, simulation outcome, hypothesis accepted or refuted").
//   EV.chainCard(h)   for a hypothesis: one block per test, read from top to bottom:
//                       1 what was set in each simulation   (the network it ran on, and the settings)
//                       2 what came out of it               (the measures its decision rule looks at; 1 and 2 are one table, a simulation a row)
//                       3 what the hypothesis required      (the decision rule against those numbers)
//                       4 the result                        (the harness's check, then the ruling or verdict, and what it did to the guesses)
//   EV.simHead(s)     at the head of a simulation's panel: its setting, the tests that used it with their result, its records (the files of its run).
// Everything is read from the records the page holds (EV.M). Nothing recorded after the step the page is at appears (EV.seen).
(() => {
  const css = `
.ev .ch { border: 1px solid var(--border); border-radius: 10px; margin: 10px 0 12px; background: var(--surface-0, transparent); }
.ev .ch-head { display: flex; flex-wrap: wrap; align-items: center; gap: 4px 8px; padding: 7px 12px; border-bottom: 1px solid var(--border); font-size: var(--f-sec); }
.ev .ch-head b { font-size: var(--f-body, inherit); }
.ev .ch-step { padding: 8px 12px 9px; border-top: 1px solid var(--border); position: relative; }
.ev .ch-step:first-of-type { border-top: 0; }
.ev .ch-k { margin: 0 0 5px; font-size: var(--f-note); font-weight: 700; color: var(--text-secondary); }
.ev .ch-k .ch-n { display: inline-block; min-width: 18px; height: 18px; line-height: 18px; text-align: center; border-radius: 9px; background: var(--text-primary); color: var(--surface-1, #fff); margin-right: 6px; font-weight: 700; }
.ev .ch-k .sm { font-weight: 400; margin-left: 6px; }
.ev .ch-wrap { overflow-x: auto; }
.ev table.ch-t { border-collapse: collapse; width: 100%; font-size: var(--f-sec); }
.ev table.ch-t th, .ev table.ch-t td { padding: 4px 8px 4px 0; text-align: left; vertical-align: top; border-bottom: 1px solid var(--grid, var(--border)); }
.ev table.ch-t tr:last-child td { border-bottom: 0; }
.ev table.ch-t th { font-weight: 600; color: var(--text-secondary); font-size: var(--f-note); vertical-align: bottom; }
.ev table.ch-t th.ch-g { color: var(--text-primary); border-bottom: 2px solid var(--text-primary); padding-bottom: 2px; }
.ev table.ch-t .ch-out { padding-left: 12px; }
.ev table.ch-t td.ch-first, .ev table.ch-t th.ch-first { border-left: 2px solid var(--border); }
.ev table.ch-t td.num, .ev table.ch-t th.num { text-align: right; white-space: nowrap; }
.ev table.ch-t td.ch-dv { font-weight: 700; }
.ev table.ch-t .ch-lab { color: var(--text-secondary); overflow-wrap: anywhere; }
.ev .ch-res { display: flex; flex-wrap: wrap; align-items: center; gap: 4px 8px; margin: 0 0 4px; }
.ev .ch-arrow { color: var(--text-muted); }
.ev .ch-because { margin: 2px 0 0; font-size: var(--f-sec); }
.ev .ch-note { margin: 5px 0 0; }
.ev .sp { margin: 14px 0 0; padding-top: 10px; border-top: 1px solid var(--border); } .ev .sp:first-of-type { border-top: 0; padding-top: 2px; }
.ev h3.sp-h { margin: 0 0 6px; font-size: var(--f-body, 14px); font-weight: 700; } .ev h3.sp-h .sm { font-weight: 400; margin-left: 6px; }
.ev h3.sp-h .ch-n, .ev h3.sp-n .ch-n { display: inline-block; min-width: 20px; height: 20px; line-height: 20px; text-align: center; border-radius: 10px; background: var(--text-primary); color: var(--surface-1, #fff); margin-right: 7px; font-size: var(--f-note); font-weight: 700; }
.ev .sp-sum { margin: 0 0 6px; } .ev .sp-sum p { margin: 0 0 3px; } .ev .sp-sum .sh-n { color: var(--text-secondary); }
.ev table.so-t td:first-child { width: 44%; } .ev table.so-t tr.so-read td { background: color-mix(in srgb, var(--good) 11%, var(--surface-1, #fff)); } .ev table.so-t tr.so-read td:first-child { box-shadow: inset 3px 0 0 var(--good); } .ev table.so-t tr.so-read .sf-name { color: var(--text-primary); font-weight: 600; }
.ev table.so-t td.so-by { white-space: nowrap; } .ev table.sf-t .sf-name .wd, .ev table.sf-t .sf-name b { font-weight: inherit; }
.ev table.sf-t tr.sf-fx td, .ev table.sf-t tr.sf-fx .sf-v { color: var(--text-secondary); font-weight: 400; }
.ev details.h-fold { margin: 10px 0 0; } .ev details.h-fold > summary { cursor: pointer; font-size: var(--f-note); font-weight: 700; color: var(--text-secondary); padding: 3px 0; }
.ev .sh { margin: 6px 0 10px; border: 1px solid var(--border); border-radius: 10px; padding: 2px 12px; }
.ev .sh p { margin: 0 0 3px; } .ev .sh ul { margin: 0; padding: 0; list-style: none; } .ev .sh li { margin: 0 0 4px; display: flex; flex-wrap: wrap; align-items: center; gap: 3px 7px; }
.ev .sh .sh-n { color: var(--text-secondary); }
.ev details.t-rec { margin: 10px 0 0; border-top: 1px solid var(--border); padding-top: 6px; } .ev details.t-rec > summary { cursor: pointer; padding: 3px 0; }
.ev details.sf { margin: 4px 0 2px; } .ev details.sf > summary { cursor: pointer; }
.ev details.sf .sf-btn { display: inline-block; margin-left: 6px; padding: 0 8px; border: 1px solid var(--border); border-radius: 6px; font-size: var(--f-note); background: var(--surface-1, #fff); } .ev details.sf[open] .sf-o, .ev details.sf:not([open]) .sf-f { display: none; }
.ev table.sf-t { border-collapse: separate; border-spacing: 0; } .ev table.sf-t th, .ev table.sf-t td { padding: 4px 10px; border-bottom: 1px solid var(--grid, var(--border)); }
.ev table.sf-t thead th { color: var(--text-muted); font-weight: 600; }
.ev table.sf-t tr.sf-g td { padding: 7px 10px 6px; border-top: 8px solid var(--surface-1, #fff); border-bottom: 0; background: color-mix(in srgb, var(--text-primary) 7%, var(--surface-1, #fff)); border-radius: 7px; }
.ev table.sf-t .sf-kind { text-transform: uppercase; letter-spacing: .05em; font-size: var(--f-note); color: var(--text-secondary); font-weight: 600; } .ev table.sf-t .sf-kind .sw { margin-right: 5px; }
.ev table.sf-t .sf-id { font-size: var(--f-body, 14px); font-weight: 700; color: var(--text-primary); } .ev table.sf-t .sf-desc { display: block; font-size: var(--f-note); color: var(--text-secondary); font-weight: 400; margin-top: 1px; } .ev table.sf-t .sf-band { text-decoration: none; cursor: help; } .ev table.sf-t .sf-band .sf-id, .ev table.sf-t .sf-band:not(:has(.sf-id)) .sf-kind { text-decoration: underline dotted color-mix(in srgb, currentColor 55%, transparent); text-underline-offset: 3px; }
.ev table.sf-t .sf-chip { display: inline-block; margin-left: 8px; padding: 0 7px; border-radius: 999px; border: 1px solid var(--warning); color: var(--text-primary); font-size: var(--f-note); }
.ev table.sf-t td:first-child { padding-left: 18px; width: 36%; } .ev table.sf-t tr.sf-g td:first-child { padding-left: 10px; } .ev table.sf-t .sf-name { color: var(--text-secondary); }
.ev table.sf-t .sf-v { font-weight: 650; color: var(--text-primary); font-variant-numeric: tabular-nums; } .ev table.sf-t .sf-u { color: var(--text-muted); font-size: var(--f-note); }
.ev table.sf-t td.sf-was, .ev table.sf-t td.sf-was .sf-v { color: var(--text-muted); font-weight: 400; } .ev table.sf-t th.sf-was { font-weight: 400; }
.ev table.sf-t tr.sf-diff td { background: color-mix(in srgb, var(--warning) 13%, var(--surface-1, #fff)); } .ev table.sf-t tr.sf-diff td:first-child { box-shadow: inset 3px 0 0 var(--warning); } .ev table.sf-t tr.sf-diff .sf-name { color: var(--text-primary); font-weight: 600; }
.ev table.sf-t tr.sf-diff td.sf-was, .ev table.sf-t tr.sf-diff td.sf-was .sf-v { color: var(--text-secondary); } .ev table.sf-t .sf-ne { color: var(--warning); font-weight: 700; margin-left: 2px; }
`;
  const st = document.createElement('style'); st.id = 'ev-chain-css'; st.textContent = css; document.head.appendChild(st);
})();

Object.assign(EV, {
  // the changes a simulation made to the brief's network, in words; '' when it ran on the network as the brief gives it
  simNet(s) { return s && Array.isArray(s.structure) && s.structure.length && EV.editsSay ? EV.editsSay(s.structure) : ''; },
  chSame(a, b) { return JSON.stringify(a) === JSON.stringify(b); },
  // the session has ended and the page shows all of it (stepped back, nothing is said to be final)
  chDone() { return !!(EV.M && EV.M.ended) && EV.s.step == null; },
  // plain names for the settings and measures of the objects a simulation added to the network (what the brief's network named stays as it was said)
  simNames(s) {
    if (!s || !s.topology || !EV.netApply || s._named) return; s._named = 1;
    EV.NET_SAYS = EV.NET_SAYS || {};
    const keep = [TH_DATA.KNOB, EV.LABEL, TH_DATA.PLAIN, EV.SET_UNIT, TH_DATA.UNIT, EV.NET_SAYS].filter(Boolean).map(o => [o, { ...o }]);
    try { EV.netApply({ id: `${EV.M.id}|${s.id}`, topology: s.topology }); } catch (err) { /* names stay raw */ }
    keep.forEach(([o, was]) => Object.assign(o, was));
  },
  chName(k) { return (EV.LABEL && EV.LABEL[k]) || TH_DATA.KNOB[k] || k; },
  chMeasure(k) { return TH_DATA.PLAIN[k] || k; },
  // the measures a decision rule reads (the names before @), kept when a simulation of the test recorded them: the brief's, an added object's,
  // or one the experiment defined itself
  chainMeasures(T) {
    const have = new Set(T.sims.flatMap(s => Object.keys(s.metrics || {}))), out = [];
    for (const m of String(T.rule || '').matchAll(/([A-Za-z_][A-Za-z0-9_.]*)@/g)) if (have.has(m[1]) && !out.includes(m[1])) out.push(m[1]);
    return out.length ? out : EV.measuresOf(T.rule);
  },
  // the rows of a test: one per simulation its rule names, in the rule's order. s: its record once the page has reached it, else null (then the
  // setting is read from the experiment's plan and nothing is said of its outcome)
  chainRows(T) {
    const M = EV.M, x = M.expById[T.exp] || {}, runs = x.runs || [];
    const labels = T.labels && T.labels.length ? T.labels : T.sims.map(s => s.label);
    return labels.map(l => { const rec = T.sims.find(q => q.label === l), s = rec && EV.seen(rec.id) ? rec : null, r = runs.find(q => q.label === l) || {};
      return { label: l, s, params: (s && s.params) || r.params || {}, structure: (s && s.structure) || r.structure || null }; }).filter(r => r.s || Object.keys(r.params).length || r.structure)
      .map((r, i) => [r, i]).sort((a, b) => (a[0].structure && a[0].structure.length ? 1 : 0) - (b[0].structure && b[0].structure.length ? 1 : 0) || a[1] - b[1]).map(q => q[0]);
  },

  // 1 and 2: what was set, what came out. A simulation is a row; left of the rule, its setting (the cause); right of it, the measures (the effect).
  chainTable(T) {
    const M = EV.M, e = EV.e, rows = EV.chainRows(T), kn = (M.brief && M.brief.knobs) || {}; if (!rows.length) return '';
    rows.forEach(r => EV.simNames(r.s));
    const net = r => (Array.isArray(r.structure) && r.structure.length && EV.editsSay ? EV.editsSay(r.structure) : ''), anyNet = rows.some(net), netVary = new Set(rows.map(net)).size > 1;
    const keys = [...new Set(rows.flatMap(r => Object.keys(r.params)))];
    const vary = keys.filter(k => rows.some(r => !EV.chSame(r.params[k], rows[0].params[k])));
    // nothing differs between them (or there is one simulation): the settings that are not at the brief's default say what this simulation is
    const off = vary.length ? [] : keys.filter(k => kn[k] && 'default' in kn[k] && rows.some(r => k in r.params && !EV.chSame(r.params[k], kn[k].default)));
    const cols = vary.length ? vary : off, ms = EV.chainMeasures(T), x = M.expById[T.exp] || {}, own = new Set((x.measurements || []).map(m => m && m.name));
    const same = keys.filter(k => !cols.includes(k)), nSet = (anyNet ? 1 : 0) + Math.max(cols.length, anyNet ? 0 : 1);
    const val = (k, v) => (v == null ? '–' : EV.setVal ? EV.setVal(k, v) : String(v));
    const head = `<tr><th></th><th class="ch-g" colspan="${nSet}">what was set</th>${ms.length ? `<th class="ch-g ch-out ch-first" colspan="${ms.length}">what came out</th>` : ''}</tr>
      <tr><th>simulation</th>${anyNet ? '<th>network</th>' : ''}${cols.map(k => `<th>${e(EV.chName(k))}</th>`).join('')}${!cols.length && !anyNet ? '<th>settings</th>' : ''}
      ${ms.map((k, i) => `<th class="num${i ? '' : ' ch-first ch-out'}">${e(EV.chMeasure(k))}${own.has(k) ? ' <span class="sm" title="a measurement this experiment defined itself, computed by the harness from what the simulation recorded over time">ƒx</span>' : ''}</th>`).join('')}</tr>`;
    const body = rows.map(r => { const s = r.s, m = (s && s.metrics) || {};
      return `<tr data-sim="${e(s ? s.id : '')}" data-label="${e(r.label)}"><td>${s ? EV.link(s.id) : '<span class="mut">not run yet</span>'} <span class="ch-lab">${e(r.label || '')}</span>${s && s.same_as ? ` <span class="sm mut" title="the same settings, seed and network as ${e(s.same_as)}: its result was returned, nothing was run again">the result of ${e(s.same_as)}</span>` : ''}</td>
        ${anyNet ? `<td class="${netVary ? 'ch-dv' : ''}" data-ch="net">${net(r) ? e(net(r)) : '<span class="ch-lab">as given</span>'}</td>` : ''}
        ${cols.map(k => `<td class="${vary.length ? 'ch-dv' : ''}" data-k="${e(k)}">${e(val(k, r.params[k]))}</td>`).join('')}${!cols.length && !anyNet ? '<td class="ch-lab">all at the brief’s defaults</td>' : ''}
        ${ms.map((k, i) => `<td class="num${i ? '' : ' ch-first ch-out'}" data-m="${e(k)}">${s ? (s.error ? '<span class="bad">failed</span>' : EV.v4(k, m[k])) : '<span class="mut">–</span>'}</td>`).join('')}</tr>`; }).join('');
    const differs = [netVary ? 'the network' : '', ...vary.map(EV.chName)].filter(Boolean);
    const note = rows.length > 1 ? (differs.length ? `Between these simulations only ${e(differs.join(', '))} differ${differs.length === 1 ? 's' : ''} (in bold).` : 'These simulations were given the same setting.') : '';
    const sameSay = same.map(k => `${EV.chName(k)} ${val(k, rows[0].params[k])}`).join(' · ');
    return `<div class="ch-wrap"><table class="ch-t" data-test="${e(T.id)}"><thead>${head}</thead><tbody>${body}</tbody></table></div>
      <p class="sm ch-note">${note}${sameSay ? ` The same in all: ${e(sameSay)}${anyNet && !netVary ? '' : ''}.` : ''} Click a simulation for its records: its network, how ns-3 was started, every measure, the charts over time.</p>`;
  },

  // 4: the result. The harness's check of the rule, then the ruling (the supervisor's) or the verdict (the AI's), then what it did to the guesses.
  chainResult(T) {
    const M = EV.M, e = EV.e, c = T.check && EV.seen(T.check.id) ? T.check : null, v = T.verdict && EV.seen(T.verdict.id) ? T.verdict : null;
    const who = v && v.by === 'supervisor' ? 'supervisor' : 'model', R = v && v.by === 'supervisor' ? (T.rulings || []).find(r => r.id === v.id) || null : null;
    const first = v && v.because ? (EV.nbFirst ? EV.nbFirst(v.because) : [v.because, false]) : null;
    const ck = c ? `<span class="hp-badge ck-${c.void ? 'void' : e(c.result)}" data-ch="check">the rule ${EV.checkRes(c)}</span> <span class="sm">checked by the harness · ${EV.link(c.id)}</span>` : `<span class="mut">${EV.chDone() ? 'the rule was not checked' : 'the rule is not checked yet'}</span>`;
    const vd = v ? `<span class="ch-arrow">→</span> <span class="hp-badge ${EV.stCls(v.result)}" data-ch="verdict">hypothesis ${EV.verdictRes(v.result)}</span> <span class="sm">${who === 'supervisor' ? 'ruled by the supervisor' : 'judged by the AI'} in turn ${e(v.turn)} · ${EV.link(v.id)}</span>`
      : c ? `<span class="ch-arrow">→</span> <span class="mut">${EV.chDone() ? 'no verdict was given' : 'not judged yet'}</span>` : '';
    return `<p class="ch-res">${ck} ${vd}</p>${R && R.questions && R.fair === false ? '<p class="sm"><span class="warnc">The supervisor did not find this a fair test.</span></p>' : ''}
      ${first ? `<p class="ch-because"><span class="sm">${who === 'supervisor' ? 'the supervisor' : 'the AI'}:</span> <span data-own="${who}">${e(first[0])}</span>${first[1] ? ` <span class="sm">· in full: ${EV.link(v.id)}</span>` : ''}</p>` : ''}
      ${R && R.fits && EV.fitsRead ? EV.fitsRead(R) : ''}`;
  },

  // One test, from its simulations to its result.
  chainTest(T, n, of) {
    const e = EV.e, table = EV.chainTable(T), bars = T.rule && EV.ruleBars ? EV.ruleBars(T, 0, !(T.check && EV.seen(T.check.id) && !T.check.void)) : '';   // before its check is recorded: the rule alone, no measured number
    const k = (i, name, note) => `<p class="ch-k"><span class="ch-n">${i}</span>${name}${note ? ` <span class="sm">${note}</span>` : ''}</p>`;
    return `<div class="ch" data-chain="${e(T.id)}"><div class="ch-head"><b>${of > 1 ? `Test ${n} of ${of}` : 'Its test'}</b><span class="sm">experiment ${EV.link(T.exp)} · turn ${e(T.turn)}</span></div>
      <div class="ch-step" data-ch-step="set">${k(1, 'The simulations: what was set, and what came out', '')}${table || `<p class="sm mut">${EV.chDone() ? 'no simulation of this test is recorded' : 'its simulations are not recorded yet'}</p>`}</div>
      <div class="ch-step" data-ch-step="rule">${k(2, 'What the hypothesis required of these numbers', 'its decision rule, stated before the simulations ran')}${bars || (T.rule ? EV.ruleRead(T) : `<p class="sm mut">no decision rule is recorded</p>`)}</div>
      <div class="ch-step" data-ch-step="result">${k(3, 'The result', '')}${EV.chainResult(T)}</div></div>`;
  },

  // A hypothesis: every test of it the page has reached, each from its simulations to its result.
  chainCard(h) {
    const M = EV.M; if (!h) return '';
    const ts = (h.tests || []).map(q => M.testById[q]).filter(T => T && EV.seen(T.exp));
    if (!ts.length) return `<h3 class="f-h3">From this hypothesis to its result</h3><p class="sm mut" id="ch-none">${EV.chDone() ? 'It was not put to a test: no simulation was run for it.' : 'It has not been put to a test yet.'}</p>`;
    return `<h3 class="f-h3" id="ch-h">From this hypothesis to its result</h3>${ts.map((T, i) => EV.chainTest(T, i + 1, ts.length)).join('')}`;
  },

  // The full setting of a simulation, in one table: every setting of the network it ran on (by object: each link, its queues, each flow) and of the
  // run, beside the brief's value, with what this simulation has differently in bold; then what the program fixes for every simulation.
  // A network session only (the two-host program's options are all in the table of settings below; what its scenario fixes is in "The setting").
  simFull(s) {
    const M = EV.M, e = EV.e, b = M.brief || {}, t0 = b.topology; if (!t0 || !EV.netSettings || !EV.netWith) return '';
    const kn = b.knobs || {}, dflt = Object.fromEntries(Object.entries(kn).map(([k, q]) => [k, q.default]));
    const base = EV.netSettings(EV.netWith(t0, dflt)), t = EV.netWith(s.topology || t0, { ...dflt, ...(s.params || {}) }), mine = EV.netSettings(t);
    const val = (k, v) => (v == null ? '–' : EV.setVal ? EV.setVal(k, v) : String(v)), ids0 = new Set([...(t0.links || []), ...(t0.flows || []), ...(t0.hosts || [])].map(x => x.id));
    let n = 0, changed = 0;
    // a value as it is read: the number (or the word) strong, its unit or its note light
    const fig = text => { const x = String(text), m = /^([−-]?[\d.,]+)\s+(.+)$/.exec(x) || /^(.+?)\s+(\(.+\))$/.exec(x); return m ? `<span class="sf-v">${e(m[1])}</span> <span class="sf-u">${e(m[2])}</span>` : `<span class="sf-v">${e(x)}</span>`; };
    const mark = '<span class="sf-ne" title="not as in the brief">≠</span>';
    const row = (k, name, v, was, added) => { const diff = added || (was !== undefined && !EV.chSame(v, was)); n++; changed += diff ? 1 : 0;
      return `<tr data-k="${e(k)}"${diff ? ' class="sf-diff"' : ''}><td title="${e(k)}">${k in kn ? '<span title="the AI may change it">✦</span> ' : ''}<span class="sf-name">${e(name)}</span></td><td data-v="${e(String(v))}">${fig(val(k, v))}${diff ? ' ' + mark : ''}</td><td class="sf-was">${added ? 'not in the brief' : was === undefined ? '–' : fig(val(k, was))}</td></tr>`; };
    const group = (kind, id, pop, rows, color, added) => (rows.length ? `<tr class="sf-g"><td colspan="3">${EV.objBand(`${s.id}|set|${kind}|${id || ''}`, kind, id, pop, color)}${added ? ' <span class="sf-chip">added by this simulation</span>' : ''}</td></tr>${rows.join('')}` : '');
    const short = (k, id) => { const rest = k.slice(id.length + 1), W = { rate: 'rate', delay: 'one-way delay', mtu: 'largest packet', device_queue: 'device’s transmit queue', type: 'TCP type', packet_bytes: 'packet size', start: 'starts at', stop: 'stops at', on_time: 'on period', off_time: 'off period', max_bytes: 'stops after', loss: 'packets received in error' };
      return rest.split('.').map(w => W[w] || w.replace(/_/g, ' ')).join(' · ').replace(/^queue · length$/, 'queue length').replace(/^queue · parts · /, 'part of ').replace(/^queue · largest rate · /, 'largest rate of '); };
    const of = id => Object.keys(mine).filter(k => k === id || k.startsWith(id + '.')).map(k => row(k, short(k, id), mine[k], base[k], !ids0.has(id) || !(k in base)));
    // the queue in front of each device, where this simulation or the brief describes one: which queue disc it is
    const t0b = EV.netWith(t0, dflt), qSay = q => (q ? (q.kind === 'scheduler' ? 'scheduler (this project’s FlowQueueDisc)' : EV.netDisc ? `${EV.netDisc(q.kind)[0]} (ns-3 ${EV.netDisc(q.kind)[1]})` : q.kind) : 'a plain queue of 100 packets (none described)');
    const qRows = l => { const l0 = (t0b.links || []).find(x => x.id === l.id), E = EV.netEnds(l), E0 = l0 ? EV.netEnds(l0) : {};
      return l.between.map(h => { const q = (E[h] || {}).queue || null, q0 = (E0[h] || {}).queue || null; if (!q && !q0) return ''; const diff = !l0 || (q ? q.kind : 'none') !== (q0 ? q0.kind : 'none'); n++; changed += diff ? 1 : 0;
        return `<tr data-k="${e(`${l.id}.${h}.queue.kind`)}"${diff ? ' class="sf-diff"' : ''}><td><span class="sf-name">queue on ${e(h)}’s side</span></td><td data-v="${e(q ? q.kind : 'none')}">${fig(qSay(q))}${diff ? ' ' + mark : ''}</td><td class="sf-was">${l0 ? fig(qSay(q0)) : 'not in the brief'}</td></tr>`; }).filter(Boolean); };
    const path = f => { const w = EV.netPath ? EV.netPath(t, f) : null; return w && w.length ? 'by ' + w.map(q => q[0]).join(', ') : ''; };
    const links = (t.links || []).map(l => { const E = EV.netEnds(l), qOf = h => { const q = (E[h] || {}).queue; return q ? (EV.netDisc ? EV.netDisc(q.kind)[0] : q.kind) : 'a plain queue of 100 packets'; };
      return group('link', e(l.id), { what: 'a point-to-point link: a channel and a device at each end', facts: [['Joins', l.between.join(' – ')], ...l.between.map(h => [`Queue on ${h}’s side`, qOf(h)]), ...(ids0.has(l.id) ? [] : [['In the brief', 'no: this simulation added it']])] },
        [...qRows(l), ...of(l.id)], '', !ids0.has(l.id)); }).join('');
    const flows = (t.flows || []).map(f => { const bulk = (f.app || (f.kind === 'udp' ? 'onoff' : 'bulk')) === 'bulk';
      return group('flow', e(f.id), { what: `${f.kind.toUpperCase()} · ns-3 ${bulk ? 'BulkSendApplication' : 'OnOffApplication'}`, facts: [['From, to', `${f.from} → ${f.to}`], ['Its way', path(f).replace(/^by /, '') || 'not found'], ['Sends', bulk ? 'always has data: as fast as TCP accepts' : 'packets at a constant rate'], ...(ids0.has(f.id) ? [] : [['In the brief', 'no: this simulation added it']])] },
        of(f.id), EV.netColor ? EV.netColor(t, f.id) : '', !ids0.has(f.id)); }).join('');
    const sys = b.system || {}, runKeys = Object.keys(s.params || {}).filter(k => !(k in mine)), RUN = { seed: 'seed', duration: 'measured time', tcpInitCwnd: 'TCP’s first window', tcpBufBytes: 'TCP’s buffers', tcpSack: 'TCP selective acknowledgement', tcpTimestamps: 'TCP timestamps', tcpDelAck: 'segments per acknowledgement' };
    const run = group('the run', '', { what: 'settings of the simulation', lead: 'What belongs to no object of the network: how long is measured, and the seed of the random numbers.' }, runKeys.map(k => row(k, RUN[k] || EV.chName(k), s.params[k], k in kn ? kn[k].default : sys[k], false)));
    const gone = [...(t0.links || []).map(x => ['link', x.id]), ...(t0.flows || []).map(x => ['flow', x.id]), ...(t0.hosts || []).map(x => ['host', x.id])].filter(([kind, id]) => ![...(t.links || []), ...(t.flows || []), ...(t.hosts || [])].some(x => x.id === id));
    const p = s.params || {}, fx = (name, v) => `<tr class="sf-fx"><td><span class="sf-name">${e(name)}</span></td><td colspan="2">${fig(v)}</td></tr>`;
    const fixed = `<tr class="sf-g"><td colspan="3">${EV.objBand(`${s.id}|set|program|`, 'set by the program', '', { what: 'fixed in the program', lead: 'The same for every simulation: no setting of a brief, and not the AI’s to change.' }, '')}</td></tr>`
      + [['traffic starts at', '1 s (each flow up to 10 ms later, by the seed)'], ['not measured', '1 s (the first second of traffic)'], ['a sample of the series', '0.1 s (between two samples)'], ['TCP’s buffers', p.tcpBufBytes ? 'as set above' : '1 MB (each)'],
         ['TCP’s first window', p.tcpInitCwnd ? 'as set above' : '10 segments'], ['a full TCP segment', 'one packet (of the smallest MTU)'], ['TCP’s shortest retransmission timeout', '1 s (ns-3’s own)'],
         ['a device without a described queue', '100 packets (a plain queue in front of it, ns-3 FifoQueueDisc)'], ['the way of a flow', 'the fewest links']].map(q => fx(q[0], q[1])).join('');
    const hosts = `${(t.hosts || []).length} hosts: ${(t.hosts || []).map(h => e(h.id) + (ids0.has(h.id) ? '' : ' (added)')).join(', ')}`;
    return `<details class="sf" id="sim-full" data-n="${n}" data-changed="${changed}"${EV.store && EV.store('ev-simfull') === '0' ? '' : ' open'}><summary><b>The full setting</b> <span class="sm">all ${n} values of the network and the run as this simulation had them${changed ? `, ${changed} of them not as in the brief (marked ≠)` : ', every one as in the brief'}</span> <span class="cl noprint sf-btn" aria-hidden="true"><span class="sf-o">show the table</span><span class="sf-f">fold</span></span></summary>
      <p class="sm">${hosts}${gone.length ? ` · <b>removed by this simulation</b>: ${e(gone.map(q => q.join(' ')).join(', '))}` : ''}</p>
      <div class="ch-wrap"><table class="ch-t sf-t"><thead><tr><th>setting</th><th>this simulation</th><th class="sf-was">the brief</th></tr></thead><tbody>${links}${flows}${run}${fixed}</tbody></table></div>
      <p class="sm ch-note">✦ the AI may change it; every other value is fixed by the operator. The picture in “The setting” at the top of the page shows this simulation’s network.</p></details>`;
  },

  // A simulation's pane in four parts, each said once (2026-11-24, the operator: "add the outcome of the simulation and remove redundancy"):
  // 1 Setting (what differs from the brief in a line, then the full setting), 2 Outcome (who read it, then every measure by object), 3 Over time
  // (the charts, from EV.resultPanel), 4 Records (the run's files and how ns-3 was started). For a session on a network whose experiment has no control;
  // every other simulation keeps the head and the two tables it had.
  simNew(s, ctl) { const b = (EV.M && EV.M.brief) || {}; return !!(s && !s.src && !ctl && b.topology && EV.netSettings && EV.netWith); },
  spHead(n, name, note) { return `<h3 class="sp-h"><span class="ch-n">${n}</span>${name}${note ? ` <span class="sm">${note}</span>` : ''}</h3>`; },
  simSetting(s) {
    const P = EV.simHead(s, true);
    return `<div class="sp" data-sp="setting" data-sh="setting">${EV.spHead(1, 'Setting', 'what this simulation was given')}<div class="sp-sum">${P.setting}</div>${EV.simFull(s)}</div>`;
  },
  simOutcome(s) {
    const M = EV.M, e = EV.e, P = EV.simHead(s, true), m = s.metrics || {}, t = s.topology || (M.brief || {}).topology || {}, x = M.expById[s.exp] || {};
    const own = new Set((x.measurements || []).map(q => q && q.name)), keys = Object.keys(m);
    // who read what here: a measure -> the tests whose decision rule reads it at this simulation
    const by = {}; P.ts.forEach(T => P.reads(T).forEach(k => (by[k] = by[k] || []).push(T)));
    const badge = T => { const c = T.check && EV.seen(T.check.id) ? T.check : null, v = T.verdict && EV.seen(T.verdict.id) ? T.verdict : null;
      return `${EV.link(T.hyp)}${v ? ` <span class="hp-badge ${EV.stCls(v.result)}">${EV.verdictRes(v.result)}</span>` : c ? ` <span class="hp-badge ck-${c.void ? 'void' : e(c.result)}">the rule ${EV.checkRes(c)}</span>` : ''}`; };
    const show = (k, v) => { const [u, f] = EV.unit(k); return typeof v !== 'number' ? '<span class="sf-v">–</span>' : `<span class="sf-v">${(+f(v).toPrecision(7)).toLocaleString('en-US')}</span>${u ? ` <span class="sf-u">${e(u)}</span>` : ''}`; };
    const row = k => `<tr data-m="${e(k)}"${by[k] ? ' class="so-read"' : ''}><td><span class="sf-name">${e(EV.chMeasure(k))}</span>${own.has(k) ? ' <span class="sm" title="a measurement this experiment defined itself, computed by the harness from what the simulation recorded over time">ƒx</span>' : ''}</td><td data-v="${e(String(m[k]))}">${show(k, m[k])}</td><td class="so-by">${by[k] ? by[k].map(badge).join(' ') : ''}</td></tr>`;
    // each measure under the object it is measured at: the flow or the link whose name it begins with (the longest name that fits)
    const objs = [...(t.flows || []).map(f => ['flow', f.id]), ...(t.links || []).map(l => ['link', l.id])], home = k => objs.filter(o => k.startsWith(o[1] + '_')).sort((a, b) => b[1].length - a[1].length)[0];
    const band = (kind, id, note, color) => `<tr class="sf-g"><td colspan="3">${EV.objBand(`${s.id}|out|${kind}|${id || ''}`, kind, id ? e(id) : '', note ? { what: 'measures', lead: note } : kind === 'flow' ? { what: 'measured at its receiver', lead: 'What arrived of this flow over the measured seconds, and what its sender had to send again or lost.' } : kind === 'link' ? { what: 'measured at its devices and queues', lead: 'How much of the link’s rate was used in each direction, and the packets dropped from the queues in front of it.' } : null, color)}</td></tr>`;
    const groups = objs.map(o => { const ks = keys.filter(k => !own.has(k) && (home(k) || [])[1] === o[1] && (home(k) || [])[0] === o[0]); return ks.length ? band(o[0], o[1], '', o[0] === 'flow' && EV.netColor ? EV.netColor(t, o[1]) : '') + ks.map(row).join('') : ''; }).join('');
    const rest = keys.filter(k => !own.has(k) && !home(k)), mine = keys.filter(k => own.has(k));
    const table = s.error ? `<p class="bad">No measurements: ${e(s.error)}</p>` : !keys.length ? `<p class="sm mut">no measurement is recorded</p>`
      : `<div class="ch-wrap"><table class="ch-t sf-t so-t" id="sim-out"><thead><tr><th>measure</th><th>value</th><th class="sf-was">read by</th></tr></thead><tbody>${groups}${rest.length ? band('other', '', '') + rest.map(row).join('') : ''}${mine.length ? band('defined by the experiment', '', 'Measurements this experiment defined itself: computed by the harness from what the simulation recorded over time.') + mine.map(row).join('') : ''}</tbody></table></div>`;
    const used = P.ts.length ? `<p class="sp-sum">${P.ts.map(T => `<span data-used="${e(T.id)}">${badge(T)}</span>`).join(' · ')} <span class="sm">${P.ts.length === 1 ? 'read this simulation: the measure its rule reads is marked' : 'read this simulation: the measures their rules read are marked'}</span></p>`
      : `<p class="sp-sum sm">${s.exp === 'X0' ? 'The baseline: run by the harness before the first turn. No decision rule names it.' : 'No decision rule names this simulation.'}</p>`;
    return `<div class="sp" data-sp="outcome" data-sh="used">${EV.spHead(2, 'Outcome', 'what was measured, over the measured seconds')}${used}${table}</div>`;
  },
  simRecords(s, cmd) {
    const P = EV.simHead(s, true);
    return `<div class="sp" data-sp="records" data-sh="records">${EV.spHead(4, 'Records', 'the files of this run, and how it was started')}${P.records}${cmd || ''}</div>`;
  },

  // The band that heads an object's rows: its kind and its name. What the object is opens in a box on hover or Tab (the page's own box, data-wd "o:<key>"):
  // pop = { what: the chip beside the name, lead: a sentence, facts: [[label, value], ...] }, kept by key until the pane is drawn again.
  OBJ_SAYS: {},
  objBand(key, kind, id, pop, color) {
    const e = EV.e; if (pop) EV.OBJ_SAYS[key] = { title: `${kind}${id ? ' ' + id : ''}`, ...pop };
    const name = `<span class="sf-kind">${color ? `<i class="sw" style="background:${color}"></i>` : ''}${kind}</span>${id ? ` <b class="sf-id">${id}</b>` : ''}`;
    return pop ? `<span class="wd sf-band" data-wd="o:${e(key)}" tabindex="0">${name}</span>` : name;
  },
  objPop(key) {
    const e = EV.e, p = EV.OBJ_SAYS[key]; if (!p) return '';
    return `<p class="wd-h"><b>${e(p.title)}</b>${p.what ? `<span class="wd-kind">${e(p.what)}</span>` : ''}</p>${p.lead ? `<p class="wd-lead">${e(p.lead)}</p>` : ''}${p.facts && p.facts.length ? `<dl class="wd-kv">${p.facts.map(([k, v]) => `<dt>${e(k)}</dt><dd>${e(v)}</dd>`).join('')}</dl>` : ''}`;
  },

  // The head of a simulation's panel: its setting, who used it, its records.
  simHead(s, parts) {
    const M = EV.M, e = EV.e; if (!s || s.src) return '';   // (an operator's run has no session records)
    EV.simNames(s);
    const kn = (M.brief && M.brief.knobs) || {}, net = EV.simNet(s), isNet = !!(M.brief && M.brief.topology);
    const off = Object.keys(s.params || {}).filter(k => kn[k] && 'default' in kn[k] && !EV.chSame(s.params[k], kn[k].default));
    const val = (k, v) => (EV.setVal ? EV.setVal(k, v) : String(v));
    const setting = `${isNet ? `<p><span class="sh-n">network</span> ${net ? `<b>changed</b>: ${e(net)}` : 'as the brief gives it'}</p>` : ''}
      <p><span class="sh-n">settings</span> ${off.length ? off.map(k => `<b>${e(EV.chName(k))} ${e(val(k, s.params[k]))}</b> <span class="sm">(the brief’s default: ${e(val(k, kn[k].default))})</span>`).join(' · ') + ' <span class="sm">· every other setting at its default</span>' : 'every setting at the brief’s default'}</p>${parts ? '' : EV.simFull(s)}`;
    const ts = M.tests.filter(T => EV.seen(T.exp) && T.sims.some(q => q.id === s.id));
    const reads = T => { const out = []; for (const m of String(T.rule || '').matchAll(/([A-Za-z_][A-Za-z0-9_.]*)@([A-Za-z0-9_]+)/g)) if (m[2] === s.label && !out.includes(m[1])) out.push(m[1]); return out; };
    const used = ts.length ? `<ul>${ts.map(T => { const c = T.check && EV.seen(T.check.id) ? T.check : null, v = T.verdict && EV.seen(T.verdict.id) ? T.verdict : null, ms = reads(T).filter(k => s.metrics && k in s.metrics);
      return `<li data-used="${e(T.id)}">${EV.link(T.hyp)}${v ? ` <span class="hp-badge ${EV.stCls(v.result)}">${EV.verdictRes(v.result)}</span>` : c ? ` <span class="hp-badge ck-${c.void ? 'void' : e(c.result)}">the rule ${EV.checkRes(c)}</span>` : ''}
        <span class="sm">${ms.length ? 'its rule reads here: ' + ms.map(k => `${e(EV.chMeasure(k))} ${EV.v4(k, s.metrics[k])}`).join(' · ') : 'its rule names this simulation'}</span></li>`; }).join('')}</ul>`
      : `<p class="sm">${s.exp === 'X0' ? 'The baseline: every setting at its default, run by the harness before the first turn. No decision rule names it.' : 'No decision rule names this simulation.'}</p>`;
    const base = s.run ? `../sessions/${e(M.id)}/runs/${e(s.run)}/` : null, file = (f, say) => `<a href="${base}${f}" target="_blank" rel="noopener" title="${e(say)}">${f}</a>`;
    const records = base ? `<p>run ${e(s.run)} · ${isNet ? file('network.txt', 'the network as this simulation ran it, written by the harness') + ' · ' : ''}${file('params.json', 'the settings the program was given')} · ${file('metrics.json', 'the measures over the measured seconds, as the program wrote them')} · ${file('series.csv', 'a sample every 0.1 s of the whole run')}</p>
      <p class="sm">the files ns-3 read and wrote for this run, as they are on the server; the measures and the charts below are drawn from them</p>` : `<p class="sm mut">no run id is recorded</p>`;
    if (parts) return { setting, used, ts, reads, records };
    const row = (name, body, k) => `<div class="td-l" data-sh="${k}"><span class="td-k">${name}</span><div class="td-v">${body}</div></div>`;
    return `<div class="sh td td-top" id="sim-head">${row('Setting', setting, 'setting')}${row('Used by', used, 'used')}${row('Records', records, 'records')}</div>`;
  },
});

// the full setting of a simulation: the browser remembers whether a reader keeps it open
document.getElementById('ev').addEventListener('click', ev => {
  if (!(ev.target.closest && ev.target.closest('#sim-full > summary'))) return;
  setTimeout(() => { const d = document.getElementById('sim-full'); if (d && EV.store) EV.store('ev-simfull', d.open ? '1' : '0'); }, 0);
});
// a test's older sections, record by record, under its chain: folded on the lean page; the browser remembers when a reader opens them
document.getElementById('ev').addEventListener('click', ev => {
  if (!(ev.target.closest && ev.target.closest('#t-rec > summary'))) return;
  setTimeout(() => { const d = document.getElementById('t-rec'); if (!d || !EV.store) return; EV.store('ev-trec', d.open ? '1' : '0'); if (d.open && EV.flowFit) EV.flowFit(); }, 0);
});
