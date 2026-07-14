import json
from pathlib import Path
from dataclasses import dataclass, field, asdict


@dataclass
class Config:
    openrgb_enabled: bool = True
    openrgb_devices: list[dict] | None = None
    mad68_enabled: bool = True
    govee_enabled: bool = False
    govee_brightness: int = 100
    reload_apps: bool = True
    template_dir: str = ""
    app_outputs: dict[str, str] = field(default_factory=lambda: {
        "vencord": "~/.config/Vencord/themes/matugen.theme.css",
        "spicetify": "~/.config/spicetify/Themes/Matugen/color.ini",
        "brave": "~/.config/BraveSoftware/Brave-Browser/current-theme.css",
        "opencode": "~/.config/opencode/themes/matugen.json",
        "steam": "~/.steam/steamui/skins/Material-Theme/css/main/colors/matugen.css",
        "flow_launcher": "~/AppData/Roaming/FlowLauncher/Themes/matugen.json",
        "windows_terminal": "~/AppData/Local/Packages/Microsoft.WindowsTerminal_8wekyb3d8bbwe/LocalState/matugen-scheme.json",
    })
    custom_templates: list[dict] = field(default_factory=list)

    @classmethod
    def load(cls, path: str | Path) -> "Config":
        path = Path(path)
        if not path.exists():
            return cls()
        data = json.loads(path.read_text(encoding="utf-8"))
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})

    def save(self, path: str | Path):
        Path(path).write_text(
            json.dumps(asdict(self), indent=2, ensure_ascii=False), encoding="utf-8"
        )
