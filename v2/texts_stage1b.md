# v2, stage 1b: the briefs three-hosts-2 and three-hosts-link-2, and the chain rule's refusal
Every text changed in this stage, before and after (exact). `why` names the item of the audit or of the plan.

## A3: three-hosts-2: the description without the sentence that names the hidden behaviour, and without the words that say where the limit is

`briefs/three-hosts-2.json (from three-hosts)`

before:

```
A network of four hosts: a, b, r and c. Host a sends a TCP flow, fa, to c; host b sends a UDP flow, fb, to c at a constant rate ({fb.rate}, packets of {fb.packet_bytes} bytes). Both reach c through r, which forwards them. Link la joins a and r and link lb joins b and r; each carries {la.rate}. Link lc joins r and c and carries only {lc.rate} with a one-way delay of {lc.delay}: everything the two flows send to c must pass it. On r's side of lc a scheduler divides the link between the two flows by two parts, {lc.queue.parts.fa} for fa and {lc.queue.parts.fb} for fb (the parts are divided by their sum); each flow waits in a queue of its own of {lc.queue.length} packets, and a packet that arrives at a full queue is dropped. How the scheduler behaves when one flow has less to send than its part allows is not described here; finding that out is part of the work. The congestion control of fa is {fa.type}. In each simulation the flows start within the first 10 ms, traffic runs for one second that is not measured, and then for duration seconds, over which the outputs are measured.
```

after:

```
A network of four hosts: a, b, r and c. Host a sends a TCP flow, fa, to c; host b sends a UDP flow, fb, to c at a constant rate ({fb.rate}, packets of {fb.packet_bytes} bytes). Both reach c through r, which forwards them. Link la joins a and r and link lb joins b and r; each carries {la.rate}. Link lc joins r and c and carries {lc.rate} with a one-way delay of {lc.delay}. On r's side of lc a scheduler divides the link between the two flows by two parts, {lc.queue.parts.fa} for fa and {lc.queue.parts.fb} for fb (the parts are divided by their sum); each flow waits in a queue of its own of {lc.queue.length} packets, and a packet that arrives at a full queue is dropped. The congestion control of fa is {fa.type}. In each simulation the flows start within the first 10 ms, traffic runs for one second that is not measured, and then for duration seconds, over which the outputs are measured.
```

## A2: three-hosts-link-2: the description without the sentence on routes; its limits allow 6 hosts, 6 links and 4 flows (they were 4, 4 and 2 against the 4, 3 and 2 it has, which left one more link and nothing else)

`briefs/three-hosts-link-2.json (from three-hosts-link)`

before:

```
A network of four hosts: a, b, r and c. Link la joins a and r, link lb joins b and r, and link lc joins r and c. Links la and lb each carry {la.rate} with a one-way delay of {la.delay}; link lc carries {lc.rate} with a one-way delay of {lc.delay}. Flow fa is TCP from a to c: it always has data to send, and its congestion control is {fa.type}. Flow fb is UDP from b to c: packets of {fb.packet_bytes} bytes at a constant rate ({fb.rate}). A host with more than one link forwards packets. Each host sends a packet along the route with the fewest links to the packet's destination; the routes are worked out once, before traffic starts, and do not change during a simulation. On r's side of lc, packets wait in one queue of {lc.queue.length} packets, first in, first out, and a packet that arrives when it is full is dropped; every other side of a link has a plain queue of 100 packets. In each simulation the flows start within the first 10 ms, traffic runs for one second that is not measured, and then for duration seconds, over which the outputs are measured.
```

after:

```
A network of four hosts: a, b, r and c. Link la joins a and r, link lb joins b and r, and link lc joins r and c. Links la and lb each carry {la.rate} with a one-way delay of {la.delay}; link lc carries {lc.rate} with a one-way delay of {lc.delay}. Flow fa is TCP from a to c: it always has data to send, and its congestion control is {fa.type}. Flow fb is UDP from b to c: packets of {fb.packet_bytes} bytes at a constant rate ({fb.rate}). A host with more than one link forwards packets. On r's side of lc, packets wait in one queue of {lc.queue.length} packets, first in, first out, and a packet that arrives when it is full is dropped; every other side of a link has a plain queue of 100 packets. In each simulation the flows start within the first 10 ms, traffic runs for one second that is not measured, and then for duration seconds, over which the outputs are measured.
```

## A8 (narrow): the refusal of a guess that starts from old records says how an explanation not yet tried may be stated

`harness/loop.py`

before:

```
"; nothing has been learned since your last guess: test what is open, or look with a request, before you guess again")), "harness", None
```

after:

```
"; nothing has been learned since your last guess: test what is open, or look with a request, before you guess again")
                    + (". An explanation not tried yet may be stated without a new record as the competitor of an earlier guess: name that guess in competes_with and cite a record it cites" if COMP["on"] else "")), "harness", None
```
