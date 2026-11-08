import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from morocco.ocr_backfill import backfill


class OcrBackfillTests(unittest.TestCase):
    def test_separate_discovery_output_resume_and_changed_settings_guard(self):
        try:
            import fitz
        except ImportError:
            self.skipTest('Optional PyMuPDF ingestion dependency is unavailable')
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            canonical, sources, models = [root / s for s in ('canonical', 'sources', 'models')]
            for directory in (canonical, sources / 'English', sources / 'Arabic', models):
                directory.mkdir(parents=True)
            pdf = fitz.open()
            pdf.new_page().insert_text((50, 50), 'Synthetic test document')
            pdf.save(sources / 'English/source.pdf')
            pdf.save(sources / 'Arabic/source.pdf')
            pdf.close()
            inventory = [{'document_id': 'en', 'path': 'English/source.pdf'},
                         {'document_id': 'ar', 'path': 'Arabic/source.pdf'}]
            pages = [{'document_id': 'en', 'page': 1, 'text': ''},
                     {'document_id': 'ar', 'page': 1, 'text': ''}]
            for name, rows in [('inventory', inventory), ('pages', pages)]:
                (canonical / (name + '.jsonl')).write_text(''.join(json.dumps(r) + '\n' for r in rows))
            original = (canonical / 'pages.jsonl').read_bytes()
            (models / 'eng.traineddata').write_bytes(b'synthetic-model')

            def recognize(command, **kwargs):
                target = Path(command[2])
                target.with_suffix('.txt').write_text('Recovered synthetic words')
                target.with_suffix('.tsv').write_text('conf\ttext\n95\tRecovered\n90\tsynthetic\n')

            with patch('morocco.ocr_backfill.subprocess.check_output', return_value='synthetic OCR\n'), \
                    patch('morocco.ocr_backfill.subprocess.run', side_effect=recognize) as recognize_call:
                summary = backfill(canonical, sources, root / 'result', models, workers=1)
                self.assertEqual(summary['attempted'], 1)
                self.assertEqual(summary['text_recovered'], 1)
                self.assertEqual(len(summary['out_of_scope_pages']), 1)
                self.assertEqual((canonical / 'pages.jsonl').read_bytes(), original)
                backfill(canonical, sources, root / 'result', models, workers=1)
                self.assertEqual(recognize_call.call_count, 1)
                with self.assertRaisesRegex(ValueError, 'settings changed'):
                    backfill(canonical, sources, root / 'result', models, workers=1, dpi=201)


if __name__ == '__main__':
    unittest.main()
