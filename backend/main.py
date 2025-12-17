from typing import Annotated
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
)

app = FastAPI()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v2/auth/login")

async def get_db():
    async with SessionLocal() as db:
        yield db


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
    '/api/v2/auth/login',
    response_model=TokenResponse,
)
async def api_login(data: LoginSchema, db=Depends(get_db)):
    user = await database.get_user_by_email(db, data.email)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Incorrect email or password')
    if not verify_password(data.password, user.user_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Incorrect email or password')

    return {
        'access_token': create_access_token(user.user_id),
        'refresh_token': create_refresh_token(user.user_id),
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