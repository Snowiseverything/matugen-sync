import colorsys
import logging
import time

logger = logging.getLogger(__name__)


def wait_for_openrgb(timeout: float = 30.0, interval: float = 2.0):
    from openrgb import OpenRGBClient
    start = time.time()
    while time.time() - start < timeout:
        try:
            cli = OpenRGBClient()
            if cli.devices:
                names = [d.name for d in cli.devices]
                if any("DRAM" in n or "RAM" in n for n in names):
                    if any("ASUS" in n or "AURA" in n or "Motherboard" in n or "GAMING" in n for n in names):
                        cli.disconnect()
                        return True
                logger.info("  OpenRGB devices found: %s, waiting for RAM+Mobo...", names)
            cli.disconnect()
        except Exception:
            pass
        if time.time() - start < timeout:
            logger.info("  Waiting for OpenRGB server...")
            time.sleep(interval)
    return False


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


def _apply_calibration(hex_color: str, cfg: dict) -> str:
    c = hex_color
    hue_shift = cfg.get("hue_shift", 0)
    saturation = cfg.get("saturation", 1.0)
    lightness = cfg.get("lightness", 0.5)
    brightness = cfg.get("brightness", 1.0)
    if hue_shift:
        c = _shift_hue(c, hue_shift)
    if saturation != 1.0 or lightness != 0.5:
        c = _adjust_sl(c, saturation, lightness)
    if brightness != 1.0:
        r, g, b = _hex_to_rgb_int(c)
        r = min(255, int(r * brightness))
        g = min(255, int(g * brightness))
        b = min(255, int(b * brightness))
        c = "#{:02x}{:02x}{:02x}".format(r, g, b)
    return c


def _colors_match(c1: tuple, c2: tuple) -> bool:
    return abs(c1[0] - c2[0]) <= 2 and abs(c1[1] - c2[1]) <= 2 and abs(c1[2] - c2[2]) <= 2


def sync_openrgb(
    accent_hex: str,
    devices: list[dict] | None = None,
    wait: bool = False,
):
    from openrgb import OpenRGBClient
    from openrgb.utils import RGBColor

    if wait:
        if not wait_for_openrgb():
            logger.warning("  OpenRGB server did not become available")
            return

    try:
        cli = OpenRGBClient()
    except Exception as e:
        logger.warning("  OpenRGB server not reachable: %s", e)
        logger.warning("  Make sure OpenRGB server is running as admin")
        return

    color = RGBColor(*_hex_to_rgb_int(accent_hex))

    if not cli.devices:
        logger.warning("  No OpenRGB devices found (server running as admin?)")
        cli.disconnect()
        return

    def _set_color_and_verify(sdk_dev, color_rgb, color_hex, zone=None):
        if sdk_dev.active_mode != 0:
            sdk_dev.set_mode(0)
        targets = [zone] if zone else sdk_dev.zones
        for t in targets:
            if not t.colors:
                continue
            for attempt in range(3):
                t.set_color(color_rgb)
                time.sleep(0.1)
                led = t.colors[0]
                if _colors_match((led.red, led.green, led.blue), (color_rgb.red, color_rgb.green, color_rgb.blue)):
                    break
        label = f"{sdk_dev.name} / {zone.name}" if zone else sdk_dev.name
        logger.info("  OpenRGB %s set to %s", label, color_hex)

    if devices:
        for dev_cfg in devices:
            zone_overrides = dev_cfg.pop("zones", {})

            for sdk_dev in cli.devices:
                if str(sdk_dev.id) != str(dev_cfg.get("id", "")):
                    continue

                if zone_overrides:
                    for zone in sdk_dev.zones:
                        z_cfg = zone_overrides.get(zone.name, {})
                        base = _apply_calibration(accent_hex, dev_cfg)
                        z_color = _apply_calibration(base, z_cfg)
                        z_rgb = RGBColor(*_hex_to_rgb_int(z_color))
                        _set_color_and_verify(sdk_dev, z_rgb, z_color, zone)
                else:
                    dev_color = _apply_calibration(accent_hex, dev_cfg)
                    dev_color_rgb = RGBColor(*_hex_to_rgb_int(dev_color))
                    _set_color_and_verify(sdk_dev, dev_color_rgb, dev_color)

            dev_cfg["zones"] = zone_overrides
        cli.disconnect()
        return

    for dev in cli.devices:
        _set_color_and_verify(dev, color, accent_hex)
    cli.disconnect()


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
        data = bytearray([0, 7, 65, 2, 0, 0x96, r, g, b, 0xB1] + [0] * 23)
        dev.write(bytes(data))
        logger.info("  MAD68 keyboard set to #%02x%02x%02x", r, g, b)
    except Exception as e:
        logger.warning("  MAD68 write failed: %s", e)
    finally:
        dev.close()
