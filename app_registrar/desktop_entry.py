"""Desktop entry (.desktop file) management."""

import os
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime

from .constants import (
    APPLICATIONS_DIR,
    REGISTERED_BY_KEY,
    REGISTERED_BY_VALUE,
    REGISTRATION_DATE_KEY,
)
from .utils import sanitize_filename, generate_keywords, update_desktop_database_async


@dataclass
class DesktopEntry:
    name: str = ''
    exec_path: str = ''
    comment: str = ''
    icon: str = ''
    categories: list = field(default_factory=list)
    keywords: list = field(default_factory=list)
    terminal: bool = False
    startup_notify: bool = True
    filename: str = ''
    registration_date: str = ''
    file_path: str = ''
    managed: bool = False
    exec_exists: bool = True


def read_desktop_entry(file_path: str):
    """Parse a .desktop file into a DesktopEntry.

    Returns None if the file cannot be read. Uses manual parsing
    because configparser mishandles Exec values containing '='
    and doesn't preserve key casing without extra config.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except (IOError, OSError, UnicodeDecodeError):
        return None

    entry = DesktopEntry()
    entry.file_path = file_path
    entry.filename = os.path.basename(file_path)

    in_section = False
    for line in content.splitlines():
        line = line.strip()
        if line == '[Desktop Entry]':
            in_section = True
            continue
        if line.startswith('[') and line.endswith(']'):
            in_section = False
            continue
        if not in_section or '=' not in line or line.startswith('#'):
            continue

        key, _, value = line.partition('=')
        key = key.strip()
        value = value.strip()

        if key == 'Name':
            entry.name = value
        elif key == 'Exec':
            entry.exec_path = value
        elif key == 'Comment':
            entry.comment = value
        elif key == 'Icon':
            entry.icon = value
        elif key == 'Categories':
            entry.categories = [c for c in value.rstrip(';').split(';') if c]
        elif key == 'Keywords':
            entry.keywords = [k for k in value.rstrip(';').split(';') if k]
        elif key == 'Terminal':
            entry.terminal = value.lower() == 'true'
        elif key == 'StartupNotify':
            entry.startup_notify = value.lower() == 'true'
        elif key == REGISTERED_BY_KEY:
            entry.managed = value == REGISTERED_BY_VALUE
        elif key == REGISTRATION_DATE_KEY:
            entry.registration_date = value

    # Use os.access for executable check, never trust cached FileInfo
    exec_base = entry.exec_path.split()[0] if entry.exec_path else ''
    if exec_base:
        entry.exec_exists = os.path.isfile(exec_base) and os.access(exec_base, os.X_OK)
    else:
        entry.exec_exists = False

    return entry


def write_desktop_entry(entry: DesktopEntry) -> str:
    """Write a valid .desktop file following the freedesktop Desktop Entry Spec.

    Returns the full file path. Runs update-desktop-database async afterwards.
    Trailing semicolons on list values per spec requirement.
    """
    if not entry.filename:
        entry.filename = sanitize_filename(entry.name) + '.desktop'

    if not entry.registration_date:
        entry.registration_date = datetime.now().isoformat()

    file_path = os.path.join(APPLICATIONS_DIR, entry.filename)
    os.makedirs(APPLICATIONS_DIR, exist_ok=True)

    categories_str = ';'.join(entry.categories) + ';' if entry.categories else ''

    all_keywords = generate_keywords(entry.name, entry.exec_path, entry.keywords)
    keywords_str = ';'.join(all_keywords) + ';' if all_keywords else ''

    lines = [
        '[Desktop Entry]',
        'Type=Application',
        'Version=1.0',
        f'Name={entry.name}',
        f'Exec={entry.exec_path}',
    ]

    if entry.comment:
        lines.append(f'Comment={entry.comment}')
    if entry.icon:
        lines.append(f'Icon={entry.icon}')
    if categories_str:
        lines.append(f'Categories={categories_str}')
    if keywords_str:
        lines.append(f'Keywords={keywords_str}')

    lines.append(f'Terminal={"true" if entry.terminal else "false"}')
    lines.append(f'StartupNotify={"true" if entry.startup_notify else "false"}')
    lines.append(f'{REGISTERED_BY_KEY}={REGISTERED_BY_VALUE}')
    lines.append(f'{REGISTRATION_DATE_KEY}={entry.registration_date}')
    lines.append('')  # trailing newline required by spec

    with open(file_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))

    entry.file_path = file_path
    update_desktop_database_async()

    return file_path


def delete_desktop_entry(file_path: str) -> bool:
    try:
        os.remove(file_path)
        update_desktop_database_async()
        return True
    except (IOError, OSError):
        return False


def get_managed_entries() -> list:
    entries = []
    if not os.path.isdir(APPLICATIONS_DIR):
        return entries

    for filename in sorted(os.listdir(APPLICATIONS_DIR)):
        if not filename.endswith('.desktop'):
            continue
        file_path = os.path.join(APPLICATIONS_DIR, filename)
        entry = read_desktop_entry(file_path)
        if entry and entry.managed:
            entries.append(entry)

    return sorted(entries, key=lambda e: e.name.lower())


def get_all_desktop_entries() -> list:
    entries = []
    if not os.path.isdir(APPLICATIONS_DIR):
        return entries

    for filename in sorted(os.listdir(APPLICATIONS_DIR)):
        if not filename.endswith('.desktop'):
            continue
        file_path = os.path.join(APPLICATIONS_DIR, filename)
        entry = read_desktop_entry(file_path)
        if entry and entry.name:
            entries.append(entry)

    return sorted(entries, key=lambda e: e.name.lower())


def find_entry_for_exec(exec_path: str):
    for entry in get_managed_entries():
        exec_base = entry.exec_path.split()[0] if entry.exec_path else ''
        if exec_base == exec_path:
            return entry
    return None


def find_duplicate_names() -> dict:
    name_map = defaultdict(list)
    for entry in get_managed_entries():
        name_map[entry.name.lower()].append(entry)
    return {k: v for k, v in name_map.items() if len(v) > 1}
