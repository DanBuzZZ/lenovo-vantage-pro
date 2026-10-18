#!/usr/bin/env bash
# ==============================================================================
# Lenovo Vantage Pro — Multi-Distribution Release Asset Builder
# Packages v0.5.1 into:
#   1. .deb (Debian, Ubuntu 22.04/24.04, Linux Mint, Pop!_OS)
#   2. .pkg.tar.zst (Arch Linux, CachyOS, Manjaro, EndeavourOS)
#   3. .tar.gz (Universal Standalone Installer for Fedora, openSUSE, etc.)
# ==============================================================================

set -euo pipefail

VERSION="0.5.1"
PKGNAME="lenovo-vantage-pro"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
DIST_DIR="${REPO_ROOT}/dist"
BUILD_DIR="${REPO_ROOT}/build_pkg"

echo "=== Building Lenovo Vantage Pro v${VERSION} Release Assets ==="

rm -rf "${BUILD_DIR}"
mkdir -p "${BUILD_DIR}" "${DIST_DIR}"

# 1. Compile SUID helper binary with high optimization
echo "[1/4] Compiling lenovo-vantage-helper..."
gcc -O2 -Wall -Wextra "${REPO_ROOT}/helper/helper.c" -o "${BUILD_DIR}/lenovo-vantage-helper"
strip --strip-unneeded "${BUILD_DIR}/lenovo-vantage-helper"

# ------------------------------------------------------------------------------
# 2. Build .deb package (Debian / Ubuntu / Mint / Pop!_OS)
# ------------------------------------------------------------------------------
echo "[2/4] Building Debian/Ubuntu package (.deb)..."
DEB_ROOT="${BUILD_DIR}/deb_root"
mkdir -p "${DEB_ROOT}/DEBIAN"
mkdir -p "${DEB_ROOT}/opt/lenovo-vantage"
mkdir -p "${DEB_ROOT}/usr/bin"
mkdir -p "${DEB_ROOT}/etc/udev/rules.d"
mkdir -p "${DEB_ROOT}/usr/share/applications"
mkdir -p "${DEB_ROOT}/usr/share/icons/hicolor/scalable/apps"

# Copy python source files
cp "${REPO_ROOT}/src/"*.py "${DEB_ROOT}/opt/lenovo-vantage/"
cp "${REPO_ROOT}/helper/helper.c" "${DEB_ROOT}/opt/lenovo-vantage/"
chmod 644 "${DEB_ROOT}/opt/lenovo-vantage/"*

# Copy SUID binary
cp "${BUILD_DIR}/lenovo-vantage-helper" "${DEB_ROOT}/usr/bin/lenovo-vantage-helper"
chmod 4755 "${DEB_ROOT}/usr/bin/lenovo-vantage-helper"

# Copy udev rule
cp "${REPO_ROOT}/udev/99-lenovo-vantage.rules" "${DEB_ROOT}/etc/udev/rules.d/99-lenovo-vantage.rules"
chmod 644 "${DEB_ROOT}/etc/udev/rules.d/99-lenovo-vantage.rules"

# Create launcher script and symlink
cat << 'EOF' > "${DEB_ROOT}/usr/bin/lenovo-vantage"
#!/usr/bin/env bash
exec python3 /opt/lenovo-vantage/app.py "$@"
EOF
chmod 755 "${DEB_ROOT}/usr/bin/lenovo-vantage"
ln -sf lenovo-vantage "${DEB_ROOT}/usr/bin/vantage"

# Copy desktop file and icon
cp "${REPO_ROOT}/vantage.desktop" "${DEB_ROOT}/usr/share/applications/lenovo-vantage.desktop"
chmod 644 "${DEB_ROOT}/usr/share/applications/lenovo-vantage.desktop"
cp "${REPO_ROOT}/assets/vantage.png" "${DEB_ROOT}/usr/share/icons/hicolor/scalable/apps/vantage.png"
chmod 644 "${DEB_ROOT}/usr/share/icons/hicolor/scalable/apps/vantage.png"

