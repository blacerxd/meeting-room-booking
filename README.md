# Meeting Room Booking

Веб-приложение для бронирования переговорных комнат с контролем доступа через QR-коды. Позволяет сотрудникам бронировать переговорные онлайн, а при входе в комнату подтверждать бронь сканированием QR-кода — система сама проверяет права доступа и ведёт журнал входов.

## Содержание

- [Возможности](#возможности)
- [Стек технологий](#стек-технологий)
- [Инструкция запуска](#инструкция-запуска)
- [Структура проекта](#структура-проекта)
- [Тестирование](#тестирование)
- [CI/CD](#cicd)

## Возможности

-  Бронирование переговорных комнат с проверкой конфликтов по времени
-  Вход в комнату по QR-коду через камеру браузера
-  Гранулярное управление доступом (просмотр / бронирование / управление)
-  Журнал входов и выходов из переговорных
-  Кастомная модель пользователя с ролями
-  Админ-панель Django для управления всеми сущностями

## Стек технологий

**Backend**
- Python 3.12+
- Django 5.2.6
- PostgreSQL 18.4
- psycopg2-binary — драйвер PostgreSQL
- python-dotenv — переменные окружения

**Frontend**
- HTML / CSS / JavaScript
- Django Templates
- django-crispy-forms + crispy-bootstrap5 — формы
- django-widget-tweaks — настройка виджетов
- jsQR — сканирование QR-кодов в браузере

**Прочее**
- Pillow + qrcode — генерация и обработка изображений/QR
- pytest + pytest-django — тестирование
- GitHub Actions — CI/CD

## Инструкция запуска

### 1. Клонировать репозиторий

```bash
git clone https://github.com/blacerxd/meeting-room-booking.git
cd meeting-room-booking
```

### 2. Создать виртуальное окружение и установить зависимости

```bash
python -m venv venv
source venv/bin/activate    # Linux/macOS
venv\Scripts\activate       # Windows

pip install -r requirements.txt
```

### 3. Настроить PostgreSQL

Запустить PostgreSQL с правами суперпользователя и создать базу данных:

```bash
sudo -iu postgres psql
```

```sql
CREATE DATABASE meeting_booking;
CREATE USER meeting_user WITH PASSWORD 'ваш_пароль';
GRANT ALL PRIVILEGES ON DATABASE meeting_booking TO meeting_user;
```

### 4. Настроить переменные окружения

Создать файл `.env` в корне проекта:

```env
SECRET_KEY=django-insecure-xd$lb&m@kq4kcvw9a&g_@)*(7%ji$05r6dfn6cqgg70_lesz=n
DEBUG=True
DB_NAME=meeting_booking
DB_USER=meeting_user
DB_PASSWORD=ваш_пароль
DB_HOST=127.0.0.1
DB_PORT=5432
```

>  Для продакшена обязательно сгенерируйте новый `SECRET_KEY` и установите `DEBUG=False`.

### 5. Применить миграции

```bash
python manage.py migrate
```

### 6. Создать суперпользователя (для доступа к админ-панели)

```bash
python manage.py createsuperuser
```

### 7. Запустить сервер

```bash
python manage.py runserver
```

Приложение будет доступно по адресу: **http://127.0.0.1:8000/**
Админ-панель: **http://127.0.0.1:8000/admin/**

## Структура проекта

```
meeting-room-booking/
├── .github/
│   └── workflows/
│       └── deploy.yml          # CI: тесты и проверка миграций через GitHub Actions
│
├── access_control/             # Управление правами доступа к комнатам
│   ├── migrations/
│   ├── admin.py                 # Регистрация политик доступа в админке
│   ├── models.py                 # Модель RoomAccessPolicy (view/book/manage)
│   ├── views.py                   # Назначение и просмотр политик доступа
│   └── urls.py
│
├── bookings/                   # Бронирование переговорных
│   ├── migrations/
│   ├── admin.py
│   ├── models.py                 # Модели Booking и RoomEntry (журнал входов)
│   ├── views.py                   # Создание, просмотр, отмена бронирований
│   └── urls.py
│
├── rooms/                      # Переговорные комнаты и QR-доступ
│   ├── management/commands/
│   │   └── close_expired_bookings.py   # Команда закрытия просроченных броней
│   ├── migrations/
│   ├── admin.py
│   ├── models.py                 # Модель Room (статус, вместимость, QR-код)
│   ├── views.py                   # Каталог комнат, обработка QR-сканирования
│   └── urls.py
│
├── users/                      # Кастомная модель пользователя
│   ├── migrations/
│   ├── admin.py
│   ├── forms.py                   # Форма регистрации с полем телефона
│   ├── models.py                  # Модель User (расширяет AbstractUser)
│   ├── views.py
│   └── urls.py
│
├── config/                     # Конфигурация Django-проекта
│   ├── settings.py               # Настройки проекта, БД, приложения, middleware
│   ├── urls.py                    # Корневой маршрутизатор
│   ├── middleware.py
│   ├── asgi.py
│   └── wsgi.py
│
├── static/
│   ├── css/
│   │   ├── style.css              # Основные стили интерфейса
│   │   └── admin.css              # Стили админ-панели
│   └── js/
│       └── app.js                 # Клиентская логика (QR-сканер и др.)
│
├── templates/
│   ├── base.html                  # Базовый шаблон с навигацией
│   ├── home.html                  # Главная страница
│   ├── about.html
│   ├── contacts.html
│   ├── access/                    # Шаблоны управления доступом
│   ├── bookings/                  # Шаблоны бронирований
│   ├── rooms/                     # Каталог комнат, карточка, QR-сканер
│   ├── users/                     # Профиль, вход, регистрация
│   ├── registration/              # Смена/восстановление пароля
│   └── admin/                     # Кастомизация админ-панели
│
├── manage.py
├── pytest.ini                  # Конфигурация тестов
├── requirements.txt             # Зависимости проекта
├── .gitignore
└── README.md
```

## Тестирование

Тесты написаны с использованием `pytest` и `pytest-django`:

```bash
pytest
```

## CI/CD

При каждом push в `main` и при открытии Pull Request автоматически запускается пайплайн GitHub Actions (`.github/workflows/deploy.yml`), который:

1. Поднимает тестовую базу PostgreSQL;
2. Устанавливает зависимости;
3. Проверяет конфигурацию (`python manage.py check`);
4. Проверяет актуальность миграций (`makemigrations --check --dry-run`);
5. Применяет миграции;
6. Запускает тесты (`pytest`).

---

**Лицензия:** учебный проект, распространяется без ограничений в образовательных целях.
