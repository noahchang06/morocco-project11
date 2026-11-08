"""OCR only empty canonical pages into a separate, resumable discovery dataset."""
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import csv
import hashlib
import io
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unicodedata


def backfill(canonical, sources, output, tessdata, workers=4, dpi=200):
    import fitz
    canonical, sources, output = map(Path, (canonical, sources, output))
    output.mkdir(parents=True, exist_ok=True)
    cache = output / 'page-cache'; cache.mkdir(exist_ok=True)
    inventory = [json.loads(x) for x in (canonical/'inventory.jsonl').read_text().splitlines()]
    inventory = {r['document_id']: r for r in inventory if 'document_id' in r}
    filemap = {unicodedata.normalize('NFC', str(f.relative_to(sources))): f for f in sources.rglob('*.pdf')}
    pages = [json.loads(x) for x in (canonical/'pages.jsonl').read_text().splitlines()]
    empty = [r for r in pages if not r['text'].strip()]
    jobs, skipped = [], []
    for page in empty:
        doc = inventory[page['document_id']]
        if doc['path'].startswith('Arabic/'):
            skipped.append(dict(document_id=page['document_id'], page=page['page'], source_path=doc['path'], reason='Arabic-language folder outside the EN/FR discovery scope'))
            continue
        jobs.append((page, doc, filemap[unicodedata.normalize('NFC', doc['path'])]))
    language = 'eng+fra' if (Path(tessdata)/'fra.traineddata').exists() else 'eng'
    version = subprocess.check_output(['tesseract', '--version'], text=True).splitlines()[0]
    models = {f.name: hashlib.sha256(f.read_bytes()).hexdigest() for f in Path(tessdata).glob('*.traineddata')}
    identity = {'dpi': dpi, 'languages': language, 'engine': version, 'models': models,
                'canonical_pages_sha256': hashlib.sha256((canonical/'pages.jsonl').read_bytes()).hexdigest(),
                'implementation_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    identity_hash = hashlib.sha256(json.dumps(identity, sort_keys=True).encode()).hexdigest()
    def one(job):
        page, doc, source = job
        dest = cache / f"{page['document_id']}-{page['page']:04}.json"
        if dest.exists():
            saved = json.loads(dest.read_text())
            if saved.get('identity_sha256') != identity_hash:
                raise ValueError('OCR settings changed; use a new output directory')
            return saved
        result = dict(document_id=page['document_id'], page=page['page'], source_path=doc['path'],
                      identity_sha256=identity_hash, extraction='tesseract_ocr', original_verified=False)
        try:
            with fitz.open(source) as pdf:
                pix = pdf[page['page']-1].get_pixmap(dpi=dpi, colorspace=fitz.csRGB)
                png = pix.tobytes('png')
            result['render_sha256'] = hashlib.sha256(png).hexdigest()
            with tempfile.TemporaryDirectory() as tmp:
                image = Path(tmp)/'page.png'; image.write_bytes(png)
                target = Path(tmp)/'ocr'
                subprocess.run(['tesseract', str(image), str(target), '--tessdata-dir', str(Path(tessdata).resolve()),
                                '-l', language, '--psm', '3', '-c', 'tessedit_create_txt=1', '-c', 'tessedit_create_tsv=1'],
                               check=True, timeout=60, capture_output=True,
                               env={**os.environ, 'OMP_THREAD_LIMIT': '1'})
                result['text'] = target.with_suffix('.txt').read_text()
                rows = list(csv.DictReader(io.StringIO(target.with_suffix('.tsv').read_text()), delimiter='\t'))
                conf = [float(r['conf']) for r in rows if r.get('text','').strip() and float(r['conf']) >= 0]
                result['mean_word_confidence'] = sum(conf)/len(conf) if conf else None
                result['word_count'] = len(conf)
                result['status'] = 'text_recovered' if result['text'].strip() else 'no_text_recovered'
        except (subprocess.SubprocessError, OSError, RuntimeError) as exc:
            result.update(status='ocr_error', error_type=type(exc).__name__, text='')
        dest.write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n')
        return result
    result = []
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = [pool.submit(one, job) for job in jobs]
        for f in as_completed(futures):
            result.append(f.result())
            if len(result) % 25 == 0: print(f'OCR checkpoint {len(result)}/{len(jobs)}', flush=True)
    result.sort(key=lambda r: (r['source_path'], r['page']))
    (output/'pages.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in result))
    summary = {**identity, 'original_empty_pages': len(empty), 'attempted': len(result),
               'text_recovered': sum(r['status']=='text_recovered' for r in result),
               'still_without_text': sum(r['status']=='no_text_recovered' for r in result),
               'errors': sum(r['status']=='ocr_error' for r in result), 'out_of_scope_pages': skipped,
               'warning': 'OCR is discovery text, not visually verified evidence. Canonical text and frozen inputs are untouched.'}
    (output/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({k:v for k,v in summary.items() if k not in ('out_of_scope_pages','models')},ensure_ascii=False),flush=True)
    return summary


if __name__ == '__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('canonical','sources','output','tessdata'):p.add_argument('--'+name,required=True)
    p.add_argument('--workers',type=int,default=4)
    a=p.parse_args();backfill(a.canonical,a.sources,a.output,a.tessdata,a.workers)
