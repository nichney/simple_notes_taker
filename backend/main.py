from typing import Annotated
import os
from fastapi import FastAPI, Depends, Form, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jwt.exceptions import InvalidTokenError
import database
from session import engine, SessionLocal
from models import Base
from security import verify_password, create_access_token, create_refresh_token, decode_token

from schemas import (
    UserRegister, UserOut, NoteCreate, 
    NoteUpdate, NoteOut, StatusOut, 
    TokenResponse, LoginSchema,
    TokenRotation,
)
from token_rotation_logic import (
    save_refresh_token,
    is_refresh_token_valid,
    delete_refresh_token,
)

import redis.asyncio as redis


app = FastAPI()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v2/auth/login")

async def get_db():
    async with SessionLocal() as db:
        yield db

async def get_redis():
    REDIS_HOST = os.getenv('REDIS_HOST')
    REDIS_PORT = int(os.getenv('REDIS_PORT'))
    redis_client = redis.Redis(
        host=REDIS_HOST,
        port=REDIS_PORT,
        decode_responses=True,
    )
    try: 
        yield redis_client
    finally:
        await redis_client.close()


async def get_current_user(token: str = Depends(oauth2_scheme), db = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_token(token)
        user_id = payload.get('sub')
        if payload.get('type') != 'access':
            raise credentials_exception
        if user_id is None:
            raise credentials_exception
    except InvalidTokenError:
        raise credentials_exception
    user = await database.get_user_by_id(db, int(user_id))
    if user is None:
        raise credentials_exception
    return user
        

@app.on_event('startup')
async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


@app.post(
    'api/v2/auth/logout',
    status_code=status.HTTP_204_NO_CONTENT,
)
async def api_logout(data:TokenRotation, redis=Depends(get_redis)):
    token_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid refresh token",
    )
    try:
        payload = decode_token(data.refresh_token)
        try:
            user_id = int(payload.get("sub"))
        except (TypeError, ValueError):
            raise token_exception
        if payload.get('type') != 'refresh':
            raise token_exception
    except InvalidTokenError:
        raise token_exception

    if not await is_refresh_token_valid(redis, data.refresh_token):
        raise token_exception

    await delete_refresh_token(redis, data.refresh_token)


@app.post(
    '/api/v2/auth/refresh',
    response_model=TokenResponse
)
async def api_refresh(data: TokenRotation, redis=Depends(get_redis)):
    token_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid refresh token",
    )
    try:
        payload = decode_token(data.refresh_token)
        try:
            user_id = int(payload.get("sub"))
        except (TypeError, ValueError):
            raise token_exception
        if payload.get('type') != 'refresh':
            raise token_exception
    except InvalidTokenError:
        raise token_exception

    if not await is_refresh_token_valid(redis, data.refresh_token):
        raise token_exception

    await delete_refresh_token(redis, data.refresh_token)

    new_access = create_access_token(user_id)
    new_refresh = create_refresh_token(user_id)

    await save_refresh_token(redis, new_refresh, user_id)

    return {
        'access_token': new_access,
        'refresh_token': new_refresh,
        'token_type': 'bearer',
    }


@app.post(
    '/api/v2/auth/login',
    response_model=TokenResponse,
)
async def api_login(data: LoginSchema, db=Depends(get_db), redis=Depends(get_redis)):
    user = await database.get_user_by_email(db, data.email)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Incorrect email or password')
    if not verify_password(data.password, user.user_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Incorrect email or password')

    new_access = create_access_token(user.user_id)
    new_refresh = create_refresh_token(user.user_id)
    await save_refresh_token(redis, new_refresh, user.user_id)

    return {
        'access_token': new_access,
        'refresh_token': new_refresh,
        'token_type': 'bearer',
    }

@app.post(
    '/api/v2/auth/register',
    response_model=UserOut,
    status_code=status.HTTP_201_CREATED,
    )
async def api_register(payload: UserRegister,  db=Depends(get_db)):
    try:
        user = await database.create_user(db, payload.email, payload.password)
        return {
            'id': user.user_id,
            'email': user.user_email,
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        )


@app.post(
    '/api/v2/create',
    response_model=NoteOut,
    status_code=status.HTTP_201_CREATED,
)
async def api_create_note_v2(payload: NoteCreate, db=Depends(get_db), user=Depends(get_current_user)):
    user_id = user.user_id

    note_id = await database.new_note(
        db,
        user_id=user_id,
        text=payload.note_text,
        date=str(payload.note_date),
    )

    return {
        "note_id": note_id,
        "note_text": payload.note_text,
        "note_date": payload.note_date,
    }


@app.get(
    '/api/v2/{note_id}',
    response_model=NoteOut,
    status_code=200
)
async def api_read_note_v2(note_id: int,  db=Depends(get_db), user=Depends(get_current_user)):
    user_id = user.user_id

    try:
        note_date, note_text = await database.get_note(db, user_id, note_id)
        return {
            "note_id": note_id,
            "note_text": note_text,
            "note_date": note_date,
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.put(
    '/api/v2/{note_id}',
    response_model=StatusOut,
)
async def api_update_note_v2(note_id: int, payload: NoteUpdate, db=Depends(get_db), user=Depends(get_current_user)):
    user_id = user.user_id

    try:
        result = await database.update_note(
            db,
            user_id,
            note_id,
            payload.note_text,
        )
        return {"status": result}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.delete(
    '/api/v2/{note_id}',
    response_model=StatusOut,
)
async def api_delete_note_v2(note_id: int, db=Depends(get_db), user=Depends(get_current_user)):
    user_id = user.user_id

    try:
        result = await database.delete_note(db, user_id, note_id)
        return {"status": result}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))