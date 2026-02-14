# Support Bot Design Document

**Date:** 2026-02-14
**Status:** Approved
**Domain:** support.muntello.me
**Server:** Ubuntu 22.04, 512MB RAM, 20GB SSD, 1 CPU

## Overview

Customer support system через Telegram бот с автоматическим управлением тикетами, веб-хуками и планами расширения до веб-виджета.

## Architecture

### System Components

```
Internet
    ↓
[Caddy :443] → HTTPS + auto SSL (Let's Encrypt)
    ↓
[FastAPI :8000] → Python app в venv, управляется systemd
    ↓
[SQLite] → /var/lib/muntello/bot.db

[Telegram API] ← webhook → [FastAPI]
```

### Data Flow (MVP)

1. **Пользователь → Бот:** Сообщение в Telegram
2. **Telegram → FastAPI:** Webhook на `https://support.muntello.me/webhook/telegram`
3. **FastAPI → DB:** Сохранение в SQLite
4. **FastAPI → Telegram API:** Пересылка в чат сотрудников (PEER ID 5237566869)
5. **Сотрудник → Reply:** Ответ через reply
6. **Telegram → FastAPI:** Webhook получает reply
7. **FastAPI → Telegram API:** Отправка пользователю

### Technology Stack

- **Caddy 2:** Reverse proxy, автоматический HTTPS
- **FastAPI:** Async Python фреймворк для API
- **aiogram 3:** Async библиотека для Telegram Bot API
- **SQLAlchemy + aiosqlite:** Async ORM для SQLite
- **systemd:** Управление приложением
- **GitHub Actions:** CI/CD автоматизация

## Project Structure

```
muntello.me/
├── .github/
│   └── workflows/
│       └── deploy.yml                 # CI/CD pipeline
├── app/
│   ├── __init__.py
│   ├── main.py                        # FastAPI приложение
│   ├── config.py                      # Конфигурация из .env
│   ├── database.py                    # SQLAlchemy setup
│   ├── models.py                      # DB модели
│   ├── bot/
│   │   ├── __init__.py
│   │   ├── handlers.py                # Telegram обработчики
│   │   ├── filters.py                 # Кастомные фильтры
│   │   └── keyboards.py               # Клавиатуры
│   ├── api/
│   │   ├── __init__.py
│   │   ├── webhook.py                 # Telegram webhook endpoint
│   │   └── health.py                  # Health check endpoint
│   └── utils/
│       ├── __init__.py
│       └── logger.py                  # Логирование
├── tests/
│   ├── __init__.py
│   ├── test_handlers.py
│   └── test_api.py
├── deployment/
│   ├── systemd/
│   │   └── muntello-bot.service       # systemd unit
│   ├── caddy/
│   │   └── Caddyfile                  # Caddy config
│   └── scripts/
│       ├── setup-server.sh            # Начальная настройка
│       └── deploy.sh                  # Скрипт деплоя
├── .env.example                       # Пример переменных
├── requirements.txt                   # Python зависимости
├── pyproject.toml                     # Poetry/pip config
└── README.md                          # Документация
```

## Database Schema

### Ticket Status Flow

```python
class TicketStatus(str, Enum):
    OPEN = "open"                      # Новый тикет
    WAITING_SUPPORT = "waiting_support"  # Ждем ответа сотрудника
    WAITING_USER = "waiting_user"      # Ждем ответа пользователя
    CLOSED = "closed"                  # Закрыт
```

### Models

**User:**
- `id` (PK): Telegram user_id
- `username`: Telegram username
- `first_name`, `last_name`: Имя пользователя
- `created_at`, `last_activity`: Временные метки
- `is_blocked`: Флаг блокировки

**Ticket:**
- `id` (PK, autoincrement): ID обращения
- `user_id` (FK): Связь с пользователем
- `status`: Статус (enum)
- `created_at`, `updated_at`, `closed_at`: Временные метки
- `closed_by`: "staff", "auto", "user"
- `support_thread_id`: ID сообщения-треда в чате сотрудников
- `reopened_at`: Дата переоткрытия (если было)

**Message:**
- `id` (PK): ID сообщения
- `ticket_id` (FK): Связь с тикетом
- `telegram_message_id`: ID в Telegram
- `is_from_user`: True = от пользователя, False = от сотрудника
- `text`: Текст сообщения
- `created_at`: Временная метка

**PendingMessage:**
- `id` (PK): ID
- `user_id` (FK): Пользователь
- `text`: Текст сообщения
- `telegram_message_id`: ID в Telegram
- `support_notification_id`: ID уведомления в чате сотрудников
- `created_at`: Временная метка

