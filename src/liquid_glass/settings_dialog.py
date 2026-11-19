"""Settings window: profile, appearance, Jamendo account and music library."""

from __future__ import annotations

from pathlib import Path
from typing import Callable

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, Gio, GLib, Gtk  # noqa: E402

from .jamendo import CLIENT_ID_FILE  # noqa: E402
from .library import CONFIG_FILE  # noqa: E402
from .profile import (  # noqa: E402
    clean_display_name,
    clean_username,
    import_avatar,
    load_avatar_paintable,
    remove_avatar,
)
from .settings import THEME_ORDER, THEMES, Settings, save_settings  # noqa: E402


class SettingsWindow(Adw.PreferencesWindow):
    def __init__(
        self,
        parent,
        settings: Settings,
        on_theme_changed: Callable[[str], None],
        on_choose_folder: Callable[[], None],
        on_profile_changed: Callable[[Settings], None],
    ) -> None:
        super().__init__(transient_for=parent, modal=True, title="Settings")
        self.set_default_size(520, 640)
        self.settings = settings
        self._on_theme_changed = on_theme_changed
        self._on_profile_changed = on_profile_changed

        page = Adw.PreferencesPage()

        page.add(self._build_profile_group())

        appearance = Adw.PreferencesGroup()
        appearance.set_title("Appearance")
        theme_row = Adw.ComboRow()
        theme_row.set_title("Theme")
        theme_row.set_subtitle("Liquid Glass is the default look")
        theme_row.set_model(Gtk.StringList.new([THEMES[key][0] for key in THEME_ORDER]))
        theme_row.set_selected(THEME_ORDER.index(settings.theme))
        theme_row.connect("notify::selected", self._on_theme_selected)
        appearance.add(theme_row)
        page.add(appearance)

        account = Adw.PreferencesGroup()
        account.set_title("Jamendo")
        account.set_description("Client ID from the Jamendo developer portal, used for online search.")
        self.client_row = Adw.EntryRow()
        self.client_row.set_title("Client ID")
        existing = CLIENT_ID_FILE.read_text().strip() if CLIENT_ID_FILE.exists() else ""
        self.client_row.set_text(existing)
        self.client_row.connect("apply", self._on_client_apply)
        account.add(self.client_row)
        page.add(account)

        library = Adw.PreferencesGroup()
        library.set_title("Library")
        folder_row = Adw.ActionRow()
        folder_row.set_title("Music folder")
        current = CONFIG_FILE.read_text().strip() if CONFIG_FILE.exists() else ""
        folder_row.set_subtitle(current or "Not set")
        choose = Gtk.Button(label="Choose…")
        choose.set_valign(Gtk.Align.CENTER)
        choose.add_css_class("flat")
        choose.connect("clicked", lambda *_: on_choose_folder())
        folder_row.add_suffix(choose)
        library.add(folder_row)
        page.add(library)

        self.add(page)

    # ------------------------------------------------------------- profile

    def _build_profile_group(self) -> Adw.PreferencesGroup:
        group = Adw.PreferencesGroup()
        group.set_title("Profile")
        group.set_description("Stored only on this computer.")

        icon_row = Adw.ActionRow()
        icon_row.set_title("Icon")
        icon_row.set_subtitle("Choose an image from your files")
        self.avatar = Adw.Avatar()
        self.avatar.set_size(56)
        self.avatar.set_show_initials(True)
        icon_row.add_prefix(self.avatar)

        change = Gtk.Button(label="Change")
        change.set_valign(Gtk.Align.CENTER)
        change.add_css_class("flat")
        change.connect("clicked", lambda *_: self._choose_avatar())
        icon_row.add_suffix(change)

        remove = Gtk.Button.new_from_icon_name("user-trash-symbolic")
        remove.set_valign(Gtk.Align.CENTER)
        remove.set_tooltip_text("Remove icon")
        remove.add_css_class("flat")
        remove.connect("clicked", lambda *_: self._remove_avatar())
        icon_row.add_suffix(remove)
        group.add(icon_row)

        self.username_row = Adw.EntryRow()
        self.username_row.set_title("Username")
        self.username_row.set_text(self.settings.username)
        self.username_row.connect("changed", self._on_profile_edited)
        group.add(self.username_row)

        self.display_row = Adw.EntryRow()
        self.display_row.set_title("Display name")
        self.display_row.set_text(self.settings.display_name)
        self.display_row.connect("changed", self._on_profile_edited)
        group.add(self.display_row)

        self._refresh_avatar()
        return group

    def _refresh_avatar(self) -> None:
        self.avatar.set_text(self.settings.display_name or self.settings.username)
        self.avatar.set_custom_image(load_avatar_paintable(self.settings.avatar))

    def _choose_avatar(self) -> None:
        dialog = Gtk.FileDialog()
        dialog.set_title("Choose an icon")
        image_filter = Gtk.FileFilter()
        image_filter.set_name("Images")
        image_filter.add_mime_type("image/png")
        image_filter.add_mime_type("image/jpeg")
        image_filter.add_mime_type("image/webp")
        filters = Gio.ListStore.new(Gtk.FileFilter)
        filters.append(image_filter)
        dialog.set_filters(filters)
        dialog.open(self, None, self._on_avatar_chosen)

    def _on_avatar_chosen(self, dialog, result) -> None:
        try:
            chosen = dialog.open_finish(result)
        except GLib.Error:
            return
        try:
            self.settings.avatar = import_avatar(Path(chosen.get_path()))
        except (ValueError, OSError) as exc:
            self.add_toast(Adw.Toast.new(str(exc)))
            return
        self._saved_profile()

    def _remove_avatar(self) -> None:
        remove_avatar()
        self.settings.avatar = ""
        self._saved_profile()

    def _on_profile_edited(self, _row) -> None:
        self.settings.username = clean_username(self.username_row.get_text())
        self.settings.display_name = clean_display_name(self.display_row.get_text())
        self._saved_profile()

    def _saved_profile(self) -> None:
        save_settings(self.settings)
        self._refresh_avatar()
        self._on_profile_changed(self.settings)

    # ----------------------------------------------------------- other

    def _on_theme_selected(self, row, _pspec) -> None:
        key = THEME_ORDER[row.get_selected()]
        if key == self.settings.theme:
            return
        self.settings.theme = key
        save_settings(self.settings)
        self._on_theme_changed(key)

    def _on_client_apply(self, row) -> None:
        value = row.get_text().strip()
        if value:
            CLIENT_ID_FILE.parent.mkdir(parents=True, exist_ok=True)
            CLIENT_ID_FILE.write_text(value)
            message = "Jamendo client ID saved"
        else:
            CLIENT_ID_FILE.unlink(missing_ok=True)
            message = "Jamendo client ID removed"
        self.add_toast(Adw.Toast.new(message))
