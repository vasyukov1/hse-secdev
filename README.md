# Media Wishlist Project

[![CI](https://github.com/vasyukov1/hse-secdev/actions/workflows/ci.yml/badge.svg)](https://github.com/vasyukov1/hse-secdev/actions/workflows/ci.yml)

Репозиторий проекта "Media Wishlist" in course HSE SecDev 2025.

## Быстрый старт
### Локальная разработка
```bash
# Создание виртуального окружения
python -m venv .venv
source .venv/bin/activate

# Установка зависимостей
pip install -r requirements.txt -r requirements-dev.txt

# Настройка pre-commit хуков
pre-commit install

# Запуск PostgreSQL
brew services start postgresql

# Запуск приложения
uvicorn app.main:app --reload
```

### Запуск в Docker
```bash
# Сборка и запуск отдельного контейнера
docker build -t secdev-app .
docker run --rm -p 8000:8000 secdev-app

# Или запуск с базой данных через Docker Compose
docker compose up --build
```

Приложение будет доступно по адресу: http://localhost:8000
Документация API: http://localhost:8000/docs

## Архитектурные решения (ADR)
Проект использует Architecture Decision Records (ADR) для документирования ключевых архитектурных решений, особенно в области безопасности.

### Актуальные ADR
- ADR-001 - RFC 7807 Error Handling
- ADR-002 - URL Validation for Media Links
- ADR-003 - Resource Limits and Timeouts


### Структура ADR
Каждый ADR содержит:
- Context - проблема и контекст решения
- Decision - принятое решение и его параметры
- Consequences - последствия и компромиссы
- Security Impact - влияние на безопасность
- Links - связи с NFR и Threat Model

## Ритуал перед PR
```bash
# Форматирование и линтинг
ruff --fix .
black .
isort .

# Запуск тестов
pytest -q

# Финальная проверка pre-commit
pre-commit run --all-files
```

## Тестирование
```bash
# Быстрое тестирование
pytest -q

# Подробное тестирование с покрытием
pytest -v --cov=app --cov-report=html

# Только определенные тесты
pytest tests/test_media.py -v
```

## CI
В репозитории настроен workflow **CI** (GitHub Actions) — required check для `main`.
Badge добавится автоматически после загрузки шаблона в GitHub.


## Эндпойнты
- `GET /health` → `{"status": "ok"}`
- `POST /media` → Созданный медиа-элемент
- `GET /media` → Массив медиа-элементов
- `GET /media/{id}` → Медиа-элемент
- `PUT /media/{id}` → Обновленный медиа-элемент
- `DELETE /media/{id}` → `{"status": "deleted"}`

## Формат данных

```json
{
  "name": "Название (1-255 символов, только разрешенные символы)",
  "year": "год (1800-текущий год)",
  "kind": "film|course",
  "status": "planned|watching|completed",
  "director": "Режиссер (обязателен для фильмов)",
  "rating": "рейтинг 0-10 (опционально)",
  "description": "описание до 1000 символов",
  "genres": "массив жанров (максимум 10)",
  "duration": "продолжительность в минутах",
  "url": "валидный URL (только http/https, запрещены внутренние адреса)"
}
```

## Формат ошибок
Все ошибки соответствуют стандарту RFC 7807:
```json
{
  "type": "about:blank",
  "title": "Validation Error",
  "status": 422,
  "detail": "Запрос содержит невалидные данные",
  "correlation_id": "uuid-v4-идентификатор",
  "errors": [
    {
      "loc": ["body", "year"],
      "msg": "Year cannot be in the future",
      "type": "value_error"
    }
  ]
}
```

## Переменные окружения

Создайте файл .env:
```bash
DATABASE_USER=username
DATABASE_PASSWORD=password
DATABASE_HOST=localhost
DATABASE_PORT=5432
DATABASE_NAME=media_db
```

## База данных
Проект использует PostgreSQL. При запуске через Docker Compose база данных создается автоматически.

## Стркутура проекта
```bash
app/
├── main.py         # Основное приложение FastAPI
├── models.py       # SQLAlchemy модели
├── schemas.py      # Pydantic схемы
├── db.py           # Настройка базы данных
├── errors.py       # Обработка ошибок RFC 7807 с маскировкой PII
└── file_utils.py   # Безопасная работа с файлами
docs/
└── adr/            # Архитектурные решения
    ├── ADR-001-rfc7807-error-handling.md
    ├── ADR-002-url-validation.md
    └── ADR-003-resource-limits.md
└── security-nfr/
    ├── NFR_BDD.md
    ├── NFR_TRACEABILITY.md
    └── NFR.md
└── threat-model/
    ├── DFD.md
    ├── RISKS.md
    └── STRIDE.md
tests/              # Тесты
├── test_media.py   # Тесты для медиа
├── test_health.py  # Тесты health-чеков
├── test_errors.py  # Тесты обработки ошибок
├── test_limits.py  # Тесты лимитов и безопасности
└── test_secure_coding.py  # Тесты безопасного кодирования
```

## Безопасность

### Реализованные меры безопасности
- Валидация входных данных через Pydantic v2 с strict schema (extra='forbid')
- RFC 7807 обработка ошибок с correlation_id для трассировки и маскировкой чувствительных данных
- Валидация URL с проверкой схем, запретом внутренних адресов и ограничением длины
- Лимиты запросов - максимальный размер 1MB
- Безопасная работа с файлами - MIME validation, лимиты размера (5MB), защита от path traversal
- SQL параметризация через SQLAlchemy ORM
- Безопасная сериализация JSON для Decimal, UUID, datetime
- Защита от симлинков при работе с файловой системой

### Связь с требованиями
- NFR-05 (Безопасность API эндпоинтов) - через валидацию и лимиты
- NFR-06 (Производительность) - через защиту от DoS атак
- NFR-09 (Логирование безопасности) - через correlation_id

### Устранённые риски
- R2 (SQL Injection) - через строгую валидацию входных данных
- R4 (DoS атака) - через лимиты размера запросов
- R10 (Недостаточное логирование) - через correlation_id в ошибках
- Защита от path traversal, symlink атак, MIME spoofing

### Тестирование безопасности
- 7+ негативных тестов в test_secure_coding.py
- Проверка SQL injection prevention
- Тесты path traversal protection
- Валидация MIME типов и размеров файлов
- Проверка маскировки чувствительных данных

См. также: `SECURITY.md`, `.pre-commit-config.yaml`, `.github/workflows/ci.yml`, `pyproject.toml`.
