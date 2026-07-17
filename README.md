# matugen-sync

Wallpaper-aware theme & RGB sync for Windows. Change wallpaper — everything follows.

## What It Does

Change wallpaper → matugen generates Material You palette → syncs to:

| Category | Targets |
|----------|---------|
| **RGB Hardware** | OpenRGB motherboard + DDR5 RAM + fans, MAD68 HE keyboard, Govee LEDs |
| **Discord** | Vencord custom theme |
| **Spotify** | Spicetify theme |
| **Steam** | Millennium skin |
| **Brave** | Custom theme |
| **Terminal** | Windows Terminal scheme |
| **Launcher** | Flow Launcher theme |
| **Code** | OpenCode theme |

## Quick Start

1. Install `matugen`: `cargo install matugen`
2. `pip install -r requirements.txt`
3. `matugen-sync --init`
4. Edit `~/.config/matugen-sync/config.json`
5. Run `matugen-sync <wallpaper.jpg>`

## RGB Setup

### OpenRGB (motherboard + RAM + fans)

1. Install OpenRGB 1.0rc3+ (portable to `%LOCALAPPDATA%\OpenRGB\`)
2. Run `setup_openrgb.bat` as admin — creates a scheduled task that launches OpenRGB server at logon
3. Run `matugen-sync --list-devices` to detect your hardware
4. Configure per-device calibration in `config.json` (hue_shift, saturation, lightness)

### MAD68 HE Keyboard

Connects via HID protocol (PID `0x1058`). Must be in Customization mode.

### Govee LEDs

Uses Home Assistant REST API. Configure token and entity IDs in `~/.config/govee-led.json`.

## Boot Sync

Run `matugen-sync --create-startup-link` once — creates a startup script that:
1. Waits 10s for OpenRGB server to start
2. Waits up to 30s for all devices to be detected
3. Syncs all RGB to current wallpaper colors
4. Exits

## Project Files

```
matugen_sync/
  __main__.py       CLI entry point
  colors.py         Calls matugen binary for M3 palette
  config.py         Config dataclass
  rgb.py            OpenRGB SDK + MAD68 HID
  govee.py          Home Assistant REST client
  templates.py      Jinja2 template renderer
templates/          Jinja2 templates
setup_openrgb.bat   Admin scheduled task for OpenRGB server
```

## Docs

- [SETUP.md](SETUP.md) — Full Windows installation guide
- [ARCHITECTURE.md](ARCHITECTURE.md) — Technical design decisions
