"""Utility functions for the App Registrar."""

import os
import re
import subprocess
from gettext import gettext as _

from .constants import APPLICATIONS_DIR


def sanitize_filename(name: str) -> str:
    """Convert a display name to a valid .desktop filename component.

    Lowercase, spaces to hyphens, strip special chars.
    Result contains only [a-z0-9-_].
    """
    name = name.lower().strip()
    name = name.replace(' ', '-')
    name = re.sub(r'[^a-z0-9\-_]', '', name)
    name = re.sub(r'-+', '-', name)
    name = name.strip('-')
    return name or 'unnamed'


def validate_exec_path(path: str) -> tuple:
    """Check that a path exists and is executable.

    Returns (valid: bool, error_message: str).
    """
    if not path:
        return False, _('Executable path is empty')
    path = os.path.expanduser(path)
    if not os.path.exists(path):
        return False, _('File does not exist: {}').format(path)
    if not os.path.isfile(path):
        return False, _('Path is not a file: {}').format(path)
    if not os.access(path, os.X_OK):
        return False, _('File is not executable: {}').format(path)
    return True, ''


def update_desktop_database():
    """Run update-desktop-database synchronously."""
    try:
        subprocess.run(
            ['update-desktop-database', APPLICATIONS_DIR],
            check=True,
            capture_output=True,
        )
    except FileNotFoundError:
        pass  # update-desktop-database not installed
    except subprocess.CalledProcessError:
        pass  # Non-critical failure


def update_desktop_database_async():
    """Run update-desktop-database in the background (non-blocking)."""
    try:
        subprocess.Popen(
            ['update-desktop-database', APPLICATIONS_DIR],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except FileNotFoundError:
        pass
