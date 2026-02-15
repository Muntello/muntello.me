#!/bin/bash
set -e

echo "🔧 Setting up Ubuntu 22.04 server for Muntello Support Bot..."

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "Please run as root or with sudo"
    exit 1
fi

# Update system
echo "📦 Updating system packages..."
apt update && apt upgrade -y

# Install Python 3.11
echo "🐍 Installing Python 3.11..."
apt install -y python3.11 python3.11-venv python3-pip software-properties-common

# Install Caddy
echo "🌐 Installing Caddy..."
apt install -y debian-keyring debian-archive-keyring apt-transport-https curl
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' | gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' | tee /etc/apt/sources.list.d/caddy-stable.list
apt update && apt install -y caddy

# Create deploy user
echo "👤 Creating deploy user..."
if ! id "deploy" &>/dev/null; then
    useradd -m -s /bin/bash deploy
    usermod -aG sudo deploy
    echo "User 'deploy' created"
else
    echo "User 'deploy' already exists"
fi

# SSH hardening
echo "🔒 Configuring SSH security..."
sed -i 's/#PermitRootLogin yes/PermitRootLogin no/' /etc/ssh/sshd_config
sed -i 's/#PasswordAuthentication yes/PasswordAuthentication no/' /etc/ssh/sshd_config
sed -i 's/PasswordAuthentication yes/PasswordAuthentication no/' /etc/ssh/sshd_config
systemctl restart sshd
echo "SSH hardened: root login disabled, password auth disabled"

# Setup firewall
echo "🛡️ Configuring firewall..."
ufw --force reset
ufw default deny incoming
ufw default allow outgoing
ufw allow 22/tcp comment 'SSH'
ufw allow 80/tcp comment 'HTTP'
ufw allow 443/tcp comment 'HTTPS'
ufw --force enable
echo "Firewall configured"

# Install fail2ban
echo "🚨 Installing fail2ban..."
apt install -y fail2ban
systemctl enable fail2ban
systemctl start fail2ban

# Setup automatic security updates
echo "🔄 Enabling automatic security updates..."
apt install -y unattended-upgrades
dpkg-reconfigure -plow unattended-upgrades

# Create application directories
echo "📁 Creating application directories..."
mkdir -p /opt/muntello
mkdir -p /var/lib/muntello
mkdir -p /var/log/muntello
mkdir -p /etc/muntello

chown -R deploy:deploy /opt/muntello
chown -R deploy:deploy /var/lib/muntello
chown -R deploy:deploy /var/log/muntello
chown -R deploy:deploy /etc/muntello

echo "✅ Server setup completed!"
echo ""
echo "Next steps:"
echo "1. Add SSH key for deploy user: /home/deploy/.ssh/authorized_keys"
echo "2. Run as deploy user: deployment/scripts/deploy-app.sh"
echo "3. Configure environment: /etc/muntello/.env"
