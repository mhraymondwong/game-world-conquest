#!/usr/bin/env python3
"""Generate ORIGINAL Civ2-inspired isometric tiles, units, and UI for World Conquest.

Aesthetic goals (inspired by classic 1990s isometric 4X look, NOT a copy):
- Diamond tiles 64×32 (+ short side faces → 64×40)
- Limited earthy palette, soft ordered dither
- Icon-like forests/hills, readable unit silhouettes
- Transparent PNG, nearest-neighbor friendly (no blur)

All art is procedurally generated; no commercial or Freeciv sprites are used.
"""
from __future__ import annotations

from PIL import Image, ImageDraw
import os
import math
import random

OUT = os.path.join(os.path.dirname(__file__), "..", "assets")
TW, TH = 64, 32  # diamond footprint
TILE_H = TH + 8  # include short extrusion
RNG = random.Random(42)

# --- Classic limited palette (original) ---
PAL = {
    "ocean_deep": (28, 62, 132),
    "ocean": (40, 90, 168),
    "ocean_lit": (72, 128, 200),
    "ocean_foam": (160, 200, 230),
    "grass": (72, 128, 52),
    "grass_lit": (104, 160, 72),
    "grass_dk": (48, 96, 40),
    "plains": (168, 148, 72),
    "plains_lit": (196, 176, 96),
    "plains_dk": (128, 112, 52),
    "forest": (40, 96, 40),
    "forest_lit": (64, 128, 56),
    "forest_dk": (28, 72, 28),
    "tree": (36, 110, 36),
    "tree_dk": (24, 78, 24),
    "tree_lit": (70, 150, 60),
    "trunk": (88, 56, 28),
    "hills": (132, 108, 68),
    "hills_lit": (168, 140, 88),
    "hills_dk": (96, 76, 48),
    "rock": (120, 110, 100),
    "coast_sand": (196, 176, 120),
    "fog": (10, 10, 14),
    "shroud": (18, 20, 28),
    "outline": (20, 18, 14),
    "brass": (200, 168, 72),
    "brass_dk": (120, 96, 40),
    "panel": (42, 34, 22),
    "ui_btn": (72, 56, 32),
    "ui_hover": (112, 90, 42),
}


def ensure(d: str) -> None:
    os.makedirs(d, exist_ok=True)


def rgba(c, a: int = 255):
    if len(c) == 4:
        return c
    return (c[0], c[1], c[2], a)


def shade(c, f: float, a: int | None = None):
    out = tuple(max(0, min(255, int(x * f))) for x in c[:3])
    alpha = a if a is not None else (c[3] if len(c) > 3 else 255)
    return out + (alpha,)


def lerp_rgb(a, b, t: float):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def in_diamond(x: int, y: int, cx: int, cy: int, w: int = TW, h: int = TH, pad: float = 1.0) -> bool:
    return abs((x - cx) / (w / 2.0)) + abs((y - cy) / (h / 2.0)) < pad


def bayer4(x: int, y: int) -> float:
    """4×4 Bayer ordered dither threshold in [0,1)."""
    m = [
        [0, 8, 2, 10],
        [12, 4, 14, 6],
        [3, 11, 1, 9],
        [15, 7, 13, 5],
    ]
    return m[y & 3][x & 3] / 16.0


