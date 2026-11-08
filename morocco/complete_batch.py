"""Finish unattempted frozen requests while retaining every failed first response."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path

from . import run_model
from .experiment import check_predictions, unique, verify, write_jsonl
from .run_model import ENDPOINT, atomic_json, digest, parse_response, payload, post
from .study import read_jsonl


def _write_jsonl(path, rows):
    temporary = path.with_suffix(path.suffix + '.tmp')
    write_jsonl(temporary, rows)
    temporary.replace(path)


def complete(directory, output, subset='test', transport=None):
    """Resume an original runner directory without resampling invalid responses.

    Transport failures are checkpointed as attempts with no response, and are
    also never retried by this wrapper. The original post helper retains its
    existing transient-transport retry policy within a single attempt.
    """
    directory, output = Path(directory), Path(output)
    verify(directory)
    config = json.loads((directory / 'config.json').read_text())
    assignments = json.loads((directory / 'splits.json').read_text())
    records = unique(read_jsonl(directory / 'inputs.jsonl'))
    requests = unique(read_jsonl(directory / 'model_requests.jsonl'))
    if records.keys() != requests.keys():
        raise ValueError('Frozen request IDs do not match inputs')
    selected = [key for key in records if assignments[key] == subset]
    if not selected:
        raise ValueError('Selected split is empty')
    bodies = {}
    for key in selected:
        if requests[key]['input'] != records[key]:
            raise ValueError('Request input differs from common evidence packet')
        bodies[key] = payload(requests[key], config)
    identity = {
        'frozen_manifest_sha256': hashlib.sha256((directory / 'manifest.json').read_bytes()).hexdigest(),
        'split': subset, 'model': config['model'], 'endpoint': ENDPOINT,
        'request_sha256': {key: digest(body) for key, body in bodies.items()},
        'runner_sha256': hashlib.sha256(Path(run_model.__file__).read_bytes()).hexdigest(),
    }
    if not (output / 'identity.json').is_file() or json.loads((output / 'identity.json').read_text()) != identity:
        raise ValueError('Existing run belongs to different frozen inputs/settings/original runner code')
    lock = output / '.running'
    with lock.open('x'):
        pass
    try:
        (output / 'raw').mkdir(exist_ok=True)
        paths = {key: output / 'raw' / (hashlib.sha256(key.encode()).hexdigest() + '.json')
                 for key in selected}
        cached = {}
        # Validate all existing attempt envelopes before making any new request.
        for key, path in paths.items():
            if path.exists():
                saved = json.loads(path.read_text())
                if (saved.get('record_id') != key or
                        saved.get('request_sha256') != digest(bodies[key])):
                    raise ValueError('Cached response has a different record or request')
                cached[key] = saved
        if transport is None and len(cached) != len(selected):
            api_key = os.environ.get('OPENAI_API_KEY')
            if not api_key:
                raise ValueError('OPENAI_API_KEY is required for unattempted requests')
            transport = lambda body: post(body, api_key)
        predictions, failures = [], []
        for key in selected:
            saved = cached.get(key)
            if saved is None:
                saved = {'record_id': key, 'request_sha256': digest(bodies[key]),
                         'received_at': datetime.now(timezone.utc).isoformat()}
                try:
                    saved['response'] = transport(bodies[key])
                except (OSError, RuntimeError, ValueError) as exc:
                    # Never persist arbitrary exception messages: a transport
                    # implementation could include credentials or request headers.
                    saved.update(response=None, transport_failure={
                        'error_type': type(exc).__name__,
                        'reason': 'Transport failed; no usable response was received.',
                    })
                atomic_json(paths[key], saved)
            response = saved.get('response')
            if saved.get('transport_failure'):
                failures.append({'record_id': key, 'failure_type': 'transport',
                                 'failure_reason': 'Transport failed; no usable response was received.',
                                 'response_status': None})
                continue
            try:
                predictions.append(parse_response(response, records[key], config['model']))
            except (ValueError, TypeError, KeyError, AttributeError) as exc:
                reason = str(exc) if isinstance(exc, ValueError) else 'Malformed response structure: ' + type(exc).__name__
                failures.append({'record_id': key, 'failure_type': 'response_validation',
                                 'failure_reason': reason,
                                 'response_status': response.get('status') if isinstance(response, dict) else None})
        _write_jsonl(output / 'accepted_predictions.jsonl', predictions)
        _write_jsonl(output / 'failures.jsonl', failures)
        if not failures:
            check_predictions([records[key] for key in selected], predictions)
            _write_jsonl(output / 'predictions.jsonl', predictions)
        elif (output / 'predictions.jsonl').exists():
            raise ValueError('Existing complete predictions conflict with failed responses; inspect the run')
        metadata = {
            **identity,
            'wrapper_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            'completed_at': datetime.now(timezone.utc).isoformat(),
            'status': 'completed_with_failures' if failures else 'completed',
            'records': len(selected), 'accepted': len(predictions), 'failed': len(failures),
            'cached_attempts': len(cached), 'new_attempts': len(selected) - len(cached),
            'resampling_policy': 'No saved attempt is resampled, including validation and transport failures.',
        }
        atomic_json(output / 'batch_metadata.json', metadata)
    finally:
        lock.unlink()
    return {key: metadata[key] for key in ('status', 'records', 'accepted', 'failed', 'split', 'new_attempts')}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('experiment')
    parser.add_argument('--output', required=True, help='Existing original runner output directory')
    parser.add_argument('--split', choices=['development', 'test'], default='test')
    args = parser.parse_args()
    print(json.dumps(complete(args.experiment, args.output, args.split), indent=2))


if __name__ == '__main__':
    main()
