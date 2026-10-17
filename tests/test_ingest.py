import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from morocco.ingest import chunks, ingest


class IngestionTests(unittest.TestCase):
    def test_offsets_and_coverage(self):
        text = 'Policy المغرب stratégie ' * 30
        spans = list(chunks(text, 80, 10))
        self.assertEqual(spans[-1][1], len(text))
        for start, end, value in spans:
            self.assertEqual(value, text[start:end])
        self.assertEqual(set(range(len(text))), {i for start, end, _ in spans for i in range(start, end)})

    def test_duplicates_and_reproducibility(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / 'raw'
            source.mkdir()
            for name in ['a.txt', 'copy.txt']:
                (source / name).write_text('Synthetic test evidence.', encoding='utf-8')
            report = ingest(source, root / 'out')
            self.assertEqual(report['duplicates'], 1)
            self.assertEqual(report['unique_documents'], 1)
            self.assertEqual(report, ingest(source, root / 'out'))

    def test_pages_never_cross_and_empty_pages_flagged(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / 'raw'
            source.mkdir()
            (source / 'test.pdf').write_bytes(b'synthetic fixture')
            with patch('morocco.ingest.read_pages', return_value=['Page one.', '', 'Page three.']):
                report = ingest(source, root / 'out')
            self.assertEqual(report['needs_review'], 1)
            rows = [json.loads(line) for line in (root / 'out/chunks.jsonl').read_text().splitlines()]
            self.assertEqual([r['page'] for r in rows], [1, 3])

    def test_output_cannot_contaminate_source(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(ValueError):
                ingest(directory, Path(directory) / 'generated')


if __name__ == '__main__':
    unittest.main()
