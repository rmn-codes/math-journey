#!/usr/bin/env python3

from __future__ import annotations

import json
import math
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = Path("/tmp/land-50m.json")
OUTPUT_DIR = ROOT / "public" / "illustrations" / "world-00-language-of-number"
REVIEW_PAGE = ROOT / "public" / "review" / "world-map-variants.html"

WIDTH = 1600
HEIGHT = 900
MARGIN_X = 34
MARGIN_Y = 42

BG = "#f7f5f1"
TEAL = "#1a7a84"
TERRACOTTA = "#c06030"
INK = "#1a1a1a"
SOFT_INK = "#4a4540"
FAINT_INK = "#8e8680"

MIN_LAT = -60.0
JUMP_THRESHOLD = 220.0
X_SCALE = 1.07
Y_SCALE = 0.91


@dataclass(frozen=True)
class Variant:
    slug: str
    title: str
    note: str
    background_svg: str
    stroke_width: float = 1.55


VARIANTS = [
    Variant(
        slug="clean",
        title="01 Clean",
        note="Plain warm-cream background. Closest to a traced reference map.",
        background_svg=f'<rect width="{WIDTH}" height="{HEIGHT}" fill="{BG}" />',
    ),
    Variant(
        slug="paper",
        title="02 Paper",
        note="Clean map with subtle aged-paper grain.",
        background_svg=f"""
  <defs>
    <pattern id="paper-grain" width="40" height="40" patternUnits="userSpaceOnUse">
      <path d="M6 8h7M24 16h4M14 30h5M31 25h3" stroke="{FAINT_INK}" stroke-opacity=".10" stroke-width="1"/>
      <circle cx="10" cy="21" r="1" fill="{FAINT_INK}" fill-opacity=".05"/>
      <circle cx="30" cy="11" r="1" fill="{FAINT_INK}" fill-opacity=".05"/>
    </pattern>
  </defs>
  <rect width="{WIDTH}" height="{HEIGHT}" fill="{BG}" />
  <rect width="{WIDTH}" height="{HEIGHT}" fill="url(#paper-grain)" />
""",
    ),
    Variant(
        slug="mist",
        title="03 Sea Mist",
        note="Pale teal atmosphere behind the Eurasia-Africa belt.",
        background_svg=f"""
  <defs>
    <radialGradient id="mist" cx="63%" cy="34%" r="42%">
      <stop offset="0%" stop-color="{TEAL}" stop-opacity=".14"/>
      <stop offset="50%" stop-color="{TEAL}" stop-opacity=".06"/>
      <stop offset="100%" stop-color="{TEAL}" stop-opacity="0"/>
    </radialGradient>
  </defs>
  <rect width="{WIDTH}" height="{HEIGHT}" fill="{BG}" />
  <rect width="{WIDTH}" height="{HEIGHT}" fill="url(#mist)" />
""",
    ),
    Variant(
        slug="dawn",
        title="04 Dawn Wash",
        note="Soft terracotta warmth from the lower-left edge.",
        background_svg=f"""
  <defs>
    <radialGradient id="dawn" cx="18%" cy="78%" r="45%">
      <stop offset="0%" stop-color="{TERRACOTTA}" stop-opacity=".16"/>
      <stop offset="42%" stop-color="{TERRACOTTA}" stop-opacity=".06"/>
      <stop offset="100%" stop-color="{TERRACOTTA}" stop-opacity="0"/>
    </radialGradient>
  </defs>
  <rect width="{WIDTH}" height="{HEIGHT}" fill="{BG}" />
  <rect width="{WIDTH}" height="{HEIGHT}" fill="url(#dawn)" />
""",
    ),
    Variant(
        slug="atlas",
        title="05 Atlas Plate",
        note="Slight vignette and paper texture, still restrained.",
        background_svg=f"""
  <defs>
    <radialGradient id="vignette" cx="50%" cy="46%" r="74%">
      <stop offset="72%" stop-color="{BG}" stop-opacity="0"/>
      <stop offset="100%" stop-color="{SOFT_INK}" stop-opacity=".08"/>
    </radialGradient>
    <pattern id="plate-paper" width="44" height="44" patternUnits="userSpaceOnUse">
      <path d="M7 9h7M24 16h5M16 34h6M34 26h3" stroke="{FAINT_INK}" stroke-opacity=".11" stroke-width="1"/>
    </pattern>
  </defs>
  <rect width="{WIDTH}" height="{HEIGHT}" fill="{BG}" />
  <rect width="{WIDTH}" height="{HEIGHT}" fill="url(#plate-paper)" />
  <rect width="{WIDTH}" height="{HEIGHT}" fill="url(#vignette)" />
""",
    ),
    Variant(
        slug="romantic",
        title="06 Romantic",
        note="Most illustrative: paper grain, teal mist, and a warm dawn glow.",
        background_svg=f"""
  <defs>
    <pattern id="romantic-paper" width="42" height="42" patternUnits="userSpaceOnUse">
      <path d="M7 8h8M26 18h4M16 33h5M33 27h3" stroke="{FAINT_INK}" stroke-opacity=".10" stroke-width="1"/>
      <circle cx="11" cy="20" r="1" fill="{FAINT_INK}" fill-opacity=".06"/>
      <circle cx="29" cy="11" r="1" fill="{FAINT_INK}" fill-opacity=".05"/>
    </pattern>
    <radialGradient id="romantic-teal" cx="64%" cy="34%" r="44%">
      <stop offset="0%" stop-color="{TEAL}" stop-opacity=".12"/>
      <stop offset="50%" stop-color="{TEAL}" stop-opacity=".05"/>
      <stop offset="100%" stop-color="{TEAL}" stop-opacity="0"/>
    </radialGradient>
    <radialGradient id="romantic-dawn" cx="20%" cy="78%" r="46%">
      <stop offset="0%" stop-color="{TERRACOTTA}" stop-opacity=".14"/>
      <stop offset="42%" stop-color="{TERRACOTTA}" stop-opacity=".05"/>
      <stop offset="100%" stop-color="{TERRACOTTA}" stop-opacity="0"/>
    </radialGradient>
  </defs>
  <rect width="{WIDTH}" height="{HEIGHT}" fill="{BG}" />
  <rect width="{WIDTH}" height="{HEIGHT}" fill="url(#romantic-paper)" />
  <rect width="{WIDTH}" height="{HEIGHT}" fill="url(#romantic-teal)" />
  <rect width="{WIDTH}" height="{HEIGHT}" fill="url(#romantic-dawn)" />
""",
        stroke_width=1.7,
    ),
]

