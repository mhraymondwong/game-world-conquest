#!/usr/bin/env python3
"""Generate a 16:9 promotional banner for World Conquest.

Original art only — reuses procedural tiles/units from assets/, composes an
isometric island scene with fog of war, cities, and unit silhouettes.
Does NOT copy Civilization II or Strategic Conquest logos/art.
"""
from __future__ import annotations

import math
import os
import random
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageEnhance

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
ASSETS = os.path.join(ROOT, "assets")
TILES = os.path.join(ASSETS, "tiles")
UNITS = os.path.join(ASSETS, "units")
PROMO = os.path.join(ASSETS, "promo")
SHOTS = os.path.join(ROOT, "..", "shots")

W, H = 1920, 1080
TW, TH = 64, 32  # iso diamond footprint
RNG = random.Random(20261010)

PAL = {
    "ocean_deep": (18, 40, 90),
    "ocean": (28, 62, 132),
    "ocean_lit": (48, 100, 180),
    "grass": (72, 128, 52),
    "panel": (28, 22, 14),
    "brass": (220, 180, 72),
    "brass_dk": (140, 110, 40),
    "fog": (8, 8, 12),
    "title_shadow": (10, 8, 4),
}


def load_tile(name: str) -> Image.Image:
    path = os.path.join(TILES, f"{name}.png")
    return Image.open(path).convert("RGBA")


def load_unit(name: str) -> Image.Image:
    path = os.path.join(UNITS, f"{name}.png")
    return Image.open(path).convert("RGBA")


