import pytest
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    async_sessionmaker,
    AsyncSession,
)

from database import (
    get_user_by_email, create_user, new_note, get_note,
    delete_note, update_note, get_user_by_id
)
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
async def sample_user(db_session_rollback: AsyncSession):
    user = await create_user(
        db=db_session_rollback,
        email='sample@user.com',
        password='test_pass',
    )
    return user
    
@pytest.fixture
async def sample_note_data(db_session_rollback: AsyncSession, sample_user):
    note_id = await new_note(
        db=db_session_rollback,
        user_id=sample_user.user_id,
        text='Sample Note Text',
        date='2025-12-16',
    )
    return note_id, sample_user.user_id


class TestDatabase:

    @pytest.mark.asyncio
    async def test_create_user(self, db_session_rollback: AsyncSession):
        user = await create_user(
            db=db_session_rollback,
            email='test@email.com',
            password='12345678',
        )
        assert user.user_id is not None
        assert user.user_email == 'test@email.com'

    @pytest.mark.asyncio
    async def test_create_note(self, db_session_rollback: AsyncSession, sample_user):
        note_id = await new_note(
            db=db_session_rollback,
            user_id=sample_user.user_id,
            text='hello world',
            date='2025-12-16',
        )
        assert note_id is not None

    @pytest.mark.asyncio
    async def test_get_note(self, db_session_rollback: AsyncSession, sample_note_data):
        note_id, user_id = sample_note_data
        
        date, text = await get_note(
            db=db_session_rollback,
            user_id=user_id,
            note_id=note_id,
        )
        assert text == 'Sample Note Text'
        assert date == '2025-12-16'

    @pytest.mark.asyncio
    async def test_update_note(self, db_session_rollback: AsyncSession, sample_note_data):
        note_id, user_id = sample_note_data
        
        result = await update_note(
            db=db_session_rollback,
            user_id=user_id,
            note_id=note_id,
            note_text='updated text',
        )

        assert result

        date, text = await get_note(db_session_rollback, user_id, note_id)
        assert text == 'updated text'

    @pytest.mark.asyncio
    async def test_delete_note(self, db_session_rollback: AsyncSession, sample_note_data):
        note_id, user_id = sample_note_data
        
        result = await delete_note(
            db=db_session_rollback,
            user_id=user_id,
            note_id=note_id,
        )

        assert result

    @pytest.mark.asyncio
    async def test_get_deleted_note_raises(self, db_session_rollback: AsyncSession, sample_user):
        with pytest.raises(ValueError):
            await get_note(
                db=db_session_rollback,
                user_id=sample_user.user_id,
                note_id=999,
            )

    @pytest.mark.asyncio
    async def test_create_user_duplicate_email_raises(self, db_session_rollback: AsyncSession, sample_user):
        with pytest.raises(ValueError) as exc:
            await create_user(
                db=db_session_rollback,
                email='sample@user.com',
                password='another_password',
            )
        assert 'already exists' in str(exc.value)

    @pytest.mark.asyncio
    async def test_update_missing_note_raises(self, db_session_rollback: AsyncSession, sample_user):
        with pytest.raises(ValueError) as exc:
            await update_note(
                db=db_session_rollback,
                user_id=sample_user.user_id,
                note_id=999,
                note_text='should fail',
            )

        assert 'does not exist' in str(exc.value)

    @pytest.mark.asyncio
    async def test_get_user_by_email(self, db_session_rollback: AsyncSession, sample_user):
        user = await get_user_by_email(
            db=db_session_rollback,
            email=sample_user.user_email,
        )
        assert user is not None
        assert user.user_email == 'sample@user.com'

    @pytest.mark.asyncio
    async def test_get_user_by_id(self, db_session_rollback: AsyncSession, sample_user):
        user = await get_user_by_id(
            db=db_session_rollback,
            user_id=sample_user.user_id,
        )
        assert user is not None
        assert user.user_id == sample_user.user_id