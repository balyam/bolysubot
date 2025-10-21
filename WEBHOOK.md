# 🔗 Webhook режим для бота

Документация по настройке бота в режиме webhook вместо long polling.

## 📊 Polling vs Webhook

| Характеристика | Polling (по умолчанию) | Webhook |
|----------------|------------------------|---------|
| **Как работает** | Бот постоянно опрашивает сервера Telegram | Telegram отправляет обновления на ваш сервер |
| **Подходит для** | Разработка, тестирование | Продакшн, VPS/Dedicated сервер |
| **Требования** | Любое подключение к интернету | Публичный IP, HTTPS, доменное имя |
| **Нагрузка** | Постоянные запросы к Telegram | Только входящие запросы |
| **Скорость** | Задержка 1-2 секунды | Мгновенная доставка |
| **Одновременно** | Только 1 экземпляр бота | Можно масштабировать |

## 🚀 Быстрый старт (Webhook)

### 1. Настройте .env

```env
# Включите webhook режим
USE_WEBHOOK=True

# Укажите ваш домен с HTTPS
WEBHOOK_HOST=https://yourdomain.com

# Путь для webhook (можно оставить по умолчанию)
WEBHOOK_PATH=/webhook/bot

# Секретный токен для безопасности (опционально но рекомендуется)
WEBHOOK_SECRET=your_random_secret_token_here

# Хост и порт для веб-приложения
WEBAPP_HOST=0.0.0.0
WEBAPP_PORT=8000
```

### 2. Запустите объединенное приложение

```bash
python app_combined.py
```

Или используйте специальный скрипт:

```bash
python main_webhook.py
```

### 3. Настройте Nginx (reverse proxy)

```nginx
server {
    listen 80;
    server_name yourdomain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com;

    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;

    # Webhook endpoint для бота
    location /webhook/bot {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Админка
    location /admin {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
    
    # API endpoints
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
    }
}
```

## 🔐 Безопасность

### Секретный токен

Telegram будет отправлять секретный токен в заголовке `X-Telegram-Bot-Api-Secret-Token`.
Бот проверяет его перед обработкой обновлений.

Сгенерируйте случайный токен:

```python
import secrets
print(secrets.token_urlsafe(32))
# Результат: xZ7yQ3kM9pL2vN4r8sH6jK9mT4wB3cF5
```

Добавьте в `.env`:
```env
WEBHOOK_SECRET=xZ7yQ3kM9pL2vN4r8sH6jK9mT4wB3cF5
```

### HTTPS обязателен!

Telegram требует **HTTPS** для webhook. Используйте:

1. **Let's Encrypt (бесплатно):**
   ```bash
   sudo apt install certbot python3-certbot-nginx
   sudo certbot --nginx -d yourdomain.com
   ```

2. **Cloudflare** (бесплатный SSL)

3. **Ngrok** (для тестирования):
   ```bash
   ngrok http 8000
   # Используйте полученный https URL
   ```

## 📦 Структура объединенного приложения

```
app_combined.py
├── FastAPI приложение
│   ├── /admin - Веб-админка
│   ├── /webhook/bot - Telegram webhook
│   ├── / - API корень
│   └── /health - Проверка здоровья
│
├── Telegram Bot (aiogram)
│   ├── Обработчики
│   ├── Middlewares
│   └── Клавиатуры
│
└── Админка (SQLAdmin)
    └── Управление данными
```

## 🔄 Переключение между режимами

### Из Polling в Webhook:

1. Остановите `main.py` (polling)
2. Обновите `.env`:
   ```env
   USE_WEBHOOK=True
   WEBHOOK_HOST=https://yourdomain.com
   ```
3. Запустите `app_combined.py`

### Из Webhook в Polling:

1. Остановите `app_combined.py`
2. Обновите `.env`:
   ```env
   USE_WEBHOOK=False
   ```
3. Запустите `main.py`

## 🛠 Разработка vs Продакшн

### Локальная разработка (Polling):

```env
USE_WEBHOOK=False
DEBUG=True
```

