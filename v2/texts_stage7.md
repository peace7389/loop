# v2, stage 7: the instructions and the format built in one function (no text changed)
Every text changed in this stage, before and after (exact). `why` names the item of the audit or of the plan.

## no text changed: main builds the instructions and the format through loop.built_texts

`harness/loop.py`

before:

```
    if arm == "plain":
        schema, system = plain_format(schema), plain_prompt(system)
    competitors = arm == "supervised" and (json.loads((tools.SESSION / "session.json").read_text()).get("flags", {}).get("competitors", False) if was else COMPETITORS)   # a session keeps what it started with
    COMP["on"] = competitors
    if arm == "supervised":
        schema, system = supervised_format(schema, competitors), supervised_prompt(system, competitors)
    # the short format of the arm "hypotheses" (2026-11-22): a new session, or one that started in it; a session started before keeps the full format
    short = SHORT_FORMAT and arm == "hypotheses" and (was is None or json.loads((tools.SESSION / "session.json").read_text()).get("flags", {}).get("format") == "short")
    if short:
        schema, system = short_format(schema), short_prompt(system)
    asks_budget = arm == "plain" or (arm == "hypotheses" and not short)   # the formats that still have budget_request (the turn's text names it)
    if may_change(brief):  # only a session that may change the structure is told how
        plain_s = structure_text(brief)
        for a_, b_ in STRUCTURE_PLAIN if arm == "plain" else ():
            assert plain_s.count(a_) == 1, a_
            plain_s = plain_s.replace(a_, b_)
        system += plain_s
    schema, system = with_findings(schema), system + FINDINGS_TEXT[arm]   # findings, in every arm (2026-11-22)
    stated_rules(system, arm)
    stated_new_link(system, brief)
    if arm == "plain" and [w for w in PLAIN_WORDS if w in system.lower()]:   # the plain arm is told nothing of hypotheses (the coherence audit, 2026-11-22: STRUCTURE was added after plain_prompt's check)
        raise ValueError(f"the instructions of the arm 'plain' name: {', '.join(w for w in PLAIN_WORDS if w in system.lower())}")
    try:   # a label's length, in the answer format too
        schema["properties"]["experiment"]["anyOf"][0]["properties"]["runs"]["items"]["properties"]["label"]["maxLength"] = LABEL_MOST
    except (KeyError, IndexError, TypeError):
        pass
    if isinstance(schema["properties"].get("requests"), dict):   # the most requests a reply may hold, in the answer format too (the coherence audit, 2026-11-22)
        schema["properties"]["requests"]["maxItems"] = LOOKS if arm == "supervised" else REQUESTS_MOST

```

after:

```
    competitors = arm == "supervised" and (json.loads((tools.SESSION / "session.json").read_text()).get("flags", {}).get("competitors", False) if was else COMPETITORS)   # a session keeps what it started with
    COMP["on"] = competitors
    # the short format of the arm "hypotheses" (2026-11-22): a new session, or one that started in it; a session started before keeps the full format
    short = SHORT_FORMAT and arm == "hypotheses" and (was is None or json.loads((tools.SESSION / "session.json").read_text()).get("flags", {}).get("format") == "short")
    asks_budget = arm == "plain" or (arm == "hypotheses" and not short)   # the formats that still have budget_request (the turn's text names it)
    schema, system = built_texts(schema, system, brief, arm, competitors, short)   # the instructions and the format, as every text audit reads them too

```

## no text changed: the lines main had, as a function of their own (same order)

`harness/loop.py`

before:

```
def main():
    ap = argparse.ArgumentParser()

```

after:

```
def built_texts(schema, system, brief, arm, competitors, short):
    """The instructions and the answer format of a session as the loop sends them: main calls it, and harness/text_audit.py to write the texts out
    without a session. schema: answer_format(schema.json, the brief); system: prompt.txt. COMP["on"] is set by the caller (competitors)."""
    if arm == "plain":
        schema, system = plain_format(schema), plain_prompt(system)
    if arm == "supervised":
        schema, system = supervised_format(schema, competitors), supervised_prompt(system, competitors)
    if short:
        schema, system = short_format(schema), short_prompt(system)
    if may_change(brief):  # only a session that may change the structure is told how
        plain_s = structure_text(brief)
        for a_, b_ in STRUCTURE_PLAIN if arm == "plain" else ():
            assert plain_s.count(a_) == 1, a_
            plain_s = plain_s.replace(a_, b_)
        system += plain_s
    schema, system = with_findings(schema), system + FINDINGS_TEXT[arm]   # findings, in every arm (2026-11-22)
    stated_rules(system, arm)
    stated_new_link(system, brief)
    if arm == "plain" and [w for w in PLAIN_WORDS if w in system.lower()]:   # the plain arm is told nothing of hypotheses (the coherence audit, 2026-11-22: STRUCTURE was added after plain_prompt's check)
        raise ValueError(f"the instructions of the arm 'plain' name: {', '.join(w for w in PLAIN_WORDS if w in system.lower())}")
    try:   # a label's length, in the answer format too
        schema["properties"]["experiment"]["anyOf"][0]["properties"]["runs"]["items"]["properties"]["label"]["maxLength"] = LABEL_MOST
    except (KeyError, IndexError, TypeError):
        pass
    if isinstance(schema["properties"].get("requests"), dict):   # the most requests a reply may hold, in the answer format too (the coherence audit, 2026-11-22)
        schema["properties"]["requests"]["maxItems"] = LOOKS if arm == "supervised" else REQUESTS_MOST
    return schema, system


def main():
    ap = argparse.ArgumentParser()

```
