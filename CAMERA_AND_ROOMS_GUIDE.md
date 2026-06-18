# MeetFlow - Руководство по камере и управлению переговорными

## 📸 Доступ к камере (HTTPS/SSL)

### Почему нужен HTTPS?
Современные браузеры (Chrome, Firefox, Safari) **блокируют доступ к камере** на HTTP-соединениях, кроме `localhost`. Для работы QR сканера необходим HTTPS.

### Быстрая настройка SSL сертификата:

#### Вариант 1: Самоподписанный сертификат (для тестирования)

```bash
# Создание директории для сертификатов
mkdir -p config/ssl
cd config/ssl

# Генерация приватного ключа
openssl genrsa -out meetflow.key 2048

# Генерация запроса на сертификат
openssl req -new -key meetflow.key -out meetflow.csr \
  -subj "/C=RU/ST=Moscow/L=Moscow/O=MeetFlow/CN=188.127.227.39"

# Самоподписанный сертификат (действителен 365 дней)
openssl x509 -req -days 365 -in meetflow.csr -signkey meetflow.key -out meetflow.crt
```

#### Вариант 2: Let's Encrypt (для production)

```bash
# Установка Certbot
sudo apt update
sudo apt install certbot python3-certbot-nginx

# Получение сертификата (нужен домен)
sudo certbot --nginx -d meetflow.example.com

# Автоматическое обновление
sudo certbot renew --dry-run
```

### Настройка Nginx как reverse proxy:

```bash
sudo apt install nginx
```

Создайте файл `/etc/nginx/sites-available/meetflow`:

```nginx
server {
    listen 80;
    server_name 188.127.227.39;
    
    # Редирект на HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name 188.127.227.39;
    
    # SSL сертификаты
    ssl_certificate /home/cjcjr/meeting-room-booking/config/ssl/meetflow.crt;
    ssl_certificate_key /home/cjcjr/meeting-room-booking/config/ssl/meetflow.key;
    
    # SSL настройки
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;
    
    # Размер загрузки для изображений
    client_max_body_size 10M;
    
    # Статические файлы
    location /static/ {
        root /home/cjcjr/meeting-room-booking;
        expires 30d;
    }
    
    # Медиа файлы (фотографии комнат)
    location /media/ {
        root /home/cjcjr/meeting-room-booking;
    }
    
    # Django приложение
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Активация:

```bash
sudo ln -s /etc/nginx/sites-available/meetflow /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### Запуск с Gunicorn (production):

```bash
# Установка Gunicorn
source venv/bin/activate
pip install gunicorn

# Запуск
gunicorn config.wsgi:application \
  --bind 127.0.0.1:8000 \
  --workers 3 \
  --timeout 120 \
  --access-logfile /var/log/gunicorn/access.log \
  --error-logfile /var/log/gunicorn/error.log
```

### Systemd сервис для автозапуска:

Создайте `/etc/systemd/system/meetflow.service`:

```ini
[Unit]
Description=MeetFlow Django Application
After=network.target

[Service]
User=cjcjr
Group=www-data
WorkingDirectory=/home/cjcjr/meeting-room-booking
Environment="PATH=/home/cjcjr/meeting-room-booking/venv/bin"
ExecStart=/home/cjcjr/meeting-room-booking/venv/bin/gunicorn config.wsgi:application --bind 127.0.0.1:8000 --workers 3

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable meetflow
sudo systemctl start meetflow
sudo systemctl status meetflow
```

---

## 🏢 Добавление новых переговорных

### Способ 1: Через Django Admin (рекомендуется)

1. **Запустите сервер**:
```bash
source venv/bin/activate
python manage.py runserver 0.0.0.0:8080
```

2. **Перейдите в админку**: `http://188.127.227.39:8080/admin/`

3. **Войдите как суперпользователь**:
```bash
python manage.py createsuperuser
```

4. **Добавьте переговорную**:
   - Раздел "Переговорные" → "Добавить переговорную"
   - Заполните поля:
     - **Название**: например, "Переговорная "Европа""
     - **Описание**: подробное описание
     - **Вместимость**: количество человек
     - **Местоположение**: этаж/офис
     - **Статус**: "Доступна"
     - **Изображение**: загрузите фото комнаты
     - **QR код ID**: генерируется автоматически

