# Popular Places API

REST API для пошуку, перегляду та керування популярними місцями, категоріями й відгуками користувачів.

# Встановлення та запуск

## 1. Клонування репозиторію

```bash
git clone https://github.com/torri87/popular-places-api.git
cd popular-places-api
```

## 2. Налаштування змінних середовища

Створи файл `.env` на основі `.env.example`:

```bash
cp .env.example .env
```

Приклад налаштувань:

```env
SECRET_KEY=your_secret_key
DEBUG=True

# PostgreSQL
DB_NAME=locations_db
DB_USER=user_locations
DB_PASSWORD=password_locations
DB_HOST=db
DB_PORT=5432

# Redis
REDIS_URL=redis://redis:6379/1
```

## 3. Збірка та запуск контейнерів

```bash
docker compose up --build -d
```

Docker Compose запустить три сервіси.

Міграції бази даних застосовуються автоматично під час запуску контейнера `web`.

## 4. Перевірка стану контейнерів

```bash
docker compose ps
```

## 5. Створення адміністратора

```bash
docker compose exec web python manage.py createsuperuser
```

## 6. Доступ до застосунку

Після успішного запуску застосунок буде доступний за адресами:

- API: http://localhost:8000/api/
- Django Admin: http://localhost:8000/admin/

При переході на `http://localhost:8000/` відбувається автоматичне перенаправлення на `/api/`.

---

# API Documentation

Базова адреса API:

```text
http://localhost:8000/api/
```

Запити та відповіді API використовують формат JSON, якщо для конкретного endpoint не зазначено інший формат.

## 1. Категорії (Categories)

Базовий endpoint:

```text
/api/categories/
```

| HTTP-метод | Endpoint | Опис | Доступ |
|---|---|---|---|
| GET | `/api/categories/` | Отримати список категорій | Усі |
| POST | `/api/categories/` | Створити категорію | Адміністратор |

Для окремої категорії:

| HTTP-метод | Endpoint | Опис | Доступ |
|---|---|---|---|
| GET | `/api/categories/{id}/` | Отримати категорію | Усі |
| PUT | `/api/categories/{id}/` | Повністю оновити категорію | Адміністратор |
| PATCH | `/api/categories/{id}/` | Частково оновити категорію | Адміністратор |
| DELETE | `/api/categories/{id}/` | Видалити категорію | Адміністратор |

### Створення категорії

```http
POST /api/categories/
Content-Type: application/json
```

Тіло запиту:

```json
{
  "name": "Парки"
}
```

Приклад відповіді (`201 Created`):

```json
{
  "id": 1,
  "name": "Парки"
}
```

### Отримання списку категорій

```http
GET /api/categories/
```

Приклад відповіді:

```json
[
  {
    "id": 1,
    "name": "Парки"
  },
  {
    "id": 2,
    "name": "Ресторани"
  }
]
```

---

## 2. Місця (Locations)

Базовий endpoint:

```text
/api/locations/
```

| HTTP-метод | Endpoint | Опис | Доступ |
|---|---|---|---|
| GET | `/api/locations/` | Отримати список місць | Усі |
| POST | `/api/locations/` | Створити місце | Авторизований користувач |

Для окремого місця:

| HTTP-метод | Endpoint | Опис | Доступ |
|---|---|---|---|
| GET | `/api/locations/{id}/` | Отримати інформацію про місце | Усі |
| PUT | `/api/locations/{id}/` | Повністю оновити місце | Власник або адміністратор |
| PATCH | `/api/locations/{id}/` | Частково оновити місце | Власник або адміністратор |
| DELETE | `/api/locations/{id}/` | Видалити місце | Власник або адміністратор |

### Створення місця

```http
POST /api/locations/
Content-Type: application/json
```

Тіло запиту:

```json
{
  "title": "Центральний парк",
  "description": "Популярне місце для прогулянок та відпочинку.",
  "category": 1,
  "address": "м. Луцьк, Україна",
  "latitude": 50.7472,
  "longitude": 25.3254
}
```

Приклад відповіді (`201 Created`):

