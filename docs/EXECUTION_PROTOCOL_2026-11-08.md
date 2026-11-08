# Execution protocol and source audit — evidence cutoff 2026-11-08

This execution cohort contains **five assistant-screened records: one development record and four test records**. The user delegated the remaining study-design and inclusion decisions to the assistant. This authorizes preparing predictions; it does **not** constitute independent human verification of the records or supply human reference labels. All five remain pending human field verification. No classifications, model outputs, or performance results are reported in this document.

The date in this document's name is the evidence cutoff, not a claim that every retrieval or execution occurred that day. Preserve actual retrieval timestamps separately. The design snapshot was written before supplementary selection; it is not a preregistration of earlier development work.

## Scope and selection

The unit is a named organization, a specific AI application or recognition task, and an identifiable Moroccan site or national scope. The target evidence window is **2020-01-01 through 2026-11-08**, using English or French sources. Preserve the distinction between verified publication dates, dates stated in report content, reporting periods, event dates, and file metadata. This cohort does not have a verified publication date for every source: Crédit du Maroc is retained on the basis of a dated management-report section, with its publication chronology still requiring human verification. Its frozen `source_date` is `null`; the visible section date remains in the shared evidence context. Missing publication dates are not imputed. The configured two-year evidence-age rule is separate from the target window and does not turn an unknown publication date into a known one.

The following do not establish an eligible application on their own:

- General strategies, institutes, research centers, funding, training, or compute infrastructure.
- A general model release without a named applied system or intended user.
- Ordinary digital services without an explicit AI or recognition component.
- Student prototypes without a named institutional or external application.
- Alleged entities or applications that cannot be supported by a source after bounded tracing.

An institutional agreement describing a specific application can meet the scope requirement; inclusion does not establish its deployment status. Uncertainty about that status is not itself an exclusion. Duplicate URLs, translations, syndicated copies, aliases, and repeated descriptions are linked to the same application where appropriate. Neither desired class balance nor model output determined inclusion.

## Original corpus and supplementary search

The user-supplied corpus contained **54 PDFs and 2,104 pages**. Screening used available extracted text, broad AI/application terms, organization searches, and targeted passage reads. **373 pages had no extracted text; no OCR was performed, and those pages were not substantively screened.** Other pages were not all read line by line. Some documents had missing publication metadata or unreliable column reading order. Consequently, this exercise cannot establish exhaustive recall or the absence of additional applications in the supplied files.

The supplementary search used the following fixed queries, with the first five returned links screened for each query: **8 queries × 5 result positions = 40 positions**, including duplicates. This is not a count of 40 unique sources or applications.

| Theme | English query | French query |
| --- | --- | --- |
| Banking/insurance | `Morocco bank insurance artificial intelligence deployed official` | `Maroc banque assurance intelligence artificielle déployée officiel` |
| Industry | `Morocco industry manufacturing artificial intelligence deployment official` | `Maroc industrie fabrication intelligence artificielle déploiement officiel` |
| Agriculture/health | `Morocco agriculture health artificial intelligence deployed official` | `Maroc agriculture santé intelligence artificielle déployée officiel` |
| Administration/transport | `Morocco government transport artificial intelligence application official` | `Maroc administration transport intelligence artificielle application officiel` |

Searches used `system1_search_query`. The stopping rule was to screen the first five positions in each query's displayed result order, retain at most one primary/original-reporting follow-up evidence item per secondary result, include all verifiable eligible applications within that bound, and deduplicate by organization, task, and site. Follow-up queries and failures are logged separately. Search attempts to locate that one evidence item are not additional unrestricted discovery queries.

The French queries were initially submitted together, then repeated verbatim individually because merged output did not identify each query's result order. A French Bank Al-Maghrib trace query was also repeated after truncated output. These repetitions are disclosed; no alternative discovery terms were substituted. Result ordering is the displayed sequence, including PDF entries, rather than the numerical suffix of a search reference. Search rankings can change, so preserved ledgers define this execution's boundary.

## Retained cohort and evidence

