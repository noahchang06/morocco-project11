# Morocco Diplomacy Lab Project 11 — team handoff

**Status verified: October 17, 2026. Team: Noah, Yuxin, Xichen.**

This handoff supersedes earlier progress messages where they imply a completed research system. We have implemented and tested a local research scaffold and processed a starting document collection. We have not yet produced a human-reviewed deployment dataset or run a real model comparison. Suggested responsibilities below are future assignments, not claims about contributions already made.

## 1. Purpose and confirmed scope

Assigned sponsor project: **Winning the AI Race in Morocco: A Commercial Strategy for North and West Africa**, supporting the U.S. Consulate General Casablanca. The research proposal is **Mapping Public Evidence of AI Deployment in Morocco**. The sponsor-facing goal is a traceable deployment database and evidence for a white paper about Morocco’s AI ecosystem and commercial partnerships.

The confirmed academic task is classification of publicly documented deployment maturity. The user explicitly chose to keep this study after an earlier chat proposed changing to a RAG chatbot.

- **RQ1 — accuracy:** compare an LLM with a fixed bilingual rule baseline against human labels; primary metric macro-F1.
- **RQ2 — coverage:** compare organizations, sectors and evidence discovered through matched English/French searches with equal budgets.
- **RQ3 — robustness:** examine insufficiently supported claims and changes in sector distributions when weak evidence is removed.

Original scale: approximately 150 English/French documents, targeting at least 100 unique deployment records, preceded by a 20-document pilot. These are targets, not achieved counts. Feasibility must be reassessed after the pilot. The current TA collection was not assembled under a matched-search protocol and cannot by itself answer RQ2.

A deployment record represents **canonical organization + AI use case + Moroccan location**. Multiple documents/passages can support one record. One document can describe multiple records. Labels are `operational`, `pilot`, `announced`, and `insufficiently_supported`. Documents that do not contain an eligible deployment claim should be excluded from the classification dataset rather than automatically receiving the last label.

The dataset measures public evidence, not national deployment prevalence. Missing evidence is not proof of non-deployment. Arabic sources are preserved in the collection but remain outside the original English/French classification scope unless the team formally revises it.

## 2. RAG architecture: discussed, not implemented

An earlier Morocco chat proposed PDF extraction → page-bounded chunks → multilingual E5 embeddings → FAISS retrieval → fixed GPT answer generation → cited answers → Streamlit interface. It also proposed comparison against an LLM without retrieval and a Moroccan user study. **That was a proposed alternative direction, not the implemented system or the confirmed evaluation plan.**

No embedding model, vector index, semantic retriever, question-answering service, RAG comparison, Streamlit app, or Moroccan user study has been implemented. Existing chunks are text passages, not vectors. The offline HTML tool is an annotation interface, not a chatbot. RAG work should only resume after an explicit scope decision; it is unnecessary for the present classification experiment.

Current architecture:

```text
Local source PDFs
  → inventory + extraction + physical page preservation
  → page-bounded chunks + quality flags
  → HUMAN claim selection and deployment normalization [pending]
  → exact-quotation validation
  → canonical-organization development/test grouping
  → independent human labels + adjudication [pending]
  → frozen identical evidence inputs
       ├─ draft deterministic bilingual rules [implemented]
       └─ model request export / prediction import [implemented]
          actual model execution [pending]
  → prediction/quotation checks
  → metrics + paired organization bootstrap + error audit
```

Both classifiers receive the same selected evidence bundle. The rules presently use quotation text only; the model request also carries whitelisted metadata. The study is evaluating classification, not automatic extraction. Machine-suggested passages, if added later, must remain distinguishable from human-reviewed evidence.

## 3. Dataset and actual preliminary progress