### Ticket Lifecycle

**Новое сообщение от пользователя:**
- Если есть активный тикет (статус != CLOSED) → продолжаем, меняем статус на WAITING_SUPPORT
- Если нет активного:
  - Был закрытый тикет → создаем PendingMessage, отправляем в чат выбор (новый/переоткрыть)
  - Первое обращение → создаем новый тикет со статусом WAITING_SUPPORT

**Ответ сотрудника (reply):**
- Находим тикет по support_thread_id
- Сохраняем сообщение (is_from_user=False)
- Меняем статус на WAITING_USER
- Отправляем пользователю

**Команда /close:**
- Закрываем тикет (статус CLOSED, closed_by="staff")
- Уведомляем пользователя: "✅ Обращение #123 закрыто"

**Автозакрытие:**
- Если тикет в статусе WAITING_USER более 24 часов без активности
- Статус CLOSED, closed_by="auto"
- Уведомляем пользователя: "⏱ Обращение #123 автоматически закрыто"

**Выбор сотрудника (новый/переоткрыть):**
- Inline кнопки: "📝 Новое обращение" / "🔄 Переоткрыть #123"
- Callback query обрабатывает выбор
- PendingMessage связывается с тикетом и удаляется

## Security Configuration

### Server Hardening

**User Management:**
```bash
# Непривилегированный пользователь
useradd -m -s /bin/bash deploy
usermod -aG sudo deploy
```

**SSH Hardening:**
```
PermitRootLogin no
PasswordAuthentication no
PubkeyAuthentication yes
```

**Firewall (ufw):**
```bash
ufw allow 22/tcp   # SSH
ufw allow 80/tcp   # HTTP (Let's Encrypt)
ufw allow 443/tcp  # HTTPS
```

**Additional:**
- Fail2ban для защиты от брутфорса
- Unattended-upgrades для автообновлений безопасности

### Directory Permissions

```
/opt/muntello/           # deploy:deploy (755)
/var/lib/muntello/       # deploy:deploy, БД (600)
/var/log/muntello/       # deploy:deploy (755)
/etc/muntello/.env       # deploy:deploy (600) - СЕКРЕТЫ
```

## Caddy Configuration

```caddy
support.muntello.me {
    reverse_proxy localhost:8000 {
        health_uri /health
        health_interval 10s
        health_timeout 5s
    }

    log {
        output file /var/log/caddy/support.log
        format json
    }

    header {
        X-Content-Type-Options "nosniff"
        X-Frame-Options "DENY"
        X-XSS-Protection "1; mode=block"
        -Server
    }
}
```

**Автоматический HTTPS:**
- Let's Encrypt сертификат
- Автообновление сертификата
- HTTP → HTTPS редирект

## FastAPI Application

### Configuration

```python
class Settings(BaseSettings):
    TELEGRAM_BOT_TOKEN: str
    SUPPORT_CHAT_ID: int = 5237566869
    WEBHOOK_URL: str = "https://support.muntello.me"
    DATABASE_URL: str = "sqlite+aiosqlite:///var/lib/muntello/bot.db"
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"

    class Config:
        env_file = "/etc/muntello/.env"
```

### Lifespan Management

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await init_db()
    bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)
    dp = Dispatcher()
    setup_handlers(dp)
    await bot.set_webhook(f"{settings.WEBHOOK_URL}/webhook/telegram")

    yield

    # Shutdown
    await bot.delete_webhook()
    await bot.session.close()
```

### API Endpoints

- `POST /webhook/telegram` - Telegram webhook
- `GET /health` - Health check
- `GET /metrics` - Базовые метрики

## Telegram Bot Handlers

### User Message Handler

```python
@router.message(F.chat.type == "private")
async def handle_user_message(message: Message):
    user = await get_or_create_user(message.from_user)
    active_ticket = await get_active_ticket(user.id)

    if active_ticket:
        # Продолжаем тикет
        await add_message(active_ticket, message.text, is_from_user=True)
        active_ticket.status = TicketStatus.WAITING_SUPPORT
    else:
        last_closed = await get_last_closed_ticket(user.id)
        if last_closed:
            # Выбор: новый/переоткрыть
            await send_choice_to_support(user, message.text, last_closed.id)
        else:
            # Первый раз
            ticket = await create_ticket(user.id)
            await add_message(ticket, message.text, is_from_user=True)