| Split | Organization/application | Source date and source | Scope and material limit |
| --- | --- | --- | --- |
| Development | MTNRA — Idarati AI administrative assistance | [Official national portal, English, 2026-09-09](https://www.maroc.ma/en/news/morocco-moves-ai-strategy-implementation-targets-mad-100-bln-gdp-value-2030) | Moroccan national services. This English source supplies the frozen classifier evidence. The undated [AI marketplace](https://ai.mmsp.gov.ma/) was consulted during source screening but is **not model input**. Portal service counts do not measure AI use. |
| Test | Ministry of Health and Social Protection / DeepEcho — prenatal ultrasound | [Official national portal carrying MAP reporting, 2026-05-06](https://maroc.ma/fr/actualites/gitex-future-health-africa-morocco-signature-de-conventions-visant-renforcer-la-digitalisation-et) | Public primary-care establishments and local hospitals in Morocco. The source describes an agreement and intended clinical evaluation; individual facilities and device name are unspecified. Its FDA statement is a source claim, not independently verified here. |
| Test | NARSA / UM6P — Smart Drive Test | [Le360 report credited to MAP, 2025-10-28](https://fr.le360.ma/societe/permis-de-conduire-presentation-du-modele-de-la-voiture-intelligente-smart-drive-test_C4AHSL7XKJDFPK5HL5E75PIQI4/) | Moroccan driving examinations; presentation in Rabat. Traffic-sign/light recognition and assessment are described. The original MAP wire URL was not recovered: this is one syndicated reporting item, not an operator self-report or independent corroboration. |
| Test | Pôle Digital — satellite crop mapping | [Organization project page, 2026-09-02](https://poledigital.ma/dispositif-digitalde-gestion-de-ladata-agricole/) | Explicit machine learning/deep learning, named Moroccan use sites, dashboard and QgisCropMapper workflow. Counted once across sites and interfaces. Site-associated years are not assumed rollout dates. Publication is from HTML `datePublished`; `dateModified` is 2026-09-04. |
| Test | Crédit du Maroc — AI bancassurance sales/customer journeys | [Annual financial report covering 2024](https://www.creditdumaroc.ma/sites/default/files/Rapport_financier_annuel_2024_.pdf), physical PDF page 47; publication date unknown | Moroccan bank branch network; individual branches are unspecified. The section header says **MARS 2025**, which dates management-report content and does **not** verify the publication month or day. Frozen `source_date` remains `null`, while the section header is preserved in shared context. PDF creation/modification metadata is 2025-04-30, also not a publication date. Do not substitute 2024-01-01, 2025-03-01, or 2025-04-30. |

Idarati belongs to a previously examined organization and is development-only. Other previously examined calibration families were ONDA, Mistral AI, and CIMR; none supplies a test record here. The four newly retained organizations form the test partition, with aliases and partner roles preserved. This organization-based assignment is neither random sampling nor label balancing.

The English-query branch contributed DeepEcho and NARSA, but their retained evidence is French. Pôle Digital and Crédit du Maroc also have French evidence. Thus **all four test records use French sources**. English search terms are not English evaluation examples, and the search design does not support a bilingual-performance or language-coverage claim.

## Exclusions and source preservation

The screening ledgers retain per-result reasons, including generic JAZARI/AI-factory infrastructure, financial regulation and strategy pages, ordinary digital identity or appointment services, general conference summaries without named operators, and unverified bank-scoring claims. Known leads with unresolved application scope, unavailable source originals, outdated evidence, or explicit scope-specific withdrawal were not silently converted into current deployment records. These decisions do not prove that an application does not exist elsewhere.

Preserved evidence includes source URLs, source type/language, original HTML/PDF bytes, extracted text, hashes, and quote/context locations. Full surrounding paragraphs retain temporal and limiting language. Crédit du Maroc uses native PDF text order to avoid interleaving its two columns; supporting pages identify the bank and network. Exact substring/hash checks establish traceability, not truth, semantic sufficiency, or independent human review. The provenance bundle contains the design snapshot, original-corpus coverage audit, known-lead decisions, EN/FR search and screening ledgers, follow-up logs, and candidate-source files.

## Fair comparison and permitted conclusions

Rules and the LLM must receive the **same frozen, label-free evidence packet**, including the same context and source metadata. Comparing quote-only rules with an LLM given surrounding paragraphs and additional metadata is not the matched-information experiment. Retain packet hashes, source snapshots, split assignments, prompt, model/settings, rule/code versions, failures, and actual run timestamps. Keep assistant inclusion rationales and human labels outside classifier inputs.

There must be **no semantic prompt or rule tuning using the selected test records**. Preserve the primary run's original outputs and failure logs. A necessary technical repair, such as fixing request or response-format handling, must be identified and versioned separately, retain the primary failure record, and disclose any rerun; it must not silently alter evidence, decision criteria, or the primary result. This protocol does not assert that a repair or rerun occurred. Any semantic change motivated by test inspection constitutes further development and cannot preserve the same claim of an untouched test evaluation.

The present cohort is a small, bounded convenience sample. It is not representative of Moroccan AI adoption, a coverage census, or a validated bilingual benchmark. Assistant selection and French interpretation have not received independent qualified human review. A completed prediction run alone does not resolve these limitations.

Before research scoring, Noah and Yuxin must independently verify the record fields and label the held-out evidence while blind to predictions. Retain both original annotations; compute raw agreement and Cohen's kappa before adjudication, and preserve adjudicated reference labels separately. Only then report the prespecified fixed four-class macro-F1, confusion matrices, and false-operational numerator/denominator. Any estimates from four test records are descriptive and highly unstable; no superiority or general performance claim is warranted from this cohort alone.