| Item | Verified value | Interpretation |
|---|---:|---|
| Source files processed | 54 PDFs | Includes English, French and Arabic materials; per-document language is not yet verified |
| Unique byte hashes | 54 | No exact byte duplicates; not a count of unique policies or deployments |
| Physical pages | 2,104 | Physical PDF pages, not printed page labels |
| Extracted chunks | 3,594 | 1,800-character maximum, 200-character overlap |
| File-level extraction errors | 0 | Does not establish correctness or completeness |
| Documents containing empty extracted pages | 19 | Includes blank, image-only, scanned or otherwise unextractable pages |
| Empty extracted pages | 372 | Needs selective visual review, not automatic exclusion |
| Documents with no meaningful extracted text | 10 | Quality script found fewer than 100 stripped characters; these ten had zero |
| Additional encoding-corruption flags | 2 | Heuristic based on control-character frequency; requires visual review |
| Proposed pilot documents | 20 | Purposive feasibility selection; no eligibility approval yet |
| Reviewed deployment records | 0 | No real curated records file exists |
| Independent reviewer labels / adjudicated gold | 0 | No agreement result exists for research data |
| Real model runs / research comparisons | 0 | No empirical accuracy, macro-F1 or confidence interval to report |
| Automated tests | 13 passing | Synthetic software checks only |

The extraction fingerprint is `23c482b5badc44c2fbcd95f46d86a7e68e0655d70ceedfac13f62c1bdf6e4c78`. It is calculated from serialized extracted chunks. Changing extractor, extraction behavior, text, offsets or chunk settings can change it.

`data/processed/inventory.jsonl` retains source path, title derived from filename, content hash, document ID, page count and extraction status. Issuer, language, source URL, date, geography, document type and translation group remain null until reviewed. Filename-derived titles are not verified bibliographic titles.

The two flagged encoding cases are the electronic-exchange law PDF and `French/Data Protection Law 98.pdf`. Some other problems, such as spaced-out text, do not necessarily trigger this heuristic. The `Al-Khwarizmi Program1.pdf` filename differs from its extracted opening title about an AI hub; review metadata rather than assuming the filename is correct.

This collection includes policy, legislation, institutional announcements, reports, research articles and possible deployment leads. Its eligibility yield is unknown. Exact hashing does not identify translations, syndication, near duplicates, or repeat coverage of the same deployment. Those links remain manual work.

## 4. Locations and portable handoff

Current project root:

```text
/Users/noah/Documents/Codex/2026-10-17/read/outputs/morocco-research
```

Original source folder and downloaded archive:

```text
/Users/noah/Downloads/Morroco
/Users/noah/Downloads/Morroco.zip
```

The spelling `Morroco` is the actual source-folder spelling. Original PDFs have not been modified. They are **not included in the project handoff ZIP**; teammates need access to the shared TA source collection or a separately transferred copy. The handoff ZIP includes extracted text, metadata, code, tests and the generated offline tool. Respect the source folder’s sharing permissions when transferring it.

Extract the ZIP, open a terminal in the extracted `morocco-research` directory, and use relative project commands below. Source paths containing `/Users/noah` are local to Noah’s machine; change the input folder path on another machine. No remote repository, pushed commit, hosted application or cloud deployment was created in this work.

## 5. Code and artifact map

Paths below are relative to the project root above.

| File | Purpose and status |
|---|---|
| `morocco/__init__.py` | Package marker |
| `morocco/ingest.py` | Recursive PDF/TXT/MD ingestion; hashes, extraction, page/chunk preservation and report |
| `morocco/study.py` | Record validation, deterministic organization split, draft bilingual rules, core metrics and draft-run CLI |
| `morocco/experiment.py` | Frozen request export, artifact-integrity verification, imported-prediction validation, reviewer agreement, clustered bootstrap, evaluation and audits |
| `morocco/review.py` | Generates offline HTML evidence-selection tool or prediction-free labeling packets |
| `morocco/pilot.py` | Generates a fixed proposed 20-document selection and heuristic extraction-quality report |
| `tests/test_ingest.py` | Four ingestion tests |
| `tests/test_study.py` | Five study tests |
| `tests/test_experiment.py` | Four experiment/reviewer-packet tests, including synthetic end-to-end evaluation |
| `evidence-review.html` | Generated offline review tool containing extracted corpus text; manual browser verification pending |
| `data/processed/inventory.jsonl` | One inventory row per source file |
| `data/processed/pages.jsonl` | Document hash, physical page, full extracted page text |
| `data/processed/chunks.jsonl` | Chunk ID, document ID, source path, page, character offsets and text |
| `data/processed/report.json` | Actual corpus counts and fingerprint |
| `data/pilot/selection.json` | 20 proposed documents, rationale and pending eligibility status |
| `data/pilot/extraction-quality.json` | Per-document text counts, empty pages, control-character fraction and review flags |
| `README.md`, `workflow.md` | Setup and operation guidance |
| `protocol.md` | Draft annotation definitions and data formats |
| `pilot-plan.md` | Human-readable pilot proposal |
| `corpus-status.md` | Extraction counts and documents with empty pages |
| `.gitignore` | Ignores local environment, caches, raw and processed data, `.env`; does not cover every future annotation/run directory |
| `HANDOFF.md` | This verified handoff |

