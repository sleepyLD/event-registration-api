"""Read-only HTTP checks plus DB outage/restart in an isolated Compose project."""
import json
import os
from pathlib import Path
import subprocess
import time
import urllib.error
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
PROJECT = "event-registration-stage11-check"
ENV = dict(os.environ, API_PORT="18000")
RESULTS = []


def compose(*args):
    cmd = ["docker", "compose", "-p", PROJECT, *args]
    result = subprocess.run(cmd, cwd=ROOT, env=ENV, capture_output=True, text=True, encoding="utf-8", errors="replace")
    RESULTS.append({"command": cmd, "exit_code": result.returncode,
                    "stdout": result.stdout, "stderr": result.stderr})
    if result.returncode:
        raise RuntimeError("Compose command failed: " + " ".join(args))


def http(path, expected, expected_body=None, retry=True):
    deadline = time.monotonic() + (60 if retry else 0)
    while True:
        try:
            try:
                with urllib.request.urlopen("http://127.0.0.1:18000" + path, timeout=12) as response:
                    status, raw = response.status, response.read().decode()
            except urllib.error.HTTPError as response:
                status, raw = response.code, response.read().decode()
            body = json.loads(raw) if path != "/docs" else None
            assert status == expected, (status, raw)
            if expected_body is not None:
                assert body == expected_body, body
            if path == "/openapi.json":
                assert "/health" in body["paths"]
            if path == "/docs":
                assert "swagger-ui" in raw
            RESULTS.append({"request": "GET " + path, "status": status,
                            "body": body if path == "/health" else "content verified", "result": "PASS"})
            return
        except (AssertionError, OSError, ValueError):
            if time.monotonic() >= deadline:
                raise
            time.sleep(1)


def main():
    failed = 0
    try:
        compose("up", "--build", "-d", "--wait", "--wait-timeout", "120")
        http("/health", 200, {"status": "ok", "database": "ok"})
        http("/docs", 200)
        http("/openapi.json", 200)
        compose("exec", "-T", "api", "python", "-m", "pip", "check")
        compose("stop", "db")
        http("/health", 503, {"code": "DATABASE_UNAVAILABLE", "message": "Database unavailable"}, retry=False)
        compose("start", "db")
        http("/health", 200, {"status": "ok", "database": "ok"})
        compose("stop")
        compose("up", "-d", "--wait", "--wait-timeout", "120")
        http("/health", 200, {"status": "ok", "database": "ok"})
        compose("ps")
        compose("logs", "--tail=100", "api")
    except Exception as exc:
        failed += 1
        RESULTS.append({"result": "FAIL", "error": str(exc)})
    finally:
        try:
            compose("down")  # only this fixed isolated project; retains its empty DB volume
        except Exception as exc:
            failed += 1
            RESULTS.append({"result": "FAIL", "error": str(exc)})
        output = ROOT / "docs/evidence/stage-1.1-checks.json"
        output.write_text(json.dumps({"failed_checks": failed, "results": RESULTS}, indent=2), encoding="utf-8")
    print(json.dumps({"failed_checks": failed, "http_checks": sum("request" in r for r in RESULTS),
                      "evidence": "docs/evidence/stage-1.1-checks.json"}))
    return int(bool(failed))


if __name__ == "__main__":
    raise SystemExit(main())
