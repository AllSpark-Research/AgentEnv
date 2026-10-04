import json, math, os, subprocess, sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
out = Path(os.environ.get('VERIFIER_LOG_DIR', '/logs/verifier'))
out.mkdir(parents=True, exist_ok=True)
reward = out / 'reward.txt'
reward.unlink(missing_ok=True)
try:
    spec = json.loads((HERE / 'eval_spec.json').read_text())
    rubric = spec['rubric']
    if any(x['method'] == 'llm_judge' for x in rubric):
        for key in ['JUDGE_BASE_URL', 'JUDGE_MODEL']:
            if not os.environ.get(key, '').strip():
                raise RuntimeError(f'{key} is required for this task; configure verifier.env')
    p = subprocess.run([sys.executable, str(HERE / 'hybrid_verify.py')], capture_output=True, text=True)
    (out / 'verifier.stdout').write_text(p.stdout)
    (out / 'verifier.stderr').write_text(p.stderr)
    if p.returncode:
        raise RuntimeError(f'hybrid verifier exited {p.returncode}')
    result = json.loads(p.stdout.strip().splitlines()[-1])
    (out / 'result.json').write_text(json.dumps(result, indent=2, ensure_ascii=False))
    if result.get('fatal'):
        raise RuntimeError(result['fatal'])
    items = result.get('per_item', [])
    if {x['id'] for x in items} != {x['id'] for x in rubric}:
        raise RuntimeError('Missing or unexpected rubric item results')
    for item in items:
        detail = str(item.get('detail', '')).lower()
        if 'fail-safe' in detail or 'no verify.py output' in detail or 'unparseable/unreachable' in detail:
            raise RuntimeError(f"Evaluation infrastructure failure for {item['id']}: {detail}")
        value = float(item['score'])
        if not math.isfinite(value) or not 0 <= value <= 1:
            raise RuntimeError(f"Invalid score for {item['id']}")
    score = float(result['score'])
    if not math.isfinite(score) or not 0 <= score <= 1:
        raise RuntimeError('Invalid aggregate reward')
    reward.write_text(str(score) + '\n')
    print(json.dumps(result, ensure_ascii=False))
except Exception as e:
    (out / 'error.json').write_text(json.dumps({'error': str(e)}, indent=2))
    print(f'VERIFIER ERROR: {e}', file=sys.stderr)
    sys.exit(1)