`data/curated/records.jsonl`, reviewer exports, adjudicated labels, frozen research runs, real model predictions and research results do not yet exist. Any examples below are format examples, not completed records.

## 6. Tools, versions and model status

- Development was performed with Codex assistance in the local Codex desktop environment. Codex is the implementation assistant; it is not automatically the experimental classifier. No reliable development-model identifier has been recorded for this handoff.
- Python standard library supplies the pipeline, HTML generation, tests, splitting and statistics; no ML framework is required for these components.
- Actual corpus ingestion used the bundled **Python 3.12.14** runtime and **pypdf 6.10.0**. The ingestion code tries PyMuPDF first, then falls back to pypdf. PyMuPDF was unavailable during the recorded ingestion. Installing PyMuPDF later can silently change the selected extractor; use a clean pypdf-only environment for reproduction.
- Tests were rerun on **Python 3.14.5**, with **13 tests passing**. Compatibility guidance is Python 3.10+, but not every supported version has been tested.
- The generated page uses plain HTML/CSS/JavaScript and browser file downloads. No backend, hosted storage, authentication, or automatic save is implemented.
- Node.js was used for JavaScript syntax validation. Playwright was used to attempt UI testing; its bundled browser was unavailable and the local Chrome launch failed. This did not complete a browser interaction test.
- The PDF skill informed extraction review. No OCR engine was run and no complete visual PDF audit has been done.
- No E5, FAISS, Streamlit, OpenAI API client, other LLM API, or paid inference run was used in the research pipeline.
- The proposal names “GPT-5.6 Sol.” This is a proposal reference, **not a verified runnable API identifier**. The team must select and verify an available experimental model and record any change explicitly.

## 7. Running the system

### A. Environment and smoke tests

On a teammate’s machine, substitute the actual extracted project path in the first command. A clean environment with pypdf only reproduces the recorded extractor choice.

```sh
cd /Users/noah/Documents/Codex/2026-10-17/read/outputs/morocco-research
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install 'pypdf==6.10.0'
python3 -m unittest discover -s tests -v
```

Expected test summary: `Ran 13 tests` and `OK`. The library is optional for the synthetic tests but required for PDF extraction. A complete dependency lock/package distribution has not been created.

The already available bundled interpreter on Noah’s machine is:

```text
/Users/noah/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3
```

### B. Re-ingest only when needed

Processed data already exists; do not rebuild it merely to open the review tool.

```sh
python3 -m morocco.ingest /Users/noah/Downloads/Morroco --output data/processed
python3 -m morocco.pilot
python3 -m morocco.review --output evidence-review.html
```

Ingestion defaults to `--size 1800 --overlap 200`. Output must be outside the source directory. Symlinked files are skipped. Exact duplicates retain inventory entries but are indexed once. The command returns a nonzero exit status when file-level extraction errors are recorded.

**Re-ingestion overwrites processed outputs.** Preserve a copy before modifying extraction or chunk settings once annotations reference offsets. Curated metadata belongs in a separate directory. `pilot.py` assumes the original filenames and will fail if they are renamed or absent; update its selection list deliberately.

### C. Human evidence selection

Open `evidence-review.html` in a browser; it works without a server. Filter to a document, navigate physical pages, select text, click **Use selected passage**, fill required identifiers/details, and save. Reusing a record ID with identical deployment details adds another evidence passage. Optional fields are source date, source type and language.

Export to JSONL before closing or reloading. The tool does not automatically persist work. Resume with the exported JSONL. Review original PDFs to verify reading order and completeness. The interface shows extracted text, not PDF page images. It currently cannot curate all desired sector/ownership/source-URL metadata or conveniently edit/delete saved records; use reviewed JSON editing until those controls are added.

Create `data/curated` and save reviewed exports as `data/curated/records.jsonl`. Illustrative record structure:

