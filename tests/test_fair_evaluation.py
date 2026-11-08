import json
from pathlib import Path
import tempfile
import unittest

from morocco.evidence import prepare
from morocco.experiment import check_predictions, evaluate, freeze, write_jsonl
from morocco.run_model import run
from morocco.study import baseline


class FairEvaluationTests(unittest.TestCase):
    def fixture(self):
        text = 'The AI tool was launched. It is now in production.'
        quote = 'The AI tool was launched.'
        records = [dict(record_id='r1', organization_id='org1', organization='Example',
                        use_case='AI task', moroccan_location='Rabat', label='LEAK',
                        evidence=[dict(document_id='doc', page=1, start=0, end=len(quote),
                                       quote=quote, source_date='2026-10-01',
                                       source_url='https://example.org/report',
                                       rationale='LEAK', context='FORGED CONTEXT')])]
        return records, [dict(document_id='doc', page=1, text=text)]

    def test_context_is_source_derived_and_annotations_are_removed(self):
        records, pages = self.fixture()
        clean = prepare(records, pages, '2026-11-08')
        encoded = json.dumps(clean)
        self.assertNotIn('LEAK', encoded)
        self.assertNotIn('FORGED', encoded)
        self.assertEqual(clean[0]['evidence'][0]['context'], pages[0]['text'])
        self.assertIn('https://example.org/report', encoded)
        # A model may cite the supporting context outside the initial short quote.
        check_predictions(clean, [dict(record_id='r1', label='operational',
                                      quote='It is now in production.', evidence_index=0)])
        # Rules really scan context too: mixed cues abstain instead of quote-only announced.
        self.assertEqual(baseline(clean[0])['label'], 'insufficiently_supported')

    def test_bad_context_and_future_source_rejected(self):
        records, pages = self.fixture()
        records[0]['evidence'][0]['context_start'] = 3
        with self.assertRaises(ValueError):
            prepare(records, pages, '2026-11-08')
        records[0]['evidence'][0].pop('context_start')
        with self.assertRaises(ValueError):
            prepare(records, pages, '2025-01-01')

    def test_metadata_affects_rules_and_planned_trial_not_pilot(self):
        record = {'record_id': 'a', 'as_of_date': '2026-11-08', 'outdated_years': 2,
                  'evidence': [{'quote': 'The tool is in production.', 'source_date': '2023-01-01'}]}
        self.assertEqual(baseline(record)['reason_code'], 'outdated')
        record['evidence'][0]['source_date'] = '2024-11-08'
        self.assertEqual(baseline(record)['label'], 'operational')
        for text in ['The agency plans to start a pilot.', 'A trial will begin next year.',
                     'Une expérimentation est prévue en 2027.']:
            self.assertEqual(baseline({'record_id': 'a', 'evidence': [{'quote': text}]})['label'], 'announced')

    def test_pdf_wraps_preserve_negation_and_exact_quotation(self):
        for text in ['The system is not\nin production.', 'Le système ne fonctionne pas\nen service.']:
            self.assertEqual(baseline({'record_id': 'a', 'evidence': [{'quote': text}]})['label'], 'insufficiently_supported')
        text = 'The assistant is intended\nto guide users.'
        result = baseline({'record_id': 'a', 'evidence': [{'quote': text}]})
        self.assertEqual(result['label'], 'announced')
        self.assertEqual(result['quote'], text)

    def test_calibration_and_organization_split_guards(self):
        records, pages = self.fixture()
        with tempfile.TemporaryDirectory() as temp:
            p = Path(temp)
            with self.assertRaises(ValueError):
                freeze(records, pages, p/'bad', 'fixture-model', '2026-11-08',
                       split_map={'r1': 'test'}, calibration_ids=['r1'])
            records.append({**records[0], 'record_id': 'r2'})
            with self.assertRaises(ValueError):
                freeze(records, pages, p/'bad2', 'fixture-model', '2026-11-08',
                       split_map={'r1': 'development', 'r2': 'test'})

    def fake_transport(self, body):
        record = json.loads(body['input'])
        pred = dict(record_id=record['record_id'], label='operational',
                    quote='It is now in production.', evidence_index=0,
                    reason_code=None, rationale='Synthetic fixture only.')
        return {'status': 'completed', 'model': body['model'], 'id': 'fixture-response',
                'output': [{'type': 'message', 'content': [
                    {'type': 'output_text', 'text': json.dumps(pred)}]}]}

    def test_pending_candidates_are_development_only_and_cannot_be_scored(self):
        records, pages = self.fixture()
        records[0]['human_inclusion_confirmed'] = False
        with tempfile.TemporaryDirectory() as temp:
            p = Path(temp)
            with self.assertRaisesRegex(ValueError, 'Unconfirmed candidate'):
                freeze(records, pages, p/'study', 'fixture-model', '2026-11-08')
            with self.assertRaisesRegex(ValueError, 'cannot contain held-out'):
                freeze(records, pages, p/'bad', 'fixture-model', '2026-11-08',
                       split_map={'r1': 'test'}, purpose='development_smoke_test')
            freeze(records, pages, p/'smoke', 'fixture-model', '2026-11-08',
                   split_map={'r1': 'development'}, purpose='development_smoke_test',
                   model_settings={'temperature': 0, 'max_output_tokens': 1500})
            config = json.loads((p/'smoke'/'config.json').read_text())
            self.assertEqual(config['model_settings']['temperature'], 0)
            self.assertNotIn('Eligibility has already been screened.', config['prompt'])
            with self.assertRaisesRegex(ValueError, 'cannot produce research'):
                evaluate(p/'smoke', p/'unused-predictions', p/'unused-gold', p/'scores', subset='development')

    def test_runner_resume_subset_evaluation_and_config_guard(self):
        records, pages = self.fixture()
        records.append({**records[0], 'record_id': 'r2', 'organization_id': 'org2'})
        with tempfile.TemporaryDirectory() as temp:
            p = Path(temp)
            freeze(records, pages, p/'frozen', 'fixture-model', '2026-11-08',
                   split_map={'r1': 'test', 'r2': 'development'})
            self.assertEqual(run(p/'frozen', p/'api', 'test', True)['records'], 1)
            self.assertFalse((p/'api').exists())
            calls = []
            def transport(body):
                calls.append(body)
                return self.fake_transport(body)
            run(p/'frozen', p/'api', 'test', transport=transport)
            run(p/'frozen', p/'api', 'test', transport=transport)
            self.assertEqual(len(calls), 1)
            self.assertEqual(json.loads(calls[0]['input']),
                             json.loads((p/'frozen'/'inputs.jsonl').read_text().splitlines()[0]))
            write_jsonl(p/'gold.jsonl', [{'record_id': 'r1', 'label': 'operational'}])
            result = evaluate(p/'frozen', p/'api'/'predictions.jsonl', p/'gold.jsonl', p/'results', iterations=100)
            self.assertEqual(result['metrics']['model']['macro_f1'], .25)
            self.assertTrue((p/'results'/'report.md').is_file())
            with self.assertRaises(ValueError):
                run(p/'frozen', p/'api', 'development', transport=transport)

    def test_invalid_response_is_retained_not_silently_resampled(self):
        records, pages = self.fixture()
        with tempfile.TemporaryDirectory() as temp:
            p = Path(temp)
            freeze(records, pages, p/'frozen', 'fixture-model', '2026-11-08', split_map={'r1': 'development'})
            calls = []
            def transport(body):
                calls.append(body)
                response = self.fake_transport(body)
                response['status'] = 'incomplete'
                return response
            for _ in range(2):
                with self.assertRaises(ValueError):
                    run(p/'frozen', p/'api', transport=transport)
            self.assertEqual(len(calls), 1)
            self.assertFalse((p/'api'/'predictions.jsonl').exists())
            self.assertEqual(len(list((p/'api'/'raw').glob('*.json'))), 1)


if __name__ == '__main__':
    unittest.main()
