# Muntello Support Bot

A production-ready Telegram support bot with Linear integration for automated ticket management and customer support workflows.

## Features

### Core Functionality
- **Automatic Ticket Creation**: Creates Linear issues from Telegram messages
- **Two-Way Communication**: Bidirectional messaging between customers and support team
- **Status Tracking**: Real-time ticket status updates (open/in-progress/resolved/closed)
- **Linear Integration**: Syncs tickets with Linear project management
- **Webhook Updates**: Real-time notifications for ticket changes
- **Health Monitoring**: Built-in health checks and metrics

### Technical Features
- FastAPI-based webhook server
- PostgreSQL database with connection pooling
- Comprehensive logging with structured output
- Security-hardened deployment configuration
- Automatic HTTPS with Caddy
- CI/CD pipeline with GitHub Actions

## Architecture

```
app/
├── main.py                 # FastAPI application and webhook setup
├── config.py              # Configuration management with Pydantic
├── utils/
│   └── logging.py         # Structured logging utility
├── database/
│   ├── connection.py      # Database connection and session management
│   ├── models.py          # SQLAlchemy ORM models
│   └── service.py         # Database service layer
├── telegram/
│   ├── handlers.py        # Message and callback handlers
│   └── keyboards.py       # Telegram keyboard utilities
└── api/
    ├── health.py          # Health check endpoints
    └── webhook.py         # Telegram webhook handler

deployment/
├── scripts/               # Deployment automation
│   ├── server-setup.sh    # Server initialization
│   └── deploy.sh          # Application deployment
├── systemd/              # Service configuration
│   └── muntello-bot.service
└── caddy/                # Web server configuration
    └── Caddyfile

tests/                     # Comprehensive test suite
├── test_config.py
├── test_database.py
├── test_handlers.py
└── test_webhook.py
```

## Prerequisites

### Production Server
- Ubuntu 20.04+ or CentOS 8+
- Python 3.11 or higher
- PostgreSQL 15+
- Caddy web server
- Systemd for service management

### Development Environment
- Python 3.11+
- PostgreSQL 15+ (or Docker for local testing)
- Git

