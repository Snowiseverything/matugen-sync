import colorsys
import logging

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


def sync_openrgb(
    accent_hex: str,
    devices: list[dict] | None = None,
):
    from openrgb import OpenRGBClient
    from openrgb.utils import RGBColor

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

    def _set_device_color(sdk_dev, color_rgb, color_hex):
        # Switch to Direct mode to override Rainbow/Spectrum Cycle
        if sdk_dev.active_mode != 0:
            sdk_dev.set_mode(0)
        sdk_dev.set_color(color_rgb)
        logger.info("  OpenRGB %s set to %s", sdk_dev.name, color_hex)

    if devices:
        for dev_cfg in devices:
            dev_color = accent_hex
            hue_shift = dev_cfg.get("hue_shift", 0)
            saturation = dev_cfg.get("saturation", 1.0)
            lightness = dev_cfg.get("lightness", 0.5)
            if hue_shift:
                dev_color = _shift_hue(dev_color, hue_shift)
            if saturation != 1.0 or lightness != 0.5:
                dev_color = _adjust_sl(dev_color, saturation, lightness)
            dev_color_rgb = RGBColor(*_hex_to_rgb_int(dev_color))

            for sdk_dev in cli.devices:
                if str(sdk_dev.id) == str(dev_cfg.get("id", "")):
                    _set_device_color(sdk_dev, dev_color_rgb, dev_color)
        cli.disconnect()
        return

    for dev in cli.devices:
        _set_device_color(dev, color, accent_hex)
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