def diamond_points(cx, cy, w=TW, h=TH):
    return [(cx, cy - h // 2), (cx + w // 2, cy), (cx, cy + h // 2), (cx - w // 2, cy)]


def draw_diamond(draw, cx, cy, fill, outline=None, w=TW, h=TH):
    pts = diamond_points(cx, cy, w, h)
    draw.polygon(pts, fill=fill, outline=outline)


def fill_diamond_dither(img: Image.Image, cx: int, cy: int, c_lo, c_hi, density: float = 0.45,
                        w: int = TW, h: int = TH, mode: str = "bayer"):
    """Paint Civ2-style ordered dither inside the diamond top face."""
    for y in range(cy - h // 2, cy + h // 2 + 1):
        for x in range(cx - w // 2, cx + w // 2 + 1):
            if not in_diamond(x, y, cx, cy, w, h, 0.98):
                continue
            # classic 2-tone checker with Bayer modulation (readable at 1x)
            check = ((x >> 1) + (y >> 1)) & 1
            thr = bayer4(x, y)
            if mode == "checker":
                use_hi = check == 0
            else:
                # mix: checker base + density via Bayer
                use_hi = (check == 0 and thr < density + 0.25) or (check == 1 and thr < density - 0.15)
            tgrad = (y - (cy - h // 2)) / float(h)
            dark = lerp_rgb(c_lo, shade(c_lo, 0.85)[:3], tgrad)
            lit = lerp_rgb(c_hi, shade(c_hi, 1.05)[:3], 1.0 - tgrad * 0.4)
            col = lit if use_hi else dark
            edge = abs((x - cx) / (w / 2.0)) + abs((y - cy) / (h / 2.0))
            if edge > 0.78:
                col = shade(col, 0.72)[:3]
            elif edge > 0.65:
                col = shade(col, 0.88)[:3]
            img.putpixel((x, y), rgba(col))


def add_extrusion(draw, cx, cy, base, side_shade=0.72):
    left = [(cx - TW // 2, cy), (cx, cy + TH // 2), (cx, cy + TH // 2 + 6), (cx - TW // 2, cy + 6)]
    right = [(cx + TW // 2, cy), (cx, cy + TH // 2), (cx, cy + TH // 2 + 6), (cx + TW // 2, cy + 6)]
    draw.polygon(left, fill=shade(base, side_shade))
    draw.polygon(right, fill=shade(base, side_shade * 0.88))


def make_blank_tile() -> Image.Image:
    return Image.new("RGBA", (TW, TILE_H), (0, 0, 0, 0))


def make_ocean():
    img = make_blank_tile()
    d = ImageDraw.Draw(img)
    cx, cy = TW // 2, TH // 2 + 2
    add_extrusion(d, cx, cy, PAL["ocean_deep"], 0.65)
    fill_diamond_dither(img, cx, cy, PAL["ocean_deep"], PAL["ocean"], density=0.38, mode="bayer")
    # wave lines — denser Civ2-ish water texture
    for i in range(28):
        x = 8 + (i * 5 + (i * 3) % 7) % (TW - 16)
        y = cy - 10 + (i * 2 + (i // 3)) % 20
        if in_diamond(x, y, cx, cy, pad=0.78):
            col = PAL["ocean_lit"] if i % 2 == 0 else PAL["ocean_foam"]
            length = 3 + (i % 4)
            d.line([(x, y), (x + length, y)], fill=rgba(col, 210 if i % 2 == 0 else 160))
    # ordered dither wash for depth
    for y in range(cy - TH // 2, cy + TH // 2 + 1):
        for x in range(cx - TW // 2, cx + TW // 2 + 1):
            if not in_diamond(x, y, cx, cy, pad=0.9):
                continue
            if bayer4(x, y + 1) < 0.18:
                px = img.getpixel((x, y))
                if px[3] > 0:
                    img.putpixel((x, y), rgba(lerp_rgb(px[:3], PAL["ocean_deep"], 0.35)))
    # outline
    draw_diamond(d, cx, cy, None, outline=shade(PAL["ocean_deep"], 0.55), w=TW, h=TH)
    # re-fill was wiped by outline-only; draw outline via points on edge
    for ang in range(0, 360, 2):
        pass
    # proper outline
    pts = diamond_points(cx, cy)
    d.line(pts + [pts[0]], fill=shade(PAL["ocean_deep"], 0.5), width=1)
    path = os.path.join(OUT, "tiles", "ocean.png")
    img.save(path)
    print("tile ocean")
    return img


def make_land(name: str, c_lo, c_hi, density: float, decor: str | None = None):
    img = make_blank_tile()
    d = ImageDraw.Draw(img)
    cx, cy = TW // 2, TH // 2 + 2
    add_extrusion(d, cx, cy, c_lo, 0.7)
    fill_diamond_dither(img, cx, cy, c_lo, c_hi, density=density, mode="bayer")
    if decor == "grass_tufts":
        for _ in range(18):
            x = RNG.randint(12, TW - 12)
            y = RNG.randint(cy - 8, cy + 8)
            if in_diamond(x, y, cx, cy, pad=0.7):
                d.point((x, y), fill=rgba(PAL["grass_dk"]))
                d.point((x, y - 1), fill=rgba(PAL["grass_lit"]))
    elif decor == "plains_dots":
        for _ in range(7):
            x = RNG.randint(14, TW - 14)
            y = RNG.randint(cy - 6, cy + 6)
            if in_diamond(x, y, cx, cy, pad=0.65):
                d.ellipse([x, y, x + 2, y + 1], fill=rgba(PAL["plains_dk"]))
    elif decor == "forest":
        # denser green wash then trees
        for y in range(cy - TH // 2, cy + TH // 2 + 1):
            for x in range(cx - TW // 2, cx + TW // 2 + 1):
                if in_diamond(x, y, cx, cy, pad=0.92) and bayer4(x + 1, y) < 0.35:
                    px = img.getpixel((x, y))
                    if px[3] > 0:
                        img.putpixel((x, y), rgba(lerp_rgb(px[:3], PAL["forest"], 0.55)))
        # tree icons — small cones in iso perspective
        spots = [(-12, 2), (-6, -3), (-2, 4), (2, -5), (8, 1), (4, 5),
                 (-9, -1), (0, 0), (10, -3), (-4, 2), (6, -1), (-1, -6)]
        for dx, dy in spots:
            _draw_tree(d, cx + dx, cy + dy)
    elif decor == "hills":
        ridges = [(-10, 2, 14), (4, -2, 12), (-2, 4, 10)]
        for hx, hy, hw in ridges:
            _draw_hill(d, cx + hx, cy + hy, hw)
        # rock speckles
        for _ in range(6):
            x = RNG.randint(14, TW - 14)
            y = RNG.randint(cy - 6, cy + 6)
            if in_diamond(x, y, cx, cy, pad=0.6):
                d.point((x, y), fill=rgba(PAL["rock"]))
    pts = diamond_points(cx, cy)
    d.line(pts + [pts[0]], fill=shade(c_lo, 0.45), width=1)
    path = os.path.join(OUT, "tiles", f"{name}.png")
    img.save(path)
    print("tile", name)
    return img


def _draw_tree(d: ImageDraw.ImageDraw, x: int, y: int):
    # trunk
    d.line([(x, y + 2), (x, y + 5)], fill=rgba(PAL["trunk"]), width=1)
    # layered foliage (Civ2-ish cone blobs)
    d.polygon([(x, y - 7), (x + 5, y - 1), (x - 5, y - 1)], fill=rgba(PAL["tree_dk"]))
    d.polygon([(x, y - 9), (x + 4, y - 3), (x - 4, y - 3)], fill=rgba(PAL["tree"]))
    d.polygon([(x, y - 11), (x + 3, y - 5), (x - 3, y - 5)], fill=rgba(PAL["tree_lit"]))


def _draw_hill(d: ImageDraw.ImageDraw, x: int, y: int, w: int = 12):
    h = max(5, w // 2)
    # shadowed slope
    d.polygon([(x, y - h), (x + w // 2, y + 2), (x - w // 2, y + 2)], fill=rgba(PAL["hills_dk"]))
    # lit face
    d.polygon([(x, y - h), (x + w // 4, y), (x - w // 6, y + 1)], fill=rgba(PAL["hills_lit"]))
    # ridge line
    d.line([(x - 1, y - h + 1), (x + w // 3, y)], fill=rgba(PAL["hills_lit"]), width=1)


def make_coast_variant(name: str, edge: str):
    """Ocean base with land wedges / sandy shore along named edges."""
    img = make_blank_tile()
    d = ImageDraw.Draw(img)
    cx, cy = TW // 2, TH // 2 + 2
    add_extrusion(d, cx, cy, PAL["ocean_deep"], 0.65)
    fill_diamond_dither(img, cx, cy, PAL["ocean_deep"], PAL["ocean"], density=0.35, mode="bayer")

    land_lo, land_hi = PAL["grass_dk"], PAL["grass_lit"]
    for y in range(TILE_H):
        for x in range(TW):
            if not in_diamond(x, y, cx, cy, pad=0.98):
                continue
            u = (x - cx) / (TW / 2.0)   # E positive
            v = (y - cy) / (TH / 2.0)   # S positive
            # isometric cardinal wedges
            land = False
            sand = False
            # N = top tip (negative v, small |u|)
            if "N" in edge and v < 0.0 and abs(u) < 0.92 - abs(v) * 0.15:
                land = v < -0.08
                sand = -0.08 <= v < 0.05
            if "S" in edge and v > 0.0 and abs(u) < 0.92 - abs(v) * 0.15:
                land = v > 0.08
                sand = -0.05 < v <= 0.08
            if "E" in edge and u > 0.0 and abs(v) < 0.92 - abs(u) * 0.15:
                land = u > 0.08
                sand = -0.05 < u <= 0.08
            if "W" in edge and u < 0.0 and abs(v) < 0.92 - abs(u) * 0.15:
                land = u < -0.08
                sand = -0.08 <= u < 0.05
            # corner-ish combos already covered by letter presence
            if land:
                col = land_hi if bayer4(x, y) < 0.4 else land_lo
                # vertical gradient
                t = (y - (cy - TH // 2)) / float(TH)
                col = lerp_rgb(land_hi, land_lo, t * 0.4)
                if bayer4(x, y) < 0.35:
                    col = land_hi
                img.putpixel((x, y), rgba(col))
            elif sand:
                col = PAL["coast_sand"] if bayer4(x, y) < 0.5 else shade(PAL["coast_sand"], 0.88)[:3]
                # mix a bit of water foam
                if bayer4(x + 2, y) < 0.25:
                    col = PAL["ocean_foam"]
                img.putpixel((x, y), rgba(col))

    # foam speckles near shore
    for _ in range(8):
        x = RNG.randint(8, TW - 8)
        y = RNG.randint(cy - 10, cy + 10)
        if in_diamond(x, y, cx, cy, pad=0.8):
            px = img.getpixel((x, y))
            if px[2] > 140:  # bluish
                d.point((x, y), fill=rgba(PAL["ocean_foam"], 180))

    pts = diamond_points(cx, cy)
    d.line(pts + [pts[0]], fill=shade(PAL["ocean_deep"], 0.5), width=1)
    path = os.path.join(OUT, "tiles", f"{name}.png")
    img.save(path)
    print("coast", name)


def make_fog():
    # Unexplored: solid near-black diamond (matches draw path size TW×TH)
    img = Image.new("RGBA", (TW, TH), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    cx, cy = TW // 2, TH // 2
    draw_diamond(d, cx, cy, rgba(PAL["fog"]), outline=rgba((0, 0, 0)))
    # subtle dither so it isn't a flat void
    for y in range(TH):
        for x in range(TW):
            if in_diamond(x, y, cx, cy, pad=0.95) and bayer4(x, y) < 0.2:
                img.putpixel((x, y), rgba((16, 16, 22)))
    img.save(os.path.join(OUT, "tiles", "fog.png"))

    # Explored shroud: semi-transparent dark overlay (same footprint as terrain blit)
    img2 = Image.new("RGBA", (TW, TILE_H), (0, 0, 0, 0))
    d2 = ImageDraw.Draw(img2)
    cx2, cy2 = TW // 2, TH // 2 + 2
    # darken diamond only
    for y in range(TILE_H):
        for x in range(TW):
            if in_diamond(x, y, cx2, cy2, pad=0.98):
                a = 150 if bayer4(x, y) < 0.55 else 125
                img2.putpixel((x, y), rgba(PAL["shroud"], a))
    img2.save(os.path.join(OUT, "tiles", "shroud.png"))
    print("fog/shroud")


def make_city(owner: str):
    """Small isometric building cluster — Civ2-ish city icon, original design."""
    colors = {
        "neutral": {"roof": (168, 168, 168), "wall": (110, 110, 110), "accent": (200, 200, 200)},
        "player": {"roof": (70, 130, 210), "wall": (48, 88, 150), "accent": (120, 180, 240)},
        "ai": {"roof": (210, 70, 70), "wall": (140, 42, 42), "accent": (240, 120, 100)},
    }
    c = colors[owner]
    img = Image.new("RGBA", (48, 48), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)

    # ground pad (iso diamond) with dither
    for y in range(22, 42):
        for x in range(6, 42):
            u = abs((x - 24) / 16.0) + abs((y - 32) / 8.0)
            if u < 1.0:
                col = (110, 96, 60) if bayer4(x, y) < 0.45 else (90, 78, 52)
                if u > 0.85:
                    col = shade(col, 0.75)[:3]
                img.putpixel((x, y), rgba(col))

    def building(bx, by, bw, bh, roof, wall):
        top = [(bx, by - bh), (bx + bw // 2, by - bh + bw // 4),
               (bx, by - bh + bw // 2), (bx - bw // 2, by - bh + bw // 4)]
        left = [(bx - bw // 2, by - bh + bw // 4), (bx, by - bh + bw // 2),
                (bx, by + bw // 4), (bx - bw // 2, by)]
        right = [(bx + bw // 2, by - bh + bw // 4), (bx, by - bh + bw // 2),
                 (bx, by + bw // 4), (bx + bw // 2, by)]
        d.polygon(left, fill=shade(wall, 0.72))
        d.polygon(right, fill=shade(wall, 0.92))
        d.polygon(top, fill=rgba(roof))
        # roof ridge highlight
        d.line([(bx, by - bh), (bx + bw // 2 - 1, by - bh + bw // 4)], fill=rgba(shade(roof, 1.2)[:3]))
        for wy in range(2):
            wx = bx + 1
            yy = by - bh + bw // 2 + 2 + wy * 4
            if yy < by - 1:
                d.rectangle([wx, yy, wx + 2, yy + 2], fill=rgba((255, 220, 120)))

    # back row house
    building(18, 28, 10, 7, shade(c["roof"], 0.9)[:3], shade(c["wall"], 0.9)[:3])
    # main hall
    building(24, 32, 18, 11, c["roof"], c["wall"])
    # keep / tower
    building(31, 29, 9, 16, c["accent"], c["wall"])
    # front annex
    building(14, 35, 11, 7, shade(c["roof"], 0.95)[:3], shade(c["wall"], 0.85)[:3])
    # flag
    d.line([(31, 9), (31, 1)], fill=rgba((40, 40, 40)), width=1)
    d.polygon([(31, 1), (40, 3), (31, 7)], fill=rgba(c["roof"]))

    img = outline_sprite(img, col=(18, 16, 12, 230))
    img.save(os.path.join(OUT, "tiles", f"city_{owner}.png"))
    print("city", owner)


def outline_sprite(img: Image.Image, col=(20, 18, 14, 220)) -> Image.Image:
    w, h = img.size
    out = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    for y in range(h):
        for x in range(w):
            p = img.getpixel((x, y))
            if p[3] > 128:
                out.putpixel((x, y), p)
                continue
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nx, ny = x + dx, y + dy
                if 0 <= nx < w and 0 <= ny < h and img.getpixel((nx, ny))[3] > 128:
                    out.putpixel((x, y), col)
                    break
    return out


def tint_ai(img: Image.Image) -> Image.Image:
    """Recolor toward crimson for AI faction — still readable silhouette."""
    out = img.copy()
    w, h = out.size
    for y in range(h):
        for x in range(w):
            r, g, b, a = out.getpixel((x, y))
            if a < 16:
                continue
            # skip near-black outline
            if r + g + b < 60:
                continue
            # push red, pull green/blue
            nr = min(255, int(r * 0.55 + 140))
            ng = int(g * 0.45)
            nb = int(b * 0.45)
            out.putpixel((x, y), (nr, ng, nb, a))
    # small faction badge
    d = ImageDraw.Draw(out)
    d.rectangle([1, 1, 7, 7], fill=(200, 40, 40, 230), outline=(255, 200, 80, 255))
    return out


def make_army():
    img = Image.new("RGBA", (32, 32), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    # shadow
    d.ellipse([8, 26, 24, 31], fill=(0, 0, 0, 60))
    # boots
    d.rectangle([11, 24, 15, 29], fill=(40, 36, 32, 255))
    d.rectangle([17, 24, 21, 29], fill=(40, 36, 32, 255))
    # legs
    d.rectangle([12, 20, 15, 25], fill=(55, 70, 45, 255))
    d.rectangle([17, 20, 20, 25], fill=(55, 70, 45, 255))
    # torso
    d.rectangle([10, 12, 22, 21], fill=(60, 100, 55, 255))
    d.rectangle([11, 13, 21, 16], fill=(80, 120, 70, 255))  # belt highlight
    # arms
    d.rectangle([7, 13, 10, 20], fill=(55, 90, 50, 255))
    d.rectangle([22, 13, 25, 18], fill=(55, 90, 50, 255))
    # rifle
    d.line([(22, 14), (29, 10)], fill=(30, 28, 24, 255), width=2)
    d.rectangle([27, 9, 30, 11], fill=(50, 50, 45, 255))
    # helmet
    d.ellipse([11, 4, 21, 12], fill=(45, 75, 40, 255))
    d.rectangle([11, 8, 21, 11], fill=(45, 75, 40, 255))
    # face
    d.ellipse([13, 7, 19, 12], fill=(200, 168, 128, 255))
    img = outline_sprite(img)
    img.save(os.path.join(OUT, "units", "army.png"))
    tint_ai(img).save(os.path.join(OUT, "units", "army_ai.png"))
    print("army")


def make_fighter():
    img = Image.new("RGBA", (40, 28), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    # shadow
    d.ellipse([8, 20, 32, 26], fill=(0, 0, 0, 50))
    # wings
    d.polygon([(6, 14), (20, 8), (22, 12), (10, 18)], fill=(90, 110, 140, 255))
    d.polygon([(18, 12), (34, 6), (36, 10), (22, 16)], fill=(70, 90, 120, 255))
    # fuselage
    d.polygon([(8, 14), (30, 10), (34, 14), (28, 18), (10, 18)], fill=(170, 180, 195, 255))
    d.polygon([(8, 14), (30, 10), (28, 14), (10, 16)], fill=(200, 210, 220, 255))
    # cockpit
    d.ellipse([22, 10, 28, 15], fill=(40, 70, 110, 255))
    # prop / nose
    d.ellipse([6, 12, 11, 17], fill=(50, 50, 55, 255))
    d.line([(4, 14), (8, 14)], fill=(30, 30, 30, 255), width=1)
    # tail
    d.polygon([(30, 10), (36, 6), (36, 12), (32, 14)], fill=(80, 90, 110, 255))
    # star insignia (original simple)
    d.polygon([(16, 13), (17, 15), (19, 15), (17, 16), (18, 18), (16, 17), (14, 18), (15, 16), (13, 15), (15, 15)],
              fill=(220, 200, 60, 255))
    img = outline_sprite(img)
    img.save(os.path.join(OUT, "units", "fighter.png"))
    tint_ai(img).save(os.path.join(OUT, "units", "fighter_ai.png"))
    print("fighter")


def make_ship(name: str, kind: str):
    """kind: destroyer | submarine | transport | carrier | battleship"""
    img = Image.new("RGBA", (48, 28), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    # water shadow
    d.ellipse([4, 18, 44, 26], fill=(20, 40, 80, 70))

    hull = {
        "destroyer": (75, 95, 115),
        "battleship": (55, 65, 85),
        "carrier": (80, 90, 105),
        "transport": (120, 105, 75),
        "submarine": (50, 70, 60),
    }[kind]
    lit = shade(hull, 1.25)[:3]
    dk = shade(hull, 0.7)[:3]

    if kind == "submarine":
        d.ellipse([4, 10, 40, 20], fill=rgba(hull))
        d.ellipse([6, 10, 38, 16], fill=rgba(lit))
        d.rectangle([18, 5, 26, 11], fill=rgba(dk))  # conning tower
        d.line([(22, 5), (22, 1)], fill=(30, 30, 30, 255))
        d.ellipse([36, 12, 44, 18], fill=rgba(dk))  # stern taper
        d.polygon([(4, 14), (0, 15), (4, 16)], fill=rgba(dk))  # bow
    else:
        # iso-ish hull diamond
        length = {"destroyer": 28, "battleship": 34, "carrier": 36, "transport": 30}[kind]
        bow_x = 4
        stern_x = 4 + length
        # lower hull
        d.polygon([
            (bow_x, 16), (bow_x + 6, 10), (stern_x, 10),
            (stern_x + 4, 16), (stern_x, 22), (bow_x + 6, 22)
        ], fill=rgba(hull))
        # deck (lit)
        d.polygon([
            (bow_x, 16), (bow_x + 6, 10), (stern_x, 10), (stern_x + 4, 16)
        ], fill=rgba(lit))
        # bridge
        bx = bow_x + length // 3
        d.rectangle([bx, 4, bx + 9, 11], fill=rgba(dk))
        d.rectangle([bx + 2, 2, bx + 7, 4], fill=(35, 35, 40, 255))
        if kind in ("destroyer", "battleship"):
            guns = [bow_x + 10, bow_x + 16] if kind == "destroyer" else [bow_x + 8, bow_x + 14, bow_x + 22]
            for gx in guns:
                d.rectangle([gx, 11, gx + 3, 14], fill=(25, 25, 28, 255))
                d.line([(gx + 1, 11), (gx + 7, 8)], fill=(20, 20, 22, 255), width=2)
            if kind == "battleship":
                # second funnel
                d.rectangle([bx + 12, 5, bx + 16, 11], fill=rgba(shade(dk, 0.85)[:3]))
        elif kind == "carrier":
            # flight deck
            d.rectangle([bow_x + 8, 11, stern_x - 2, 15], fill=(55, 55, 65, 255))
            d.line([(bow_x + 10, 13), (stern_x - 4, 13)], fill=(220, 200, 80, 255))
            # island superstructure already bridge
            d.rectangle([stern_x - 10, 6, stern_x - 4, 12], fill=rgba(dk))
        elif kind == "transport":
            for i in range(3):
                hx = bow_x + 10 + i * 7
                d.rectangle([hx, 11, hx + 5, 17], fill=(150, 130, 95, 255))
                d.rectangle([hx + 1, 12, hx + 4, 14], fill=(40, 60, 90, 255))

    img = outline_sprite(img)
    img.save(os.path.join(OUT, "units", f"{name}.png"))
    tint_ai(img).save(os.path.join(OUT, "units", f"{name}_ai.png"))
    print(name)


def make_ui_icons():
    ensure(os.path.join(OUT, "ui"))
    for name, col in [("btn", PAL["ui_btn"]), ("btn_hover", PAL["ui_hover"]), ("panel", PAL["panel"])]:
        img = Image.new("RGBA", (64, 32), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        d.rounded_rectangle([0, 0, 63, 31], radius=4, fill=rgba(col, 230), outline=rgba(PAL["brass"]))
        # inner highlight line
        d.line([(4, 3), (59, 3)], fill=rgba(PAL["brass"], 120))
        img.save(os.path.join(OUT, "ui", f"{name}.png"))

    for uname in ["army", "fighter", "destroyer", "submarine", "transport", "carrier", "battleship"]:
        src = Image.open(os.path.join(OUT, "units", f"{uname}.png")).convert("RGBA")
        src.thumbnail((22, 22), Image.Resampling.NEAREST)
        frame = Image.new("RGBA", (28, 28), (0, 0, 0, 0))
        d = ImageDraw.Draw(frame)
        d.rounded_rectangle([0, 0, 27, 27], radius=3, fill=rgba(PAL["panel"], 230), outline=rgba(PAL["brass"]))
        ox = (28 - src.size[0]) // 2
        oy = (28 - src.size[1]) // 2
        frame.paste(src, (ox, oy), src)
        frame.save(os.path.join(OUT, "ui", f"prod_{uname}.png"))
    print("ui")


def main():
    ensure(os.path.join(OUT, "tiles"))
    ensure(os.path.join(OUT, "units"))
    ensure(os.path.join(OUT, "ui"))
    RNG.seed(42)

    make_ocean()
    make_land("grass", PAL["grass_dk"], PAL["grass_lit"], 0.42, decor="grass_tufts")
    make_land("plains", PAL["plains_dk"], PAL["plains_lit"], 0.40, decor="plains_dots")
    make_land("forest", PAL["forest_dk"], PAL["forest_lit"], 0.35, decor="forest")
    make_land("hills", PAL["hills_dk"], PAL["hills_lit"], 0.38, decor="hills")

    for edge in ["N", "S", "E", "W", "NE", "NW", "SE", "SW", "NS", "EW"]:
        make_coast_variant(f"coast_{edge}", edge)

    make_fog()
    for o in ["neutral", "player", "ai"]:
        make_city(o)

    make_army()
    make_fighter()
    make_ship("destroyer", "destroyer")
    make_ship("submarine", "submarine")
    make_ship("transport", "transport")
    make_ship("carrier", "carrier")
    make_ship("battleship", "battleship")
    make_ui_icons()
    print("DONE — original Civ2-inspired tileset written to", OUT)


if __name__ == "__main__":
    main()
