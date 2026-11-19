"""Application entry point: actions, shortcuts, themes, settings, updates and window lifecycle."""

from __future__ import annotations

import sys
import threading
from pathlib import Path

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, Gdk, Gio, GLib, Gtk  # noqa: E402

from . import __version__  # noqa: E402
from .engine import Engine  # noqa: E402
from .library import CONFIG_FILE, Track  # noqa: E402
from .mpris import MprisService  # noqa: E402
from .settings import THEMES, Settings, load_settings  # noqa: E402
from .settings_dialog import SettingsWindow  # noqa: E402
from .updater import launch_update, newer_version_available  # noqa: E402
from .window import MainWindow  # noqa: E402

APP_ID = "io.github.liquidglass.Player"
PACKAGE_DIR = Path(__file__).parent


class LiquidGlassApp(Adw.Application):
    def __init__(self) -> None:
        super().__init__(application_id=APP_ID, flags=Gio.ApplicationFlags.DEFAULT_FLAGS)
        self.engine = Engine()
        self.settings: Settings = load_settings()
        self.window: MainWindow | None = None
        self.mpris: MprisService | None = None
        self._theme_provider: Gtk.CssProvider | None = None
        self.connect("startup", self._on_startup)
        self.connect("activate", self._on_activate)
        self.connect("shutdown", lambda *_: self.engine.stop())

    def _on_startup(self, _app) -> None:
        Adw.StyleManager.get_default().set_color_scheme(Adw.ColorScheme.FORCE_DARK)
        self._apply_theme(self.settings.theme)
        self._install_actions()

    def _apply_theme(self, key: str) -> None:
        display = Gdk.Display.get_default()
        if self._theme_provider is not None:
            Gtk.StyleContext.remove_provider_for_display(display, self._theme_provider)
        provider = Gtk.CssProvider()
        provider.load_from_path(str(PACKAGE_DIR / THEMES[key][1]))
        Gtk.StyleContext.add_provider_for_display(display, provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
        self._theme_provider = provider

    def _install_actions(self) -> None:
        bindings = [
            ("play-pause", self.engine.play_pause, "<Control>space"),
            ("next-track", self.engine.next, "<Control>Right"),
            ("previous-track", self.engine.previous, "<Control>Left"),
            ("toggle-mini", self._toggle_mini, "<Control>m"),
            ("settings", self.open_settings, "<Control>comma"),
            ("quit", self.quit, "<Control>q"),
            ("update", self._start_update, None),
        ]
        for name, handler, accel in bindings:
            action = Gio.SimpleAction.new(name, None)
            action.connect("activate", lambda *_args, fn=handler: fn())
            self.add_action(action)
            if accel:
                self.set_accels_for_action(f"app.{name}", [accel])

    def _toggle_mini(self) -> None:
        if self.window is not None:
            self.window.toggle_mini()

    def open_settings(self) -> None:
        if self.window is None:
            return
        dialog = SettingsWindow(
            self.window,
            self.settings,
            self._apply_theme,
            lambda: self.window._on_open_clicked(None),
        )
        dialog.present()

    def _on_activate(self, _app) -> None:
        if self.window is None:
            self.window = MainWindow(self, self.engine)
            self.mpris = MprisService(self, self.engine)
            self.engine.on("track-changed", self._notify_track)

            if CONFIG_FILE.exists():
                folder = CONFIG_FILE.read_text().strip()
                if folder and Path(folder).is_dir():
                    self.window.load_library(folder)

            threading.Thread(target=self._check_for_update, daemon=True).start()
        self.window.present()

    def _check_for_update(self) -> None:
        version = newer_version_available()
        if version:
            GLib.idle_add(self._announce_update, version)

    def _announce_update(self, version: str) -> bool:
        if self.window is not None:
            toast = Adw.Toast.new(f"Liquid Glass {version} is available")
            toast.set_button_label("Update")
            toast.set_action_name("app.update")
            toast.set_timeout(0)
            self.window.toasts.add_toast(toast)
        return GLib.SOURCE_REMOVE

    def _start_update(self) -> None:
        if not launch_update() and self.window is not None:
            self.window.toast("No terminal found. Run liquid-glass-update in a terminal.")

    def _notify_track(self, track: Track) -> None:
        if self.window is not None and self.window.is_active():
            return
        notification = Gio.Notification.new(track.title)
        notification.set_body(f"{track.artist} — {track.album}")
        notification.set_icon(Gio.ThemedIcon.new("audio-x-generic"))
        self.send_notification("now-playing", notification)


def main(argv: list[str] | None = None) -> int:
    args = sys.argv if argv is None else argv
    if "--version" in args:
        print(f"Liquid Glass {__version__}")
        return 0
    app = LiquidGlassApp()
    return app.run(args)
