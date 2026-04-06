import os

import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw, Gio, GLib
from gettext import gettext as _

from .constants import CATEGORIES
from .desktop_entry import DesktopEntry, write_desktop_entry
from .utils import sanitize_filename, validate_exec_path


class RegistrationDialog(Adw.Window):

    def __init__(self, parent, entry=None, exec_path=None, settings_manager=None,
                 on_save=None, **kwargs):
        super().__init__(**kwargs)

        self._entry = entry
        self._on_save = on_save
        self._settings = settings_manager
        self._icon_path = ''

        self.set_transient_for(parent)
        self.set_modal(True)
        self.set_default_size(500, 700)

        is_edit = entry is not None
        self.set_title(_('Edit App') if is_edit else _('Register as App'))

        toolbar_view = Adw.ToolbarView()

        header = Adw.HeaderBar()

        cancel_btn = Gtk.Button(label=_('Cancel'))
        cancel_btn.connect('clicked', lambda *_: self.close())
        header.pack_start(cancel_btn)

        save_label = _('Save') if is_edit else _('Register')
        self._save_btn = Gtk.Button(label=save_label)
        self._save_btn.add_css_class('suggested-action')
        self._save_btn.set_sensitive(is_edit)
        self._save_btn.connect('clicked', self._on_save_clicked)
        header.pack_end(self._save_btn)

        toolbar_view.add_top_bar(header)

        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)

        clamp = Adw.Clamp()
        clamp.set_maximum_size(500)
        clamp.set_margin_top(24)
        clamp.set_margin_bottom(24)
        clamp.set_margin_start(12)
        clamp.set_margin_end(12)

        content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=24)

        general_group = Adw.PreferencesGroup()
        general_group.set_title(_('General'))

        self._name_row = Adw.EntryRow()
        self._name_row.set_title(_('Name'))
        self._name_row.connect('changed', self._on_name_changed)
        general_group.add(self._name_row)

        self._comment_row = Adw.EntryRow()
        self._comment_row.set_title(_('Comment'))
        general_group.add(self._comment_row)

        self._exec_row = Adw.EntryRow()
        self._exec_row.set_title(_('Executable'))

        exec_browse = Gtk.Button(icon_name='document-open-symbolic')
        exec_browse.set_valign(Gtk.Align.CENTER)
        exec_browse.add_css_class('flat')
        exec_browse.connect('clicked', self._on_browse_exec)
        self._exec_row.add_suffix(exec_browse)
        general_group.add(self._exec_row)

        content.append(general_group)

        icon_group = Adw.PreferencesGroup()
        icon_group.set_title(_('Appearance'))

        self._icon_preview = Gtk.Image.new_from_icon_name('application-x-executable-symbolic')
        self._icon_preview.set_pixel_size(48)

        self._icon_row = Adw.ActionRow()
        self._icon_row.set_title(_('Icon'))
        self._icon_row.set_subtitle(_('Click to select an icon'))
        self._icon_row.add_prefix(self._icon_preview)
        self._icon_row.set_activatable(True)
        self._icon_row.connect('activated', self._on_browse_icon)

        icon_browse = Gtk.Button(icon_name='document-open-symbolic')
        icon_browse.set_valign(Gtk.Align.CENTER)
        icon_browse.add_css_class('flat')
        icon_browse.connect('clicked', self._on_browse_icon)
        self._icon_row.add_suffix(icon_browse)

        icon_clear = Gtk.Button(icon_name='edit-clear-symbolic')
        icon_clear.set_valign(Gtk.Align.CENTER)
        icon_clear.add_css_class('flat')
        icon_clear.connect('clicked', self._on_clear_icon)
        self._icon_row.add_suffix(icon_clear)

        icon_group.add(self._icon_row)
        content.append(icon_group)

        categories_group = Adw.PreferencesGroup()
        categories_group.set_title(_('Categories'))

        self._category_checks = {}

        flow = Gtk.FlowBox()
        flow.set_selection_mode(Gtk.SelectionMode.NONE)
        flow.set_max_children_per_line(3)
        flow.set_min_children_per_line(2)
        flow.set_row_spacing(6)
        flow.set_column_spacing(12)
        flow.set_homogeneous(True)
        flow.set_margin_top(6)
        flow.set_margin_bottom(6)
        flow.set_margin_start(12)
        flow.set_margin_end(12)

        for cat in CATEGORIES:
            check = Gtk.CheckButton(label=cat)
            flow.append(check)
            self._category_checks[cat] = check

        categories_group.add(flow)
        content.append(categories_group)

        options_group = Adw.PreferencesGroup()
        options_group.set_title(_('Options'))

        self._terminal_row = Adw.SwitchRow()
        self._terminal_row.set_title(_('Run in Terminal'))
        self._terminal_row.set_subtitle(_('Launch the app inside a terminal emulator'))
        options_group.add(self._terminal_row)

        self._notify_row = Adw.SwitchRow()
        self._notify_row.set_title(_('Startup Notification'))
        self._notify_row.set_subtitle(_('Show a loading indicator when launching'))
        self._notify_row.set_active(True)
        options_group.add(self._notify_row)

        content.append(options_group)

        self._warning_label = Gtk.Label()
        self._warning_label.add_css_class('error')
        self._warning_label.set_wrap(True)
        self._warning_label.set_visible(False)
        content.append(self._warning_label)

        clamp.set_child(content)
        scroll.set_child(clamp)
        toolbar_view.set_content(scroll)
        self.set_content(toolbar_view)

        if is_edit:
            self._prefill_from_entry(entry)
        elif exec_path:
            self._exec_row.set_text(exec_path)

        if not is_edit and self._settings:
            if self._settings.default_terminal:
                self._terminal_row.set_active(True)
            for cat in self._settings.default_categories:
                if cat in self._category_checks:
                    self._category_checks[cat].set_active(True)
            if self._settings.default_icon and not self._icon_path:
                self._set_icon(self._settings.default_icon)

    def _prefill_from_entry(self, entry):
        self._name_row.set_text(entry.name)
        self._comment_row.set_text(entry.comment)
        self._exec_row.set_text(entry.exec_path)
        if entry.icon:
            self._set_icon(entry.icon)
        for cat in entry.categories:
            if cat in self._category_checks:
                self._category_checks[cat].set_active(True)
        self._terminal_row.set_active(entry.terminal)
        self._notify_row.set_active(entry.startup_notify)

    def _set_icon(self, path):
        self._icon_path = path
        if path and os.path.isfile(path):
            self._icon_preview.set_from_file(path)
            self._icon_row.set_subtitle(os.path.basename(path))
        elif path:
            self._icon_preview.set_from_icon_name(path)
            self._icon_row.set_subtitle(path)
        else:
            self._icon_preview.set_from_icon_name('application-x-executable-symbolic')
            self._icon_row.set_subtitle(_('Click to select an icon'))

    def _on_name_changed(self, row):
        name = row.get_text().strip()
        self._save_btn.set_sensitive(bool(name))
        self._warning_label.set_visible(False)

    def _on_browse_exec(self, *args):
        dialog = Gtk.FileDialog()
        dialog.set_title(_('Select Executable'))
        dialog.open(self, None, self._on_exec_selected)

    def _on_exec_selected(self, dialog, result):
        try:
            gfile = dialog.open_finish(result)
            self._exec_row.set_text(gfile.get_path())
        except GLib.Error:
            pass

    def _on_browse_icon(self, *args):
        dialog = Gtk.FileDialog()
        dialog.set_title(_('Select Icon'))

        filter_images = Gtk.FileFilter()
        filter_images.set_name(_('Images (PNG, SVG)'))
        filter_images.add_mime_type('image/png')
        filter_images.add_mime_type('image/svg+xml')

        filters = Gio.ListStore.new(Gtk.FileFilter)
        filters.append(filter_images)
        dialog.set_filters(filters)

        dialog.open(self, None, self._on_icon_selected)

    def _on_icon_selected(self, dialog, result):
        try:
            gfile = dialog.open_finish(result)
            self._set_icon(gfile.get_path())
        except GLib.Error:
            pass

    def _on_clear_icon(self, *args):
        self._set_icon('')

    def _on_save_clicked(self, *args):
        name = self._name_row.get_text().strip()
        exec_path = self._exec_row.get_text().strip()

        if not name:
            self._show_warning(_('Name is required'))
            return

        valid, error = validate_exec_path(exec_path)
        if not valid:
            self._show_warning(error)
            return

        categories = [cat for cat, check in self._category_checks.items()
                      if check.get_active()]

        if self._entry:
            entry = self._entry
            entry.name = name
            entry.exec_path = exec_path
            entry.comment = self._comment_row.get_text().strip()
            entry.icon = self._icon_path
            entry.categories = categories
            entry.terminal = self._terminal_row.get_active()
            entry.startup_notify = self._notify_row.get_active()
        else:
            entry = DesktopEntry(
                name=name,
                exec_path=exec_path,
                comment=self._comment_row.get_text().strip(),
                icon=self._icon_path,
                categories=categories,
                terminal=self._terminal_row.get_active(),
                startup_notify=self._notify_row.get_active(),
                filename=sanitize_filename(name) + '.desktop',
                managed=True,
            )

        try:
            write_desktop_entry(entry)
            if self._on_save:
                self._on_save(entry)
            self.close()
        except Exception as e:
            self._show_warning(str(e))

    def _show_warning(self, message):
        self._warning_label.set_text(message)
        self._warning_label.set_visible(True)
