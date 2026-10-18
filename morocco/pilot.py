"""Build the reproducible 20-document feasibility-pilot manifest."""
import argparse
import json
import unicodedata
from pathlib import Path

from .study import read_jsonl


SELECTION = [
('NVIDIA Datacenters.pdf','deployment lead','Infrastructure project reporting; verify stage and AI use-case eligibility.'),
('Al-Khwarizmi Program1.pdf','deployment lead','Extracted title concerns an AI hub; filename mismatch needs metadata correction.'),
('Institut Jazari ROOT.pdf','boundary case','Institution founding is not by itself evidence of deployed AI.'),
('AI in Education.pdf','deployment lead','Check for specific implemented or planned education use cases.'),
('AI in Morocco.pdf','discovery context','Potential organization leads; verify claims against original sources.'),
('AIReadinessAssessmentMorocco_Report_23-03-24.pdf','discovery context','Readiness context and potential deployment leads.'),
('EHEI-JST_51630-Chouraik+Resent.pdf','discovery context','Research paper; distinguish proposed systems from deployment evidence.'),
('1017-Article Text-3470-1-10-20240709.pdf','discovery context','French-language research source; assess concrete organization-level claims.'),
('Al-Khwarizmi Program.pdf','boundary case','Research funding/program announcements do not establish operation.'),
('Morocco Moves AI Strategy Into Implementation, Targets MAD 100 Bln in GDP Value by 2030 _ Maroc.ma.pdf','boundary case','National implementation claims need organization-specific evidence.'),
('Roadmap.pdf','policy context','Use policy context to check announcement versus demonstrated deployment.'),
('Rapport de Synthèse ANG.pdf','discovery context','Long Morocco AI report; screen for attributable deployment claims.'),
('AI reform.pdf','extraction challenge','Spaced text requires visual reading-order review.'),
('DigitalMorroco2030.pdf','extraction challenge','No meaningful extracted text; inspect and arrange OCR.'),
('ai readiness evaluation.pdf','extraction challenge','No meaningful extracted text; inspect and arrange OCR.'),
('French/Right to Privacy.pdf','boundary case','Regulatory text is context, not evidence of any particular deployment.'),
('canva-sante-en.pdf','sector context','Health-sector context; check for organization-specific AI evidence.'),
('French/health.pdf','translation review','Possible related health document; verify translation group manually.'),
('Enseignement-EN.pdf','sector context','Education strategy; screen for eligible claims.'),
('French/higher education.pdf','translation review','Possible counterpart to English education document; verify manually.')]


def normalized_path(path):
    return unicodedata.normalize('NFC', path)


def build(processed, output, plan_output=Path('pilot-plan.md')):
    processed, output, plan_output = Path(processed), Path(output), Path(plan_output)
    rows = read_jsonl(processed / 'inventory.jsonl')
    pages = read_jsonl(processed / 'pages.jsonl')
    by_path = {}
    for row in rows:
        key = normalized_path(row['path'])
        if key in by_path:
            raise ValueError(f'Duplicate Unicode-normalized path: {row["path"]}')
        by_path[key] = row

    missing = [name for name, _, _ in SELECTION if normalized_path(name) not in by_path]
    if missing:
        raise ValueError('Pilot source files missing: ' + ', '.join(missing))

    output.mkdir(parents=True, exist_ok=True)
    selected = []
    for name, role, reason in SELECTION:
        row = by_path[normalized_path(name)]
        selected.append({
            'document_id': row['document_id'],
            'path': row['path'],
            'role': role,
            'selection_reason': reason,
            'eligibility': 'pending human review',
            'empty_pages': row.get('empty_pages', []),
        })
    (output / 'selection.json').write_text(
        json.dumps(selected, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')

    pages_by_document = {}
    for page in pages:
        pages_by_document.setdefault(page['document_id'], []).append(page['text'])
    quality = []
    for row in rows:
        document_id = row.get('document_id')
        if not document_id:
            continue
        text = ''.join(pages_by_document.get(document_id, []))
        controls = sum(ord(c) < 32 and c not in '\n\r\t' for c in text)
        fraction = controls / max(1, len(text))
        quality.append({
            'path': row['path'],
            'document_id': document_id,
            'characters': len(text.strip()),
            'empty_pages': row.get('empty_pages', []),
            'control_character_fraction': fraction,
            'review_flags': (
                (['no meaningful text'] if len(text.strip()) < 100 else [])
                + (['possible font encoding corruption'] if fraction > .01 else [])
            ),
        })
    (output / 'extraction-quality.json').write_text(
        json.dumps(quality, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')

    markdown = '# Proposed 20-document pilot\n\nThis purposive feasibility selection is not a representative sample or the matched English/French search experiment. Context documents may yield zero eligible deployments. Arabic sources remain preserved in the corpus but outside the original English/French study scope. No labels are assigned.\n\n'
    for index, row in enumerate(selected, 1):
        markdown += f"{index}. **{row['path']}** — {row['role']}. {row['selection_reason']}\n\n"
    plan_output.write_text(markdown.rstrip() + '\n', encoding='utf-8')
    return selected, quality


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--processed', type=Path, default=Path('data/processed'))
    parser.add_argument('--output', type=Path, default=Path('data/pilot'))
    parser.add_argument('--plan-output', type=Path, default=Path('pilot-plan.md'))
    args = parser.parse_args()
    selected, quality = build(args.processed, args.output, args.plan_output)
    print(json.dumps({
        'selected_documents': len(selected),
        'quality_rows': len(quality),
        'output': str(args.output),
        'plan_output': str(args.plan_output),
    }, indent=2))


if __name__ == '__main__':
    main()
