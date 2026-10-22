from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
import pytest
from tests.integration.test_api import event, user, assert_invariant


def parallel(items, fn):
    barrier = Barrier(len(items))
    def call(item):
        barrier.wait(timeout=15)
        return fn(item)
    with ThreadPoolExecutor(max_workers=len(items)) as pool:
        return list(pool.map(call, items))


@pytest.mark.parametrize('capacity', [1, 5])
def test_different_users_cannot_oversell(client, engine, capacity):
    eid = event(client, capacity)
    users = [user(client, f'U{i}') for i in range(20)]
    responses = parallel(users, lambda uid: client.post(f'/events/{eid}/registrations', json={'user_id': uid}))
    assert Counter(r.status_code for r in responses) == {201: capacity, 409: 20-capacity}
    assert all(r.json()['code'] == 'EVENT_FULL' for r in responses if r.status_code == 409)
    assert_invariant(engine, eid)


def test_duplicate_registration_and_cancellation(client, engine):
    eid, uid = event(client, 10), user(client)
    path = f'/events/{eid}/registrations'
    responses = parallel(range(10), lambda _: client.post(path, json={'user_id': uid}))
    assert Counter(r.status_code for r in responses) == {201: 1, 409: 9}
    assert all(r.json()['code'] == 'ALREADY_REGISTERED' for r in responses if r.status_code == 409)
    responses = parallel(range(10), lambda _: client.delete(f'{path}/{uid}'))
    assert Counter(r.status_code for r in responses) == {204: 1, 404: 9}
    assert all(r.json()['code'] == 'REGISTRATION_NOT_FOUND' for r in responses if r.status_code == 404)
    assert_invariant(engine, eid)


def test_mixed_registration_and_cancellation(client, engine):
    eid = event(client, 5)
    users = [user(client, f'M{i}') for i in range(10)]
    path = f'/events/{eid}/registrations'
    for uid in users[:5]:
        assert client.post(path, json={'user_id': uid}).status_code == 201
    operations = [('cancel', uid) for uid in users[:5]] + [('register', uid) for uid in users[5:]]
    def perform(op):
        kind, uid = op
        return client.delete(f'{path}/{uid}') if kind == 'cancel' else client.post(path, json={'user_id': uid})
    responses = parallel(operations, perform)
    assert all(r.status_code in (201, 204, 409) for r in responses)
    assert_invariant(engine, eid)
