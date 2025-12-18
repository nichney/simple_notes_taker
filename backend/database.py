from sqlalchemy import select, func, delete, update
from sqlalchemy.orm import Session
from models import User, Note
from security import hash_password


async def get_user_by_email(db, email: str):
    stmt = select(User).where(User.user_email == email)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def get_user_by_id(db, user_id: int):
    stmt = select(User).where(User.user_id == user_id)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def create_user(db, email: str, password: str) -> User:
    # Check if user exists by email
    stmt = select(User).where(User.user_email == email)
    res = await db.execute(stmt)

    if res.scalar_one_or_none():
        raise ValueError("User already exists")

    user = User(
        user_email=email,
        user_password=hash_password(password),
    )

    db.add(user)
    await db.commit()
    await db.refresh(user)

    return user


async def new_note(db, user_id: int, text: str, date: str):
    #await ensure_user(db, user_id)

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
    #await ensure_user(db, user_id)

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
    #await ensure_user(db, user_id)

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
    #await ensure_user(db, user_id)

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
