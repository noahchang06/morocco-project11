"""Local ingestion; never uploads documents or calls a model."""
import argparse
import hashlib
import json
from pathlib import Path


def digest(data):
    return hashlib.sha256(data).hexdigest()


def chunks(text, size=1800, overlap=200):
    if size <= 0 or not 0 <= overlap < size:
        raise ValueError('Require size > 0 and 0 <= overlap < size')
    start = 0
    while start < len(text):
        end = min(start + size, len(text))
        if text[start:end].strip():
            yield start, end, text[start:end]
        if end == len(text):
            break
        start = end - overlap


def read_pages(path):
    if path.suffix.lower() == '.pdf':
        try:
            import pymupdf
        except ImportError:
            try:
                from pypdf import PdfReader
            except ImportError as exc:
                raise RuntimeError('PDF extraction requires PyMuPDF or pypdf') from exc
            return [page.extract_text() or '' for page in PdfReader(path).pages]
        with pymupdf.open(path) as document:
            return [page.get_text(sort=True) for page in document]
    return [path.read_text(encoding='utf-8')]


def ingest(source, output, size=1800, overlap=200):
    source, output = Path(source).resolve(), Path(output).resolve()
    if not source.is_dir():
        raise ValueError('Source must be an existing directory')
    if output == source or source in output.parents:
        raise ValueError('Output must be outside the source directory')
    if size <= 0 or not 0 <= overlap < size:
        raise ValueError('Invalid chunk settings')
    inventory, passages, pages_out, seen = [], [], [], {}
    for path in sorted(source.rglob('*')):
        if not path.is_file() or path.is_symlink():
            continue
        relative = str(path.relative_to(source))
        row = {'path': relative, 'title': path.stem, 'language': None,
               'issuer': None, 'publication_date': None, 'source_url': None,
               'geographic_scope': None, 'document_type': None,
               'translation_group': None}
        inventory.append(row)
        if path.suffix.lower() not in {'.pdf', '.txt', '.md'}:
            row['status'] = 'unsupported'
            continue
        try:
            sha = digest(path.read_bytes())
            row.update(document_id=sha, sha256=sha)
            if sha in seen:
                row.update(status='duplicate', duplicate_of=seen[sha])
                continue
            pages = read_pages(path)
            row.update(status='extracted', page_count=len(pages),
                       empty_pages=[i for i, text in enumerate(pages, 1) if not text.strip()])
            if row['empty_pages']:
                row['status'] = 'needs_review'
            seen[sha] = relative
            for page_number, text in enumerate(pages, 1):
                pages_out.append({'document_id': sha, 'page': page_number, 'text': text})
                for start, end, passage in chunks(text, size, overlap):
                    passages.append({'chunk_id': digest(f'{sha}:{page_number}:{start}:{end}:{passage}'.encode()),
                                     'document_id': sha, 'source_path': relative,
                                     'page': page_number, 'start': start, 'end': end, 'text': passage})
        except Exception as exc:
            row.update(status='error', error=f'{type(exc).__name__}: {exc}')
    output.mkdir(parents=True, exist_ok=True)
    for name, rows in [('inventory', inventory), ('pages', pages_out), ('chunks', passages)]:
        (output / f'{name}.jsonl').write_text(''.join(json.dumps(r, ensure_ascii=False) + '\n' for r in rows), encoding='utf-8')
    report = {'files': len(inventory), 'unique_documents': len(seen),
              'pages': len(pages_out), 'chunks': len(passages),
              'duplicates': sum(r['status'] == 'duplicate' for r in inventory),
              'errors': sum(r['status'] == 'error' for r in inventory),
              'needs_review': sum(r['status'] == 'needs_review' for r in inventory),
              'chunk_characters': size, 'overlap_characters': overlap,
              'corpus_fingerprint': digest(json.dumps(passages, sort_keys=True, ensure_ascii=False).encode())}
    (output / 'report.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    parser.add_argument('--output', type=Path, default=Path('data/processed'))
    parser.add_argument('--size', type=int, default=1800)
    parser.add_argument('--overlap', type=int, default=200)
    args = parser.parse_args()
    report = ingest(args.source, args.output, args.size, args.overlap)
    print(json.dumps(report, indent=2))
    raise SystemExit(1 if report['errors'] else 0)


if __name__ == '__main__':
    main()
