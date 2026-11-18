"""Main window: library list, online search, now-playing panel, visualizer, EQ and mini mode."""

from __future__ import annotations

import threading
from pathlib import Path

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, Gdk, GdkPixbuf, GLib, Gtk, Pango  # noqa: E402

from .engine import SPECTRUM_BANDS, Engine  # noqa: E402
from .jamendo import JamendoError, fetch_bytes, load_client_id, search_tracks  # noqa: E402
from .library import CONFIG_FILE, Track, extract_art, load_online, save_online, scan  # noqa: E402

EQ_LABELS = ["29", "59", "119", "237", "474", "947", "1.9k", "3.8k", "7.5k", "15k"]
DEFAULT_SIZE = (980, 640)
MINI_SIZE = (420, 260)


def fmt_time(ns: int) -> str:
    seconds = max(0, ns) // 1_000_000_000
    return f"{seconds // 60}:{seconds % 60:02d}"


def make_art_texture(data: bytes | None, size: int = 168):
    """Scale embedded art and desaturate it to match the monochrome theme."""
    if not data:
        return None
    try:
        loader = GdkPixbuf.PixbufLoader()
        loader.write(data)
        loader.close()
        pixbuf = loader.get_pixbuf()
    except GLib.Error:
        return None
    if pixbuf is None:
        return None
    pixbuf = pixbuf.scale_simple(size, size, GdkPixbuf.InterpType.BILINEAR)
    mono = pixbuf.copy()
    pixbuf.saturate_and_pixelate(mono, 0.0, False)
    return Gdk.Texture.new_for_pixbuf(mono)


class Visualizer(Gtk.DrawingArea):
    """Monochrome spectrum bars with a damped spring for each band."""

    STIFFNESS = 0.22
    DAMPING = 0.55

    def __init__(self) -> None:
        super().__init__()
        self.set_content_height(96)
        self.set_hexpand(True)
        self.targets = [0.0] * SPECTRUM_BANDS
        self.bars = [0.0] * SPECTRUM_BANDS
        self.velocity = [0.0] * SPECTRUM_BANDS
        self.set_draw_func(self._draw)
        self.add_tick_callback(self._tick)

    def set_magnitudes(self, magnitudes: list) -> None:
        if not magnitudes:
            self.targets = [0.0] * SPECTRUM_BANDS
            return
        self.targets = [max(0.0, min(1.0, (db + 80.0) / 80.0)) for db in magnitudes]

    def _tick(self, _widget, _clock) -> bool:
        for i in range(len(self.bars)):
            target = self.targets[i] if i < len(self.targets) else 0.0
            self.velocity[i] = self.velocity[i] * self.DAMPING + (target - self.bars[i]) * self.STIFFNESS
            self.bars[i] = max(0.0, min(1.0, self.bars[i] + self.velocity[i]))
        self.queue_draw()
        return GLib.SOURCE_CONTINUE

    def _draw(self, _area, cr, width, height) -> None:
        n = len(self.bars)
        gap = 3
        bar_width = max(1.0, (width - gap * (n - 1)) / n)
        for i, level in enumerate(self.bars):
            bar_height = max(2.0, level * height)
            x = i * (bar_width + gap)
            cr.set_source_rgba(1, 1, 1, 0.28 + 0.72 * level)
            cr.rectangle(x, height - bar_height, bar_width, bar_height)
            cr.fill()


