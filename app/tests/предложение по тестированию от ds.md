Что тестировать
1. Юнит-тесты (изолированно, без БД/Redis)
Тест	Что проверяет
test_hash_password	Хеш не равен исходному паролю
test_verify_password_ok	verify_password возвращает True для правильного пароля
test_verify_password_fail	False для неправильного
test_expire_token_check_valid	expire_token_check → True если токен жив
test_expire_token_check_expired	→ False если просрочен
test_generate_key_by_user	Ключ = str(user.token)
test_user_session_frozen	Нельзя изменить поля после создания
2. Интеграционные тесты репозиториев (с реальной БД/Redis)
UserRepository:
- test_create_user_ok — создание пользователя, возвращает id
- test_create_user_duplicate — дубликат username → возвращает None (не падает)
- test_auth_user_ok — правильные логин/пароль → UserSessionCreateSchema
- test_auth_user_not_found — несуществующий username → UserNotFoundError
- test_auth_user_wrong_password — неправильный пароль → PasswordNotValidError
PostgresSessionRepository:
- test_create_session_ok — создание, проверка что вернулся UserSession с id, token, expire_token
- test_find_session_ok — поиск существующей сессии → datetime
- test_find_session_not_found — несуществующая → SessionNotFoundError
- test_delete_session — удаление, потом find_session → SessionNotFoundError
- test_token_expiry — создать с 0 временем жизни, проверить что expire_token_check → False
RedisSessionRepository:
- test_set_and_get_session — положили, прочитали — вернулось то же значение
- test_get_session_not_found — нет ключа → None
- test_delete_session — удалили, get → None
- test_session_ttl — проверить что TTL установлен (необязательно, exists + ttl)
3. Интеграционные тесты API (через TestClient)
Тест	Что проверяет
test_register_ok	POST /register → 201, новый пользователь
test_register_duplicate	POST /register тем же username → 400
test_auth_ok	POST /auth → 201 + кука sessionToken
test_auth_wrong_password	→ 400
test_auth_not_found	→ 400
test_logout_ok	auth → logout → кука удалена
test_logout_without_cookie	POST /logout без куки → 200
test_private_endpoint_valid_session	auth → запрос к /api/v1/other/ → 200
test_private_endpoint_no_cookie	без куки → 401
test_private_endpoint_invalid_cookie	с поддельной кукой → 401
4. Интеграционный тест Cache-aside
- auth → проверить что сессия есть в Redis
- удалить вручную из Redis
- запрос к private endpoint — должен сходить в Postgres и переположить в Redis
- проверить что Redis снова содержит сессию
---
Инструменты
- pytest + pytest-asyncio
- TestClient из FastAPI (httpx)
- Для тестовой БД: отдельная тестовая база или asyncpg с CREATE DATABASE на лету
- Для Redis: redis контейнер в тестах или мок
Структура
tests/
├── conftest.py           # фикстуры: app, db_pool, redis, client
├── test_unit/
│   ├── test_hash.py
│   ├── test_schemas.py
│   └── test_utils.py
├── test_integration/
│   ├── test_user_repo.py
│   ├── test_postgres_session_repo.py
│   ├── test_redis_session_repo.py
│   └── test_cache_aside.py
└── test_api/
    ├── test_auth.py
    ├── test_register.py
    └── test_middleware.py
---
Если хочешь, могу написать conftest.py с фикстурами (это самая сложная часть), чтобы ты отталкивался от него — дай знать.