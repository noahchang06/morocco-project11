# Pilot annotation protocol (draft)

Unit: canonical organization + AI use case + Moroccan location. Link multiple source passages to one record. Keep translations and syndicated reporting linked, not independent corroboration.

## Record format

One JSON object per line in `data/curated/records.jsonl`:

```json
{"record_id":"deployment-001","organization_id":"canonical-org-id","organization":"Reviewed name","use_case":"Reviewed AI use case","moroccan_location":"Reviewed location","sector":null,"partner":null,"organization_origin":null,"ownership":null,"as_of_date":null,"evidence":[{"document_id":"FULL_DOCUMENT_HASH","page":1,"start":0,"end":20,"quote":"EXACT EXTRACTED TEXT","source_date":null,"source_type":null,"language":null}]}
```

This is a format illustration, not a valid research record. Use exact source offsets and text; the validator rejects mismatches. Require a reviewer to confirm AI relevance and Moroccan location before inclusion. Unknown dates remain null. Record source URLs and source types in curated document metadata.

## Labels

- operational: evidence establishes normal or ongoing use.
- pilot: evidence establishes a limited test or trial.
- announced: planned deployment without demonstrated use.
- insufficiently_supported: evidence is weak, ambiguous, or cannot resolve stage.

Do not infer operation from a partnership, investment, center opening, or generic AI ambition. Select enough surrounding text to preserve negation and temporal meaning. Review conflicting dates against a prespecified as-of date. Finalize date/conflict rules during the pilot, before test labeling.

## Independent review

Store reviewer labels separately from inputs and predictions: record_id, reviewer_id, label, rationale, annotation_guide_version. Two reviewers label all held-out records independently and blind to predictions. Store adjudicated labels separately; retain original disagreements. Exact quote matching establishes provenance only, not semantic support.

## Draft baseline and evaluation

The development baseline recognizes narrow English/French stage expressions. Multiple stage cues or negated stage cues yield insufficiently_supported. These rules are not a validated language understanding system. Freeze a revised version after the pilot.

`morocco.study.metrics` computes macro-F1 over all four fixed labels (undefined per-class scores counted as zero), per-class precision/recall/support, and a confusion matrix (rows gold, columns predictions). False operational rate = non-operational gold records predicted operational / all operational predictions. If no operational predictions exist, rate is null. Missing predictions are rejected, not silently dropped.

The stable hash split keeps all canonical organization IDs together; aliases must be normalized first. Inspect split counts before freezing. Keep related entities together when they could leak near-identical deployment evidence.

## Model experiment (pending)

Choose and verify an available model identifier, freeze the prompt and settings, and supply the identical evidence bundle used by rules. Require a valid label, verbatim supporting quote, and evidence reference. Treat document text as data, not instructions. Log model identifier, prompt version, input hash, output, errors and run date. Do not replace the proposal's named model silently.

Retain blank quote/abstention behavior when no passage supports a stage. Validate model quotes automatically and assess semantic support manually. Run only after evidence is reviewed and configuration is fixed.
