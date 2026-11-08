"""Validate independent reviews, prepare blinded adjudication, and finalize offline."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

from .experiment import (agreement, check_predictions, evaluate, unique, verify,
                         write_json, write_jsonl)
from .review import HTML
from .run_model import digest, parse_response, payload
from .study import LABELS, read_jsonl

REASONS = {'outdated', 'conflicting', 'ambiguous', 'unverified'}


def write_sections(output, result, agreement_result, config):
    """Populate report prose only from completed, human-reviewed evaluation."""
    def number(value):
        return 'undefined' if value is None else f'{value:.4f}'
    model = result['metrics']['model']
    lines = ['# 4.3 Independent annotation and agreement', '',
             f"The two independent reviewers labeled {agreement_result['n']} records before adjudication. "
             f"Raw stage agreement was {number(agreement_result['raw_agreement'])}; unweighted Cohen's kappa was "
             f"{number(agreement_result['cohen_kappa'])}. These values use the preserved original labels, not the adjudicated labels.", '',
             '# 4.4 Classification evaluation', '',
             f"The primary comparison used {model['n']} records and identical evidence packets for both methods. "
             f"The model was {config['model']}. The model returned {model['accepted_predictions']} accepted outputs "
             f"and {model['response_failures']} response failures. All records remain in the evaluation denominator.", '',
             '| Method | Fixed four-class macro-F1 | False operational / predicted operational | Rate |',
             '|---|---:|---:|---:|']
    for method, score in result['metrics'].items():
        lines.append(f"| {method} | {number(score['macro_f1'])} | {score['false_operational_numerator']}/"
                     f"{score['operational_prediction_denominator']} | {number(score['false_operational_rate'])} |")
    lines += ['', 'A failed response is a false negative for its reference class and a prediction for none of the four stages. '
              'Classes absent from both reference and predictions contribute zero to the fixed four-class average. '
              'The false-operational rate uses all operational predictions as its denominator; it is not the conventional false-positive rate.', '',
              'See evaluation/report.md for confusion matrices and per-class results, and evaluation/results.json for paired '
              'organization-cluster bootstrap intervals. Small samples require descriptive interpretation; repeatability and exact quotation '
              'validation do not establish correctness. Independently inspect the false-operational audit before interpreting errors.', '']
    (Path(output)/'report_sections.md').write_text('\n'.join(lines))


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def selected_inputs(frozen, subset):
    frozen = Path(frozen); verify(frozen)
    config = json.loads((frozen/'config.json').read_text())
    splits = json.loads((frozen/'splits.json').read_text())
    rows = [r for r in read_jsonl(frozen/'inputs.jsonl') if splits[r['record_id']] == subset]
    if not rows: raise ValueError('Selected split is empty')
    return config, unique(rows)


def validate_reviews(rows, inputs, guide, allow_corrections=True):
    rows = unique(rows)
    if rows.keys() != inputs.keys():
        raise ValueError('Review IDs must exactly match the assigned packet')
    reviewers = set()
    for key, row in rows.items():
        person = row.get('reviewer_id')
        if not isinstance(person, str) or not person.strip(): raise ValueError('Missing reviewer identity')
        reviewers.add(person.strip().casefold())
        if row.get('annotation_guide_version') != guide: raise ValueError('Wrong annotation guide version')
        if not isinstance(row.get('notes'), str) or type(row.get('translation_assisted')) is not bool:
            raise ValueError('Notes and translation-assistance status are required')
        if row['translation_assisted'] and not row['notes'].strip():
            raise ValueError('Describe translation assistance in notes')
        if row.get('review_status') == 'needs_correction':
            if not allow_corrections or row.get('label') is not None or not row['notes'].strip():
                raise ValueError('Corrections require notes and a null label; unresolved corrections block finalization')
            continue
        if row.get('review_status') != 'confirmed': raise ValueError('Human field confirmation is required')
        if not isinstance(row.get('rationale'), str) or not row['rationale'].strip():
            raise ValueError('Annotation rationale is required')
        if row.get('label') == 'insufficiently_supported':
            if row.get('reason_code') not in REASONS: raise ValueError('Invalid insufficiency reason')
        elif row.get('reason_code') is not None: raise ValueError('Maturity label requires null reason code')
        check_predictions([inputs[key]], [row])
    if len(reviewers) != 1: raise ValueError('Each export must contain exactly one reviewer')
    return rows, next(iter(reviewers))


def seal(directory):
    directory = Path(directory)
    write_json(directory/'manifest.json', {p.name: sha(p) for p in sorted(directory.iterdir())
                                          if p.is_file() and p.name != 'manifest.json'})


def prepare_reviews(frozen, first_path, second_path, output, subset='test'):
    config, inputs = selected_inputs(frozen, subset)
    a, person_a = validate_reviews(read_jsonl(first_path), inputs, config['guide_version'])
    b, person_b = validate_reviews(read_jsonl(second_path), inputs, config['guide_version'])
    if person_a == person_b: raise ValueError('Two distinct independent reviewers are required')
    corrections = [k for k in inputs if a[k]['review_status'] != 'confirmed' or b[k]['review_status'] != 'confirmed']
    output = Path(output); output.mkdir(parents=True, exist_ok=False)
    (output/'reviewer-a.jsonl').write_bytes(Path(first_path).read_bytes())
    (output/'reviewer-b.jsonl').write_bytes(Path(second_path).read_bytes())
    state = {'frozen_manifest_sha256': sha(Path(frozen)/'manifest.json'), 'subset': subset,
             'guide_version': config['guide_version'], 'reviewers': [person_a, person_b],
             'record_ids': list(inputs), 'correction_ids': corrections,
             'created_at': datetime.now(timezone.utc).isoformat(),
             'identity_limit': 'Software validates recorded names and structure; it cannot authenticate people or prove blinding.'}
    if corrections:
        state.update(status='blocked_field_corrections', adjudication_ids=[])
        write_json(output/'field-corrections.json', [{
            'record_id': k, 'first': a[k], 'second': b[k]} for k in corrections])
        # Do not turn missing stages into labels or quietly compute partial agreement.
    else:
        write_json(output/'agreement.json', agreement({k:r['label'] for k,r in a.items()},
                                                     {k:r['label'] for k,r in b.items()}))
        pending = [k for k in inputs if (a[k]['label'], a[k]['reason_code']) != (b[k]['label'], b[k]['reason_code'])]
        write_jsonl(output/'consensus.jsonl', [dict(a[k], reference_origin='independent_consensus',
                                                  independent_reviewers=state['reviewers']) for k in inputs if k not in pending])
        write_jsonl(output/'disagreements.jsonl', [dict(record_id=k, first=a[k], second=b[k]) for k in pending])
        state.update(status='awaiting_adjudication' if pending else 'ready_for_finalization', adjudication_ids=pending)
        if pending:
            data = [dict(inputs[k], independent_annotations=[a[k], b[k]]) for k in pending]
            encoded = json.dumps(data, ensure_ascii=True).replace('<','\\u003c').replace('>','\\u003e').replace('&','\\u0026')
            html = HTML.replace('__MODE__', '"labels"').replace('__DATA__', encoded)
            html = html.replace('Independent review</h2>', 'Adjudication</h2>')
            html = html.replace('Keep model outputs and other reviewers’ labels hidden.',
                                'Read both locked independent annotations below; keep model outputs hidden.')
            html = html.replace('No model predictions, screening decisions or other reviewers’ labels are included.',
                                'The two independent annotations are included for adjudication; model predictions are withheld.')
            (output/'adjudication-packet.html').write_text(html)
    write_json(output/'review-state.json', state); seal(output)
    return {k: state[k] for k in ('status','record_ids','correction_ids','adjudication_ids')}


def collect_run(frozen, run_directory, inputs, config, subset):
    """Reconstruct accepted outputs/failures from preserved raw responses, offline."""
    frozen, run_directory = Path(frozen), Path(run_directory)
    identity = json.loads((run_directory/'identity.json').read_text())
    if identity.get('frozen_manifest_sha256') != sha(frozen/'manifest.json') or identity.get('split') != subset or identity.get('model') != config['model']:
        raise ValueError('Model run does not belong to the reviewed frozen split')
    requests = unique(read_jsonl(frozen/'model_requests.jsonl'))
    expected = {k: digest(payload(requests[k], config)) for k in inputs}
    if identity.get('request_sha256') != expected: raise ValueError('Model request identity differs')
    accepted, failures = [], []
    for key in inputs:
        file = run_directory/'raw'/(hashlib.sha256(key.encode()).hexdigest()+'.json')
        saved = json.loads(file.read_text())
        if saved.get('record_id') != key or saved.get('request_sha256') != expected[key]:
            raise ValueError('Raw response identity differs')
        if saved.get('transport_failure'):
            failures.append(dict(record_id=key, failure_type='transport', failure_reason='Recorded transport failure'))
            continue
        try:
            accepted.append(parse_response(saved.get('response'), inputs[key], config['model']))
        except (ValueError, TypeError, KeyError, AttributeError) as error:
            failures.append(dict(record_id=key, failure_type='response_validation',
                                 failure_reason=str(error) if isinstance(error, ValueError) else 'Malformed response'))
    return accepted, failures


def finalize(frozen, prepared, run_directory, output, adjudication=None, iterations=2000):
    frozen, prepared = Path(frozen), Path(prepared); verify(prepared)
    state = json.loads((prepared/'review-state.json').read_text())
    if state['frozen_manifest_sha256'] != sha(frozen/'manifest.json'): raise ValueError('Reviewed inputs changed')
    if state['status'] == 'blocked_field_corrections': raise ValueError('Field corrections require a new reviewed input version')
    config, inputs = selected_inputs(frozen, state['subset'])
    # Revalidate sealed originals, not merely the state file's summary.
    a, person_a = validate_reviews(read_jsonl(prepared/'reviewer-a.jsonl'), inputs, config['guide_version'], False)
    b, person_b = validate_reviews(read_jsonl(prepared/'reviewer-b.jsonl'), inputs, config['guide_version'], False)
    if person_a == person_b: raise ValueError('Reviewers must be distinct')
    pending = [k for k in inputs if (a[k]['label'],a[k]['reason_code']) != (b[k]['label'],b[k]['reason_code'])]
    decisions = {}
    if pending:
        if adjudication is None: raise ValueError('Independent adjudication export is required for disagreements')
        decisions, person = validate_reviews(read_jsonl(adjudication), {k:inputs[k] for k in pending}, config['guide_version'], False)
        if person in (person_a, person_b): raise ValueError('Use a distinct adjudicator for disputed records')
    elif adjudication is not None and read_jsonl(adjudication):
        raise ValueError('No disputed records require adjudication')
    gold = [dict(decisions[k] if k in decisions else a[k],
                 reference_origin='adjudicated' if k in decisions else 'independent_consensus') for k in inputs]
    # Reference labels are locked before reading predictions. Never call an API.
    accepted, failures = collect_run(frozen, run_directory, inputs, config, state['subset'])
    output = Path(output); output.mkdir(parents=True, exist_ok=False)
    write_jsonl(output/'gold.jsonl', gold)
    write_jsonl(output/'accepted_predictions.jsonl', accepted)
    write_jsonl(output/'failures.jsonl', failures)
    promoted = output/'human-reviewed-frozen'; promoted.mkdir()
    write_jsonl(promoted/'inputs.jsonl', list(inputs.values()))
    write_json(promoted/'splits.json', {k:state['subset'] for k in inputs})
    write_jsonl(promoted/'rule_predictions.jsonl', [r for r in read_jsonl(frozen/'rule_predictions.jsonl') if r['record_id'] in inputs])
    write_jsonl(promoted/'model_requests.jsonl', [r for r in read_jsonl(frozen/'model_requests.jsonl') if r['record_id'] in inputs])
    original_screening = config.pop('screening_audit', None)
    config.update(purpose='study', calibration_ids=[k for k in config.get('calibration_ids',[]) if k in inputs],
                  unconfirmed_candidate_ids=[], pending_human_review_ids=[],
                  parent_frozen_manifest_sha256=sha(frozen/'manifest.json'),
                  human_review_manifest_sha256=sha(prepared/'manifest.json'),
                  human_review_scope=state['subset'], reviewed_record_ids=list(inputs))
    write_json(promoted/'config.json',config); seal(promoted)
    write_json(output/'human-review-attestation.json', {
        'reviewers':state['reviewers'], 'record_ids':list(inputs), 'inputs_unchanged':True,
        'reviewer_a_sha256':sha(prepared/'reviewer-a.jsonl'), 'reviewer_b_sha256':sha(prepared/'reviewer-b.jsonl'),
        'adjudication_sha256':sha(adjudication) if adjudication is not None else None,
        'original_screening_audit':original_screening, 'source_run_identity_sha256':sha(Path(run_directory)/'identity.json'),
        'limit':state['identity_limit']})
    (output/'agreement.json').write_bytes((prepared/'agreement.json').read_bytes())
    result = evaluate(promoted, output/'accepted_predictions.jsonl', output/'gold.jsonl',
                      output/'evaluation', subset=state['subset'],iterations=iterations,failures_path=output/'failures.jsonl')
    write_sections(output, result, json.loads((output/'agreement.json').read_text()), config)
    write_json(output/'completion.json', {'status':'completed','records':len(inputs),
                                        'accepted':len(accepted),'failed':len(failures),
                                        'source_frozen_manifest_sha256':sha(frozen/'manifest.json')})
    return result


def main():
    parser=argparse.ArgumentParser(description=__doc__); sub=parser.add_subparsers(dest='command',required=True)
    p=sub.add_parser('prepare');p.add_argument('--frozen',required=True);p.add_argument('--reviewer-a',required=True);p.add_argument('--reviewer-b',required=True);p.add_argument('--output',required=True);p.add_argument('--split',default='test',choices=['test','development'])
    f=sub.add_parser('finalize');f.add_argument('--frozen',required=True);f.add_argument('--prepared',required=True);f.add_argument('--run',required=True);f.add_argument('--output',required=True);f.add_argument('--adjudication')
    a=parser.parse_args()
    if a.command=='prepare':r=prepare_reviews(a.frozen,a.reviewer_a,a.reviewer_b,a.output,a.split)
    else:r=finalize(a.frozen,a.prepared,a.run,a.output,a.adjudication)
    print(json.dumps(r,ensure_ascii=False,indent=2))


if __name__=='__main__': main()
