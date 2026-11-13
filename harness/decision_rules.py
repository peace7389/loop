"""Decision rules: the comparisons the model states before its simulations run. The harness reads them and checks them itself.
Grammar: numbers; measure@label (an output value of the simulation with that label; the @label may be left out when the
experiment has one simulation); + - * / and parentheses; abs(), min(), max(); exactly one of < <= > >= == per
comparison; comparisons joined by AND and OR (AND first), with parentheses to group them. The viewer's own parser for the pass rules of the first session reads the same grammar without @label."""
import re

TOKEN = re.compile(r"\s*(?:(\d+\.?\d*(?:[eE][+-]?\d+)?|\.\d+)|([A-Za-z_][A-Za-z0-9_]*)(?:@([A-Za-z0-9_]+))?|(<=|>=|==|&&|\|\||<|>|[-+*/(),]))")
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
        word = name.upper() if name and not label else op
        out.append(("num", float(num)) if num else ("and",) if word in ("AND", "&&") else ("or",) if word in ("OR", "||") else ("name", name, label) if name else ("op", op))
        i = m.end()
    return out

def parse(text, measures, labels):
    """The decision rule as a tree of comparisons joined by AND and OR, or DecisionRuleError saying what is wrong with it."""
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
    def comparison():
        left = expr()
        op = take() if pos < len(toks) else ("end",)
        if op[0] != "op" or op[1] not in COMPARE:
            raise DecisionRuleError("each comparison needs exactly one of < <= > >= ==")
        return ("cmp", left, op[1], expr())
    def part():  # one comparison, or a group of comparisons in brackets
        nonlocal pos
        start = pos
        try:
            return comparison()
        except DecisionRuleError:
            pos = start
            if peek() != ("op", "("):
                raise
        take()
        group = either()
        if (take() if pos < len(toks) else ("end",)) != ("op", ")"):
            raise DecisionRuleError("a bracket is not closed")
        return group
    def both():
        parts = [part()]
        while peek() == ("and",):
            take()
            parts.append(part())
        return parts[0] if len(parts) == 1 else ("and", parts)
    def either():
        parts = [both()]
        while peek() == ("or",):
            take()
            parts.append(both())
        return parts[0] if len(parts) == 1 else ("or", parts)
    tree = either()
    if pos < len(toks):
        raise DecisionRuleError("comparisons are joined by AND or OR")
    return tree

def names(text, measures, labels):
    """The labels of the simulations a decision rule names, each once, in the order they stand in it."""
    out = []
    def walk(node):
        if node[0] == "val":
            if node[2] not in out:
                out.append(node[2])
        else:
            for n in node[1:]:
                for m in (n if isinstance(n, list) else [n]):
                    if isinstance(m, tuple):
                        walk(m)
    walk(parse(text, measures, labels))
    return out

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
    def truth(node):  # every part is evaluated, so a simulation without a value is always noticed
        if node[0] == "cmp":
            return COMPARE[node[2]](_value(node[1], values), _value(node[3], values))
        results = [truth(n) for n in node[1]]
        return all(results) if node[0] == "and" else any(results)
    held = truth(parse(text, measures, labels))
    def number(m):
        name, label = m.group(2), m.group(3)
        if not name or name not in measures:
            return m.group(0)
        v = (values.get(label or labels[0]) or {}).get(name)
        return m.group(0).replace(name + (f"@{label}" if label else ""), repr(v) if isinstance(v, float) else str(v))
    return held, TOKEN.sub(number, str(text)).strip()
