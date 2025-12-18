# main.py
Global variables:
- `app`: `FastAPI` instance
- `oauth2_scheme`: `OAuth2PasswordBearer` instance
---
Help methods:
- `get_db()` yields database `SessionLocal()` from module `session`
- `get_redis()` yields redis database, uses `redis.asyncio`
- `get_current_user(token = Depends(oauth2_scheme), db = Depends(get_db))` validates access token and call `get_user_by_id(...)` from `database` module. Returns `User` instance from `models` module. Raises as error `HTTPException` if token validation failed 
---
Methods, associated with `app`
- `@app.on_event('startup')`:
  - `startup()` runs async engine which connects to Postgres
- `@app.post`:
  - `api_logout(data:TokenRotation, redis=Depends(get_redis))` validates refresh token from user, retrieves it from redis database if it's valid. Uses `delete_refresh_token(...)` and `is_refresh_token_valid(...)` from `token_rotation_logic` module. Uses `decode_token(...)` from `security` module
  - `api_refresh(data: TokenRotation, redis=Depends(get_redis))` validates refresh token, generates and returns new refresh and access tokens. Uses `decode_token(...)`, `create_access_token(...)` and `create_refresh_token(...)` from `security` module, `is_refresh_token_valid(...)`, `delete_refresh_token(...)`, `save_refresh_token(...)` from `token_rotation_logic` module
  - `api_login(data: LoginSchema, db=Depends(get_db), redis=Depends(get_redis))` gets user from Postgres, creates and returns access and refresh tokens. Uses `get_user_by_email(...)` from `database` module, `verify_password(...)`, `create_access_token(...)` and `create_refresh_token(...)` from `security` module, `save_refresh_token(...)` from `token_rotation_logic` module
  - `api_register(payload: UserRegister,  db=Depends(get_db))` creates a new user by email and password, raises an `HTTPException` if user already exists. Uses `create_user(...)` from `database` module
  - `api_create_note_v2(payload: NoteCreate, db=Depends(get_db), user=Depends(get_current_user))` creates new note for logged in users. Returns note_id, note_text and note_date for created note. Uses `new_note(...)` from `database` module
- `@app.get`:
  - `api_read_note_v2(note_id: int,  db=Depends(get_db), user=Depends(get_current_user))` returns note id, note text and note date of requested note for logged in users. Raises an error if there is no requested note. Uses `get_note(...)` from `database` module
- `@app.put`:
  - `api_update_note_v2(note_id: int, payload: NoteUpdate, db=Depends(get_db), user=Depends(get_current_user))` updates existing note text for logged in users. Raises an error if there is no requested note. Uses `update_note(...)` from `database` module.
- `@app.delete`:
  - `api_delete_note_v2(note_id: int, db=Depends(get_db), user=Depends(get_current_user))` deletes existing note for logged in users, raises an error if there is no requested note. Uses `delete_note(...)` from `database` module.

# database.py
Methods:
- `get_user_by_email(db, email: str)` takes user email, returns `User` instance from `models` module with such email. Uses `sqlalchemy`
- ` get_user_by_id(db, user_id: int)` takes user id, returns `User` instance from `models` module for user with same id. Uses `sqlalchemy`
- `create_user(db, email: str, password: str) -> User:` writes to database email and hashed password, raises `ValueError` if email is already in base. Returns `User` instance from `models` module with such email. Uses `sqlalchemy`
- `new_note(db, user_id: int, text: str, date: str)` searches for maximum id note number in database, then write to database new note with id increased on 1. Returns id of new note. Uses `sqlalchemy`
- `get_note(db, user_id: int, note_id: int)` selects note from database by user id and note id. Raises an error if there is no note with given id. Uses `sqlalchemy`. Returns `return note.note_date, note.note_text`
- `delete_note(db, user_id: int, note_id: int)` selects note from database by user id and note id, raises an error if there is no note with given id. Then deletes note from database. Uses `sqlalchemy`, returns `True`
- `update_note(db, user_id: int, note_id: int, note_text: str)` selects note, raises an error if there is no note with given id. Updates note text. Uses `sqlalchemy`, returns `True`

