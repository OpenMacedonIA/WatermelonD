#!/bin/bash

# secure_system.sh
# Hardens the system security for Neo Core.
# Usage: sudo ./secure_system.sh

if [ "$EUID" -ne 0 ]; then
  echo "Please run as root (sudo)."
  exit 1
fi

echo "========================================="
echo "===   Neo Core Security Hardening    ==="
echo "========================================="

# 1. Detect Package Manager
PKG_MANAGER=""
if command -v apt-get &> /dev/null; then
    PKG_MANAGER="apt"
elif command -v dnf &> /dev/null; then
    PKG_MANAGER="dnf"
fi

if [ -z "$PKG_MANAGER" ]; then
    echo "Error: Unsupported package manager."
    exit 1
fi

# 2. Install Security Tools
echo "[1/4] Installing Security Tools (UFW, Fail2Ban)..."
if [ "$PKG_MANAGER" == "apt" ]; then
    apt-get update
    apt-get install -y ufw fail2ban
elif [ "$PKG_MANAGER" == "dnf" ]; then
    dnf install -y ufw fail2ban
fi

# 3. Configure Firewall (UFW)
echo "[2/4] Configuring Firewall (UFW)..."
ufw default deny incoming
ufw default allow outgoing

# Allow SSH (Port 22)
ufw allow 22/tcp
echo "  -> Allowed SSH (Port 22)"

# Allow Neo Web Admin (Port 5000)
ufw allow 5000/tcp
echo "  -> Allowed Neo Web Admin (Port 5000)"

# Check if user wants to enable now
read -p "Do you want to enable UFW now? This may disconnect you if not careful. (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "y" | ufw enable
    echo "  -> UFW Enabled."
else
    echo "  -> UFW configured but NOT enabled. Run 'sudo ufw enable' manually."
fi

# 4. Configure Fail2Ban
echo "[3/4] Configuring Fail2Ban..."
# Create local config to avoid overriding updates
cat <<EOT > /etc/fail2ban/jail.local
[sshd]
enabled = true
port = ssh
filter = sshd
logpath = /var/log/auth.log
maxretry = 3
bantime = 3600
findtime = 600
EOT

# Restart Fail2Ban
systemctl restart fail2ban
systemctl enable fail2ban
echo "  -> Fail2Ban active and protecting SSH."

# 5. Lock Down File Permissions
echo "[4/4] Locking Down File Permissions..."
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
PROJECT_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"

if [ -d "$PROJECT_ROOT/config" ]; then
    echo "  -> Setting 600 permissions on $PROJECT_ROOT/config/*.json"
    chmod 600 "$PROJECT_ROOT/config/"*.json 2>/dev/null
    # Ensure direcotry is accessible to owner
    chmod 700 "$PROJECT_ROOT/config"
fi

if [ -d "$PROJECT_ROOT/database" ]; then
    echo "  -> Setting 600 permissions on $PROJECT_ROOT/database/*.db"
    chmod 600 "$PROJECT_ROOT/database/"*.db 2>/dev/null
    chmod 700 "$PROJECT_ROOT/database"
fi

echo ""
echo "Security Hardening Complete!"
echo "Check status with: sudo ufw status verbose"
echo "Check bans with: sudo fail2ban-client status sshd"
