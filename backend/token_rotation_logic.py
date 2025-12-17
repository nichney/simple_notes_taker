import os

REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv('REFRESH_TOKEN_EXPIRE_DAYS'))

async def save_refresh_token(redis, refresh_token: str, user_id: int):
    await redis.set(
        f"refresh:{refresh_token}",
        user_id,
        ex=REFRESH_TOKEN_EXPIRE_DAYS*24*60*60,
    )


async def is_refresh_token_valid(redis, refresh_token: str) -> bool:
    return await redis.exists(f"refresh:{refresh_token}") == 1


async def delete_refresh_token(redis, refresh_token: str):
    await redis.delete(f"refresh:{refresh_token}")