```json
{"record_id":"deployment-001","organization_id":"canonical-org","organization":"Reviewed organization","use_case":"Specific AI use case","moroccan_location":"Reviewed location","sector":null,"partner":null,"organization_origin":null,"ownership":null,"evidence":[{"document_id":"FULL_SOURCE_SHA256","page":1,"start":0,"end":20,"quote":"EXACT EXTRACTED TEXT","source_date":null,"source_type":null,"language":"en"}]}
```

The example is not a valid ready-to-use record. Character offsets must match the actual extracted page text exactly; end is exclusive. Document IDs are full content hashes. Normalize organization aliases before splitting. Existence of required fields and exact quotes is checked; factual correctness, eligibility, dates, schema completeness and canonicalization still require human review.

```sh
python3 -m morocco.study data/curated/records.jsonl --output data/pilot-run
```

This validates evidence and writes draft rule predictions and splits. It overwrites files in its output directory; use the `freeze` workflow for protected experiment snapshots. Do not give prediction files to annotators before independent labeling.

### D. Independent labeling and agreement

```sh
python3 -m morocco.review --records data/curated/records.jsonl --output reviewer-packet.html
```

The packet whitelists evidence/details and omits attached labels and predictions. Give reviewers separate copies; do not share their exports until labeling is complete. Blindness is a procedural requirement, not enforced access control. For test-only labeling, prepare a validated records file containing only the frozen test IDs and generate a packet from it; there is no automatic test-packet CLI.

Reviewers supply an ID, guide version, label and rationale, then export JSONL. Keep each reviewer’s file separate and immutable after collection.

```sh
python3 -m morocco.experiment agreement reviewer-a.jsonl reviewer-b.jsonl
```

Requires the same nonempty ID set, valid labels and no duplicate record IDs. Outputs raw agreement and Cohen’s kappa; kappa is null for the degenerate expected-agreement=1 case. The function does not independently verify reviewer identities, annotation-guide consistency or procedural independence.

Resolve disagreements by discussion or a third reviewer and retain both original annotations. Adjudicated gold is a separate JSONL file with `record_id` and `label`; keep rationale and adjudication provenance too. Do not substitute model output for gold labels.

### E. Freeze the experiment

Finalize the guide, baseline and prompt using development data first. Choose an explicit model and as-of date. Replace placeholder values below before execution.

```sh
python3 -m morocco.experiment freeze data/curated/records.jsonl \
  --output data/experiment-v1 \
  --model VERIFIED_MODEL_ID \
  --as-of-date YYYY-MM-DD
```

The output directory must not exist. Outputs are `inputs.jsonl`, `splits.json`, `config.json`, `rule_predictions.jsonl`, `model_requests.jsonl`, and `manifest.json`. Configuration records the model designation, as-of date, split seed, prompt and rule-source hash. Allowed input fields are whitelisted to avoid label leakage.

The split hashes canonical organization ID with seed `morocco-pilot-1` and uses a default 0.25 threshold for test assignment. This is an expected fraction, not an exact 75/25 partition; it is not stratified. Check class coverage and organization counts before freezing. Related entities sharing effectively duplicate evidence may need a common grouping policy. Do not select seeds after inspecting model test performance.

`freeze` validates the date’s format but does **not** filter evidence after the as-of date or ensure publication dates exist. Resolve temporal inclusion upstream. Neither the rule baseline nor validation implements a complete conflict-resolution policy.

### F. Execute the model externally and import predictions

No model API runner exists. `model_requests.jsonl` is a project-specific request envelope, **not guaranteed to be any provider’s batch API schema**. A teammate must build the adapter or run requests externally with fixed settings. Retain raw responses, actual model ID/version, parameters, prompt version, timestamps, errors, retries and cost information where available in `run_metadata.json` and logs. This metadata is recommended but is not created or enforced by current evaluation code.

Required prediction structure:

```json
{"record_id":"deployment-001","label":"announced","quote":"verbatim substring of supplied evidence","evidence_index":0,"rationale":"Explanation"}
```

`evidence_index` is zero-based within the record’s evidence list. Empty quote plus null index is permitted only for `insufficiently_supported`. Rationale is requested but not currently validated. Import requires every frozen input ID exactly once, including development records even when only test records are scored. Quote matching checks provenance, not whether the quote supports the stage.

