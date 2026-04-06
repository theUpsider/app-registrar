#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INSTALL_DIR="$HOME/.local/share/nautilus-app-registrar"
EXTENSIONS_DIR="$HOME/.local/share/nautilus-python/extensions"
APPLICATIONS_DIR="$HOME/.local/share/applications"
APP_DESKTOP="$APPLICATIONS_DIR/io.github.theUpsider.AppRegistrar.desktop"

echo "=== App Registrar Installer ==="
echo ""

MISSING=()
for pkg in python3-nautilus python3-gi gir1.2-adw-1; do
    if ! dpkg -s "$pkg" >/dev/null 2>&1; then
        MISSING+=("$pkg")
    fi
done

if [ ${#MISSING[@]} -gt 0 ]; then
    echo "Missing system packages: ${MISSING[*]}"
    echo "Install them with:"
    echo "  sudo apt install ${MISSING[*]}"
    echo ""
    read -rp "Attempt to install now? [y/N] " response
    if [[ "$response" =~ ^[Yy]$ ]]; then
        sudo apt install -y "${MISSING[@]}"
    else
        echo "Cannot continue without dependencies. Exiting."
        exit 1
    fi
fi

echo "Installing app module to $INSTALL_DIR ..."
mkdir -p "$INSTALL_DIR"
cp -r "$SCRIPT_DIR/app_registrar" "$INSTALL_DIR/"

echo "Installing Nautilus extension to $EXTENSIONS_DIR ..."
mkdir -p "$EXTENSIONS_DIR"
cp "$SCRIPT_DIR/nautilus_extension.py" "$EXTENSIONS_DIR/nautilus_app_registrar.py"

echo "Creating desktop entry ..."
mkdir -p "$APPLICATIONS_DIR"
cat > "$APP_DESKTOP" <<EOF
[Desktop Entry]
Type=Application
Version=1.0
Name=App Registrar
Comment=Register executables as desktop applications
Exec=env PYTHONPATH=$INSTALL_DIR /usr/bin/python3 -m app_registrar
Icon=application-x-executable
Categories=Utility;
Keywords=app;registrar;register;desktop;launcher;executable;
Terminal=false
StartupNotify=true
X-RegisteredBy=nautilus-app-registrar
EOF

update-desktop-database "$APPLICATIONS_DIR" 2>/dev/null || true

echo "Restarting Nautilus ..."
nautilus -q 2>/dev/null || true
sleep 1
# Restart Nautilus with clean environment so python-nautilus extensions
# load correctly (avoids interference from conda/virtualenv/etc.)
env -i HOME="$HOME" DISPLAY="${DISPLAY:-}" \
    XAUTHORITY="${XAUTHORITY:-}" \
    XDG_RUNTIME_DIR="${XDG_RUNTIME_DIR:-}" \
    DBUS_SESSION_BUS_ADDRESS="${DBUS_SESSION_BUS_ADDRESS:-}" \
    WAYLAND_DISPLAY="${WAYLAND_DISPLAY:-}" \
    PATH="/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin" \
    nohup nautilus --gapplication-service >/dev/null 2>&1 &
disown

echo ""
echo "=== Installation complete ==="
echo "  • App module:  $INSTALL_DIR/app_registrar/"
echo "  • Extension:   $EXTENSIONS_DIR/nautilus_app_registrar.py"
echo "  • Launcher:    $APP_DESKTOP"
echo ""
echo "Right-click any executable in Nautilus to 'Register as App',"
echo "or launch 'App Registrar' from your application menu."
