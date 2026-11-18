"""Application entry point: actions, shortcuts, notifications and window lifecycle."""

from __future__ import annotations

import sys
from pathlib import Path

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, Gdk, Gio, Gtk  # noqa: E402

from .engine import Engine  # noqa: E402
from .library import CONFIG_FILE, Track  # noqa: E402
from .mpris import MprisService  # noqa: E402
from .window import MainWindow  # noqa: E402

APP_ID = "io.github.liquidglass.Player"
STYLE_PATH = Path(__file__).with_name("style.css")


class LiquidGlassApp(Adw.Application):
    def __init__(self) -> None:
        super().__init__(application_id=APP_ID, flags=Gio.ApplicationFlags.DEFAULT_FLAGS)
        self.engine = Engine()
        self.window: MainWindow | None = None
        self.mpris: MprisService | None = None
        self.connect("startup", self._on_startup)
        self.connect("activate", self._on_activate)
        self.connect("shutdown", lambda *_: self.engine.stop())

    def _on_startup(self, _app) -> None:
        Adw.StyleManager.get_default().set_color_scheme(Adw.ColorScheme.FORCE_DARK)

        provider = Gtk.CssProvider()
        provider.load_from_path(str(STYLE_PATH))
        Gtk.StyleContext.add_provider_for_display(
            Gdk.Display.get_default(), provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )
        self._install_actions()

    def _install_actions(self) -> None:
        bindings = [
            ("play-pause", self.engine.play_pause, "<Control>space"),
            ("next-track", self.engine.next, "<Control>Right"),
            ("previous-track", self.engine.previous, "<Control>Left"),
            ("toggle-mini", self._toggle_mini, "<Control>m"),
            ("quit", self.quit, "<Control>q"),
        ]
        for name, handler, accel in bindings:
            action = Gio.SimpleAction.new(name, None)
            action.connect("activate", lambda *_args, fn=handler: fn())
            self.add_action(action)
            self.set_accels_for_action(f"app.{name}", [accel])

    def _toggle_mini(self) -> None:
        if self.window is not None:
            self.window.toggle_mini()

    def _on_activate(self, _app) -> None:
        if self.window is None:
            self.window = MainWindow(self, self.engine)
            self.mpris = MprisService(self, self.engine)
            self.engine.on("track-changed", self._notify_track)

            if CONFIG_FILE.exists():
                folder = CONFIG_FILE.read_text().strip()
                if folder and Path(folder).is_dir():
                    self.window.load_library(folder)
        self.window.present()

    def _notify_track(self, track: Track) -> None:
        if self.window is not None and self.window.is_active():
            return
        notification = Gio.Notification.new(track.title)
        notification.set_body(f"{track.artist} — {track.album}")
        notification.set_icon(Gio.ThemedIcon.new("audio-x-generic"))
        self.send_notification("now-playing", notification)


def main(argv: list[str] | None = None) -> int:
    app = LiquidGlassApp()
    return app.run(sys.argv if argv is None else argv)