### G. Evaluate

```sh
python3 -m morocco.experiment evaluate data/experiment-v1 \
  --predictions model-predictions.jsonl \
  --gold adjudicated-test.jsonl \
  --output data/results-v1
```

Default scoring split is `test`; use `--split development` only for explicitly development diagnostics. Gold IDs must exactly match the selected split. Results output directory must be new.

Outputs:

- `results.json`: metrics for both methods, paired cluster-bootstrap intervals and quotation-check statement.
- `false_operational_audit.jsonl`: every operational prediction whose gold label is non-operational; semantic-review/notes placeholders remain for people.
- `evaluation_provenance.json`: frozen-manifest, prediction-file and gold-file hashes.

The manifest check detects ordinary changes to frozen artifacts but is not cryptographic protection against someone rewriting both files and manifest. Results do not automatically generate publication tables or figures.

## 8. Evaluation implementation and test evidence

Macro-F1 is averaged across all four fixed labels. Undefined per-label precision/recall/F1 are set to zero; absent classes therefore affect the macro average. A synthetic test with only one perfectly predicted class has macro-F1 0.25 by design. Do not confuse that fixture with a research result.

Confusion-matrix rows are gold labels; columns are predictions. Per-class support is reported. False-operational rate is **non-operational gold records predicted operational / all operational predictions**; it is null if the denominator is zero. This is distinct from false-positive rate among all non-operational gold records.

Bootstrap uses 2,000 iterations by default, seed 42, sampling organizations with replacement and retaining their records together. The same sampled clusters are used for both methods and the model-minus-rules macro-F1 difference. Intervals use empirical 2.5th/97.5th percentile positions. Fewer than two organizations produces an unavailable result. Two clusters being accepted does not mean the estimate is reliable; small pilot intervals should be described cautiously.

The current draft baseline (`draft-1`) recognizes a narrow set of English/French stage phrases. It abstains when stage cues conflict or when a recognized stage sentence contains listed negation terms. It does not resolve chronology, semantic scope, all future-tense constructions, or multilingual paraphrases. Develop a reasonable fixed baseline before comparing it with an LLM; do not tune it on test errors.

Tests verified on the handoff date:

1. Chunk offsets and character coverage.
2. Byte duplicates and reproducible ingestion.
3. Page boundaries and empty-page flags (mocked PDF extraction).
4. Prevention of output inside the source directory.
5. English/French future phrases classified as announced in fixtures.
6. Negation and mixed stage cues abstain in fixtures.
7. Same canonical organization stays in the same split.
8. False-operational denominator and missing-prediction rejection.
9. Exact source quotation validation.
10. Freeze-to-evaluate synthetic integration, no label leakage, no overwrite, tamper rejection.
11. Invalid/missing model quotations and abstention validation.
12. Agreement and degenerate-kappa behavior.
13. Reviewer-packet label omission and script-text escaping.

**All 13 passed on the latest rerun.** Tests do not establish real extraction fidelity, labeling quality, model performance, complete UI behavior or complete coverage of edge cases. JavaScript syntax validation passed; browser interaction testing did not complete because the browser failed to launch. Test the selection/export/resume flow manually before live annotation, including accented, Arabic and non-BMP characters if used.

## 9. Outstanding issues and prioritized next steps

### Priority 0: obtain the first trustworthy records

1. Noah confirms the classification scope with the team and checks whether the course requires narrowing three proposed RQs to one or two for Deliverable 3. Keep RQ1 primary; decide whether RQ2/RQ3 remain full questions or supporting analyses.
2. Yuxin and Noah screen five pilot documents and record eligible/excluded/context-only status with reasons. Aim for 5–10 records only if evidence supports them. No forced yield.
3. Xichen manually verifies the offline tool’s selection, offset validation, multiple passages, export and resume. Fix issues before teammates depend on it.
4. Two reviewers independently label the same calibration records without predictions; discuss disagreements and revise guide definitions and date/conflict rules. Calibration records remain development material.
5. Resolve source URLs, dates, document language, issuer, geography and source type for selected evidence. Inspect originals and repair only the extraction failures likely to contribute useful records first.

### Priority 1: establish a reproducible experiment

