"""Run a short end-to-end demo against the running API; creates new demo data."""
import json
import urllib.request
import urllib.error
from uuid import uuid4

BASE = 'http://localhost:8000'


def request(method, path, body=None, expected=200):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(BASE + path, data=data, method=method, headers={'Content-Type': 'application/json'})
    try:
        response = urllib.request.urlopen(req, timeout=15)
    except urllib.error.HTTPError as exc:
        response = exc
    with response:
        raw = response.read()
        result = json.loads(raw) if raw else None
        print(method, path, response.status, result)
        if response.status != expected:
            raise RuntimeError(f'Expected {expected}, received {response.status}')
        return result


def main():
    tag = uuid4().hex[:8]
    request('GET', '/health')
    a = request('POST', '/users', {'name': f'Alice-{tag}'}, 201)['id']
    b = request('POST', '/users', {'name': f'Bob-{tag}'}, 201)['id']
    event = request('POST', '/events', {'title': f'Workshop-{tag}', 'capacity': 1}, 201)['id']
    path = f'/events/{event}/registrations'
    request('POST', path, {'user_id': a}, 201)
    request('POST', path, {'user_id': b}, 409)
    request('DELETE', f'{path}/{a}', expected=204)
    request('POST', path, {'user_id': b}, 201)
    request('GET', f'/events/{event}')
    request('GET', path)
    print('Demo completed. Demo data remains for inspection.')


if __name__ == '__main__':
    main()