```

### Support Reply Handler

```python
@router.message(F.chat.id == settings.SUPPORT_CHAT_ID, F.reply_to_message)
async def handle_support_reply(message: Message):
    ticket = await get_ticket_by_support_thread_id(message.reply_to_message.message_id)

    if message.text.startswith("/close"):
        await close_ticket(ticket, closed_by="staff")
        await notify_user(ticket.user_id, f"✅ Обращение #{ticket.id} закрыто")
    else:
        await add_message(ticket, message.text, is_from_user=False)
        ticket.status = TicketStatus.WAITING_USER
        await message.bot.send_message(ticket.user_id, message.text)
```

### Callback Handlers

```python
@router.callback_query(F.data.startswith("new_ticket:"))
async def handle_new_ticket_callback(callback: CallbackQuery):
    # Создание нового тикета из pending

@router.callback_query(F.data.startswith("reopen_ticket:"))
async def handle_reopen_ticket_callback(callback: CallbackQuery):
    # Переоткрытие закрытого тикета
```

## CI/CD Pipeline

### GitHub Actions Workflow

**On push to main:**
1. **Test Job:**
   - pytest с coverage
   - ruff linting

2. **Deploy Job:**
   - SSH на сервер
   - git pull
   - pip install -r requirements.txt
   - systemctl restart muntello-bot
   - Health check

3. **Notify Job:**
   - Telegram уведомление о статусе

### GitHub Secrets

```
SERVER_HOST=<IP сервера>
SSH_PRIVATE_KEY=<deploy user key>
TELEGRAM_ADMIN_CHAT_ID=<admin chat>
TELEGRAM_BOT_TOKEN=<bot token>
```

## Monitoring & Logging

### Structured Logging

- **Format:** JSON (pythonjsonlogger)
- **Destinations:**
  - `/var/log/muntello/app.log` (rotating, 10MB, 5 backups)
  - stdout → systemd journald

### Key Events

```python
logger.info("ticket_created", extra={"ticket_id": ticket.id, "user_id": user.id})
logger.info("ticket_closed", extra={"ticket_id": ticket.id, "closed_by": "staff"})
logger.warning("pending_message_expired", extra={"pending_id": pending.id})
logger.error("telegram_api_error", extra={"error": str(e)})
```

### Health Check

```python
@router.get("/health")
async def health_check():
    # Проверка БД
    # Возврат статуса: healthy/unhealthy
```

### Metrics

```python
@router.get("/metrics")
async def metrics():
    return {
        "active_tickets": count,
        "messages_last_hour": count,
        "timestamp": now
    }
```

### External Monitoring (рекомендуется)

- **UptimeRobot:** Проверка https://support.muntello.me/health
- **Sentry:** Отлов ошибок Python (free tier)

## Deployment Process

### Initial Server Setup

1. Обновление системы
2. Создание пользователя deploy с SSH ключами
3. SSH hardening (no root, no password)
4. Firewall (ufw)
5. Fail2ban
6. Автообновления
7. Установка Python 3.11, Caddy
8. Создание директорий

### Application Deployment

1. Git clone репозитория
2. Python venv + pip install
3. Создание .env файла
4. Инициализация БД
5. Настройка systemd сервиса
6. Настройка Caddy
7. Запуск и проверка

### Environment Variables

```bash
TELEGRAM_BOT_TOKEN=<token>
SUPPORT_CHAT_ID=-1005237566869
WEBHOOK_URL=https://support.muntello.me
DATABASE_URL=sqlite+aiosqlite:///var/lib/muntello/bot.db
DEBUG=False
LOG_LEVEL=INFO
```

## Future Enhancements

1. **Автоматизация обработки запросов:**
   - AI-assisted responses
   - Автоматическая категоризация
   - FAQ бот

2. **Web Widget:**
   - JavaScript виджет для сайта
   - WebSocket для real-time
   - История переписки

3. **Analytics:**
   - Дашборд метрик
   - Время ответа
   - Satisfaction ratings

4. **Scalability:**
   - Миграция на PostgreSQL
   - Redis для кеширования
   - Horizontal scaling

## Resource Usage (512MB RAM)

- OS + системные процессы: ~200MB
- FastAPI приложение: ~80MB
- Caddy: ~15MB
- **Остаток:** ~200MB для роста и кеша

SQLite выбран для нулевого потребления RAM и достаточной производительности для 10k+ пользователей.

## Success Criteria

- ✅ Автоматическое развертывание через GitHub Actions
- ✅ HTTPS с автообновлением сертификатов
- ✅ Структурированное логирование
- ✅ Health check мониторинг
- ✅ Автоматическое управление статусами тикетов
- ✅ Уведомления о закрытии
- ✅ Переоткрытие тикетов
- ✅ Отображение номеров обращений
