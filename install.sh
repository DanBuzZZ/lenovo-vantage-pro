#!/usr/bin/env bash
# ==============================================================================
# Lenovo Vantage Pro — Hardware Control Center for Linux
# Enterprise Installation Script (v0.5.0)
# ==============================================================================

set -e

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}==================================================================${NC}"
echo -e "${BLUE}   Lenovo Vantage Pro — Hardware Control Center Installer (v0.5.0)${NC}"
echo -e "${BLUE}==================================================================${NC}"

# Check for root/sudo
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}[ERROR] Please run this installer with sudo or as root.${NC}"
    echo -e "Usage: sudo ./install.sh"
    exit 1
fi

REAL_USER="${SUDO_USER:-$USER}"
REAL_HOME=$(getent passwd "$REAL_USER" | cut -d: -f6)

echo -e "${GREEN}[1/6] Detecting Linux Distribution and Installing Dependencies...${NC}"

if [ -f /etc/os-release ]; then
    . /etc/os-release
    DISTRO_ID="${ID:-unknown}"
    DISTRO_LIKE="${ID_LIKE:-$DISTRO_ID}"
fi

case "$DISTRO_LIKE" in
    *arch*|*cachyos*|*manjaro*|*endeavouros*)
        echo -e "Detected Arch Linux / CachyOS ecosystem."
        pacman -Sy --needed --noconfirm python-pyqt6 python-psutil python-evdev iw gcc make ethtool iproute2
        ;;
    *debian*|*ubuntu*|*pop*|*mint*)
        echo -e "Detected Debian / Ubuntu ecosystem."
        apt-get update
        apt-get install -y python3-pyqt6 python3-psutil python3-evdev iw gcc make ethtool iproute2 libevdev2
        ;;
    *fedora*|*rhel*)
        echo -e "Detected Fedora / RHEL ecosystem."
        dnf install -y python3-qt6 python3-psutil python3-evdev iw gcc make ethtool iproute
        ;;
    *suse*)
        echo -e "Detected openSUSE ecosystem."
        zypper install -y python3-qt6 python3-psutil python3-evdev iw gcc make ethtool iproute2
        ;;
    *)
        echo -e "${YELLOW}[WARNING] Unrecognized distro family ($DISTRO_LIKE). Please ensure PyQt6, psutil, evdev, gcc, and iw are installed.${NC}"
        ;;
esac

echo -e "${GREEN}[2/6] Compiling SUID Hardware Control Helper...${NC}"
mkdir -p /opt/lenovo-vantage
gcc -O2 -Wall -Wextra helper/helper.c -o /usr/bin/lenovo-vantage-helper
chown root:root /usr/bin/lenovo-vantage-helper
chmod 4755 /usr/bin/lenovo-vantage-helper
echo -e "Compiled /usr/bin/lenovo-vantage-helper (SUID 4755 root:root)."

echo -e "${GREEN}[3/6] Installing Udev Rules for Non-Root HID & Hotkeys...${NC}"
mkdir -p /etc/udev/rules.d
cp -f udev/99-lenovo-vantage.rules /etc/udev/rules.d/99-lenovo-vantage.rules
udevadm control --reload-rules 2>/dev/null || true
udevadm trigger 2>/dev/null || true
echo -e "Installed /etc/udev/rules.d/99-lenovo-vantage.rules."

echo -e "${GREEN}[4/6] Installing Application Files to /opt/lenovo-vantage/...${NC}"
cp -f src/*.py /opt/lenovo-vantage/
cp -f helper/helper.c /opt/lenovo-vantage/
chown -R "$REAL_USER:$REAL_USER" /opt/lenovo-vantage/ 2>/dev/null || true
chmod -R 755 /opt/lenovo-vantage/

echo -e "${GREEN}[5/6] Installing Application Icons and Desktop Launcher...${NC}"
mkdir -p /usr/share/icons/hicolor/scalable/apps
mkdir -p /usr/share/applications
mkdir -p /usr/bin

if [ -f assets/icon.png ]; then
    cp -f assets/icon.png /usr/share/icons/hicolor/scalable/apps/vantage.png
elif [ -f assets/vantage.png ]; then
    cp -f assets/vantage.png /usr/share/icons/hicolor/scalable/apps/vantage.png
fi

cat << "EOF" > /usr/share/applications/lenovo-vantage.desktop
[Desktop Entry]
Name=Lenovo Vantage Pro
Comment=Hardware Control Center for Lenovo Gaming Laptops
Exec=python3 /opt/lenovo-vantage/app.py
Icon=vantage
Terminal=false
Type=Application
Categories=Settings;HardwareSettings;System;
StartupNotify=true
StartupWMClass=lenovo-vantage-pro
EOF

cat << "EOF" > /usr/bin/lenovo-vantage
#!/usr/bin/env bash
exec python3 /opt/lenovo-vantage/app.py "$@"
EOF

chmod +x /usr/bin/lenovo-vantage
ln -sf /usr/bin/lenovo-vantage /usr/bin/vantage

# Initialize permissions on hardware files
/usr/bin/lenovo-vantage-helper fix-perms 2>/dev/null || true

echo -e "${GREEN}[6/6] Installation Complete!${NC}"
echo -e "${BLUE}==================================================================${NC}"
echo -e "${GREEN}Lenovo Vantage Pro has been successfully installed!${NC}"
echo -e "You can launch it from your application launcher or by running:"
echo -e "  ${YELLOW}lenovo-vantage${NC}"
echo -e "${BLUE}==================================================================${NC}"