### Способ 2: Через Django Shell

```bash
source venv/bin/activate
python manage.py shell
```

```python
import uuid
from rooms.models import Room

# Создание новой переговорной
room = Room.objects.create(
    name="Переговорная 'Европа'",
    description="Большая конференц-комната для международных встреч. Видеоконференц-связь, переводчик, запись встреч.",
    capacity=20,
    location="5 этаж, зал 501",
    status='available',
    qr_code_id=str(uuid.uuid4())
)

# Добавление фотографии
# (файл должен быть уже загружен через админку или media папку)
# room.image = 'rooms/europe_room.jpg'
# room.save()

print(f"Создана комната: {room.name}")
print(f"QR код: {room.qr_code_id}")
print(f"ID: {room.id}")
```

### Способ 3: Через миграцию (для批量 добавления)

Создайте файл `rooms/migrations/0005_add_custom_rooms.py`:

```python
from django.db import migrations
import uuid

def add_custom_rooms(apps, schema_editor):
    Room = apps.get_model('rooms', 'Room')
    
    new_rooms = [
        {
            'name': 'Переговорная "Европа"',
            'description': 'Большая конференц-комната для международных встреч',
            'capacity': 20,
            'location': '5 этаж, зал 501',
            'status': 'available',
        },
        {
            'name': 'Переговорная "Азия"',
            'description': 'Комната для небольших встреч с клиентами из Азии',
            'capacity': 6,
            'location': '3 этаж, офис 304',
            'status': 'available',
        },
    ]
    
    for room_data in new_rooms:
        Room.objects.create(
            **room_data,
            qr_code_id=str(uuid.uuid4()),
        )

def remove_custom_rooms(apps, schema_editor):
    Room = apps.get_model('rooms', 'Room')
    room_names = ['Переговорная "Европа"', 'Переговорная "Азия"']
    Room.objects.filter(name__in=room_names).delete()

class Migration(migrations.Migration):
    dependencies = [
        ('rooms', '0004_room_image'),
    ]

    operations = [
        migrations.RunPython(add_custom_rooms, remove_custom_rooms),
    ]
```

Запустите миграцию:
```bash
python manage.py migrate
```

---

## 📷 Добавление фотографий к переговорным

### Способ 1: Через Django Admin

1. Откройте админку: `http://188.127.227.39:8080/admin/rooms/room/`
2. Выберите комнату для редактирования
3. В поле "Изображение" загрузите фото
4. Сохраните изменения

**Требования к изображениям**:
- Форматы: JPG, PNG, GIF, WebP
- Рекомендуемый размер: 1200x800px (соотношение 3:2)
- Максимальный размер: 5MB
- Хорошее освещение, чёткое изображение

### Способ 2: Прямая загрузка в media папку

```bash
# Создайте папку если её нет
mkdir -p media/rooms

# Скопируйте изображение
cp /path/to/your/photo.jpg media/rooms/room_1.jpg
```

Затем через shell:

```python
from rooms.models import Room

room = Room.objects.get(id=1)
room.image = 'rooms/room_1.jpg'
room.save()
```

### Способ 3: Через код (для автоматической загрузки)

```python
import os
from django.core.files import File
from rooms.models import Room

room = Room.objects.get(id=1)

# Открываем файл
image_path = '/path/to/photo.jpg'
with open(image_path, 'rb') as f:
    room.image.save('room_1.jpg', File(f), save=True)

print(f"Фото добавлено: {room.image.url}")
```

---

## 🔍 Генерация QR кодов для печати

### Создание QR кодов высокого качества:

