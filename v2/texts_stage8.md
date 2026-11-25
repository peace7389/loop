# v2, stage 8: what the checks of wrong input found
Every text changed in this stage, before and after (exact). `why` names the item of the audit or of the plan.

## the refusal of a network whose scheduler no flow passes: what is wrong, and no suggestion (found by the check of wrong input)

`harness/network.py`

before:

```
bad.append(f"no flow passes {sch}: put it on the side that sends, or use a plain queue")
```

after:

```
bad.append(f"no flow passes {sch}: a scheduler divides its link between the flows that pass it on that side")
```
