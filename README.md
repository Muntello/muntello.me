# Muntello Support Bot

Telegram-бот для поддержки с автоматическим управлением тикетами и двусторонней коммуникацией между клиентами и командой поддержки.

## Features

### Core Functionality
- **Automatic Ticket Creation**: Создание тикетов из сообщений в Telegram
- **Two-Way Communication**: Двусторонний обмен сообщениями между клиентами и поддержкой
- **Status Tracking**: Отслеживание статусов (open/waiting_support/waiting_user/closed)
- **Pending Messages**: Умная обработка сообщений от пользователей с закрытыми тикетами (переоткрытие / новый тикет)
- **Health Monitoring**: Эндпоинты `/health` и `/metrics`

### Technical Features
- FastAPI webhook-сервер с aiogram 3
- SQLite (aiosqlite) для хранения данных
- Structured JSON logging
- Systemd + Caddy с автоматическим HTTPS
- CI/CD через GitHub Actions

## Architecture

```
app/
├── main.py                 # FastAPI application, bot setup, lifespan
├── config.py               # Pydantic Settings (env vars)
├── models.py               # SQLAlchemy ORM models (User, Ticket, Message, PendingMessage)
├── database.py             # Database engine, session, init_db()
├── api/
│   ├── health.py           # GET /health, GET /metrics
│   └── webhook.py          # POST /webhook/telegram
├── bot/
│   ├── handlers.py         # Message and callback handlers
│   ├── filters.py          # PrivateChatFilter, SupportChatFilter
│   └── keyboards.py        # Inline keyboard utilities
├── services/
│   └── ticket_service.py   # Ticket business logic
└── utils/
    └── logger.py           # Structured logging setup

deployment/
├── scripts/
│   ├── setup-server.sh     # Server initialization (one-time)
│   └── deploy-app.sh       # Application deployment
├── systemd/
│   └── muntello-bot.service
└── caddy/
    └── Caddyfile

tests/
├── test_config.py
├── test_database.py
├── test_models.py
├── test_health_api.py
└── test_ticket_service.py
```

## Prerequisites

### Production Server
- Ubuntu 22.04+
- Python 3.11+
- Caddy web server
- Systemd

### Development Environment
- Python 3.11+
- Git

