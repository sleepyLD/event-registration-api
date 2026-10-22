import os
import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import text
from app.db.connection import build_engine
from app.main import app


@pytest.fixture(scope='session')
def engine():
    if os.getenv('ALLOW_TEST_DATABASE') != '1' or os.getenv('POSTGRES_DB') != 'event_registration_test':
        pytest.exit('Refusing DB tests: use compose.test.yaml isolated environment.', returncode=2)
    engine = build_engine()
    with engine.connect() as conn:
        assert conn.scalar(text('SELECT current_database()')) == 'event_registration_test'
        assert conn.scalar(text('SELECT current_user')) == 'event_test'
    command.upgrade(Config('alembic.ini'), 'head')
    yield engine
    engine.dispose()


@pytest.fixture(autouse=True)
def clean_database(request):
    # Pure schema-validation unit tests never request a database.
    if 'engine' not in request.fixturenames:
        yield
        return
    engine = request.getfixturevalue('engine')
    with engine.begin() as conn:
        conn.execute(text('TRUNCATE registrations, events, users RESTART IDENTITY'))
    yield


@pytest.fixture
def client(engine):
    with TestClient(app) as client:
        yield client
