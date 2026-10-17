# Morocco Diplomacy Lab — Project 11

Evidence-grounded classification of publicly documented AI deployments in Morocco. Compare a fixed bilingual rule baseline and an LLM against independently reviewed labels: **operational**, **pilot**, **announced**, and **insufficiently_supported**.

This is a research scaffold, not a completed benchmark or RAG chatbot. The local TA collection has been ingested, but human annotation and real model evaluation remain pending. Thirteen synthetic tests pass locally; An inactive GitHub Actions template is included in `ci/github-actions-tests.yml`; GitHub CI has not run.

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
