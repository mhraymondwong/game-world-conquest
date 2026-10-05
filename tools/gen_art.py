#!/usr/bin/env python3
"""Generate original isometric tiles, units, and UI icons for World Conquest."""
from PIL import Image, ImageDraw
import os, math, random

OUT = os.path.join(os.path.dirname(__file__), "..", "assets")
TW, TH = 64, 32  # diamond tile
RNG = random.Random(42)

def ensure(d):
    os.makedirs(d, exist_ok=True)

def diamond_points(cx, cy, w=TW, h=TH):
    return [(cx, cy - h//2), (cx + w//2, cy), (cx, cy + h//2), (cx - w//2, cy)]

def draw_diamond(draw, cx, cy, fill, outline=None, w=TW, h=TH):
    pts = diamond_points(cx, cy, w, h)
    draw.polygon(pts, fill=fill, outline=outline)

def shade(c, f):
    return tuple(max(0, min(255, int(x * f))) for x in c[:3]) + ((c[3],) if len(c) > 3 else ())

def make_tile(name, base, top_shade=1.15, side_shade=0.75, dither=None, overlay=None):
    img = Image.new("RGBA", (TW, TH + 8), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    cx, cy = TW // 2, TH // 2 + 2
    # left face (darker), right face, top
    left = [ (cx - TW//2, cy), (cx, cy + TH//2), (cx, cy + TH//2 + 4), (cx - TW//2, cy + 4) ]
    right = [ (cx + TW//2, cy), (cx, cy + TH//2), (cx, cy + TH//2 + 4), (cx + TW//2, cy + 4) ]
    d.polygon(left, fill=shade(base, side_shade))
    d.polygon(right, fill=shade(base, side_shade * 0.9))
    draw_diamond(d, cx, cy, shade(base, top_shade), outline=shade(base, 0.55))
    # dither / texture
    if dither == "water":
        for i in range(18):
            x = RNG.randint(8, TW - 8)
            y = RNG.randint(6, TH - 4)
            # only inside diamond roughly
            if abs((x - cx) / (TW/2)) + abs((y - cy) / (TH/2)) < 0.85:
                d.point((x, y), fill=shade(base, 1.35 if i % 2 == 0 else 0.7))
                if i % 3 == 0:
                    d.line([(x, y), (x + 3, y)], fill=shade(base, 1.4))
    elif dither == "grass":
        for i in range(12):
            x = RNG.randint(10, TW - 10)
            y = RNG.randint(8, TH - 6)
            if abs((x - cx) / (TW/2)) + abs((y - cy) / (TH/2)) < 0.8:
                d.point((x, y), fill=shade(base, 0.65))
                d.point((x, y - 1), fill=shade(base, 1.2))
    elif dither == "plains":
        for i in range(8):
            x = RNG.randint(12, TW - 12)
            y = RNG.randint(10, TH - 8)
            if abs((x - cx) / (TW/2)) + abs((y - cy) / (TH/2)) < 0.75:
                d.ellipse([x, y, x + 2, y + 1], fill=shade(base, 0.85))
    if overlay == "forest":
        # simple tree blobs
        for dx, dy in [(-6, 0), (4, -2), (0, 3), (-2, -4)]:
            tx, ty = cx + dx, cy + dy - 2
            d.ellipse([tx - 4, ty - 5, tx + 4, ty + 1], fill=(34, 90, 34, 255))
            d.ellipse([tx - 3, ty - 8, tx + 3, ty - 2], fill=(48, 120, 48, 255))
            d.line([(tx, ty + 1), (tx, ty + 4)], fill=(80, 50, 20, 255))
    elif overlay == "hills":
        for dx, dy in [(-8, 2), (6, 0), (0, -2)]:
            hx, hy = cx + dx, cy + dy
            d.polygon([(hx, hy - 6), (hx + 8, hy + 2), (hx - 8, hy + 2)], fill=shade(base, 0.7))
            d.polygon([(hx, hy - 6), (hx + 4, hy - 1), (hx - 2, hy + 1)], fill=shade(base, 1.1))
    path = os.path.join(OUT, "tiles", f"{name}.png")
    img.save(path)
    print("tile", name)
    return path

def make_coast_variant(name, land_color, ocean_color, edge):
    """edge: N,S,E,W,NE,NW,SE,SW bitmask-ish simple blends"""
    img = Image.new("RGBA", (TW, TH + 8), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    cx, cy = TW // 2, TH // 2 + 2
    draw_diamond(d, cx, cy, ocean_color, outline=shade(ocean_color, 0.6))
    # paint land half based on edge string
    for y in range(TH + 8):
        for x in range(TW):
            if abs((x - cx) / (TW/2)) + abs((y - cy) / (TH/2)) >= 1.0:
                continue
            # isometric axes: NW-SE and NE-SW
            u = (x - cx) / (TW/2) + (y - cy) / (TH/2)  # SE direction
            v = -(x - cx) / (TW/2) + (y - cy) / (TH/2)  # SW direction
            land = False
            if "N" in edge and (y - cy) < -2:
                land = True
            if "S" in edge and (y - cy) > 2:
                land = True
            if "E" in edge and (x - cx) > 2:
                land = True
            if "W" in edge and (x - cx) < -2:
                land = True
            if land:
                # dither toward ocean
                if RNG.random() < 0.85 or abs((x-cx)/(TW/2))+abs((y-cy)/(TH/2)) < 0.5:
                    img.putpixel((x, y), land_color)
                else:
                    img.putpixel((x, y), shade(ocean_color, 1.1))
    path = os.path.join(OUT, "tiles", f"{name}.png")
    img.save(path)
    print("coast", name)

def make_fog():
    img = Image.new("RGBA", (TW, TH), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    cx, cy = TW // 2, TH // 2
    draw_diamond(d, cx, cy, (8, 8, 12, 255), outline=(0, 0, 0, 255))
    img.save(os.path.join(OUT, "tiles", "fog.png"))
    # explored shroud (dim)
    img2 = Image.new("RGBA", (TW, TH), (0, 0, 0, 0))
    d2 = ImageDraw.Draw(img2)
    draw_diamond(d2, cx, cy, (20, 20, 30, 140), outline=None)
    img2.save(os.path.join(OUT, "tiles", "shroud.png"))
    print("fog")

def make_city(owner):
    colors = {
        "neutral": ((160, 160, 160), (100, 100, 100)),
        "player": ((70, 140, 220), (40, 90, 160)),
        "ai": ((220, 70, 70), (140, 40, 40)),
    }
    roof, wall = colors[owner]
    img = Image.new("RGBA", (48, 48), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    # base platform
    d.polygon([(24, 36), (40, 28), (24, 20), (8, 28)], fill=(90, 80, 60, 255))
    # main building
    d.rectangle([14, 14, 34, 30], fill=wall)
    d.polygon([(14, 14), (24, 6), (34, 14)], fill=roof)
    # windows
    for wx, wy in [(17, 18), (23, 18), (29, 18), (17, 24), (29, 24)]:
        d.rectangle([wx, wy, wx + 3, wy + 3], fill=(255, 230, 140, 255))
    # flag
    d.line([(24, 6), (24, 0)], fill=(40, 40, 40, 255))
    d.polygon([(24, 0), (32, 2), (24, 5)], fill=roof)
    # small side building
    d.rectangle([8, 22, 14, 30], fill=shade(wall, 0.85))
    d.polygon([(8, 22), (11, 18), (14, 22)], fill=shade(roof, 0.9))
    img.save(os.path.join(OUT, "tiles", f"city_{owner}.png"))
    print("city", owner)

def unit_base(w, h, body_color, outline):
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    return img, d

def make_army():
    img, d = unit_base(32, 32, None, None)
    # soldier silhouette
    d.ellipse([12, 4, 20, 12], fill=(50, 90, 50, 255))  # helmet
    d.rectangle([11, 11, 21, 22], fill=(60, 100, 60, 255))  # body
    d.rectangle([8, 13, 11, 20], fill=(70, 110, 70, 255))  # arm
    d.rectangle([21, 13, 24, 18], fill=(180, 160, 80, 255))  # rifle
    d.rectangle([12, 22, 15, 30], fill=(40, 40, 40, 255))
    d.rectangle([17, 22, 20, 30], fill=(40, 40, 40, 255))
    d.ellipse([13, 6, 19, 11], fill=(200, 170, 130, 255))  # face
    img.save(os.path.join(OUT, "units", "army.png"))
    # AI tinted version via red overlay badge
    img2 = img.copy()
    d2 = ImageDraw.Draw(img2)
    d2.rectangle([2, 2, 8, 8], fill=(200, 40, 40, 220))
    img2.save(os.path.join(OUT, "units", "army_ai.png"))
    print("army")

def make_fighter():
    img, d = unit_base(40, 28, None, None)
    # plane top-down-ish iso
    d.polygon([(8, 14), (28, 10), (36, 14), (28, 18)], fill=(180, 190, 200, 255))  # fuselage
    d.polygon([(16, 6), (22, 14), (16, 22), (10, 14)], fill=(100, 120, 150, 255))  # wings
    d.polygon([(30, 12), (36, 10), (36, 18), (30, 16)], fill=(80, 90, 110, 255))  # tail
    d.ellipse([24, 11, 30, 17], fill=(60, 80, 120, 255))  # cockpit
    img.save(os.path.join(OUT, "units", "fighter.png"))
    img2 = img.copy(); ImageDraw.Draw(img2).rectangle([2,2,8,8], fill=(200,40,40,220))
    img2.save(os.path.join(OUT, "units", "fighter_ai.png"))
    print("fighter")

def make_ship(name, length, color, extras=None):
    img = Image.new("RGBA", (48, 28), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    # hull diamond-ish
    d.polygon([(4, 16), (12, 8), (12 + length, 8), (8 + length, 16), (12 + length, 22), (12, 22)], fill=color)
    d.polygon([(12, 8), (12 + length, 8), (8 + length, 16), (4, 16)], fill=shade(color, 1.2))
    # bridge
    bx = 14 + length // 3
    d.rectangle([bx, 4, bx + 8, 10], fill=shade(color, 0.7))
    d.rectangle([bx + 2, 2, bx + 6, 4], fill=(40, 40, 40, 255))
    if extras == "guns":
        for gx in [16, 22, 28]:
            d.rectangle([gx, 10, gx + 2, 14], fill=(30, 30, 30, 255))
            d.line([(gx + 1, 10), (gx + 6, 8)], fill=(20, 20, 20, 255), width=2)
    elif extras == "carrier":
        d.rectangle([14, 10, 14 + length - 4, 14], fill=(60, 60, 70, 255))
        d.line([(16, 12), (14 + length - 6, 12)], fill=(220, 200, 80, 255))
    elif extras == "transport":
        for i in range(3):
            d.rectangle([16 + i * 6, 10, 20 + i * 6, 16], fill=(140, 120, 90, 255))
    elif extras == "sub":
        # redraw as submarine
        img = Image.new("RGBA", (48, 24), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        d.ellipse([4, 8, 40, 20], fill=(50, 70, 60, 255))
        d.rectangle([18, 4, 26, 10], fill=(40, 55, 50, 255))
        d.line([(22, 4), (22, 0)], fill=(30, 30, 30, 255))
        d.ellipse([36, 10, 44, 16], fill=(40, 55, 45, 255))
    img.save(os.path.join(OUT, "units", f"{name}.png"))
    img2 = img.copy(); ImageDraw.Draw(img2).rectangle([2,2,8,8], fill=(200,40,40,220))
    img2.save(os.path.join(OUT, "units", f"{name}_ai.png"))
    print(name)

def make_ui_icons():
    ensure(os.path.join(OUT, "ui"))
    # end turn button bg
    for name, col in [("btn", (70, 55, 30)), ("btn_hover", (110, 90, 40)), ("panel", (40, 32, 20))]:
        img = Image.new("RGBA", (64, 32), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        d.rounded_rectangle([0, 0, 63, 31], radius=4, fill=col + (230,), outline=(200, 170, 80, 255))
        img.save(os.path.join(OUT, "ui", f"{name}.png"))
    # production icons (small)
    for uname in ["army", "fighter", "destroyer", "submarine", "transport", "carrier", "battleship"]:
        src = Image.open(os.path.join(OUT, "units", f"{uname}.png"))
        src.thumbnail((24, 24))
        frame = Image.new("RGBA", (28, 28), (0, 0, 0, 0))
        d = ImageDraw.Draw(frame)
        d.rounded_rectangle([0, 0, 27, 27], radius=3, fill=(50, 40, 25, 220), outline=(200, 170, 80, 255))
        frame.paste(src, (2, 2), src)
        frame.save(os.path.join(OUT, "ui", f"prod_{uname}.png"))
    print("ui")

def main():
    ensure(os.path.join(OUT, "tiles"))
    ensure(os.path.join(OUT, "units"))
    ensure(os.path.join(OUT, "ui"))
    grass = (72, 140, 60, 255)
    plains = (160, 150, 70, 255)
    ocean = (40, 80, 160, 255)
    forest_base = (50, 110, 45, 255)
    hills_base = (130, 110, 70, 255)
    make_tile("ocean", ocean, 1.1, 0.7, dither="water")
    make_tile("grass", grass, 1.12, 0.75, dither="grass")
    make_tile("plains", plains, 1.1, 0.78, dither="plains")
    make_tile("forest", forest_base, 1.05, 0.7, dither="grass", overlay="forest")
    make_tile("hills", hills_base, 1.08, 0.72, overlay="hills")
    for edge in ["N", "S", "E", "W", "NE", "NW", "SE", "SW", "NS", "EW"]:
        make_coast_variant(f"coast_{edge}", grass, ocean, edge)
    make_fog()
    for o in ["neutral", "player", "ai"]:
        make_city(o)
    make_army()
    make_fighter()
    make_ship("destroyer", 18, (70, 90, 110, 255), "guns")
    make_ship("submarine", 16, (50, 70, 60, 255), "sub")
    make_ship("transport", 20, (120, 100, 70, 255), "transport")
    make_ship("carrier", 24, (80, 90, 100, 255), "carrier")
    make_ship("battleship", 26, (55, 65, 80, 255), "guns")
    make_ui_icons()
    print("DONE")

if __name__ == "__main__":
    main()
