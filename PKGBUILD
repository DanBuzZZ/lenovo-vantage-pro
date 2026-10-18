# Maintainer: DanBuzZZ <adityadanys@gmail.com>
pkgname=lenovo-vantage-pro
pkgver=0.5.0
pkgrel=1
pkgdesc="Native Linux Hardware Control Center & Esports Suite for Lenovo Gaming Laptops (IdeaPad Gaming 3 & Legion)"
arch=('x86_64')
url="https://github.com/DanBuzZZ/lenovo-vantage-pro"
license=('GPL3')
depends=(
    'python'
    'python-pyqt6'
    'python-psutil'
    'python-evdev'
    'iw'
    'ethtool'
    'iproute2'
)
makedepends=('gcc' 'make')
optdepends=(
    'nvidia-utils: RTX 3050/4060 VRAM and power telemetry'
    'acpi_call: direct ACPI VPC2004/SSFM communication fallback'
    'kscreen: KWin Wayland display refresh rate control'
)
provides=('lenovo-vantage' 'vantage')
conflicts=('vantage' 'lenovo-vantage')
source=("${pkgname}-${pkgver}.tar.gz::https://github.com/DanBuzZZ/lenovo-vantage-pro/archive/v${pkgver}.tar.gz")
sha256sums=('SKIP')

build() {
    cd "${srcdir}/${pkgname}-${pkgver}" 2>/dev/null || cd "${startdir}"
    gcc -O2 -Wall -Wextra helper/helper.c -o lenovo-vantage-helper
}

package() {
    cd "${srcdir}/${pkgname}-${pkgver}" 2>/dev/null || cd "${startdir}"

    install -dm755 "${pkgdir}/opt/lenovo-vantage"
    install -Dm755 src/*.py "${pkgdir}/opt/lenovo-vantage/"
    install -Dm644 helper/helper.c "${pkgdir}/opt/lenovo-vantage/"

    # SUID helper
    install -Dm4755 lenovo-vantage-helper "${pkgdir}/usr/bin/lenovo-vantage-helper"

    # Udev rules
    install -Dm644 udev/99-lenovo-vantage.rules "${pkgdir}/etc/udev/rules.d/99-lenovo-vantage.rules"

    # Launcher scripts
    install -dm755 "${pkgdir}/usr/bin"
    cat << "EOF" > "${pkgdir}/usr/bin/lenovo-vantage"
#!/usr/bin/env bash
exec python3 /opt/lenovo-vantage/app.py "$@"
EOF
    chmod 755 "${pkgdir}/usr/bin/lenovo-vantage"
    ln -sf /usr/bin/lenovo-vantage "${pkgdir}/usr/bin/vantage"

    # Desktop entry & icon
    install -Dm644 assets/vantage.png "${pkgdir}/usr/share/icons/hicolor/scalable/apps/vantage.png"
    cat << "EOF" > "${pkgdir}/usr/share/applications/lenovo-vantage.desktop"
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
}
