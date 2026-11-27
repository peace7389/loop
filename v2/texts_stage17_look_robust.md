# after v2.2: a look of the supervisor that fails does not stop the session
Every text changed in this stage, before and after (exact). `why` names the item of the audit or of the plan.

## (code) a failed look gives a note and the session goes on, whatever failed

`harness/loop.py`

before:

```
                    except (ValueError, KeyError, TypeError) as e:
                        append(ledger, turn, "note", due[-1], {"text": f"the supervisor's look at {', '.join(due)} could not be read ({type(e).__name__}): no finding of its own"})
```

after:

```
                    except Exception as e:   # its look is not needed to go on: a note, and the session goes on (also at a model server error, as the look at the baseline was)
                        append(ledger, turn, "note", due[-1], {"text": f"the supervisor's look at {', '.join(due)} could not be read ({type(e).__name__}): no finding of its own"})
```
