from fastapi import FastAPI, Depends, Form, HTTPException, status
import database
from session import engine, SessionLocal
from models import Base

from schemas import UserRegister, UserOut, NoteCreate, NoteUpdate, NoteOut, StatusOut

app = FastAPI()

async def get_db():
    async with SessionLocal() as db:
        yield db

@app.on_event('startup')
async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

@app.get('/api/v1/{user_id}/{note_id}', deprecated=True)
async def api_read(user_id: int, note_id: int, db=Depends(get_db)):
    try:
        note_date, note_text = await database.get_note(db, user_id, note_id)
        return {
                'user_id': user_id,
                'note_id': note_id,
                'note_date': note_date,
                'note_text': note_text,
                }

    except Exception as e:
        return {'error_message': e}


@app.delete('/api/v1/{user_id}/{note_id}', deprecated=True)
async def api_delete(user_id: int, note_id: int, db=Depends(get_db)):
    try:
        succeed = await database.delete_note(user_id, note_id)
        return {'status': succeed}
    except Exception as e:
        return {'error_message': e}


@app.post('/api/v1/{user_id}/create', deprecated=True)
async def api_create(user_id: int, note_text: str = Form(...), note_date: str = Form(...), db=Depends(get_db)):
    new_id = await database.new_note(db, user_id, note_text, note_date)
    return {
        'user_id': user_id,
        'note_id': new_id
    }

@app.put('/api/v1/{user_id}/{note_id}/update', deprecated=True)
async def api_update(user_id: int, note_id: int, note_text: str, db=Depends(get_db)):
    try:
        succeed = await database.update_note(user_id, note_id, note_text)
        return {
                'user_id': user_id,
                'note_id': note_id,
                'status': succeed,
        }
    except Exception as e:
        return {'error_message': e}


@app.post(
    '/api/v2/auth/register',
    response_model=UserOut,
    status_code=status.HTTP_201_CREATED,
    )
async def api_register(payload: UserRegister,  db=Depends(get_db)):
    try:
        user = await database.create_user(db, payload.email, payload.password)
        return user
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
async def api_create_note_v2(payload: NoteCreate, db=Depends(get_db)):
    user_id = 1  # TODO: JWT

    note_id = await database.new_note(
        db,
        user_id=user_id,
        note_text=payload.note_text,
        note_date=str(payload.note_date),
    )

    return {
        "note_id": note_id,
        "note_text": payload.note_text,
        "note_date": payload.note_date,
    }


@app.get(
    '/api/v2/{note_id}',
    response_model=NoteOut,
)
async def api_read_note_v2(note_id: int,  db=Depends(get_db)):
    user_id = 1  # TODO: JWT

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
async def api_update_note_v2(note_id: int, payload: NoteUpdate, db=Depends(get_db)):
    user_id = 1 # TODO: JWT

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
async def api_delete_note_v2(note_id: int, db=Depends(get_db)):
    user_id = 1 # TODO: JWT

    try:
        result = await database.delete_note(db, user_id, note_id)
        return {"status": result}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))