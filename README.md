# Simple Notes Taker

Backend-сервис заметок на FastAPI с PostgreSQL и Redis, полностью запускаемый через Docker.

Проект намеренно разделён на:

* `database` — PostgreSQL + Redis
* `backend` — FastAPI

Это позволяет развернуть бэкенд и базу данных на разных машинах.

## Функционал
* Регистрация и аутентификация по JWT
* CRUD операции для заметок
* Асинхронная работа с БД (SQLAlchemy)
## Требования

* Docker >= 24
* Docker Compose

Backend использует `Python 3.10`.

`Python > 3.10` в данный момент не поддерживается из-за зависимостей `passlib / bcrypt`.


## Структура проекта

```
.
├── backend        # FastAPI приложение
│   ├── Dockerfile
│   ├── docker-compose.yml
│   ├── .env.example
│   └── ...
└── database       # PostgreSQL + Redis
    └── docker-compose.yml
```

## Запуск

### 1) Клонирование репозитория

```bash
git clone https://github.com/nichney/simple_notes_taker.git
cd simple_notes_taker
```
### 2) Создание Docker-сети

При запуске бэкенда и базы данных на одной машине потребуется создать сеть, чтобы компоненты могли связаться:

```bash
docker network create notes_net
```
### 3) Запуск базы данных и Redis

```bash
cd database
docker compose up -d
```

Будут запущены контейнеры:

* `notes_postgres`
* `notes_redis`

### 4) Настройка backend

```bash
cd ../backend
cp .env.example .env
```

Пример .env, который необходимо отредактировать:

```env
# Database
DATABASE_URL=postgresql+asyncpg://postgres:password@notes_postgres:5432/notesdb

# Redis
REDIS_HOST=notes_redis
REDIS_PORT=6379

# Security
SECRET_KEY=your_secret_key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=30
```
### 5) Запуск backend

```bash
docker compose up --build
```

После успешного запуска:

* API: [http://127.0.0.1:8000](http://127.0.0.1:8000)
* Swagger UI: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

## Остановка сервисов

```bash
# backend
cd backend
docker compose down

# database
cd ../database
docker compose down
```

Данные PostgreSQL и Redis сохраняются в Docker volumes.
