#!/usr/bin/env bash
set -euo pipefail

INSTALL_DIR="$HOME/.local/share/nautilus-app-registrar"
EXTENSIONS_DIR="$HOME/.local/share/nautilus-python/extensions"
APPLICATIONS_DIR="$HOME/.local/share/applications"
CONFIG_DIR="$HOME/.config/nautilus-app-registrar"
APP_DESKTOP="$APPLICATIONS_DIR/io.github.theUpsider.AppRegistrar.desktop"

echo "=== App Registrar Uninstaller ==="
echo ""

EXTENSION_FILE="$EXTENSIONS_DIR/nautilus_app_registrar.py"
if [ -f "$EXTENSION_FILE" ]; then
    echo "Removing Nautilus extension ..."
    rm -f "$EXTENSION_FILE"
else
    echo "Extension not found, skipping."
fi

if [ -d "$INSTALL_DIR" ]; then
    echo "Removing app module from $INSTALL_DIR ..."
    rm -rf "$INSTALL_DIR"
else
    echo "App module not found, skipping."
fi

if [ -f "$APP_DESKTOP" ]; then
    echo "Removing desktop entry ..."
    rm -f "$APP_DESKTOP"
fi

echo ""
read -rp "Also remove all apps registered by App Registrar? [y/N] " response
if [[ "$response" =~ ^[Yy]$ ]]; then
    echo "Scanning for managed desktop entries ..."
    count=0
    for desktop_file in "$APPLICATIONS_DIR"/*.desktop; do
        [ -f "$desktop_file" ] || continue
        if grep -q "^X-RegisteredBy=nautilus-app-registrar$" "$desktop_file" 2>/dev/null; then
            name=$(grep "^Name=" "$desktop_file" | head -1 | cut -d= -f2)
            echo "  Removing: $name ($desktop_file)"
            rm -f "$desktop_file"
            count=$((count + 1))
        fi
    done
    echo "  Removed $count registered app(s)."
fi

if [ -d "$CONFIG_DIR" ]; then
    echo ""
    read -rp "Remove configuration ($CONFIG_DIR)? [y/N] " response
    if [[ "$response" =~ ^[Yy]$ ]]; then
        rm -rf "$CONFIG_DIR"
        echo "Configuration removed."
    else
        echo "Configuration preserved."
    fi
fi

update-desktop-database "$APPLICATIONS_DIR" 2>/dev/null || true

echo ""
echo "Restarting Nautilus ..."
nautilus -q 2>/dev/null || true

echo ""
echo "=== Uninstallation complete ==="