6. Complete the 20-document pilot and report yield, duplicate frequency, ambiguity, extraction problems and class/organization counts. Reassess the 100-record target.
7. Finalize inclusion rules: evidence of AI versus generic digitization; infrastructure/funding/center eligibility; Moroccan location granularity; dated status changes; insufficient support versus non-eligible context.
8. Choose and verify the experimental model, obtain appropriate access, and implement a logged API adapter if desired. Add a dry-run mode, structured response validation, retry handling, resume behavior and metadata checks before real inference.
9. Improve and freeze rules/prompt on development records. Add meaningful regression cases for observed failure patterns. Extend metadata/schema validation and require dates/as-of enforcement before final freezing.
10. Normalize organizations/related entities, inspect split composition and freeze test evidence and guide. Collect two independent test labels and adjudicate separately from predictions.
11. Run both methods, validate quotations, evaluate and review every false-operational prediction plus a stratified sample of records for semantic support.

### Priority 2: supporting questions and team delivery

12. Define matched English/French queries, dates, budgets, rank/result logs and deduplication policy before collecting RQ2 data. No search logger or coverage-analysis code exists yet.
13. Add RQ3 summaries after sector/source/ownership metadata and labels exist: insufficient-support rates and sector shares/rankings before/after filtering. No such analysis code exists yet.
14. Pin dependencies/extractor and add environment/run provenance. Decide on a shared Git repository and data-sharing location. Do not assume `.gitignore` protects all annotations or results.
15. Add adjudication exports, source links/PDF navigation, more complete metadata fields, edit/delete controls and safe persistence if the annotation tool becomes a team dependency. These are useful improvements, not prerequisites for a carefully managed small JSONL pilot.

## 10. Recommended team allocation

These are proposed assignments. Confirm availability and record actual contributions as work is done.

| Person | Primary responsibility | Immediate output | Shared responsibility |
|---|---|---|---|
| Noah | Research protocol, sponsor relevance, scope decisions, Deliverable 3 integration | Final inclusion/date/conflict rules; agreed RQs; report outline and contribution log | Independent reviewer A; coordinate adjudication and error interpretation |
| Yuxin | Corpus curation, bibliographic metadata, source verification, translations/deduplication | Five-document screening log, exact candidate evidence, verified source metadata | Independent reviewer B; English/French discovery protocol and coverage log |
| Xichen | Pipeline maintenance, UI verification, model adapter, experiment reproducibility and evaluation | Verified annotation flow, runtime setup, logged model runner, reproducible evaluation outputs | Third-reviewer adjudication where needed; keep predictions from reviewers until labels are locked |

Noah and Yuxin should label independently before discussion. Xichen should avoid shaping gold labels from knowledge of model predictions; resolve adjudication before consulting predictions. If team availability changes, swap roles while preserving independent labeling and the separation of gold labels from model development.

Suggested milestones are relative rather than deadline claims: first working session for scope/UI checks and five-document screening; next session for calibration and guide revision; then complete the 20-document feasibility pilot; then freeze and run the initial development experiment. Confirm the actual course deadline before scheduling the full held-out study.

## 11. Deliverable 3: required content and remaining work

The assignment context supplied in the Morocco chat calls for one **4–5-page conference-format PDF**, with title/team, actual team contributions, research question(s), Methods (about 1.5–2 pages), Evaluation Plan (about 1.5–2 pages), Preliminary Results (about 0.5–1 page), references outside the page limit, and a shareable lightning-talk slides link. Use future tense for planned work and past tense for completed work. Verify the current course template, deadline and question-count requirement in Canvas; they have not been checked in this implementation session.

**Methods:** describe the actual classification pipeline, unit of analysis, corpus provenance, eligibility, languages/exclusions, metadata, evidence selection, duplicate/translation linking, canonical organization split, guide/version, independent labels/adjudication, rule precedence, model/prompt/settings and reproducibility. Fill in undecided choices before claiming the method is fully specified. Do not substitute the unimplemented RAG architecture.

**Evaluation Plan:** map RQ1 to macro-F1, per-label scores, confusion matrix, paired organization-cluster intervals, false-operational errors, raw agreement/kappa and semantic quotation review. Specify absent-class and failure handling. For RQ2, describe matched-search collection and planned overlap/unique-yield comparisons only after scope is confirmed. For RQ3, specify weak-evidence and sector-distribution analysis. Do not list statistical tests or effects as completed when they are not implemented or run.

