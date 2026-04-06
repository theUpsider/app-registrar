import json
import os
from copy import deepcopy

from .constants import CONFIG_DIR, SETTINGS_FILE, DEFAULT_SETTINGS


class SettingsManager:

    def __init__(self):
        self._settings = deepcopy(DEFAULT_SETTINGS)
        self.load()

    def load(self):
        try:
            with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
                saved = json.load(f)
            for key, value in DEFAULT_SETTINGS.items():
                if key not in saved:
                    saved[key] = value
            self._settings = saved
        except (FileNotFoundError, json.JSONDecodeError, IOError):
            self._settings = deepcopy(DEFAULT_SETTINGS)

    def save(self):
        os.makedirs(CONFIG_DIR, exist_ok=True, mode=0o700)
        with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
            json.dump(self._settings, f, indent=2)

    def get(self, key: str, default=None):
        return self._settings.get(key, default)

    def set(self, key: str, value):
        self._settings[key] = value
        self.save()

    def reset(self):
        self._settings = deepcopy(DEFAULT_SETTINGS)
        self.save()

    @property
    def default_icon(self) -> str:
        return self._settings.get('default_icon', '')

    @default_icon.setter
    def default_icon(self, value: str):
        self.set('default_icon', value)

    @property
    def default_categories(self) -> list:
        return self._settings.get('default_categories', [])

    @default_categories.setter
    def default_categories(self, value: list):
        self.set('default_categories', value)

    @property
    def default_terminal(self) -> bool:
        return self._settings.get('default_terminal', False)

    @default_terminal.setter
    def default_terminal(self, value: bool):
        self.set('default_terminal', value)

    @property
    def confirm_before_delete(self) -> bool:
        return self._settings.get('confirm_before_delete', True)

    @confirm_before_delete.setter
    def confirm_before_delete(self, value: bool):
        self.set('confirm_before_delete', value)

    @property
    def show_system_apps(self) -> bool:
        return self._settings.get('show_system_apps', False)

    @show_system_apps.setter
    def show_system_apps(self, value: bool):
        self.set('show_system_apps', value)

    @property
    def window_width(self) -> int:
        return self._settings.get('window_width', 900)

    @window_width.setter
    def window_width(self, value: int):
        self.set('window_width', value)

    @property
    def window_height(self) -> int:
        return self._settings.get('window_height', 600)

    @window_height.setter
    def window_height(self, value: int):
        self.set('window_height', value)

    @property
    def window_maximized(self) -> bool:
        return self._settings.get('window_maximized', False)

    @window_maximized.setter
    def window_maximized(self, value: bool):
        self.set('window_maximized', value)