# models.py
global variables:
- `Base`: `declarative_base()` result from `sqlalchemy.orm` module
classes:
- `User(Base)`:
  - `__tablename__ = "users"`
  - `user_id = Column(Integer, primary_key=True)`
  - `user_email = Column(String, nullable=False, unique=True, index=True)`
  - `user_password = Column(String, nullable=False) # hashed password`
  - `created_at = Column(DateTime(timezone=True), server_default=func.now())`
- `Note(Base)`:
  - `__tablename__ = "notes"`

  - `user_id = Column(Integer, ForeignKey("users.user_id"), primary_key=True)`
  - `note_id = Column(Integer, primary_key=True)`
  - `note_date = Column(String)`
  - `note_text = Column(Text)`
  - `user = relationship("User")`

# schemas.py
All classes are childs of `BaseModel` from module `pydantic`
classes:
- `UserRegister`:
  - `email: EmailStr`
  - `password: str = Field(min_length=8, max_length=128)`
- `UserOut`:
  - `id: int`
  - `email: EmailStr`
- `NoteCreate`:
  - `note_text: str`
  - `note_date: date`
- `NoteUpdate`:
  - `note_text: str`
- `NoteOut`:
  - `note_id: int`
  - `note_text: str`
  - `note_date: date`
- `StatusOut`:
  - `status: bool`
- `LoginSchema`:
  - `email: str`
  - `password: str`
- `TokenResponse`:
  - `access_token: str`
  - `refresh_token: str`
  - `token_type: str`
- `TokenRotation`:
  - `refresh_token: str`

# security.py
Global variables:
- `pwd_context` instance of `CryptContext` from module `passlib.context`
- `SECRET_KEY` gets it's variable from env with `os.getenv(...)`. It is a signature key for JWT.
- `ALGORITHM` gets it's variable from env with `os.getenv(...)`. It is an algorithm for JWT encoding and decoding
- `ACCESS_TOKEN_EXPIRE_MINUTES: int` gets it's variable from env with `os.getenv(...)`.
- `REFRESH_TOKEN_EXPIRE_DAYS: int` gets it's variable from env with `os.getenv(...)`.
---
Methods:
- `hash_password(password: str) -> str:` calls `pwd_context.hash(...)`
- `verify_password(password: str, hashed: str) -> bool:` calls `pwd_context.verify(...)`
- `create_access_token(user_id: int) -> str:` uses `datetime` and `jwt` modules
- `create_refresh_token(user_id: int) -> str:` uses `datetime` and `jwt` modules. The difference from `create_access_token(...)` if that it uses `REFRESH_TOKEN_EXPIRE_DAYS` instead of `ACCESS_TOKEN_EXPIRE_MINUTES` on token creation.
- `decode_token(token: str) -> dict:` calls `jwt.decode(...)`

# session.py
Global variables:
- `DATABASE_URL` gets it's variable from env with `os.getenv(...)`.
- `engine` is a result for `create_async_engine(...)` from `sqlalchemy.ext.asyncio` module.
- `SessionLocal` is a result for `async_sessionmaker` from `sqlalchemy.ext.asyncio` module.

# token_rotation_logic.py
Global variabled:
- `REFRESH_TOKEN_EXPIRE_DAYS` gets it's variable from env with `os.getenv(...)`.
---
Methods:
- `save_refresh_token(redis, refresh_token: str, user_id: int):` calls `set` method for `redis` instance, stores refresh token and user_id there.
- `is_refresh_token_valid(redis, refresh_token: str) -> bool:` calls `exists` method for `redis` instance
- `delete_refresh_token(redis, refresh_token: str):` calls `delete` method for `redis` instance