Suggested 3–4 planned visuals: (1) corpus/record eligibility flow and language/source table; (2) rule-versus-model scores with intervals and sample sizes; (3) confusion matrices and false-operational error categories; (4) English/French discovery overlap or sector distributions before/after filtering, depending on retained questions. An architecture figure can support Methods but does not replace the requested evaluation visuals.

**Preliminary Results can already state:** 54 PDFs processed, 2,104 physical pages, 3,594 extracted chunks, zero file-level extraction exceptions, 372 empty extracted pages across 19 PDFs, ten PDFs with no meaningful extracted text, two encoding warnings, a proposed 20-document pilot, and 13 passing synthetic tests. Explain extraction limitations. Chunk counts are not deployment counts and test success is not research accuracy.

**To strengthen Preliminary Results before submission:** complete the calibration exercise and report actual eligible-record yield, excluded/context-only documents, organization/class counts, reviewer disagreements, guide revisions and, if ready, a clearly marked development-only baseline/model run. A small honest empirical pilot is more useful than claiming a finished system.

**Still missing:** reviewed records and verified metadata; actual reviewer agreement/gold labels; model execution and observed scores; audit findings; finalized RQ scope and methods choices; named actual contributions; final report drafting, reference verification, conference formatting, PDF render/QA; lightning-talk slide deck/link. No Deliverable 3 PDF or slides were created in this work.

Safe report wording now:

> We processed 54 supplied PDF files comprising 2,104 physical pages and generated 3,594 page-bounded text chunks. We implemented quotation validation, organization-based splitting, a draft bilingual rule baseline, and evaluation utilities; 13 synthetic software tests passed. Extraction produced no file-level exceptions, but 372 pages had no extracted text and require review. Human deployment annotation and model evaluation have not yet been completed.

Do not report “54 verified deployments,” “a deployed RAG system,” “validated model performance,” “100 records collected,” or a completed user study.

## 12. Full processed-document inventory

The table below is generated from the actual inventory and extracted pages. Folder-derived language hints are deliberately omitted because they have not been verified. “Empty pages” means no stripped extracted text, not necessarily a blank visual page. Every row is processed; `needs_review` flags empty pages and does not capture all other quality problems.

