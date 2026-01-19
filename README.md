# Simple Notes Taker

Backend-сервис заметок, полностью запускаемый через Docker.

Стек:
 * FastAPI
 * PostgreSQL
 * Redis

## Функционал
* Регистрация и аутентификация по JWT
* CRUD операции для заметок
* Асинхронная работа с БД (SQLAlchemy)
## Требования

* Docker >= 24
* Docker Compose

Backend использует `Python 3.10`.

`Python > 3.10` в данный момент не поддерживается из-за зависимостей `passlib / bcrypt`.

## Запуск

### 1) Клонирование репозитория

```bash
git clone https://github.com/nichney/simple_notes_taker.git
cd simple_notes_taker
```

### 2) Настройка backend

```bash
cp .env.example .env
vim .env
```

Пример .env, который необходимо отредактировать:

```env
### For backend service
# Database url for backend service
DATABASE_URL=postgresql+asyncpg://postgres:password@notes_postgres:5432/notesdb

# Redis
REDIS_HOST=notes_redis
REDIS_PORT=6379

# Security
SECRET_KEY=6749a721572bd937a4e9e4a3ce412517ba28916d7280d2f6b1b150d5503f49fd
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=30

### For DB service
POSTGRES_DB=notesdb
POSTGRES_USER=postgres
POSTGRES_PASSWORD=password

```
Сгенерировать SECRET_KEY можно командой `openssl rand -hex 32`
### 3) Запуск backend

```bash
docker compose up -d --build 
```

После успешного запуска:

* API: [http://127.0.0.1:8000](http://127.0.0.1:8000)
* Swagger UI: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

## Остановка сервисов

```bash
docker compose down
```

Данные PostgreSQL и Redis сохраняются в Docker volumes.
