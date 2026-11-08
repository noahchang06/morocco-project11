"""Validated human evidence bundles and a development-only bilingual baseline."""
import argparse
import hashlib
import json
import re
from datetime import date
from pathlib import Path

LABELS = ('operational', 'pilot', 'announced', 'insufficiently_supported')
RULE_VERSION = 'draft-4-shared-context-wraps'
CUES = {
    'operational': r'\b(in daily use|in ongoing use|currently uses|currently operates|in production|en production|utilise actuellement|en service)\b',
    'pilot': r'\b(pilot|piloting|trial|testing|pilote|expérimentation|en test)\b',
    'announced': r'\b(plans to|will deploy|will launch|intend(?:s|ed)? to|planned|launched|unveiled|prévoit|prévu|prévue|sera déployé|sera déployée|projet de|lancement|a annoncé)\b',
}
NEGATION = r"\b(not|never|no longer|pas|jamais|aucun|aucune|sans)\b"
FUTURE = r'\b(will|plans? to|planned|intended to|prévoit|prévu|prévue|sera|va déployer)\b'


def read_jsonl(path):
    return [json.loads(line) for line in Path(path).read_text(encoding='utf-8').splitlines() if line.strip()]


def validate(records, pages):
    lookup = {(p['document_id'], p['page']): p['text'] for p in pages}
    ids = set()
    for record in records:
        for field in ('record_id', 'organization_id', 'organization', 'use_case', 'moroccan_location', 'evidence'):
            if not record.get(field):
                raise ValueError(f'Missing {field}')
        if record['record_id'] in ids:
            raise ValueError('Duplicate record_id')
        ids.add(record['record_id'])
        for item in record['evidence']:
            text = lookup.get((item['document_id'], item['page']))
            start, end = item['start'], item['end']
            if text is None or not isinstance(start, int) or not isinstance(end, int) or not 0 <= start < end <= len(text):
                raise ValueError('Invalid evidence location')
            if not item['quote'].strip() or text[start:end] != item['quote']:
                raise ValueError('Quotation does not match preserved page text')


def split(records, seed='morocco-pilot-1', test_fraction=.25):
    """Stable organization grouping; normalize aliases before use. No class balancing."""
    if not 0 < test_fraction < 1:
        raise ValueError('test_fraction must be between 0 and 1')
    return {r['record_id']: ('test' if int(hashlib.sha256((seed + ':' + r['organization_id']).encode()).hexdigest(), 16) / 2**256 < test_fraction else 'development') for r in records}


def baseline(record):
    matches = []
    negated = False
    evidence = record['evidence']
    if record.get('as_of_date'):
        cutoff = date.fromisoformat(record['as_of_date'])
        year = cutoff.year - record.get('outdated_years', 2)
        try:
            threshold = cutoff.replace(year=year)
        except ValueError:  # leap day
            threshold = cutoff.replace(year=year, day=28)
        dates = [date.fromisoformat(e['source_date']) for e in evidence if e.get('source_date')]
        if len(dates) == len(evidence) and max(dates) < threshold:
            return {'record_id': record['record_id'], 'label': 'insufficiently_supported',
                    'quote': '', 'evidence_index': None, 'reason_code': 'outdated',
                    'rule_version': RULE_VERSION, 'reason': 'all supplied sources predate the frozen recency threshold'}
    for index, item in enumerate(evidence):
        for sentence in re.split(r'(?<=[.!?])\s+', item.get('context', item['quote'])):
            # PDF line wraps are not sentence boundaries. Match normalized spaces
            # while retaining the exact source substring for the returned quote.
            match_text = re.sub(r'\s+', ' ', sentence)
            found = [label for label, pattern in CUES.items() if re.search(pattern, match_text, re.I)]
            if found and re.search(NEGATION, match_text, re.I):
                negated = True
                continue
            if found and re.search(FUTURE, match_text, re.I):
                found = ['announced']
            matches.extend((label, sentence, index) for label in found)
    labels = {label for label, _, _ in matches}
    # Conservative abstention on mixed temporal stages; this draft does not resolve chronology.
    label = next(iter(labels)) if len(labels) == 1 and not negated else 'insufficiently_supported'
    quote, index = next(((text, index) for stage, text, index in matches if stage == label), ('', None))
    return {'record_id': record['record_id'], 'label': label, 'quote': quote,
            'evidence_index': index, 'reason_code': 'ambiguous' if label == 'insufficiently_supported' else None,
            'rule_version': RULE_VERSION, 'reason': 'unique unnegated cue' if quote else 'absent, negated, or conflicting cues'}


def metrics(gold, predictions):
    if not gold or set(gold) != set(predictions):
        raise ValueError('Require nonempty gold and exactly matching prediction IDs')
    if any(label not in LABELS for label in [*gold.values(), *predictions.values()]):
        raise ValueError('Unknown label')
    matrix = [[0] * 4 for _ in LABELS]
    for key, actual in gold.items():
        matrix[LABELS.index(actual)][LABELS.index(predictions[key])] += 1
    scores = {}
    for i, label in enumerate(LABELS):
        tp = matrix[i][i]
        actual = sum(matrix[i])
        predicted = sum(row[i] for row in matrix)
        scores[label] = {'precision': tp / predicted if predicted else 0,
                         'recall': tp / actual if actual else 0,
                         'f1': 2 * tp / (actual + predicted) if actual + predicted else 0,
                         'support': actual}
    op_count = sum(row[0] for row in matrix)
    false_op = op_count - matrix[0][0]
    return {'n': len(gold), 'macro_f1': sum(s['f1'] for s in scores.values()) / 4,
            'per_label': scores, 'labels': LABELS, 'confusion_matrix': matrix,
            'false_operational_numerator': false_op, 'operational_prediction_denominator': op_count,
            'false_operational_rate': false_op / op_count if op_count else None}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('records')
    parser.add_argument('--pages', default='data/processed/pages.jsonl')
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    records = read_jsonl(args.records)
    validate(records, read_jsonl(args.pages))
    output = Path(args.output)
    output.mkdir(parents=True, exist_ok=True)
    (output / 'splits.json').write_text(json.dumps(split(records), indent=2), encoding='utf-8')
    (output / 'rule_predictions.jsonl').write_text(''.join(json.dumps(baseline(r), ensure_ascii=False) + '\n' for r in records), encoding='utf-8')
    print(f'Validated {len(records)} records; wrote draft predictions and organization splits.')


if __name__ == '__main__':
    main()
