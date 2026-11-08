"""One label-free, source-verified evidence packet for both classifiers."""
from datetime import date
from .study import validate

RECORD_FIELDS = ('record_id', 'organization_id', 'organization', 'use_case',
                 'moroccan_location', 'sector', 'partner', 'organization_origin', 'ownership')
EVIDENCE_FIELDS = ('document_id', 'page', 'start', 'end', 'quote', 'source_date',
                   'source_type', 'source_url', 'language', 'original_verified')


def prepare(records, pages, as_of_date=None, outdated_years=2):
    """Use reviewed context offsets, or the complete preserved page as a fallback.

    Never trust supplied context text or annotation-derived rationale. Metadata must
    be curated before annotation. Missing dates stay unknown, not invented.
    """
    validate(records, pages)
    lookup = {(p['document_id'], p['page']): p['text'] for p in pages}
    cutoff = date.fromisoformat(as_of_date) if as_of_date else None
    if type(outdated_years) is not int or outdated_years < 1:
        raise ValueError('outdated_years must be a positive integer')
    clean = []
    for record in records:
        row = {k: record[k] for k in RECORD_FIELDS if k in record}
        row.update(as_of_date=as_of_date, outdated_years=outdated_years, evidence=[])
        for item in record['evidence']:
            page = lookup[item['document_id'], item['page']]
            start, end = item.get('context_start', 0), item.get('context_end', len(page))
            if (type(start) is not int or type(end) is not int or
                    not 0 <= start <= item['start'] < item['end'] <= end <= len(page)):
                raise ValueError('Context must contain the exact quotation: ' + record['record_id'])
            source_date = item.get('source_date')
            if source_date:
                published = date.fromisoformat(source_date)
                if cutoff and published > cutoff:
                    raise ValueError('Source after evidence cutoff: ' + record['record_id'])
            evidence = {k: item.get(k) for k in EVIDENCE_FIELDS}
            evidence.update(context=page[start:end], context_start=start, context_end=end,
                            context_scope='reviewed_passage' if 'context_start' in item or 'context_end' in item else 'full_source_page')
            row['evidence'].append(evidence)
        clean.append(row)
    return clean
