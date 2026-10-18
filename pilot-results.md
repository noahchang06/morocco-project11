# Pilot feasibility result (provisional)

Date: 2026-10-18
Scope: English-first feasibility screen of the proposed 20-document pilot

## Reproducible corpus result

Using the recorded `pypdf==6.10.0` extractor, Xichen's complete-folder run produced:

- 54 files and 54 unique documents
- 2,104 physical PDF pages
- 3,594 extracted chunks
- zero exact file duplicates and zero file-level extraction exceptions
- 19 documents requiring extraction review
- corpus fingerprint `23c482b5badc44c2fbcd95f46d86a7e68e0655d70ceedfac13f62c1bdf6e4c78`

The 20-document manifest generated successfully. This is a purposive feasibility pilot, not a representative sample.

## Review status and provenance

The first five documents were manually screened by Xichen using the offline evidence tool. The remaining documents received an assistant-assisted provisional screen of the extracted text. The table below is a triage log, not an independent second review, adjudication, or group agreement. French-language decisions remain deferred unless an English counterpart made the document's role clear. Image-only PDFs remain unresolved until OCR or visual review.

| Status | Documents | Count |
|---|---|---:|
| Candidate deployment record | `Morocco Moves AI Strategy Into Implementation...pdf` | 1 |
| Context only / source lead | See table below | 11 |
| Deferred for qualified French review | See table below | 5 |
| Extraction/OCR blocker | `DigitalMorroco2030.pdf`; `ai readiness evaluation.pdf` | 2 |
| Probable duplicate/alternate export with poor extraction | `AI reform.pdf` | 1 |

## Document decisions

| Document | Provisional screening decision | Reason |
|---|---|---|
| `NVIDIA Datacenters.pdf` | Defer language review; infrastructure lead | French reporting describes announced AI-compute infrastructure. Infrastructure capacity alone is not a task-specific AI application. |
| `Al-Khwarizmi Program1.pdf` | Context only | AI hub/infrastructure reporting; no task-specific application with deployment evidence. |
| `Institut Jazari ROOT.pdf` | Context only | Institution creation does not establish an eligible AI application. |
| `AI in Education.pdf` | Context only | Education roadmap/agreement material; no specific deployed application. |
| `AI in Morocco.pdf` | Context only / original-source leads | Broad ecosystem and academic discussion; claims require verification against cited primary sources. |
| `AIReadinessAssessmentMorocco_Report_23-03-24.pdf` | Context only / original-source leads | Page 4 mentions biometric systems authorized for authentication and proof of life; page 6 describes a launched digital-ID platform. The report does not establish both a canonical operating organization and task-specific AI use, so neither is yet a defensible record. |
| `EHEI-JST_51630-Chouraik+Resent.pdf` | Context only | Academic paper makes broad sector-level deployment claims without a named operating organization. |
| `1017-Article Text-3470-1-10-20240709.pdf` | Context only / original-source leads | Pages 2–3 mention license-plate recognition, traffic management, satellite agriculture and airport facial recognition, but do not identify a canonical operator for a record. |
| `Al-Khwarizmi Program.pdf` | Defer language review; program context | French funding-program results describe selected research projects, not demonstrated operational applications. |
| `Morocco Moves AI Strategy Into Implementation, Targets MAD 100 Bln in GDP Value by 2030 _ Maroc.ma.pdf` | Candidate | Supports `calibration-idarati-001`. Idarati AI was presented with intended functions but no evidence of live use, trial or coverage; development label `announced`. Operator identity remains a limitation. |
| `Roadmap.pdf` | Context only | Describes programs, factories and an unnamed sovereign solutions platform, but does not identify a specific application/operator pair or live status. |
| `Rapport de Synthèse ANG.pdf` | Context only | Page 34 records agreements; pages 44–45 contain recommendations. These are commitments and proposed uses, not evidence of a specific deployed application. |
| `AI reform.pdf` | Probable duplicate / extraction problem | Appears to be an alternate export of the `Roadmap.pdf` article with characters split by spaces; it adds no independent evidence. |
| `DigitalMorroco2030.pdf` | Extraction/OCR blocker | All 15 pages produced no meaningful text. No substantive eligibility judgment was made. |
| `ai readiness evaluation.pdf` | Extraction/OCR blocker | All 65 pages produced no meaningful text. No substantive eligibility judgment was made. |
| `French/Right to Privacy.pdf` | Defer language review; legal context | French biometric/data-protection decision, not direct evidence of a specific deployment. |
| `canva-sante-en.pdf` | Context only | Health and social-protection reform report; no specific task-level AI application identified. |
| `French/health.pdf` | Defer language review / translation counterpart | French counterpart to the health-policy material; preserve for matched-language work. |
| `Enseignement-EN.pdf` | Context only | Higher-education transformation plan and institution-building; no specific deployed AI application. |
| `French/higher education.pdf` | Defer language review / translation counterpart | French counterpart to the higher-education plan; preserve for matched-language work. |

## Candidate record and development result

The pilot currently contains one defensible candidate, `calibration-idarati-001`. Xichen's provisional human label is `announced`. After adding the observed development cue `intended to`, rule baseline `draft-2` also predicts `announced`. This is development calibration, not held-out accuracy.

## Feasibility conclusion

The current folder has low eligible-record yield: one candidate from the 20-document pilot, with two image-only sources and five sources still requiring qualified French review. One record cannot support meaningful macro-F1, agreement, confidence intervals, or a held-out model comparison. The correct next step is targeted primary-source collection for the unresolved leads, followed by canonical organization resolution and another screening round. Do not force policy, infrastructure, institutions, generic sector claims or recommendations into classifier inputs merely to increase the record count.

Priority follow-ups are:

1. Find the original CNDP or social-security source for authentication/proof-of-life use and identify the operating institution.
2. Find primary sources naming operators for license-plate recognition, traffic management, agricultural satellite analysis and airport facial recognition.
3. Resolve the operator and actual availability of the unnamed sovereign AI-solutions platform.
4. OCR the two image-only PDFs only if their likely evidentiary value justifies the work.

Until those steps produce additional records, report this as a completed feasibility pilot with insufficient yield for the proposed classification benchmark, not as a completed accuracy experiment.

<!-- four-record-smoke-test:start -->
## Four-record end-to-end pipeline check — October 18, 2026

The expanded local corpus contains 57 source files, 2,248
physical pages, and 3,812 extracted chunks. Ingestion reported
0 file-level errors and 20 documents requiring
extraction review.

Four evidence-linked calibration records now pass exact page, offset, and quotation
validation. Their provisional labels are:

- Operational: 1
- Pilot: 0
- Announced: 3
- Insufficiently supported: 0

The added cases cover ONDA's operational facial-recognition system at Casablanca
Airport and two announced MTNRA/Mistral models. The earlier Idarati case remains
classified as announced.

A complete freeze, prediction-import, manifest-integrity, quotation-validation, and
evaluation smoke test succeeded. The deterministic split placed 2 records in
the test subset. Fixed four-class macro-F1 was 0.00 for the draft rules
and 0.25 for the pipeline-check predictions.

These values are not research performance estimates. The pipeline-check predictions
were constructed from the assumed labels solely to validate the software path, the
test subset contains only the announced class, and the assumed-consensus labels do
not constitute independently collected reviewer agreement. Cluster bootstrap status:
`unavailable: fewer than two organization clusters`.

All imported prediction quotations passed exact-substring validation. Semantic
support and final eligibility remain human-review responsibilities.
<!-- four-record-smoke-test:end -->
