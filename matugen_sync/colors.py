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


def _extract_colors_fast(image_path: str | Path) -> dict[str, str]:
    try:
        from PIL import Image
        import colorsys
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
        d[key] = accent
    d["background"] = "#19120c"
    d["on_background"] = "#efe0d5"
    d["surface"] = "#19120c"
    d["on_surface"] = "#efe0d5"
    d["surface_variant"] = "#51453a"
    d["surface_container"] = "#261e18"

    return d
