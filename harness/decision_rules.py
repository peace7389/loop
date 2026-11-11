"""Decision rules: the comparisons the model states before its simulations run. The harness reads them and checks them itself.
Grammar: numbers; measure@label (an output value of the simulation with that label; the @label may be left out when the
experiment has one simulation); + - * / and parentheses; abs(), min(), max(); exactly one of < <= > >= == per
comparison; comparisons joined by AND. The viewer's own parser for the pass rules of the first session reads the same grammar without @label."""
import re

TOKEN = re.compile(r"\s*(?:(\d+\.?\d*(?:[eE][+-]?\d+)?|\.\d+)|([A-Za-z_][A-Za-z0-9_]*)(?:@([A-Za-z0-9_]+))?|(<=|>=|==|&&|<|>|[-+*/(),]))")
COMPARE = {"<": lambda a, b: a < b, "<=": lambda a, b: a <= b, ">": lambda a, b: a > b, ">=": lambda a, b: a >= b, "==": lambda a, b: a == b}
FUNCS = {"abs": abs, "min": min, "max": max}

class DecisionRuleError(ValueError):
    """The decision rule cannot be read (the turn is malformed), or cannot be evaluated (a simulation it names gave no value)."""

def _tokens(text):
    out, i, text = [], 0, str(text)
    while i < len(text):
        m = TOKEN.match(text, i)
        if not m or m.end() == i:
            if not text[i:].strip():
                break
            raise DecisionRuleError(f"cannot read {text[i:i + 12].strip()!r}")
        num, name, label, op = m.groups()
        out.append(("num", float(num)) if num else ("and",) if op == "&&" or (name and name.upper() == "AND" and not label) else ("name", name, label) if name else ("op", op))
        i = m.end()
    return out

def parse(text, measures, labels):
    """The decision rule as a list of comparisons (left, operator, right), or DecisionRuleError saying what is wrong with it."""
    toks, pos = _tokens(text), 0
    def peek():
        return toks[pos] if pos < len(toks) else ("end",)
    def take():
        nonlocal pos
        pos += 1
        return toks[pos - 1]
    def expr():
        v = term()
        while peek() in (("op", "+"), ("op", "-")):
            v = ("bin", take()[1], v, term())
        return v
    def term():
        v = factor()
        while peek() in (("op", "*"), ("op", "/")):
            v = ("bin", take()[1], v, factor())
        return v
    def factor():
        t = take() if pos < len(toks) else ("end",)
        if t == ("op", "-"):
            return ("neg", factor())
        if t == ("op", "("):
            v = expr()
            if take() != ("op", ")"):
                raise DecisionRuleError("a bracket is not closed")
            return v
        if t[0] == "num":
            return t
        if t[0] == "name":
            _, name, label = t
            if peek() == ("op", "(") and not label:
                if name not in FUNCS:
                    raise DecisionRuleError(f"unknown function {name}()")
                take()
                args = [expr()]
                while peek() == ("op", ","):
                    take()
                    args.append(expr())
                if take() != ("op", ")"):
                    raise DecisionRuleError("a bracket is not closed")
                return ("call", name, args)
            if name not in measures:
                raise DecisionRuleError(f"{name} is not one of the outputs")
            if not label and len(labels) != 1:
                raise DecisionRuleError(f"say which simulation: {name}@label")
            if label and label not in labels:
                raise DecisionRuleError(f"no simulation in this experiment is labelled {label}")
            return ("val", name, label or labels[0])
        raise DecisionRuleError("a value is missing")
    out = []
    while True:
        left = expr()
        op = take() if pos < len(toks) else ("end",)
        if op[0] != "op" or op[1] not in COMPARE:
            raise DecisionRuleError("each comparison needs exactly one of < <= > >= ==")
        out.append((left, op[1], expr()))
        if pos >= len(toks):
            return out
        if take() != ("and",):
            raise DecisionRuleError("comparisons are joined by AND")

def _value(node, values):
    kind = node[0]
    if kind == "num":
        return node[1]
    if kind == "val":
        v = (values.get(node[2]) or {}).get(node[1])
        if not isinstance(v, (int, float)):
            raise DecisionRuleError(f"simulation {node[2]} gave no value for {node[1]}")
        return v
    if kind == "neg":
        return -_value(node[1], values)
    if kind == "call":
        return FUNCS[node[1]](*[_value(a, values) for a in node[2]])
    a, b = _value(node[2], values), _value(node[3], values)
    if node[1] == "/" and b == 0:
        raise DecisionRuleError("division by zero")
    return {"+": a + b, "-": a - b, "*": a * b, "/": a / b if b else 0}[node[1]]

def check(text, measures, labels, values):
    """Evaluate a decision rule from the measured values {label: metrics}. Returns (held, the decision rule with the numbers written in)."""
    held = all(COMPARE[op](_value(l, values), _value(r, values)) for l, op, r in parse(text, measures, labels))
    def number(m):
        name, label = m.group(2), m.group(3)
        if not name or name not in measures:
            return m.group(0)
        v = (values.get(label or labels[0]) or {}).get(name)
        return m.group(0).replace(name + (f"@{label}" if label else ""), repr(v) if isinstance(v, float) else str(v))
    return held, TOKEN.sub(number, str(text)).strip()
