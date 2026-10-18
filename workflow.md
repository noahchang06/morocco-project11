# Implementation plan and operating workflow

## 1. Prepare the 20-document pilot — implemented

Read [pilot-plan.md](pilot-plan.md). This is a proposed feasibility selection, not a representative sample. The full TA collection contains 54 PDFs and 2,104 pages. The selection includes deployment leads, boundary cases and extraction challenges. `data/pilot/extraction-quality.json` flags missing text and suspicious control characters. These automated flags do not replace visual inspection.

Open [evidence-review.html](evidence-review.html) in a browser. Filter by a pilot filename, inspect a page, select text, click **Use selected passage**, enter deployment details, and save. Reuse a record ID to add another passage to the same deployment. Export before closing; work is held in memory. Import a prior export to resume. Keep independent backups of exports.

Human reviewers must confirm AI relevance, Moroccan location and source provenance. Do not invent a record for a document without eligible deployment evidence. Resolve OCR and corrupted text before selecting passages. The original PDFs remain in Downloads, unchanged.

## 2. Build and annotate evidence records — tooling implemented; human work pending

Save reviewed exports to `data/curated/records.jsonl`. Validate them and build a draft split:

```sh
python3 -m morocco.study data/curated/records.jsonl --output data/pilot-run
```

Organization IDs must be canonical across aliases. Inspect split counts before finalizing: hashing prevents cross-split organizations but cannot guarantee class balance or adequate test size. The pilot should be used for development, not reported as the final held-out test.

Create prediction-free reviewer packets:

```sh
python3 -m morocco.review --records data/curated/records.jsonl --output reviewer-packet.html
```

Give each reviewer a separate copy and have them export labels independently. The local tool does not enforce organizational access controls; keep predictions separate from reviewers. Compare exports:

```sh
python3 -m morocco.experiment agreement reviewer-a.jsonl reviewer-b.jsonl
```

Retain original labels, resolve disagreements, and save adjudicated gold records as JSONL objects containing `record_id` and `label`. The evaluation requires exactly the selected split’s gold IDs. Do not derive gold labels from model or baseline predictions.

## 3. Freeze and run the comparison — export/import path implemented

Choose the experimental model explicitly and confirm its actual availability. The proposal’s model name is not automatically an API identifier. No external model service is called by this implementation.

```sh
python3 -m morocco.experiment freeze data/curated/records.jsonl \
  --output data/experiment-v1 --model VERIFIED_MODEL_ID --as-of-date YYYY-MM-DD
```

The command creates a new directory and refuses to overwrite one. It records model designation, prompt, as-of date, split seed, rule code hash, frozen evidence, baseline predictions and model request objects. A manifest detects changes before evaluation. This is an integrity check, not protection against deliberate modification of both files and manifest.

Run `model_requests.jsonl` using the chosen model with fixed settings. Retain actual model identifier, provider version, generation settings, timestamps and failures in a separate `run_metadata.json`. Direct API execution and automatic verification of this metadata remain pending. Do not silently substitute models. Return one prediction per frozen input:

```json
{"record_id":"deployment-001","label":"announced","quote":"verbatim text from supplied evidence","evidence_index":0,"rationale":"Explanation"}
```

For an insufficiently supported claim without supporting quotation, use `quote: ""` and `evidence_index: null`. Every other quotation must be an exact substring of the referenced supplied passage. Quotation validity does not prove semantic support.

## 4. Evaluate and audit — implemented

```sh
python3 -m morocco.experiment evaluate data/experiment-v1 \
  --predictions model-predictions.jsonl --gold adjudicated-test.jsonl \
  --output data/results-v1
```

Outputs include fixed four-class macro-F1, per-class precision/recall/support, a confusion matrix, false-operational numerator and denominator, paired organization-cluster bootstrap intervals, and a false-operational audit queue. No operational predictions yields a null false-operational rate. Fewer than two organizations yields no bootstrap interval. Small samples and absent classes still limit interpretation. Confidence intervals are descriptive, not a substitute for adequate sample size.

Model predictions must cover all frozen records; gold labels cover exactly the selected split. Use `--split development` for explicitly development-only diagnostics. Evaluation refuses altered frozen files, duplicate/missing prediction IDs, invalid labels and unsupported quotation strings. Results save input hashes for traceability.

## Remaining research work

- Review the pilot, repair extraction, select evidence, normalize organizations and annotate independently.
- Refine and freeze the rule baseline and annotation guide on development data.
- Choose/verify a model and execute the fixed experiment.
- Manually assess semantic quotation support and false-operational errors.
- Implement the matched bilingual search collection and RQ2 coverage analysis; the TA folder has no matched-search provenance.
- Implement RQ3 sector/source robustness summaries once curated metadata and gold labels exist.

No deployment labels, model outputs, human agreement results or research accuracy scores have been fabricated. Synthetic tests validate software behavior only.

## Verification status

Seventeen automated tests pass, including a synthetic freeze-to-evaluation integration test, coverage for evidence metadata/edit controls, the development-calibration cue “intended to,” configurable pilot paths and Unicode-normalized source matching. On 2026-10-17, Xichen completed a macOS/Chrome walkthrough with one Idarati record and two evidence passages: validation passed, and export/resume produced a byte-identical re-export. The revised record editing and deletion controls still need an independent teammate walkthrough before live annotation.
