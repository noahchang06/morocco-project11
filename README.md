# Morocco Diplomacy Lab — Project 11

Evidence-grounded classification of publicly documented AI deployments in Morocco. Compare a fixed bilingual rule baseline and an LLM against independently reviewed labels: **operational**, **pilot**, **announced**, and **insufficiently_supported**.

This is a research scaffold, not a completed benchmark or RAG chatbot. The local TA collection has been ingested, but human annotation and real model evaluation remain pending. Fourteen automated tests pass locally. An inactive GitHub Actions template is included in `ci/github-actions-tests.yml`; GitHub CI has not run.

## How this can be useful in Morocco

The intended practical output is an evidence-backed database and analysis that the U.S. Consulate General Casablanca and relevant Moroccan stakeholders could use to investigate AI activity and identify organizations worth contacting. For example, a user investigating logistics could filter records by sector, see the organization and AI use case, distinguish operational systems from pilots or announcements, and inspect dated quotations and source links.

The database supports due diligence and follow-up questions; a public announcement is not independent verification of a working deployment. Each record should retain organization, use case, Moroccan location, sector, partners, maturity label, evidence date and provenance. Missing records must not be interpreted as proof that an organization does not use AI.

For this semester, the feasible output is a small reviewed dataset, an evaluation of classification reliability, and a sponsor-facing analysis. A shared table/export is sufficient initially; a searchable dashboard is a later option, not implemented. A maintained national resource would additionally require broader collection, Arabic-language review, local stakeholder validation, an update schedule and a designated owner. None of those deployment or stakeholder-validation steps has been completed.

The first step toward practical use is to ask the Consulate which decisions the records should support and which fields it needs. Stakeholder feedback is planned; no usefulness findings or user study results exist yet. Keep the academic classification experiment separate from any future public application.

## First team review: English-language sources

The team speaks English and Mandarin. Start with **English passages the reviewers can assess directly**. Mandarin can support internal discussion, but retain English source quotations and their original offsets in the study records. Do not translate quotations in place.

The following six files total **29 physical PDF pages**. Their extracted text was checked for English content; this is not a complete visual, bibliographic or eligibility audit. The filenames below are relative to the TA's shared `Morroco` folder, not files committed to this repository. Dates and substantive claims in these PDFs must be read as historical source claims, not automatically as current facts.

| Suggested screening owner | Exact corpus filename | Pages | What to review and return |
|---|---|---:|---|
| Noah | `Morocco Moves AI Strategy Into Implementation, Targets MAD 100 Bln in GDP Value by 2030 _ Maroc.ma.pdf` | 2 | Identify specific named systems/use cases separately from national targets. Preserve wording about demonstrations, intended functions and proofs of concept; do not assign a final stage during screening. |
| Noah | `Al-Khwarizmi Program1.pdf` | 2 | Check the extracted AI-hub article against the PDF and correct its metadata. Separate infrastructure investment/agreements from a specific deployed AI application; note date inconsistencies if encountered. This filename does not match its extracted article title. |
| Yuxin | `AIReadinessAssessmentMorocco_Report_23-03-24.pdf` | 13 | Build the initial organization/source-reference list and verify bibliographic dates. Treat this as historical readiness context and a source of leads, not a current deployment census. |
| Xichen | `AI in Morocco.pdf` | 9 | Find concrete organization/use-case leads and their cited original sources; distinguish the paper's proposed framework and broad ecosystem discussion from deployment evidence. |
| Xichen | `AI in Education.pdf` | 2 | Identify whether the passage names a specific AI application or only a roadmap, agreement, training activity or institution. Flag page-extraction navigation/sidebar contamination. |
| Xichen | `Institut Jazari ROOT.pdf` | 1 | Exercise the inclusion boundary: founding an institution alone does not establish an eligible AI application. Record either an eligible claim with evidence or a reasoned context-only decision. |

**Shared calibration:** everyone reads the two short files assigned to Noah first (four pages total). Discuss eligibility and record structure, not model predictions. After the team agrees on the evidence bundles and guide, Noah and Yuxin independently label the same calibration records without seeing one another's labels. Screening ownership above is not a substitute for independent annotation.

**Optional second round:** `Rapport de Synthèse ANG.pdf` (50 pages) contains English report text despite its French filename. Begin with the executive summary and sectoral perspectives, using actual PDF pages to record evidence. `Enseignement-EN.pdf` (6 pages) is another English context source. These are secondary priorities; do not require the team to read the entire corpus before starting calibration.

