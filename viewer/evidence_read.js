// Decision rules and checks written for reading. The exact text is what the model wrote and what the harness recorded;
// this file shows the same thing with the outputs by their plain names and the numbers in the units the page uses
// everywhere: "tcp_goodput_bps@low_w50 > 800000000" as "TCP goodput at low_w50 > 800 Mbps", a check as
// "483 Mbps > 800 Mbps: failed". Nothing is computed that the record does not hold: a measured number is the value of
// that output in the simulation the rule names, and it opens that simulation. The exact text stays on hover.
// The grammar is the harness's (decision_rules.py): numbers; measure@label; + - * / and brackets; abs(), min(), max();
// one of < <= > >= == per comparison; comparisons joined by AND and OR. A text that cannot be read is shown as it is.
// ======================================================================================================
Object.assign(EV, {
  READ_WORDS: { '<': 'under', '<=': 'at most', '>': 'over', '>=': 'at least', '==': 'equal to' },  // a comparison in words; one that did not hold: "not over"
  readTrees: new Map(),  // a rule's text -> its tree (null: unreadable), read once: the notebook draws every rule at every click
  readTree(text) { const C = EV.readTrees; if (!C.has(text)) C.set(text, EV.readTree1(text)); return C.get(text); },
  readTree1(text) {
    const toks = [], re = /\s*(?:(\d+\.?\d*(?:[eE][+-]?\d+)?|\.\d+)|([A-Za-z_][A-Za-z0-9_]*)(?:@([A-Za-z0-9_]+))?|(<=|>=|==|&&|\|\||<|>|[-+*\/(),]))/y; let m, pos = 0;
    text = String(text || '');
    while (re.lastIndex < text.length) { const at = re.lastIndex; m = re.exec(text); if (!m || re.lastIndex === at) { if (!text.slice(at).trim()) break; return null; }
      const w = m[2] && !m[3] ? m[2].toUpperCase() : m[4];
      toks.push(m[1] ? ['num', Number(m[1]), m[1]] : w === 'AND' || w === '&&' ? ['and'] : w === 'OR' || w === '||' ? ['or'] : m[2] ? ['name', m[2], m[3] || null] : ['op', m[4]]); }
    const peek = () => toks[pos] || ['end'], take = () => toks[pos++] || ['end'], is = (t, v) => t[0] === 'op' && t[1] === v, fail = () => { throw new Error('unreadable'); };
    const expr = () => { let v = term(); while (is(peek(), '+') || is(peek(), '-')) v = ['bin', take()[1], v, term()]; return v; };
    const term = () => { let v = factor(); while (is(peek(), '*') || is(peek(), '/')) v = ['bin', take()[1], v, factor()]; return v; };
    const factor = () => { const t = take();
      if (is(t, '-')) return ['neg', factor()];
      if (is(t, '(')) { const v = expr(); if (!is(take(), ')')) fail(); return ['grp', v]; }
      if (t[0] === 'num') return t;
      if (t[0] === 'name') { if (is(peek(), '(') && !t[2]) { take(); const args = [expr()]; while (is(peek(), ',')) { take(); args.push(expr()); } if (!is(take(), ')')) fail(); return ['call', t[1], args]; }
        return ['val', t[1], t[2]]; }
      return fail(); };
    const comparison = () => { const left = expr(), op = take(); if (op[0] !== 'op' || !['<', '<=', '>', '>=', '=='].includes(op[1])) fail(); return ['cmp', left, op[1], expr()]; };
    const part = () => { const start = pos; try { return comparison(); } catch (x) { pos = start; if (!is(peek(), '(')) throw x; } take(); const g = either(); if (!is(take(), ')')) fail(); return ['all', g]; };
    const both = () => { const ps = [part()]; while (peek()[0] === 'and') { take(); ps.push(part()); } return ps.length === 1 ? ps[0] : ['and', ps]; };
    const either = () => { const ps = [both()]; while (peek()[0] === 'or') { take(); ps.push(both()); } return ps.length === 1 ? ps[0] : ['or', ps]; };
    try { const tree = either(); return pos < toks.length ? null : tree; } catch (x) { return null; }
  },
  // the output whose unit an expression carries (null: a plain number, such as a factor or a ratio of two outputs)
  readUnit(n) {
    const U = EV.readUnit;
    return n[0] === 'val' ? n[1] : n[0] === 'neg' || n[0] === 'grp' ? U(n[1]) : n[0] === 'call' ? n[2].map(U).find(Boolean) || null
      : n[0] !== 'bin' ? null : n[1] === '+' || n[1] === '-' ? U(n[2]) || U(n[3]) : n[1] === '*' ? (U(n[2]) && U(n[3]) ? null : U(n[2]) || U(n[3])) : U(n[3]) ? null : U(n[2]);
  },
  readValue(n, val) {  // the number an expression comes to, from the measured values (null when one is missing)
    const V = q => EV.readValue(q, val), k = n[0];
    if (k === 'num') return n[1]; if (k === 'val') { const v = val(n[1], n[2]); return typeof v === 'number' ? v : null; } if (k === 'neg') { const v = V(n[1]); return v == null ? null : -v; } if (k === 'grp') return V(n[1]);
    if (k === 'call') { const a = n[2].map(V); return a.some(v => v == null) || !{ abs: 1, min: 1, max: 1 }[n[1]] ? null : Math[n[1]](...a); }
    const a = V(n[2]), b = V(n[3]); return a == null || b == null ? null : n[1] === '+' ? a + b : n[1] === '-' ? a - b : n[1] === '*' ? a * b : b ? a / b : null;
  },
  // a number in the unit of an output (key), with p significant digits; a literal of a rule keeps every digit it was written with
  readNum(v, key, p) { const [u, f] = key ? EV.unit(key) : ['', q => q], x = f(v), big = u === 'Mbps' && p && p <= 4 && Math.abs(x) >= 10000; return (+(big ? x / 1000 : x).toPrecision(p || 12)).toLocaleString('en-US', { maximumFractionDigits: 9 }) + (u ? ' ' + (big ? 'Gbps' : u) : ''); },
  // o.sims: { label: simulation } gives the check (measured numbers in place of the outputs, each opening its simulation);
  // without it, the rule. o.test: the test's id, carried by those links. Returns HTML, or null when the text cannot be read
  readHtml(text, o) {
    const tree = EV.readTree(text); if (!tree) return null; o = o || {};
    const e = EV.e, sims = o.sims || null, one = sims && Object.keys(sims).length === 1 ? Object.values(sims)[0] : null, sim = l => (sims ? sims[l] || (l == null ? one : null) : null);
    const val = (name, label) => { const s = sim(label); return s && s.metrics ? s.metrics[name] : undefined; };
    const R = (n, U, p) => { const k = n[0];
      if (k === 'num') return e(EV.readNum(n[1], U, o.max || 0));
      if (k === 'val') { if (!sims) return `${e(TH_DATA.PLAIN[n[1]] || n[1])}${n[2] ? (o.at ? o.at(n[2]) : ` at <span data-own="model">${e(n[2])}</span>`) : ''}`; const s = sim(n[2]), v = val(n[1], n[2]);
        if (typeof v === 'number' && o.plain) return e(EV.readNum(v, n[1], p));
        return typeof v !== 'number' ? '<span class="mut">no value</span>' : `<a class="rn" data-act="open" data-t="sim" data-id="${e(s.id)}"${o.test ? ` data-test="${e(o.test)}"` : ''} title="${e(`${TH_DATA.PLAIN[n[1]] || n[1]} at ${o.says && o.says(s.label || n[2]) ? o.says(s.label || n[2]) + ' · the AI named it ' : ''}${s.label || n[2] || ''} (${s.id}): ${v}`)}">${e(EV.readNum(v, n[1], p))}</a>`; }
      if (k === 'neg') return '−' + R(n[1], U, p); if (k === 'grp') return '(' + R(n[1], U, p) + ')';
      if (k === 'call') return `${n[1]}(${n[2].map(a => R(a, U || EV.readUnit(a), p)).join(', ')})`;
      if (n[1] === '+' || n[1] === '-') { const u = U || EV.readUnit(n); return `${R(n[2], u, p)} ${n[1] === '-' ? '−' : '+'} ${R(n[3], u, p)}`; }
      const ua = EV.readUnit(n[2]), ub = EV.readUnit(n[3]);  // * and /: a side that carries no output of its own is a plain factor
      return `${R(n[2], ua || (ub ? null : U), p)} ${n[1] === '*' ? '×' : '÷'} ${R(n[3], ub, p)}`; };
    // "x >= 200 and x <= 300" on one measure reads as one phrase, "x within 200 to 300" (strict comparisons: "between 200 and 300"), as the bars draw it as one band;
    // with the measured numbers: "245 Mbps within 200 Mbps to 300 Mbps" (in words, where it does not hold: "not within")
    const band = (lo, hi) => { const U = EV.readUnit(lo[1]) || EV.readUnit(lo[3]), incl = lo[2] === '>=' && hi[2] === '<=', words = `${incl ? 'within' : 'between'} ${R(lo[3], U, 3)} ${incl ? 'to' : 'and'} ${R(hi[3], U, 3)}`; let p = 3;
      if (sims) { const a = EV.readValue(lo[1], val); if (a != null) { while (p < (o.max || 9) && (EV.readNum(a, U, p) === EV.readNum(lo[3][1], U, p) || EV.readNum(a, U, p) === EV.readNum(hi[3][1], U, p)) && a !== lo[3][1] && a !== hi[3][1]) p++;
        const OKb = { '>': (x, y) => x > y, '>=': (x, y) => x >= y, '<': (x, y) => x < y, '<=': (x, y) => x <= y }, held = OKb[lo[2]](a, lo[3][1]) && OKb[hi[2]](a, hi[3][1]); return `${R(lo[1], U, p)}${o.words ? ',' : ''} ${o.words && !held ? 'not ' : ''}${words}`; } }
      return `${R(lo[1], U, p)} ${words}`; };
    const pairs = list => { const out = []; list.forEach(n => { const num = n[0] === 'cmp' && n[3][0] === 'num', lower = num && (n[2] === '>' || n[2] === '>='), upper = num && (n[2] === '<' || n[2] === '<='), k = num ? JSON.stringify(n[1]) : null;
      const mate = lower || upper ? out.find(q => q.k === k && !q.lo && (lower ? q.upper && n[3][1] < q.n[3][1] : q.lower && n[3][1] > q.n[3][1])) : null;
      if (mate) { mate.lo = lower ? n : mate.n; mate.hi = lower ? mate.n : n; } else out.push({ n, k, lower, upper }); }); return out; };
    const C = n => { if (n[0] === 'and') return pairs(n[1]).map(q => (q.lo ? band(q.lo, q.hi) : C(q.n))).join(' and '); if (n[0] === 'or') return n[1].map(C).join(' or '); if (n[0] === 'all') return '(' + C(n[1]) + ')';
      const U = EV.readUnit(n[1]) || EV.readUnit(n[3]); let p = 3;
      if (sims) { const a = EV.readValue(n[1], val), b = EV.readValue(n[3], val);  // as many digits as it takes to tell the two sides apart
        if (a != null && b != null && a !== b) while (p < (o.max || 9) && EV.readNum(a, U, p) === EV.readNum(b, U, p)) p++;
        if (o.words && a != null && b != null) { const held = { '<': a < b, '<=': a <= b, '>': a > b, '>=': a >= b, '==': a === b }[n[2]];  // in words: "483 Mbps, not over 700 Mbps"
          return `${R(n[1], U, p)}, ${held ? '' : 'not '}${EV.READ_WORDS[n[2]]} ${R(n[3], U, p)}`; } }
      return `${R(n[1], U, p)} ${n[2]} ${R(n[3], U, p)}`; };
    return C(tree);
  },
  // a test's decision rule, and its check, for reading; the exact text on hover
  // max: the most significant digits of a number (levels 1 and 2 of the page: four; the detail pane: as many as it takes)
  // A simulation is named in a rule by the label the AI gave it ("w025b"), which says little to a reader. What that simulation IS, in the page's words: the
  // settings in which the simulations this test names differ from each other ("ratio 0.25"); where they do not differ (one simulation), the settings
  // that are not the brief's defaults. From the experiment's own designs, which are recorded with the rule (so nothing later is used). '' when the
  // label is not among the designs.
  simSays(T, label, among) {  // among: the labels to tell this one apart from (a side of one comparison); without it, all the labels the test's rule names
    if (!T) return ''; const C = T._says || (T._says = {}), key = (label == null ? '' : label) + (among ? '|' + among.join(',') : ''); if (key in C) return C[key];
    const M = EV.M, x = M.expById[T.exp], runs = (x && x.runs) || [], kn = (M.brief && M.brief.knobs) || {}, r = runs.find(q => q.label === label) || (label == null && runs.length === 1 ? runs[0] : null); if (!r) return (C[key] = '');
    const group = among && among.length > 1 ? among : T.labels, mine = group && group.length > 1 ? runs.filter(q => group.includes(q.label)) : [r], keys = [...new Set([...Object.keys(kn), ...runs.flatMap(q => Object.keys(q.params || {}))])];
    const num = v => (typeof v === 'number' ? v : /^[0-9.]+\s*[kMG]?bps$/.test(String(v)) ? EV.knNum(v) : NaN), same = (a, b) => (isNaN(num(a)) || isNaN(num(b)) ? String(a) === String(b) : num(a) === num(b));
    const val = (q, k) => (q.params && k in q.params ? q.params[k] : (kn[k] || {}).default), show = (k, v) => TASK_VIEW._rate(String(EV.val(k, v))).replace(/^Tcp/, '') + (k === 'duration' ? ' s' : '');
    const vary = keys.filter(k => mine.some(q => !same(val(q, k), val(mine[0], k)))), use = vary.length ? vary : keys.filter(k => kn[k] && 'default' in kn[k] && !same(val(r, k), kn[k].default));
    return (C[key] = use.length ? use.map(k => `${TH_DATA.KNOB[k] || k} ${show(k, val(r, k))}`).join(', ') : 'every setting at its default');
  },
  // the same after a measure's name: " at ratio 0.25 (w025b)": what the simulation is, then the AI's own name for it, small
  simAt(T, label) { const e = EV.e, says = EV.simSays(T, label); return says ? ` at <span class="sim-says" data-exact="1" title="${e(`The simulation the AI named “${label}”: ${says}`)}">${e(says)}</span> <span class="sim-lab" data-own="model" title="The AI's own name for this simulation">${e(label)}</span>` : ` at <span data-own="model">${e(label)}</span>`; },
  // One side of a comparison in plain words, without the AI's labels: a measure by its name, + − × ÷ as they are, min and max as "the smaller of" and "the larger
  // of", abs of a difference as "the gap between". Where every measure of the side comes from one simulation: that simulation (label), and "at <its
  // settings>" (where); where they come from several, each measure is followed by its own simulation's settings, so that two of the same name can be told apart.
  exprSays(n, T) {
    const labels = [], walk = q => { if (!q) return; if (q[0] === 'val') { if (!labels.includes(q[2])) labels.push(q[2]); } else if (q[0] === 'neg' || q[0] === 'grp') walk(q[1]); else if (q[0] === 'call') q[2].forEach(walk); else if (q[0] === 'bin') { walk(q[2]); walk(q[3]); } }; walk(n);
    const one = labels.length === 1 ? labels[0] : null, says = l => (one !== null ? EV.simSays(T, l) : EV.simSays(T, l, labels)) || l || '', name = q => (TH_DATA.PLAIN[q[1]] || q[1]) + (one !== null || q[2] == null ? '' : ` at ${says(q[2])}`), unit = EV.readUnit(n);
    const W = (q, top) => { const k = q[0];
      if (k === 'num') return String(EV.readNum(q[1], top && unit ? unit : null, 0)); if (k === 'val') return name(q); if (k === 'neg') return '−' + W(q[1]); if (k === 'grp') return top ? W(q[1], true) : `(${W(q[1])})`;
      if (k === 'call') { const a = q[2], inner = a.length === 1 && a[0][0] === 'grp' ? a[0][1] : a[0];
        if (q[1] === 'abs' && a.length === 1 && inner[0] === 'bin' && inner[1] === '-') return `the gap between ${W(inner[2])} and ${W(inner[3])}`;
        if ((q[1] === 'min' || q[1] === 'max') && a.length > 1 && a.every(x => x[0] === 'val' && x[1] === a[0][1]) && new Set(a.map(x => x[2])).size === a.length) return `the ${q[1] === 'min' ? (a.length === 2 ? 'smaller' : 'smallest') : a.length === 2 ? 'larger' : 'largest'} ${TH_DATA.PLAIN[a[0][1]] || a[0][1]} of ${a.length} simulations`;  // one measure over several simulations
        if ((q[1] === 'min' || q[1] === 'max') && a.length === 2) return `the ${q[1] === 'min' ? 'smaller' : 'larger'} of ${W(a[0])} and ${W(a[1])}`;
        return `${q[1]}(${a.map(x => W(x)).join(', ')})`; }
      return `${W(q[2])} ${{ '+': '+', '-': '−', '*': '×', '/': '÷' }[q[1]]} ${W(q[3])}`; };
    return { what: W(n, true), label: one, where: one != null && says(one) ? `at ${says(one)}` : labels.length > 1 && !/ simulations$/.test(W(n, true)) ? `from ${labels.length} simulations` : '' };
  },
  // The comparisons of a test's rule, one by one, each side in plain words (EV.exprSays): what is compared with what, and, with measured = true, the two
  // numbers and whether that comparison holds. For a card that lists them (a hypothesis's box on the board): a long rule reads as a few short lines.
  ruleParts(T, measured) {
    const tree = T && T.rule ? EV.readTree(T.rule) : null; if (!tree) return []; const cmps = [], walk = n => { if (!n) return; if (n[0] === 'and' || n[0] === 'or') n[1].forEach(walk); else if (n[0] === 'all') walk(n[1]); else if (n[0] === 'cmp') cmps.push(n); }; walk(tree);
    const sims = Object.fromEntries(T.sims.map(q => [q.label, q])), one = T.sims.length === 1 ? T.sims[0] : null, val = (name, label) => { const q = sims[label] || (label == null ? one : null); return q && q.metrics ? q.metrics[name] : undefined; };
    const OK = { '>': (a, b) => a > b, '>=': (a, b) => a >= b, '<': (a, b) => a < b, '<=': (a, b) => a <= b, '==': (a, b) => a === b }, txt = h => String(h).replace(/<[^>]+>/g, '');
    return cmps.map(n => { const U = EV.readUnit(n[1]) || EV.readUnit(n[3]), L = EV.exprSays(n[1], T), R = EV.exprSays(n[3], T), w = EV.READ_WORDS[n[2]], isNum = n[3][0] === 'num', a = measured ? EV.readValue(n[1], val) : null, b = measured || isNum ? EV.readValue(n[3], val) : null, both = typeof a === 'number' && typeof b === 'number';
      const side = x => x.what + (x.label != null && x.where ? ' ' + x.where : '');
      return { left: side(L), word: w, right: isNum ? txt(EV.readNum(n[3][1], U, 0)) : side(R), a: both ? txt(EV.readNum(a, U, 4)) : null, b: typeof b === 'number' ? txt(EV.readNum(b, U, 4)) : null, held: both ? OK[n[2]](a, b) : null }; });
  },
  ruleRead(T, max) { const h = T.rule ? EV.readHtml(T.rule, { max, at: l => EV.simAt(T, l) }) : null; return !T.rule ? EV.nr : h ? `<span class="rr" data-rr="rule" title="${EV.e(T.rule)}">${h}</span>` : `<code>${EV.e(T.rule)}</code>`; },
  checkRead(T, max) {
    const c = T.check; if (!c) return null;
    if (c.void) return `<span class="rr" data-rr="void" data-void="1" title="${EV.e(EV.VOID)}${c.recorded ? ' (the harness recorded: ' + c.recorded + ')' : ''}">${EV.gkey('void')}void: compared a simulation with itself</span>`;
    const h = EV.readHtml(T.rule, { sims: Object.fromEntries(T.sims.map(s => [s.label, s])), test: T.id, max, says: l => EV.simSays(T, l) }), word = c.result === 'held' || c.result === 'failed' ? EV.checkRes(c) : `<span class="mut">${EV.e(c.result || 'not checked')}</span>`;
    return `<span class="rr" data-rr="check" title="${EV.e(c.numbers == null ? '' : c.numbers + ' : ' + (c.recorded || c.result))}">${h || `<code>${EV.e(c.numbers ?? '')}</code>`}: ${word}</span>`;
  },
  // A rule as bars, one per comparison: the range the rule allows is shaded, a tick stands at the rule's threshold (its right side) and a dot at the
  // measured value (its left side), in the colour of "held" inside the range and of "failed" outside. Where a rule holds one measure between two numbers
  // ("… >= 200 Mbps and … <= 300 Mbps") the two comparisons are ONE bar with the band between its two ticks (only in a rule joined by "and" throughout).
  // Both sides are worked out from the simulations the rule names, as the check's numbers are; nothing is drawn for a comparison whose sides cannot be
  // worked out. plan: the rule alone, before or without its check: what it allows, with no dot (a comparison with a measured right side is then in words).
  ruleBars(T, max, plan) {  // max: on a notebook card, at most so many bars, then how many more stand in the test's detail
    const tree = T.rule ? EV.readTree(T.rule) : null, c = T.check; if (!tree || (!plan && (!c || c.void))) return ''; const e = EV.e, cmps = []; let or = false;
    const walk = n => { if (!n) return; if (n[0] === 'and' || n[0] === 'or') { if (n[0] === 'or') or = true; n[1].forEach(walk); } else if (n[0] === 'all') walk(n[1]); else if (n[0] === 'cmp') cmps.push(n); }; walk(tree);
    const sims = Object.fromEntries(T.sims.map(q => [q.label, q])), one = T.sims.length === 1 ? T.sims[0] : null, val = (name, label) => { const q = sims[label] || (label == null ? one : null); return q && q.metrics ? q.metrics[name] : undefined; };
    const OK = { '>': (a, b) => a > b, '>=': (a, b) => a >= b, '<': (a, b) => a < b, '<=': (a, b) => a <= b, '==': (a, b) => a === b }, WORD = { '>': 'must be over', '>=': 'must be at least', '<': 'must be under', '<=': 'must be at most', '==': 'must equal' };
    const txt = h => String(h).replace(/<[^>]+>/g, ''), key = parts => 'v:' + parts.join('¦'), ok = x => typeof x === 'number' && isFinite(x);
    const items = []; cmps.forEach(n => { const k = JSON.stringify(n[1]), num = n[3][0] === 'num', lower = n[2] === '>' || n[2] === '>=', upper = n[2] === '<' || n[2] === '<=';
      const mate = !or && num && (lower || upper) ? items.find(q => q.k === k && q.num && !q.lo && (lower ? q.upper && n[3][1] < q.n[3][1] : q.lower && n[3][1] > q.n[3][1])) : null;
      if (mate) { mate.lo = lower ? n : mate.n; mate.hi = lower ? mate.n : n; } else items.push({ n, k, num, lower, upper }); });
    const hit = (kind, x, says, attr) => `<i class="rb-hit" data-hit="${kind}" style="left:${x}%" tabindex="0" data-wd="${e(key(says))}"${attr || ''} aria-label="${e(says[1] + ': ' + says[0])}"></i>`;
    const bars = items.map((it, i) => { const n = it.lo || it.n, U = EV.readUnit(n[1]) || EV.readUnit(n[3]), L = EV.exprSays(n[1], T), a = plan ? null : EV.readValue(n[1], val), at = x => (x.label ? EV.simAt(T, x.label) : ''), left = `${e(L.what)}${at(L)}`, N = x => EV.readNum(x, U, 4);
      const dotAttr = n[1][0] === 'val' ? ` data-measure="${e(n[1][1])}" data-sim="${e(n[1][2] || '')}"` : '';
      if (it.lo) {  // one measure held between two numbers: one bar, the band between its two ticks
        const b0 = it.lo[3][1], b1 = it.hi[3][1]; if (!plan && !ok(a)) return ''; const held = plan ? null : OK[it.lo[2]](a, b0) && OK[it.hi[2]](a, b1), st = held ? 'held' : 'failed';
        const lo = Math.min(0, b0, plan ? b0 : a), top = Math.max(b1, plan ? b1 : a, lo + 1e-12), hi = lo + (top - lo) * 1.14, pct = x => (100 * (x - lo) / (hi - lo)).toFixed(2), band = `${it.lo[2] === '>=' && it.hi[2] === '<=' ? 'within' : 'between'} ${txt(N(b0))} ${it.lo[2] === '>=' && it.hi[2] === '<=' ? 'to' : 'and'} ${txt(N(b1))}`;
        const th = (b, n2) => hit('th', pct(b), [txt(N(b)), n2 === it.lo ? 'lowest allowed' : 'highest allowed', `rule: ${L.what} ${band}`, plan ? '' : st, plan ? '' : `measured: ${txt(N(a))}`]);
        return `<div class="rb" data-i="${i}" data-range="1"${plan ? '' : ` data-held="${held ? 1 : 0}" data-a="${a}"`} data-lo="${b0}" data-hi="${b1}" data-oplo="${e(it.lo[2])}" data-ophi="${e(it.hi[2])}" data-op="range"><div class="rb-l"><span data-exact="1">${left}</span> ${plan ? '' : `<b>${N(a)}</b> `}<span class="sm">· must be ${band}</span>${plan ? '' : ' ' + (held ? EV.res('held', 'holds') : EV.res('failed', 'does not hold'))}</div>
          <div class="rb-t"><i class="rb-ok" style="left:${pct(b0)}%;width:${(pct(b1) - pct(b0)).toFixed(2)}%"></i><i class="rb-th" style="left:${pct(b0)}%"></i><i class="rb-th" style="left:${pct(b1)}%"></i>${plan ? '' : `<i class="rb-dot ${held ? 'ok' : 'bad'}" style="left:${pct(a)}%"></i>`}${th(b0, it.lo)}${th(b1, it.hi)}${plan ? '' : hit('dot', pct(a), [txt(N(a)), L.what, L.where, st, `rule: ${band}`], dotAttr)}</div></div>`; }
      const R = EV.exprSays(n[3], T), b = plan && !it.num ? null : EV.readValue(n[3], val), w = EV.READ_WORDS[n[2]], right = it.num ? '' : ` <span data-exact="1">(${e(R.what)}${at(R)})</span>`;
      if (plan && !ok(b)) return `<div class="rb rb-words" data-i="${i}" data-op="${e(n[2])}"><div class="rb-l"><span data-exact="1">${left}</span> <span class="sm">· ${WORD[n[2]]} <span data-exact="1">${e(R.what)}${at(R)}</span>: a measured value, known once the simulations are back</span></div></div>`;
      if (!plan && (!ok(a) || !ok(b))) return '';
      const lo = Math.min(0, plan ? b : a, b), hi0 = Math.max(plan ? b : a, b, lo + 1e-12), hi = lo + (hi0 - lo) * (plan ? 1.5 : 1.14), pct = x => (100 * (x - lo) / (hi - lo)).toFixed(2), held = plan ? null : OK[n[2]](a, b), up = n[2] === '>' || n[2] === '>=', eq = n[2] === '==', st = held ? 'held' : 'failed';
      // pointing at the dot or at the threshold opens a small box with its value (the page's own box, at once; a mark of a few pixels has a wider place to point at): three
      // short lines. The dot: the value and what it is; the simulation, by its settings; the rule, with the sign of whether it holds. The threshold: the value and that it
      // is the threshold; the rule in full; what was measured, with the same sign.
      const va = plan ? '' : txt(N(a)), vb = txt(N(b)), dotSays = [va, L.what, L.where, st, `rule: ${w} ${vb}`];
      const thSays = it.num ? [vb, 'threshold', `rule: ${L.what} ${w} ${vb}`, plan ? '' : st, plan ? '' : `measured: ${va}`] : [vb, R.what, R.where, st, `${L.what}: ${va}`];
      return `<div class="rb" data-i="${i}"${plan ? '' : ` data-held="${held ? 1 : 0}" data-a="${a}"`} data-b="${b}" data-op="${e(n[2])}"><div class="rb-l"><span data-exact="1">${left}</span> ${plan ? '' : `<b>${N(a)}</b> `}<span class="sm">· ${WORD[n[2]]} ${N(b)}${right}</span>${plan ? '' : ' ' + (held ? EV.res('held', 'holds') : EV.res('failed', 'does not hold'))}</div>
        <div class="rb-t"><i class="rb-ok" style="left:${eq ? pct(b) : up ? pct(b) : 0}%;width:${eq ? 0.6 : up ? (100 - pct(b)).toFixed(2) : pct(b)}%"></i><i class="rb-th" style="left:${pct(b)}%"></i>${plan ? '' : `<i class="rb-dot ${held ? 'ok' : 'bad'}" style="left:${pct(a)}%"></i>`}${hit('th', pct(b), thSays)}${plan ? '' : hit('dot', pct(a), dotSays, dotAttr)}</div></div>`; }).filter(Boolean);
    if (max && bars.length) return `<div class="rbs rbs-card" data-n="${bars.length}">${bars.slice(0, max).join('')}${bars.length > max ? `<p class="sm rb-more">and ${bars.length - max} more comparison${bars.length - max === 1 ? '' : 's'} in the test's detail</p>` : ''}</div>`;
    return bars.length ? `<div class="rbs" data-n="${bars.length}"${plan ? ' data-plan="1"' : ''}>${bars.join('')}<p class="sm rb-key"><i class="rb-ok k"></i> what the rule allows · <i class="rb-th k"></i> the rule's threshold${plan ? '' : ' · <i class="rb-dot k"></i> what was measured'}</p></div>` : '';
  },
  // the measured numbers alone, without the result's word; plain: as text, where a link cannot stand (inside another link)
  checkNums(T, plain) { const c = T.check; if (!c) return ''; const h = c.void ? null : EV.readHtml(T.rule, { sims: Object.fromEntries(T.sims.map(s => [s.label, s])), test: T.id, plain });
    return h ? `<span class="rr" data-rr="numbers" title="${EV.e(c.numbers ?? '')}">${h}</span>` : `<code>${EV.e(c.numbers ?? '')}</code>`; },
  // the same for a check named by its ledger id (an evidence item, a highlight): its test is found from the check
  checkReadById(id) { const T = EV.M.tests.find(q => q.check && q.check.id === id); return T ? EV.checkRead(T) : null; },
});
