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
  readNum(v, key, p) { const [u, f] = key ? EV.unit(key) : ['', q => q], x = f(v); return (+x.toPrecision(p || 12)).toLocaleString('en-US', { maximumFractionDigits: 9 }) + (u ? ' ' + u : ''); },
  // o.sims: { label: simulation } gives the check (measured numbers in place of the outputs, each opening its simulation);
  // without it, the rule. o.test: the test's id, carried by those links. Returns HTML, or null when the text cannot be read
  readHtml(text, o) {
    const tree = EV.readTree(text); if (!tree) return null; o = o || {};
    const e = EV.e, sims = o.sims || null, one = sims && Object.keys(sims).length === 1 ? Object.values(sims)[0] : null, sim = l => (sims ? sims[l] || (l == null ? one : null) : null);
    const val = (name, label) => { const s = sim(label); return s && s.metrics ? s.metrics[name] : undefined; };
    const R = (n, U, p) => { const k = n[0];
      if (k === 'num') return e(EV.readNum(n[1], U, 0));
      if (k === 'val') { if (!sims) return `${e(TH_DATA.PLAIN[n[1]] || n[1])}${n[2] ? ' at ' + e(n[2]) : ''}`; const s = sim(n[2]), v = val(n[1], n[2]);
        if (typeof v === 'number' && o.plain) return e(EV.readNum(v, n[1], p));
        return typeof v !== 'number' ? '<span class="mut">no value</span>' : `<a class="rn" data-act="open" data-t="sim" data-id="${e(s.id)}"${o.test ? ` data-test="${e(o.test)}"` : ''} title="${e(`${TH_DATA.PLAIN[n[1]] || n[1]} at ${s.label || n[2] || ''} (${s.id}): ${v}`)}">${e(EV.readNum(v, n[1], p))}</a>`; }
      if (k === 'neg') return '−' + R(n[1], U, p); if (k === 'grp') return '(' + R(n[1], U, p) + ')';
      if (k === 'call') return `${n[1]}(${n[2].map(a => R(a, U || EV.readUnit(a), p)).join(', ')})`;
      if (n[1] === '+' || n[1] === '-') { const u = U || EV.readUnit(n); return `${R(n[2], u, p)} ${n[1] === '-' ? '−' : '+'} ${R(n[3], u, p)}`; }
      const ua = EV.readUnit(n[2]), ub = EV.readUnit(n[3]);  // * and /: a side that carries no output of its own is a plain factor
      return `${R(n[2], ua || (ub ? null : U), p)} ${n[1] === '*' ? '×' : '÷'} ${R(n[3], ub, p)}`; };
    const C = n => { if (n[0] === 'and' || n[0] === 'or') return n[1].map(C).join(n[0] === 'and' ? ' and ' : ' or '); if (n[0] === 'all') return '(' + C(n[1]) + ')';
      const U = EV.readUnit(n[1]) || EV.readUnit(n[3]); let p = 3;
      if (sims) { const a = EV.readValue(n[1], val), b = EV.readValue(n[3], val);  // as many digits as it takes to tell the two sides apart
        if (a != null && b != null && a !== b) while (p < 9 && EV.readNum(a, U, p) === EV.readNum(b, U, p)) p++;
        if (o.words && a != null && b != null) { const held = { '<': a < b, '<=': a <= b, '>': a > b, '>=': a >= b, '==': a === b }[n[2]];  // in words: "483 Mbps, not over 700 Mbps"
          return `${R(n[1], U, p)}, ${held ? '' : 'not '}${EV.READ_WORDS[n[2]]} ${R(n[3], U, p)}`; } }
      return `${R(n[1], U, p)} ${n[2]} ${R(n[3], U, p)}`; };
    return C(tree);
  },
  // a test's decision rule, and its check, for reading; the exact text on hover
  ruleRead(T) { const h = T.rule ? EV.readHtml(T.rule) : null; return !T.rule ? EV.nr : h ? `<span class="rr" data-rr="rule" title="${EV.e(T.rule)}">${h}</span>` : `<code>${EV.e(T.rule)}</code>`; },
  checkRead(T) {
    const c = T.check; if (!c) return null;
    if (c.void) return `<span class="rr" data-rr="void" data-void="1" title="${EV.e(EV.VOID)}${c.recorded ? ' (the harness recorded: ' + c.recorded + ')' : ''}">${EV.gkey('void')}void: compared a simulation with itself</span>`;
    const h = EV.readHtml(T.rule, { sims: Object.fromEntries(T.sims.map(s => [s.label, s])), test: T.id }), word = c.result === 'held' || c.result === 'failed' ? EV.checkRes(c) : `<span class="mut">${EV.e(c.result || 'not checked')}</span>`;
    return `<span class="rr" data-rr="check" title="${EV.e(c.numbers == null ? '' : c.numbers + ' : ' + (c.recorded || c.result))}">${h || `<code>${EV.e(c.numbers ?? '')}</code>`}: ${word}</span>`;
  },
  // the measured numbers alone, without the result's word; plain: as text, where a link cannot stand (inside another link)
  checkNums(T, plain) { const c = T.check; if (!c) return ''; const h = c.void ? null : EV.readHtml(T.rule, { sims: Object.fromEntries(T.sims.map(s => [s.label, s])), test: T.id, plain });
    return h ? `<span class="rr" data-rr="numbers" title="${EV.e(c.numbers ?? '')}">${h}</span>` : `<code>${EV.e(c.numbers ?? '')}</code>`; },
  // the same for a check named by its ledger id (an evidence item, a highlight): its test is found from the check
  checkReadById(id) { const T = EV.M.tests.find(q => q.check && q.check.id === id); return T ? EV.checkRead(T) : null; },
});
