"""Audio engine built on GStreamer playbin.

Handles gapless playback, the 10-band equalizer, ReplayGain-based volume
normalization, and the spectrum analyzer that feeds the visualizer.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Callable

import gi

gi.require_version("Gst", "1.0")
from gi.repository import GLib, Gst  # noqa: E402

from .library import Track  # noqa: E402

Gst.init(None)

NS_PER_SECOND = 1_000_000_000
SPECTRUM_BANDS = 32
EQ_MIN_DB = -24.0
EQ_MAX_DB = 12.0

# Audio filter chain applied by playbin:
#   ReplayGain normalization -> limiter -> 10-band EQ -> spectrum analyzer.
AUDIO_FILTER = (
    "rgvolume ! rglimiter ! audioconvert ! "
    "equalizer-10bands name=eq ! audioconvert ! "
    f"spectrum name=spectrum bands={SPECTRUM_BANDS} threshold=-80 "
    "interval=33000000 post-messages=true ! audioconvert"
)

Listener = Callable[..., None]


class Engine:
    """Playback controller. Events are delivered on the GLib main loop.

    Events:
        track-changed(track: Track)
        state(status: str)          -- "Playing", "Paused" or "Stopped"
        spectrum(magnitudes: list)  -- dB values per band, roughly -80..0
        error(message: str)
    """

    def __init__(self) -> None:
        self._listeners: dict[str, list[Listener]] = defaultdict(list)
        self.playlist: list[Track] = []
        self.index = -1
        self.volume = 0.8
        self._state = Gst.State.NULL

        self.player = Gst.ElementFactory.make("playbin", "player")
        if self.player is None:
            raise RuntimeError("GStreamer 'playbin' element is missing; install gst-plugins-base.")

        audio_filter = Gst.parse_bin_from_description(AUDIO_FILTER, True)
        self._eq = audio_filter.get_by_name("eq")
        self.player.set_property("audio-filter", audio_filter)
        self.player.set_property("volume", self.volume)
        # Fires from the streaming thread shortly before the current stream ends.
        # Setting the next URI here is what makes playback gapless.
        self.player.connect("about-to-finish", self._on_about_to_finish)

        bus = self.player.get_bus()
        bus.add_signal_watch()
        bus.connect("message", self._on_message)

    # ------------------------------------------------------------------ events

    def on(self, event: str, callback: Listener) -> None:
        self._listeners[event].append(callback)

    def _emit(self, event: str, *args) -> None:
        # GLib.idle_add is thread-safe, so this also works from the streaming thread.
        GLib.idle_add(self._dispatch, event, args)

    def _dispatch(self, event: str, args: tuple) -> bool:
        for callback in list(self._listeners.get(event, [])):
            callback(*args)
        return GLib.SOURCE_REMOVE

    # ------------------------------------------------------------------ queue

    @property
    def current(self) -> Track | None:
        if 0 <= self.index < len(self.playlist):
            return self.playlist[self.index]
        return None

    def set_playlist(self, tracks: list[Track]) -> None:
        self.playlist = list(tracks)
        self.index = -1

    def play_index(self, index: int) -> None:
        if not 0 <= index < len(self.playlist):
            return
        track = self.playlist[index]
        self.index = index
        self.player.set_state(Gst.State.NULL)
        self.player.set_property("uri", track.uri)
        self.player.set_state(Gst.State.PLAYING)
        self._emit("track-changed", track)

    def _on_about_to_finish(self, player) -> None:
        next_index = self.index + 1
        if 0 <= next_index < len(self.playlist):
            track = self.playlist[next_index]
            self.index = next_index
            player.set_property("uri", track.uri)
            self._emit("track-changed", track)

    # ------------------------------------------------------------ transport

    def play(self) -> None:
        if self.current is None:
            if self.playlist:
                self.play_index(0)
            return
        if self._state != Gst.State.PLAYING:
            self.player.set_state(Gst.State.PLAYING)

    def pause(self) -> None:
        if self.current is not None:
            self.player.set_state(Gst.State.PAUSED)

    def play_pause(self) -> None:
        if self._state == Gst.State.PLAYING:
            self.pause()
        else:
            self.play()

    def stop(self) -> None:
        self.player.set_state(Gst.State.NULL)

    def next(self) -> None:
        if self.index + 1 < len(self.playlist):
            self.play_index(self.index + 1)
        else:
            self.stop()

    def previous(self) -> None:
        # Restart the track if we're a few seconds in, otherwise go back one.
        if self.index <= 0 or self.position_ns() > 3 * NS_PER_SECOND:
            self.seek(0)
        else:
            self.play_index(self.index - 1)

    def seek(self, position_ns: int) -> None:
        if self.current is None:
            return
        self.player.seek_simple(
            Gst.Format.TIME,
            Gst.SeekFlags.FLUSH | Gst.SeekFlags.KEY_UNIT,
            max(0, int(position_ns)),
        )

    def seek_relative(self, delta_ns: int) -> None:
        self.seek(self.position_ns() + delta_ns)

    def position_ns(self) -> int:
        ok, position = self.player.query_position(Gst.Format.TIME)
        return position if ok and position > 0 else 0

    def duration_ns(self) -> int:
        ok, duration = self.player.query_duration(Gst.Format.TIME)
        return duration if ok and duration > 0 else 0

    def playback_status(self) -> str:
        if self._state == Gst.State.PLAYING:
            return "Playing"
        if self._state == Gst.State.PAUSED:
            return "Paused"
        return "Stopped"

    # ------------------------------------------------------------- audio

    def set_volume(self, volume: float) -> None:
        self.volume = max(0.0, min(1.0, float(volume)))
        self.player.set_property("volume", self.volume)

    def set_eq_band(self, band: int, gain_db: float) -> None:
        if self._eq is None or not 0 <= band < 10:
            return
        gain = max(EQ_MIN_DB, min(EQ_MAX_DB, float(gain_db)))
        self._eq.set_property(f"band{band}", gain)

    # ------------------------------------------------------------ bus

    def _on_message(self, _bus, message) -> None:
        kind = message.type

        if kind == Gst.MessageType.EOS:
            self.stop()

        elif kind == Gst.MessageType.ERROR:
            error, _debug = message.parse_error()
            self._emit("error", error.message)
            self.stop()

        elif kind == Gst.MessageType.STATE_CHANGED and message.src == self.player:
            _old, new, _pending = message.parse_state_changed()
            if new != self._state:
                self._state = new
                self._emit("state", self.playback_status())

        elif kind == Gst.MessageType.ELEMENT:
            structure = message.get_structure()
            if structure is not None and structure.get_name() == "spectrum":
                magnitudes = structure.get_value("magnitude")
                self._emit("spectrum", list(magnitudes))
