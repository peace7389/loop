// The marks of the page: drawn shapes, not characters of a font, so that a sign has one weight and one size wherever it
// stands (the card "What this session is made of", the tree, the tests list, the flow charts, Home, the keys of charts).
// One small shape per kind (a path in a 12 by 12 box; with a number: drawn as a line of that width, otherwise filled), in
// the colour of its state. A mark's kind is also in its data-m ("hyp", "held", "supported-again", ...), for the page checks.
// The colour of held and failed, supported and refuted is on the sign only: the word beside it is ordinary text.
// ======================================================================================================
Object.assign(EV, {
  GK: { hyp: 'M6 1 11 6 6 11 1 6Z', dropped: ['M6 1.8 10.2 6 6 10.2 1.8 6ZM2.4 9.6 9.6 2.4', 1.2], rule: ['M6 2.4V9.6', 1.5], sim: 'M6 2.3a3.7 3.7 0 1 0 0 7.4a3.7 3.7 0 1 0 0-7.4Z', 'sim-returned': ['M6 2.9a3.1 3.1 0 1 0 0 6.2a3.1 3.1 0 1 0 0-6.2Z', 1.4],
        held: ['M2.3 6.4 4.9 9 9.8 3.2', 1.9], failed: ['M3 3 9 9M9 3 3 9', 1.9], 'not-checked': ['M3 6H9', 1.6], void: ['M6 2.1a3.9 3.9 0 1 0 0 7.8a3.9 3.9 0 1 0 0-7.8ZM3.3 8.7 8.7 3.3', 1.3], supported: 'M6 1.7 10.7 9.9H1.3Z', refuted: 'M6 10.3 10.7 2.1H1.3Z', inconclusive: 'M1.6 4.5H10.4V7.5H1.6Z',
        report: 'M6 .7 7.6 4.2 11.4 4.6 8.5 7.1 9.4 10.9 6 8.9 2.6 10.9 3.5 7.1 .6 4.6 4.4 4.2Z',
        check: ['M2.3 6.4 4.9 9 9.8 3.2', 1.9],                    // a tick that is not a check's result: "agrees", "reviewed", the icon of the record type
        warn: ['M6 1.7 10.9 10.2H1.1ZM6 5V7.3M6 8.8V8.9', 1.2] },  // a warning: a verdict that disagrees with its check, a refusal, a number that differs
  GC: { rule: 'q', held: 'ok', supported: 'ok', failed: 'bad', refuted: 'bad', inconclusive: 'mu', dropped: 'mu', 'not-checked': 'mu', void: 'mu', warn: 'wn' },  // the colour of each kind (none: the neutral one)
  gk(kind) { const g = EV.GK[kind.replace('-again', '')] || EV.GK.rule, line = Array.isArray(g);
    return `<svg viewBox="0 0 12 12" aria-hidden="true"><path d="${line ? g[0] : g}" ${line ? `fill="none" stroke="currentColor" stroke-width="${g[1]}" stroke-linecap="round" stroke-linejoin="round"` : 'fill="currentColor"'}/></svg>`; },
  // a mark inside a line of text
  gkey: (kind, cls) => `<i class="gk ${EV.GC[kind.replace('-again', '')] || ''}${kind.endsWith('-again') ? ' ag' : ''}${cls || ''}" data-m="${kind}">${EV.gk(kind)}</i>`,
  // the same mark inside an SVG drawing, its box at (x, y) with side s
  gks(kind, x, y, s, extra) { const g = EV.GK[kind] || EV.GK.rule, line = Array.isArray(g);
    return `<svg class="gks ${EV.GC[kind] || ''}" data-m="${kind}" x="${x}" y="${y}" width="${s}" height="${s}" viewBox="0 0 12 12"${extra || ''}><path d="${line ? g[0] : g}" ${line ? `fill="none" stroke="currentColor" stroke-width="${g[1]}" stroke-linecap="round" stroke-linejoin="round"` : 'fill="currentColor"'}/></svg>`; },
  // a result as its sign (coloured) and its word (ordinary text): of a check, of a verdict; and the two counts of checks
  ck: r => (r === 'held' || r === 'failed' || r === 'void' ? r : 'not-checked'), vk: r => (r === 'supported' || r === 'refuted' ? r : 'inconclusive'),
  res: (kind, word) => `<span class="rs">${EV.gkey(kind)}${EV.e(word)}</span>`,
  // a void check: its decision rule compared a simulation with itself. It is neither held nor failed, wherever a check is counted or drawn
  VOID: 'void: this decision rule compared a simulation with itself', RESTS: 'rests on void checks',
  checkRes: c => (c.result === 'void' ? `<span class="rs" data-void="1" title="${EV.VOID}${c.recorded ? ' (the harness recorded: ' + c.recorded + ')' : ''}">${EV.gkey('void')}void</span>` : EV.res(EV.ck(c.result), c.result)), verdictRes: r => EV.res(EV.vk(r), r),
  // beside a verdict whose checks (those of its hypothesis in the last experiment that tested it before the verdict) were all void
  rests: (v, short) => (v && v.voidOnly ? ` <span class="rs mut" data-rests="void" title="${EV.RESTS}: every check this verdict could rest on compared a simulation with itself">${short ? EV.gkey('void') : '· ' + EV.RESTS}</span>` : ''),
  tally: (held, failed, voids) => `<span class="rs tally" data-held="${held}" data-failed="${failed}" data-void="${voids || 0}">${EV.gkey('held')}${held}</span> <span class="rs">${EV.gkey('failed')}${failed}</span>${voids ? ` <span class="rs" title="${EV.VOID}">${EV.gkey('void')}${voids}</span>` : ''}`,
  warn: (text, title) => `<span class="warnc rs"${title ? ` title="${EV.e(title)}"` : ''}>${EV.gkey('warn')}${text || ''}</span>`,
  // a claim of the final report: the checks it cites as marks, in the order cited; "no check cited"; or, the one warning, "no evidence".
  // seen: which records the replay shows (a check recorded later is not drawn)
  claimMarks(q, seen) { const cs = q.cites.filter(c => !seen || seen(c.id));
    return q.kind === 'none' ? EV.warn('no evidence') : cs.length ? `<span class="cm" data-kind="${q.kind}">${cs.map(c => `<span class="rs" data-check="${EV.e(c.id)}">${EV.gkey(EV.ck(c.result))}${EV.e(c.id)}</span>`).join(' ')}</span>` : '<span class="cm" data-kind="nocheck">no check cited</span>'; },
  CLAIM_KINDS: [['held', 'cite held checks only'], ['both', 'cite held and failed checks'], ['failed', 'cite failed checks only'], ['nocheck', 'cite no check'], ['none', 'with no evidence']],
  claimCounts(claims) { const n = k => claims.filter(q => q.kind === k).length;
    return `<span id="claim-counts" data-counts="${EV.CLAIM_KINDS.map(([k]) => n(k)).join(',')}">${claims.length} claim${claims.length === 1 ? '' : 's'} · ${EV.CLAIM_KINDS.map(([k, t]) => (k === 'none' && n(k) ? `<span class="warnc">${n(k)} ${t}</span>` : `${n(k)} ${t}`)).join(' · ')}</span>`; },
  // a hypothesis in short: its question when the session recorded one (the hypothesis put as one plain question, for a
  // reader who is not a specialist); a session that recorded none: the hypothesis text in its place
  hshort: h => (h ? h.question || h.text || '' : ''),
  // the question where there is room for it: its first 30 words, then "more" (and "less"); the click moves nothing
  QWORDS: 30,
  question(h) { const e = EV.e, w = h.question.split(/\s+/), open = (EV.s.qmore || {})[h.id];
    return `<span class="hq" data-q="${e(h.id)}" data-words="${w.length}">${e(open || w.length <= EV.QWORDS ? h.question : w.slice(0, EV.QWORDS).join(' ') + ' …')}${w.length > EV.QWORDS ? ` <a class="noprint sm" data-act="qmore" data-id="${e(h.id)}">${open ? 'less' : 'more'}</a>` : ''}</span>`; },
  // a dot of a chart, for the chart's key: filled or hollow, in a colour
  dot: (filled, col) => `<i class="gk"><svg viewBox="0 0 12 12" aria-hidden="true"><circle cx="6" cy="6" r="4" fill="${filled ? col || 'currentColor' : 'var(--surface-1)'}" stroke="${col || 'currentColor'}" stroke-width="${filled ? 0 : 1.8}"/></svg></i>`,
});
// the icons of the record types that have a drawn mark
Object.assign(EV_ICON, { hypothesis: EV.gkey('hyp'), simulation: EV.gkey('sim'), check: EV.gkey('check'), malformed: EV.gkey('warn'), report: EV.gkey('report') });
EV.act = Object.assign(EV.act || {}, { qmore(id) { const q = EV.s.qmore = EV.s.qmore || {}; q[id] = !q[id]; EV.draw(); } });