| # | Source-relative filename | Pages | Empty pages | Status / additional flags | Proposed pilot |
|---|---|---:|---:|---|---|
| 1 | 1017-Article Text-3470-1-10-20240709.pdf | 18 | 0 | extracted | Yes |
| 2 | 2007-1-07-129-53-05-echang-elect-donnees-jurid-fr(elec-exchange).pdf | 7 | 0 | extracted; possible font encoding corruption |  |
| 3 | 5.-Resolution-on-Generative-AI-Systems-101023.pdf | 10 | 0 | extracted |  |
| 4 | AI in Education.pdf | 2 | 0 | extracted | Yes |
| 5 | AI in Morocco.pdf | 9 | 0 | extracted | Yes |
| 6 | AI reform.pdf | 2 | 0 | extracted | Yes |
| 7 | AIReadinessAssessmentMorocco_Report_23-03-24.pdf | 13 | 0 | extracted | Yes |
| 8 | AI_for_Africa_by_Africa_EN.pdf | 4 | 0 | extracted |  |
| 9 | AUDA-NEPAD White Paper- Regulation and Responsible Adoption of AI in Africa Towards Achievement of AU Agenda 2063.pdf | 234 | 0 | extracted |  |
| 10 | Africa AI Strategy.pdf | 66 | 0 | extracted |  |
| 11 | Africa Union Data Policy Framework.pdf | 84 | 2 | needs_review |  |
| 12 | African Digital Compact.pdf | 102 | 0 | extracted |  |
| 13 | African-digital-foreign-policy_En.pdf | 204 | 12 | needs_review |  |
| 14 | Al-Khwarizmi Program.pdf | 1 | 0 | extracted | Yes |
| 15 | Al-Khwarizmi Program1.pdf | 2 | 0 | extracted | Yes |
| 16 | Arabic/PlaquetteInstitutionnel_18092024_Ara.pdf | 15 | 15 | needs_review; no meaningful text |  |
| 17 | Arabic/employment.pdf | 4 | 0 | extracted |  |
| 18 | Arabic/health.pdf | 25 | 0 | extracted |  |
| 19 | Arabic/higher ed.pdf | 4 | 0 | extracted |  |
| 20 | Arabic/new model.pdf | 152 | 14 | needs_review |  |
| 21 | Arabic/unesco.pdf | 3 | 3 | needs_review; no meaningful text |  |
| 22 | Artificial intelligence needs assessment survey in Africa - UNESCO Digital Library.pdf | 82 | 82 | needs_review; no meaningful text |  |
| 23 | Category 2 Institues and Centres, Part II_ Designation of the Moroccan International Centre for Artificial Intelligence (Ai Movement) as a centre under the auspices of UNESCO (category 2) - UNESCO Digital Library.pdf | 2 | 2 | needs_review; no meaningful text |  |
| 24 | DigitalMorroco2030.pdf | 15 | 15 | needs_review; no meaningful text | Yes |
| 25 | EHEI-JST_51630-Chouraik+Resent.pdf | 16 | 0 | extracted | Yes |
| 26 | Enseignement-EN.pdf | 6 | 1 | needs_review | Yes |
| 27 | French/Data Protection Law 98.pdf | 12 | 0 | extracted; possible font encoding corruption |  |
| 28 | French/Évaluation des besoins en intelligence artificielle en Afrique - UNESCO Digital Library.pdf | 82 | 82 | needs_review; no meaningful text |  |
| 29 | French/PlaquetteInstitutionnel_18092024_Fra.pdf | 15 | 15 | needs_review; no meaningful text |  |
| 30 | French/Public Policy Development Guide.pdf | 182 | 3 | needs_review |  |
| 31 | French/Right to Privacy.pdf | 4 | 0 | extracted | Yes |
| 32 | French/employment.pdf | 7 | 0 | extracted |  |
| 33 | French/health.pdf | 38 | 0 | extracted | Yes |
| 34 | French/higher education.pdf | 6 | 0 | extracted | Yes |
| 35 | French/new development model.pdf | 170 | 16 | needs_review |  |
| 36 | French/unesco.pdf | 2 | 2 | needs_review; no meaningful text |  |
| 37 | Implementation of the Recommendation on the Ethics of Artificial Intelligence (AI) - UNESCO Digital Library.pdf | 5 | 5 | needs_review; no meaningful text |  |
| 38 | Institut Jazari ROOT.pdf | 1 | 0 | extracted | Yes |
| 39 | Investments.pdf | 9 | 0 | extracted |  |
| 40 | Loi-09-08-Fr.pdf | 29 | 0 | extracted |  |
| 41 | Morocco Moves AI Strategy Into Implementation, Targets MAD 100 Bln in GDP Value by 2030 _ Maroc.ma.pdf | 2 | 0 | extracted | Yes |
| 42 | NVIDIA Datacenters.pdf | 2 | 0 | extracted | Yes |
| 43 | Open Data Governance.pdf | 9 | 0 | extracted |  |
| 44 | Project-Breakdown.pdf | 6 | 0 | extracted |  |
| 45 | Rapport de Synthèse ANG.pdf | 50 | 0 | extracted | Yes |
| 46 | Roadmap.pdf | 1 | 0 | extracted | Yes |
| 47 | Stratégie Nationale de Cybersécurité 2030.pdf | 49 | 18 | needs_review |  |
| 48 | Unlocking the Potential- AI in Sub-Saharan Africa.pdf | 56 | 3 | needs_review |  |
| 49 | ai readiness evaluation.pdf | 65 | 65 | needs_review; no meaningful text | Yes |
| 50 | canva-sante-en.pdf | 36 | 0 | extracted | Yes |
| 51 | employment.pdf | 6 | 0 | extracted |  |
| 52 | loi_05-20_cybersecurite_fr.pdf | 7 | 0 | extracted |  |
| 53 | n2533914.pdf | 3 | 0 | extracted |  |
| 54 | new development model 2035.pdf | 168 | 17 | needs_review |  |

The complete proposed selection and rationales are in `pilot-plan.md`; source hashes and page references are preserved in the JSONL inventory.