CANONICAL_VARIANT_SLUG = "mist"


def load_topology() -> dict:
    if not SOURCE.exists():
        raise SystemExit(f"Missing source data: {SOURCE}")
    return json.loads(SOURCE.read_text(encoding="utf-8"))


def polygon_area(points: list[tuple[float, float]]) -> float:
    area = 0.0
    for i, (x1, y1) in enumerate(points):
        x2, y2 = points[(i + 1) % len(points)]
        area += x1 * y2 - x2 * y1
    return abs(area) / 2.0


def build_path_data(topo: dict) -> str:
    scale_x, scale_y = topo["transform"]["scale"]
    trans_x, trans_y = topo["transform"]["translate"]
    min_lon, _min_lat, max_lon, _max_lat = topo["bbox"]
    max_lat = 83.2
    usable_w = WIDTH - 2 * MARGIN_X
    usable_h = HEIGHT - 2 * MARGIN_Y
    cx = WIDTH / 2
    cy = HEIGHT / 2

    decoded: list[list[tuple[float, float]]] = []
    for arc in topo["arcs"]:
        x = y = 0
        points: list[tuple[float, float]] = []
        for dx, dy in arc:
            x += dx
            y += dy
            points.append((trans_x + x * scale_x, trans_y + y * scale_y))
        decoded.append(points)

    def project(lon: float, lat: float) -> tuple[float, float]:
        x = MARGIN_X + (lon - min_lon) / (max_lon - min_lon) * usable_w
        y = MARGIN_Y + (max_lat - lat) / (max_lat - MIN_LAT) * usable_h
        x = cx + (x - cx) * X_SCALE
        y = cy + (y - cy) * Y_SCALE
        return x, y

    def ring_points(ring: list[int]) -> list[tuple[float, float]]:
        output: list[tuple[float, float]] = []
        for i, arc_index in enumerate(ring):
            pts = decoded[arc_index] if arc_index >= 0 else list(reversed(decoded[-arc_index - 1]))
            if i:
                pts = pts[1:]
            output.extend(pts)
        return output

    def split_visible_segments(points: list[tuple[float, float]]) -> list[list[tuple[float, float]]]:
        filtered = [(lon, lat) for lon, lat in points if lat >= MIN_LAT]
        if len(filtered) < 2:
            return []

        segments: list[list[tuple[float, float]]] = []
        current = [filtered[0]]
        prev_x, _ = project(*filtered[0])
        for lon, lat in filtered[1:]:
            x, _ = project(lon, lat)
            if abs(x - prev_x) > JUMP_THRESHOLD:
                if len(current) >= 2:
                    segments.append(current)
                current = [(lon, lat)]
            else:
                current.append((lon, lat))
            prev_x = x
        if len(current) >= 2:
            segments.append(current)
        return segments

    parts: list[str] = []
    geom = topo["objects"]["land"]["geometries"][0]
    for polygon in geom["arcs"]:
        exterior = polygon[0]
        raw_points = ring_points(exterior)
        if len(raw_points) < 2:
            continue

        visible = [(lon, lat) for lon, lat in raw_points if lat >= MIN_LAT]
        if len(visible) < 3:
            continue

        projected = [project(lon, lat) for lon, lat in visible]
        xs = [x for x, _ in projected]
        ys = [y for _, y in projected]
        bbox_w = max(xs) - min(xs)
        bbox_h = max(ys) - min(ys)
        area = polygon_area(projected)

        if bbox_w < 9 and bbox_h < 9:
            continue
        if area < 85 and max(bbox_w, bbox_h) < 18:
            continue

        avg_lat = sum(lat for _, lat in visible) / len(visible)
        if avg_lat < MIN_LAT:
            continue

        for seg in split_visible_segments(raw_points):
            proj_seg = [project(lon, lat) for lon, lat in seg]
            if len(proj_seg) < 2:
                continue
            sx = [x for x, _ in proj_seg]
            sy = [y for _, y in proj_seg]
            if max(sx) - min(sx) < 3 and max(sy) - min(sy) < 3:
                continue
            x0, y0 = proj_seg[0]
            commands = [f"M {x0:.2f} {y0:.2f}"]
            for x, y in proj_seg[1:]:
                commands.append(f"L {x:.2f} {y:.2f}")
            parts.append(" ".join(commands))

    return " ".join(parts)


