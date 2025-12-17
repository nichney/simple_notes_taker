import pytest
from fastapi.testclient import TestClient
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    async_sessionmaker,
    AsyncSession,
)

from main import app, get_db
from models import Base


DATABASE_URL = "sqlite+aiosqlite:///:memory:"

@pytest.fixture(scope="module")
async def async_engine():
    engine = create_async_engine(DATABASE_URL)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all) 
    
    yield engine
    await engine.dispose()

@pytest.fixture(scope="function")
async def db_session_rollback(async_engine):
    async with async_engine.connect() as connection:
        async with connection.begin() as transaction:
            async_session = async_sessionmaker(
                connection, 
                expire_on_commit=False, 
                class_=AsyncSession
            )
            async with async_session() as session:
                yield session
                
            await transaction.rollback()

@pytest.fixture
async def override_get_db(db_session_rollback):
    """Override db with test session"""
    def override_db_dependency():
        yield db_session_rollback 

    app.dependency_overrides[get_db] = override_db_dependency
    yield app.dependency_overrides[get_db]

    app.dependency_overrides.pop(get_db)

@pytest.fixture
def client(override_get_db):
    return TestClient(app)

@pytest.fixture
def registered_user(client):
    """Register user"""
    response = client.post(
        '/api/v2/auth/register',
        json={'email': 'test@login.com', 'password': 'test_password'}
    )

    return {
        'email': 'test@login.com', 
        'password': 'test_password',
        'id': response.json()['id']
    }


def test_register(client):
    response = client.post(
        '/api/v2/auth/register',
        json={'email': 'sample@email.com', 'password': 'sample_password'}
    )
    assert response.status_code == 201
    assert response.json()['id'] is not None
    assert response.json()['email'] == 'sample@email.com'

def test_register_fail(client, registered_user):
    response = client.post(
        '/api/v2/auth/register',
        json={'email': registered_user['email'], 'password': registered_user['password']}
    )
    assert response.status_code == 409
    assert "already exists" in response.json()['detail']

def test_register_empty_password(client):
    response = client.post(
        '/api/v2/auth/register',
        json={'email': 'sample@email.com', 'password': ''}
    )
    assert response.status_code == 422
    
def test_register_invalid_email(client):
    response = client.post(
        '/api/v2/auth/register',
        json={'email': 'not an email', 'password': '12345678'}
    )
    assert response.status_code == 422


def test_login(client, registered_user):
    response = client.post(
        '/api/v2/auth/login',
        json={'email': registered_user['email'], 'password': registered_user['password']}
    )
    assert response.status_code == 200
    assert response.json()['access_token'] is not None
    assert response.json()['refresh_token'] is not None

def test_login_invalid_password(client, registered_user):
    response = client.post(
        '/api/v2/auth/login',
        json={'email': registered_user['email'], 'password': 'another_password'}
    )
    assert response.status_code == 401

def test_login_invalid_email(client):
    response = client.post(
        '/api/v2/auth/login',
        json={'email': 'nouser@sample.com', 'password': 'sample_password'}
    )
    assert response.status_code == 401