**Defer for now:** French-only material such as `NVIDIA Datacenters.pdf` and `Al-Khwarizmi Program.pdf`, Arabic documents, and PDFs without meaningful extracted text such as `DigitalMorroco2030.pdf` and `ai readiness evaluation.pdf`. Filename language is not sufficient to establish document language. Request a qualified French/Arabic reviewer or a verified English version where needed. Machine translation can help discovery, but do not describe translated-only judgments as independently verified original-language gold labels. Preserve original and translated text separately and record translation provenance if a translation-assisted method is adopted.

This is an **English-first calibration round**, not a silent replacement of the original bilingual proposal or its 20-document pilot. The matched English/French research question remains pending: either secure suitable language review and run the original collection protocol, or explicitly revise/defer that question with course guidance. Existing English/French rule code is not evidence that the team has validated French classification.

### What each reviewer should produce

Keep screening notes in the team's shared data location, outside Git. For each document, record:

- Filename, verified title, issuer, original URL, publication date, language, and physical pages reviewed; use “unknown” instead of guessing.
- Eligibility decision: candidate deployment evidence, context only, duplicate/translation, or extraction problem; include a short reason.
- For each candidate: canonical organization, specific AI use case, Moroccan location, exact quotation, physical page and surrounding context. Use the review tool to capture exact offsets; manually validate against the PDF.
- Any conflicting dates/status claims, uncertain identity, missing metadata or original-source follow-up needed.

Do not force every document to produce a deployment. “No eligible record” is a valid screening result. Do not force an ambiguous non-deployment document into the `insufficiently_supported` class. For a source with an eligible but weakly supported claim, that class may be appropriate during annotation.

## After the review: specific implementation sequence

Assignments below are recommendations to confirm as a team, not completed contributions. The first calibration round is development data. Do not report it as a held-out test.

| Step | Owner and collaborators | Specific action | Output / completion check |
|---|---|---|---|
| 1. Consolidate screening | Yuxin; Noah checks eligibility | Merge the six screening logs, resolve source identity and metadata, link repeated/translated coverage, and list missing original sources. | One screening log with decisions for all six documents and a verified candidate list. No forced record count. |
| 2. Finalize calibration guide | Noah; all discuss | Define eligible AI applications, infrastructure/center exclusions, location granularity, publication window, as-of date, negation and conflicting-status rules. Decide how English-first work affects RQ2. | Versioned guide and a decision log. Undefined rules resolved before final test annotation. |
| 3. Verify annotation tooling | Xichen; Yuxin tries the workflow | Xichen completed a macOS/Chrome walkthrough on 2026-10-17: one Idarati record, two passages, validation, export/resume and byte-identical re-export passed. Source URL/sector/ownership fields and saved-record editing controls were then added with regression coverage. Do not add autosave without deciding storage/privacy behavior. | Xichen's walkthrough and automated tests pass. Yuxin should independently try the revised controls before live annotation. |
| 4. Create canonical records | Yuxin; Xichen validates | Export selected evidence, normalize organization IDs, link sources to deployment records, and keep context/excluded documents out of the classifier inputs. | Validated `data/curated/records.jsonl`; no quote mismatches, duplicate IDs or unresolved organization aliases. |
| 5. Independently annotate | Noah and Yuxin; Xichen adjudicates after independent completion | Generate prediction-free packets; label the same calibration evidence separately, calculate agreement, discuss disagreements and preserve original labels. Adjudicate before consulting predictions. | Two reviewer exports, an agreement summary and adjudicated development labels. Revise the guide if calibration exposes ambiguities. |
| 6. Complete pilot and assess yield | Yuxin leads collection; Noah reviews scope | Expand beyond the first six toward the proposed 20-document feasibility pilot using reviewable languages. Record yield, class counts, organization counts, duplicates and extraction failures; revise the proposed selection transparently if needed. | Pilot feasibility report; decision on further collection and whether the original 100-record target is attainable. |
| 7. Improve the baseline | Xichen; Noah checks rules against guide | Tune bilingual or explicitly English-only rules on development examples only. Address observed temporal/negation failures; add meaningful regression tests and version the rules. | Frozen development-tested baseline. Do not use final test errors to tune it. |
| 8. Add real model execution | Xichen; Noah approves experimental model/configuration | Verify an actual model ID and access; implement an adapter for the exported request format, fixed settings, raw-response logs, schema/quote checks, retries and resumable runs. Enforce model/settings metadata and the date policy. | A logged development dry run and validated prediction JSONL. API execution and configuration enforcement are not implemented yet. |
| 9. Freeze final study inputs | Noah owns protocol; Yuxin owns records; Xichen packages | Finalize guide, prompt, rules and dates; normalize related organizations; inspect organization-disjoint split sizes and class coverage. Exclude calibration organizations from the final test. Current hash splitting does not automatically enforce that exclusion, so extend it with an explicit split manifest and leakage checks before final freezing. | Frozen inputs/configuration and manifest, with nonempty usable splits and a documented calibration/test separation. |
| 10. Label and evaluate held-out records | Noah and Yuxin label; Xichen runs evaluation | Obtain independent test labels and adjudication, then run both methods on identical frozen evidence and evaluate. Inspect every false-operational error and manually assess quotation support. | Metrics, paired organization-bootstrap intervals, disagreement/error audit and provenance. No real results exist yet. |
| 11. Finish supporting analyses | Yuxin and Noah; Xichen implements analysis | If retained, implement prospective matched-language search logs and RQ2 overlap/unique-yield analysis with qualified review. Add RQ3 sector/source summaries after metadata and gold labels exist. | Clearly separated completed and planned analyses; no retrospective claim that the TA folder was a matched search experiment. |
| 12. Deliver research and sponsor outputs | Noah integrates; Yuxin verifies sources; Xichen supplies technical evidence | Prepare a reviewed table/export, document limitations and update needs, and write Deliverable 3 with actual counts, contribution records and pilot findings. Produce the required slides/link and report PDF. | Reproducible handoff, sponsor-facing evidence table and course submission. Dashboard and local stakeholder validation remain later work. |

