import json
import tempfile
import unittest
import unicodedata
from pathlib import Path

from morocco.pilot import SELECTION, build


def write_jsonl(path, rows):
    path.write_text(''.join(json.dumps(row) + '\n' for row in rows), encoding='utf-8')


class PilotTests(unittest.TestCase):
    def test_custom_paths_and_unicode_normalization(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            processed, output = root / 'processed', root / 'pilot'
            processed.mkdir()
            rows, pages = [], []
            for index, (name, _, _) in enumerate(SELECTION):
                stored_name = unicodedata.normalize('NFC', name)
                document_id = f'doc-{index}'
                rows.append({'path': stored_name, 'document_id': document_id,
                             'empty_pages': []})
                pages.append({'document_id': document_id, 'page': 1,
                              'text': 'Meaningful extracted source text. ' * 4})
            write_jsonl(processed / 'inventory.jsonl', rows)
            write_jsonl(processed / 'pages.jsonl', pages)

            selected, quality = build(processed, output, root / 'plan.md')

            self.assertEqual(len(selected), 20)
            self.assertEqual(len(quality), 20)
            self.assertTrue((output / 'selection.json').exists())
            self.assertIn('Rapport de Synthèse ANG.pdf', (root / 'plan.md').read_text())

    def test_missing_sources_are_reported(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write_jsonl(root / 'inventory.jsonl', [])
            write_jsonl(root / 'pages.jsonl', [])
            with self.assertRaisesRegex(ValueError, 'Pilot source files missing'):
                build(root, root / 'pilot', root / 'plan.md')


if __name__ == '__main__':
    unittest.main()
