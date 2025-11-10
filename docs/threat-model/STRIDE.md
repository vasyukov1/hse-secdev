# STRIDE Анализ угроз

## Таблица угроз и контролей

| Поток/Элемент | Угроза (STRIDE) | Контроль | Ссылка на NFR | Обоснование/Проверка |
|---------------|------------------|----------|---------------|---------------------|
| F1 (User→API) | **S**poofing: Подмена пользователя | JWT токены с TTL, валидация | NFR-03 | Access: 15 мин, Refresh: 7 дней |
| F1 (User→API) | **T**ampering: Изменение данных в транзите | HTTPS enforcement | NFR-10 | 100% redirect HTTP→HTTPS |
| F1 (User→API) | **R**epudiation: Отказ от операций | Логирование auth событий | NFR-09 | 100% auth событий логгируются |
| F1 (User→API) | **I**nformation Disclosure: Перехват данных | Шифрование TLS, валидация данных | NFR-05, NFR-10 | Pydantic схемы + HTTPS |
| F1 (User→API) | **D**oS: Отказ в обслуживании | Rate limiting middleware | NFR-01, NFR-06 | ≤5 попыток/мин, p95 ≤500ms при 30 RPS |
| F1 (User→API) | **E**levation of Privilege: Неавторизованный доступ | Валидация входных данных | NFR-05 | 100% эндпоинтов с валидацией |
| F2-F5 (API→DB) | **T**ampering: SQL Injection | Параметризованные запросы SQLAlchemy | NFR-05 | Pydantic валидация + ORM |
| F2-F5 (API→DB) | **I**nformation Disclosure: Утечка PII данных | Шифрование чувствительных данных | NFR-04 | PII в зашифрованном виде в БД |
| F6 (DB→API) | **I**nformation Disclosure: Чтение чужих данных | Проверка прав доступа | NFR-05 | Валидация ownership данных |
| API (Application) | **T**ampering: Уязвимости в зависимостях | SCA сканирование в CI/CD | NFR-07 | Critical/High ≤7 дней для исправления |
| API (Application) | **D**oS: Resource exhaustion | Лимиты запросов, мониторинг | NFR-01, NFR-06 | Rate limiting + нагрузочное тестирование |
| DB (Database) | **S**poofing: Неавторизованный доступ | Защита учетных данных БД | NFR-11 | Ротация секретов каждые ≤30 дней |
| DB (Database) | **I**nformation Disclosure: Кража данных БД | Шифрование PII, безопасные бэкапы | NFR-04 | Argon2id для паролей, шифрование PII |
| Container (Runtime) | **E**levation of Privilege: Привилегии контейнера | Запуск без root прав | NFR-08 | runAsNonRoot: true в Dockerfile |

## Неприменимые угрозы

- **Spoofing DB**: База данных не инициирует соединения наружу
- **Repudiation DB**: Логирование на уровне приложения (NFR-09) достаточно
- **Elevation DB**: Один уровень привилегий для приложения
