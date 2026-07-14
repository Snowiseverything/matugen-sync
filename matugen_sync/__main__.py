import argparse
import json
import logging
import shutil
import sys
import time
from pathlib import Path

from .colors import extract_colors
from .config import Config
from .templates import render_templates
from .rgb import sync_openrgb, sync_mad68, list_devices
from . import govee

logger = logging.getLogger("matugen-sync")

CONFIG_DIR = Path.home() / ".config" / "matugen-sync"
CONFIG_FILE = CONFIG_DIR / "config.json"
TEMPLATE_DIR = CONFIG_DIR / "templates"
COLORS_CACHE = Path.home() / ".cache" / "matugen-sync" / "colors.json"

DEFAULT_OUTPUTS: dict[str, str] = {
    "vencord": "~/.config/Vencord/themes/matugen.theme.css",
    "spicetify": "~/.config/spicetify/Themes/Matugen/color.ini",
    "brave": "~/.config/BraveSoftware/Brave-Browser/current-theme.css",
    "opencode": "~/.config/opencode/themes/matugen.json",
    "steam": "~/.steam/steamui/skins/Material-Theme/css/main/colors/matugen.css",
    "flow_launcher": "~/AppData/Roaming/FlowLauncher/Themes/matugen.json",
    "windows_terminal": "~/AppData/Local/Packages/Microsoft.WindowsTerminal_8wekyb3d8bbwe/LocalState/matugen-scheme.json",
}


def setup_logging(verbose: bool):
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(level=level, format="%(message)s", stream=sys.stdout)


def save_colors_cache(colors: dict):
    COLORS_CACHE.parent.mkdir(parents=True, exist_ok=True)
    COLORS_CACHE.write_text(json.dumps(colors, indent=2, ensure_ascii=False), encoding="utf-8")


def load_colors_cache() -> dict | None:
    if COLORS_CACHE.exists():
        return json.loads(COLORS_CACHE.read_text(encoding="utf-8"))
    return None


def deploy_app_outputs(rendered_dir: Path, app_outputs: dict[str, str]):
    for app_name, dest in app_outputs.items():
        src = rendered_dir / f"{app_name}.css"
        if not src.exists():
            src = rendered_dir / f"{app_name}.json"
        if not src.exists():
            src = rendered_dir / f"{app_name}.ini"
        if not src.exists():
            logger.debug("  No output for %s", app_name)
            continue
        dst = Path(dest).expanduser()
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(str(src), str(dst))
        logger.info("  %s -> %s", src.name, dst)


def _get_wallpaper_path() -> str | None:
    import winreg
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Control Panel\Desktop") as key:
            val, _ = winreg.QueryValueEx(key, "Wallpaper")
            return val if val and val != "(none)" else None
    except Exception:
        return None


def _watch_loop(args, cfg, app_outputs):
    import winreg
    logger.info("Watching for wallpaper changes...")
    last_wall = None
    while True:
        try:
            wall = _get_wallpaper_path()
            if wall and wall != last_wall:
                logger.info("Wallpaper changed: %s", wall)
                last_wall = wall
                _run_sync(wall, args, cfg, app_outputs)
            time.sleep(5)
        except KeyboardInterrupt:
            logger.info("Watcher stopped.")
            break
        except Exception as e:
            logger.debug("Watch error: %s", e)
            time.sleep(5)


