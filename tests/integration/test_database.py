import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import text, inspect
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from app.services.registrations import change_registration
from tests.integration.test_api import event, user, assert_invariant


@pytest.mark.parametrize('sql', [
    "INSERT INTO events(title,capacity,remaining_slots) VALUES ('X',0,0)",
    "INSERT INTO events(title,capacity,remaining_slots) VALUES ('X',10001,1)",
    "INSERT INTO events(title,capacity,remaining_slots) VALUES ('X',1,-1)",
    "INSERT INTO events(title,capacity,remaining_slots) VALUES ('X',1,2)",
    "INSERT INTO users(name) VALUES (' ')",
    "INSERT INTO registrations(event_id,user_id,status) VALUES (999,999,'active')",
])
def test_constraints(engine, sql):
    with pytest.raises(IntegrityError), engine.begin() as conn:
        conn.execute(text(sql))


def test_partial_unique_and_status_constraints(client, engine):
    eid, uid = event(client), user(client)
    path = f'/events/{eid}/registrations'
    assert client.post(path, json={'user_id': uid}).status_code == 201
    invalids = [
        "INSERT INTO registrations(event_id,user_id,status) VALUES (:e,:u,'active')",
        "INSERT INTO registrations(event_id,user_id,status) VALUES (:e,:u,'cancelled')",
        "INSERT INTO registrations(event_id,user_id,status) VALUES (:e,:u,'unknown')",
    ]
    for sql in invalids:
        with pytest.raises(IntegrityError), engine.begin() as conn:
            conn.execute(text(sql), {'e': eid, 'u': uid})
    assert client.delete(f'{path}/{uid}').status_code == 204
    assert client.post(path, json={'user_id': uid}).status_code == 201
    assert_invariant(engine, eid)


def test_failure_rolls_back_registration_and_cancellation(client, engine):
    eid, uid = event(client), user(client)
    with pytest.raises(RuntimeError), Session(engine) as session, session.begin():
        change_registration(session, eid, uid)
        raise RuntimeError('simulated failure after flush')
    with engine.connect() as conn:
        assert conn.scalar(text('SELECT count(*) FROM registrations')) == 0
        assert conn.scalar(text('SELECT remaining_slots FROM events WHERE id=:e'), {'e': eid}) == 2
    assert client.post(f'/events/{eid}/registrations', json={'user_id': uid}).status_code == 201
    with pytest.raises(RuntimeError), Session(engine) as session, session.begin():
        change_registration(session, eid, uid, cancel=True)
        raise RuntimeError('simulated cancellation failure after flush')
    with engine.connect() as conn:
        row = conn.execute(text('SELECT status, cancelled_at FROM registrations')).one()
        assert row.status == 'active' and row.cancelled_at is None
    assert_invariant(engine, eid)


def test_migration_roundtrip_on_disposable_database(engine):
    # conftest refuses every database except the explicit isolated test DB.
    config = Config('alembic.ini')
    command.downgrade(config, 'base')
    assert 'events' not in inspect(engine).get_table_names()
    command.upgrade(config, 'head')
    assert {'events', 'users', 'registrations'} <= set(inspect(engine).get_table_names())
    command.check(config)
