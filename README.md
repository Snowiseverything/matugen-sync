# Matugen Sync

Wallpaper-aware theme & RGB sync for Desktop workstation. One wallpaper change → everything follows.

## What It Does

Change wallpaper via `skwd-wall` → matugen generates Material You palette → applies to:

| Category | Targets |
|----------|---------|
| **RGB Hardware** | OpenRGB fans (device 2), OpenRGB RAM (device 0,1), MAD68 HE keyboard |
| **Terminal** | kitty, starship prompt, fastfetch |
| **Shell** | hyprland colors, fuzzel launcher, swaync notifications |
| **Desktop** | caelestia lockscreen/sidebar, GTK3/4, Brave browser |
| **Apps** | Steam + Millennium, Spotify (spicetify), Discord (Vencord), OpenCode |
| **Achievements** | ACCELA (Steam achievement manager) accent color |

## Flow

```
Wallpaper change
  → skwd-wall triggers matugen
    → matugen renders 16+ templates (config.toml)
      → writes colors to each app's config
      → runs post_processing: wall-sync.sh
        ├─ updates fastfetch colors
        ├─ updates ACCELA.conf accent
        └─ updates ~/.cache/skwd-wall/colors.json
          → rgb-sync.sh (via matugen post_processing)
            ├─ openrgb -- fans @ S=0.80 L=0.35, RAM @ hue-20° S=0.90 L=0.30
            └─ mad68-rgb.py → MAD68 HE keyboard (HID protocol)
```

## Files

```
scripts/
├── rgb-sync.sh        # Reads colors.json, drives OpenRGB + MAD68
└── mad68-rgb.py       # MAD68 HE keyboard RGB (32-byte HID, PID 0x1058)
templates/
├── skwd-colors.json   # Matugen template → colors.json (M3 hex palette)
└── config.toml.example # Full 16-template matugen config with post_processing
```

## Hardware Details

### OpenRGB (Fans + RAM)
- **Fans (device 2):** accent hue, S=0.80 L=0.35
- **RAM (device 0,1):** hue -20° (compensates ENE controller yellow tint), S=0.90 L=0.30
- Brightness 50 on all devices
- Single `openrgb` call per device (~1.4s total)

### MAD68 HE Keyboard
- PID `0x1058`, uses hub.f.gg 32-byte HID protocol
- Report format: `[7, 65, 2, 0, 0x96, R, G, B, 0xB1, 0×23 zeros]`
- Requires udev rule for hidraw write access
- Keyboard must be in Customization mode

## Requirements

- `matugen` (AUR: matugen-bin) — Material You color generator
- `skwd-wall` — wallpaper picker daemon (triggers matugen on change)
- `OpenRGB` server running (for fans/RAM)
- Python `hidapi` (`pip install hidapi`) — MAD68 keyboard
- udev rule at `/etc/udev/rules.d/99-mad68.rules` — MAD68 write access
- `jq` — colors.json parsing in rgb-sync.sh

## Setup

1. **matugen config:** merge `templates/config.toml.example` into `~/.config/matugen/config.toml`
2. **Templates:** copy `templates/skwd-colors.json` to `~/.config/matugen/templates/` (or symlink from Dotfiles)
3. **Scripts:** copy `scripts/rgb-sync.sh` and `scripts/mad68-rgb.py` to `~/.local/bin/`
4. **UDEV rule:** create `/etc/udev/rules.d/99-mad68.rules`
5. **Keyboard mode:** set MAD68 to Customization mode before RGB writes
6. **Test:** `skwd wall toggle` → everything should update

## Per-Device RGB Calibration

Hue, saturation, and lightness calibrated per device in `rgb-sync.sh` to account for:
- ENE controller yellow tint on RAM sticks (hue -20°)
- Fan LED color accuracy (direct accent hue)
- All at 50% brightness for eye comfort

## MAD68 Protocol Reference

```
Offset  Value  Description
0       7      Header byte
1       65     Report ID
2       2      Sub-command
3       0      Reserved
4       0x96   Mode (static)
5       R      Red
6       G      Green
7       B      Blue
8       0xB1   End marker
9-31    0      Padding (23 bytes)
```

Total 32 bytes. Keyboard PID `0x1058` (HE version). Interface 1 for HID.

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| Keyboard not responding | Check `sudo cat /sys/kernel/debug/hid/*/rdesc` for device path |
| RGB stuck on old color | `systemctl --user restart skwd-daemon` then toggle wallpaper |
| matugen not running | `matugen image ~/wallpaper.jpg` to test manually |
| OpenRGB no devices | Check `openrgb --server` is running, devices in GUI |
| colors.json stale | rgb-sync ran before matugen finished — moved post_processing to matugen config |

## See Also

- `~/Dotfiles/.opencode/` — Desktop memory + agent config (separate repo: snow-memory)
- `~/Dotfiles/matugen/` — All 16+ template files
- `~/Dotfiles/scripts/wall-sync.sh` — Post-processing orchestrator
