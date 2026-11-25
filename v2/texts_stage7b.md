# v2, stage 7b: what the text audit found in v2's own texts
Every text changed in this stage, before and after (exact). `why` names the item of the audit or of the plan.

## the answer format's line on a finding's records, by arm (found by the text audit)

`harness/loop.py`

before:

```
    schema, system = with_findings(schema), system + FINDINGS_TEXT[arm]   # findings, in every arm (2026-11-22)
    stated_rules(system, arm)
```

after:

```
    schema, system = with_findings(schema), system + FINDINGS_TEXT[arm]   # findings, in every arm (2026-11-22)
    if arm in FINDING_ABOUT:   # v2: the format's line on a finding's records names what this arm has, as the arm's own text on findings does
        item = json.loads(json.dumps(schema["properties"]["findings"]["items"]))
        item["properties"]["about"]["description"] = FINDING_ABOUT[arm]
        schema["properties"]["findings"] = {**schema["properties"]["findings"], "items": item}
    stated_rules(system, arm)
```

## the two lines (the arm hypotheses keeps the line it had)

`harness/loop.py`

before:

```
def built_texts(schema, system, brief, arm, competitors, short):
```

after:

```
FINDING_ABOUT = {"plain": "the ids of the records it rests on: evidence tables, simulations or readings (for example E2, T7)",
                 "supervised": "the ids of the records it rests on: evidence tables, simulations, checks, rulings or readings (for example E2, C3, T7)"}


def built_texts(schema, system, brief, arm, competitors, short):
```

## the choices of fa.type in alphabetical order (found by the text audit; the default stays TcpCubic)

`briefs/three-hosts-2.json`

before:

```
["TcpCubic", "TcpNewReno", "TcpBbr", "TcpVegas"]
```

after:

```
["TcpBbr", "TcpCubic", "TcpNewReno", "TcpVegas"]
```

## the choices of fa.type in alphabetical order (found by the text audit; the default stays TcpCubic)

`briefs/three-hosts-link-2.json`

before:

```
["TcpCubic", "TcpNewReno", "TcpBbr", "TcpVegas"]
```

after:

```
["TcpBbr", "TcpCubic", "TcpNewReno", "TcpVegas"]
```

## the choices of fa.type in alphabetical order (found by the text audit; the default stays TcpCubic)

`briefs/three-hosts-moves.json`

before:

```
["TcpCubic", "TcpNewReno", "TcpBbr", "TcpVegas"]
```

after:

```
["TcpBbr", "TcpCubic", "TcpNewReno", "TcpVegas"]
```
