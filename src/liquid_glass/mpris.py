"""MPRIS2 D-Bus service so media keys, playerctl and desktop widgets can control playback."""

from __future__ import annotations

from gi.repository import Gio, GLib

BUS_NAME = "org.mpris.MediaPlayer2.liquidglass"
OBJECT_PATH = "/org/mpris/MediaPlayer2"
ROOT_IFACE = "org.mpris.MediaPlayer2"
PLAYER_IFACE = "org.mpris.MediaPlayer2.Player"

INTROSPECTION_XML = """
<node>
  <interface name="org.mpris.MediaPlayer2">
    <method name="Raise"/>
    <method name="Quit"/>
    <property name="CanQuit" type="b" access="read"/>
    <property name="CanRaise" type="b" access="read"/>
    <property name="HasTrackList" type="b" access="read"/>
    <property name="Identity" type="s" access="read"/>
    <property name="DesktopEntry" type="s" access="read"/>
    <property name="SupportedUriSchemes" type="as" access="read"/>
    <property name="SupportedMimeTypes" type="as" access="read"/>
  </interface>
  <interface name="org.mpris.MediaPlayer2.Player">
    <method name="Next"/>
    <method name="Previous"/>
    <method name="Pause"/>
    <method name="PlayPause"/>
    <method name="Stop"/>
    <method name="Play"/>
    <method name="Seek">
      <arg direction="in" name="Offset" type="x"/>
    </method>
    <method name="SetPosition">
      <arg direction="in" name="TrackId" type="o"/>
      <arg direction="in" name="Position" type="x"/>
    </method>
    <property name="PlaybackStatus" type="s" access="read"/>
    <property name="Rate" type="d" access="read"/>
    <property name="Metadata" type="a{sv}" access="read"/>
    <property name="Volume" type="d" access="readwrite"/>
    <property name="Position" type="x" access="read"/>
    <property name="CanGoNext" type="b" access="read"/>
    <property name="CanGoPrevious" type="b" access="read"/>
    <property name="CanPlay" type="b" access="read"/>
    <property name="CanPause" type="b" access="read"/>
    <property name="CanSeek" type="b" access="read"/>
    <property name="CanControl" type="b" access="read"/>
  </interface>
</node>
"""


class MprisService:
    def __init__(self, app, engine) -> None:
        self._app = app
        self._engine = engine
        self._conn: Gio.DBusConnection | None = None
        self._info = Gio.DBusNodeInfo.new_for_xml(INTROSPECTION_XML)

        Gio.bus_own_name(
            Gio.BusType.SESSION,
            BUS_NAME,
            Gio.BusNameOwnerFlags.NONE,
            self._on_bus_acquired,
            None,
            None,
        )
        engine.on("state", self._on_state)
        engine.on("track-changed", self._on_track)

    # ----------------------------------------------------------- registration

    def _on_bus_acquired(self, connection, _name) -> None:
        self._conn = connection
        for iface_name in (ROOT_IFACE, PLAYER_IFACE):
            iface = self._info.lookup_interface(iface_name)
            connection.register_object(
                OBJECT_PATH,
                iface,
                self._on_method_call,
                self._on_get_property,
                self._on_set_property,
            )

    # ------------------------------------------------------------- callbacks

    def _on_method_call(self, _conn, _sender, _path, iface, method, params, invocation):
        engine = self._engine
        if iface == ROOT_IFACE:
            if method == "Raise":
                self._app.activate()
            elif method == "Quit":
                self._app.quit()
        else:
            if method == "Play":
                engine.play()
            elif method == "Pause":
                engine.pause()
            elif method == "PlayPause":
                engine.play_pause()
            elif method == "Stop":
                engine.stop()
            elif method == "Next":
                engine.next()
            elif method == "Previous":
                engine.previous()
            elif method == "Seek":
                offset_us = params.unpack()[0]
                engine.seek_relative(offset_us * 1000)
            elif method == "SetPosition":
                _track_id, position_us = params.unpack()
                engine.seek(position_us * 1000)
        invocation.return_value(None)

    def _on_get_property(self, _conn, _sender, _path, iface, prop):
        return self._properties(iface).get(prop)

    def _on_set_property(self, _conn, _sender, _path, iface, prop, value):
        if iface == PLAYER_IFACE and prop == "Volume":
            self._engine.set_volume(value.unpack())
            return True
        return False

    # ------------------------------------------------------------- properties

    def _properties(self, iface: str) -> dict[str, GLib.Variant]:
        if iface == ROOT_IFACE:
            return {
                "CanQuit": GLib.Variant("b", True),
                "CanRaise": GLib.Variant("b", True),
                "HasTrackList": GLib.Variant("b", False),
                "Identity": GLib.Variant("s", "Liquid Glass"),
                "DesktopEntry": GLib.Variant("s", "liquid-glass"),
                "SupportedUriSchemes": GLib.Variant("as", ["file"]),
                "SupportedMimeTypes": GLib.Variant(
                    "as",
                    [
                        "audio/flac",
                        "audio/mpeg",
                        "audio/ogg",
                        "audio/opus",
                        "audio/x-wav",
                    ],
                ),
            }

        engine = self._engine
        has_tracks = bool(engine.playlist)
        return {
            "PlaybackStatus": GLib.Variant("s", engine.playback_status()),
            "Rate": GLib.Variant("d", 1.0),
            "Metadata": self._metadata(),
            "Volume": GLib.Variant("d", engine.volume),
            "Position": GLib.Variant("x", engine.position_ns() // 1000),
            "CanGoNext": GLib.Variant("b", engine.index + 1 < len(engine.playlist)),
            "CanGoPrevious": GLib.Variant("b", has_tracks),
            "CanPlay": GLib.Variant("b", has_tracks),
            "CanPause": GLib.Variant("b", has_tracks),
            "CanSeek": GLib.Variant("b", has_tracks),
            "CanControl": GLib.Variant("b", True),
        }

    def _metadata(self) -> GLib.Variant:
        track = self._engine.current
        if track is None:
            return GLib.Variant("a{sv}", {})
        return GLib.Variant(
            "a{sv}",
            {
                "mpris:trackid": GLib.Variant(
                    "o", f"/org/mpris/MediaPlayer2/Track/{self._engine.index + 1}"
                ),
                "mpris:length": GLib.Variant("x", self._engine.duration_ns() // 1000),
                "xesam:title": GLib.Variant("s", track.title),
                "xesam:artist": GLib.Variant("as", [track.artist]),
                "xesam:album": GLib.Variant("s", track.album),
                "xesam:trackNumber": GLib.Variant("i", track.number),
                "xesam:url": GLib.Variant("s", track.uri),
            },
        )

    # --------------------------------------------------------- notifications

    def _on_state(self, status: str) -> None:
        self._changed(PLAYER_IFACE, {"PlaybackStatus": GLib.Variant("s", status)})

    def _on_track(self, _track) -> None:
        self._changed(PLAYER_IFACE, {"Metadata": self._metadata()})

    def _changed(self, iface: str, changed: dict) -> None:
        if self._conn is None:
            return
        self._conn.emit_signal(
            None,
            OBJECT_PATH,
            "org.freedesktop.DBus.Properties",
            "PropertiesChanged",
            GLib.Variant("(sa{sv}as)", (iface, changed, [])),
        )
