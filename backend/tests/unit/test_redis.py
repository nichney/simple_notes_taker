import pytest

from token_rotation_logic import (
    save_refresh_token,
    is_refresh_token_valid,
    delete_refresh_token,
)

class FakeRedis:
    def __init__(self):
        self.storage = {}

    async def set(self, key, value, ex=None):
        self.storage[key] = value

    async def exists(self, key):
        return 1 if key in self.storage else 0

    async def delete(self, key):
        self.storage.pop(key, None)


@pytest.mark.asyncio
async def test_save_refresh_token():
    redis = FakeRedis()
    token = 'refresh123'
    user_id = 42

    await save_refresh_token(redis, token, user_id)

    assert redis.storage[f'refresh:{token}'] == user_id


@pytest.mark.asyncio
async def test_is_refresh_token_valid_true():
    redis = FakeRedis()
    token = 'refresh123'

    redis.storage[f'refresh:{token}'] = 42

    assert await is_refresh_token_valid(redis, token) is True


@pytest.mark.asyncio
async def test_is_refresh_token_valid_false():
    redis = FakeRedis()
    token = 'refresh123'

    assert await is_refresh_token_valid(redis, token) is False


@pytest.mark.asyncio
async def test_delete_refresh_token():
    redis = FakeRedis()
    token = 'refresh123'

    redis.storage[f'refresh:{token}'] = 42

    await delete_refresh_token(redis, token)

    assert f'refresh:{token}' not in redis.storage
