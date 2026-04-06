import os

import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw, GLib, Gio
from gettext import gettext as _

from .constants import UNDO_TIMEOUT_SECS
from .desktop_entry import (
    delete_desktop_entry,
    get_all_desktop_entries,
    get_managed_entries,
)
from .detail_view import DetailView
from .registration_dialog import RegistrationDialog



class EntryRow(Adw.ActionRow):

    def __init__(self, entry, **kwargs):
        super().__init__(**kwargs)

        self.entry = entry

        self.set_title(GLib.markup_escape_text(entry.name))
        subtitle = entry.exec_path
        if entry.categories:
            subtitle += '  ·  ' + ', '.join(entry.categories)
        self.set_subtitle(GLib.markup_escape_text(subtitle))
        self.set_activatable(True)

        icon = Gtk.Image()
        icon.set_pixel_size(32)
        if entry.icon and os.path.isfile(entry.icon):
            icon.set_from_file(entry.icon)
        elif entry.icon:
            icon.set_from_icon_name(entry.icon)
        else:
            icon.set_from_icon_name('application-x-executable-symbolic')
        self.add_prefix(icon)

        if not entry.exec_exists:
            warning = Gtk.Image.new_from_icon_name('dialog-warning-symbolic')
            warning.add_css_class('warning')
            warning.set_tooltip_text(_('Executable not found'))
            self.add_suffix(warning)

        if not entry.managed:
            lock = Gtk.Image.new_from_icon_name('changes-prevent-symbolic')
            lock.set_tooltip_text(_('System app (read-only)'))
            self.add_suffix(lock)

        arrow = Gtk.Image.new_from_icon_name('go-next-symbolic')
        arrow.add_css_class('dim-label')
        self.add_suffix(arrow)


