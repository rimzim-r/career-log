# Evaluation results

Setup: 20 log entries across 8 projects, 25 test requests (14 covered by the log, 11 not covered).
Generator prompt: one bullet per project, only facts from cited entries, relevance rules.

| Model | Abstention (uncovered) | Supported bullets | Project recall | Errors |
|---|---|---|---|---|
| openai/gpt-oss-20b (Groq) | 11 / 11 | 24 / 24 | 0.98 | 0 |

What "supported" means: the bullet cites a real entry, every number in it appears in the cited entries,
and it uses none of a fixed list of risky words (deployed, pipeline, production, SQL, and so on)
that the cited entries do not use.

## Limits of this evaluation

- The checker cannot catch vague overclaims. For example, "matching fine-tuned DistilBERT" passed
  although the entry says "statistically indistinguishable".
- The 25 requests were written by me for my own log, so they test this log, not resumes in general.
- Results come from single runs. The model varies slightly between runs.
- An earlier prompt let the model write bullets for "A/B testing" from an ablation and a baseline
  comparison (abstention 10 / 11). Adding relevance rules fixed it (11 / 11).
- Two recall misses came from gaps in my own log, not from the model. Fixing the log fixed them.
