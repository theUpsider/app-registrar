"""Constants and default values for the App Registrar."""

import os

APP_ID = 'io.github.appregistrar.AppRegistrar'
APP_NAME = 'App Registrar'
APP_VERSION = '1.0.0'

# Runtime paths (all user-space, no root required)
APPLICATIONS_DIR = os.path.expanduser('~/.local/share/applications')
EXTENSIONS_DIR = os.path.expanduser('~/.local/share/nautilus-python/extensions')
CONFIG_DIR = os.path.expanduser('~/.config/nautilus-app-registrar')
SETTINGS_FILE = os.path.join(CONFIG_DIR, 'settings.json')
INSTALL_DIR = os.path.expanduser('~/.local/share/nautilus-app-registrar')

# Desktop entry metadata keys
REGISTERED_BY_KEY = 'X-RegisteredBy'
REGISTERED_BY_VALUE = 'nautilus-app-registrar'
REGISTRATION_DATE_KEY = 'X-RegistrationDate'

# Freedesktop main categories
# https://specifications.freedesktop.org/menu-spec/latest/apa.html
CATEGORIES = [
    'AudioVideo',
    'Audio',
    'Video',
    'Development',
    'Education',
    'Game',
    'Graphics',
    'Network',
    'Office',
    'Science',
    'Settings',
    'System',
    'Utility',
]

# Default settings values
DEFAULT_SETTINGS = {
    'default_icon': '',
    'default_categories': [],
    'default_terminal': False,
    'confirm_before_delete': True,
    'show_system_apps': False,
    'window_width': 900,
    'window_height': 600,
    'window_maximized': False,
}

# Undo timeout in seconds
UNDO_TIMEOUT_SECS = 5
