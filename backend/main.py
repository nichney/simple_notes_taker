from fastapi import FastAPI, Depends, Form
import database
from session import engine, SessionLocal
from models import Base

app = FastAPI()

async def get_db():
    async with SessionLocal() as db:
        yield db

@app.on_event('startup')
async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

@app.get('/api/v1/{user_id}/{note_id}')
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


@app.delete('/api/v1/{user_id}/{note_id}')
async def api_delete(user_id: int, note_id: int, db=Depends(get_db)):
    try:
        succeed = await database.delete_note(user_id, note_id)
        return {'status': succeed}
    except Exception as e:
        return {'error_message': e}


@app.post('/api/v1/{user_id}/create')
async def api_create(user_id: int, note_text: str = Form(...), note_date: str = Form(...), db=Depends(get_db)):
    new_id = await database.new_note(db, user_id, note_text, note_date)
    return {
        'user_id': user_id,
        'note_id': new_id
    }

@app.put('/api/v1/{user_id}/{note_id}/update')
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
