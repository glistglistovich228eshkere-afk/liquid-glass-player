"""Settings window: appearance, Jamendo account and music library."""

from __future__ import annotations

from typing import Callable

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, Gtk  # noqa: E402

from .jamendo import CLIENT_ID_FILE  # noqa: E402
from .library import CONFIG_FILE  # noqa: E402
from .settings import THEME_ORDER, THEMES, Settings, save_settings  # noqa: E402


class SettingsWindow(Adw.PreferencesWindow):
    def __init__(
        self,
        parent,
        settings: Settings,
        on_theme_changed: Callable[[str], None],
        on_choose_folder: Callable[[], None],
    ) -> None:
        super().__init__(transient_for=parent, modal=True, title="Settings")
        self.set_default_size(520, 560)
        self.settings = settings
        self._on_theme_changed = on_theme_changed

        page = Adw.PreferencesPage()

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