The immediate goal is to learn whether we can create and consistently label a small set of defensible deployment records. We can start screening, metadata cleanup and UI verification now; model access is not required for those tasks.

## Setup

From the cloned repository directory:

```sh
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
python3 -m unittest discover -s tests -v
```

Python 3.12 is the recommended ingestion environment. The recorded extractor is pypdf 6.10.0. Do not install PyMuPDF in the reproduction environment: the current ingestion code preferentially uses it when available, changing extracted text and offsets.

## Obtain and prepare data

Ask the team for the TA's shared document collection. PDFs, extracted text, annotation files, generated review pages and experiment results are intentionally excluded from Git. The generated HTML embeds source text and must not be committed.

Set the input path to your downloaded folder:

```sh
python3 -m morocco.ingest /absolute/path/to/Morroco --output data/processed
python3 -m morocco.pilot
python3 -m morocco.review --output evidence-review.html
```

The pilot generator expects the original collection's filenames. Open the generated HTML locally to select exact evidence and export records. It has no automatic save; export before closing. Browser interaction verification is still pending. Keep annotations and run files under the ignored `data/` directory.

Do not rebuild processed text once annotations reference its offsets without preserving the previous version and revalidating quotations.

## Study workflow

1. Screen source documents and verify organization, AI use case, Moroccan location, dates and provenance.
2. Save human-reviewed evidence records to `data/curated/records.jsonl`.
3. Generate separate reviewer packets; collect independent labels and adjudicate disagreements.
4. Refine rules and prompt using development data. Freeze inputs and organization-disjoint splits.
5. Execute an explicitly chosen model externally, import predictions and evaluate against gold labels.

The model integration exports requests and imports validated predictions; it does not call a paid API. There is no embedding index, semantic retrieval or RAG application.

## Documentation

- [Complete team handoff](HANDOFF.md): inventory, code map, schemas, commands, evaluation definitions, proposed responsibilities and Deliverable 3 checklist. This dated snapshot includes Noah's historical local paths; substitute your clone/source paths.
- [Operating workflow](workflow.md): detailed research steps and commands.
- [Annotation protocol](protocol.md): draft definitions and record format.
- [Pilot selection](pilot-plan.md): proposed 20-document feasibility sample.
- [Corpus status](corpus-status.md): recorded ingestion counts and empty-page review list.

## Collaboration

Use a feature branch and pull request for changes. Run the tests before opening a PR. Never use model predictions as gold labels or tune the baseline on held-out errors. Keep reviewer exports separate until independent labeling is complete.

No open-source license has been assigned; the team should decide licensing before public distribution. Source documents retain their original rights and sharing conditions.

## Enable GitHub CI

The current GitHub OAuth login lacks the `workflow` scope, so the test workflow is stored as an inactive template. With suitable GitHub permissions, move `ci/github-actions-tests.yml` to `.github/workflows/tests.yml` and commit it to run tests on pushes and pull requests. Local tests do not require GitHub Actions.
