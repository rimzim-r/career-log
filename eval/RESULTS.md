# Evaluation results

The evaluation sends 25 test requests through the bullet generator: 14 that the log covers and 11 that it does not (for example Kubernetes, Java, mobile apps, A/B testing). It checks three things.

- **Abstention.** A request the log does not cover should return no bullets.
- **Supported bullets.** A bullet is supported if it cites a real entry, every number in it appears in the cited entries, and it uses none of a fixed list of risky words (or their forms, such as deploy, deployed, deploying) that the cited entries do not use.
- **Project recall.** For a covered request, how many of the expected projects show up in the answer.

## Final run

Run on 2026-10-20 with `openai/gpt-oss-20b` on Groq. The log had 23 entries across 8 projects. Retrieval fetched 12 entries per request, the model ran at temperature 0, and a failed model reply raises an error instead of returning an empty answer.

| Metric | Result |
|---|---|
| Errors | 0 |
| Abstention on requests the log does not cover | 11 / 11 |
| Fully supported bullets | 24 / 24 |
| Average project recall | 0.90 |
| Covered requests with at least one expected project | 13 / 14 |

## All runs

Runs differ in log size, model, retrieval settings and checker, so they are not strictly comparable. They show what each change did.

| # | Log entries | Model | What changed | Abstention | Supported | Recall | At least one project |
|---|---|---|---|---|---|---|---|
| 1 | 19 | gpt-oss-120b | Baseline prompt | 10 / 11 | 29 / 29 | 1.00 | 14 / 14 |
| 2 | 19 | gpt-oss-120b | Added relevance rules | 11 / 11 | 24 / 24 | 0.93 | 14 / 14 |
| 3 | 20 | gpt-oss-20b | Filled two gaps in the log | 11 / 11 | 24 / 24 | 0.98 | 14 / 14 |
| 4 | 23 | gpt-oss-20b | Log grew with check-in entries | 11 / 11 | 26 / 26 | 0.90 | 13 / 14 |
| 5 | 23 | gpt-oss-20b | Retrieval 8 to 12 entries | 11 / 11 | 21 / 23 | 0.90 | 13 / 14 |
| 6 | 23 | gpt-oss-20b | Repeat of run 5 | 10 / 11 | 23 / 25 | 0.90 | 13 / 14 |
| 7 | 23 | gpt-oss-20b | Wider risky-word check and number sources | 10 / 11 | 21 / 21 | 0.83 | 12 / 14 |
| 8 | 23 | gpt-oss-20b | Temperature 0, larger token budget, loud failures | 11 / 11 | 24 / 24 | 0.90 | 13 / 14 |

## What the runs showed

- **The relevance rules fixed a real fault.** In run 1 the model wrote bullets for "A/B testing" from a model comparison and an ablation. Run 2 added rules against adjacent work and abstention reached 11 / 11.
- **Gaps in the log looked like model errors.** Two early recall misses came from entries that did not say what the request asked for. Adding the missing facts to the log fixed them.
- **Retrieval, not the model, hid the phishing project.** With 8 results per request, no phishing entry reached the model for "machine learning projects" or "research and writing papers". Fetching 12 fixed retrieval, though recall did not change because the model then chose a different subset.
- **The checker caught real problems.** Flagged bullets included an added "real-time", an added "deploying", an "improved" the entry did not use, and a true number (5,136 hours) cited from the wrong entry. The last one led to a rule that cites the entry holding a number when it belongs to the same project.
- **Results vary from run to run.** Across runs 3 to 8, recall ranged from 0.83 to 0.98 on near-identical code. Fixing the temperature at 0 made the final run steadier, but 25 requests is a small sample and each figure comes from a single run.

## Known limits

- **Off-topic bullets on A/B testing.** In 2 of the 4 runs before the final one, the model wrote faithful but irrelevant bullets for "A/B testing and experimentation" (phishing and ensemble results). Every fact in them was true, but none was A/B testing. The final run abstained. This is a weakness of the small model, not something the checker can detect.
- **Recall misses.** "Research and writing papers" returned no bullets in several runs and one bullet in others. "Machine learning projects" sometimes omitted the phishing project. Search finds these projects, so the cause is the model's choice of which projects to write about.
- **The checker is partial.** It catches numbers and a fixed list of risky words and their forms. It does not catch vague overclaims, so bullets still need a human read.
- **The scoring changed mid-way.** Runs 7 and 8 use a stricter checker than runs 1 to 6, and the evaluation counts a bullet as supported when its number is found in another entry of the same project.
- **Silent failures were possible before run 8.** Before run 8, two invalid replies from the model produced an empty answer that looked like "nothing relevant". One zero-bullet case was checked directly and was the model's own choice, but earlier abstention figures cannot rule out occasional hidden failures.
- **The test requests are mine.** They were written for this log, so they test this log, not resumes in general.