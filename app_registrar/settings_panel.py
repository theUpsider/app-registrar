import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw, Gio, GLib
from gettext import gettext as _

from .constants import CATEGORIES



class SettingsWindow(Adw.PreferencesWindow):

    def __init__(self, settings_manager, **kwargs):
        super().__init__(**kwargs)

        self._settings = settings_manager

        self.set_title(_('Settings'))
        self.set_default_size(450, 600)
        self.set_search_enabled(False)

        page = Adw.PreferencesPage()
        self.add(page)

        defaults_group = Adw.PreferencesGroup()
        defaults_group.set_title(_('Registration Defaults'))
        defaults_group.set_description(_('Default values for new app registrations'))
        page.add(defaults_group)

        self._icon_row = Adw.ActionRow()
        self._icon_row.set_title(_('Default Icon'))
        self._icon_row.set_subtitle(self._settings.default_icon or _('None'))
        self._icon_row.set_activatable(True)
        self._icon_row.connect('activated', self._on_browse_default_icon)

        icon_browse = Gtk.Button(icon_name='document-open-symbolic')
        icon_browse.set_valign(Gtk.Align.CENTER)
        icon_browse.add_css_class('flat')
        icon_browse.connect('clicked', self._on_browse_default_icon)
        self._icon_row.add_suffix(icon_browse)

        icon_clear = Gtk.Button(icon_name='edit-clear-symbolic')
        icon_clear.set_valign(Gtk.Align.CENTER)
        icon_clear.add_css_class('flat')
        icon_clear.connect('clicked', self._on_clear_default_icon)
        self._icon_row.add_suffix(icon_clear)

        defaults_group.add(self._icon_row)

        self._terminal_row = Adw.SwitchRow()
        self._terminal_row.set_title(_('Run in Terminal'))
        self._terminal_row.set_subtitle(_('Default for new registrations'))
        self._terminal_row.set_active(self._settings.default_terminal)
        self._terminal_row.connect('notify::active', self._on_terminal_changed)
        defaults_group.add(self._terminal_row)

        cat_group = Adw.PreferencesGroup()
        cat_group.set_title(_('Default Categories'))
        cat_group.set_description(_('Pre-selected categories for new registrations'))
        page.add(cat_group)

        self._category_checks = {}
        for cat in CATEGORIES:
            row = Adw.SwitchRow()
            row.set_title(cat)
            row.set_active(cat in self._settings.default_categories)
            row.connect('notify::active', self._on_category_changed)
            cat_group.add(row)
            self._category_checks[cat] = row

        behavior_group = Adw.PreferencesGroup()
        behavior_group.set_title(_('Behavior'))
        page.add(behavior_group)

        self._confirm_row = Adw.SwitchRow()
        self._confirm_row.set_title(_('Confirm Before Delete'))
        self._confirm_row.set_subtitle(_('Show confirmation dialog when removing an app'))
        self._confirm_row.set_active(self._settings.confirm_before_delete)
        self._confirm_row.connect('notify::active', self._on_confirm_changed)
        behavior_group.add(self._confirm_row)

        self._system_apps_row = Adw.SwitchRow()
        self._system_apps_row.set_title(_('Show System Apps'))
        self._system_apps_row.set_subtitle(_('Include apps not created by this tool (read-only)'))
        self._system_apps_row.set_active(self._settings.show_system_apps)
        self._system_apps_row.connect('notify::active', self._on_system_apps_changed)
        behavior_group.add(self._system_apps_row)

        reset_group = Adw.PreferencesGroup()
        page.add(reset_group)

        reset_btn = Gtk.Button(label=_('Reset to Defaults'))
        reset_btn.add_css_class('destructive-action')
        reset_btn.set_halign(Gtk.Align.CENTER)
        reset_btn.set_margin_top(12)
        reset_btn.connect('clicked', self._on_reset)
        reset_group.add(reset_btn)

    def _on_browse_default_icon(self, *args):
        dialog = Gtk.FileDialog()
        dialog.set_title(_('Select Default Icon'))

        filter_images = Gtk.FileFilter()
        filter_images.set_name(_('Images (PNG, SVG)'))
        filter_images.add_mime_type('image/png')
        filter_images.add_mime_type('image/svg+xml')

        filters = Gio.ListStore.new(Gtk.FileFilter)
        filters.append(filter_images)
        dialog.set_filters(filters)

        dialog.open(self, None, self._on_default_icon_selected)

    def _on_default_icon_selected(self, dialog, result):
        try:
            gfile = dialog.open_finish(result)
            path = gfile.get_path()
            self._settings.default_icon = path
            self._icon_row.set_subtitle(path)
        except GLib.Error:
            pass

    def _on_clear_default_icon(self, *args):
        self._settings.default_icon = ''
        self._icon_row.set_subtitle(_('None'))

    def _on_terminal_changed(self, row, *args):
        self._settings.default_terminal = row.get_active()

    def _on_category_changed(self, row, *args):
        cats = [cat for cat, r in self._category_checks.items() if r.get_active()]
        self._settings.default_categories = cats

    def _on_confirm_changed(self, row, *args):
        self._settings.confirm_before_delete = row.get_active()

    def _on_system_apps_changed(self, row, *args):
        self._settings.show_system_apps = row.get_active()
        parent = self.get_transient_for()
        if parent and hasattr(parent, 'refresh_list'):
            parent.refresh_list()

    def _on_reset(self, *args):
        self._settings.reset()
        self._icon_row.set_subtitle(_('None'))
        self._terminal_row.set_active(False)
        self._confirm_row.set_active(True)
        self._system_apps_row.set_active(False)
        for row in self._category_checks.values():
            row.set_active(False)
