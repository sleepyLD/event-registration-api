"""Build/run disposable PostgreSQL tests and save exact output and exit status."""
from pathlib import Path
import json
import subprocess
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.stderr.reconfigure(encoding='utf-8', errors='replace')

ROOT = Path(__file__).resolve().parents[1]
COMPOSE = ['docker', 'compose', '-f', 'compose.test.yaml']


def main():
    rows = []
    result_code = 1
    try:
        command = COMPOSE + ['up', '--build', '--abort-on-container-exit', '--exit-code-from', 'tests']
        result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, encoding='utf-8', errors='replace')
        rows.append({'command': command, 'exit_code': result.returncode, 'stdout': result.stdout, 'stderr': result.stderr})
        print(result.stdout)
        print(result.stderr, file=sys.stderr)
        result_code = result.returncode
    except OSError as exc:
        rows.append({'error': str(exc)})
        print(str(exc), file=sys.stderr)
    finally:
        try:
            result = subprocess.run(COMPOSE + ['down'], cwd=ROOT, capture_output=True, text=True, encoding='utf-8', errors='replace')
            rows.append({'command': COMPOSE + ['down'], 'exit_code': result.returncode, 'stdout': result.stdout, 'stderr': result.stderr})
            if result.returncode:
                result_code = result.returncode
        except OSError as exc:
            rows.append({'cleanup_error': str(exc)})
            result_code = 1
        path = ROOT / 'docs/evidence/portfolio-tests.local.json'
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({'exit_code': result_code, 'results': rows}, ensure_ascii=False, indent=2), encoding='utf-8')
        print('Evidence saved: docs/evidence/portfolio-tests.local.json')
    return result_code


if __name__ == '__main__':
    raise SystemExit(main())