# DEBIAN/control
cat << EOF > "${DEB_ROOT}/DEBIAN/control"
Package: ${PKGNAME}
Version: ${VERSION}
Section: utils
Priority: optional
Architecture: amd64
Depends: python3, python3-pyqt6, python3-psutil, python3-evdev, iw, ethtool, iproute2
Recommends: kscreen
Maintainer: DanBuzZZ <adityadanys@gmail.com>
Homepage: https://github.com/DanBuzZZ/lenovo-vantage-pro
Description: Native Linux Hardware Control Center & Esports Suite for Lenovo Gaming Laptops
 Comprehensive open-source hardware control center engineered for modern Lenovo
 gaming laptops (IdeaPad Gaming 3 15IAH7, Legion 5/7, LOQ).
 Features dual turbine MMIO fan curve control, acoustic shockwave heatsink purge,
 165Hz/60Hz Wayland refresh rate locking, ACPI Screen OverDrive (ODV2),
 Intel Alder Lake P-Core thread scheduler, 4-Zone RGB Lighting Studio,
 low-latency Wi-Fi ping stabilizer, blackbox flight telemetry recorder,
 automated 6-point hardware diagnostics, and real-time bilingual EN/ID support.
EOF

# DEBIAN/postinst
cat << 'EOF' > "${DEB_ROOT}/DEBIAN/postinst"
#!/bin/sh
set -e

chown root:root /usr/bin/lenovo-vantage-helper 2>/dev/null || true
chmod 4755 /usr/bin/lenovo-vantage-helper 2>/dev/null || true

if command -v udevadm >/dev/null 2>&1; then
    udevadm control --reload-rules 2>/dev/null || true
    udevadm trigger 2>/dev/null || true
fi

if command -v update-desktop-database >/dev/null 2>&1; then
    update-desktop-database 2>/dev/null || true
fi

if command -v gtk-update-icon-cache >/dev/null 2>&1; then
    gtk-update-icon-cache -q /usr/share/icons/hicolor 2>/dev/null || true
fi

exit 0
EOF
chmod 755 "${DEB_ROOT}/DEBIAN/postinst"

# DEBIAN/prerm
cat << 'EOF' > "${DEB_ROOT}/DEBIAN/prerm"
#!/bin/sh
set -e

pkill -f "python3 /opt/lenovo-vantage/app.py" 2>/dev/null || true
exit 0
EOF
chmod 755 "${DEB_ROOT}/DEBIAN/prerm"

DEB_OUT="${DIST_DIR}/${PKGNAME}_${VERSION}_amd64.deb"
dpkg-deb --build --root-owner-group "${DEB_ROOT}" "${DEB_OUT}"
echo "✓ Generated: ${DEB_OUT}"

# ------------------------------------------------------------------------------
# 3. Build Arch Linux package (.pkg.tar.zst)
# ------------------------------------------------------------------------------
echo "[3/4] Building Arch Linux / CachyOS package (.pkg.tar.zst)..."
ARCH_ROOT="${BUILD_DIR}/arch_root"
mkdir -p "${ARCH_ROOT}/opt/lenovo-vantage"
mkdir -p "${ARCH_ROOT}/usr/bin"
mkdir -p "${ARCH_ROOT}/etc/udev/rules.d"
mkdir -p "${ARCH_ROOT}/usr/share/applications"
mkdir -p "${ARCH_ROOT}/usr/share/icons/hicolor/scalable/apps"

cp "${REPO_ROOT}/src/"*.py "${ARCH_ROOT}/opt/lenovo-vantage/"
cp "${REPO_ROOT}/helper/helper.c" "${ARCH_ROOT}/opt/lenovo-vantage/"
cp "${BUILD_DIR}/lenovo-vantage-helper" "${ARCH_ROOT}/usr/bin/lenovo-vantage-helper"
chmod 4755 "${ARCH_ROOT}/usr/bin/lenovo-vantage-helper"
cp "${REPO_ROOT}/udev/99-lenovo-vantage.rules" "${ARCH_ROOT}/etc/udev/rules.d/99-lenovo-vantage.rules"

cat << 'EOF' > "${ARCH_ROOT}/usr/bin/lenovo-vantage"
#!/usr/bin/env bash
exec python3 /opt/lenovo-vantage/app.py "$@"
EOF
chmod 755 "${ARCH_ROOT}/usr/bin/lenovo-vantage"
ln -sf lenovo-vantage "${ARCH_ROOT}/usr/bin/vantage"

cp "${REPO_ROOT}/vantage.desktop" "${ARCH_ROOT}/usr/share/applications/lenovo-vantage.desktop"
cp "${REPO_ROOT}/assets/vantage.png" "${ARCH_ROOT}/usr/share/icons/hicolor/scalable/apps/vantage.png"