```json
{
  "id": 1,
  "title": "Центральний парк",
  "description": "Популярне місце для прогулянок та відпочинку.",
  "category": 1,
  "address": "м. Луцьк, Україна",
  "latitude": 50.7472,
  "longitude": 25.3254,
  "author": "username",
  "avg_rating": null,
  "reviews_count": 0,
  "views_7d": 0,
  "popularity": 0.0,
  "created_at": "2026-11-23T10:00:00Z",
  "updated_at": "2026-11-23T10:00:00Z"
}
```


### Отримання списку місць

```http
GET /api/locations/
```

Приклад відповіді:

```json
[
  {
    "id": 1,
    "title": "Центральний парк",
    "description": "Популярне місце для прогулянок.",
    "category": 1,
    "address": "м. Луцьк, Україна",
    "latitude": 50.7472,
    "longitude": 25.3254,
    "author": "username",
    "avg_rating": 4.75,
    "reviews_count": 12,
    "views_7d": 150,
    "popularity": 162.5,
    "created_at": "2026-11-23T10:00:00Z",
    "updated_at": "2026-11-23T10:00:00Z"
  }
]
```


### Отримання окремого місця

```http
GET /api/locations/1/
```

Повертає інформацію про конкретне місце. Під час перегляду також реєструється перегляд.

### Пошук

Пошук здійснюється за назвою та описом місця.

Параметр:

```text
?search=назва
```

Приклад:

```http
GET /api/locations/?search=парк
```

### Сортування

Доступні поля сортування:

- `created_at` — дата створення.
- `avg_rating` — середній рейтинг.
- `popularity` — популярність.

Приклади:

```http
GET /api/locations/?ordering=created_at
GET /api/locations/?ordering=-avg_rating
GET /api/locations/?ordering=popularity
```


За замовчуванням місця сортуються за датою створення у зворотному порядку (`-created_at`).

### Фільтрація

Приклад використання:

```http
GET /api/locations/?<filter_parameter>=<value>
```

### Експорт місць

| HTTP-метод | Endpoint | Опис |
|---|---|---|
| GET | `/api/locations/export/csv/` | Експорт місць у CSV |
| GET | `/api/locations/export/json/` | Експорт місць у JSON |

Приклади:

```http
GET /api/locations/export/csv/
GET /api/locations/export/json/
```

Експорт враховує застосовані фільтри, пошук та сортування.

CSV-файл повертається з назвою `locations.csv`, JSON-файл — `locations.json`.

Експорт містить такі дані:

- `id`
- `title`
- `description`
- `category`
- `address`
- `latitude`
- `longitude`
- `author`
- `avg_rating`
- `reviews_count`
- `views_7d`
- `popularity`
- `created_at`
- `updated_at`

---

## 3. Відгуки (Reviews)

Базовий endpoint:

```text
/api/reviews/
```

| HTTP-метод | Endpoint | Опис | Доступ |
|---|---|---|---|
| GET | `/api/reviews/` | Отримати список відгуків | Усі |
| POST | `/api/reviews/` | Створити відгук | Авторизований користувач |

Для окремого відгуку:

| HTTP-метод | Endpoint | Опис | Доступ |
|---|---|---|---|
| GET | `/api/reviews/{id}/` | Отримати відгук | Усі |
| PUT | `/api/reviews/{id}/` | Повністю оновити відгук | Власник або адміністратор |
| PATCH | `/api/reviews/{id}/` | Частково оновити відгук | Власник або адміністратор |
| DELETE | `/api/reviews/{id}/` | Видалити відгук | Власник або адміністратор |

### Створення відгуку

```http
POST /api/reviews/
Content-Type: application/json
```

Тіло запиту:

```json
{
  "location": 1,
  "rating": 5,
  "comment": "Чудове місце для відпочинку!"
}
```

Приклад відповіді (`201 Created`):

```json
{
  "id": 1,
  "location": 1,
  "author_name": "username",
  "rating": 5,
  "comment": "Чудове місце для відпочинку!",
  "likes_count": 0,
  "dislikes_count": 0,
  "created_at": "2026-11-23T10:00:00Z",
  "updated_at": "2026-11-23T10:00:00Z"
}
```


