# Systemd Service Installation

## Installation Steps

1. **Copy service file to systemd directory:**
   ```bash
   sudo cp deployment/systemd/muntello-bot.service /etc/systemd/system/
   ```

2. **Reload systemd daemon:**
   ```bash
   sudo systemctl daemon-reload
   ```

3. **Enable service (start on boot):**
   ```bash
   sudo systemctl enable muntello-bot
   ```

4. **Start service:**
   ```bash
   sudo systemctl start muntello-bot
   ```

5. **Check status:**
   ```bash
   sudo systemctl status muntello-bot
   ```

## Useful Commands

- **View logs:** `sudo journalctl -u muntello-bot -f`
- **Restart service:** `sudo systemctl restart muntello-bot`
- **Stop service:** `sudo systemctl stop muntello-bot`
- **Disable service:** `sudo systemctl disable muntello-bot`