class MainWindow(Adw.ApplicationWindow):

    def __init__(self, app, settings_manager, **kwargs):
        super().__init__(application=app, **kwargs)

        self._settings = settings_manager
        self._entries = []
        self._selected_entry = None
        self._pending_delete = None
        self._undo_timeout_id = 0
        self._undo_backup_content = None

        self.set_title(_('App Registrar'))
        self.set_default_size(
            self._settings.window_width,
            self._settings.window_height,
        )
        if self._settings.window_maximized:
            self.maximize()

        self.connect('notify::default-width', self._on_window_size_changed)
        self.connect('notify::default-height', self._on_window_size_changed)
        self.connect('notify::maximized', self._on_maximized_changed)

        self._setup_actions()
        self._build_ui()
        self.refresh_list()
        self._validate_entries_async()

    def _setup_actions(self):
        new_action = Gio.SimpleAction.new('new-entry', None)
        new_action.connect('activate', self._on_new_entry)
        self.add_action(new_action)

        edit_action = Gio.SimpleAction.new('edit-entry', None)
        edit_action.connect('activate', self._on_edit_entry)
        edit_action.set_enabled(False)
        self.add_action(edit_action)

        delete_action = Gio.SimpleAction.new('delete-entry', None)
        delete_action.connect('activate', self._on_delete_entry)
        delete_action.set_enabled(False)
        self.add_action(delete_action)

    def _build_ui(self):
        self._toast_overlay = Adw.ToastOverlay()
        self.set_content(self._toast_overlay)

        self._split_view = Adw.NavigationSplitView()
        self._toast_overlay.set_child(self._split_view)

        sidebar_page = Adw.NavigationPage.new(self._build_sidebar(), _('Apps'))
        self._split_view.set_sidebar(sidebar_page)

        content_page = Adw.NavigationPage.new(self._build_content(), _('Details'))
        self._split_view.set_content(content_page)

    def _build_sidebar(self):
        toolbar_view = Adw.ToolbarView()

        header = Adw.HeaderBar()

        menu_model = Gio.Menu()
        menu_model.append(_('Settings'), 'app.settings')
        menu_model.append(_('About'), 'app.about')

        menu_btn = Gtk.MenuButton()
        menu_btn.set_icon_name('open-menu-symbolic')
        menu_btn.set_menu_model(menu_model)
        header.pack_end(menu_btn)

        new_btn = Gtk.Button(icon_name='list-add-symbolic')
        new_btn.set_tooltip_text(_('Register new app (Ctrl+N)'))
        new_btn.set_action_name('win.new-entry')
        header.pack_start(new_btn)

        toolbar_view.add_top_bar(header)

        self._search_entry = Gtk.SearchEntry()
        self._search_entry.set_placeholder_text(_('Search apps…'))
        self._search_entry.set_margin_start(8)
        self._search_entry.set_margin_end(8)
        self._search_entry.set_margin_top(4)
        self._search_entry.set_margin_bottom(4)
        self._search_entry.connect('search-changed', self._on_search_changed)
        toolbar_view.add_top_bar(self._search_entry)

        sidebar_content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)

        self._banner = Adw.Banner()
        self._banner.set_title(_('Some registered apps have missing executables'))
        self._banner.set_button_label(_('Show'))
        self._banner.connect('button-clicked', self._on_banner_show_broken)
        self._banner.set_revealed(False)
        sidebar_content.append(self._banner)

        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scroll.set_vexpand(True)

        self._list_box = Gtk.ListBox()
        self._list_box.set_selection_mode(Gtk.SelectionMode.SINGLE)
        self._list_box.add_css_class('navigation-sidebar')
        self._list_box.set_placeholder(self._build_empty_state())
        self._list_box.connect('row-selected', self._on_row_selected)
        scroll.set_child(self._list_box)
        sidebar_content.append(scroll)

        toolbar_view.set_content(sidebar_content)
        return toolbar_view

    def _build_content(self):
        toolbar_view = Adw.ToolbarView()

        header = Adw.HeaderBar()

        edit_btn = Gtk.Button(icon_name='document-edit-symbolic')
        edit_btn.set_tooltip_text(_('Edit (Ctrl+E / F2)'))
        edit_btn.set_action_name('win.edit-entry')
        header.pack_end(edit_btn)

        delete_btn = Gtk.Button(icon_name='user-trash-symbolic')
        delete_btn.set_tooltip_text(_('Delete (Delete / Ctrl+Backspace)'))
        delete_btn.add_css_class('destructive-action')
        delete_btn.set_action_name('win.delete-entry')
        header.pack_end(delete_btn)

        toolbar_view.add_top_bar(header)

        self._detail_stack = Gtk.Stack()
        self._detail_stack.set_transition_type(Gtk.StackTransitionType.CROSSFADE)

        empty_detail = Adw.StatusPage()
        empty_detail.set_icon_name('view-list-symbolic')
        empty_detail.set_title(_('Select an App'))
        empty_detail.set_description(_('Choose an app from the list to view its details'))
        self._detail_stack.add_named(empty_detail, 'empty')

        self._detail_view = DetailView()
        self._detail_stack.add_named(self._detail_view, 'detail')

        self._detail_stack.set_visible_child_name('empty')
        toolbar_view.set_content(self._detail_stack)

        return toolbar_view

    def _build_empty_state(self):
        status = Adw.StatusPage()
        status.set_icon_name('application-x-executable-symbolic')
        status.set_title(_('No Apps Registered'))
        status.set_description(
            _('Right-click an executable in Nautilus to register it as an app, or click + above.')
        )
        return status

    def refresh_list(self):
        if self._settings.show_system_apps:
            self._entries = get_all_desktop_entries()
        else:
            self._entries = get_managed_entries()

        self._rebuild_list()

    def _rebuild_list(self):
        search_text = self._search_entry.get_text().strip().lower()

        while True:
            row = self._list_box.get_row_at_index(0)
            if row is None:
                break
            self._list_box.remove(row)

        visible_entries = self._entries
        if search_text:
            visible_entries = [
                e for e in self._entries
                if search_text in e.name.lower()
                or any(search_text in c.lower() for c in e.categories)
                or any(search_text in k.lower() for k in e.keywords)
            ]

        for entry in visible_entries:
            row = EntryRow(entry)
            self._list_box.append(row)

        if self._selected_entry:
            for i, entry in enumerate(visible_entries):
                if entry.file_path == self._selected_entry.file_path:
                    row = self._list_box.get_row_at_index(i)
                    if row:
                        self._list_box.select_row(row)
                    return

        first = self._list_box.get_row_at_index(0)
        if first:
            self._list_box.select_row(first)
        else:
            self._on_row_selected(self._list_box, None)

    def _on_search_changed(self, entry):
        self._rebuild_list()

    def _on_row_selected(self, list_box, row):
        if row and isinstance(row, EntryRow):
            self._selected_entry = row.entry
            self._detail_view.set_entry(row.entry)
            self._detail_stack.set_visible_child_name('detail')

            is_managed = row.entry.managed
            self.lookup_action('edit-entry').set_enabled(is_managed)
            self.lookup_action('delete-entry').set_enabled(is_managed)
        else:
            self._selected_entry = None
            self._detail_stack.set_visible_child_name('empty')
            self.lookup_action('edit-entry').set_enabled(False)
            self.lookup_action('delete-entry').set_enabled(False)

    def _on_new_entry(self, *args):
        dialog = RegistrationDialog(
            parent=self,
            settings_manager=self._settings,
            on_save=self._on_entry_saved,
        )
        dialog.present()

    def _on_edit_entry(self, *args):
        if not self._selected_entry or not self._selected_entry.managed:
            return
        dialog = RegistrationDialog(
            parent=self,
            entry=self._selected_entry,
            settings_manager=self._settings,
            on_save=self._on_entry_saved,
        )
        dialog.present()

    def _on_entry_saved(self, entry):
        self._selected_entry = entry
        self.refresh_list()

    def _on_delete_entry(self, *args):
        if not self._selected_entry or not self._selected_entry.managed:
            return

        if self._settings.confirm_before_delete:
            self._show_delete_confirmation()
        else:
            self._do_delete()

    def _show_delete_confirmation(self):
        dialog = Adw.AlertDialog()
        dialog.set_heading(_('Remove App?'))
        dialog.set_body(
            _("Remove '{}' from the app menu?").format(self._selected_entry.name)
        )
        dialog.add_response('cancel', _('Cancel'))
        dialog.add_response('delete', _('Remove'))
        dialog.set_response_appearance('delete', Adw.ResponseAppearance.DESTRUCTIVE)
        dialog.set_default_response('cancel')
        dialog.set_close_response('cancel')
        dialog.connect('response', self._on_delete_response)
        dialog.present(self)

    def _on_delete_response(self, dialog, response):
        if response == 'delete':
            self._do_delete()

    def _do_delete(self):
        entry = self._selected_entry
        if not entry:
            return

        try:
            with open(entry.file_path, 'r', encoding='utf-8') as f:
                self._undo_backup_content = f.read()
        except (IOError, OSError):
            self._undo_backup_content = None

        self._pending_delete = entry
        delete_desktop_entry(entry.file_path)
        self._selected_entry = None
        self.refresh_list()

        toast = Adw.Toast.new(
            _("'{}' removed").format(entry.name)
        )
        toast.set_button_label(_('Undo'))
        toast.set_action_name('win.undo-delete')
        toast.set_timeout(UNDO_TIMEOUT_SECS)
        toast.connect('dismissed', self._on_undo_timeout)

        undo_action = Gio.SimpleAction.new('undo-delete', None)
        undo_action.connect('activate', self._on_undo_delete)
        self.add_action(undo_action)

        self._toast_overlay.add_toast(toast)

    def _on_undo_delete(self, *args):
        if self._pending_delete and self._undo_backup_content:
            entry = self._pending_delete
            try:
                os.makedirs(os.path.dirname(entry.file_path), exist_ok=True)
                with open(entry.file_path, 'w', encoding='utf-8') as f:
                    f.write(self._undo_backup_content)
                from .utils import update_desktop_database_async
                update_desktop_database_async()
            except (IOError, OSError):
                pass

            self._pending_delete = None
            self._undo_backup_content = None
            self._selected_entry = entry
            self.refresh_list()

    def _on_undo_timeout(self, toast):
        self._pending_delete = None
        self._undo_backup_content = None
        try:
            self.remove_action('undo-delete')
        except Exception:
            pass

    def _validate_entries_async(self):
        GLib.idle_add(self._run_validation)

    def _run_validation(self):
        broken = [e for e in self._entries if e.managed and not e.exec_exists]
        self._banner.set_revealed(len(broken) > 0)
        return GLib.SOURCE_REMOVE

    def _on_banner_show_broken(self, *args):
        self._search_entry.set_text('')
        broken = [e for e in self._entries if not e.exec_exists]
        if broken:
            for i in range(self._list_box.get_last_child() is not None):
                row = self._list_box.get_row_at_index(i)
                if row and isinstance(row, EntryRow) and not row.entry.exec_exists:
                    self._list_box.select_row(row)
                    break
        self._banner.set_revealed(False)

    def _on_window_size_changed(self, *args):
        if not self.is_maximized():
            self._settings.window_width = self.get_default_size()[0]
            self._settings.window_height = self.get_default_size()[1]

    def _on_maximized_changed(self, *args):
        self._settings.window_maximized = self.is_maximized()
