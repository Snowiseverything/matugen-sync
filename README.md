# matugen-sync

Wallpaper-aware theme & RGB sync. Change wallpaper → everything follows.

## Windows

```
Wallpaper change
  → matugen-sync --watch (or manual run)
    → matugen binary generates Material You palette
      → Jinja2 templates render for each app (Discord, Steam, Brave, etc.)
      → OpenRGB SDK → motherboard + DDR5 RAM + fans
      → HID write → MAD68 HE keyboard
      → Home Assistant API → Govee LED strip
```

## Quick Start

1. Install `matugen`: `cargo install matugen`
2. `pip install -r requirements.txt`
3. `matugen-sync --init`
4. Edit `~/.config/matugen-sync/config.json` with your app paths
5. Run `matugen-sync <wallpaper.jpg>`

See [SETUP.md](SETUP.md) for full Windows installation.

## Files

```
matugen_sync/           # Python package
  __main__.py           # CLI entry point (--watch, --list-devices, etc.)
  colors.py             # Calls matugen binary for M3 palette
  config.py             # Config dataclass (JSON ~/.config/matugen-sync/)
  rgb.py                # OpenRGB SDK client + MAD68 HID
  govee.py              # Home Assistant REST client
  templates.py          # Jinja2 template renderer
templates/              # Jinja2 templates for each app
setup_openrgb.bat       # Creates admin scheduled task for OpenRGB server
```

See [ARCHITECTURE.md](ARCHITECTURE.md) for technical details on Windows workarounds.
