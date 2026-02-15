#!/bin/bash
set -e

echo "🚀 Deploying Muntello Support Bot application..."

# Check if running as deploy user
if [ "$USER" != "deploy" ]; then
    echo "⚠️  Please run as deploy user"
    echo "Switch user: sudo -i -u deploy"
    exit 1
fi

cd /opt/muntello

# Check if git repo exists
if [ ! -d ".git" ]; then
    echo "📦 Cloning repository..."
    git clone git@github.com:Muntello/muntello.me.git .
else
    echo "⬇️  Pulling latest changes..."
    git pull origin main
fi

# Create/activate virtual environment
if [ ! -d "venv" ]; then
    echo "🐍 Creating virtual environment..."
    python3.11 -m venv venv
fi

echo "📚 Installing dependencies..."
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# Check .env file
if [ ! -f "/etc/muntello/.env" ]; then
    echo "⚠️  Environment file not found at /etc/muntello/.env"
    echo "Please create it from .env.example and configure:"
    echo "  cp .env.example /etc/muntello/.env"
    echo "  nano /etc/muntello/.env"
    exit 1
fi

# Create symlink to environment file
echo "🔗 Linking environment file..."
if [ ! -L ".env" ]; then
    ln -s /etc/muntello/.env .env
fi

# Ensure database directory exists
echo "📁 Ensuring database directory exists..."
sudo mkdir -p /var/lib/muntello
sudo chown deploy:deploy /var/lib/muntello

# Initialize database
echo "🗄️  Initializing database..."
python -c "
import asyncio
from app.database import init_db
asyncio.run(init_db())
print('Database initialized')
"

echo "✅ Application deployment completed!"
echo ""
echo "Next steps:"
echo "1. Configure systemd service: deployment/systemd/muntello-bot.service"
echo "2. Configure Caddy: deployment/caddy/Caddyfile"
echo "3. Start service: sudo systemctl start muntello-bot"
