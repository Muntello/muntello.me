# Muntello Support Bot

Telegram support bot with ticket management system for handling user support requests.

## Features

- Ticket creation from any message
- Support chat integration with threaded replies
- Ticket status tracking (open/pending/resolved/closed)
- Response forwarding between users and support team
- Webhook-based updates for real-time notifications

## Prerequisites

- Python 3.11 or higher
- SQLite database
- Telegram Bot Token (from [@BotFather](https://t.me/botfather))
- Support chat/group with topic/thread support

## Installation

### 1. Clone and Setup

```bash
# Navigate to project directory
cd /Users/muntello/pets/muntello.me/.worktrees/feature-support-bot

# Create virtual environment
python3.11 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install dependencies
pip install -r requirements.txt
pip install -e ".[dev]"
```

### 2. Configuration

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your configuration
nano .env
```

Required environment variables:

- `TELEGRAM_BOT_TOKEN` - Your bot token from @BotFather
- `SUPPORT_CHAT_ID` - Support chat/group ID (e.g., -1005237566869)
- `WEBHOOK_URL` - Public webhook URL (e.g., https://support.muntello.me)
- `DATABASE_URL` - Database connection string
- `DEBUG` - Enable debug mode (True/False)
- `LOG_LEVEL` - Logging level (DEBUG/INFO/WARNING/ERROR)

### 3. Database Setup

The database will be automatically initialized on first run. By default, it uses SQLite at:

```
/var/lib/muntello/bot.db
```

Ensure the directory exists and has proper permissions:

```bash
sudo mkdir -p /var/lib/muntello
sudo chown $USER:$USER /var/lib/muntello
```

## Development

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/test_handlers.py
```

### Code Quality

```bash
# Format and lint code
ruff check src/ tests/
ruff format src/ tests/
```

### Running Locally

```bash
# Activate virtual environment
source venv/bin/activate

# Run the bot
python -m src.main
```

## Architecture

```
src/
├── main.py              # Application entry point
├── config.py            # Configuration management
├── bot/
│   ├── handlers.py      # Message and callback handlers
│   └── middleware.py    # Bot middleware
├── api/
│   └── webhook.py       # FastAPI webhook endpoints
└── db/
    ├── models.py        # Database models
    └── repository.py    # Data access layer
```

## Deployment

The bot is designed to run with webhook-based updates:

1. Deploy to server with public HTTPS endpoint
2. Configure webhook URL in `.env`
3. Run with uvicorn:

```bash
uvicorn src.main:app --host 0.0.0.0 --port 8000
```

For production, use a process manager like systemd or supervisor.

## License

Proprietary - All rights reserved

## Support

For issues or questions, contact the development team.