def label_svg() -> str:
    # Same projection assumptions as build_path_data.
    topo = load_topology()
    min_lon, _min_lat, max_lon, _max_lat = topo["bbox"]
    max_lat = 83.2
    usable_w = WIDTH - 2 * MARGIN_X
    usable_h = HEIGHT - 2 * MARGIN_Y
    cx = WIDTH / 2
    cy = HEIGHT / 2

    def project(lon: float, lat: float) -> tuple[float, float]:
        x = MARGIN_X + (lon - min_lon) / (max_lon - min_lon) * usable_w
        y = MARGIN_Y + (max_lat - lat) / (max_lat - MIN_LAT) * usable_h
        x = cx + (x - cx) * X_SCALE
        y = cy + (y - cy) * Y_SCALE
        return x, y

    markers = [
        ("Mesopotamia", 44.0, 33.0, 18, -9, "start"),
        ("Nile Valley", 31.0, 26.0, -18, -9, "end"),
        ("Indus Valley", 68.0, 28.0, 18, -9, "start"),
        ("Yellow River", 111.0, 35.0, 18, -9, "start"),
    ]

    layers: list[str] = []
    for label, lon, lat, dx, dy, anchor in markers:
        x, y = project(lon, lat)
        tx = x + dx
        ty = y + dy
        layers.append(
            f'<circle cx="{x:.2f}" cy="{y:.2f}" r="5.4" fill="{TERRACOTTA}" stroke="{INK}" stroke-width="1.4" />'
        )
        layers.append(
            f'<text x="{tx:.2f}" y="{ty:.2f}" fill="{BG}" stroke="{BG}" stroke-width="5.6" '
            f'stroke-linejoin="round" paint-order="stroke" font-family="Georgia, serif" '
            f'font-size="26" text-anchor="{anchor}">{label}</text>'
        )
        layers.append(
            f'<text x="{tx:.2f}" y="{ty:.2f}" fill="{SOFT_INK}" font-family="Georgia, serif" '
            f'font-size="26" text-anchor="{anchor}">{label}</text>'
        )
    return "".join(layers)