class MainWindow(Adw.ApplicationWindow):
    def __init__(self, app, engine: Engine) -> None:
        super().__init__(application=app, title="Liquid Glass")
        self.set_default_size(*DEFAULT_SIZE)
        self.engine = engine
        self.online_tracks: list[Track] = load_online()
        self.tracks: list[Track] = list(self.online_tracks)
        self.visible: list[Track] = []
        self.online_results: list[Track] = []
        self.online_mode = False
        self.add_css_class("glass-window")

        self._build_ui()

        engine.on("track-changed", self._on_track)
        engine.on("state", self._on_state)
        engine.on("spectrum", self.viz.set_magnitudes)
        engine.on("error", lambda message: self.toast(f"Playback error: {message}"))
        GLib.timeout_add(250, self._tick_position)
        self._apply_filter()

    # ------------------------------------------------------------------ build

    def _build_ui(self) -> None:
        self.header = Adw.HeaderBar()

        open_btn = self._glass_button("folder-open-symbolic", "Add music folder", self._on_open_clicked)
        self.header.pack_start(open_btn)

        self.search = Gtk.SearchEntry(placeholder_text="Search your library")
        self.search.set_hexpand(True)
        self.search.connect("search-changed", self._on_search_changed)
        self.search.connect("activate", lambda *_: self._on_search_activate())
        self.header.set_title_widget(self.search)

        self.online_btn = Gtk.ToggleButton(label="Jamendo")
        self.online_btn.set_tooltip_text("Search Jamendo online (type, then press Enter)")
        self.online_btn.add_css_class("glass-button")
        self.online_btn.connect("toggled", lambda b: self.set_online_mode(b.get_active()))
        self.header.pack_end(self.online_btn)

        self.mini_btn = Gtk.ToggleButton()
        self.mini_btn.set_icon_name("view-restore-symbolic")
        self.mini_btn.set_tooltip_text("Mini player (Ctrl+M)")
        self.mini_btn.add_css_class("glass-button")
        self.mini_btn.connect("toggled", lambda b: self.set_mini(b.get_active()))
        self.header.pack_end(self.mini_btn)

        self.listbox = Gtk.ListBox()
        self.listbox.set_selection_mode(Gtk.SelectionMode.SINGLE)
        self.listbox.add_css_class("track-list")
        self.listbox.connect("row-activated", self._on_row_activated)

        self.scroller = Gtk.ScrolledWindow()
        self.scroller.set_vexpand(True)
        self.scroller.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        self.scroller.set_child(self.listbox)

        content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        content.append(self.scroller)
        content.append(self._build_panel())

        view = Adw.ToolbarView()
        view.add_top_bar(self.header)
        view.set_content(content)

        self.toasts = Adw.ToastOverlay()
        self.toasts.set_child(view)
        self.set_content(self.toasts)

    def _build_panel(self) -> Gtk.Widget:
        panel = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=20)
        panel.add_css_class("glass-panel")

        self.art = Gtk.Picture()
        self.art.set_content_fit(Gtk.ContentFit.COVER)
        self.art.set_size_request(168, 168)
        self.art.add_css_class("art")
        panel.append(self.art)

        right = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        right.set_hexpand(True)
        right.set_valign(Gtk.Align.CENTER)

        self.title_lbl = Gtk.Label(label="Nothing playing")
        self.title_lbl.set_xalign(0)
        self.title_lbl.set_ellipsize(Pango.EllipsizeMode.END)
        self.title_lbl.add_css_class("np-title")

        self.meta_lbl = Gtk.Label(label="Add a music folder or search Jamendo to begin")
        self.meta_lbl.set_xalign(0)
        self.meta_lbl.set_ellipsize(Pango.EllipsizeMode.END)
        self.meta_lbl.add_css_class("np-artist")

        self.viz = Visualizer()
        self.viz.add_css_class("viz")

        self.seek = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 0, 1000, 1)
        self.seek.set_draw_value(False)
        self.seek.set_hexpand(True)
        self.seek.add_css_class("seek")
        self.seek.connect("change-value", self._on_seek)

        self.time_lbl = Gtk.Label(label="0:00 / 0:00")
        self.time_lbl.add_css_class("dim")

        seek_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        seek_row.append(self.seek)
        seek_row.append(self.time_lbl)

        self.play_btn = self._glass_button(
            "media-playback-start-symbolic", "Play / Pause", lambda *_: self.engine.play_pause(), primary=True
        )
        controls = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        controls.append(
            self._glass_button("media-skip-backward-symbolic", "Previous (Ctrl+Left)", lambda *_: self.engine.previous())
        )
        controls.append(self.play_btn)
        controls.append(
            self._glass_button("media-skip-forward-symbolic", "Next (Ctrl+Right)", lambda *_: self.engine.next())
        )

        spacer = Gtk.Box()
        spacer.set_hexpand(True)
        controls.append(spacer)

        controls.append(Gtk.Image.new_from_icon_name("audio-volume-high-symbolic"))
        self.volume = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 0, 1, 0.01)
        self.volume.set_draw_value(False)
        self.volume.set_size_request(120, -1)
        self.volume.add_css_class("seek")
        self.volume.set_value(self.engine.volume)
        self.volume.connect("value-changed", lambda s: self.engine.set_volume(s.get_value()))
        controls.append(self.volume)

        eq_btn = Gtk.MenuButton()
        eq_btn.set_icon_name("multimedia-equalizer-symbolic")
        eq_btn.set_tooltip_text("Equalizer")
        eq_btn.add_css_class("glass-button")
        eq_btn.set_popover(self._build_eq())
        controls.append(eq_btn)

        right.append(self.title_lbl)
        right.append(self.meta_lbl)
        right.append(self.viz)
        right.append(seek_row)
        right.append(controls)
        panel.append(right)
        return panel

    def _build_eq(self) -> Gtk.Popover:
        popover = Gtk.Popover()
        popover.add_css_class("glass-popover")
        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        for margin_setter in (box.set_margin_top, box.set_margin_bottom, box.set_margin_start, box.set_margin_end):
            margin_setter(14)

        for index, label in enumerate(EQ_LABELS):
            column = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
            band = Gtk.Scale.new_with_range(Gtk.Orientation.VERTICAL, -12, 12, 1)
            band.set_inverted(True)
            band.set_draw_value(False)
            band.set_size_request(-1, 150)
            band.set_value(0)
            band.add_css_class("seek")
            band.connect("value-changed", lambda s, i=index: self.engine.set_eq_band(i, s.get_value()))
            caption = Gtk.Label(label=label)
            caption.add_css_class("dim")
            column.append(band)
            column.append(caption)
            box.append(column)

        popover.set_child(box)
        return popover

    @staticmethod
    def _glass_button(icon: str, tooltip: str, handler, primary: bool = False) -> Gtk.Button:
        button = Gtk.Button.new_from_icon_name(icon)
        button.set_tooltip_text(tooltip)
        button.add_css_class("glass-button")
        if primary:
            button.add_css_class("primary")
        button.connect("clicked", handler)
        return button

    # ----------------------------------------------------------- behaviour

    def toast(self, message: str) -> None:
        self.toasts.add_toast(Adw.Toast.new(message))

    def toggle_mini(self) -> None:
        self.mini_btn.set_active(not self.mini_btn.get_active())

    def set_mini(self, mini: bool) -> None:
        self.scroller.set_visible(not mini)
        if mini:
            self.add_css_class("mini")
            self.set_default_size(*MINI_SIZE)
        else:
            self.remove_css_class("mini")
            self.set_default_size(*DEFAULT_SIZE)

    def set_online_mode(self, online: bool) -> None:
        self.online_mode = online
        if online:
            self.search.set_placeholder_text("Search Jamendo, then press Enter")
            self._show(self.online_results)
        else:
            self.search.set_placeholder_text("Search your library")
            self._apply_filter()

    def _on_search_changed(self, _entry) -> None:
        if not self.online_mode:
            self._apply_filter()

    def _on_search_activate(self) -> None:
        if self.online_mode:
            self._run_online_search()

    def _run_online_search(self) -> None:
        query = self.search.get_text().strip()
        if not query:
            self.toast("Type something to search for")
            return
        client_id = load_client_id()
        if not client_id:
            self.toast("Add your Jamendo client ID to ~/.config/liquid-glass/jamendo_client_id")
            return
        self.toast("Searching Jamendo…")

        def worker() -> None:
            try:
                results = search_tracks(query, client_id)
            except JamendoError as exc:
                GLib.idle_add(self.toast, f"Jamendo search failed: {exc}")
                return
            GLib.idle_add(self._set_online_results, results)

        threading.Thread(target=worker, daemon=True).start()

    def _set_online_results(self, results: list[Track]) -> bool:
        self.online_results = results
        self.toast(f"{len(results)} results from Jamendo")
        if self.online_mode:
            self._show(results)
        return GLib.SOURCE_REMOVE

    def _on_open_clicked(self, _button) -> None:
        dialog = Gtk.FileDialog()
        dialog.set_title("Choose your music folder")
        dialog.select_folder(self, None, self._on_folder_chosen)

    def _on_folder_chosen(self, dialog, result) -> None:
        try:
            folder = dialog.select_folder_finish(result)
        except GLib.Error:
            return
        self.load_library(folder.get_path())

    def load_library(self, path: str) -> None:
        CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
        CONFIG_FILE.write_text(path)
        self.toast("Scanning library…")

        def worker() -> None:
            tracks = scan(Path(path))
            GLib.idle_add(self._set_tracks, tracks)

        threading.Thread(target=worker, daemon=True).start()

    def _set_tracks(self, tracks: list[Track]) -> bool:
        self.tracks = list(tracks) + list(self.online_tracks)
        self.toast(f"{len(tracks)} tracks loaded")
        if not self.online_mode:
            self._apply_filter()
        return GLib.SOURCE_REMOVE

    def _apply_filter(self) -> None:
        words = self.search.get_text().lower().split()
        filtered = [t for t in self.tracks if all(w in t.haystack for w in words)]
        self._show(filtered)

    def _show(self, tracks: list[Track]) -> None:
        """Rebuild the list with ``tracks``; this list is also the playback queue."""
        self.visible = list(tracks)
        child = self.listbox.get_first_child()
        while child is not None:
            following = child.get_next_sibling()
            self.listbox.remove(child)
            child = following

        for track in self.visible:
            self.listbox.append(self._make_row(track))
        self._highlight_current()

    def _in_library(self, track: Track) -> bool:
        return track in self.tracks

    def _make_row(self, track: Track) -> Gtk.ListBoxRow:
        row = Gtk.ListBoxRow()
        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=14)
        box.set_margin_top(6)
        box.set_margin_bottom(6)
        box.set_margin_start(6)
        box.set_margin_end(6)

        number = Gtk.Label(label=f"{track.number:02d}" if track.number else "–")
        number.add_css_class("dim")
        number.set_width_chars(3)

        text = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        text.set_hexpand(True)
        title = Gtk.Label(label=track.title)
        title.set_xalign(0)
        title.set_ellipsize(Pango.EllipsizeMode.END)
        title.add_css_class("track-title")
        subtitle = Gtk.Label(label=f"{track.artist} · {track.album}")
        subtitle.set_xalign(0)
        subtitle.set_ellipsize(Pango.EllipsizeMode.END)
        subtitle.add_css_class("dim")
        text.append(title)
        text.append(subtitle)

        box.append(number)
        box.append(text)

        if self.online_mode:
            if self._in_library(track):
                saved = Gtk.Label(label="In library")
                saved.add_css_class("dim")
                box.append(saved)
            else:
                add = Gtk.Button.new_from_icon_name("list-add-symbolic")
                add.set_tooltip_text("Add to library")
                add.add_css_class("glass-button")
                add.connect("clicked", lambda _b, t=track: self._add_to_library(t))
                box.append(add)

        row.set_child(box)
        return row

    def _add_to_library(self, track: Track) -> None:
        if self._in_library(track):
            return
        self.online_tracks.append(track)
        self.tracks.append(track)
        save_online(self.online_tracks)
        self.toast(f"Added {track.title} to your library")
        self._show(self.visible)

    def _on_row_activated(self, _listbox, row: Gtk.ListBoxRow) -> None:
        index = row.get_index()
        if not 0 <= index < len(self.visible):
            return
        self.engine.set_playlist(self.visible)
        self.engine.play_index(index)

    def _highlight_current(self) -> None:
        current = self.engine.current
        row = self.listbox.get_first_child()
        index = 0
        while row is not None:
            is_current = current is not None and index < len(self.visible) and self.visible[index] == current
            if is_current:
                row.add_css_class("now-playing")
            else:
                row.remove_css_class("now-playing")
            row = row.get_next_sibling()
            index += 1

    # ------------------------------------------------------------ engine events

    def _on_track(self, track: Track) -> None:
        self.title_lbl.set_label(track.title)
        self.meta_lbl.set_label(f"{track.artist} — {track.album}")
        self.set_title(f"{track.title} — Liquid Glass")
        if track.is_remote:
            self.art.set_paintable(None)
            if track.art_url:
                self._load_remote_art(track)
        else:
            self.art.set_paintable(make_art_texture(extract_art(Path(track.path))))
        self._highlight_current()

    def _load_remote_art(self, track: Track) -> None:
        def worker() -> None:
            try:
                data = fetch_bytes(track.art_url)
            except Exception:
                return
            GLib.idle_add(self._apply_art, track, data)

        threading.Thread(target=worker, daemon=True).start()

    def _apply_art(self, track: Track, data: bytes) -> bool:
        if self.engine.current == track:
            self.art.set_paintable(make_art_texture(data))
        return GLib.SOURCE_REMOVE

    def _on_state(self, status: str) -> None:
        playing = status == "Playing"
        self.play_btn.set_icon_name("media-playback-pause-symbolic" if playing else "media-playback-start-symbolic")
        if not playing:
            self.viz.set_magnitudes([])

    def _tick_position(self) -> bool:
        if self.engine.current is None:
            return GLib.SOURCE_CONTINUE
        position = self.engine.position_ns()
        duration = self.engine.duration_ns()
        if duration > 0:
            self.seek.set_value(position * 1000 / duration)
        self.time_lbl.set_label(f"{fmt_time(position)} / {fmt_time(duration)}")
        return GLib.SOURCE_CONTINUE

    def _on_seek(self, _scale, _scroll, value: float) -> bool:
        duration = self.engine.duration_ns()
        if duration > 0:
            self.engine.seek(int(duration * value / 1000))
        return False
