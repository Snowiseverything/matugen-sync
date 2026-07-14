import json
import logging
import urllib.request
from pathlib import Path

logger = logging.getLogger("matugen-sync")

CONFIG_PATH = Path.home() / ".config" / "govee-led.json"


def _load_config() -> dict:
    default = {
        "ha_url": "http://100.83.33.67:8123",
        "ha_token": "",
        "entities": ["light.govee_h6102_2f48"],
    }
    if CONFIG_PATH.exists():
        try:
            data = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
            default.update(data)
        except Exception as e:
            logger.warning("Failed to read %s: %s", CONFIG_PATH, e)
    return default


def _ha_call(ha_url: str, ha_token: str, endpoint: str, data: dict | None = None):
    req = urllib.request.Request(
        f"{ha_url}/api/{endpoint}",
        data=json.dumps(data).encode() if data else None,
        headers={
            "Authorization": f"Bearer {ha_token}",
            "Content-Type": "application/json",
        },
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read())


def discover():
    cfg = _load_config()
    if not cfg["ha_token"]:
        logger.error("HA token not configured. Edit %s", CONFIG_PATH)
        return
    try:
        r = _ha_call(cfg["ha_url"], cfg["ha_token"], "states")
        for s in r:
            if "govee" in s.get("entity_id", "").lower():
                eid = s["entity_id"]
                state = s.get("state", "?")
                color = s.get("attributes", {}).get("rgb_color", "?")
                print(f"  {eid}: {state} rgb={color}")
    except Exception as e:
        logger.error("HA discover failed: %s", e)


def set_color(hex_color: str, brightness: int = 100):
    cfg = _load_config()
    if not cfg["ha_token"]:
        logger.warning("HA token not set — skipping Govee. Edit %s", CONFIG_PATH)
        return

    h = hex_color.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    pct = max(1, min(100, brightness))

    for entity in cfg["entities"]:
        try:
            _ha_call(
                cfg["ha_url"],
                cfg["ha_token"],
                "services/light/turn_on",
                {"entity_id": entity, "rgb_color": [r, g, b], "brightness_pct": pct},
            )
            logger.info("  Govee %s set to #%s at %d%%", entity, h, pct)
        except Exception as e:
            logger.warning("  Govee %s failed: %s", entity, e)
