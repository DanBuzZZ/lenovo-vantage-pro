#!/usr/bin/env bash
# ==============================================================================
# Lenovo Vantage Pro — Uninstaller Script
# ==============================================================================

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m'

if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}[ERROR] Please run this script with sudo or as root.${NC}"
    exit 1
fi

echo "Removing Lenovo Vantage Pro..."

# Stop any running instances
pkill -f "python3 /opt/lenovo-vantage/app.py" 2>/dev/null || true

# Remove binaries and scripts
rm -f /usr/bin/lenovo-vantage
rm -f /usr/bin/vantage
rm -f /usr/bin/lenovo-vantage-helper

# Remove application directory
rm -rf /opt/lenovo-vantage

# Remove udev rules
rm -f /etc/udev/rules.d/99-lenovo-vantage.rules
udevadm control --reload-rules 2>/dev/null || true
udevadm trigger 2>/dev/null || true

# Remove desktop entry and icon
rm -f /usr/share/applications/lenovo-vantage.desktop
rm -f /usr/share/icons/hicolor/scalable/apps/vantage.png

echo -e "${GREEN}Lenovo Vantage Pro has been uninstalled successfully.${NC}"
