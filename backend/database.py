from sqlalchemy import select, func, delete, update
from sqlalchemy.orm import Session
from models import User, Note

async def ensure_user(db, user_id: int):
    user = await db.get(User, user_id)
    if not user:
        user = User(user_id=user_id)
        db.add(user)
        await db.commit()

async def new_note(db, user_id: int, text: str, date: str):
    await ensure_user(db, user_id)

    # max(note_id)
    stmt = select(func.max(Note.note_id)).where(Note.user_id == user_id)
    result = await db.execute(stmt)
    last_id = result.scalar() or 0
    new_id = last_id + 1

    note = Note(
        user_id=user_id,
        note_id=new_id,
        note_text=text,
        note_date=date,
    )

    db.add(note)
    await db.commit()
    return new_id


async def get_note(db, user_id: int, note_id: int):
    await ensure_user(db, user_id)

    stmt = (
        select(Note)
        .where(Note.user_id == user_id)
        .where(Note.note_id == note_id)
    )

    result = await db.execute(stmt)
    note = result.scalar_one_or_none()

    if not note:
        raise ValueError(f"Note {note_id} does not exist for user {user_id}")

    return note.note_date, note.note_text


async def delete_note(db, user_id: int, note_id: int):
    await ensure_user(db, user_id)

    stmt_check = (
        select(Note)
        .where(Note.user_id == user_id)
        .where(Note.note_id == note_id)
    )
    res = await db.execute(stmt_check)
    note = res.scalar_one_or_none()

    if not note:
        raise ValueError(f"Note {note_id} does not exist for user {user_id}")

    stmt_delete = (
        delete(Note)
        .where(Note.user_id == user_id)
        .where(Note.note_id == note_id)
    )
    await db.execute(stmt_delete)
    await db.commit()

    return True

async def update_note(db, user_id: int, note_id: int, note_text: str):
    await ensure_user(db, user_id)

    stmt_check = (
        select(Note)
        .where(Note.user_id == user_id)
        .where(Note.note_id == note_id)
    )
    res = await db.execute(stmt_check)
    note = res.scalar_one_or_none()

    if not note:
        raise ValueError(f"Note {note_id} does not exist for user {user_id}")
    
    stmt_update = (
        update(Note)
        .where(Note.user_id == user_id)
        .where(Note.note_id == note_id)
        .values(note_text=note_text)
    )
    await db.execute(stmt_update)
    await db.commit()

    return True
