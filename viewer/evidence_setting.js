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
           queuePktsTcp: 'TCP queue length', tcpInitCwnd: 'TCP first window', tcpBufBytes: 'TCP buffers', devQueuePkts: 'device queue length', tcpVariant: 'TCP type', duration: 'measured time', seed: 'seed' },
  SET_ORDER: ['linkRate', 'linkDelay', 'mtu', 'udpPacketBytes', 'udpRate', 'weightUdp', 'queuePkts', 'queuePktsUdp', 'queuePktsTcp', 'tcpVariant', 'tcpInitCwnd', 'tcpBufBytes', 'devQueuePkts', 'duration', 'seed'],
  SET_UNIT: { mtu: 'bytes', udpPacketBytes: 'bytes', queuePkts: 'packets', queuePktsUdp: 'packets', queuePktsTcp: 'packets', tcpInitCwnd: 'segments', devQueuePkts: 'packets', duration: 's' },
  POLICY_SAYS: { share: 'a flow may use what the other leaves unused', cap: 'each flow is held to its configured part of the link', random: 'the harness chooses share or cap and records it under checks/' },
  FLAGS: [['budget', 'simulations allowed at the start', "the brief's limit"], ['draft', 'draft before the answer', 'on'], ['max_tokens', 'most tokens of one answer', '32000 with a draft (the draft may use at most half), 3000 without'], ['temperature', 'temperature', '0.3'], ['baseline', 'baseline simulation first', 'on'], ['judge', 'a second model call judges whether each new hypothesis follows from its guess', 'on'], ['arm', 'who rules on the tests (supervised: a supervisor, a second AI asked apart from the researcher)', 'the researcher itself']],
  // the tools of the harness in plain words (a tool the manifest names and this list does not is shown by its own name)
  TOOL_SAYS: { describe_system: 'read the brief again', metrics: "ask for a simulation's measures", series: 'ask for its series (a sample every 0.1 s)', measure: 'ask for a measurement it defines itself, computed from a recorded series (nothing is simulated)', probe: 'ask for a finer record of a simulation it ran (round-trip time, the receiver’s window, waiting times): the same simulation run again with taps that only listen, kept only if the result is the same', grep_trace: 'search its flow record', list_runs: 'list its simulations so far' },
  // what each setting is, in the page's own words: shown on hover where the brief has no line about it (a fixed setting)
  SET_SAYS: { linkRate: 'the rate of the link between the two computers', linkDelay: 'the time a bit takes to cross the link, one way', mtu: 'the largest packet the link carries', udpPacketBytes: 'the size of each UDP packet; the scenario fixes it', udpRate: 'the rate at which the UDP application sends',
              weightUdp: 'the part of the link configured for UDP; TCP gets the rest', queuePkts: 'how many packets each queue holds', queuePktsUdp: 'how many packets the UDP queue holds', queuePktsTcp: 'how many packets the TCP queue holds', tcpInitCwnd: 'how many segments TCP sends before its first acknowledgement', tcpBufBytes: 'the size of TCP\'s send buffer and of its receive buffer', devQueuePkts: 'how many packets wait in a device\'s transmit queue, after the scheduler', tcpVariant: 'the congestion control of the TCP sender', duration: 'the seconds of traffic that are measured', seed: 'the random seed of a simulation' },
  // what each measure is, in one or two plain sentences: the page's own words for a reader (the line the AI is given about a measure stays beside it, as a quotation)
  MEASURE_SAYS: { udp_goodput_bps: 'How much UDP data reaches the receiver each second. Lost packets do not count.', tcp_goodput_bps: 'How much TCP data reaches the receiver each second. A packet sent twice counts once.',
                  udp_loss_frac: 'The share of the UDP packets sent that never arrived.', drops_band0: 'Packets thrown away at the scheduler’s UDP queue because it was full.', drops_band1: 'Packets thrown away at the scheduler’s TCP queue because it was full.',
                  tcp_retrans: 'How many times TCP had to send a packet again.', link_util: 'How busy the link was: the share of its capacity that carried bits.', link_rate_bps: 'The capacity of the link.', weight_udp: 'The ratio, as that simulation used it.' },
  // The TCP types (congestion control: how a TCP sender decides how fast to send) in one plain line each: [what it reacts to, what it does].
  // The page's own words, for the reader, wherever a TCP type is chosen or named; the AI is not given them (its brief names the types only).
  TCP_SAYS: {
    TcpNewReno: ['reacts to loss', 'the classic: it speeds up a little every round trip and halves its rate at a loss'],
    TcpLinuxReno: ['reacts to loss', 'NewReno the way Linux counts it: the same slow rise, the same halving'],
    TcpCubic: ['reacts to loss', 'the usual one on Linux: at a loss it cuts its rate by about a third, then climbs back fast'],
    TcpBic: ['reacts to loss', 'the forerunner of Cubic: after a loss it searches for its old rate, halving the gap each time'],
    TcpVegas: ['reacts to delay', 'it slows as soon as packets start to queue, before any is lost; gentle, so it gives way to the others'],
    TcpBbr: ['measures the path', 'it estimates the rate the path can carry and sends at that rate; a loss alone does not slow it'],
  },
  tcpSays(v) { const k = /^Tcp/.test(String(v)) ? String(v) : 'Tcp' + v, s = EV.TCP_SAYS[k]; return s ? { name: k.replace(/^Tcp/, ''), reacts: s[0], says: s[1] } : null; },
  // one line for one type; the lines of several, as a short list
  tcpLine(v) { const t = EV.tcpSays(v); return t ? `${t.reacts}: ${t.says}` : ''; },
  tcpList(vs) { const e = EV.e, ts = vs.map(EV.tcpSays).filter(Boolean); return ts.length ? `<div class="tcp-says" data-tcp-n="${ts.length}"><p class="sm">How a TCP sender decides how fast to send. ${ts.length === 1 ? 'This type' : 'The types'}, in the page’s words:</p>${ts.map(t => `<p class="tcp-l" data-tcp="${e(t.name)}"><b>${e(t.name)}</b> <span class="sm">${e(t.reacts)}</span><br>${e(t.says)}</p>`).join('')}</div>` : ''; },
  label(k, meaning) { return `<abbr class="st-l" title="${EV.e(`${meaning || EV.SET_SAYS[k] || ''} (field: ${k})`.trim())}">${EV.e(EV.LABEL[k] || k)}</abbr>`; },
  // a size in bytes as a person says it (65536 -> 64 kB, 1048576 -> 1 MB); one that is no whole kB stays in bytes
  bytes(n) { return n % (1 << 20) === 0 ? `${n >> 20} MB` : n % (1 << 10) === 0 ? `${n >> 10} kB` : `${n} bytes`; },
  setVal(k, v) { return v == null || v === '' ? 'not recorded' : k === 'tcpBufBytes' && /^\d+$/.test(String(v)) ? EV.bytes(+v) : TASK_VIEW._rate(String(v)).replace(/^Tcp/, '') + (EV.SET_UNIT[k] && /^[-\d.]+$/.test(String(v)) ? ' ' + EV.SET_UNIT[k] : ''); },
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
    const b = c.b, e = EV.e, sys = { ...EV.netFixed(b), ...(b.system || {}) }, kn = b.knobs || {}, keys = EV.SET_ORDER.filter(k => k in sys || k in kn).concat(Object.keys({ ...sys, ...kn }).filter(k => !EV.SET_ORDER.includes(k)));
    const fixed = keys.filter(k => !(k in kn)), open = keys.filter(k => k in kn);
    // A setting the AI may change has three values, each in a column of its own under its name: the lowest and the highest it may set, and the value the session
    // starts at (the baseline's); a setting chosen from a list has the list in the place of the first two. A fixed setting has its one value.
    const row = k => (k in kn ? `<tr data-k="${e(k)}" data-set="knob"><td>${EV.label(k, kn[k].meaning)}</td>${kn[k].choices ? `<td colspan="2" data-c="choices"><span class="st-ch" title="${e(kn[k].choices.map(c => String(c).replace(/^Tcp/, '')).join(', '))}"><span class="sm">one of</span> ${e(kn[k].choices.map(c => String(c).replace(/^Tcp/, '')).join(', '))}</span></td>` : `<td data-c="lowest">${e(EV.setVal(k, kn[k].min))}</td><td data-c="highest">${e(EV.setVal(k, kn[k].max))}${kn[k].step != null && kn[k].step !== '' ? ` <span class="sm">in steps of ${e(kn[k].step)}</span>` : ''}</td>`}<td data-c="start"><b>${e(EV.setVal(k, kn[k].default))}</b></td></tr>`
      : `<tr data-k="${e(k)}" data-set="fixed"><td>${EV.label(k)}</td><td colspan="3" data-c="value"><b>${e(EV.setVal(k, sys[k]))}</b></td></tr>`);
    const part = (by, words, list) => (list.length ? `<tr class="st-grp" data-by="${by}"><td colspan="4"><i class="sw"></i>${words}</td></tr>${by === 'model' ? '<tr class="st-cols"><td></td><td>lowest</td><td>highest</td><td title="The value the session starts at: the baseline simulation uses it">starts at</td></tr>' : ''}${list.map(row).join('')}` : '');
    return keys.length ? `<table class="st-who" data-exact="1"><tbody>${part('operator', 'fixed by the operator', fixed)}${part('model', 'the AI may change it', open)}</tbody></table>` : `<p class="sm">the settings: ${EV.nr}</p>`;
  },
  // 3 · the aim, and who set it. An open aim: the one the AI chose is the goal of its final report (c.chosen)
  setAim(c) {
    const g = c.b.goal || {}, e = EV.e, w = EV.aimWords(g);
    if (g.kind === 'open') return `<p data-aim="open"><b>Open:</b> the AI chooses its own aim and has to justify it. <span class="st-by" data-by="model"><i class="sw"></i>chosen by the AI</span></p>${c.mode === 'session' ? `<p class="sm lc4" id="st-chosen">${c.chosen ? `<span class="aim-when">At the end, in its final report, it chose:</span> <span data-own="model">${e(c.chosen)}</span>` : c.ended ? 'It stated no aim: there is no final report.' : 'It has not stated its aim yet.'}</p>` : ''}`;
    if (!w) return `<p class="sm">the aim: ${EV.nr}</p>`;
    return `<p data-aim="given"><b>Find ${w}.</b> <span class="st-by" data-by="operator"><i class="sw"></i>set by the operator</span></p>${g.tolerance != null && g.tolerance !== '' ? `<p class="sm">Tolerance ${e(g.tolerance)} %: two results closer than this count as equal.</p>` : ''}`;
  },
  // the lean page: the aim stands right under the heading of the setting, before the network, in the aim's own box (as in the brief's card), so that a
  // reader sees first what the session is about (2026-11-22, the operator: "show the aim clearly on the setting section for users to see what this session
  // is about"). The block "The aim" is then not among the rest: one place for it.
  setAimBox(c) { const g = c.b.goal || {};
    return `<div class="bc-aim set-aim" id="set-aim" data-aim="${EV.e(g.kind || '')}"><h3>${EV.flag()}The aim <span class="sm set-aim-q">what this session is about</span></h3>${EV.setAim(c)}</div>`; },
  // The cards of one row are equally tall (the row stretches them), so the aim's card has room below its two lines: the aim the AI
  // chose is shown in as many whole lines as that room holds (never fewer than four), and in full on hover when it is still cut.
  aimFit() { const p = document.getElementById('st-chosen'), card = p && p.closest('.st-b'); if (!p || !card) return;
    p.style.webkitLineClamp = '4'; const cs = getComputedStyle(p), lh = parseFloat(cs.lineHeight) || parseFloat(cs.fontSize) * 1.45, full = p.scrollHeight;
    const room = card.getBoundingClientRect().bottom - parseFloat(getComputedStyle(card).paddingBottom) - p.getBoundingClientRect().top, n = Math.max(4, Math.floor((room + 1) / lh));
    p.style.webkitLineClamp = String(n); p.dataset.lines = n; if (full > n * lh + 2) p.title = p.textContent; else p.removeAttribute('title'); },
  // 4 · the three lists, built from the brief, the flags and the manifest (the outputs and the tools the harness offers)
  // The task as the AI reads it, written from a brief's aim and the settings it leaves open. The harness writes the same sentence (tools.task_text in
  // harness/tools.py) into every brief that states no task of its own; the set-up page shows it as the form changes. Keep the two alike, word for word.
  taskText(b) { const kn = Object.keys((b && b.knobs) || {}), g = (b && b.goal) || {}, may = `You may change ${kn.length} setting${kn.length === 1 ? '' : 's'} (${kn.join(', ')}); every other setting is fixed.`;
    if (g.kind === 'given') { const t = g.target || {}, c = (g.conditions || []).map(x => String(x).trim()); return `Find the settings that give the ${t.direction === 'max' ? 'largest' : 'smallest'} ${t.measure}${c.length ? ', while ' + c.join(' and ') : ''}. ${may} Explain why they are best.`; }
    return `No aim is given. Choose what 'performance' should mean for this system and say why; then find the settings that are best for it. ${may} Explain why they are best.`; },
  setLists(c) {
    const b = c.b, e = EV.e, sys = { ...EV.netFixed(b), ...(b.system || {}) }, kn = b.knobs || {}, man = c.man || {}, lim = b.limits || {}, order = k => EV.SET_ORDER.filter(q => q in k).concat(Object.keys(k).filter(q => !EV.SET_ORDER.includes(q))), outs = Object.keys(man.outputs || {}), tools = Object.keys(man.tools || {});
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
      <details class="st-exact" id="st-exact"${EV.s.exact ? ' open' : ''}><summary>the exact text the AI ${was} given</summary><p class="sm">What the harness returns when the AI asks to read the brief (<code>describe_system()</code>), word for word: the brief, then the measures and the tools.</p><pre id="st-given">${c.given ? e(JSON.stringify(c.given, null, 1)) : 'not recorded'}</pre></details>`;
  },
  // 5 · the limits (and, on a session, how many simulations were used)
  setLimits(c) { const l = c.b.limits || {}, e = EV.e;
    return `<p><b>${e(l.simulations ?? 'not recorded')}</b> simulations in all · <b>${e(l.simulations_per_experiment ?? 'not recorded')}</b> in one turn${c.mode === 'session' ? ` · <span id="st-used"><b>${e(c.used ?? 'not recorded')}</b> used</span>` : ''}</p>`; },
  // 6 · kept from the AI: the scheduling policy, only with the operator columns on
  setKept(c) {
    if (!c.op) return `<p class="mut" id="st-kept" data-shown="0">The scheduling policy: shown with the operator columns on.</p>`;
    return `<p id="st-kept" data-shown="1" data-by="operator"><i class="sw"></i>scheduling policy: <b>${c.policyHidden ? 'chosen by the harness: shown once the session is scored' : EV.e(c.policy || 'not recorded')}</b>${!c.policyHidden && EV.POLICY_SAYS[c.policy] ? ` <span class="sm">· ${EV.e(EV.POLICY_SAYS[c.policy])}</span>` : ''} <span class="sm">· never told to the AI</span></p>`;
  },
  // 7 · how the AI runs: the flags, each beside its default
  setRuns(c) { const f = c.flags, e = EV.e, show = v => (v === true ? 'on' : v === false ? 'off' : v == null ? 'the default' : String(v));
    return `<table class="st-flags" data-exact="1"><tbody>${c.mode === 'session' ? `<tr data-flag="model"><td>model</td><td><b>${e(c.model || 'not recorded')}</b></td><td class="sm">taken from the model server</td></tr>` : ''}${EV.FLAGS.map(([k, name, dflt]) => `<tr data-flag="${k}"><td>${e(name)}</td><td><b>${f ? e(show(f[k])) : 'not recorded'}</b></td><td class="sm">default: ${e(dflt)}</td></tr>`).join('')}</tbody></table>`; },
  // one line that carries a folded block's content
  setLine(key, c) { const l = c.b.limits || {}, f = c.flags || {}, e = EV.e, b = c.b, kn = Object.keys(b.knobs || {}), nf = Object.keys({ ...EV.netFixed(b), ...(b.system || {}) }).length, g = b.goal || {}, w = EV.aimWords(g);
    // blocks 2 to 4 are folded to one line as well until asked for (2026-11-17, the operator: hidden by default)
    if (key === 'who') return `${kn.length} setting${kn.length === 1 ? '' : 's'} the AI may change: ${kn.map(k => e(EV.LABEL[k] || (TH_DATA.KNOB || {})[k] || k)).join(', ') || 'none'} · ${nf} fixed by the operator`;
    if (key === 'aim') return g.kind === 'open' ? 'open: the AI chooses its own aim' : w ? `find ${w}` : `the aim: ${EV.nr}`;
    if (key === 'told') return 'told: the task, the system’s description, the settings, the goal, the limits, its own record · not told: the scheduling policy, the code, the operator’s checks';
    return key === 'limits' ? `${e(l.simulations ?? 'not recorded')} simulations in all, ${e(l.simulations_per_experiment ?? 'not recorded')} in one turn${c.mode === 'session' ? `, ${e(c.used ?? 'not recorded')} used` : ''}`
      : key === 'kept' ? (c.op ? `scheduling policy ${c.policyHidden ? 'chosen by the harness: shown once the session is scored' : e(c.policy || 'not recorded')}` : 'the scheduling policy: shown with the operator columns on')
      : c.flags ? `${c.model ? e(c.model) + ' · ' : ''}draft ${e(f.draft ?? 'not recorded')} · temperature ${e(f.temperature ?? 'not recorded')} · baseline ${f.baseline === false || f.baseline === 'off' ? 'off' : 'on'}` : 'the flags: not recorded'; },
  // the frame of a block: its number, its heading, the sentence that says what it is for, its content
  setBlock(i, body, o) { const [key, head, says, comp] = EV.SET_BLOCKS[i], e = EV.e; o = o || {};
    return `<div class="st-b${o.cls ? ' ' + o.cls : ''}" data-block="${key}" data-comp="${comp}"${key === 'kept' ? ' data-by="operator"' : ''}><h3 class="st-h" title="${e(says)}">${o.nonum ? '' : `<span class="st-n">${i + 1}</span>`}<span class="st-t">${e(head)}</span>${o.fold != null ? ` <button class="cl noprint" data-act="setfold" data-id="${key}">${o.fold ? 'open' : 'fold'}</button>` : ''}${o.extra || ''}</h3>${o.fold ? `<p class="st-line" data-exact="1">${o.line}</p>` : `${o.says ? `<p class="st-says sm">${e(says)}</p>` : ''}${body}`}</div>`; },

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
    const fold = !S.full && EV.store('ev-sys') === '1', V = EV.sysVals(), O = EV.OB, on = O && EV.sysFind(S.sysObj) ? S.sysObj : null;  // no part is chosen until the reader clicks one
    const shown = V.sim ? `the picture shows the settings of ${EV_ICON.simulation} ${EV.term('Simulation', 'simulation')} ${e(V.sim.id)} “${e(V.sim.label || '')}”${fold ? '' : ' <button class="cl" data-act="sysdef">show the brief\'s defaults</button>'}`
      : M.brief ? `the picture shows the ${EV.term('Brief', 'brief')}'s defaults, as in the baseline` : `the brief of this session: ${EV.nr}`;
    const again = M.brief && !EV.off && !fold ? `<button class="cl noprint" data-act="setagain" style="float:right;margin-right:6px" title="Open the set-up page filled in with every value of this session; the brief is saved under a new name, never overwritten">Start a new session from this setup</button>` : '';
    const head = `<h2>The setting <small>${shown}</small> ${S.full ? '' : `<button class="cl noprint" data-act="sysfold" style="float:right">${fold ? 'unfold' : 'fold'}</button>`}${again}</h2><p class="sec-q">What is this network, what was the AI asked, and what could it see?</p>`;
    if (fold) return `<div class="ev-card noprint" id="s-system">${head}</div>`;
    const c = EV.setCtx(), row = EV.files.row || {};
    // the scheduler's mark: the policy is not told to the AI; with the operator columns on the mark names it
    const pol = `<text x="432" y="162" text-anchor="middle" class="sv" id="sy-pol"${S.op ? ' data-by="operator"' : ''}>${S.op && row.policy && !row.policy_hidden ? `policy: ${e(row.policy)} · not told to the AI` : 'policy not told to the AI'}</text>`;
    // a brief with a network: the picture is drawn from the network itself (evidence_net.js), with the knobs at their defaults or, when a simulation is open, at its values
    const NT = EV.net(M.brief), netPic = () => {
      const netOn = NT && EV.netParts(V.sim && V.sim.topology ? V.sim.topology : NT).includes(S.sysObj) ? S.sysObj : null;   // the part whose card stands beside the schema: none until a click
      const kn = M.brief.knobs || {}, vals = { ...Object.fromEntries(Object.entries(kn).map(([k, q]) => [k, q.default])), ...(V.sim ? V.sim.params : {}) }, net = V.sim && V.sim.topology ? V.sim.topology : NT, b2 = { ...M.brief, topology: EV.netWith(net, vals) };  // a simulation that changed the structure: its own network
      const sched = EV.netQueues(NT).some(x => x.q.kind === 'scheduler'), says = !sched ? '' : S.op && row.policy && !row.policy_hidden ? `scheduling policy: ${row.policy} · not told to the AI` : 'how a scheduler divides its link is not told to the AI';
      const netSvg = EV.netSvg(b2, { pol: says, op: S.op, on: netOn });   // its width sets the schema's column: the part's card beside it takes the rest of the row
      const edits = V.sim && V.sim.structure && V.sim.structure.length ? `<p class="sm" id="net-changed" data-own="model"><b>This simulation changed the structure:</b> ${EV.e(EV.editsSay(V.sim.structure))}</p>` : '';
      return `<div class="sy-row sy-net" style="--net-w:${Math.ceil(+((/viewBox="0 0 ([\d.]+)/.exec(netSvg) || [])[1] || 1000))}px"><div><div class="ev-scroll">${netSvg}</div>${edits}<p class="sm gl-key">${EV.sysLegend()}</p>${EV.netWords(b2)}</div><div class="sy-side">${EV.netKinds(b2)}<div class="sy-det${netOn ? ' on' : ''}" id="net-det">${netOn ? `${EV.netCard(b2, netOn, V.sim)}<p class="sy-det-h sm noprint"><button class="cl" data-act="sysobj" data-id="">close</button></p>` : '<p class="sm mut" id="sy-hint">Click a part of the schema (a host, an application, a socket, a queue, a device, a link) to see what it is in ns-3, its settings, who decides each, and what is measured there.</p>'}</div></div></div>`; };
    const pic = NT ? netPic() : !O ? `<p class="sm">${O === false ? 'viewer/objects.json, the list of the ns-3 objects, could not be read.' : 'Loading the ns-3 objects…'}</p>`
      : `<div class="sy-row"><div><div class="ev-scroll">${EV.sysSvg({ v: V.v, knob: V.knob, fixed: V.fixed, on, act: 'sysobj', pol })}</div>
          <p class="sm gl-key">${M.brief ? EV.sysLegend() : ''}${(O.around || []).length ? `<span>outside a packet's path: ${(O.around || []).map((o, i) => `<a data-act="sysobj" data-id="around-${i}"${on === 'around-' + i ? ' style="font-weight:700"' : ''}>${e(o.name.toLowerCase())}</a>`).join(', ')}</span>` : ''}</p></div><div class="sy-side"><div class="sy-det${on ? ' on' : ''}">${on ? `${EV.objCard(on)}<p class="sy-det-h sm noprint"><button class="cl" data-act="sysobj" data-id="">close</button></p>` : '<p class="sm mut" id="sy-hint">Click a part of the picture to see its settings, what the AI may change there, and what is measured there.</p>'}</div></div></div>`;
    // Blocks 2 to 7 are not shown at all, or shown in full: one button under the picture (2026-11-17, the operator: "hidden altogether or shown in full").
    // The browser remembers which. The full view (for print and review) always has them.
    const all = S.full || EV.store('ev-setall') === '1', none = `<p class="sm">${EV.nr}: this session was made before briefs existed.</p>`, has = !!M.brief;
    const L = EV.LEAN, rest = !all ? '' : `<div class="st-row${L ? ' st-two' : ''}">${EV.setBlock(1, has ? EV.setWho(c) : none, { nonum: L })}${L ? '' : EV.setBlock(2, has ? EV.setAim(c) : none)}${EV.setBlock(3, has ? EV.setLists(c) : none, { cls: 'st-told', nonum: L })}</div>
        <div class="st-row st-low">${EV.setBlock(4, has ? EV.setLimits(c) : none, { nonum: L })}${EV.setBlock(5, EV.setKept(c), { nonum: L })}${EV.setBlock(6, EV.setRuns(c), { nonum: L })}</div>`;
    // the button stands right under the picture, before the blocks it shows: it stays where it is when they come and go, so that a reader can go back
    // and forth without moving the pointer. The picture's block carries its number 1 only while the others are there to count with it.
    const more = S.full ? '' : `<p class="sm noprint" id="st-more"><button class="cl" data-act="setall" aria-expanded="${all ? 'true' : 'false'}">${all ? 'hide the rest' : 'show the rest'}</button>${all ? '' : ` <span>who decides what · ${EV.LEAN ? '' : 'the aim · '}what the AI is told and can do · the limits · what is kept from the AI · how the AI runs</span>`}</p>`;
    return `<div class="ev-card noprint" id="s-system">${head}${EV.LEAN && has ? EV.setAimBox(c) : ''}<div class="st" id="st-blocks">
        ${EV.setBlock(0, pic, { cls: 'st-wide', nonum: !all })}${more}${rest}</div>
      </div>`;
  },
});
EV.act = Object.assign(EV.act || {}, {
  setfold(id) { const S = EV.s; S.setOpen = S.setOpen || {}; S.setOpen[id] = !S.setOpen[id]; EV.draw(); },
  setall() { EV.store('ev-setall', EV.store('ev-setall') === '1' ? '0' : '1'); EV.draw(); },
  setagain() { EV.go({ view: 'new', from: EV.s.sid }); },
});
