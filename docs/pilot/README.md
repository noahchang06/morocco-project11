# Deployment-stage evaluation on the November 9 records

The team ran a bilingual rule baseline and `gpt-4.1-mini-2025-04-14` on 15 supplied claims about AI applications in Morocco. Both methods received the same short quotations and metadata, with November 8, 2026 as the evidence cutoff. All 15 model responses passed output validation. The working reference excluded one discontinued workflow after prediction, leaving 14 scored records from 13 organizations. Every record was treated as development data. The [technical appendix](APPENDIX.md) documents what each method saw and how the working reference was formed.

## Classification results

| Method | Macro-F1 on 14 primary records | Macro-F1 on all 15 | False operational / all operational predictions (both cohorts) |
| --- | ---: | ---: | --- |
| Rules | 0.1500 | 0.1591 | 0 / 0 (undefined) |
| LLM | 0.4504 | 0.4754 | 1 / 4 (25%) |

Macro-F1 gives equal weight to the four stages. The all-15 sensitivity calculation counts the excluded workflow as insufficiently supported because its evidence was outdated. Both calculations use the saved predictions. The rules classified every record as insufficiently supported. The LLM identified all three reference operational cases and called one reference pilot operational. Neither reference pilot received a pilot prediction.

The primary confusion matrices use the reference stage for rows. Each group of four predicted counts is ordered **operational, pilot, announced, insufficiently supported**.

| Reference stage | Rules O | Rules P | Rules A | Rules I | LLM O | LLM P | LLM A | LLM I |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Operational | 0 | 0 | 0 | 3 | 3 | 0 | 0 | 0 |
| Pilot | 0 | 0 | 0 | 2 | 1 | 0 | 1 | 0 |
| Announced | 0 | 0 | 0 | 3 | 0 | 1 | 2 | 0 |
| Insufficiently supported | 0 | 0 | 0 | 6 | 0 | 1 | 3 | 2 |

## Review agreement and interpretation

The two supplied review files contained stage labels for the same 14 records. Before adjudication, the reviews agreed on 11 stages (78.6%, unweighted Cohen's κ = 0.664). One initial review explicitly described its labels as AI-assisted and provisional. Xichen took responsibility for AI-assisted adjudication after the model outputs had been inspected. Adjudication could draw on fuller source material than either classifier received.

Matching the classifier inputs removed the earlier difference in access to context. The rules applied a hard two-year check to exactly dated evidence, while the LLM applied the age instruction inconsistently. The score difference therefore reflects both classification and adherence to that instruction. The small convenience sample and timing of adjudication limit conclusions to this retrospective comparison.

## Sector robustness

The primary records span ten sectors. Removing the six records labelled insufficiently supported for outdated evidence leaves eight records across six sectors. These eight include announcements, pilots and operational cases.

| Sector | Primary count (share of 14) | After filtering (share of 8) |
| --- | ---: | ---: |
| Banking / finance | 3 (21.4%) | 1 (12.5%) |
| Health | 2 (14.3%) | 2 (25.0%) |
| Public safety | 2 (14.3%) | 2 (25.0%) |
| Customs / public finance | 1 (7.1%) | 1 (12.5%) |
| Education | 1 (7.1%) | 1 (12.5%) |
| Industry / mining | 1 (7.1%) | 1 (12.5%) |
| Agriculture | 1 (7.1%) | 0 (0.0%) |
| Justice | 1 (7.1%) | 0 (0.0%) |
| Transport / aviation | 1 (7.1%) | 0 (0.0%) |
| Transport / rail | 1 (7.1%) | 0 (0.0%) |

Health and public safety each retain two records. Their shares rise because the denominator falls from 14 to eight. These proportions describe the records collected for this pilot.

## Reproduce the tables

From the repository root, run the following commands with Python 3.

```sh
python3 docs/pilot/scorecard.py
python3 -m unittest discover -s tests -v
```

The [scorecard](scorecard.py) reads [aggregate counts](counts.json) and prints the classification scores for both cohorts, original review agreement and sector shares as JSON. The value `null` represents an undefined rate. Neither command requires an API key. The team retains the original record inputs, raw responses and review decisions in its November 9 review archive. The [November 8 checkpoint](../../PROGRESS_2026-11-08.md) covers a separate five-record exercise.

Team members with the original ZIP can also reconstruct the published counts from the archived review entries, frozen predictions, reference labels and sectors. The verifier checks both SHA-256 manifests and compares every reconstructed cell with the public table.

```sh
python3 docs/pilot/verify_archive.py /path/to/Morocco_review_2026-11-09.zip
```

For the editable manuscript, the [section revisions](manuscript-updates.tex) give the replacement passages and [LaTeX appendix](paper-appendix.tex) includes the evaluation diagram and exact prompt.
