"""Generate SVG social preview images from markdown frontmatter under a Hugo content directory.

This command scans the provided `content` directory for markdown files (`index.md` and `_index.md`),
reads the frontmatter to extract title/description/summary, and writes an SVG image next to the
markdown folder named `<folder-name>-image.svg`.
"""
from __future__ import annotations

from pathlib import Path
from xml.sax.saxutils import escape
from typing import Optional

import sys

try:
    import yaml  # type: ignore
except Exception:  # pragma: no cover - optional dep
    yaml = None  # type: ignore

import click


def read_frontmatter(md_path: Path) -> dict:
    """Read YAML frontmatter from a markdown file.

    Returns an empty dict if no frontmatter is present or parsing fails.
    """
    try:
        txt = md_path.read_text(encoding="utf-8")
    except Exception:
        return {}
    if txt.startswith("\ufeff"):
        txt = txt[1:]
    s = txt.lstrip()
    if not s.startswith("---"):
        return {}
    parts = s.split("---", 2)
    if len(parts) < 3:
        return {}
    fm_raw = parts[1]
    if yaml:
        try:
            data = yaml.safe_load(fm_raw) or {}
            if isinstance(data, dict):
                return data
        except Exception:
            pass
    # Fallback: basic key:value parse for common keys
    data = {}
    for line in fm_raw.splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            k = k.strip()
            v = v.strip().strip('"').strip("'")
            if k in {"title", "seoTitle", "description", "summary", "layout"}:
                data[k] = v
    return data


def wrap_by_width(text: str, font_size: int, width: int, margin: int):
    if not text:
        return []
    avg_char_w = font_size * 0.55
    max_chars = max(8, int((width - 2 * margin) / avg_char_w))
    words, lines, cur = text.split(), [], ""
    for w in words:
        add = (" " if cur else "") + w
        if len(cur) + len(add) <= max_chars:
            cur += add
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def tspans_center(lines, line_height, cx):
    out = []
    for i, line in enumerate(lines):
        dy = "0" if i == 0 else str(line_height)
        out.append(f'<tspan x="{cx}" dy="{dy}">{escape(line)}</tspan>')
    return "\n        ".join(out)


def make_svg(title, desc, *, width=1200, height=630, bg="#f3f4f6", fg="#0b1220"):
    margin = 80
    title_size = 52
    desc_size = 30
    lh_title = int(title_size * 1.25)
    lh_desc = int(desc_size * 1.45)
    gap = 28
    cx = width // 2

    t_lines = wrap_by_width(title or "", title_size, width, margin)
    d_lines = wrap_by_width(desc or "", desc_size, width, margin)

    block_h = len(t_lines) * lh_title + (gap if d_lines else 0) + len(d_lines) * lh_desc
    start_y = int((height - block_h) / 2 + title_size)
    y_desc = start_y + len(t_lines) * lh_title + (gap if d_lines else 0)

    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" preserveAspectRatio="xMidYMid meet">
  <rect width="100%" height="100%" fill="{bg}"/>
  <g font-family="-apple-system,system-ui,Segoe UI,Roboto,Helvetica,Arial,sans-serif" fill="{fg}">
    <text y="{start_y}" text-anchor="middle" font-size="{title_size}" font-weight="700" xml:space="preserve">
        {tspans_center(t_lines, lh_title, cx)}
    </text>
    <text y="{y_desc}" text-anchor="middle" font-size="{desc_size}" xml:space="preserve">
        {tspans_center(d_lines, lh_desc, cx)}
    </text>
  </g>
</svg>'''


def resolve_output_path(folder: Path) -> Path:
    return folder / (folder.name + "-image.svg")


def generate_for(md: Path, width=1200, height=630, bg="#f3f4f6", fg="#0b1220") -> Optional[Path]:
    fm = read_frontmatter(md)
    if not fm:
        return None
    title = (fm.get("title") or "").strip()
    desc_primary = (fm.get("description") or "").strip()
    desc_fallback = (fm.get("summary") or "").strip()
    desc = desc_primary if desc_primary else desc_fallback
    out_path = resolve_output_path(md.parent)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    svg = make_svg(title, desc, width=width, height=height, bg=bg, fg=fg)
    out_path.write_text(svg, encoding="utf-8")
    return out_path


@click.command()
@click.option(
    "--content-dir",
    type=click.Path(exists=True, file_okay=False, dir_okay=True, path_type=Path),
    default=Path("content"),
    help="Path to Hugo content directory (default: content)",
)
@click.option("--width", type=int, default=1200, help="Image width in px (default: 1200)")
@click.option("--height", type=int, default=630, help="Image height in px (default: 630)")
@click.option("--bg", type=str, default="#f3f4f6", help="Background color (default: #f3f4f6)")
@click.option("--fg", type=str, default="#0b1220", help="Foreground color (default: #0b1220)")
def svg(content_dir: Path, width: int, height: int, bg: str, fg: str):
    """Generate SVG images for markdown files under the content folder.

    Scans recursively for `index.md` and `_index.md` and writes
    `<folder-name>-image.svg` into the same folder.
    """
    content_dir = content_dir.resolve()
    if not content_dir.exists():
        click.secho(f"Content directory not found: {content_dir}", fg="red")
        raise click.exceptions.Exit(1)

    click.echo(f"\n=== Generating SVGs from {content_dir} ===")

    # Discover markdown files to process (focus on section/page roots)
    md_files: list[Path] = []
    md_files.extend(content_dir.rglob("index.md"))
    md_files.extend(content_dir.rglob("_index.md"))
    md_files = sorted(set(md_files))

    if not md_files:
        click.echo("No markdown files (index.md/_index.md) found")
        return

    count = 0
    for md in md_files:
        out = generate_for(md, width=width, height=height, bg=bg, fg=fg)
        if out:
            rel = out.relative_to(content_dir)
            click.echo(f"  wrote {rel}")
            count += 1
        else:
            rel_md = md.relative_to(content_dir)
            click.echo(f"  skip {rel_md}")

    click.echo(f"Generated {count} SVG file(s)")