### External Services
- Telegram Bot Token (from [@BotFather](https://t.me/botfather))
- Linear account with API access
- Domain name with DNS configured

## Quick Start (Development)

### 1. Clone and Setup

```bash
# Clone repository
git clone https://github.com/Muntello/muntello.me.git
cd muntello.me

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
# Copy environment template
cp .env.example .env

# Edit configuration
nano .env
```

**Required Environment Variables:**

```bash
# Telegram Configuration
TELEGRAM_BOT_TOKEN=your_bot_token_here              # From @BotFather
TELEGRAM_CHANNEL_ID=-100XXXXXXXXXXXXX               # Support channel ID

# Linear Configuration
LINEAR_API_KEY=lin_api_XXXXXXXXXXXXXXXXXXXXXXXX     # Linear API key
LINEAR_TEAM_ID=your-team-id                         # Linear team ID

# Database Configuration
DATABASE_URL=postgresql://user:password@localhost:5432/dbname

# Security
WEBHOOK_SECRET=random_32_character_secret_here      # Generate with: openssl rand -hex 32

# Application Settings
ENVIRONMENT=development                             # development/production
LOG_LEVEL=INFO                                      # DEBUG/INFO/WARNING/ERROR
DEBUG=True                                          # Enable debug mode
```

### 3. Database Setup

```bash
# Using Docker (recommended for development)
docker run -d \
  --name postgres-dev \
  -e POSTGRES_USER=muntello \
  -e POSTGRES_PASSWORD=devpassword \
  -e POSTGRES_DB=support_bot \
  -p 5432:5432 \
  postgres:15-alpine

# Update DATABASE_URL in .env
DATABASE_URL=postgresql://muntello:devpassword@localhost:5432/support_bot
```

### 4. Run Locally

```bash
# Start the application
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

# In another terminal, expose webhook (for local testing)
# Using ngrok or similar tunnel service
ngrok http 8000

# Update WEBHOOK_SECRET in .env with ngrok URL
```

### 5. Run Tests

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=app --cov-report=html

# Run specific test categories
pytest tests/ -v -m unit           # Unit tests only
pytest tests/ -v -m integration    # Integration tests only
```

## Production Deployment

### Automated Deployment

The recommended deployment method uses the provided automation scripts:

```bash
# 1. Run server setup (one-time)
ssh root@your-server.com
bash deployment/scripts/server-setup.sh

# 2. Deploy application
bash deployment/scripts/deploy.sh
```

See [deployment/scripts/README.md](deployment/scripts/README.md) for detailed instructions.

### Manual Deployment Steps

<details>
<summary>Click to expand manual deployment guide</summary>

#### 1. Server Preparation

```bash
# Install system dependencies
sudo apt update
sudo apt install -y python3.11 python3.11-venv postgresql-15 caddy git

# Create deployment user
sudo useradd -r -m -d /opt/muntello -s /bin/bash deploy
```

#### 2. Database Setup

```bash
# Create database and user
sudo -u postgres psql << EOF
CREATE DATABASE support_bot;
CREATE USER muntello WITH PASSWORD 'SECURE_PASSWORD_HERE';
GRANT ALL PRIVILEGES ON DATABASE support_bot TO muntello;
\c support_bot
GRANT ALL ON SCHEMA public TO muntello;
EOF
```

#### 3. Application Setup

```bash
# Clone repository
sudo -u deploy git clone https://github.com/Muntello/muntello.me.git /opt/muntello
cd /opt/muntello

# Create virtual environment
sudo -u deploy python3.11 -m venv venv
sudo -u deploy venv/bin/pip install --upgrade pip
sudo -u deploy venv/bin/pip install -r requirements.txt

# Configure environment
sudo mkdir -p /etc/muntello
sudo cp .env.example /etc/muntello/.env
sudo nano /etc/muntello/.env  # Edit with production values
sudo chown -R deploy:deploy /etc/muntello
sudo chmod 600 /etc/muntello/.env
```

#### 4. Systemd Service

```bash
# Install service file
sudo cp deployment/systemd/muntello-bot.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable muntello-bot
sudo systemctl start muntello-bot

# Check status
sudo systemctl status muntello-bot
```

#### 5. Caddy Web Server

**Configure DNS first:**
```bash
# Ensure DNS record points to your server
dig support.muntello.me  # Should show your server IP
```

**Install Caddy configuration:**
```bash
# Copy Caddyfile
sudo cp deployment/caddy/Caddyfile /etc/caddy/

# Reload Caddy
sudo systemctl reload caddy

# Check status
sudo systemctl status caddy
```

See [deployment/caddy/README.md](deployment/caddy/README.md) for detailed Caddy configuration.

</details>

### GitHub Actions CI/CD

The repository includes automated CI/CD pipeline. Configure these GitHub secrets:

```
SSH_PRIVATE_KEY        # SSH key for deployment server access
SERVER_HOST            # Production server hostname/IP
DEPLOY_USER            # Deployment user (typically 'deploy')
TELEGRAM_BOT_TOKEN     # For deployment notifications
TELEGRAM_CHANNEL_ID    # Channel for deployment status updates
```

Pipeline stages:
1. **Test**: Run pytest with PostgreSQL service container
2. **Deploy**: SSH deployment to production server (main branch only)
3. **Verify**: Health checks and service verification
4. **Notify**: Telegram notifications for deployment status

## Configuration Reference

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `TELEGRAM_BOT_TOKEN` | Yes | - | Bot token from @BotFather |
| `TELEGRAM_CHANNEL_ID` | Yes | - | Support channel ID (e.g., -100XXX) |
| `LINEAR_API_KEY` | Yes | - | Linear API authentication key |
| `LINEAR_TEAM_ID` | Yes | - | Linear team identifier |
| `DATABASE_URL` | Yes | - | PostgreSQL connection string |
| `WEBHOOK_SECRET` | Yes | - | 32+ character random secret |
| `ENVIRONMENT` | No | `production` | Environment: development/production |
| `LOG_LEVEL` | No | `INFO` | Logging level |
| `DEBUG` | No | `False` | Debug mode flag |

### Security Configuration

**IMPORTANT**: Never commit real secrets to version control.

```bash
# Generate secure webhook secret
openssl rand -hex 32

# Generate secure database password
openssl rand -base64 32
```

See [SECURITY-POLICY.md](docs/SECURITY-POLICY.md) for comprehensive security guidelines.

## Development Guide

### Project Structure

- **app/**: Core application code
  - `main.py`: FastAPI application initialization
  - `config.py`: Configuration with validation
  - `database/`: Database layer (models, connection, service)
  - `telegram/`: Telegram bot handlers and utilities
  - `api/`: REST API endpoints
  - `utils/`: Shared utilities (logging, etc.)

- **deployment/**: Production deployment configurations
  - `scripts/`: Automated deployment scripts
  - `systemd/`: Service configuration
  - `caddy/`: Web server configuration

- **tests/**: Comprehensive test suite
  - Unit tests for individual components
  - Integration tests for end-to-end workflows
  - Database tests with fixtures

### Running Tests

```bash
# All tests with verbose output
pytest tests/ -v

# With coverage report
pytest tests/ --cov=app --cov-report=term-missing --cov-report=html

# Specific test categories
pytest tests/ -m unit           # Unit tests
pytest tests/ -m integration    # Integration tests
pytest tests/ -m db             # Database tests

# Specific test files
pytest tests/test_handlers.py -v
pytest tests/test_database.py -v
```

### Code Quality

The project uses Ruff for linting and formatting:

```bash
# Check code quality
ruff check app/ tests/

# Auto-fix issues
ruff check --fix app/ tests/

# Format code
ruff format app/ tests/
```

### Database Migrations

Currently using direct SQLAlchemy models. For future migrations:

```bash
# Install Alembic
pip install alembic

# Initialize Alembic
alembic init alembic

# Create migration
alembic revision --autogenerate -m "description"

# Apply migration
alembic upgrade head
```

## Monitoring and Operations

### Health Checks

```bash
# Application health
curl http://localhost:8000/health

# Detailed health with metrics
curl http://localhost:8000/health?detailed=true

# Via public endpoint
curl https://support.muntello.me/health
```

### Logs

```bash
# Application logs (systemd)
sudo journalctl -u muntello-bot -f

# Last 100 lines
sudo journalctl -u muntello-bot -n 100

# Logs since specific time
sudo journalctl -u muntello-bot --since "1 hour ago"

# Filter by log level
sudo journalctl -u muntello-bot -p err

# Caddy logs
sudo tail -f /var/log/caddy/support.log
```

### Service Management

```bash
# Check service status
sudo systemctl status muntello-bot

# Start/stop/restart service
sudo systemctl start muntello-bot
sudo systemctl stop muntello-bot
sudo systemctl restart muntello-bot

# Reload after code changes
sudo systemctl restart muntello-bot

# Check service logs
sudo journalctl -u muntello-bot --since today
```

### Database Management

```bash
# Connect to database
psql postgresql://muntello:password@localhost/support_bot

# Backup database
pg_dump -U muntello support_bot > backup.sql

# Restore database
psql -U muntello support_bot < backup.sql

# View active connections
SELECT * FROM pg_stat_activity WHERE datname = 'support_bot';
```

## Troubleshooting

### Common Issues

**Bot not receiving messages:**
1. Check webhook is set: `curl https://api.telegram.org/bot<TOKEN>/getWebhookInfo`
2. Verify DNS and HTTPS working: `curl https://support.muntello.me/health`
3. Check Caddy logs: `sudo journalctl -u caddy -f`
4. Verify service running: `sudo systemctl status muntello-bot`

**Database connection errors:**
1. Check PostgreSQL running: `sudo systemctl status postgresql`
2. Verify credentials in `/etc/muntello/.env`
3. Test connection: `psql -U muntello -h localhost support_bot`
4. Check database logs: `sudo journalctl -u postgresql -f`

**Linear integration not working:**
1. Verify API key is valid (test with Linear API)
2. Check team ID is correct
3. Review application logs for Linear API errors
4. Ensure network can reach Linear API endpoints

### Debug Mode

Enable debug mode for verbose logging:

```bash
# Edit environment file
sudo nano /etc/muntello/.env

# Set DEBUG=True and LOG_LEVEL=DEBUG
DEBUG=True
LOG_LEVEL=DEBUG

# Restart service
sudo systemctl restart muntello-bot

# Watch detailed logs
sudo journalctl -u muntello-bot -f
```

## Testing Strategy

### Test Categories

- **Unit Tests** (`-m unit`): Test individual functions and classes
- **Integration Tests** (`-m integration`): Test component interactions
- **Database Tests** (`-m db`): Test database operations with fixtures

### Test Coverage

The project maintains high test coverage:

```bash
# Generate coverage report
pytest tests/ --cov=app --cov-report=html

# View report
open htmlcov/index.html
```

### CI/CD Testing

GitHub Actions automatically runs tests on:
- Every push to feature branches
- Every pull request to main
- Before production deployment

## Contributing

### Development Workflow

1. Create feature branch: `git checkout -b feature/your-feature`
2. Make changes and add tests
3. Run tests: `pytest tests/ -v`
4. Check code quality: `ruff check app/ tests/`
5. Commit changes: `git commit -m "feat: description"`
6. Push and create pull request

### Commit Message Format

Follow conventional commits:
- `feat:` New features
- `fix:` Bug fixes
- `docs:` Documentation changes
- `test:` Test additions/changes
- `refactor:` Code refactoring
- `chore:` Maintenance tasks

## Security

### Reporting Security Issues

Please report security vulnerabilities to security@muntello.me. Do not create public issues for security concerns.

### Security Best Practices

1. **Never commit secrets** to version control
2. **Use strong passwords** for database and services
3. **Keep dependencies updated** regularly
4. **Monitor logs** for suspicious activity
5. **Review access controls** periodically

See [SECURITY-POLICY.md](docs/SECURITY-POLICY.md) for detailed security guidelines.

## Performance Considerations

### Database Optimization

- Connection pooling configured for concurrent requests
- Indexes on frequently queried columns (ticket_id, chat_id)
- Automatic connection recycling (1 hour)

### Resource Limits

Configured in systemd service:
- File descriptors: 65536
- Private /tmp directory
- Read-only system directories
- Restricted network access

## Roadmap

### Planned Features
- [ ] Multi-language support
- [ ] Automated ticket categorization
- [ ] Customer satisfaction ratings
- [ ] Analytics dashboard
- [ ] SLA tracking and alerts
- [ ] Attachment support

### Under Consideration
- Support for multiple Linear teams
- Integration with other ticketing systems
- Advanced workflow automation
- Customer self-service portal

## FAQ

**Q: Can I use this with multiple Telegram bots?**
A: The current implementation supports one bot instance. For multiple bots, deploy separate instances with different configurations.

**Q: What database backends are supported?**
A: PostgreSQL is the primary supported database. SQLite can be used for development/testing but is not recommended for production.

**Q: How do I migrate from development to production?**
A: Use the automated deployment scripts in `deployment/scripts/`. They handle all migration steps automatically.

**Q: Can I customize the ticket workflow?**
A: Yes, modify the ticket status transitions in `app/database/models.py` and handler logic in `app/telegram/handlers.py`.

**Q: How do I handle high traffic?**
A: Scale horizontally by running multiple instances behind a load balancer, ensuring all instances share the same PostgreSQL database.

## License

Proprietary - All rights reserved

## Support

For issues or questions:
- Create an issue in the GitHub repository
- Contact the development team
- Email: support@muntello.me

## Acknowledgments

Built with:
- [FastAPI](https://fastapi.tiangolo.com/) - Modern web framework
- [python-telegram-bot](https://python-telegram-bot.org/) - Telegram Bot API wrapper
- [SQLAlchemy](https://www.sqlalchemy.org/) - Database ORM
- [Caddy](https://caddyserver.com/) - Web server with automatic HTTPS
- [PostgreSQL](https://www.postgresql.org/) - Database system