# Calculate total installed size in bytes
INST_SIZE=$(du -sb "${ARCH_ROOT}" | cut -f1)

# .PKGINFO
cat << EOF > "${ARCH_ROOT}/.PKGINFO"
format = 2
pkgname = ${PKGNAME}
pkgbase = ${PKGNAME}
pkgver = ${VERSION}-1
pkgdesc = Native Linux Hardware Control Center & Esports Suite for Lenovo Gaming Laptops
url = https://github.com/DanBuzZZ/lenovo-vantage-pro
builddate = $(date +%s)
packager = DanBuzZZ <adityadanys@gmail.com>
size = ${INST_SIZE}
arch = x86_64
license = GPL3
depend = python
depend = python-pyqt6
depend = python-psutil
depend = python-evdev
depend = iw
depend = ethtool
depend = iproute2
optdepend = nvidia-utils: RTX 3050/4060 VRAM and power telemetry
optdepend = acpi_call: direct ACPI VPC2004/SSFM communication fallback
optdepend = kscreen: KWin Wayland display refresh rate control
provides = lenovo-vantage
provides = vantage
conflict = vantage
conflict = lenovo-vantage
EOF

ARCH_OUT="${DIST_DIR}/${PKGNAME}-${VERSION}-1-x86_64.pkg.tar.zst"
(
    cd "${ARCH_ROOT}"
    # Package files into a standard Arch zst archive with root ownership
    tar --sort=name --owner=root:0 --group=root:0 --numeric-owner \
        -cf - .PKGINFO etc opt usr | zstd -c -T0 -19 > "${ARCH_OUT}"
)
echo "✓ Generated: ${ARCH_OUT}"

# ------------------------------------------------------------------------------
# 4. Build Universal Standalone Installer Tarball (.tar.gz)
# ------------------------------------------------------------------------------
echo "[4/4] Building Universal Standalone Tarball (.tar.gz)..."
TGZ_NAME="${PKGNAME}-${VERSION}-linux-x86_64"
TGZ_DIR="${BUILD_DIR}/${TGZ_NAME}"
mkdir -p "${TGZ_DIR}"

cp -r "${REPO_ROOT}/src" "${TGZ_DIR}/"
cp -r "${REPO_ROOT}/helper" "${TGZ_DIR}/"
cp -r "${REPO_ROOT}/udev" "${TGZ_DIR}/"
cp -r "${REPO_ROOT}/assets" "${TGZ_DIR}/"
cp "${REPO_ROOT}/install.sh" "${TGZ_DIR}/"
cp "${REPO_ROOT}/uninstall.sh" "${TGZ_DIR}/"
cp "${REPO_ROOT}/vantage.desktop" "${TGZ_DIR}/"
cp "${REPO_ROOT}/vantage.sh" "${TGZ_DIR}/"
cp "${REPO_ROOT}/Makefile" "${TGZ_DIR}/"
cp "${REPO_ROOT}/PKGBUILD" "${TGZ_DIR}/"
cp "${REPO_ROOT}/README.md" "${TGZ_DIR}/"
cp "${REPO_ROOT}/LICENSE" "${TGZ_DIR}/"

# Also include precompiled helper binary
mkdir -p "${TGZ_DIR}/bin"
cp "${BUILD_DIR}/lenovo-vantage-helper" "${TGZ_DIR}/bin/"

TGZ_OUT="${DIST_DIR}/${TGZ_NAME}.tar.gz"
(
    cd "${BUILD_DIR}"
    tar --sort=name --owner=root:0 --group=root:0 --numeric-owner \
        -czf "${TGZ_OUT}" "${TGZ_NAME}"
)
echo "✓ Generated: ${TGZ_OUT}"

# ------------------------------------------------------------------------------
# 5. Generate Checksums (SHA256SUMS.txt)
# ------------------------------------------------------------------------------
(
    cd "${DIST_DIR}"
    sha256sum "$(basename "${DEB_OUT}")" "$(basename "${ARCH_OUT}")" "$(basename "${TGZ_OUT}")" > SHA256SUMS.txt
)
echo "✓ Generated: ${DIST_DIR}/SHA256SUMS.txt"

# Clean up build artifacts
rm -rf "${BUILD_DIR}"

echo ""
echo "=== All Release Assets Successfully Built in: ${DIST_DIR} ==="
ls -lh "${DIST_DIR}"