### External Services
- Telegram Bot Token (от [@BotFather](https://t.me/botfather))
- Домен с настроенным DNS

## Quick Start (Development)

### 1. Clone and Setup

```bash
git clone https://github.com/Muntello/muntello.me.git
cd muntello.me

python3.11 -m venv venv
source venv/bin/activate

pip install --upgrade pip
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
cp .env.example .env
nano .env
```

**Environment Variables:**

```bash
# Telegram
TELEGRAM_BOT_TOKEN=YOUR_BOT_TOKEN_HERE               # От @BotFather
TELEGRAM_WEBHOOK_SECRET=GENERATE_RANDOM_32_CHAR_STRING  # openssl rand -hex 32
SUPPORT_CHAT_ID=-100XXXXXXXXXXXXX                    # ID чата поддержки
WEBHOOK_URL=https://support.muntello.me              # Public URL для webhook

# Database
DATABASE_URL=sqlite+aiosqlite:////var/lib/muntello/bot.db

# Application
DEBUG=False
LOG_LEVEL=INFO                                       # DEBUG/INFO/WARNING/ERROR
```

### 3. Run Locally

```bash
# Start the application
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

# Для локального тестирования webhook нужен туннель
ngrok http 8000
# Обновить WEBHOOK_URL в .env на URL от ngrok
```

### 4. Run Tests

```bash
pytest tests/ -v

# С покрытием
pytest tests/ --cov=app --cov-report=html
```

## Production Deployment

### Automated Deployment

```bash
# 1. Настройка сервера (одноразово)
ssh root@your-server.com
bash deployment/scripts/setup-server.sh

# 2. Деплой приложения
ssh deploy@your-server.com
bash deployment/scripts/deploy-app.sh
```

### Manual Deployment Steps

<details>
<summary>Click to expand manual deployment guide</summary>

#### 1. Server Preparation

```bash
sudo apt update
sudo apt install -y python3.11 python3.11-venv caddy git

sudo useradd -r -m -d /opt/muntello -s /bin/bash deploy
```

#### 2. Application Setup

```bash
sudo -u deploy git clone https://github.com/Muntello/muntello.me.git /opt/muntello
cd /opt/muntello

sudo -u deploy python3.11 -m venv venv
sudo -u deploy venv/bin/pip install --upgrade pip
sudo -u deploy venv/bin/pip install -r requirements.txt

# Environment
sudo mkdir -p /etc/muntello
sudo cp .env.example /etc/muntello/.env
sudo nano /etc/muntello/.env  # Заполнить реальные значения
sudo chown -R deploy:deploy /etc/muntello
sudo chmod 600 /etc/muntello/.env

# Database directory
sudo mkdir -p /var/lib/muntello
sudo chown deploy:deploy /var/lib/muntello
```

#### 3. Systemd Service

```bash
sudo cp deployment/systemd/muntello-bot.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable muntello-bot
sudo systemctl start muntello-bot
sudo systemctl status muntello-bot
```

#### 4. Caddy Web Server

```bash
# Убедиться, что DNS настроен
dig support.muntello.me

# Установить конфигурацию
sudo cp deployment/caddy/Caddyfile /etc/caddy/
sudo systemctl reload caddy
sudo systemctl status caddy
```

</details>

### GitHub Actions CI/CD

GitHub Secrets:

```
SSH_PRIVATE_KEY        # SSH key для доступа к серверу
SERVER_HOST            # Hostname/IP сервера
DEPLOY_USER            # Пользователь деплоя (deploy)
TELEGRAM_BOT_TOKEN     # Для уведомлений о деплое
TELEGRAM_CHANNEL_ID    # Канал для уведомлений
```

Pipeline:
1. **Test**: pytest на каждый push и PR
2. **Deploy**: SSH деплой на сервер (только main branch)
3. **Verify**: Health check и проверка сервиса
4. **Notify**: Telegram уведомление о статусе деплоя

## Configuration Reference

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `TELEGRAM_BOT_TOKEN` | Yes | - | Bot token от @BotFather |
| `TELEGRAM_WEBHOOK_SECRET` | Yes | - | Secret для верификации webhook |
| `SUPPORT_CHAT_ID` | No | `5237566869` | ID чата поддержки в Telegram |
| `WEBHOOK_URL` | No | `https://support.muntello.me` | Public URL для webhook |
| `DATABASE_URL` | No | `sqlite+aiosqlite:////var/lib/muntello/bot.db` | SQLite connection string |
| `LOG_LEVEL` | No | `INFO` | Уровень логирования |
| `DEBUG` | No | `False` | Debug mode |

### Security

```bash
# Генерация webhook secret
openssl rand -hex 32
```

## Monitoring and Operations

### Health Checks

```bash
# Health check
curl https://support.muntello.me/health
# {"status":"healthy","timestamp":"...","database":"ok","version":"1.0.0"}

# Metrics
curl https://support.muntello.me/metrics
# {"active_tickets":1,"messages_last_hour":21,"timestamp":"..."}
```

### Logs

```bash
# Логи бота
sudo journalctl -u muntello-bot -f
sudo journalctl -u muntello-bot -n 100
sudo journalctl -u muntello-bot --since "1 hour ago"

# Логи Caddy
sudo tail -f /var/log/caddy/support.muntello.me.log
```

### Service Management

```bash
sudo systemctl status muntello-bot
sudo systemctl restart muntello-bot
sudo systemctl stop muntello-bot
sudo journalctl -u muntello-bot --since today
```

### Database Management

```bash
# Подключение к БД (на сервере через Python, sqlite3 не установлен)
/opt/muntello/venv/bin/python -c "
import sqlite3
conn = sqlite3.connect('/var/lib/muntello/bot.db')
cursor = conn.cursor()
cursor.execute('SELECT * FROM tickets')
for row in cursor.fetchall():
    print(row)
conn.close()
"

# Бэкап
cp /var/lib/muntello/bot.db /var/lib/muntello/bot.db.backup

# Размер БД
ls -lh /var/lib/muntello/bot.db
```

## Troubleshooting

### Bot not receiving messages

1. Проверить webhook: `curl https://api.telegram.org/bot<TOKEN>/getWebhookInfo`
2. Проверить DNS и HTTPS: `curl https://support.muntello.me/health`
3. Проверить Caddy: `sudo journalctl -u caddy -f`
4. Проверить сервис: `sudo systemctl status muntello-bot`

### Database errors

1. Проверить файл БД: `ls -la /var/lib/muntello/bot.db`
2. Проверить права: `stat /var/lib/muntello/bot.db`
3. Проверить `.env`: `cat /etc/muntello/.env`
4. Проверить логи: `sudo journalctl -u muntello-bot --since "10 min ago"`

### Debug Mode

```bash
sudo nano /etc/muntello/.env
# Установить DEBUG=True и LOG_LEVEL=DEBUG

sudo systemctl restart muntello-bot
sudo journalctl -u muntello-bot -f
```

## Server Info

| Parameter | Value |
|-----------|-------|
| Domain | support.muntello.me |
| OS | Ubuntu 22.04 |
| Python | 3.11 |
| App path | /opt/muntello |
| Config | /etc/muntello/.env |
| Database | /var/lib/muntello/bot.db |
| Logs | journalctl -u muntello-bot |

## Contributing

### Workflow

1. `git checkout -b feature/your-feature`
2. Внести изменения и добавить тесты
3. `pytest tests/ -v`
4. `ruff check app/ tests/`
5. `git commit -m "feat: description"`
6. Push и создать PR

### Commit Format

- `feat:` New features
- `fix:` Bug fixes
- `docs:` Documentation
- `test:` Tests
- `refactor:` Refactoring
- `chore:` Maintenance

## FAQ

**Q: Какая база данных используется?**
A: SQLite через aiosqlite. Файл БД хранится в `/var/lib/muntello/bot.db`.

**Q: Как кастомизировать workflow тикетов?**
A: Изменить статусы в `app/models.py` (TicketStatus enum) и логику обработки в `app/bot/handlers.py`.

**Q: Можно ли запустить несколько ботов?**
A: Да, деплоить отдельные инстансы с разными конфигурациями.

## License

Proprietary - All rights reserved

## Acknowledgments

Built with:
- [FastAPI](https://fastapi.tiangolo.com/) - Web framework
- [aiogram](https://aiogram.dev/) - Telegram Bot API
- [SQLAlchemy](https://www.sqlalchemy.org/) - Database ORM
- [Caddy](https://caddyserver.com/) - Web server with automatic HTTPS