```python
import os
import qrcode
from django.core.management.base import BaseCommand
from rooms.models import Room

class Command(BaseCommand):
    help = 'Генерация QR кодов для всех комнат'
    
    def handle(self, *args, **options):
        output_dir = 'qr_codes'
        os.makedirs(output_dir, exist_ok=True)
        
        for room in Room.objects.all():
            # URL для сканирования
            qr_data = f"https://meetflow.example.com/rooms/scanner/?qr={room.qr_code_id}"
            
            # Создание QR кода с высокой коррекцией ошибок
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_H,
                box_size=10,
                border=4,
            )
            qr.add_data(qr_data)
            qr.make(fit=True)
            
            # Создание изображения
            img = qr.make_image(fill_color="black", back_color="white")
            filename = f"{output_dir}/room_{room.id}_{room.name.replace(' ', '_')}.png"
            img.save(filename)
            
            self.stdout.write(f"✓ Создан QR код: {filename}")
            self.stdout.write(f"  Комната: {room.name}")
            self.stdout.write(f"  QR ID: {room.qr_code_id}")
            self.stdout.write(f"  URL: {qr_data}\n")
```

Использование:
```bash
python manage.py generate_qr_codes
```

### Печать QR кодов:

1. Откройте папку `qr_codes/`
2. Распечатайте QR коды на бумаге или стикерах
3. Разместите у каждой переговорной комнаты
4. Размер: рекомендуется 5x5 см или больше

---

## 🎯 Проверка работы камеры

### Тестирование в браузере:

1. **Откройте сканер**: `https://188.127.227.39/rooms/scanner/`
2. **Разрешите камеру**: браузер запросит разрешение
3. **Наведите на QR код**: система должна распознать
4. **Проверьте результат**: должно появиться сообщение "Добро пожаловать!"

### Если камера не работает:

1. **Проверьте HTTPS**: откройте DevTools (F12) → Console
   - Должно быть: `Secure context: YES`
   - Если `NO` - проблема с SSL

2. **Проверьте разрешения**:
   - Chrome: `chrome://settings/content/camera`
   - Firefox: `about:preferences#privacy`
   - Разрешите доступ к камере для вашего сайта

3. **Проверьте консоль ошибок**:
   - F12 → Console
   - Ищите ошибки с пометкой `camera` или `getUserMedia`

4. **Тест на localhost**:
   ```bash
   # Камера работает на localhost без HTTPS
   python manage.py runserver
   # Откройте http://localhost:8000/rooms/scanner/
   ```

---

## 📋 Полный чек-лист

### После добавления новой комнаты:

- [ ] Создана комната в админке или shell
- [ ] Загружено фото комнаты (опционально)
- [ ] Сгенерирован QR код
- [ ] QR код распечатан и размещён у двери
- [ ] Создана политика доступа (если нужно ограничить доступ)
- [ ] Протестировано сканирование QR кода
- [ ] Проверено бронирование через интерфейс

### Для production:

- [ ] Установлен SSL сертификат (Let's Encrypt)
- [ ] Настроен Nginx как reverse proxy
- [ ] Запущен Gunicorn
- [ ] Настроен Systemd сервис
- [ ] Включен HTTPS в settings.py:
  ```python
  SECURE_SSL_REDIRECT = True
  SESSION_COOKIE_SECURE = True
  CSRF_COOKIE_SECURE = True
  ```
- [ ] Протестирована камера на внешнем доступе
- [ ] Настроен бекап базы данных

---

## 🆘 Частые проблемы

### Камера не включается:
- **Причина**: Нет HTTPS
- **Решение**: Настройте SSL сертификат или тестируйте на localhost

### Фото не загружается:
- **Причина**: Не настроен MEDIA_URL/MEDIA_ROOT
- **Решение**: Проверьте `config/settings.py` и `config/urls.py`

### QR код не сканируется:
- **Причина**: Нет доступа к комнате или нет активного бронирования
- **Решение**: 
  1. Создайте политику доступа (Access Control → Room Access Policies)
  2. Забронируйте комнату на текущее время
  3. Отсканируйте QR код

### Комнаты не отображаются:
- **Причина**: Нет политик доступа
- **Решение**: Запустите миграцию `access_control.0002` или создайте политики вручную

---

## 📞 Поддержка

При возникновении проблем:
1. Проверьте логи: `logs/errors.log`
2. Включите DEBUG=True для детальных ошибок
3. Проверьте консоль браузера (F12)
4. Убедитесь что все миграции применены: `python manage.py migrate`