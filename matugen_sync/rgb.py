import colorsys
import logging
import subprocess
import sys

logger = logging.getLogger(__name__)


def _hex_to_rgb_int(hex_color: str) -> tuple[int, int, int]:
    h = hex_color.lstrip("#")
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def _shift_hue(hex_color: str, degrees: float) -> str:
    r, g, b = _hex_to_rgb_int(hex_color)
    rn, gn, bn = r / 255.0, g / 255.0, b / 255.0
    h, l, s = colorsys.rgb_to_hls(rn, gn, bn)
    h = (h + degrees / 360.0) % 1.0
    r2, g2, b2 = colorsys.hls_to_rgb(h, l, s)
    return "#{:02x}{:02x}{:02x}".format(int(r2 * 255), int(g2 * 255), int(b2 * 255))


def _adjust_sl(hex_color: str, saturation: float, lightness: float) -> str:
    r, g, b = _hex_to_rgb_int(hex_color)
    rn, gn, bn = r / 255.0, g / 255.0, b / 255.0
    h, l, s = colorsys.rgb_to_hls(rn, gn, bn)
    r2, g2, b2 = colorsys.hls_to_rgb(h, lightness, saturation)
    return "#{:02x}{:02x}{:02x}".format(int(r2 * 255), int(g2 * 255), int(b2 * 255))


def _run_openrgb(args: list[str], openrgb_cli: str) -> bool:
    cmd = [openrgb_cli] + args
    try:
        subprocess.run(cmd, timeout=15, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except Exception as e:
        logger.warning("OpenRGB command failed: %s", e)
        return False


def list_devices(openrgb_cli: str) -> list[dict]:
    try:
        result = subprocess.run(
            [openrgb_cli, "-l"],
            capture_output=True, text=True, timeout=30,
        )
        lines = result.stdout.split("\n")
        devices = []
        for line in lines:
            line = line.strip()
            if line and line[0].isdigit():
                idx_str = line.split(":")[0].strip()
                name = ":".join(line.split(":")[1:]).strip()
                devices.append({"id": int(idx_str), "name": name})
        return devices
    except Exception as e:
        logger.warning("Failed to list OpenRGB devices: %s", e)
        return []


def sync_openrgb(
    accent_hex: str,
    openrgb_cli: str = "openrgb",
    devices: list[dict] | None = None,
):
    color = accent_hex[1:]

    if devices:
        for dev in devices:
            dev_color = accent_hex
            hue_shift = dev.get("hue_shift", 0)
            saturation = dev.get("saturation", 1.0)
            lightness = dev.get("lightness", 0.5)

            if hue_shift:
                dev_color = _shift_hue(dev_color, hue_shift)
            if saturation != 1.0 or lightness != 0.5:
                dev_color = _adjust_sl(dev_color, saturation, lightness)

            dev_id = str(dev.get("id", ""))
            base_args = ["--mode", "static", "--color", dev_color[1:],
                         "--brightness", str(dev.get("brightness", 50))]
            if dev_id:
                base_args = ["--device", dev_id] + base_args

            ok = _run_openrgb(base_args, openrgb_cli)
            if ok:
                logger.info("  OpenRGB device %s set to %s", dev.get("name", dev_id), dev_color)
        return

    _run_openrgb(["--mode", "static", "--color", color, "--brightness", "50"], openrgb_cli)
    logger.info("  OpenRGB set to #%s (all devices/zones)", color)


def sync_mad68(hex_color: str):
    try:
        import hid
    except ImportError:
        logger.warning("hidapi not installed, skipping MAD68")
        return

    VID, PID, INTERFACE = 0x373B, 0x1058, 1
    r, g, b = _hex_to_rgb_int(hex_color)

    target = None
    for d in hid.enumerate(VID, PID):
        if d.get("interface_number") == INTERFACE:
            target = d["path"]
            break

    if not target:
        logger.warning("  MAD68 keyboard not found (VID %04x, PID %04x)", VID, PID)
        return

    dev = hid.device()
    try:
        dev.open_path(target)
        # Windows HID API requires 0x00 report ID prefix
        data = bytearray([0, 7, 65, 2, 0, 0x96, r, g, b, 0xB1] + [0] * 23)
        dev.write(bytes(data))
        logger.info("  MAD68 keyboard set to #%02x%02x%02x", r, g, b)
    except Exception as e:
        logger.warning("  MAD68 write failed: %s", e)
    finally:
        dev.close()
