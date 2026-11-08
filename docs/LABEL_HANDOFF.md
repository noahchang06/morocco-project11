# Completing the human review and evaluation

The current cohort needs two independent human exports, not another model run. No project gold labels or agreement scores exist yet. Keep the private experiment outputs hidden until reference labels are locked.

## Independent reviewers

Noah and Yuxin each open the existing blind reviewer packet, verify all four test records, label independently, and export one JSONL file. Use a consistent, distinct reviewer ID, the packet guide version, exact source quotations, and notes explaining any translation assistance. Record substantive field problems as needs_correction with a null stage. Save the original exports before discussion.

Place the exports at data/incoming/noah.jsonl and data/incoming/yuxin.jsonl. The filenames are conventions; no empty placeholder labels have been created.

## Validate and prepare adjudication

```bash
python -m morocco.finalize prepare \
  --frozen data/execution-20261108-v1/frozen \
  --reviewer-a data/incoming/noah.jsonl \
  --reviewer-b data/incoming/yuxin.jsonl \
  --output data/review-round-1
```

The command checks exact IDs, distinct recorded reviewer identities, guide versions, field confirmation, labels, reason codes, nonempty rationales, exact quote provenance and translation notes. It copies both original files and seals them with hashes.

If fields need correction, it produces field-corrections.json and blocks scoring; it does not silently omit records or interpret null labels as a stage. Correct the evidence in a new version and disclose the change. Do not modify the sealed source experiment.

When all fields are confirmed, agreement.json records raw agreement and Cohen's kappa from the original independent labels. Consensus rows are derived only from the two human exports. Different stages or insufficiency reason codes generate disagreements.jsonl and an offline adjudication-packet.html containing the evidence and both annotations, but no model predictions. A distinct human adjudicator resolves these and exports adjudicator.jsonl. The software cannot verify that reviewers or the adjudicator actually remained blind; that procedure must be followed by the team.

## Finalize without another API call

```bash
python -m morocco.finalize finalize \
  --frozen data/execution-20261108-v1/frozen \
  --prepared data/review-round-1 \
  --run data/execution-20261108-v1/llm-test \
  --adjudication data/incoming/adjudicator.jsonl \
  --output data/final-results
```

Omit --adjudication only when there are no disputed stage/reason codes. The adjudicator's identity must differ from both original reviewers. Both output directories must be new, preventing accidental overwrites.

Finalization revalidates the sealed independent exports and input hashes, locks reference labels, then reconstructs accepted predictions and failures from the original raw model responses. It makes no API call. Missing or mismatched raw responses stop finalization. The original pending-review experiment is unchanged. A separate study snapshot contains only the confirmed test inputs, byte-equivalent evidence packets, copied rule outputs and a human-review attestation.

Outputs include agreement.json, gold.jsonl, human-review-attestation.json, the reviewed snapshot, evaluation/results.json, evaluation/report.md, report_sections.md and evaluation/false_operational_audit.jsonl. Response failures remain in the four-record denominator and count as false negatives for their gold class; invalid_output is an audit column, not a fifth stage. Raw agreement is never recomputed from adjudicated labels. The replication is kept as a separate reliability diagnostic.

The command can validate names, hashes and fields, but cannot authenticate the humans or establish their actual independence. Do not substitute assistant-generated labels. All current software tests use temporary synthetic fixtures and are not project evaluation results.
