# Implemented information mechanisms

Method implementation version: 0.1.0. First implementation: 2026-11-19 (America/New_York).
Code: `src/franark/capabilities.py`. This is a reproducible baseline suite, not
the literal six-stage neural architecture in the original simulator.

## A01: budgeted selection — `memory.select`

Background: Robertson and Zaragoza (2009), DOI
[10.1561/1500000019](https://doi.org/10.1561/1500000019), describes the probabilistic
relevance framework. Our positive-IDF variant and defaults follow
[Lucene BM25Similarity](https://lucene.apache.org/core/9_9_1/core/org/apache/lucene/search/similarities/BM25Similarity.html).

For unique query terms, document frequency $n_q$, corpus size $N$, term count
$f(q,d)$, document length $|d|$ and mean length $\overline{l}$:

$$
s(d,Q)=\sum_{q\in Q}\log\left(1+\frac{N-n_q+0.5}{n_q+0.5}\right)
\frac{f(q,d)(k_1+1)}{f(q,d)+k_1(1-b+b|d|/\overline{l})}.
$$

Defaults are $k_1=1.2$, $b=0.75$. Unicode word counts are used, with no stemming,
stop list, embeddings or model-token counting. Stable score ordering is followed
by greedy whole-document selection. Pinned documents are included first; exceeding
their budget raises an error. Actual selected JSON must fit the requested byte
budget. This is a heuristic packing rule, not an optimal knapsack solver.

Failure modes include synonym mismatch, missing context and oversized relevant
documents. Relevance scores are not probabilities. Source ID and version
references describe caller-provided material, not independently authenticated facts.

## A02: exact state differences — `memory.delta`

Background: [RFC 6902](https://www.rfc-editor.org/rfc/rfc6902.html), Bryan and
Nottingham (2013). We implement an `add`/`remove`/`replace` subset; arrays are
replaced atomically. This is not a general-purpose implementation of all JSON
Patch operations and is not a learned predictive model.

$$
\Delta_t=\operatorname{diff}(x_{t-1},x_t),\qquad
\operatorname{apply}(x_{t-1},\Delta_t)=x_t.
$$

The packet includes source versions and SHA-256 hashes of both canonical states.
Replay checks the base and reconstructed hashes. Even a one-day birthdate change
is emitted; no surprise threshold suppresses small changes. A difference is not
an error verdict: a reviewer must establish the correct value.

## A03: exact repeated-pattern encoding — `memory.pack`

Background: Deutsch (1996), [RFC 1951](https://www.rfc-editor.org/rfc/rfc1951.html).
DEFLATE combines repeated-substring coding and Huffman coding. We use Python
`zlib`, with the compressed stream carried in a base64 JSON envelope.

$$
\operatorname{decode}(\operatorname{encode}(m))=m.
$$

Every call verifies UTF-8 reconstruction and its hash. The reusable decoder bounds
expansion and rejects trailing/incomplete data. Compression level defaults to 6.
Envelope and base64 overhead count in output size; small messages can grow.
This is a storage/transport codec. It is not a shorter natural-language prompt,
learned procedural macro, or replacement for the original brain-inspired chunker.

## A04: explicit task projection — `memory.project`

Engineering baseline: copy an explicit set of fields, addressed with
[RFC 6901 JSON Pointers](https://www.rfc-editor.org/rfc/rfc6901.html), Bryan,
Zyp and Nottingham (2013).

$$
P_{S,C}(x)=\{(p,x[p]):p\in S\cup C\},
$$

where $S$ is the task's field list and $C$ its protected fields. Missing fields
are returned explicitly. Source/version/hash references remain attached. This
is not learned manifold compression or an information-bottleneck optimizer.
Selecting protected fields and proving task sufficiency remain workflow design
decisions. Projection is also not an authorization control: the API must restrict
the source record before an agent can receive it.

## A05: extractive briefings — `memory.summarize`

Background: Carbonell and Goldstein (1998),
[DOI 10.1145/290941.291025](https://doi.org/10.1145/290941.291025),
[author-hosted paper](https://www.cs.cmu.edu/afs/cs/Web/People/jgc/publication/MMR_DiversityBased_Reranking_SIGIR_1998.pdf).
Our implementation uses BM25 relevance and bag-of-words cosine redundancy:

$$
d^*=\arg\max_{d\notin A}\left[\lambda\widetilde{s}(d,Q)
-(1-\lambda)\max_{a\in A}\cos(v_d,v_a)\right].
$$

Scores are normalized by the maximum candidate score, with $\lambda=0.7$ by
default. Complete sentences are selected under byte and sentence limits; pinned
documents pin all their sentences. The chosen excerpts are returned in original
source order, with Python character offsets (not UTF-8 byte offsets).

This is an established extractive baseline, not generative synthesis. Exact
wording does not prove semantic completeness: omitted negations, qualifications,
later corrections or context can still change interpretation. No fabricated
entailment audit or semantic-drift percentage is displayed. Input is capped at
500 candidate sentences. Review generation and factual coverage require separate
evaluation against a labeled task set.

## A06: boundary timelines — `memory.timeline`

Engineering background: Fowler's (2005)
[Event Sourcing](https://martinfowler.com/eaaDev/EventSourcing.html) explains why
change history matters. The implemented view builder is not a complete event
sourcing platform and does not implement a research paper's surprise detector.

$$
K=\{0,n-1\}\cup\{t:h(x_t)\ne h(x_{t-1})\}
\cup K_{\mathrm{critical}}\cup K_{\mathrm{heartbeat}}.
$$

All state changes are retained, including gradual small changes. Only identical
consecutive states can be coalesced. Critical markers, the first/final state and
periodic heartbeats are retained, with folded event IDs pointing back to the
originals. Inputs must have unique IDs, chronological timestamps and timezones.
Different source systems may deliver late corrections; reconciling effective time
and observed time is a future application concern. Originals remain necessary.

## Measurement semantics

Each execution returns method/version, implementation-file SHA-256, input/output
hashes, wall time, current-thread CPU time and canonical UTF-8 JSON sizes. Timing
covers the method and output serialization; it excludes input validation, HTTP,
database persistence and surrounding model calls. All timings are observed on
the executing host, not hardware-independent predictions.

$$
r_{\mathrm{wire}}=\frac{|\mathrm{canonical}(input)|}
{|\mathrm{canonical}(result)|}.
$$

The wire ratio includes configuration and provenance overhead. Ratios across
different inputs/methods are not directly comparable. The selector/summary also
return the exact bytes of the selected representation. Model tokens, semantic
fidelity and power are null for local methods. Actual provider token usage is
recorded separately when the OpenAI response supplies it. Model price is not
inferred; estimates would need a dated pricing configuration.

The six methods do not automatically compose. They should be selected according
to the task, type contract, budget and measured outcome. Source hashes establish
byte identity, not factual truth, access rights, signed-document authenticity or
clinical correctness.
