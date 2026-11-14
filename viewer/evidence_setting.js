// "The setting": what the network is, what the AI was asked, and what it could and could not see, in seven blocks.
// "New session" (the set-up page: evidence_run.js and brief_editor.js) has the same seven blocks, in the same order,
// built from the same pieces: there each block is a form, here each shows the recorded values, read-only, in the same
// place and the same words.
//   1 The network          the picture of the system (evidence_system.js); a click on a part shows its values
//   2 Who decides what     each setting: fixed by the operator (a value), or the AI may change it (a range, a step)
//   3 The aim              the aim as set, and who set it
//   4 What the AI is told, is not told, and can do    three lists built from the brief and from the tools the harness
//                          offers, and the exact text the AI was given (what describe_system() returns, word for word)
//   5 The limits           simulations in all and in one experiment, and how many were used
//   6 Kept from the AI     the scheduling policy: shown only with the operator columns on
//   7 How the AI runs      the options the session was started with
// In Brief the blocks 5 to 7 are one line each. Nothing here is written by hand about a session: every value is the
// session's own record (session.json: what it was given, its flags), a line of control.py's list (the policy), or a
// count the page makes from the ledger (the simulations used).
// ======================================================================================================
Object.assign(EV, {
  // [key, heading, the one plain sentence that says what the block is for, the piece that fills it]
  SET_BLOCKS: [
    ['network', 'The network', 'Two computers and one link: where each setting acts.', 'picture'],
    ['who', 'Who decides what', 'Each setting is fixed by the operator or left to the AI within a range.', 'settings'],
    ['aim', 'The aim', 'What counts as a good result, and who chose it.', 'aim'],
    ['told', 'What the AI is told, is not told, and can do', 'All the AI has to work with, and what is kept back.', 'lists'],
    ['limits', 'The limits', 'How many simulations the AI may run.', 'limits'],
    ['kept', 'Kept from the AI (operator)', 'How the scheduler divides the link: the AI has to find that out.', 'policy'],
    ['runs', 'How the AI runs', 'The options a session is started with.', 'flags'],
  ],
  // the settings by plain words; the field name and the brief's own line about it are on hover
  LABEL: { linkRate: 'link rate', linkDelay: 'link delay', mtu: 'largest packet', udpPacketBytes: 'UDP packet size', weightUdp: 'ratio', udpRate: 'UDP rate', queuePkts: 'queue length', queuePktsUdp: 'UDP queue length',
           queuePktsTcp: 'TCP queue length', tcpVariant: 'TCP type', duration: 'measured time', seed: 'seed' },
  SET_ORDER: ['linkRate', 'linkDelay', 'mtu', 'udpPacketBytes', 'udpRate', 'weightUdp', 'queuePkts', 'queuePktsUdp', 'queuePktsTcp', 'tcpVariant', 'duration', 'seed'],
  SET_UNIT: { mtu: 'bytes', udpPacketBytes: 'bytes', queuePkts: 'packets', queuePktsUdp: 'packets', queuePktsTcp: 'packets', duration: 's' },
  POLICY_SAYS: { share: 'a flow may use what the other leaves unused', cap: 'each flow is held to its configured part of the link', random: 'the harness chooses share or cap and records it under checks/' },
  FLAGS: [['budget', 'simulations allowed at the start', "the brief's limit"], ['draft', 'draft before the answer', 'on'], ['max_tokens', 'most tokens of one answer', '32000 with a draft, 3000 without'], ['temperature', 'temperature', '0.3'], ['baseline', 'baseline simulation first', 'on']],
  // the tools of the harness in plain words (a tool the manifest names and this list does not is shown by its own name)
  TOOL_SAYS: { describe_system: 'read the brief again', metrics: "ask for a simulation's measures", series: 'ask for its series (a sample every 0.1 s)', grep_trace: 'search its flow record', list_runs: 'list its simulations so far' },
  // what each setting is, in the page's own words: shown on hover where the brief has no line about it (a fixed setting)
  SET_SAYS: { linkRate: 'the rate of the link between the two computers', linkDelay: 'the time a bit takes to cross the link, one way', mtu: 'the largest packet the link carries', udpPacketBytes: 'the size of each UDP packet; the scenario fixes it', udpRate: 'the rate at which the UDP application sends',
              weightUdp: 'the part of the link configured for UDP; TCP gets the rest', queuePkts: 'how many packets each queue holds', queuePktsUdp: 'how many packets the UDP queue holds', queuePktsTcp: 'how many packets the TCP queue holds', tcpVariant: 'the congestion control of the TCP sender', duration: 'the seconds of traffic that are measured', seed: 'the random seed of a simulation' },
  label(k, meaning) { return `<abbr class="st-l" title="${EV.e(`${meaning || EV.SET_SAYS[k] || ''} (field: ${k})`.trim())}">${EV.e(EV.LABEL[k] || k)}</abbr>`; },
  setVal(k, v) { return v == null || v === '' ? 'not recorded' : TASK_VIEW._rate(String(v)).replace(/^Tcp/, '') + (EV.SET_UNIT[k] && /^[-\d.]+$/.test(String(v)) ? ' ' + EV.SET_UNIT[k] : ''); },
  // a knob's range in words: "0.05 to 0.95, in steps of 0.01" or its choices
  setRange(k, s) { return s.choices ? s.choices.map(c => String(c).replace(/^Tcp/, '')).join(', ') : `${EV.SET_UNIT[k] ? String(s.min) : EV.setVal(k, s.min)} to ${EV.setVal(k, s.max)}${s.step != null && s.step !== '' ? ', in steps of ' + s.step : ''}`; },
  // a goal in words, from its fields: "the largest TCP goodput, while UDP loss <= 1 %"
  aimWords(g) {
    if (!g || g.kind === 'open') return null; const t = g.target || {}, conds = (g.conditions || []).map(c => EV.readHtml(c) || EV.e(c));
    return `the ${t.direction === 'min' ? 'smallest' : 'largest'} ${EV.e(TH_DATA.PLAIN[t.measure] || t.measure || 'measure not recorded')}${conds.length ? ', while ' + conds.join(' and ') : ''}`;
  },

  // ---- the pieces. c: { mode: 'session' | 'setup', b: the brief (its description filled in), man: the manifest's outputs and tools, flags, model, policy, policyHidden, op, used }
  // 2 · who decides what: one line per setting, in a fixed order; the two colours are those of the picture
  setWho(c) {
    const b = c.b, e = EV.e, sys = b.system || {}, kn = b.knobs || {}, keys = EV.SET_ORDER.filter(k => k in sys || k in kn).concat(Object.keys({ ...sys, ...kn }).filter(k => !EV.SET_ORDER.includes(k)));
    const row = k => (k in kn ? `<tr data-k="${e(k)}" data-set="knob"><td>${EV.label(k, kn[k].meaning)}</td><td><span data-by="model"><i class="sw"></i>the AI may change it</span></td><td>${e(EV.setRange(k, kn[k]))} <span class="sm" title="the value it starts from: the brief's default">from ${e(EV.SET_UNIT[k] ? String(kn[k].default) : EV.setVal(k, kn[k].default))}</span></td></tr>`
      : `<tr data-k="${e(k)}" data-set="fixed"><td>${EV.label(k)}</td><td><span data-by="operator"><i class="sw"></i>fixed by the operator</span></td><td>${e(EV.setVal(k, sys[k]))}</td></tr>`);
    return keys.length ? `<table class="st-who"><tbody>${keys.map(row).join('')}</tbody></table>` : `<p class="sm">the settings: ${EV.nr}</p>`;
  },
  // 3 · the aim, and who set it. An open aim: the one the AI chose is the goal of its final report (c.chosen)
  setAim(c) {
    const g = c.b.goal || {}, e = EV.e, w = EV.aimWords(g);
    if (g.kind === 'open') return `<p data-aim="open"><b>Open:</b> the AI chooses its own aim and has to justify it. <span class="st-by" data-by="model"><i class="sw"></i>chosen by the AI</span></p>${c.mode === 'session' ? `<p class="sm lc4" id="st-chosen">${c.chosen ? `It chose: ${e(c.chosen)}` : c.ended ? 'It stated no aim: there is no final report.' : 'It has not stated its aim yet.'}</p>` : ''}`;
    if (!w) return `<p class="sm">the aim: ${EV.nr}</p>`;
    return `<p data-aim="given"><b>Find ${w}.</b> <span class="st-by" data-by="operator"><i class="sw"></i>set by the operator</span></p>${g.tolerance != null && g.tolerance !== '' ? `<p class="sm">Tolerance ${e(g.tolerance)} %: two results closer than this count as equal.</p>` : ''}`;
  },
  // 4 · the three lists, built from the brief, the flags and the manifest (the outputs and the tools the harness offers)
  setLists(c) {
    const b = c.b, e = EV.e, sys = b.system || {}, kn = b.knobs || {}, man = c.man || {}, lim = b.limits || {}, order = k => EV.SET_ORDER.filter(q => q in k), outs = Object.keys(man.outputs || {}), tools = Object.keys(man.tools || {});
    const it = (key, html, title) => `<li data-it="${key}"${title ? ` title="${e(title)}"` : ''}>${html}</li>`;
    const told = [it('task', 'the task', b.task), it('description', 'the description of the system', b.description),
      `<li data-it="fixed" data-keys="${e(order(sys).join(','))}" title="${e(order(sys).map(k => `${EV.LABEL[k] || k} ${EV.setVal(k, sys[k])}`).join(', '))}">the ${order(sys).length} fixed settings <span class="sm">(block 2)</span></li>`,
      `<li data-it="knobs" data-keys="${e(order(kn).join(','))}" title="${e(order(kn).map(k => `${EV.LABEL[k] || k} ${EV.setRange(k, kn[k])}`).join('; '))}">the ${order(kn).length} knobs and their ranges <span class="sm">(block 2)</span></li>`,
      `<li data-it="goal" data-kind="${e((b.goal || {}).kind || '')}">${(b.goal || {}).kind === 'open' ? 'that the goal is open: it has to state its own' : 'the goal <span class="sm">(block 3)</span>'}</li>`,
      `<li data-it="limits" data-sims="${e(lim.simulations ?? '')}" data-per="${e(lim.simulations_per_experiment ?? '')}">the limits <span class="sm">(block 5)</span></li>`,
      c.flags && (c.flags.baseline === false || c.flags.baseline === 'off') ? '' : it('baseline', `the baseline simulation${c.flags ? '' : ' (if the session ran one: not recorded)'}`, 'Every knob at its default, run by the harness before the first turn'),
      `<li data-it="measures" data-keys="${e(outs.join(','))}">the ${outs.length} measures of each simulation: ${outs.map(k => `<abbr title="${e(k + ': ' + man.outputs[k])}">${e(String(TH_DATA.PLAIN[k] || k).toLowerCase().replace(/\b(udp|tcp)\b/g, q => q.toUpperCase()))}</abbr>`).join(', ') || 'not recorded'}</li>`,
      it('record', "its own record so far, and the harness's notes")].join('');
    const not = [it('policy', 'the scheduling policy'), it('code', "the simulator's code"), it('operator', "the operator's checks, sweeps, answer key and scores"), it('sessions', 'any other session')].join('');
    const can = [it('plan', 'plan simulations within the limits'), it('set', 'set the knobs'),
      ...tools.map(t => `<li data-it="tool" data-tool="${e(t)}" title="${e(t + ': ' + man.tools[t])}">${e(EV.TOOL_SAYS[t] || t)}</li>`), it('state', 'state hypotheses, decision rules, verdicts and a final report')].join('');
    const cannot = [it('change', 'change the code or a fixed setting'), it('exceed', 'exceed the limits'), it('more', 'see more of a simulation than its measures')].join('');
    const was = c.mode === 'setup' ? 'will be' : 'was';
    return `<div class="st-lists"><div data-list="told"><h4>The AI is told</h4><ul>${told}</ul></div><div data-list="not"><h4>The AI is not told</h4><ul>${not}</ul></div>
        <div data-list="can"><h4>The AI can</h4><ul>${can}</ul><h4>It cannot</h4><ul data-list="cannot">${cannot}</ul></div></div>
      <details class="st-exact" id="st-exact"${EV.s.exact ? ' open' : ''}><summary>the exact text the AI ${was} given</summary><p class="sm">What the harness's <code>describe_system()</code> returns for this ${c.mode === 'setup' ? 'set-up' : 'session'}, word for word: the brief, then the measures and the tools.</p><pre id="st-given">${c.given ? e(JSON.stringify(c.given, null, 1)) : 'not recorded'}</pre></details>`;
  },
  // 5 · the limits (and, on a session, how many simulations were used)
  setLimits(c) { const l = c.b.limits || {}, e = EV.e;
    return `<p><b>${e(l.simulations ?? 'not recorded')}</b> simulations in all · <b>${e(l.simulations_per_experiment ?? 'not recorded')}</b> in one experiment${c.mode === 'session' ? ` · <span id="st-used"><b>${e(c.used ?? 'not recorded')}</b> used</span>` : ''}</p>`; },
  // 6 · kept from the AI: the scheduling policy, only with the operator columns on
  setKept(c) {
    if (!c.op) return `<p class="mut" id="st-kept" data-shown="0">The scheduling policy: shown with the operator columns on.</p>`;
    return `<p id="st-kept" data-shown="1" data-by="operator"><i class="sw"></i>scheduling policy: <b>${c.policyHidden ? 'chosen by the harness: shown once the session is scored' : EV.e(c.policy || 'not recorded')}</b>${!c.policyHidden && EV.POLICY_SAYS[c.policy] ? ` <span class="sm">· ${EV.e(EV.POLICY_SAYS[c.policy])}</span>` : ''} <span class="sm">· never told to the AI</span></p>`;
  },
  // 7 · how the AI runs: the flags, each beside its default
  setRuns(c) { const f = c.flags, e = EV.e, show = v => (v === true ? 'on' : v === false ? 'off' : v == null ? 'the default' : String(v));
    return `<table class="st-flags"><tbody>${c.mode === 'session' ? `<tr data-flag="model"><td>model</td><td><b>${e(c.model || 'not recorded')}</b></td><td class="sm">taken from the model server</td></tr>` : ''}${EV.FLAGS.map(([k, name, dflt]) => `<tr data-flag="${k}"><td>${e(name)}</td><td><b>${f ? e(show(f[k])) : 'not recorded'}</b></td><td class="sm">default: ${e(dflt)}</td></tr>`).join('')}</tbody></table>`; },
  // one line that carries a folded block's content
  setLine(key, c) { const l = c.b.limits || {}, f = c.flags || {}, e = EV.e;
    return key === 'limits' ? `${e(l.simulations ?? 'not recorded')} simulations in all, ${e(l.simulations_per_experiment ?? 'not recorded')} in one experiment${c.mode === 'session' ? `, ${e(c.used ?? 'not recorded')} used` : ''}`
      : key === 'kept' ? (c.op ? `scheduling policy ${c.policyHidden ? 'chosen by the harness: shown once the session is scored' : e(c.policy || 'not recorded')}` : 'the scheduling policy: shown with the operator columns on')
      : c.flags ? `${c.model ? e(c.model) + ' · ' : ''}draft ${e(f.draft ?? 'not recorded')} · temperature ${e(f.temperature ?? 'not recorded')} · baseline ${f.baseline === false || f.baseline === 'off' ? 'off' : 'on'}` : 'the flags: not recorded'; },
  // the frame of a block: its number, its heading, the sentence that says what it is for, its content
  setBlock(i, body, o) { const [key, head, says, comp] = EV.SET_BLOCKS[i], e = EV.e; o = o || {};
    return `<div class="st-b${o.cls ? ' ' + o.cls : ''}" data-block="${key}" data-comp="${comp}"${key === 'kept' ? ' data-by="operator"' : ''}><h3 class="st-h" title="${e(says)}"><span class="st-n">${i + 1}</span><span class="st-t">${e(head)}</span>${o.fold != null ? ` <button class="cl noprint" data-act="setfold" data-id="${key}">${o.fold ? 'open' : 'fold'}</button>` : ''}${o.extra || ''}</h3>${o.fold ? `<p class="st-line">${o.line}</p>` : `${o.says ? `<p class="st-says sm">${e(says)}</p>` : ''}${body}`}</div>`; },

  // ---- what a session's records say of its setting
  setCtx() {
    const M = EV.M, S = EV.s, m = M.meta || {}, row = EV.files.row || {}, g = m.given || null, b = M.brief || {}, rep = EV.repNow();
    return { mode: 'session', b, given: g, man: g ? { outputs: g.outputs, tools: g.tools } : null, flags: m.flags || null, model: m.model || null, op: !!S.op, policy: row.policy || null, policyHidden: !!row.policy_hidden,
      used: M.sims.filter(q => !q.same_as && q.exp !== 'X0' && EV.seen(q.id)).length, chosen: rep && rep.goal ? (Array.isArray(rep.goal) ? rep.goal.join(' · ') : String(rep.goal)) : null, ended: M.ended && (S.step == null || S.step >= M.steps.length - 1) };
  },

  // ---- section 1 of a session's page
  settingCard() {
    const M = EV.M, S = EV.s, e = EV.e; EV.sysLoad();
    if (S.sel && S.sel.t === 'sim' && M.simById[S.sel.id] && S.sel !== S.sysFrom) { S.sysSim = { sid: M.id, id: S.sel.id }; S.sysFrom = S.sel; }  // the picture follows the simulation opened last (every opening is a new selection)
    const fold = !S.full && EV.store('ev-sys') === '1', V = EV.sysVals(), O = EV.OB, on = !O ? null : EV.sysFind(S.sysObj) ? S.sysObj : EV.sysId('sender', 'tc', 'Scheduler') || 'link';
    const shown = V.sim ? `the picture shows the settings of ${EV_ICON.simulation} ${EV.term('Simulation', 'simulation')} ${e(V.sim.id)} “${e(V.sim.label || '')}”${fold ? '' : ' <button class="cl" data-act="sysdef">show the brief\'s defaults</button>'}`
      : M.brief ? `the picture shows the ${EV.term('Brief', 'brief')}'s defaults, as in the baseline` : `the brief of this session: ${EV.nr}`;
    const again = M.brief && !EV.off && !fold ? `<button class="cl noprint" data-act="setagain" style="float:right;margin-right:6px" title="Open the set-up page filled in with every value of this session; the brief is saved under a new name, never overwritten">Start a new session from this setup</button>` : '';
    const head = `<h2>The setting <small>${shown}</small> ${S.full ? '' : `<button class="cl noprint" data-act="sysfold" style="float:right">${fold ? 'unfold' : 'fold'}</button>`}${again}</h2><p class="sec-q">What is this network, what was the AI asked, and what could it see?</p>`;
    if (fold) return `<div class="ev-card noprint" id="s-system">${head}</div>`;
    const c = EV.setCtx(), row = EV.files.row || {};
    // the scheduler's mark: the policy is not told to the AI; with the operator columns on the mark names it
    const pol = `<text x="432" y="162" text-anchor="middle" class="sv" id="sy-pol"${S.op ? ' data-by="operator"' : ''}>${S.op && row.policy && !row.policy_hidden ? `policy: ${e(row.policy)} · not told to the AI` : 'policy not told to the AI'}</text>`;
    const pic = !O ? `<p class="sm">${O === false ? 'viewer/objects.json, the list of the ns-3 objects, could not be read.' : 'Loading the ns-3 objects…'}</p>`
      : `<div class="sy-row"><div><div class="ev-scroll">${EV.sysSvg({ v: V.v, knob: V.knob, fixed: V.fixed, on, act: 'sysobj', pol })}</div>
          <p class="sm gl-key"><span><i class="sw" style="background:var(--series-1)"></i>UDP</span><span><i class="sw" style="background:var(--series-2)"></i>TCP</span>${M.brief ? EV.sysLegend() : ''}${(O.around || []).length ? `<span>outside a packet's path: ${(O.around || []).map((o, i) => `<a data-act="sysobj" data-id="around-${i}"${on === 'around-' + i ? ' style="font-weight:700"' : ''}>${e(o.name.toLowerCase())}</a>`).join(', ')}</span>` : ''}</p></div><div class="sy-det">${EV.objCard(on)}</div></div>`;
    const open = k => S.full || (S.setOpen || {})[k], line = (i, key, body) => EV.setBlock(i, body(), { fold: S.full ? null : !open(key), line: EV.setLine(key, c) });
    const none = `<p class="sm">${EV.nr}: this session was made before briefs existed.</p>`, has = !!M.brief;
    return `<div class="ev-card noprint" id="s-system">${head}<div class="st" id="st-blocks">
        ${EV.setBlock(0, pic, { cls: 'st-wide' })}
        <div class="st-row">${EV.setBlock(1, has ? EV.setWho(c) : none)}${EV.setBlock(2, has ? EV.setAim(c) : none)}${EV.setBlock(3, has ? EV.setLists(c) : none, { cls: 'st-told' })}</div>
        <div class="st-row st-low">${line(4, 'limits', () => (has ? EV.setLimits(c) : none))}${line(5, 'kept', () => EV.setKept(c))}${line(6, 'runs', () => EV.setRuns(c))}</div></div>
      </div>`;
  },
});
EV.act = Object.assign(EV.act || {}, {
  setfold(id) { const S = EV.s; S.setOpen = S.setOpen || {}; S.setOpen[id] = !S.setOpen[id]; EV.draw(); },
  setagain() { EV.go({ view: 'new', from: EV.s.sid }); },
});