Один користувач може залишити лише один відгук для конкретного місця.


### Отримання списку відгуків

```http
GET /api/reviews/
```

### Фільтрація відгуків

Підтримуються параметри:

- `location` — фільтрація за ID місця.
- `author` — фільтрація за ID автора.

Приклади:

```http
GET /api/reviews/?location=1
GET /api/reviews/?author=2
GET /api/reviews/?location=1&author=2
```

### Голосування за відгук

Endpoint:

```http
POST /api/reviews/{id}/vote/
```

Доступний лише авторизованим користувачам.

Тіло запиту:

```json
{
  "value": "1 або 0"
}
```

Кожен користувач може проголосувати за конкретний відгук лише один раз.

У разі успіху повертається оновлений відгук зі статистикою голосів (`201 Created`).

Якщо користувач уже голосував, API повертає HTTP `400 Bad Request`:

```json
{
  "detail": "Ви вже голосували за цей відгук."
}
```

---

## 4. Автентифікація та користувачі (Authentication)

Базовий endpoint:

```text
/api/auth/
```


### Реєстрація

```http
POST /api/auth/register/
Content-Type: application/json
```

Тіло запиту:

```json
{
  "username": "newuser",
  "email": "newuser@example.com",
  "password": "StrongPassword123!"
}
```

Всі три поля обов'язкові. Пароль перевіряється стандартними валідаторами Django.

Успішна відповідь (`201 Created`):

```json
{
  "id": 1,
  "username": "newuser",
  "email": "newuser@example.com"
}
```

Після реєстрації користувач автоматично авторизується.


### Вхід

```http
POST /api/auth/login/
Content-Type: application/json
```

Тіло запиту:

```json
{
  "username": "newuser",
  "password": "StrongPassword123!"
}
```

Успішна відповідь (`200 OK`):

```json
{
  "id": 1,
  "username": "newuser",
  "email": "newuser@example.com"
}
```

У разі неправильного логіна або пароля повертається помилка:

```json
{
  "non_field_errors": [
    "Невірний логін або пароль."
  ]
}
```

Після успішного входу створюється сесія користувача.

### Вихід

```http
POST /api/auth/logout/
```

Завершує поточну сесію користувача.

Доступний лише авторизованим користувачам.

Успішна відповідь: HTTP `204 No Content`.

### Отримання CSRF-токена

```http
GET /api/auth/csrf/
```


Приклад відповіді:

```json
{
  "csrfToken": "<csrf_token>"
}
```

Для небезпечних HTTP-методів (`POST`, `PUT`, `PATCH`, `DELETE`) при використанні сесійної автентифікації потрібно передавати відповідний CSRF-токен.

### Отримання поточного користувача

```http
GET /api/auth/me/
```

Повертає інформацію про поточного авторизованого користувача.

Успішна відповідь (`200 OK`):

```json
{
  "id": 1,
  "username": "newuser",
  "email": "newuser@example.com"
}
```

Доступний лише авторизованим користувачам.

### Запит на скидання пароля

```http
POST /api/auth/password-reset/
Content-Type: application/json
```

Тіло запиту:

```json
{
  "email": "newuser@example.com"
}
```

Надсилає лист для скидання пароля, якщо активний користувач із таким email існує.

Відповідь:

```json
{
  "detail": "Якщо такий email існує, лист надіслано."
}
```

### Підтвердження скидання пароля

```http
POST /api/auth/password-reset/confirm/
Content-Type: application/json
```

Встановлює новий пароль за допомогою `uid` та `token`, отриманих у листі.

Тіло запиту:

```json
{
  "uid": "<uid_from_email>",
  "token": "<token_from_email>",
  "new_password": "NewStrongPassword123!"
}
```

Успішна відповідь (`200 OK`):

```json
{
  "detail": "Пароль змінено успішно"
}
```

Якщо посилання недійсне або прострочене, API повертає HTTP `400 Bad Request`.

Новий пароль також проходить перевірку валідаторами Django.

---


# Тестування

Для запуску тестів виконай:

```bash
docker compose exec web python manage.py test
```

