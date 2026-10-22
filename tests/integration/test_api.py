import pytest
from sqlalchemy import text


def user(client, name='A'):
    r = client.post('/users', json={'name': name})
    assert r.status_code == 201
    return r.json()['id']


def event(client, capacity=2):
    r = client.post('/events', json={'title': ' Workshop ', 'capacity': capacity})
    assert r.status_code == 201
    return r.json()['id']


def assert_invariant(engine, event_id):
    with engine.connect() as conn:
        row = conn.execute(text("SELECT capacity, remaining_slots, (SELECT count(*) FROM registrations WHERE event_id=e.id AND status='active') AS active FROM events e WHERE id=:id"), {'id': event_id}).one()
        assert 0 <= row.remaining_slots <= row.capacity
        assert row.active + row.remaining_slots == row.capacity
        assert row.active <= row.capacity
        assert conn.scalar(text("SELECT count(*) FROM (SELECT user_id FROM registrations WHERE event_id=:id AND status='active' GROUP BY user_id HAVING count(*)>1) t"), {'id': event_id}) == 0


def test_sequential_workflow(client, engine):
    eid = event(client)
    a, b, c = [user(client, name) for name in ['A', 'B', 'C']]
    path = f'/events/{eid}/registrations'
    original = client.post(path, json={'user_id': a})
    assert original.status_code == 201
    assert client.post(path, json={'user_id': a}).json()['code'] == 'ALREADY_REGISTERED'
    assert client.post(path, json={'user_id': b}).status_code == 201
    full = client.post(path, json={'user_id': c})
    assert full.status_code == 409 and full.json()['code'] == 'EVENT_FULL'
    assert client.post(path, json={'user_id': a}).json()['code'] == 'ALREADY_REGISTERED'
    cancelled = client.delete(f'{path}/{a}')
    assert cancelled.status_code == 204 and cancelled.content == b''
    assert client.delete(f'{path}/{a}').json()['code'] == 'REGISTRATION_NOT_FOUND'
    repeated = client.post(path, json={'user_id': a})
    assert repeated.status_code == 201 and repeated.json()['id'] != original.json()['id']
    with engine.connect() as conn:
        assert conn.execute(text('SELECT status, cancelled_at FROM registrations WHERE id=:id'), {'id': original.json()['id']}).one().status == 'cancelled'
        assert conn.scalar(text('SELECT remaining_slots FROM events WHERE id=:id'), {'id': eid}) == 0
    assert {r['user_id'] for r in client.get(path).json()} == {a, b}
    assert_invariant(engine, eid)


def test_lists_and_missing_resources(client, engine):
    assert client.get('/events').json() == []
    eid = event(client)
    uid = user(client)
    assert client.get(f'/events/{eid}').json()['remaining_slots'] == 2
    assert client.get('/events').json()[0]['title'] == 'Workshop'
    assert client.get(f'/events/{eid}/registrations').json() == []
    assert client.get('/events/999').status_code == 404
    assert client.get('/events/999/registrations').json()['code'] == 'EVENT_NOT_FOUND'
    assert client.post('/events/999/registrations', json={'user_id': 999}).json()['code'] == 'EVENT_NOT_FOUND'
    assert client.post(f'/events/{eid}/registrations', json={'user_id': 999}).json()['code'] == 'USER_NOT_FOUND'
    assert client.delete(f'/events/{eid}/registrations/999').json()['code'] == 'USER_NOT_FOUND'
    assert client.delete(f'/events/999/registrations/{uid}').json()['code'] == 'EVENT_NOT_FOUND'
    assert_invariant(engine, eid)


@pytest.mark.parametrize('body', [{'title': ' ', 'capacity': 1}, {'title': 'A', 'capacity': 0}, {'title': 'A', 'capacity': True}, {'title': 'A', 'capacity': 1, 'remaining_slots': 1}])
def test_invalid_api_write_has_no_effect(client, engine, body):
    response = client.post('/events', json=body)
    assert response.status_code == 422 and response.json()['code'] == 'VALIDATION_ERROR'
    with engine.connect() as conn:
        assert conn.scalar(text('SELECT count(*) FROM events')) == 0


def test_bad_paths_and_registration_body(client, engine):
    eid = event(client)
    assert client.get('/events/0').status_code == 422
    assert client.post(f'/events/{eid}/registrations', json={'user_id': '1'}).status_code == 422
    assert client.delete(f'/events/{eid}/registrations/0').status_code == 422
    assert_invariant(engine, eid)


def test_health_docs(client, engine):
    assert client.get('/health').json() == {'status': 'ok', 'database': 'ok'}
    assert client.get('/docs').status_code == 200
    assert len(client.get('/openapi.json').json()['paths']) == 6
