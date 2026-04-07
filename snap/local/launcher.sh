#!/bin/sh
# Install or update the Nautilus extension when the app is launched.
EXT_DIR="${SNAP_REAL_HOME:-$HOME}/.local/share/nautilus-python/extensions"
EXT_SRC="$SNAP/lib/app-registrar/nautilus_extension.py"
EXT_DST="$EXT_DIR/nautilus_app_registrar.py"

mkdir -p "$EXT_DIR"

# Write an adapted copy of the extension that points at the snap's app module.
SNAP_APP_DIR="$SNAP/lib/app-registrar"
SNAP_PYTHON="$SNAP/usr/bin/python3"
# Fall back to system python3 if snap doesn't bundle its own
if [ ! -x "$SNAP_PYTHON" ]; then
    SNAP_PYTHON="/usr/bin/python3"
fi

# Only update if the source or the snap path has changed.
CURRENT_MARKER=""
if [ -f "$EXT_DST" ]; then
    CURRENT_MARKER=$(grep "^# SNAP_INSTALL_DIR=" "$EXT_DST" 2>/dev/null || true)
fi
DESIRED_MARKER="# SNAP_INSTALL_DIR=$SNAP_APP_DIR"

if [ "$CURRENT_MARKER" != "$DESIRED_MARKER" ]; then
    # Patch INSTALL_DIR and the python executable to point into the snap.
    sed \
        -e "s|INSTALL_DIR = .*|INSTALL_DIR = '$SNAP_APP_DIR'  $DESIRED_MARKER|" \
        -e "s|'/usr/bin/python3'|'$SNAP_PYTHON'|" \
        "$EXT_SRC" > "$EXT_DST"
    chmod +x "$EXT_DST"
    # Ask Nautilus to reload extensions.
    nautilus -q 2>/dev/null || true
fi

export PYTHONPATH="$SNAP/lib/app-registrar${PYTHONPATH:+:$PYTHONPATH}"
exec python3 -m app_registrar "$@"
