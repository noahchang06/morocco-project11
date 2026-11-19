import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from morocco.complete_batch import complete
from morocco.experiment import freeze
from morocco.run_model import run
from morocco.study import read_jsonl


class CompleteBatchTests(unittest.TestCase):
    def fixture(self, folder):
        text = 'The AI system is in production.'
        records = [dict(record_id=f'r{i}', organization_id=f'org{i}',
                        organization=f'Example {i}', use_case='AI task',
                        moroccan_location='Rabat', evidence=[dict(
                            document_id='doc', page=1, start=0, end=len(text),
                            quote=text, source_date='2026-10-01')]) for i in range(4)]
        pages = [dict(document_id='doc', page=1, text=text)]
        frozen, output = folder/'frozen', folder/'api'
        freeze(records, pages, frozen, 'fixture-model', '2026-11-08',
               split_map={r['record_id']: 'test' for r in records},
               model_settings={'temperature': 0, 'max_output_tokens': 1500})
        return frozen, output

    def response(self, body):
        record = json.loads(body['input'])
        prediction = dict(record_id=record['record_id'], label='operational',
                          quote=record['evidence'][0]['quote'], evidence_index=0,
                          reason_code=None, rationale='Synthetic test only.')
        return dict(status='completed', model=body['model'], id='fixture-response',
                    output=[dict(type='message', content=[dict(
                        type='output_text', text=json.dumps(prediction))])])

    def first_incomplete(self, frozen, output):
        calls = []
        def transport(body):
            calls.append(json.loads(body['input'])['record_id'])
            return dict(status='incomplete', model=body['model'], output=[],
                        incomplete_details={'reason': 'max_output_tokens'})
        with self.assertRaisesRegex(ValueError, 'incomplete'):
            run(frozen, output, 'test', transport=transport)
        self.assertEqual(calls, ['r0'])
        raw = output/'raw'/(hashlib.sha256(b'r0').hexdigest()+'.json')
        return raw, raw.read_bytes()

    def test_cached_failure_is_not_resampled_and_other_records_complete(self):
        with tempfile.TemporaryDirectory() as temp:
            frozen, output = self.fixture(Path(temp))
            raw, original = self.first_incomplete(frozen, output)
            calls = []
            def transport(body):
                calls.append(json.loads(body['input'])['record_id'])
                return self.response(body)
            complete(frozen, output, 'test', transport=transport)
            self.assertEqual(calls, ['r1', 'r2', 'r3'])
            self.assertEqual(raw.read_bytes(), original)
            accepted = read_jsonl(output/'accepted_predictions.jsonl')
            failures = read_jsonl(output/'failures.jsonl')
            self.assertEqual([r['record_id'] for r in accepted], ['r1', 'r2', 'r3'])
            self.assertEqual([r['record_id'] for r in failures], ['r0'])
            self.assertEqual(failures[0]['response_status'], 'incomplete')
            self.assertNotIn('label', failures[0])
            self.assertFalse((output/'predictions.jsonl').exists())
            self.assertFalse((output/'.running').exists())
            identity = json.loads((output/'identity.json').read_text())
            metadata = json.loads((output/'batch_metadata.json').read_text())
            for key, value in identity.items():
                self.assertEqual(metadata[key], value)
            self.assertIn('wrapper_sha256', metadata)
            complete(frozen, output, 'test', transport=transport)
            self.assertEqual(calls, ['r1', 'r2', 'r3'])
            self.assertEqual(raw.read_bytes(), original)
            self.assertEqual(read_jsonl(output/'accepted_predictions.jsonl'), accepted)
            self.assertEqual(read_jsonl(output/'failures.jsonl'), failures)

    def test_all_valid_cached_records_need_no_calls_and_have_full_predictions(self):
        with tempfile.TemporaryDirectory() as temp:
            frozen, output = self.fixture(Path(temp))
            run(frozen, output, 'test', transport=self.response)
            original = (output/'predictions.jsonl').read_bytes()
            def forbidden_transport(body):
                self.fail('A cached valid response must not be requested again')
            complete(frozen, output, 'test', transport=forbidden_transport)
            self.assertEqual((output/'predictions.jsonl').read_bytes(), original)
            self.assertEqual(read_jsonl(output/'accepted_predictions.jsonl'), read_jsonl(output/'predictions.jsonl'))
            self.assertEqual(read_jsonl(output/'failures.jsonl'), [])

    def test_manifest_and_runner_identity_tampering_stop_before_transport(self):
        for tamper in ('manifest', 'runner_identity'):
            with self.subTest(tamper=tamper), tempfile.TemporaryDirectory() as temp:
                frozen, output = self.fixture(Path(temp))
                self.first_incomplete(frozen, output)
                if tamper == 'manifest':
                    with (frozen/'inputs.jsonl').open('a') as handle:
                        handle.write('\n')
                else:
                    path = output/'identity.json'
                    identity = json.loads(path.read_text())
                    identity['runner_sha256'] = 'wrong-original-runner'
                    path.write_text(json.dumps(identity))
                def forbidden_transport(body):
                    self.fail('Invalid provenance must stop before any new request')
                with self.assertRaises(ValueError):
                    complete(frozen, output, 'test', transport=forbidden_transport)
                self.assertFalse((output/'accepted_predictions.jsonl').exists())

    def test_transport_failure_is_sanitized_checkpointed_and_not_a_stage(self):
        with tempfile.TemporaryDirectory() as temp:
            frozen, output = self.fixture(Path(temp))
            self.first_incomplete(frozen, output)
            calls = []
            def transport(body):
                key = json.loads(body['input'])['record_id']
                calls.append(key)
                if key == 'r1':
                    raise RuntimeError('SYNTHETIC_SECRET_MUST_NOT_BE_EXPORTED')
                return self.response(body)
            complete(frozen, output, 'test', transport=transport)
            failures = read_jsonl(output/'failures.jsonl')
            self.assertEqual({r['record_id'] for r in failures}, {'r0', 'r1'})
            self.assertTrue(all('label' not in row for row in failures))
            self.assertEqual({r['record_id'] for r in read_jsonl(output/'accepted_predictions.jsonl')}, {'r2', 'r3'})
            self.assertFalse((output/'predictions.jsonl').exists())
            checkpoint = output/'raw'/(hashlib.sha256(b'r1').hexdigest()+'.json')
            self.assertTrue(checkpoint.exists())
            self.assertIsNone(json.loads(checkpoint.read_text())['response'])
            for path in output.rglob('*.json*'):
                self.assertNotIn('SYNTHETIC_SECRET_MUST_NOT_BE_EXPORTED', path.read_text())
            complete(frozen, output, 'test', transport=transport)
            self.assertEqual(calls, ['r1', 'r2', 'r3'])
            self.assertFalse((output/'.running').exists())


if __name__ == '__main__':
    unittest.main()
