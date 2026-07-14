# Linux Setup

## Requirements

- `matugen` (AUR: `matugen-bin` or `cargo install matugen`)
- `skwd-wall` — wallpaper daemon that triggers matugen on change
- `OpenRGB` — server running (`openrgb --server`)
- `jq` — JSON parsing in shell scripts
- Python `hidapi` (`pip install hidapi`) — MAD68 keyboard
- udev rule for MAD68 write access

## Files

| File | Purpose |
|------|---------|
| `scripts/rgb-sync.sh` | Reads colors.json, drives OpenRGB via CLI |
| `scripts/mad68-rgb.py` | MAD68 HID protocol (32 bytes, no report ID) |
| `templates/config.toml.example` | Full matugen config template |
| `templates/skwd-colors.json` | Matugen template → M3 hex palette |

## Setup Steps

### 1. matugen config

Merge `templates/config.toml.example` into `~/.config/matugen/config.toml`.
This defines 16+ templates (kitty, hyprland, fuzzel, Steam, Vencord, Brave, GTK, etc.)
and a post_processing hook that calls `wall-sync.sh`.

### 2. Templates

Copy the template files from this repo's `templates/` (or symlink from your Dotfiles)
to `~/.config/matugen/templates/`. These are the actual Jinja-like template files
that matugen renders with M3 color values.

### 3. Scripts

```bash
cp scripts/rgb-sync.sh ~/.local/bin/
cp scripts/mad68-rgb.py ~/.local/bin/
```

Make sure `~/.local/bin` is in your PATH.

### 4. MAD68 udev rule

Create `/etc/udev/rules.d/99-mad68.rules`:

```
SUBSYSTEM=="hidraw", ATTRS{idVendor}=="373b", ATTRS{idProduct}=="1058", MODE="0660", GROUP="plugdev"
```

Then reload: `sudo udevadm control --reload-rules && sudo udevadm trigger`

### 5. OpenRGB

Ensure OpenRGB server is running at startup:
- Systemd user service or autostart entry
- `openrgb --server` (no admin needed on Linux for SMBus access)

### 6. Test

```bash
skwd wall toggle
```

Or manually:
```bash
matugen image ~/wallpaper.jpg
~/.local/bin/rgb-sync.sh
```

## Per-Device Calibration

In `rgb-sync.sh`, saturation and lightness are tuned per device:

- **Fans (device 2):** S=0.80, L=0.35 (accent hue, no shift)
- **RAM (device 0,1):** S=0.90, L=0.30, hue -20° (compensates ENE yellow tint)
- **Brightness:** 50 on all devices

## MAD68 Protocol (Linux)

32 bytes, no report ID prefix:

```
[7, 65, 2, 0, 0x96, R, G, B, 0xB1, 0×23 zeros]
```

Keyboard PID `0x1058`, interface 1. Must be in Customization mode.

## Flow

```
skwd-wall changes wallpaper
  → matugen renders 16+ templates via config.toml
    → writes colors to each app's config
    → runs post_processing: wall-sync.sh
      ├─ updates fastfetch colors + ACCELA.conf
      └─ updates ~/.cache/skwd-wall/colors.json
        → rgb-sync.sh (OpenRGB CLI + mad68-rgb.py)
```

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| Keyboard not responding | Check `sudo cat /sys/kernel/debug/hid/*/rdesc` for device path |
| RGB stuck on old color | `systemctl --user restart skwd-daemon` then toggle wallpaper |
| OpenRGB no devices | Check `openrgb --server` is running |
| colors.json stale | post_processing ran before matugen finished — already fixed in config |
