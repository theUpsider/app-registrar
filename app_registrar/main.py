import sys

import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw, Gio, GLib
from gettext import gettext as _

from .constants import APP_ID, APP_NAME, APP_VERSION
from .settings_manager import SettingsManager
from .window import MainWindow


class AppRegistrar(Adw.Application):

    def __init__(self):
        super().__init__(
            application_id=APP_ID,
            flags=Gio.ApplicationFlags.HANDLES_COMMAND_LINE,
        )

        self._settings_manager = SettingsManager()
        self._register_path = None
        self._unregister_path = None

        self.add_main_option(
            'register', 0, GLib.OptionFlags.NONE,
            GLib.OptionArg.FILENAME, 'Register a file as app', 'PATH',
        )
        self.add_main_option(
            'unregister', 0, GLib.OptionFlags.NONE,
            GLib.OptionArg.FILENAME, 'Unregister an app by exec path', 'PATH',
        )

    def do_command_line(self, command_line):
        options = command_line.get_options_dict()

        if options.contains('register'):
            path_bytes = options.lookup_value('register', GLib.VariantType.new('ay'))
            if path_bytes:
                self._register_path = bytes(path_bytes).decode('utf-8').rstrip('\x00')

        if options.contains('unregister'):
            path_bytes = options.lookup_value('unregister', GLib.VariantType.new('ay'))
            if path_bytes:
                self._unregister_path = bytes(path_bytes).decode('utf-8').rstrip('\x00')

        self.activate()
        return 0

    def do_activate(self):
        win = self.get_active_window()
        if not win:
            win = MainWindow(app=self, settings_manager=self._settings_manager)
            self._setup_actions(win)
            self._setup_accels()

        if self._register_path:
            from .registration_dialog import RegistrationDialog
            dialog = RegistrationDialog(
                parent=win,
                exec_path=self._register_path,
                settings_manager=self._settings_manager,
                on_save=lambda entry: win.refresh_list(),
            )
            dialog.present()
            self._register_path = None

        if self._unregister_path:
            from .desktop_entry import find_entry_for_exec, delete_desktop_entry
            entry = find_entry_for_exec(self._unregister_path)
            if entry:
                delete_desktop_entry(entry.file_path)
                win.refresh_list()
            self._unregister_path = None

        win.present()

    def _setup_actions(self, win):
        settings_action = Gio.SimpleAction.new('settings', None)
        settings_action.connect('activate', self._on_settings, win)
        self.add_action(settings_action)

        about_action = Gio.SimpleAction.new('about', None)
        about_action.connect('activate', self._on_about, win)
        self.add_action(about_action)

        quit_action = Gio.SimpleAction.new('quit', None)
        quit_action.connect('activate', lambda *_: self.quit())
        self.add_action(quit_action)

    def _setup_accels(self):
        self.set_accels_for_action('win.new-entry', ['<Control>n'])
        self.set_accels_for_action('win.edit-entry', ['<Control>e', 'F2'])
        self.set_accels_for_action('win.delete-entry', ['Delete', '<Control>BackSpace'])
        self.set_accels_for_action('app.quit', ['<Control>q'])

    def _on_settings(self, action, param, win):
        from .settings_panel import SettingsWindow
        settings_win = SettingsWindow(
            settings_manager=self._settings_manager,
            transient_for=win,
            modal=True,
        )
        settings_win.present()

    def _on_about(self, action, param, win):
        about = Adw.AboutDialog(
            application_name=APP_NAME,
            application_icon='application-x-executable',
            version=APP_VERSION,
            developer_name='David Vincent Fischer',
            license_type=Gtk.License.GPL_3_0,
            comments=_('Register executables as desktop applications'),
            website='https://github.com/theUpsider/app-registrar',
        )
        about.present(win)


def main():
    app = AppRegistrar()
    app.run(sys.argv)