def _run_sync(image_path: str, args, cfg, app_outputs):
    logger.info("Extracting colors from %s", Path(image_path).name)
    colors = extract_colors(image_path)
    save_colors_cache(colors)
    logger.info("Accent: %s", colors["accent"])

    if not args.no_templates:
        tmpl_dir = Path(cfg.template_dir).expanduser() if cfg.template_dir else TEMPLATE_DIR
        if tmpl_dir.exists():
            out_dir = Path.home() / ".cache" / "matugen-sync" / "rendered"
            out_dir.mkdir(parents=True, exist_ok=True)
            render_templates(tmpl_dir, out_dir, colors)
            logger.info("Rendered to %s", out_dir)
            deploy_app_outputs(out_dir, app_outputs)
        else:
            logger.warning("Template dir not found: %s", tmpl_dir)

    rgb_color = colors.get("source") or colors.get("accent") or colors.get("primary", "#000000")

    if not args.no_rgb:
        if cfg.openrgb_enabled:
            sync_openrgb(rgb_color, cfg.openrgb_cli, cfg.openrgb_devices)
        if cfg.mad68_enabled:
            sync_mad68(rgb_color)

    if not args.no_govee and cfg.govee_enabled:
        govee.set_color(rgb_color, cfg.govee_brightness)


def main():
    parser = argparse.ArgumentParser(description="Matugen Sync for Windows - Material You theme sync")
    parser.add_argument("image", nargs="?", help="Path to wallpaper image")
    parser.add_argument("--watch", "-w", action="store_true", help="Watch for wallpaper changes and auto-sync")
    parser.add_argument("--no-rgb", action="store_true", help="Skip RGB hardware sync (OpenRGB + MAD68)")
    parser.add_argument("--no-govee", action="store_true", help="Skip Govee LED sync")
    parser.add_argument("--no-templates", action="store_true", help="Skip template rendering")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--init", action="store_true", help="Create default config and install templates")
    parser.add_argument("--install-templates", action="store_true", help="Copy built-in templates to config dir")
    parser.add_argument("--list-paths", action="store_true", help="Show configured output paths")
    parser.add_argument("--list-devices", action="store_true", help="List detected OpenRGB devices")
    parser.add_argument("--list-govee", action="store_true", help="Discover Govee devices via Home Assistant")

    args = parser.parse_args()
    setup_logging(args.verbose)

    cfg = Config.load(CONFIG_FILE)
    app_outputs = cfg.app_outputs or DEFAULT_OUTPUTS

    if args.list_devices:
        print("OpenRGB devices:")
        devs = list_devices(cfg.openrgb_cli)
        if devs:
            for d in devs:
                print(f"  {d['id']}: {d['name']}")
            print("\nAdd to config.json under 'openrgb_devices':")
            print(json.dumps([{"id": int(d["id"]), "name": d["name"]} for d in devs], indent=2))
        else:
            print("  (none detected)")
        return

    if args.list_govee:
        print("Govee devices (via Home Assistant):")
        govee.discover()
        return

    if args.list_paths:
        print("Output paths:")
        for app_name, dest in app_outputs.items():
            p = Path(dest).expanduser()
            marker = "exists" if p.exists() else "missing"
            print(f"  [{marker}] {app_name}: {dest}")
        return

    if args.init:
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        cfg.save(CONFIG_FILE)
        logger.info("Created %s", CONFIG_FILE)
        install_templates()
        print(f"\nConfig: {CONFIG_FILE}")
        print(f"Templates: {TEMPLATE_DIR}")
        print(f"Run: matugen-sync <wallpaper.png>")
        return

    if args.install_templates:
        install_templates()
        return

    if args.watch:
        _watch_loop(args, cfg, app_outputs)
        return

    if not args.image:
        parser.print_help()
        sys.exit(1)

    image_path = Path(args.image)
    if not image_path.exists():
        logger.error("Image not found: %s", image_path)
        sys.exit(1)

    _run_sync(str(image_path), args, cfg, app_outputs)
    logger.info("Done!")


def install_templates():
    TEMPLATE_DIR.mkdir(parents=True, exist_ok=True)
    built_in = Path(__file__).resolve().parent.parent / "templates"
    if built_in.exists():
        for f in built_in.iterdir():
            if f.is_file():
                dst = TEMPLATE_DIR / f.name
                shutil.copy2(str(f), str(dst))
                logger.info("  %s -> %s", f.name, dst)
    logger.info("Templates installed to %s", TEMPLATE_DIR)


if __name__ == "__main__":
    main()
