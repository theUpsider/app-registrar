import os

import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw
from gettext import gettext as _




class DetailView(Gtk.Box):

    def __init__(self, **kwargs):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=0, **kwargs)

        self._entry = None

        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scroll.set_vexpand(True)

        clamp = Adw.Clamp()
        clamp.set_maximum_size(600)

        content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        content.set_margin_top(24)
        content.set_margin_bottom(24)
        content.set_margin_start(16)
        content.set_margin_end(16)

        self._icon = Gtk.Image()
        self._icon.set_pixel_size(96)
        self._icon.set_halign(Gtk.Align.CENTER)
        self._icon.set_margin_bottom(12)
        content.append(self._icon)

        self._name = Gtk.Label()
        self._name.add_css_class('title-1')
        self._name.set_halign(Gtk.Align.CENTER)
        content.append(self._name)

        self._comment = Gtk.Label()
        self._comment.add_css_class('dim-label')
        self._comment.set_halign(Gtk.Align.CENTER)
        self._comment.set_wrap(True)
        content.append(self._comment)

        self._warning_box = Gtk.Box(spacing=8)
        self._warning_box.set_halign(Gtk.Align.CENTER)
        self._warning_box.set_margin_top(8)
        self._warning_box.add_css_class('warning')

        warning_icon = Gtk.Image.new_from_icon_name('dialog-warning-symbolic')
        self._warning_box.append(warning_icon)

        self._warning_label = Gtk.Label(label=_('Executable not found'))
        self._warning_box.append(self._warning_label)
        self._warning_box.set_visible(False)
        content.append(self._warning_box)

        details_group = Adw.PreferencesGroup()
        details_group.set_title(_('Details'))
        details_group.set_margin_top(16)

        self._exec_row = Adw.ActionRow()
        self._exec_row.set_title(_('Executable'))
        self._exec_row.set_subtitle_selectable(True)
        details_group.add(self._exec_row)

        self._categories_row = Adw.ActionRow()
        self._categories_row.set_title(_('Categories'))
        details_group.add(self._categories_row)

        self._keywords_row = Adw.ActionRow()
        self._keywords_row.set_title(_('Keywords'))
        details_group.add(self._keywords_row)

        self._terminal_row = Adw.ActionRow()
        self._terminal_row.set_title(_('Run in Terminal'))
        details_group.add(self._terminal_row)

        self._notify_row = Adw.ActionRow()
        self._notify_row.set_title(_('Startup Notification'))
        details_group.add(self._notify_row)

        self._date_row = Adw.ActionRow()
        self._date_row.set_title(_('Registration Date'))
        details_group.add(self._date_row)

        self._file_row = Adw.ActionRow()
        self._file_row.set_title(_('Desktop File'))
        self._file_row.set_subtitle_selectable(True)
        details_group.add(self._file_row)

        content.append(details_group)

        clamp.set_child(content)
        scroll.set_child(clamp)
        self.append(scroll)

    def set_entry(self, entry):
        self._entry = entry

        if not entry:
            return

        if entry.icon and os.path.isfile(entry.icon):
            self._icon.set_from_file(entry.icon)
        elif entry.icon:
            self._icon.set_from_icon_name(entry.icon)
        else:
            self._icon.set_from_icon_name('application-x-executable-symbolic')

        self._name.set_text(entry.name)
        self._comment.set_text(entry.comment or _('No description'))

        self._warning_box.set_visible(not entry.exec_exists)

        self._exec_row.set_subtitle(entry.exec_path)
        self._categories_row.set_subtitle(', '.join(entry.categories) or _('None'))
        self._keywords_row.set_subtitle(', '.join(entry.keywords) or _('None'))
        self._terminal_row.set_subtitle(_('Yes') if entry.terminal else _('No'))
        self._notify_row.set_subtitle(_('Yes') if entry.startup_notify else _('No'))
        self._date_row.set_subtitle(entry.registration_date or _('Unknown'))
        self._file_row.set_subtitle(entry.file_path)

    @property
    def entry(self):
        return self._entry
