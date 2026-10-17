"""Validated human evidence bundles and a development-only bilingual baseline."""
import argparse
import hashlib
import json
import re
from pathlib import Path

LABELS = ('operational', 'pilot', 'announced', 'insufficiently_supported')
RULE_VERSION = 'draft-1'
CUES = {
    'operational': r'\b(in daily use|in ongoing use|currently uses|currently operates|in production|en production|utilise actuellement|en service)\b',
    'pilot': r'\b(pilot|piloting|trial|testing|pilote|expérimentation|en test)\b',
    'announced': r'\b(plans to|will deploy|will launch|intends to|planned|prévoit|prévu|prévue|sera déployé|sera déployée|projet de)\b',
}
NEGATION = r"\b(not|never|no longer|pas|jamais|aucun|aucune|sans)\b"


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
    for item in record['evidence']:
        for sentence in re.split(r'(?<=[.!?])\s+|\n+', item['quote']):
            found = [label for label, pattern in CUES.items() if re.search(pattern, sentence, re.I)]
            if found and re.search(NEGATION, sentence, re.I):
                negated = True
                continue
            matches.extend((label, sentence) for label in found)
    labels = {label for label, _ in matches}
    # Conservative abstention on mixed temporal stages; this draft does not resolve chronology.
    label = next(iter(labels)) if len(labels) == 1 and not negated else 'insufficiently_supported'
    quote = next((text for stage, text in matches if stage == label), '')
    return {'record_id': record['record_id'], 'label': label, 'quote': quote,
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