def iso_to_screen(col: int, row: int, ox: int, oy: int, scale: float = 1.0) -> tuple[int, int]:
    tw, th = int(TW * scale), int(TH * scale)
    x = ox + (col - row) * (tw // 2)
    y = oy + (col + row) * (th // 2)
    return x, y


def paste_centered(base: Image.Image, sprite: Image.Image, cx: int, cy: int, scale: float = 1.0):
    if scale != 1.0:
        nw = max(1, int(sprite.width * scale))
        nh = max(1, int(sprite.height * scale))
        sprite = sprite.resize((nw, nh), Image.Resampling.NEAREST)
    x = cx - sprite.width // 2
    y = cy - sprite.height // 2
    base.alpha_composite(sprite, (x, y))


def make_noise_bg(w: int, h: int) -> Image.Image:
    """Deep ocean gradient with Bayer-ish dither dots."""
    img = Image.new("RGBA", (w, h), (0, 0, 0, 255))
    px = img.load()
    for y in range(h):
        t = y / float(h)
        # radial vignette toward edges
        for x in range(w):
            nx = (x / w - 0.5) * 2
            ny = (y / h - 0.42) * 2
            r = math.sqrt(nx * nx + ny * ny * 1.1)
            # depth gradient
            deep = PAL["ocean_deep"]
            mid = PAL["ocean"]
            lit = PAL["ocean_lit"]
            if t < 0.55:
                tt = t / 0.55
                base = tuple(int(deep[i] + (mid[i] - deep[i]) * tt) for i in range(3))
            else:
                tt = (t - 0.55) / 0.45
                base = tuple(int(mid[i] + (lit[i] - mid[i]) * tt * 0.35) for i in range(3))
            # vignette darken
            dark = min(1.0, max(0.0, (r - 0.55) / 0.9))
            base = tuple(max(0, int(c * (1.0 - dark * 0.72))) for c in base)
            # ordered dither speckles
            bayer = ((x & 3) * 4 + (y & 3)) % 16
            if bayer < 3 and r < 0.95:
                base = tuple(min(255, c + 10) for c in base)
            elif bayer > 13:
                base = tuple(max(0, c - 8) for c in base)
            px[x, y] = base + (255,)
    return img


def build_island_map(scale: float = 1.55) -> Image.Image:
    """Compose a hand-authored island layout using game tiles."""
    tw = int(TW * scale)
    th = int(TH * scale)
    # canvas large enough for iso map
    canvas = Image.new("RGBA", (W + 200, H + 200), (0, 0, 0, 0))

    # Logical map: 0 ocean, 1 grass, 2 plains, 3 forest, 4 hills, 5 city_player, 6 city_ai, 7 city_neutral
    # Hand-crafted archipelago for a dramatic poster composition
    layout = [
        # row 0..14, col 0..18  — sparse islands
        "..................",
        "....111...........",
        "...133311.........",
        "..11344111........",
        "..134C4111........",  # C = player city
        "...1344111.22.....",
        "....1111113221....",
        ".....11113321.....",
        "......111.221.....",
        "...........1......",
        ".....22...........",
        "....2442.11.......",
        "...244A2211.......",  # A = AI city
        "....242211........",
        ".....221..........",
        "..................",
        "........111.......",
        ".......1331.......",
        "......11N11.......",  # N = neutral
        ".......111........",
        "..................",
    ]

    tile_cache = {
        ".": load_tile("ocean"),
        "1": load_tile("grass"),
        "2": load_tile("plains"),
        "3": load_tile("forest"),
        "4": load_tile("hills"),
        "C": load_tile("grass"),
        "A": load_tile("plains"),
        "N": load_tile("grass"),
    }
    city_cache = {
        "C": load_tile("city_player"),
        "A": load_tile("city_ai"),
        "N": load_tile("city_neutral"),
    }
    fog = load_tile("fog")
    shroud = load_tile("shroud")

    # Origin so islands sit in the middle-right of the banner
    ox, oy = 980, 180

    rows = len(layout)
    cols = max(len(r) for r in layout)

    # Draw ocean underlay first (full grid)
    for r in range(rows):
        for c in range(cols):
            sx, sy = iso_to_screen(c, r, ox, oy, scale)
            paste_centered(canvas, tile_cache["."], sx, sy, scale)

    # Land tiles
    land_cells = []
    for r, row in enumerate(layout):
        for c, ch in enumerate(row):
            if ch == ".":
                continue
            sx, sy = iso_to_screen(c, r, ox, oy, scale)
            paste_centered(canvas, tile_cache[ch], sx, sy, scale)
            land_cells.append((c, r, ch, sx, sy))

    # Cities on top of land
    for c, r, ch, sx, sy in land_cells:
        if ch in city_cache:
            paste_centered(canvas, city_cache[ch], sx, sy - int(6 * scale), scale * 1.05)

    # Units — player army near player city, ships in water, fighter, enemy army
    units_place = [
        # (col, row, unit_name, y_bias, scale_mul)
        (4, 4, "army", -10, 1.35),
        (5, 5, "army", -8, 1.25),
        (3, 6, "fighter", -18, 1.4),
        (7, 5, "destroyer", 2, 1.45),
        (8, 7, "battleship", 2, 1.55),
        (6, 8, "transport", 2, 1.4),
        (9, 6, "carrier", 2, 1.5),
        (10, 4, "submarine", 2, 1.35),
        (4, 12, "army_ai", -10, 1.3),
        (5, 12, "destroyer_ai", 2, 1.4),
        (3, 13, "battleship_ai", 2, 1.5),
        (12, 17, "army", -8, 1.2),
    ]
    for c, r, uname, yb, sm in units_place:
        sx, sy = iso_to_screen(c, r, ox, oy, scale)
        u = load_unit(uname)
        paste_centered(canvas, u, sx, sy + int(yb * scale / 1.5), scale * sm)

    # Fog of war: darken left / far edges with shroud + soft fog
    fog_s = fog.resize((int(fog.width * scale), int(fog.height * scale)), Image.Resampling.NEAREST)
    shroud_s = shroud.resize((int(shroud.width * scale), int(shroud.height * scale)), Image.Resampling.NEAREST)
    for r in range(rows):
        for c in range(cols):
            # shroud on far-left and bottom-right unexplored
            if c + r < 4 or (c > 14 and r > 16) or (c < 2 and r > 10):
                sx, sy = iso_to_screen(c, r, ox, oy, scale)
                paste_centered(canvas, shroud_s, sx, sy, 1.0)
            elif c + r < 7 or (r > 15 and c > 10):
                sx, sy = iso_to_screen(c, r, ox, oy, scale)
                # semi-transparent fog overlay
                fog_overlay = fog_s.copy()
                # reduce alpha
                a = fog_overlay.split()[3].point(lambda v: int(v * 0.55))
                fog_overlay.putalpha(a)
                paste_centered(canvas, fog_overlay, sx, sy, 1.0)

    return canvas


def find_font(size: int, bold: bool = True) -> ImageFont.FreeTypeFont:
    candidates = [
        "/usr/share/fonts/opentype/noto/NotoSerifCJK-Bold.ttc" if bold else "/usr/share/fonts/opentype/noto/NotoSerifCJK-Regular.ttc",
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc" if bold else "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
        "/workspace/agents/Game Designer/world-conquest/assets/fonts/NotoSansCJK-Regular.ttc",
    ]
    for path in candidates:
        if os.path.isfile(path):
            try:
                # TTC index: TC is often index 3 or 1 depending on build; try several
                for idx in (2, 3, 1, 0, 4):  # prefer TC/HK-ish
                    try:
                        return ImageFont.truetype(path, size=size, index=idx)
                    except Exception:
                        continue
            except Exception:
                pass
    return ImageFont.load_default()


def draw_title(img: Image.Image):
    d = ImageDraw.Draw(img)
    title_zh = "世界征服"
    title_en = "WORLD CONQUEST"
    tagline = "探索群島 · 攻佔城市 · 征服世界"

    font_zh = find_font(118, bold=True)
    font_en = find_font(46, bold=True)
    font_tag = find_font(28, bold=False)

    # Left panel plate
    panel = Image.new("RGBA", (720, 420), (0, 0, 0, 0))
    pd = ImageDraw.Draw(panel)
    pd.rounded_rectangle([0, 0, 719, 419], radius=18, fill=(22, 18, 12, 200), outline=PAL["brass"] + (220,), width=3)
    pd.rounded_rectangle([10, 10, 709, 409], radius=12, outline=PAL["brass_dk"] + (160,), width=1)
    # top brass stripe
    pd.rectangle([24, 28, 695, 32], fill=PAL["brass"] + (200,))
    pd.rectangle([24, 380, 695, 384], fill=PAL["brass_dk"] + (160,))

    # decorative diamond accents
    for ax, ay in [(40, 60), (680, 60), (40, 350), (680, 350)]:
        pd.polygon([(ax, ay - 8), (ax + 10, ay), (ax, ay + 8), (ax - 10, ay)], fill=PAL["brass"] + (180,))

    img.alpha_composite(panel, (72, 280))

    # Title text with layered shadow for brass glow
    cx, cy = 432, 380

    def text_center(draw, text, y, font, fill, shadow=True):
        bbox = draw.textbbox((0, 0), text, font=font)
        tw = bbox[2] - bbox[0]
        x = cx - tw // 2
        if shadow:
            for ox, oy, col in [
                (3, 4, (0, 0, 0, 200)),
                (1, 2, (40, 30, 10, 180)),
                (0, 0, fill),
            ]:
                draw.text((x + ox, y + oy), text, font=font, fill=col)
        else:
            draw.text((x, y), text, font=font, fill=fill)

    text_center(d, title_zh, 330, font_zh, PAL["brass"] + (255,))
    text_center(d, title_en, 470, font_en, (235, 220, 180, 255,))
    text_center(d, tagline, 545, font_tag, (180, 160, 110, 230,), shadow=False)

    # Small subtitle under panel
    font_sub = find_font(22, bold=False)
    sub = "原創等距 4X · 七種單位 · 戰爭迷霧"
    bbox = d.textbbox((0, 0), sub, font=font_sub)
    tw = bbox[2] - bbox[0]
    d.text((cx - tw // 2 + 1, 642), sub, font=font_sub, fill=(0, 0, 0, 160))
    d.text((cx - tw // 2, 641), sub, font=font_sub, fill=(160, 150, 120, 220))


def add_vignette(img: Image.Image) -> Image.Image:
    w, h = img.size
    vig = Image.new("L", (w, h), 0)
    vd = ImageDraw.Draw(vig)
    for i in range(80):
        a = int(255 * (i / 80.0) ** 1.4)
        vd.rectangle([i, i, w - 1 - i, h - 1 - i], outline=a)
    vig = vig.filter(ImageFilter.GaussianBlur(28))
    dark = Image.new("RGBA", (w, h), (4, 6, 14, 255))
    out = img.copy()
    out = Image.composite(dark, out, vig)
    return out


def add_scan_dither(img: Image.Image, strength: float = 0.08) -> Image.Image:
    """Light ordered dither to match tileset pixel feel without crushing detail."""
    out = img.copy()
    px = out.load()
    w, h = out.size
    for y in range(0, h, 2):
        for x in range(0, w, 2):
            r, g, b, a = px[x, y]
            thr = ((x // 2) + (y // 2)) & 1
            if thr:
                px[x, y] = (
                    max(0, int(r * (1 - strength))),
                    max(0, int(g * (1 - strength))),
                    max(0, int(b * (1 - strength))),
                    a,
                )
    return out


def main():
    os.makedirs(PROMO, exist_ok=True)
    os.makedirs(SHOTS, exist_ok=True)

    print("Building ocean background…")
    banner = make_noise_bg(W, H)

    print("Composing isometric islands…")
    scene = build_island_map(scale=1.65)
    # Crop / place scene — shift left a bit so map sits on right half
    # scene is larger; paste offset
    banner.alpha_composite(scene, (-80, -40))

    # Soft fog gradient on left for title readability
    fog_grad = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gd = ImageDraw.Draw(fog_grad)
    for x in range(900):
        alpha = int(160 * (1.0 - x / 900.0) ** 1.2)
        gd.line([(x, 0), (x, H)], fill=(12, 14, 22, alpha))
    banner = Image.alpha_composite(banner, fog_grad)

    print("Drawing title…")
    draw_title(banner)

    banner = add_vignette(banner)
    banner = add_scan_dither(banner, 0.05)

    # Slight contrast boost
    banner_rgb = banner.convert("RGB")
    banner_rgb = ImageEnhance.Contrast(banner_rgb).enhance(1.08)
    banner_rgb = ImageEnhance.Color(banner_rgb).enhance(1.05)
    banner = banner_rgb.convert("RGBA")

    out_promo = os.path.join(PROMO, "banner_16x9.png")
    out_shots = os.path.join(SHOTS, "world_conquest_banner_16x9.png")
    banner.save(out_promo, "PNG", optimize=True)
    banner.save(out_shots, "PNG", optimize=True)
    print("Wrote", out_promo)
    print("Wrote", out_shots)
    print("Size", banner.size)


if __name__ == "__main__":
    main()
