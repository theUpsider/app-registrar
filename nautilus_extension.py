"""Nautilus context menu extension for App Registrar.

Supports both Nautilus 3.0 (nautilus-python ≤1.2) and 4.0 APIs
by accepting *args in get_file_items (3.0 passes window as first arg,
4.0 passes only files).

Installed to ~/.local/share/nautilus-python/extensions/ and loaded
by Nautilus on startup. Requires `nautilus -q` to reload after changes.
"""

import os
import subprocess

import gi
gi.require_version('Nautilus', '4.0')
from gi.repository import Nautilus, GObject

INSTALL_DIR = os.path.expanduser('~/.local/share/nautilus-app-registrar')
APPLICATIONS_DIR = os.path.expanduser('~/.local/share/applications')
REGISTERED_BY_KEY = 'X-RegisteredBy'
REGISTERED_BY_VALUE = 'nautilus-app-registrar'


def _find_desktop_entry_for_exec(exec_path):
    if not os.path.isdir(APPLICATIONS_DIR):
        return None
    for filename in os.listdir(APPLICATIONS_DIR):
        if not filename.endswith('.desktop'):
            continue
        file_path = os.path.join(APPLICATIONS_DIR, filename)
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except (IOError, OSError):
            continue
        is_managed = False
        entry_exec = ''
        for line in content.splitlines():
            line = line.strip()
            if '=' not in line or line.startswith('#'):
                continue
            key, _, value = line.partition('=')
            key = key.strip()
            value = value.strip()
            if key == 'Exec':
                entry_exec = value.split()[0] if value else ''
            elif key == REGISTERED_BY_KEY and value == REGISTERED_BY_VALUE:
                is_managed = True
        if is_managed and entry_exec == exec_path:
            return file_path
    return None


def _launch_app(*args):
    env = os.environ.copy()
    python_path = env.get('PYTHONPATH', '')
    if INSTALL_DIR not in python_path:
        env['PYTHONPATH'] = INSTALL_DIR + ((':' + python_path) if python_path else '')
    cmd = ['/usr/bin/python3', '-m', 'app_registrar'] + list(args)
    subprocess.Popen(
        cmd,
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


class AppRegistrarMenuProvider(GObject.GObject, Nautilus.MenuProvider):

    def get_file_items(self, *args):
        # Nautilus 4.0: (files,) — Nautilus 3.0: (window, files)
        files = args[-1] if args else []

        if len(files) != 1:
            return []

        file_info = files[0]

        if file_info.get_uri_scheme() != 'file':
            return []

        file_path = file_info.get_location().get_path()
        if not file_path or not os.path.isfile(file_path):
            return []

        # os.access is reliable; Nautilus FileInfo caches stale permission data
        if not os.access(file_path, os.X_OK):
            return []

        items = []
        desktop_path = _find_desktop_entry_for_exec(file_path)

        if desktop_path is None:
            register_item = Nautilus.MenuItem(
                name='AppRegistrar::register',
                label='Register as App',
                tip='Create a desktop launcher for this executable',
                icon='application-x-executable',
            )
            register_item.connect('activate', self._on_register, file_path)
            items.append(register_item)
        else:
            unregister_item = Nautilus.MenuItem(
                name='AppRegistrar::unregister',
                label='Unregister App',
                tip='Remove the desktop launcher for this executable',
                icon='edit-delete-symbolic',
            )
            unregister_item.connect('activate', self._on_unregister, file_path)
            items.append(unregister_item)

        return items

    def _on_register(self, menu_item, file_path):
        _launch_app('--register', file_path)

    def _on_unregister(self, menu_item, file_path):
        _launch_app('--unregister', file_path)
