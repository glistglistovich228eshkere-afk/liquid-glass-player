# Liquid Glass

A minimalist, monochrome music player for Linux. Obsidian-black glass panels, hairline white borders, crisp typography, and a spring-driven spectrum visualizer, built natively with **GTK4 + Libadwaita** and **GStreamer**.

```
┌──────────────────────────────────────────────────────────────────────────┐
│ [📂]     ( Search artist, album, title…            )            [◱ mini]│
├──────────────────────────────────────────────────────────────────────────┤
│  01  Teardrop                              Massive Attack · Mezzanine     │
│ ░░░░ ─────────────────────────────────────────────────────────────────── │
│  02  Angel                                 Massive Attack · Mezzanine     │
│ ▓▓▓▓ ─────────────────────────────────────────────────────────────────── │
│  03  Risingson                             Massive Attack · Mezzanine     │
├──────────────────────────────────────────────────────────────────────────┤
│ ┌──────────┐  Angel                                                       │
│ │ ▓▒░▒▓▒░▓ │  Massive Attack — Mezzanine                                  │
│ │ ░▓▒▓░▒▓░ │  ▁▂▄▆█▇▅▃▂▁▂▃▅▇█▆▄▂▁▁▂▃▅▆▇▅▃▂▁   (spectrum)                  │
│ └──────────┘  1:12 ━━━━━━━━━━━━●──────────────────────── 4:58             │
│               [⏮]  [ ⏯ ]  [⏭]   🔊 ━━━━●━━   [≋ EQ]                      │
└──────────────────────────────────────────────────────────────────────────┘
```

## Features

- **Audio engine**: GStreamer `playbin` with gapless playback (FLAC, MP3, OGG/Vorbis, Opus, WAV).
- **10-band equalizer** (`equalizer-10bands`), adjustable from the EQ popover.
- **Volume normalization** via ReplayGain (`rgvolume`) plus `rglimiter` to prevent clipping. Normalization only applies to files that carry ReplayGain tags.
- **Library**: scans a folder recursively, reads artist / album / title / track number with `mutagen`, and filters live as you type. The chosen folder is remembered between launches.
- **Album art**: embedded art (ID3 APIC for MP3, FLAC pictures) is desaturated to monochrome and shown in a rounded frame.
- **Spectrum visualizer**: 32-band spectrum from GStreamer's `spectrum` element, drawn with Cairo and smoothed by a damped spring model.
- **Mini mode**: toggles a compact view that hides the track list.
- **MPRIS2 over D-Bus**: media keys, playerctl, GNOME/KDE lock-screen and media controls, and the system volume/metadata widgets all work through `org.mpris.MediaPlayer2.liquidglass`.
- **Desktop notifications** when a new track starts while the window is in the background.
- **Keyboard shortcuts** (in-app): `Ctrl+Space` play/pause, `Ctrl+Left`/`Ctrl+Right` previous/next, `Ctrl+M` mini mode, `Ctrl+Q` quit.

## Requirements

- Python 3.10+
- GTK **4.10+** (for `Gtk.FileDialog`)
- libadwaita **1.4+** (for `Adw.ToolbarView`)
- GStreamer 1.20+ with the base, good, bad (for `equalizer-10bands` / `rglimiter` in some builds), and libav plugins
- PyGObject, mutagen

## Installation

PyGObject, GTK, libadwaita and GStreamer are system libraries, so install them from your distribution first. The simplest route is a virtualenv that can see system packages.

### Arch Linux

```bash
sudo pacman -S --needed python python-gobject gtk4 libadwaita \
    gst-plugins-base gst-plugins-good gst-plugins-bad gst-libav python-mutagen git

git clone https://github.com/glistglistovich228eshkere-afk/liquid-glass-player.git
cd liquid-glass-player
python -m venv --system-site-packages .venv
.venv/bin/pip install -e .
.venv/bin/liquid-glass
```

### Ubuntu / Debian

Ubuntu 24.04+ and Debian 13+ ship GTK 4.10+ and libadwaita 1.4+, which the app needs.

```bash
sudo apt install python3-gi python3-venv git gir1.2-gtk-4.0 gir1.2-adw-1 \
    gstreamer1.0-plugins-base gstreamer1.0-plugins-good \
    gstreamer1.0-plugins-bad gstreamer1.0-libav python3-mutagen

git clone https://github.com/glistglistovich228eshkere-afk/liquid-glass-player.git
cd liquid-glass-player
python3 -m venv --system-site-packages .venv
.venv/bin/pip install -e .
.venv/bin/liquid-glass
```

### Fedora

```bash
sudo dnf install python3-gobject gtk4 libadwaita python3-mutagen git \
    gstreamer1-plugins-base gstreamer1-plugins-good \
    gstreamer1-plugins-bad-free gstreamer1-plugin-libav

git clone https://github.com/glistglistovich228eshkere-afk/liquid-glass-player.git
cd liquid-glass-player
python3 -m venv --system-site-packages .venv
.venv/bin/pip install -e .
.venv/bin/liquid-glass
```

### Desktop launcher

To add the app to your application menu:

```bash
install -Dm644 data/liquid-glass.desktop ~/.local/share/applications/liquid-glass.desktop
```

If the launcher can't find `liquid-glass`, edit the `Exec=` line to the full path inside your virtualenv.

## Usage

1. Click the folder icon in the header and pick your music folder. The library scans in the background.
2. Double-click or press Enter on a track to start playback; the queue is the currently filtered list.
3. Type in the search field to filter by artist, album, or title. Multiple words must all match.
4. Open the **≋** button to adjust the 10-band equalizer.
5. Use the **mini** toggle (or `Ctrl+M`) for a compact window.

### Media keys and external control

MPRIS is registered automatically. Try:

```bash
playerctl -p liquidglass play-pause
playerctl -p liquidglass next
```

On Wayland compositors such as Hyprland, bind media keys in your compositor config, for example `bindl = , XF86AudioPlay, exec, playerctl play-pause`.

## Design notes and limitations

- **Glass effect**: GTK4 does not blur content behind a window. The "frosted" look is built from translucent gradients, hairline highlights, and shadows. Real background blur needs your compositor: on Hyprland, add `blur` to a `windowrule` matching `class:io.github.liquidglass.Player`. KDE Plasma and GNOME have their own blur settings.
- **Global shortcuts**: Wayland does not allow applications to grab keys globally. Use your desktop's custom shortcuts together with `playerctl`, or the media keys that MPRIS already handles.
- **Gapless** works through `playbin`'s `about-to-finish` signal, so it depends on the decoder and output chain behaving well. Some MP3 files without a proper Xing header may show a short gap.
- **Library persistence** stores only the chosen folder path (`~/.config/liquid-glass/folder`). The track list is rebuilt from disk on each launch.

## Project layout

```
src/liquid_glass/
├── app.py        # Adw.Application, actions, notifications, CLI entry point
├── engine.py     # GStreamer playbin, gapless queue, EQ, spectrum, events
├── library.py    # Folder scanner, tag reading, embedded art extraction
├── mpris.py      # MPRIS2 service over Gio D-Bus
├── window.py     # Main window, now-playing panel, visualizer, mini mode
└── style.css     # Liquid Glass theme (GTK CSS)
data/
└── liquid-glass.desktop
```

## Contributing

Issues and pull requests are welcome. Please keep changes focused, and keep the visual language monochrome.

## License

MIT. See [LICENSE](LICENSE).
