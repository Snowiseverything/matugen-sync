import json
import subprocess
import shutil
from pathlib import Path


_COLOR_KEYS = [
    "primary", "on_primary", "primary_container", "on_primary_container",
    "secondary", "on_secondary", "secondary_container", "on_secondary_container",
    "tertiary", "on_tertiary", "tertiary_container", "on_tertiary_container",
    "error", "on_error", "error_container", "on_error_container",
    "background", "on_background", "surface", "on_surface",
    "surface_variant", "on_surface_variant", "surface_container",
    "inverse_surface", "inverse_on_surface", "inverse_primary",
    "outline", "shadow",
    "primary_fixed", "on_primary_fixed", "primary_fixed_dim", "on_primary_fixed_variant",
    "secondary_fixed", "on_secondary_fixed", "secondary_fixed_dim", "on_secondary_fixed_variant",
    "tertiary_fixed", "on_tertiary_fixed", "tertiary_fixed_dim", "on_tertiary_fixed_variant",
    "surface_dim", "surface_bright",
    "surface_container_lowest", "surface_container_low", "surface_container",
    "surface_container_high", "surface_container_highest",
    "outline_variant", "scrim", "surface_tint",
]


def _find_matugen() -> str:
    path = shutil.which("matugen")
    if path:
        return path
    cargo = Path.home() / ".cargo" / "bin" / "matugen.exe"
    if cargo.exists():
        return str(cargo)
    raise FileNotFoundError(
        "matugen not found. Install it: cargo install matugen"
    )


def extract_colors(image_path: str | Path, fast: bool = False) -> dict[str, str]:
    if fast:
        return _extract_colors_fast(image_path)
    matugen = _find_matugen()
    image_path = str(Path(image_path).resolve())

    result = subprocess.run(
        [matugen, "image", image_path, "--json", "hex", "--source-color-index", "0"],
        capture_output=True, text=True, timeout=30,
    )
    if result.returncode != 0:
        raise RuntimeError(f"matugen failed: {result.stderr.strip()}")

    data = json.loads(result.stdout)
    colors = data["colors"]
    source_color = colors.get("source_color", {}).get("dark", {}).get("color", "#000000")

    def _dark(key: str) -> str:
        return colors.get(key, {}).get("dark", {}).get("color", "#000000")

    def _light(key: str) -> str:
        return colors.get(key, {}).get("light", {}).get("color", "#000000")

    d: dict[str, str] = {"source": source_color, "accent": source_color}
    for key in _COLOR_KEYS:
        try:
            d[key] = _dark(key)
        except Exception:
            pass
    for key in _COLOR_KEYS:
        try:
            d["light_" + key] = _light(key)
        except Exception:
            pass

    if "on_surface" in d:
        d["on_background"] = d["on_surface"]
        d["light_on_background"] = d.get("light_on_surface", d["on_surface"])

    return d


def _tone(hex_color: str, lightness: float) -> str:
    import colorsys
    r, g, b = int(hex_color[1:3], 16), int(hex_color[3:5], 16), int(hex_color[5:7], 16)
    h, _, s = colorsys.rgb_to_hls(r / 255, g / 255, b / 255)
    r2, g2, b2 = colorsys.hls_to_rgb(h, lightness, s)
    return "#{:02x}{:02x}{:02x}".format(int(r2 * 255), int(g2 * 255), int(b2 * 255))


def _extract_colors_fast(image_path: str | Path) -> dict[str, str]:
    try:
        from PIL import Image
    except ImportError:
        return extract_colors(image_path, fast=False)

    img = Image.open(str(image_path)).convert("RGB").resize((64, 64))
    pixels = list(img.getdata())
    r = sum(p[0] for p in pixels) // len(pixels)
    g = sum(p[1] for p in pixels) // len(pixels)
    b = sum(p[2] for p in pixels) // len(pixels)

    accent = "#{:02x}{:02x}{:02x}".format(r, g, b)
    d: dict[str, str] = {"source": accent, "accent": accent}

    for key in _COLOR_KEYS:
        if key in ("background", "surface", "surface_dim",
                    "surface_container", "surface_container_lowest",
                    "surface_container_low", "surface_container_high",
                    "surface_container_highest", "surface_variant",
                    "shadow", "scrim", "outline", "outline_variant"):
            d[key] = "#19120c" if "container" in key else "#1a1a1a"
        elif key.startswith("on_"):
            d[key] = "#e0e0e0"
        elif key.startswith("primary"):
            d[key] = accent
        elif key.startswith("secondary"):
            d[key] = _tone(accent, 0.55)
        elif key.startswith("tertiary"):
            d[key] = _tone(accent, 0.45)
        elif key in ("error", "error_container"):
            d[key] = "#ba1a1a" if key == "error" else "#93000a"
        elif key in ("on_error", "on_error_container"):
            d[key] = "#ffffff" if key == "on_error" else "#ffdad6"
        elif key in ("inverse_surface", "inverse_on_surface", "inverse_primary"):
            d[key] = {"inverse_surface": "#e0e0e0",
                       "inverse_on_surface": "#1a1a1a",
                       "inverse_primary": accent}.get(key, accent)
        elif key == "surface_tint":
            d[key] = accent
        else:
            d[key] = accent

    return d
