# Architecture & Windows Workarounds

## Overview

This is a Windows port of the original Linux `matugen-sync` that synced Material You colors from wallpaper to RGB hardware and apps. The Linux version used shell scripts (`rgb-sync.sh`) + matugen templates. The Windows version is a full Python CLI with SDK integrations.

## Key Decisions

### Why Python instead of Shell?

- Windows lacks a native shell with the ergonomics of bash/ POSIX tools
- Python provides cross-platform HID, HTTP, and process management
- Jinja2 replaces matugen's built-in template engine (matugen templates require Linux `config.toml`)

### Why matugen binary instead of Python library?

- `material-color-utilities` (Python) produced incorrect `on_surface_variant` (`#ffffff` instead of gray)
- The Rust `matugen v4.1.0` binary produces proper Material You 3 colors
- `colors.py` calls `matugen image <path> --json hex` and parses the JSON output

## RAM RGB — The Hard Part

### The Problem

T-Force Delta RGB DDR5 sticks are detected via SMBus/I2C on the motherboard. On Windows, SMBus access requires:
1. A kernel driver (PawnIO, installed by OpenRGB)
2. **Administrator privileges** to use PawnIO

OpenRGB running without admin only sees USB-connected devices (motherboard AURA HID, keyboards, mice). The RAM is invisible.

Armoury Crate's `LightingService` also locks the SMBus exclusively, preventing OpenRGB from accessing it even with admin.

### The Fix (3 layers)

```
Layer 1: Stop LightingService       → sc stop LightingService + sc config LightingService start= disabled
Layer 2: OpenRGB 1.0rc3             → Added DetectTForceDeltaControllers() for SPD_DDR5_SDRAM (PR #80, merged Jun 3 2026)
Layer 3: Admin scheduled task       → OpenRGB --server runs as admin at logon via Task Scheduler (Highest privileges)
         └─ SDK client (no admin)  → matugen-sync connects to localhost:6742 via openrgb-python library
```

**Layer 1 — LightingService:**

Armoury Crate's `ASUS AURA SYNC lighting service` holds exclusive access to the SMBus controller. OpenRGB's PawnIO driver cannot initialize while it's running.

```
sc stop LightingService
sc config LightingService start= disabled
```

This permanently disables the service. AURA motherboard RGB still works via the USB HID interface (doesn't need SMBus).

**Layer 2 — OpenRGB 1.0rc3:**

The user had OpenRGB 1.0rc2 which used WinRing0 (deprecated) or PawnIO. Version 1.0rc3 (June 28, 2026) includes the T-Force Delta DDR5 detection patch (PR #80 from CalcProgrammer1/OpenRGB).

The patch adds `DetectTForceDeltaControllers()` which scans SMBus for ENE DRAM controllers on DDR5 modules and registers them with the correct 8-LED linear layout.

**Layer 3 — Admin scheduled task:**

Since SMBus access requires admin, we create a Windows scheduled task:

```
Name:    OpenRGB Server
Trigger: At logon (current user)
Action:  %LOCALAPPDATA%\OpenRGB\OpenRGB.exe --server --startminimized
Run with: Highest privileges (admin)
```

The server runs silently in the background. Our Python code connects via `openrgb-python` SDK client (no admin needed for the client).

### Architecture Diagram

```
┌─────────────────────────────────────────────────────────┐
│  Windows Scheduled Task (admin)                         │
│  ┌───────────────────────────────────────────────────┐  │
│  │  OpenRGB Server (--server)                        │  │
│  │  ├── PawnIO Driver → SMBus → RAM (ENE DRAM)      │  │
│  │  └── USB HID → Motherboard AURA                  │  │
│  └──────────────┬────────────────────────────────────┘  │
└─────────────────┼────────────────────────────────────────┘
                  │ TCP localhost:6742
┌─────────────────▼────────────────────────────────────────┐
│  matugen-sync (normal user)                              │
│  ├── openrgb-python → set_color(R, G, B) on all devices │
│  ├── hidapi → MAD68 keyboard (HID write)                 │
│  └── requests → Home Assistant → Govee LED strip         │
└──────────────────────────────────────────────────────────┘
```

## MAD68 Keyboard — Windows vs Linux

The MAD68 HE keyboard uses a proprietary HID protocol. The Linux version sends 32 bytes directly. On Windows, the HID API requires a **0x00 report ID prefix byte** (33 bytes total):

| Offset | Linux | Windows |
|--------|-------|---------|
| 0 | `7` | `0` (report ID) |
| 1 | `65` | `7` |
| 2 | `2` | `65` |
| ... | ... | ... |
| 31 | `0` (last byte) | `0xB1` |
| 32 | — | `0` (padding) |

This is because Windows HID desktop API expects a report ID byte even for devices that don't use numbered reports.

## Govee LED — Home Assistant API

Govee's native LAN API is unreliable and lacks brightness control. Instead, we use Home Assistant's REST API running on a Raspberry Pi 4 ("snowpi"):

```
POST http://snowpi:8123/api/services/light/turn_on
Authorization: Bearer <token>
Body: { "entity_id": "light.govee_h6102_2f48", "rgb_color": [R, G, B], "brightness": 204 }
```

Config stored in `~/.config/govee-led.json` (separate from the main config to avoid leaking tokens into git).

## App Theme Rendering

matugen templates use Jinja2 instead of matugen's built-in `config.toml` template system (Linux-only).

### Template variables

All Material You 3 colors are available as template variables:

```
{{ source }}         — Source color (wallpaper dominant)
{{ accent }}         — Accent/vibrant color
{{ primary }}        — Primary palette
{{ on_primary }}
{{ primary_container }}
{{ on_primary_container }}
{{ secondary }}
{{ on_secondary }}
{{ tertiary }}
{{ error }}          — Error/caution red
{{ on_error }}
{{ surface }}        — Background surface
{{ on_surface }}
{{ surface_variant }}
{{ on_surface_variant }}
{{ background }}
{{ on_background }}
{{ outline }}
{{ outline_variant }}
```

Available with `_dark` / `_light` suffix (e.g. `{{ surface_dark }}`, `{{ surface_light }}`).

### Custom filter: `hex_to_rgb`

```jinja
{{ primary | hex_to_rgb }}   → "123, 45, 67"
```

### Color format

All colors are 6-digit hex with `#` prefix (e.g. `#1a2b3c`). Windows Terminal requires `#rrggbb` format with `#`.

## File Layout

```
~/.config/matugen-sync/
├── config.json        # User configuration (app paths, device IDs, toggles)
├── templates/         # Jinja2 templates (copied from built-in or custom)
│   ├── vencord.css.j2
│   ├── steam.css.j2
│   ├── brave.css.j2
│   ├── spicetify.ini.j2
│   ├── opencode.json.j2
│   ├── flow_launcher.json.j2
│   └── windows_terminal.json.j2
~/.config/govee-led.json  # Govee HA credentials (gitignored)
~/.cache/matugen-sync/
├── colors.json        # Cached last palette
└── rendered/          # Rendered output files
```
