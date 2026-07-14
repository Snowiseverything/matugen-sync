# Windows Setup

## Prerequisites

| Dependency | Install |
|------------|---------|
| Python 3.12+ | [python.org](https://python.org) |
| Rust (for matugen) | `winget install Rust.Rustup` or [rustup.rs](https://rustup.rs) |
| OpenRGB 1.0rc3+ | Included in setup steps below |

## Step-by-Step

### 1. Install matugen (color engine)

```powershell
cargo install matugen
```

Verify: `matugen image some-wallpaper.jpg --json hex`

### 2. Install Python dependencies

```powershell
pip install -r requirements.txt
```

### 3. Initialize config

```powershell
matugen-sync --init
```

This creates `~/.config/matugen-sync/config.json` and copies built-in templates.

### 4. Configure app paths

Edit `~/.config/matugen-sync/config.json` to match your system. Default paths:

| App | Config key | Default path |
|-----|-----------|--------------|
| Discord (Vencord) | `vencord` | `~/AppData/Roaming/Vencord/themes/matugen.theme.css` |
| Spotify (Spicetify) | `spicetify` | `~/.config/spicetify/Themes/Matugen/color.ini` |
| Brave | `brave` | `~/.config/BraveSoftware/Brave-Browser/current-theme.css` |
| OpenCode | `opencode` | `~/.config/opencode/themes/matugen.json` |
| Steam (Millennium) | `steam` | `C:\Program Files (x86)\Steam\millennium\themes\Material-Theme\css\main\colors\matugen.css` |
| Flow Launcher | `flow_launcher` | `~/AppData/Roaming/FlowLauncher/Themes/matugen.json` |
| Windows Terminal | `windows_terminal` | `~/AppData/Local/Packages/Microsoft.WindowsTerminal_8wekyb3d8bbwe/LocalState/matugen-scheme.json` |

### 5. Enable OpenRGB RAM + motherboard control

```powershell
# Right-click → Run as Administrator
.\setup_openrgb.bat
```

This creates a scheduled task that starts the OpenRGB SDK server as admin at each logon (required for SMBus/RAM access).

### 6. Enable Govee LED strip (optional)

Create `~/.config/govee-led.json`:

```json
{
  "ha_url": "http://100.83.33.67:8123",
  "ha_token": "your-long-lived-token",
  "entities": ["light.govee_h6102_2f48"]
}
```

Discover entities: `matugen-sync --list-govee`

### 7. Test

```powershell
matugen-sync --list-devices
```

Should show your RAM (ENE DRAM), motherboard, and any other OpenRGB devices.

```powershell
matugen-sync C:\path\to\wallpaper.jpg
```

### 8. Auto-sync on wallpaper change

```powershell
matugen-sync --watch
```

Monitors the registry key `HKCU\Control Panel\Desktop\Wallpaper` for changes.

Run this at startup (e.g., via Startup folder: `shell:startup`) for background operation.

## Config Reference

Key fields in `~/.config/matugen-sync/config.json`:

| Field | Default | Description |
|-------|---------|-------------|
| `openrgb_enabled` | `true` | Set to `false` to skip OpenRGB |
| `openrgb_devices` | `null` | List of `{"id": N, "name": "...", "hue_shift": 0}` for per-device tuning |
| `mad68_enabled` | `true` | Set to `false` to skip MAD68 keyboard |
| `govee_enabled` | `false` | Set to `true` to enable Govee LED |
| `govee_brightness` | `100` | Govee brightness 0-100 |
| `template_dir` | `""` | Custom template directory (default: `~/.config/matugen-sync/templates/`) |

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| `matugen-sync` not found | Close & reopen terminal, or add `%USERPROFILE%\.cargo\bin` to PATH |
| OpenRGB "Connection attempt failed" | Cosmetic — colors still apply |
| RAM not detected | Run `setup_openrgb.bat` as admin; verify scheduled task "OpenRGB Server" is running |
| Govee not working | Check `ha_url` and `ha_token` in `~/.config/govee-led.json` |
| MAD68 not working | Check VID/PID in Device Manager; keyboard must be in Customization mode |
| "Permission Denied, PawnIO" | Cosmetic when running non-admin; server mode as admin fixes this |
