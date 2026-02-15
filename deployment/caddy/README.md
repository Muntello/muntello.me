# Caddy Web Server Configuration

This directory contains the Caddy configuration for the Muntello Support Bot.

## Prerequisites

1. **DNS Configuration**: Point `support.muntello.me` to your server's IP address
   - Add an A record: `support.muntello.me` → `YOUR_SERVER_IP`
   - Wait for DNS propagation (can take up to 24-48 hours)
   - Verify with: `dig support.muntello.me` or `nslookup support.muntello.me`

2. **Firewall Configuration**: Ensure ports 80 and 443 are open
   ```bash
   # For ufw (Ubuntu/Debian)
   sudo ufw allow 80/tcp
   sudo ufw allow 443/tcp

   # For firewalld (CentOS/RHEL)
   sudo firewall-cmd --permanent --add-service=http
   sudo firewall-cmd --permanent --add-service=https
   sudo firewall-cmd --reload
   ```

## Installation

### 1. Install Caddy

**Ubuntu/Debian:**
```bash
sudo apt install -y debian-keyring debian-archive-keyring apt-transport-https
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' | sudo gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' | sudo tee /etc/apt/sources.list.d/caddy-stable.list
sudo apt update
sudo apt install caddy
```

**CentOS/RHEL:**
```bash
sudo dnf install -y dnf-plugins-core
sudo dnf copr enable @caddy/caddy
sudo dnf install caddy
```

### 2. Deploy Configuration

```bash
# Copy Caddyfile to Caddy config directory
sudo cp deployment/caddy/Caddyfile /etc/caddy/Caddyfile

# Create log directory
sudo mkdir -p /var/log/caddy
sudo chown caddy:caddy /var/log/caddy

# Validate configuration
caddy validate --config /etc/caddy/Caddyfile

# Reload Caddy
sudo systemctl reload caddy
```

### 3. Enable and Start Caddy

```bash
# Enable Caddy to start on boot
sudo systemctl enable caddy

# Start Caddy
sudo systemctl start caddy

# Check status
sudo systemctl status caddy
```

## Configuration Details

### Automatic HTTPS

Caddy automatically obtains and renews SSL/TLS certificates from Let's Encrypt for `support.muntello.me`. No manual certificate management required.

### Health Checks

Caddy performs health checks on the FastAPI backend every 10 seconds:
- Health endpoint: `/health`
- Interval: 10 seconds
- Timeout: 5 seconds
- Expected status: 2xx

### Security Headers

The configuration includes security headers:
- `X-Content-Type-Options: nosniff` - Prevents MIME type sniffing
- `X-Frame-Options: DENY` - Prevents clickjacking
- `X-XSS-Protection: 1; mode=block` - XSS protection
- Server header removed - Reduces information disclosure

### Logging

Logs are stored in `/var/log/caddy/support.log` with:
- JSON format for structured logging
- 10MB rolling size
- 5 log files kept
- 720 hours (30 days) retention

### Optional Features

**HSTS (HTTP Strict Transport Security):**
Uncomment the HSTS header in the Caddyfile for production:
```caddy
Strict-Transport-Security "max-age=31536000; includeSubDomains; preload"
```

**Rate Limiting:**
Uncomment the rate limiting block to limit requests:
- 100 requests per minute per IP address
- Adjust values as needed for your use case

## Verification

### 1. Check DNS Resolution
```bash
dig support.muntello.me
# Should show your server's IP address
```

### 2. Test HTTP/HTTPS Access
```bash
# Test HTTP (should redirect to HTTPS)
curl -I http://support.muntello.me

# Test HTTPS
curl -I https://support.muntello.me

# Test health endpoint
curl https://support.muntello.me/health
```

### 3. Verify SSL Certificate
```bash
# Check certificate details
echo | openssl s_client -connect support.muntello.me:443 -servername support.muntello.me 2>/dev/null | openssl x509 -noout -text
```

### 4. Monitor Logs
```bash
# Watch Caddy logs
sudo journalctl -u caddy -f

# Watch application logs
sudo tail -f /var/log/caddy/support.log
```

## Troubleshooting

### Certificate Issues

**Problem**: Certificate not issued
```bash
# Check Caddy logs
sudo journalctl -u caddy -n 100

# Common issues:
# - DNS not pointing to server
# - Ports 80/443 blocked by firewall
# - Another service using port 80/443
```

**Solution**: Verify DNS, firewall, and port availability

### Connection Issues

**Problem**: Cannot connect to application
```bash
# Check if FastAPI is running
systemctl status muntello-bot

# Check if listening on port 8000
ss -tlnp | grep 8000

# Check Caddy reverse proxy
curl http://localhost:8000/health
```

### Log Rotation Not Working

**Problem**: Logs not rotating
```bash
# Check log directory permissions
ls -la /var/log/caddy

# Ensure caddy user owns the directory
sudo chown -R caddy:caddy /var/log/caddy
```

## Configuration Updates

After modifying the Caddyfile:

```bash
# Validate configuration
caddy validate --config /etc/caddy/Caddyfile

# Reload Caddy (zero-downtime)
sudo systemctl reload caddy

# Or restart if needed
sudo systemctl restart caddy
```

## Security Considerations

1. **Automatic HTTPS**: Caddy automatically handles SSL/TLS certificates
2. **Security Headers**: Pre-configured headers protect against common attacks
3. **Rate Limiting**: Optional rate limiting available (uncomment in Caddyfile)
4. **Logging**: JSON logs for security monitoring and analysis
5. **Backend Isolation**: FastAPI only listens on localhost (127.0.0.1)

## Additional Resources

- [Caddy Documentation](https://caddyserver.com/docs/)
- [Reverse Proxy Guide](https://caddyserver.com/docs/caddyfile/directives/reverse_proxy)
- [Automatic HTTPS](https://caddyserver.com/docs/automatic-https)
