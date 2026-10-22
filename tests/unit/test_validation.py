import pytest
from pydantic import ValidationError
from app.schemas import EventCreate, UserCreate, RegistrationCreate


@pytest.mark.parametrize('capacity', [0, -1, 10001, True, '2', 1.5, None])
def test_capacity_rejects_invalid_values(capacity):
    with pytest.raises(ValidationError):
        EventCreate(title='Workshop', capacity=capacity)


@pytest.mark.parametrize('body', [{'name': ' '}, {'name': None}, {'name': 5}, {'name': 'A', 'admin': True}, {}])
def test_invalid_users(body):
    with pytest.raises(ValidationError):
        UserCreate(**body)


def test_normalization_and_limits():
    assert UserCreate(name=' Alice ').name == 'Alice'
    assert EventCreate(title=' X ', capacity=10000).title == 'X'
    with pytest.raises(ValidationError):
        RegistrationCreate(user_id=False)