def render_svg(path_data: str, labels: str, variant: Variant) -> str:
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {WIDTH} {HEIGHT}" role="img" aria-labelledby="title desc">
  <title id="title">{variant.title} world map of early civilization cradles</title>
  <desc id="desc">{variant.note}</desc>
  {variant.background_svg}
  <path d="{path_data}" fill="none" stroke="{TEAL}" stroke-width="{variant.stroke_width}" stroke-linecap="round" stroke-linejoin="round" />
  {labels}
</svg>
"""


def build_review_page(variants: list[Variant]) -> str:
    cards = []
    for variant in variants:
        file_name = f"w00-ch001-map-early-civilization-cradles-{variant.slug}.svg"
        cards.append(
            f"""
            <article class="card">
              <h2>{variant.title}</h2>
              <p>{variant.note}</p>
              <a class="frame" href="/illustrations/world-00-language-of-number/{file_name}" target="_blank" rel="noopener">
                <img src="/illustrations/world-00-language-of-number/{file_name}" alt="{variant.title}" />
              </a>
              <code>{file_name}</code>
            </article>
            """
        )

    return f"""<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>World Map Variants</title>
    <style>
      :root {{
        --bg: #f7f5f1;
        --panel: #fffdfa;
        --ink: #1a1a1a;
        --soft: #4a4540;
        --faint: #8e8680;
        --teal: #1a7a84;
        --rule: rgba(26, 26, 26, 0.1);
      }}
      * {{ box-sizing: border-box; }}
      body {{
        margin: 0;
        background: linear-gradient(180deg, #f7f5f1 0%, #efe9df 100%);
        color: var(--ink);
        font-family: Georgia, serif;
      }}
      main {{
        max-width: 1480px;
        margin: 0 auto;
        padding: 32px 20px 56px;
      }}
      h1 {{
        margin: 0 0 8px;
        font-size: 2.4rem;
      }}
      .lede {{
        margin: 0 0 24px;
        color: var(--soft);
        max-width: 70ch;
      }}
      .grid {{
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(420px, 1fr));
        gap: 18px;
      }}
      .card {{
        background: var(--panel);
        border: 1px solid var(--rule);
        border-radius: 18px;
        padding: 18px;
        box-shadow: 0 20px 40px rgba(26, 26, 26, 0.05);
      }}
      .card h2 {{
        margin: 0 0 8px;
        font-size: 1.3rem;
      }}
      .card p {{
        margin: 0 0 14px;
        color: var(--soft);
      }}
      .frame {{
        display: block;
        border-radius: 14px;
        overflow: hidden;
        border: 1px solid var(--rule);
        background: #fff;
      }}
      .frame img {{
        display: block;
        width: 100%;
        height: auto;
      }}
      code {{
        display: inline-block;
        margin-top: 10px;
        color: var(--teal);
        background: rgba(26, 122, 132, 0.08);
        padding: 4px 8px;
        border-radius: 999px;
        font-size: 0.86rem;
      }}
    </style>
  </head>
  <body>
    <main>
      <h1>World Map Variants</h1>
      <p class="lede">All six maps use the same traced world coastline data. The differences here are proportional tuning, island filtering, line weight, and background mood.</p>
      <section class="grid">
        {''.join(cards)}
      </section>
    </main>
  </body>
</html>
"""


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    REVIEW_PAGE.parent.mkdir(parents=True, exist_ok=True)

    topo = load_topology()
    path_data = build_path_data(topo)
    labels = label_svg()

    rendered_by_slug: dict[str, str] = {}
    for variant in VARIANTS:
        file_name = f"w00-ch001-map-early-civilization-cradles-{variant.slug}.svg"
        svg = render_svg(path_data, labels, variant)
        rendered_by_slug[variant.slug] = svg
        (OUTPUT_DIR / file_name).write_text(svg, encoding="utf-8")

    canonical_svg = rendered_by_slug[CANONICAL_VARIANT_SLUG]
    (OUTPUT_DIR / "w00-ch001-map-early-civilization-cradles.svg").write_text(canonical_svg, encoding="utf-8")

    REVIEW_PAGE.write_text(build_review_page(VARIANTS), encoding="utf-8")
    print(f"Wrote {len(VARIANTS)} variants and review page")


if __name__ == "__main__":
    main()
