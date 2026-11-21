# Деплой в продакшен

Стек: `docker-compose.prod.yml` — PostgreSQL + приложение (бот через webhook + админка) + Caddy (автоматический HTTPS).
Наружу открыты только порты 80/443 (Caddy); база и приложение доступны только внутри docker-сети.

Инструкция рассчитана на чистый VPS с Ubuntu 22.04/24.04.

## 0. Подготовка

1. **Прод-бот** — в [@BotFather](https://t.me/BotFather) выполнить `/newbot`, сохранить токен.
   Тестовый токен на проде не использовать — dev и прод будут мешать друг другу.
2. **Сервер** — VPS от 1 vCPU / 1 ГБ RAM / 20 ГБ диска.
3. **Домен** — A-запись `bot.example.kz` → IP сервера. Проверка: `dig +short bot.example.kz` возвращает IP.
   **DNS должен работать до первого запуска**, иначе Caddy не получит сертификат.

## 1. Docker и firewall

```bash
ssh root@IP

# Docker + плагин compose
curl -fsSL https://get.docker.com | sh

# Firewall: только SSH и HTTP(S)
ufw allow 22/tcp && ufw allow 80/tcp && ufw allow 443/tcp
ufw enable
```

## 2. Код

```bash
git clone <URL репозитория> /opt/osialmaty
cd /opt/osialmaty
```

## 3. Конфиг `.env.prod`

```bash
cp .env.prod.example .env.prod
chmod 600 .env.prod

# сгенерировать секреты (запустить 4 раза)
python3 -c "import secrets; print(secrets.token_hex(32))"

nano .env.prod
```

| Переменная | Значение |
|---|---|
| `DOMAIN` | `bot.example.kz` (без `https://`) |
| `WEBHOOK_HOST` | `https://bot.example.kz` (тот же домен) |
| `BOT_TOKEN` | токен прод-бота |
| `POSTGRES_PASSWORD` | секрет №1 — **только hex**, без спецсимволов (подставляется в URL подключения) |
| `ADMIN_PASSWORD` | секрет №2 |
| `ADMIN_SECRET_KEY` | секрет №3 |
| `WEBHOOK_SECRET` | секрет №4 |
| `ADMIN_TELEGRAM_IDS` | ваш Telegram ID (узнать у @userinfobot) |
| `ACCESS_MODE` | `open` / `whitelist` / `invite_only` |

Остальное оставить как в шаблоне: `USE_WEBHOOK=True`, `DEBUG=False`, `SESSION_HTTPS_ONLY=True`.

Приложение не запустится, если при `USE_WEBHOOK=True` не задан `WEBHOOK_SECRET` или `WEBHOOK_HOST` не начинается с `https://`.

## 4. Запуск

```bash
cd /opt/osialmaty
docker compose --env-file .env.prod -f docker-compose.prod.yml up -d --build
```

Первая сборка — 2–3 минуты. Миграции накатываются автоматически при старте контейнера `app` (`docker-entrypoint.sh` → `alembic upgrade head`).

Алиас, чтобы не писать длинную команду:

```bash
echo "alias dc='docker compose --env-file /opt/osialmaty/.env.prod -f /opt/osialmaty/docker-compose.prod.yml'" >> ~/.bashrc
source ~/.bashrc
```

Дальше в инструкции используется `dc`.

## 5. Проверка

```bash
dc ps                                  # все 3 контейнера Up, app — (healthy)
dc logs app | head -30                 # миграции до head, без ошибок
dc logs caddy | grep -i certificate    # "certificate obtained successfully"

curl https://bot.example.kz/health     # {"status":"healthy","bot_mode":"webhook"}

# webhook зарегистрирован в Telegram
. ./.env.prod && curl -s "https://api.telegram.org/bot$BOT_TOKEN/getWebhookInfo"
#   "url": "https://bot.example.kz/webhook", без "last_error_message"
```

Вручную:
1. Открыть `https://bot.example.kz/admin` и войти.
2. Написать боту `/start`.

## 6. Начальные данные

В админке создать:
1. **Регионы** — без хотя бы одного региона бот не даст пройти `/start`.
2. **Категории** (иерархия через поле «Родитель»).
3. **Исполнителей.**

## 7. Бэкапы базы

```bash
mkdir -p /opt/backups
cat > /opt/osialmaty-backup.sh <<'EOF'
#!/bin/sh
set -e
cd /opt/osialmaty
. ./.env.prod
docker compose --env-file .env.prod -f docker-compose.prod.yml exec -T postgres \
  pg_dump -U "$POSTGRES_USER" "$POSTGRES_DB" | gzip > /opt/backups/db-$(date +%F).sql.gz
find /opt/backups -name 'db-*.sql.gz' -mtime +14 -delete
EOF
chmod +x /opt/osialmaty-backup.sh

/opt/osialmaty-backup.sh && ls -lh /opt/backups      # пробный запуск
(crontab -l 2>/dev/null; echo "0 3 * * * /opt/osialmaty-backup.sh") | crontab -
```

Бэкапы на том же сервере не спасут при потере сервера — периодически забирайте их к себе
(`scp root@IP:/opt/backups/* .`) или настройте выгрузку в облако.

Восстановление:

```bash
gunzip -c /opt/backups/db-ДАТА.sql.gz | dc exec -T postgres psql -U osialmatybot osialmatybot
```

## 8. Обновление

```bash
cd /opt/osialmaty
/opt/osialmaty-backup.sh     # бэкап перед обновлением
git pull
dc up -d --build             # пересоберёт app и накатит новые миграции
dc logs -f app               # Ctrl+C, когда убедитесь, что всё ок
```

**Откат:**

```bash
git checkout <предыдущий коммит>
dc up -d --build
```

Если в обновлении была миграция, откат кода её не отменит: восстановите базу из бэкапа,
сделанного перед обновлением, или выполните `dc exec app alembic downgrade -1`.

## Диагностика

| Симптом | Что проверить |
|---|---|
| `app` в статусе restarting | `dc logs app` — чаще всего ошибка в `.env.prod`: пустой `WEBHOOK_SECRET`, `WEBHOOK_HOST` не `https://`, пустой токен |
| Caddy не получает сертификат | DNS ещё не указывает на сервер или закрыты порты 80/443 |
| Бот молчит | `getWebhookInfo` → `last_error_message`; `dc logs app`. Webhook с неверным секретом отвечает 401 |
| Не входит в админку | Заходить строго по `https://` — cookie с флагом `secure` по http не передаётся |
