# Recording an experiment

The capabilities lab is a measurement harness. Its examples validate that the
methods execute; they are not evidence of effectiveness on SFC's workload.

Use one stable research record per experiment:

| Field | What to record |
|---|---|
| Question | Concrete system behavior being measured |
| Status | Exploratory, preregistered, running, completed, or inconclusive |
| Code | Git commit, method version, implementation hash |
| Data | Dataset ID/version/hash, provenance and permissions; synthetic vs operational |
| Task | Inputs, required outputs, protected facts and reviewer rubric |
| Configuration | Budget, method parameters, model/provider, prompt and workflow versions |
| Comparators | Full context where it fits; retrieval only; fixed summary; proposed composition |
| Execution | Hardware/runtime versions, timestamp, warmup, repetitions and seeds where applicable |
| Measurements | Method and whole-run latency, wire bytes, API requests/tokens, retries and failures |
| Quality | Required-fact recall, supported-claim precision, correction retention and task correctness |
| Review | Reviewer identity, disagreements and unresolved ambiguity |
| Outcome | All results, uncertainty, limitations and follow-up decision |

Quality metrics require a labeled ground truth and task-specific scoring:

$$
\mathrm{required\ fact\ recall}=\frac{\#\text{required facts correctly retained}}
{\#\text{required facts}},\qquad
\mathrm{claim\ precision}=\frac{\#\text{supported material claims}}
{\#\text{material claims made}}.
$$

Return undefined rather than 100% for an empty denominator. Citation existence
alone does not establish support; assess whether the cited source entails the
claim and whether later corrections supersede it.

Use the same task set and model for comparisons; sweep budgets explicitly.
Include compression and retrieval overhead in total latency and cost. Preserve
held-out tasks and failure cases, especially mundane corrections, conflicting
records, missing qualifiers and changed goals. Do not multiply individual method
ratios to claim a system compression ratio.

The lab's download includes exact input/output, configuration, source hashes and
timing. Measurement history intentionally excludes content. Exact independent
reproduction therefore also needs the downloaded bundle or an approved retained
dataset; hashes alone cannot reconstruct it. No production records belong in Git.
