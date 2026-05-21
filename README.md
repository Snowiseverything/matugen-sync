# Matugen Sync — Multi-Device RGB + Theme Sync

Syncs keyboard, fans, RAM, opencode, discord, hyprland, kitty, and more to wallpaper colors via matugen.

## Components

- **rgb-sync.sh** — Reads matugen accent from colors.json, applies to OpenRGB devices + MAD68 HE keyboard
- **mad68-rgb.py** — MAD68 HE keyboard RGB control (32-byte HID protocol, PID 0x1058)
- **skwd-colors.json** — Matugen template for wallpaper picker colors (M3 palette)
- **config.toml.example** — Full matugen config with 16+ template integrations

## Flow

```
Wallpaper change → skwd matugen integration → colors.json → rgb-sync.sh
                                                              ├─ openrgb (fans/RAM)
                                                              └─ mad68-rgb.py (keyboard)
```

## Requirements

- matugen
- skwd-wall daemon
- OpenRGB server
- Python hidapi (`pip install hidapi`)
- udev rule for MAD68 HE keyboard write access

## Setup

1. Copy templates to `~/.config/matugen/templates/`
2. Merge `config.toml.example` into `~/.config/matugen/config.toml`
3. Add udev rule: `/etc/udev/rules.d/99-mad68.rules`
4. Set keyboard to Customization mode
5. Restart skwd: `systemctl --user restart skwd-daemon`
