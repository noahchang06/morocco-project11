import json
from pathlib import Path
import tempfile
import unittest

from morocco.evaluation import failure_metrics
from morocco.experiment import evaluate, freeze, write_jsonl
from morocco.study import LABELS, metrics


class ResponseFailureEvaluationTests(unittest.TestCase):
    def test_failure_lowers_recall_without_becoming_a_stage(self):
        gold = {'a': 'operational', 'b': 'operational', 'c': 'pilot', 'd': 'announced'}
        predictions = {'a': 'operational', 'b': None, 'c': 'pilot', 'd': 'announced'}
        score = failure_metrics(gold, predictions)
        self.assertEqual(score['n'], 4)
        self.assertEqual(score['labels'], LABELS)
        self.assertEqual(score['per_label']['operational']['support'], 2)
        self.assertEqual(score['per_label']['operational']['recall'], .5)
        self.assertAlmostEqual(score['macro_f1'], 2 / 3)
        self.assertEqual(score['confusion_matrix'][0], [1, 0, 0, 0, 1])
        self.assertEqual(score['output_coverage'], .75)
        self.assertEqual(score['false_operational_rate'], 0)
        # Silently omitting the failure would produce an inflated result.
        dropped = metrics({k: v for k, v in gold.items() if k != 'b'},
                          {k: v for k, v in predictions.items() if k != 'b'})
        self.assertGreater(dropped['macro_f1'], score['macro_f1'])

    def test_all_failures_and_success_only_equivalence(self):
        gold = {'a': 'operational', 'b': 'pilot'}
        failed = failure_metrics(gold, {'a': None, 'b': None})
        self.assertEqual(failed['macro_f1'], 0)
        self.assertEqual(failed['output_coverage'], 0)
        self.assertIsNone(failed['false_operational_rate'])
        original = metrics(gold, gold)
        score = failure_metrics(gold, gold)
        for key, value in original.items():
            self.assertEqual(score[key], value)
        with self.assertRaises(ValueError):
            failure_metrics({'a': None}, {'a': None})

    def test_complete_failure_accounting_and_reporting(self):
        quote = 'The AI system is in production.'
        records = [dict(record_id=k, organization_id=k, organization='Synthetic fixture',
                        use_case='Synthetic task', moroccan_location='Rabat',
                        human_inclusion_confirmed=True,
                        evidence=[dict(document_id='fixture', page=1, start=0,
                                       end=len(quote), quote=quote, source_date='2026-01-01')])
                   for k in 'abcd']
        pages = [dict(document_id='fixture', page=1, text=quote)]
        gold = dict(a='operational', b='operational', c='pilot', d='announced')
        accepted = [dict(record_id=k, label=gold[k], quote=quote, evidence_index=0)
                    for k in 'acd']
        failures = [dict(record_id='b', failure_type='response_validation',
                         failure_reason='Synthetic truncated response', response_status='incomplete')]
        with tempfile.TemporaryDirectory() as temp:
            p = Path(temp)
            freeze(records, pages, p/'frozen', 'synthetic', '2026-11-08',
                   split_map={k: 'test' for k in gold})
            write_jsonl(p/'pred.jsonl', accepted)
            write_jsonl(p/'fail.jsonl', failures)
            write_jsonl(p/'gold.jsonl', [dict(record_id=k, label=v) for k, v in gold.items()])
            result = evaluate(p/'frozen', p/'pred.jsonl', p/'gold.jsonl', p/'out',
                              iterations=100, failures_path=p/'fail.jsonl')
            self.assertAlmostEqual(result['metrics']['model']['macro_f1'], 2 / 3)
            self.assertEqual(result['metrics']['rules']['n'], 4)
            self.assertIn('invalid_output', (p/'out/report.md').read_text())
            self.assertEqual(result['bootstrap']['clusters'], 4)
            self.assertIsNotNone(json.loads((p/'out/evaluation_provenance.json').read_text())['failures_sha256'])
            with self.assertRaisesRegex(ValueError, 'exactly match'):
                evaluate(p/'frozen', p/'pred.jsonl', p/'gold.jsonl', p/'missing', iterations=100)
            for invalid in [[], failures + [dict(failures[0], record_id='a')],
                            [dict(failures[0], record_id='outside')], failures * 2,
                            [dict(failures[0], failure_reason='')]]:
                write_jsonl(p/'fail.jsonl', invalid)
                with self.assertRaises(ValueError):
                    evaluate(p/'frozen', p/'pred.jsonl', p/'gold.jsonl', p/'bad',
                             iterations=100, failures_path=p/'fail.jsonl')
            # A failure manifest never grants permission to score unreviewed data.
            pending = [dict(r, human_inclusion_confirmed=False,
                            record_status='eligible_assistant_screened', eligibility_decision='include',
                            eligibility_rationale='Synthetic source review') for r in records]
            freeze(pending, pages, p/'pending', 'synthetic', '2026-11-08',
                   split_map={k: 'test' for k in gold}, purpose='prediction_pending_human_review')
            with self.assertRaisesRegex(ValueError, 'pending human field review'):
                evaluate(p/'pending', p/'pred.jsonl', p/'gold.jsonl', p/'blocked',
                         failures_path=p/'fail.jsonl')


if __name__ == '__main__':
    unittest.main()