```bash
python main.py
python admin_run.py  # В отдельном терминале
```

### Продакшн (Webhook):

```env
USE_WEBHOOK=True
WEBHOOK_HOST=https://yourdomain.com
WEBHOOK_SECRET=random_secret_here
DEBUG=False
```

```bash
python app_combined.py
```

Или через systemd (см. ниже).

## 🐧 Systemd сервис

Создайте `/etc/systemd/system/bolysubot.service`:

```ini
[Unit]
Description=BolySuBot Telegram Bot
After=network.target postgresql.service

[Service]
Type=simple
User=your_user
WorkingDirectory=/path/to/bolysubot
Environment="PATH=/path/to/bolysubot/.venv/bin"
ExecStart=/path/to/bolysubot/.venv/bin/python app_combined.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Активируйте:
```bash
sudo systemctl daemon-reload
sudo systemctl enable bolysubot
sudo systemctl start bolysubot
sudo systemctl status bolysubot
```

Логи:
```bash
sudo journalctl -u bolysubot -f
```

## 🧪 Тестирование webhook

### 1. Проверка здоровья:
```bash
curl http://localhost:8000/health
```

Ответ:
```json
{
  "status": "healthy",
  "bot_mode": "webhook"
}
```

### 2. Проверка webhook в Telegram:

```bash
curl "https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getWebhookInfo"
```

Должно показать:
```json
{
  "ok": true,
  "result": {
    "url": "https://yourdomain.com/webhook/bot",
    "has_custom_certificate": false,
    "pending_update_count": 0,
    "max_connections": 40
  }
}
```

### 3. Ручное тестирование webhook:

```bash
curl -X POST https://yourdomain.com/webhook/bot \
  -H "Content-Type: application/json" \
  -H "X-Telegram-Bot-Api-Secret-Token: your_secret" \
  -d '{"update_id": 123456789}'
```

## 📊 Мониторинг

### Логирование

Приложение логирует:
- Установку webhook
- Входящие обновления
- Ошибки обработки
- Проверку секретного токена

### Метрики

Добавьте endpoint для метрик:

```python
from fastapi import FastAPI

@app.get("/metrics")
async def metrics():
    return {
        "updates_processed": counter,
        "errors": error_count,
        "uptime": uptime_seconds
    }
```

## 🔧 Troubleshooting

### Webhook не работает

1. **Проверьте HTTPS:**
   ```bash
   curl -I https://yourdomain.com
   ```

2. **Проверьте доступность:**
   ```bash
   curl https://yourdomain.com/health
   ```

3. **Проверьте webhook в Telegram:**
   ```bash
   curl "https://api.telegram.org/bot<TOKEN>/getWebhookInfo"
   ```

4. **Удалите webhook и установите заново:**
   ```bash
   curl "https://api.telegram.org/bot<TOKEN>/deleteWebhook"
   curl -X POST "https://api.telegram.org/bot<TOKEN>/setWebhook" \
     -d "url=https://yourdomain.com/webhook/bot"
   ```

### Бот не отвечает

1. Проверьте логи приложения
2. Убедитесь что Nginx проксирует запросы
3. Проверьте что порт 8000 открыт
4. Проверьте firewall

### Ошибка "Invalid secret token"

Убедитесь что `WEBHOOK_SECRET` в `.env` совпадает с токеном при установке webhook.

## 🚀 Best Practices

1. **Всегда используйте HTTPS в продакшене**
2. **Устанавливайте секретный токен**
3. **Используйте reverse proxy (Nginx)**
4. **Настройте автозапуск через systemd**
5. **Мониторьте логи и метрики**
6. **Делайте регулярные бэкапы БД**
7. **Обновляйте зависимости**

## 📚 Дополнительная информация

- [Telegram Bot API - setWebhook](https://core.telegram.org/bots/api#setwebhook)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Nginx Configuration](https://nginx.org/en/docs/)
- [Let's Encrypt](https://letsencrypt.org/)

---

**Webhook готов к использованию!** 🎉


