"""Run a frozen split with the Responses API; checkpoint raw results and resume."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import time
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from .experiment import check_predictions, unique, verify, write_json, write_jsonl
from .study import LABELS, read_jsonl

ENDPOINT = 'https://api.openai.com/v1/responses'
REASONS = ['outdated', 'conflicting', 'ambiguous', 'unverified']
SCHEMA = {
    'type': 'object', 'additionalProperties': False,
    'properties': {
        'record_id': {'type': 'string'},
        'label': {'type': 'string', 'enum': list(LABELS)},
        'quote': {'type': 'string'},
        'evidence_index': {'type': ['integer', 'null']},
        'reason_code': {'type': ['string', 'null'], 'enum': REASONS + [None]},
        'rationale': {'type': 'string'},
    },
    'required': ['record_id', 'label', 'quote', 'evidence_index', 'reason_code', 'rationale'],
}


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def atomic_json(path, value):
    path = Path(path)
    temp = path.with_suffix(path.suffix + '.tmp')
    write_json(temp, value)
    temp.replace(path)


def payload(request, config):
    settings = config.get('model_settings', {'max_output_tokens': 1500})
    if not isinstance(settings, dict) or set(settings) - {'max_output_tokens', 'temperature', 'top_p', 'reasoning'}:
        raise ValueError('Unsupported model setting; use explicit generation settings only')
    if request['model'] != config['model'] or request['instructions'] != config['prompt']:
        raise ValueError('Request does not match frozen model/prompt')
    return {
        'model': config['model'], 'instructions': config['prompt'],
        'input': json.dumps(request['input'], ensure_ascii=False),
        'store': False, **settings,
        'text': {'format': {'type': 'json_schema', 'name': 'deployment_stage',
                            'strict': True, 'schema': SCHEMA}},
    }


def parse_response(response, record, model):
    if response.get('status') != 'completed':
        raise ValueError('Response incomplete; inspect the saved raw response')
    if response.get('model') != model:
        raise ValueError('Returned model differs from frozen identifier; use an explicit supported snapshot')
    parts = [part for item in response.get('output', []) for part in item.get('content', [])]
    if any(part.get('type') == 'refusal' for part in parts):
        raise ValueError('Model refused; keep the failure separate from a stage label')
    text = ''.join(part['text'] for part in parts if part.get('type') == 'output_text')
    prediction = json.loads(text)
    if set(prediction) != set(SCHEMA['required']):
        raise ValueError('Model response has missing or unexpected fields')
    if not isinstance(prediction['rationale'], str) or not prediction['rationale'].strip():
        raise ValueError('A nonempty rationale is required')
    check_predictions([record], [prediction])
    reason = prediction['reason_code']
    if prediction['label'] == 'insufficiently_supported':
        if reason not in REASONS:
            raise ValueError('Insufficiently supported requires a valid reason code')
    elif reason is not None:
        raise ValueError('Reason code must be null for maturity labels')
    return prediction


def post(body, api_key):
    """Retry transport/transient HTTP failures only; never resample invalid labels."""
    data = json.dumps(body, ensure_ascii=False).encode()
    for attempt in range(4):
        try:
            request = Request(ENDPOINT, data=data, headers={
                'Authorization': 'Bearer ' + api_key, 'Content-Type': 'application/json'})
            with urlopen(request, timeout=60) as response:
                return json.load(response)
        except HTTPError as exc:
            if exc.code not in (408, 429, 500, 502, 503, 504) or attempt == 3:
                raise RuntimeError(f'API HTTP {exc.code}; verify access, quota and frozen model/settings') from None
        except (URLError, TimeoutError):
            if attempt == 3:
                raise RuntimeError('API transport failed after four attempts') from None
        time.sleep(2 ** attempt)


def run(directory, output, subset='development', dry_run=False, transport=None):
    directory, output = Path(directory), Path(output)
    verify(directory)
    config = json.loads((directory / 'config.json').read_text())
    assignments = json.loads((directory / 'splits.json').read_text())
    records = unique(read_jsonl(directory / 'inputs.jsonl'))
    requests = unique(read_jsonl(directory / 'model_requests.jsonl'))
    if records.keys() != requests.keys():
        raise ValueError('Frozen request IDs do not match inputs')
    selected = [k for k in records if assignments[k] == subset]
    if not selected:
        raise ValueError('Selected split is empty')
    bodies = {}
    for key in selected:
        if requests[key]['input'] != records[key]:
            raise ValueError('Request input differs from common evidence packet')
        bodies[key] = payload(requests[key], config)
    if dry_run:
        return {'status': 'offline validation only; no API call or access verification',
                'records': len(selected), 'split': subset, 'model': config['model']}
    api_key = os.environ.get('OPENAI_API_KEY')
    if transport is None and not api_key:
        raise ValueError('Set OPENAI_API_KEY in your terminal; never put it in data or source control')
    transport = transport or (lambda body: post(body, api_key))
    identity = {'frozen_manifest_sha256': hashlib.sha256((directory / 'manifest.json').read_bytes()).hexdigest(),
                'split': subset, 'model': config['model'], 'endpoint': ENDPOINT,
                'request_sha256': {k: digest(v) for k, v in bodies.items()},
                'runner_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    if output.exists():
        if not (output / 'identity.json').is_file() or json.loads((output / 'identity.json').read_text()) != identity:
            raise ValueError('Existing run belongs to different frozen inputs/settings/code')
    else:
        output.mkdir(parents=True)
        write_json(output / 'identity.json', identity)
    (output / 'raw').mkdir(exist_ok=True)
    predictions = []
    # One writer per output directory; protect checkpoints from concurrent runs.
    lock = output / '.running'
    with lock.open('x'):
        pass
    try:
        for key in selected:
            raw_path = output / 'raw' / (hashlib.sha256(key.encode()).hexdigest() + '.json')
            if raw_path.exists():
                saved = json.loads(raw_path.read_text())
                if saved.get('request_sha256') != digest(bodies[key]):
                    raise ValueError('Cached response has a different request')
            else:
                response = transport(bodies[key])
                saved = {'record_id': key, 'request_sha256': digest(bodies[key]),
                         'received_at': datetime.now(timezone.utc).isoformat(), 'response': response}
                atomic_json(raw_path, saved)
            # An invalid cached response stops resume, rather than being silently resampled.
            predictions.append(parse_response(saved['response'], records[key], config['model']))
        check_predictions([records[k] for k in selected], predictions)
        temp = output / 'predictions.jsonl.tmp'
        write_jsonl(temp, predictions)
        temp.replace(output / 'predictions.jsonl')
        atomic_json(output / 'run_metadata.json', {**identity, 'records': len(predictions),
                    'completed_at': datetime.now(timezone.utc).isoformat(), 'status': 'completed'})
    finally:
        lock.unlink()
    return {'status': 'completed', 'records': len(predictions), 'split': subset,
            'predictions': str(output / 'predictions.jsonl')}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('experiment')
    parser.add_argument('--output', required=True)
    parser.add_argument('--split', choices=['development', 'test'], default='development')
    parser.add_argument('--dry-run', action='store_true', help='Validate locally; no API call or access check')
    args = parser.parse_args()
    print(json.dumps(run(args.experiment, args.output, args.split, args.dry_run), indent=2))


if __name__ == '__main__':
    main()
