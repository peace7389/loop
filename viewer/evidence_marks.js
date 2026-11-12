// The marks of the page: drawn shapes, not characters of a font, so that a sign has one weight and one size wherever it
// stands (the card "What this session is made of", the tree, the tests list, the flow charts, Home, the keys of charts).
// One small shape per kind (a path in a 12 by 12 box; with a number: drawn as a line of that width, otherwise filled), in
// the colour of its state. A mark's kind is also in its data-m ("hyp", "held", "supported-again", ...), for the page checks.
// The colour of held and failed, supported and refuted is on the sign only: the word beside it is ordinary text.
// ======================================================================================================
Object.assign(EV, {
  GK: { hyp: 'M6 1 11 6 6 11 1 6Z', dropped: ['M6 1.8 10.2 6 6 10.2 1.8 6ZM2.4 9.6 9.6 2.4', 1.2], rule: ['M6 2.4V9.6', 1.5], sim: 'M6 2.3a3.7 3.7 0 1 0 0 7.4a3.7 3.7 0 1 0 0-7.4Z', 'sim-returned': ['M6 2.9a3.1 3.1 0 1 0 0 6.2a3.1 3.1 0 1 0 0-6.2Z', 1.4],
        held: ['M2.3 6.4 4.9 9 9.8 3.2', 1.9], failed: ['M3 3 9 9M9 3 3 9', 1.9], 'not-checked': ['M3 6H9', 1.6], supported: 'M6 1.7 10.7 9.9H1.3Z', refuted: 'M6 10.3 10.7 2.1H1.3Z', inconclusive: 'M1.6 4.5H10.4V7.5H1.6Z',
        report: 'M6 .7 7.6 4.2 11.4 4.6 8.5 7.1 9.4 10.9 6 8.9 2.6 10.9 3.5 7.1 .6 4.6 4.4 4.2Z',
        check: ['M2.3 6.4 4.9 9 9.8 3.2', 1.9],                    // a tick that is not a check's result: "agrees", "reviewed", the icon of the record type
        warn: ['M6 1.7 10.9 10.2H1.1ZM6 5V7.3M6 8.8V8.9', 1.2] },  // a warning: a verdict that disagrees with its check, a refusal, a number that differs
  GC: { rule: 'q', held: 'ok', supported: 'ok', failed: 'bad', refuted: 'bad', inconclusive: 'mu', dropped: 'mu', 'not-checked': 'mu', warn: 'wn' },  // the colour of each kind (none: the neutral one)
  gk(kind) { const g = EV.GK[kind.replace('-again', '')] || EV.GK.rule, line = Array.isArray(g);
    return `<svg viewBox="0 0 12 12" aria-hidden="true"><path d="${line ? g[0] : g}" ${line ? `fill="none" stroke="currentColor" stroke-width="${g[1]}" stroke-linecap="round" stroke-linejoin="round"` : 'fill="currentColor"'}/></svg>`; },
  // a mark inside a line of text
  gkey: (kind, cls) => `<i class="gk ${EV.GC[kind.replace('-again', '')] || ''}${kind.endsWith('-again') ? ' ag' : ''}${cls || ''}" data-m="${kind}">${EV.gk(kind)}</i>`,
  // the same mark inside an SVG drawing, its box at (x, y) with side s
  gks(kind, x, y, s, extra) { const g = EV.GK[kind] || EV.GK.rule, line = Array.isArray(g);
    return `<svg class="gks ${EV.GC[kind] || ''}" data-m="${kind}" x="${x}" y="${y}" width="${s}" height="${s}" viewBox="0 0 12 12"${extra || ''}><path d="${line ? g[0] : g}" ${line ? `fill="none" stroke="currentColor" stroke-width="${g[1]}" stroke-linecap="round" stroke-linejoin="round"` : 'fill="currentColor"'}/></svg>`; },
  // a result as its sign (coloured) and its word (ordinary text): of a check, of a verdict; and the two counts of checks
  ck: r => (r === 'held' || r === 'failed' ? r : 'not-checked'), vk: r => (r === 'supported' || r === 'refuted' ? r : 'inconclusive'),
  res: (kind, word) => `<span class="rs">${EV.gkey(kind)}${EV.e(word)}</span>`,
  checkRes: c => EV.res(EV.ck(c.result), c.result), verdictRes: r => EV.res(EV.vk(r), r),
  tally: (held, failed) => `<span class="rs tally" data-held="${held}" data-failed="${failed}">${EV.gkey('held')}${held}</span> <span class="rs">${EV.gkey('failed')}${failed}</span>`,
  warn: (text, title) => `<span class="warnc rs"${title ? ` title="${EV.e(title)}"` : ''}>${EV.gkey('warn')}${text || ''}</span>`,
  // a claim of the final report: the checks it cites as marks, in the order cited; "no check cited"; or, the one warning, "no evidence".
  // seen: which records the replay shows (a check recorded later is not drawn)
  claimMarks(q, seen) { const cs = q.cites.filter(c => !seen || seen(c.id));
    return q.kind === 'none' ? EV.warn('no evidence') : cs.length ? `<span class="cm" data-kind="${q.kind}">${cs.map(c => `<span class="rs" data-check="${EV.e(c.id)}">${EV.gkey(EV.ck(c.result))}${EV.e(c.id)}</span>`).join(' ')}</span>` : '<span class="cm" data-kind="nocheck">no check cited</span>'; },
  CLAIM_KINDS: [['held', 'cite held checks only'], ['both', 'cite held and failed checks'], ['failed', 'cite failed checks only'], ['nocheck', 'cite no check'], ['none', 'with no evidence']],
  claimCounts(claims) { const n = k => claims.filter(q => q.kind === k).length;
    return `<span id="claim-counts" data-counts="${EV.CLAIM_KINDS.map(([k]) => n(k)).join(',')}">${claims.length} claim${claims.length === 1 ? '' : 's'} · ${EV.CLAIM_KINDS.map(([k, t]) => (k === 'none' && n(k) ? `<span class="warnc">${n(k)} ${t}</span>` : `${n(k)} ${t}`)).join(' · ')}</span>`; },
  // a dot of a chart, for the chart's key: filled or hollow, in a colour
  dot: (filled, col) => `<i class="gk"><svg viewBox="0 0 12 12" aria-hidden="true"><circle cx="6" cy="6" r="4" fill="${filled ? col || 'currentColor' : 'var(--surface-1)'}" stroke="${col || 'currentColor'}" stroke-width="${filled ? 0 : 1.8}"/></svg></i>`,
});
// the icons of the record types that have a drawn mark
Object.assign(EV_ICON, { hypothesis: EV.gkey('hyp'), simulation: EV.gkey('sim'), check: EV.gkey('check'), malformed: EV.gkey('warn'), report: EV.gkey('report') });
