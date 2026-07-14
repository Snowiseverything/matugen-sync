from pathlib import Path
from jinja2 import Environment, FileSystemLoader, StrictUndefined


def _hex_to_rgb(val: str) -> str:
    h = val.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f"{r} {g} {b}"


def render_templates(
    template_dir: str | Path,
    output_dir: str | Path,
    colors: dict[str, str],
    reload_apps: bool = False,
):
    template_dir = Path(template_dir).resolve()
    output_dir = Path(output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    env = Environment(
        loader=FileSystemLoader(str(template_dir)),
        undefined=StrictUndefined,
        trim_blocks=True,
        lstrip_blocks=True,
    )
    env.filters["hex_to_rgb"] = _hex_to_rgb

    # Make hex values available as #RRGGBB, RRGGBB, and RGB decimal (space-separated for CSS rgb())
    ctx = {}
    for key, val in colors.items():
        ctx[key] = val
        ctx[key.replace("#", "") + "_nohash"] = val.lstrip("#")
        ctx[key + "_rgb"] = _hex_to_rgb(val)

    rendered = []
    for tmpl_file in template_dir.iterdir():
        if not tmpl_file.is_file() or tmpl_file.suffix not in (".j2", ".jinja", ".jinja2"):
            continue
        template = env.get_template(tmpl_file.name)
        output_name = tmpl_file.name
        for suffix in (".j2", ".jinja", ".jinja2"):
            if output_name.endswith(suffix):
                output_name = output_name[: -len(suffix)]
                break
        output_path = output_dir / output_name
        result = template.render(**ctx)
        output_path.write_text(result, encoding="utf-8")
        rendered.append(str(output_path))

    return rendered
