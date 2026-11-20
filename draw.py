#!/usr/bin/env python3
"""Draw the one-page newspaper for Thursday 19 November 2026.

Renders entry.png (1024x1024, <=1 MiB) with Pillow only. All illustrations
are original vector-style drawings made in code; the world map comes from
Natural Earth 110m land polygons (public domain, world-atlas).
Deterministic: same input -> same bytes.
"""
import json
import math
import os
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
W, H = 1024, 1024

# ---------- palette ----------
NAVY = (20, 33, 61)
NAVY2 = (32, 50, 92)
NAVY3 = (48, 68, 116)
RED = (200, 16, 46)
RED_DK = (150, 10, 32)
PAPER = (253, 252, 246)
INK = (24, 24, 24)
GRAY = (96, 96, 96)
GRAY_LT = (178, 178, 178)
TEAL = (14, 124, 123)
AMBER = (224, 148, 24)
BLUE = (31, 111, 178)
GREEN = (46, 125, 50)
OCHRE = (196, 122, 18)
PURPLE = (123, 75, 148)
SKY = (214, 232, 240)
LAND = (226, 216, 188)
LAND_EDGE = (190, 176, 140)

REGION_COLORS = {
    "ASIA": BLUE, "EUROPE": GREEN, "MIDDLE EAST": OCHRE, "AFRICA": PURPLE,
    "AMERICAS": RED, "OCEANIA": TEAL, "GLOBAL": GRAY,
}

F_DIR = "/usr/share/fonts/truetype/dejavu"
F_SERIF = os.path.join(F_DIR, "DejaVuSerif.ttf")
F_SERIF_B = os.path.join(F_DIR, "DejaVuSerif-Bold.ttf")
F_SANS = os.path.join(F_DIR, "DejaVuSans.ttf")
F_SANS_B = os.path.join(F_DIR, "DejaVuSans-Bold.ttf")
F_SERIF_I = "/usr/share/fonts/truetype/liberation/LiberationSerif-Italic.ttf"


def font(path, size):
    return ImageFont.truetype(path, size)


def wrap(draw, text, fnt, max_w):
    """Greedy word wrap; returns list of lines."""
    words = text.split()
    lines, cur = [], ""
    for w in words:
        trial = (cur + " " + w).strip()
        if draw.textlength(trial, font=fnt) <= max_w or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def draw_text_block(draw, x, y, text, fnt, max_w, fill, leading=None, max_lines=None):
    lines = wrap(draw, text, fnt, max_w)
    if max_lines:
        lines = lines[:max_lines]
    lh = leading or int(fnt.size * 1.28)
    for ln in lines:
        draw.text((x, y), ln, font=fnt, fill=fill)
        y += lh
    return y


def badge(draw, x, y, text, fill, fg=(255, 255, 255), size=8):
    """Small rounded tag; returns width used."""
    f = font(F_SANS_B, size)
    w = int(draw.textlength(text, font=f)) + 10
    h = size + 6
    draw.rounded_rectangle([x, y, x + w, y + h], radius=3, fill=fill)
    draw.text((x + 5, y + 2), text, font=f, fill=fg)
    return w


def num_circle(draw, cx, cy, n, r=9, fill=RED, fg=(255, 255, 255)):
    draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=fill)
    f = font(F_SANS_B, 10 if n < 10 else 9)
    t = str(n)
    tw = draw.textlength(t, font=f)
    draw.text((cx - tw / 2, cy - f.size / 2 - 1), t, font=f, fill=fg)


# ---------- world map (Natural Earth 110m, TopoJSON) ----------
def load_land():
    path = os.path.join(HERE, "land-110m.json")
    if not os.path.exists(path):
        path = "/tmp/land-110m.json"
    with open(path) as fh:
        topo = json.load(fh)
    scale = topo["transform"]["scale"]
    trans = topo["transform"]["translate"]
    arcs = []
    for arc in topo["arcs"]:
        pts, x, y = [], 0, 0
        for dx, dy in arc:
            x += dx
            y += dy
            pts.append((x * scale[0] + trans[0], y * scale[1] + trans[1]))
        arcs.append(pts)
    polys = []

    def arc_pts(i):
        return arcs[i] if i >= 0 else list(reversed(arcs[~i]))

    def rings_to_polys(rings):
        out = []
        for ring in rings:
            pts = []
            for ai in ring:
                seg = arc_pts(ai)
                pts.extend(seg if not pts else seg[1:])
            out.append(pts)
        return out

    geom = topo["objects"]["land"]["geometries"][0]
    if geom["type"] == "MultiPolygon":
        for poly in geom["arcs"]:
            polys.extend(rings_to_polys(poly))
    else:
        polys.extend(rings_to_polys(geom["arcs"]))
    return polys


LAND_POLYS = load_land()


def project(lon, lat, box):
    """Equirectangular projection into box (x0, y0, x1, y1)."""
    x0, y0, x1, y1 = box
    lon_min, lon_max = -168.0, 192.0
    lat_min, lat_max = -58.0, 84.0
    px = x0 + (lon - lon_min) / (lon_max - lon_min) * (x1 - x0)
    py = y1 - (lat - lat_min) / (lat_max - lat_min) * (y1 - y0)
    return px, py


def draw_map(draw, box, pins):
    """Draw ocean, land, and numbered pins. pins: list of (lon, lat, n)."""
    x0, y0, x1, y1 = box
    draw.rectangle(box, fill=SKY, outline=NAVY, width=1)
    for poly in LAND_POLYS:
        pts = [project(lon, lat, box) for lon, lat in poly]
        # split polygons that wrap the antimeridian
        clean = [pts[0]]
        for p in pts[1:]:
            if abs(p[0] - clean[-1][0]) > (x1 - x0) * 0.5:
                if len(clean) > 2:
                    draw.polygon(clean, fill=LAND, outline=LAND_EDGE)
                clean = [p]
            else:
                clean.append(p)
        if len(clean) > 2:
            draw.polygon(clean, fill=LAND, outline=LAND_EDGE)
    for lon, lat, n in pins:
        px, py = project(lon, lat, box)
        num_circle(draw, px, py, n, r=8)


# ---------- illustration helpers ----------
def flag_us(draw, x, y, w, h):
    draw.rectangle([x, y, x + w, y + h], fill=(255, 255, 255), outline=NAVY)
    stripe = h / 13
    for i in range(0, 13, 2):
        draw.rectangle([x, y + i * stripe, x + w, y + (i + 1) * stripe], fill=(178, 34, 52))
    draw.rectangle([x, y, x + w * 0.4, y + stripe * 7], fill=(60, 59, 110))


def flag_cn(draw, x, y, w, h):
    draw.rectangle([x, y, x + w, y + h], fill=(222, 41, 16), outline=NAVY)
    cx, cy, r = x + w * 0.22, y + h * 0.28, h * 0.18
    star(draw, cx, cy, r, (255, 222, 0))


def flag_ru(draw, x, y, w, h):
    draw.rectangle([x, y, x + w, y + h], fill=(255, 255, 255), outline=NAVY)
    draw.rectangle([x, y + h / 3, x + w, y + 2 * h / 3], fill=(0, 57, 166))
    draw.rectangle([x, y + 2 * h / 3, x + w, y + h], fill=(213, 0, 50))


def flag_dk(draw, x, y, w, h):
    draw.rectangle([x, y, x + w, y + h], fill=(198, 12, 48), outline=NAVY)
    draw.rectangle([x + w * 0.28, y, x + w * 0.42, y + h], fill=(255, 255, 255))
    draw.rectangle([x, y + h * 0.4, x + w, y + h * 0.6], fill=(255, 255, 255))


def flag_kr(draw, x, y, w, h):
    draw.rectangle([x, y, x + w, y + h], fill=(255, 255, 255), outline=NAVY)
    cx, cy, r = x + w / 2, y + h / 2, h * 0.28
    draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(205, 0, 58))
    draw.pieslice([cx - r, cy - r, cx + r, cy + r], 180, 360, fill=(0, 56, 147))


def flag_so(draw, x, y, w, h):
    draw.rectangle([x, y, x + w, y + h], fill=(65, 137, 221), outline=NAVY)
    star(draw, x + w / 2, y + h / 2, h * 0.32, (255, 255, 255))


def flag_ae(draw, x, y, w, h):
    draw.rectangle([x, y, x + w, y + h], fill=(255, 255, 255), outline=NAVY)
    draw.rectangle([x, y, x + w * 0.25, y + h], fill=(255, 0, 0))
    draw.rectangle([x + w * 0.25, y, x + w, y + h / 3], fill=(0, 122, 61))
    draw.rectangle([x + w * 0.25, y + 2 * h / 3, x + w, y + h], fill=(0, 0, 0))


def flag_co(draw, x, y, w, h):
    draw.rectangle([x, y, x + w, y + h], fill=(252, 209, 22), outline=NAVY)
    draw.rectangle([x, y + h / 2, x + w, y + 3 * h / 4], fill=(0, 56, 147))
    draw.rectangle([x, y + 3 * h / 4, x + w, y + h], fill=(206, 17, 38))


def flag_ua(draw, x, y, w, h):
    draw.rectangle([x, y, x + w, y + h / 2], fill=(0, 91, 187), outline=NAVY)
    draw.rectangle([x, y + h / 2, x + w, y + h], fill=(255, 213, 0))


def flag_au(draw, x, y, w, h):
    draw.rectangle([x, y, x + w, y + h], fill=(0, 36, 125), outline=NAVY)
    draw.rectangle([x, y, x + w * 0.5, y + h * 0.5], fill=(198, 12, 48))
    star(draw, x + w * 0.72, y + h * 0.3, h * 0.16, (255, 255, 255))
    star(draw, x + w * 0.78, y + h * 0.68, h * 0.12, (255, 255, 255))


def star(draw, cx, cy, r, fill):
    pts = []
    for i in range(10):
        ang = -math.pi / 2 + i * math.pi / 5
        rr = r if i % 2 == 0 else r * 0.42
        pts.append((cx + rr * math.cos(ang), cy + rr * math.sin(ang)))
    draw.polygon(pts, fill=fill)


def person(draw, x, y, w, h, suit, skin=(232, 190, 150), hair=(60, 50, 40)):
    """Simple seated figure: head + shoulders + suit."""
    hr = w * 0.26
    cx = x + w / 2
    draw.ellipse([cx - hr, y, cx + hr, y + 2 * hr], fill=skin)
    draw.pieslice([cx - hr, y, cx + hr, y + 2 * hr], 180, 360, fill=hair)
    draw.rounded_rectangle([x, y + 2 * hr * 0.92, x + w, y + h], radius=6, fill=suit)
    draw.polygon([(cx - 5, y + 2 * hr * 0.95), (cx + 5, y + 2 * hr * 0.95),
                  (cx, y + 2 * hr * 0.95 + 14)], fill=(255, 255, 255))
    draw.polygon([(cx - 3, y + 2 * hr * 0.95 + 4), (cx + 3, y + 2 * hr * 0.95 + 4),
                  (cx + 2, y + 2 * hr * 0.95 + 20), (cx - 2, y + 2 * hr * 0.95 + 20)],
                 fill=RED)


def explosion(draw, cx, cy, r, fill=(255, 176, 0)):
    pts = []
    for i in range(16):
        ang = -math.pi / 2 + i * math.pi / 8
        rr = r if i % 2 == 0 else r * 0.45
        pts.append((cx + rr * math.cos(ang), cy + rr * math.sin(ang)))
    draw.polygon(pts, fill=fill, outline=(200, 60, 0))
    draw.ellipse([cx - r * 0.35, cy - r * 0.35, cx + r * 0.35, cy + r * 0.35],
                 fill=(255, 240, 200))


# ---------- illustrations (each draws inside box x0,y0,x1,y1) ----------
def ill_summit(draw, x0, y0, x1, y1):
    draw.rectangle([x0, y0, x1, y1], fill=(232, 236, 244))
    # skyline
    draw.rectangle([x0, y0, x1, y0 + (y1 - y0) * 0.42], fill=NAVY2)
    for i, bh in enumerate([46, 68, 54, 76, 62, 72, 50]):
        bx = x0 + 14 + i * ((x1 - x0 - 28) / 7)
        bw = (x1 - x0 - 28) / 7 - 8
        by = y0 + (y1 - y0) * 0.42
        draw.rectangle([bx, by - bh, bx + bw, by], fill=NAVY3)
        for wy in range(int(by - bh + 6), int(by - 4), 10):
            for wx in range(int(bx + 4), int(bx + bw - 4), 9):
                draw.rectangle([wx, wy, wx + 4, wy + 5], fill=(255, 214, 120))
    # flags row
    fw, fh = 74, 44
    flag_us(draw, x0 + 52, y0 + 8, fw, fh)
    flag_cn(draw, x0 + (x1 - x0) // 2 - fw // 2, y0 + 8, fw, fh)
    flag_ru(draw, x1 - 52 - fw, y0 + 8, fw, fh)
    # table + figures
    ty = y0 + (y1 - y0) * 0.52
    person(draw, x0 + 46, ty - 58, 92, 88, (30, 42, 74), hair=(220, 210, 180))
    person(draw, x0 + (x1 - x0) // 2 - 46, ty - 58, 92, 88, (24, 24, 24))
    person(draw, x1 - 138, ty - 58, 92, 88, (52, 32, 32), hair=(200, 200, 200))
    draw.rectangle([x0 + 18, ty + 30, x1 - 18, ty + 46], fill=(122, 84, 52))
    draw.rectangle([x0 + 18, ty + 30, x1 - 18, ty + 36], fill=(150, 106, 66))
    # name plates
    f = font(F_SANS_B, 13)
    for cx, name in [(x0 + 92, "TRUMP"), (x0 + (x1 - x0) // 2, "XI"),
                     (x1 - 92, "PUTIN")]:
        tw = draw.textlength(name, font=f)
        draw.rectangle([cx - tw / 2 - 8, ty + 48, cx + tw / 2 + 8, ty + 66],
                       fill=(255, 255, 255), outline=NAVY)
        draw.text((cx - tw / 2, ty + 51), name, font=f, fill=NAVY)
    # banner
    bf = font(F_SANS_B, 12)
    bt = "APEC 2026 · SHENZHEN · FIRST US–CHINA–RUSSIA SUMMIT"
    tw = draw.textlength(bt, font=bf)
    draw.rectangle([x0 + (x1 - x0) // 2 - tw / 2 - 10, y1 - 20,
                    x0 + (x1 - x0) // 2 + tw / 2 + 10, y1 - 2], fill=RED)
    draw.text((x0 + (x1 - x0) // 2 - tw / 2, y1 - 17), bt, font=bf, fill=(255, 255, 255))


def ill_icj(draw, x0, y0, x1, y1):
    draw.rectangle([x0, y0, x1, y1], fill=(222, 232, 240))
    # Peace Palace: brick hall + tower (sized to stay inside the box)
    bx0, by1 = x0 + 14, y1 - 12
    bw, bh = (x1 - x0) * 0.5, 40
    draw.rectangle([bx0, by1 - bh, bx0 + bw, by1], fill=(164, 94, 70))
    draw.polygon([(bx0 - 4, by1 - bh), (bx0 + bw / 2, by1 - bh - 14),
                  (bx0 + bw + 4, by1 - bh)], fill=(120, 60, 44))
    draw.rectangle([bx0 + bw * 0.7, by1 - bh - 22, bx0 + bw * 0.88, by1],
                   fill=(140, 78, 58))
    draw.polygon([(bx0 + bw * 0.66, by1 - bh - 22), (bx0 + bw * 0.79, by1 - bh - 34),
                  (bx0 + bw * 0.92, by1 - bh - 22)], fill=(90, 45, 34))
    for i in range(5):
        wx = bx0 + 8 + i * (bw - 16) / 5
        draw.rectangle([wx, by1 - 20, wx + (bw - 16) / 5 - 6, by1 - 6],
                       fill=(255, 240, 200))
    # scales
    sx = x1 - 52
    sy = y0 + 14
    draw.line([sx, sy, sx, sy + 40], fill=(120, 90, 20), width=3)
    draw.line([sx - 26, sy + 6, sx + 26, sy + 6], fill=(120, 90, 20), width=3)
    for dx in (-26, 26):
        draw.line([sx + dx, sy + 6, sx + dx - 10, sy + 24], fill=(120, 90, 20), width=2)
        draw.line([sx + dx, sy + 6, sx + dx + 10, sy + 24], fill=(120, 90, 20), width=2)
        draw.arc([sx + dx - 12, sy + 20, sx + dx + 12, sy + 34], 0, 180,
                 fill=(120, 90, 20), width=2)
    # 9-6 vote badge
    f = font(F_SANS_B, 20)
    draw.rectangle([x1 - 66, y1 - 34, x1 - 8, y1 - 8], fill=RED)
    draw.text((x1 - 56, y1 - 32), "9–6", font=f, fill=(255, 255, 255))


def ill_cop(draw, x0, y0, x1, y1):
    draw.rectangle([x0, y0, x1, y1], fill=(16, 84, 84))
    # globe (left)
    cx, cy, r = x0 + 42, y0 + (y1 - y0) // 2, 30
    draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(64, 160, 220),
                 outline=(255, 255, 255), width=2)
    draw.ellipse([cx - r * 0.5, cy - r * 0.6, cx + r * 0.3, cy + r * 0.1], fill=(80, 180, 100))
    draw.ellipse([cx - r * 0.2, cy + r * 0.2, cx + r * 0.7, cy + r * 0.7], fill=(80, 180, 100))
    # crossed-out text (right of globe)
    tx0 = x0 + 82
    f = font(F_SANS_B, 14)
    t1 = "FOSSIL FUELS"
    ty = y0 + 20
    draw.text((tx0, ty), t1, font=f, fill=(255, 255, 255))
    tw = draw.textlength(t1, font=f)
    draw.line([tx0 - 3, ty + 9, tx0 + tw + 3, ty + 9], fill=RED, width=4)
    f2 = font(F_SANS_B, 11)
    t2 = "$120bn AID"
    draw.text((tx0, ty + 24), t2, font=f2, fill=(255, 214, 120))
    tw2 = draw.textlength(t2, font=f2)
    draw.line([tx0 - 3, ty + 32, tx0 + tw2 + 3, ty + 32], fill=RED, width=3)
    f2b = font(F_SANS_B, 11)
    draw.text((tx0, ty + 40), "144 → 80 PARAS", font=f2b, fill=(255, 255, 255))
    # CUT stamp bottom-right
    f3 = font(F_SANS_B, 14)
    draw.rectangle([x1 - 56, y1 - 28, x1 - 8, y1 - 8], outline=(255, 120, 120), width=2)
    draw.text((x1 - 48, y1 - 26), "CUT", font=f3, fill=(255, 120, 120))


def ill_anthropic(draw, x0, y0, x1, y1):
    draw.rectangle([x0, y0, x1, y1], fill=(12, 32, 24))
    # header line
    f = font(F_SANS_B, 18)
    draw.text((x0 + 10, y0 + 5), "ANT", font=f, fill=(255, 255, 255))
    f2 = font(F_SANS_B, 10)
    draw.text((x0 + 54, y0 + 10), "NASDAQ · FIRST DAY", font=f2, fill=(160, 220, 180))
    # candlesticks rising (middle band)
    base = y1 - 22
    tops = [46, 42, 44, 36, 32, 28, 24]
    for i, t in enumerate(tops):
        cx = x0 + 16 + i * ((x1 - x0 - 32) // 7)
        col = (60, 200, 120) if i % 2 == 0 else (220, 70, 70)
        draw.rectangle([cx - 5, y0 + t, cx + 5, base - 2], fill=col)
        draw.line([cx, y0 + t - 6, cx, base + 2], fill=col, width=2)
    # trend line
    pts = [(x0 + 14 + i * ((x1 - x0 - 28) // 6), y0 + 44 - i * 3) for i in range(7)]
    draw.line(pts, fill=(255, 214, 120), width=2)
    # bottom line: price + gain
    f4 = font(F_SANS_B, 11)
    draw.text((x0 + 10, y1 - 18), "$83 → $97.17", font=f4, fill=(255, 255, 255))
    f3 = font(F_SANS_B, 15)
    t3 = "+17%"
    draw.text((x1 - 10 - draw.textlength(t3, font=f3), y1 - 20), t3, font=f3,
              fill=(60, 220, 130))


def ill_gta(draw, x0, y0, x1, y1):
    # sunset Vice City
    for i in range(y1 - y0):
        t = i / (y1 - y0)
        r = int(120 + 100 * t)
        g = int(40 + 60 * t)
        b = int(140 - 60 * t)
        draw.line([(x0, y0 + i), (x1, y0 + i)], fill=(r, g, b))
    # sun (right side, clear of the VI tag)
    cx, cy = x0 + int((x1 - x0) * 0.72), y0 + 32
    draw.ellipse([cx - 24, cy - 24, cx + 24, cy + 24], fill=(255, 200, 90))
    # skyline
    base = y1 - 14
    for i, bh in enumerate([34, 52, 40, 66, 46, 58, 38]):
        bx = x0 + 8 + i * ((x1 - x0 - 16) / 7)
        bw = (x1 - x0 - 16) / 7 - 4
        draw.rectangle([bx, base - bh, bx + bw, base], fill=(30, 16, 48))
        for wy in range(int(base - bh + 5), int(base - 4), 9):
            for wx in range(int(bx + 3), int(bx + bw - 3), 8):
                draw.rectangle([wx, wy, wx + 3, wy + 4], fill=(255, 220, 130))
    # road + car
    draw.rectangle([x0, base, x1, y1], fill=(20, 20, 30))
    carx, cary = x0 + (x1 - x0) // 2 - 34, y1 - 12
    draw.rounded_rectangle([carx, cary - 8, carx + 68, cary + 2], radius=4, fill=(255, 60, 120))
    draw.rounded_rectangle([carx + 14, cary - 16, carx + 50, cary - 6], radius=4,
                           fill=(255, 60, 120))
    draw.ellipse([carx + 8, cary - 2, carx + 20, cary + 8], fill=(10, 10, 10))
    draw.ellipse([carx + 48, cary - 2, carx + 60, cary + 8], fill=(10, 10, 10))
    # VI logo + tag on a dark strip
    draw.rectangle([x0, y0, x0 + 118, y0 + 20], fill=(20, 10, 30))
    f = font(F_SERIF_B, 16)
    draw.text((x0 + 8, y0 + 1), "VI", font=f, fill=(255, 255, 255))
    f2 = font(F_SANS_B, 9)
    draw.text((x0 + 38, y0 + 5), "OUT NOW · 13 YRS ON", font=f2, fill=(255, 200, 90))


def ill_cyclone(draw, x0, y0, x1, y1):
    draw.rectangle([x0, y0, x1, y1], fill=(200, 224, 240))
    # spiral
    cx, cy = x0 + (x1 - x0) // 2, y0 + (y1 - y0) // 2 + 4
    for k in range(3):
        r = 30 - k * 9
        draw.arc([cx - r, cy - r, cx + r, cy + r], 20 + k * 120, 300 + k * 120,
                 fill=(20, 80, 160), width=5)
    draw.ellipse([cx - 7, cy - 7, cx + 7, cy + 7], fill=(255, 255, 255),
                 outline=(20, 80, 160), width=2)
    # rain slashes
    for i in range(8):
        rx = x0 + 8 + i * 11
        draw.line([rx, y0 + 6, rx - 5, y0 + 16], fill=(90, 140, 200), width=2)
    f = font(F_SANS_B, 10)
    draw.text((x0 + 6, y0 + 3), "AKVAN", font=f, fill=NAVY)


def ill_bridge(draw, x0, y0, x1, y1):
    draw.rectangle([x0, y0, x1, y1], fill=(214, 228, 240))
    # sea
    draw.rectangle([x0, y1 - 26, x1, y1], fill=(70, 130, 190))
    # bridge deck + arch
    deck = y1 - 40
    draw.rectangle([x0, deck, x1, deck + 8], fill=(120, 120, 120))
    draw.arc([x0 + 8, deck - 34, x1 - 8, deck + 30], 180, 360, fill=(90, 90, 90),
             width=4)
    for px in range(int(x0 + 16), int(x1 - 8), 18):
        draw.line([px, deck - 8, px, deck], fill=(90, 90, 90), width=2)
    # supports
    for px in (x0 + 22, x0 + (x1 - x0) // 2, x1 - 22):
        draw.rectangle([px - 3, deck + 8, px + 3, y1 - 26], fill=(90, 90, 90))
    # explosion on deck
    explosion(draw, x0 + (x1 - x0) * 0.68, deck - 12, 16)
    f2 = font(F_SANS_B, 9)
    draw.text((x0 + 6, y1 - 13), "RAIL HALTED", font=f2, fill=(255, 255, 255))


def ill_riyadh(draw, x0, y0, x1, y1):
    draw.rectangle([x0, y0, x1, y1], fill=(16, 24, 48))
    # skyline night
    base = y1 - 10
    for i, bh in enumerate([26, 44, 34, 58, 40, 30]):
        bx = x0 + 6 + i * ((x1 - x0 - 12) / 6)
        bw = (x1 - x0 - 12) / 6 - 4
        draw.rectangle([bx, base - bh, bx + bw, base], fill=(48, 60, 96))
        for wy in range(int(base - bh + 4), int(base - 3), 8):
            for wx in range(int(bx + 3), int(bx + bw - 3), 7):
                draw.rectangle([wx, wy, wx + 3, wy + 3], fill=(255, 210, 110))
    # missile trail + intercept burst
    draw.line([x0 + 12, y0 + 8, x0 + (x1 - x0) * 0.6, y0 + 30], fill=(255, 180, 80),
              width=2)
    explosion(draw, x0 + (x1 - x0) * 0.62, y0 + 32, 13)
    draw.line([x1 - 14, y1 - 14, x0 + (x1 - x0) * 0.62, y0 + 32], fill=(255, 255, 255),
              width=1)
    f2 = font(F_SANS_B, 9)
    draw.text((x0 + 6, y1 - 13), "INTERCEPTED", font=f2, fill=(255, 210, 110))


def ill_greenland(draw, x0, y0, x1, y1):
    draw.rectangle([x0, y0, x1, y1], fill=(190, 220, 235))
    draw.rectangle([x0, y1 - 22, x1, y1], fill=(90, 150, 200))
    # icebergs
    draw.polygon([(x0 + 8, y1 - 22), (x0 + 30, y0 + 26), (x0 + 52, y1 - 22)],
                 fill=(255, 255, 255), outline=(140, 180, 210))
    draw.polygon([(x0 + 44, y1 - 22), (x0 + 66, y0 + 40), (x0 + 88, y1 - 22)],
                 fill=(235, 245, 250), outline=(140, 180, 210))
    flag_dk(draw, x1 - 46, y0 + 8, 34, 22)
    flag_us(draw, x1 - 46, y0 + 34, 34, 22)
    f = font(F_SANS_B, 13)
    draw.text((x0 + 6, y0 + 4), "109–0", font=f, fill=RED)


def ill_jobs(draw, x0, y0, x1, y1):
    draw.rectangle([x0, y0, x1, y1], fill=(24, 44, 84))
    # bars 4.7 -> 4.9
    base = y1 - 16
    draw.rectangle([x0 + 18, base - 26, x0 + 38, base], fill=(120, 170, 220))
    draw.rectangle([x0 + 46, base - 40, x0 + 66, base], fill=(255, 90, 90))
    f = font(F_SANS_B, 10)
    draw.text((x0 + 18, base - 40), "4.7%", font=f, fill=(200, 220, 240))
    draw.text((x0 + 46, base - 54), "4.9%", font=f, fill=(255, 255, 255))
    # rising arrow
    draw.line([(x0 + 76, y1 - 30), (x1 - 14, y0 + 22)], fill=(255, 90, 90), width=3)
    draw.polygon([(x1 - 14, y0 + 22), (x1 - 26, y0 + 24), (x1 - 16, y0 + 34)],
                 fill=(255, 90, 90))
    f2 = font(F_SANS_B, 9)
    draw.text((x0 + 6, y1 - 13), "SINCE 2021", font=f2, fill=(200, 220, 240))


def ill_suneung(draw, x0, y0, x1, y1):
    draw.rectangle([x0, y0, x1, y1], fill=(240, 232, 210))
    # desks + students
    for i, dx in enumerate([14, 52, 90]):
        draw.ellipse([x0 + dx + 8, y0 + 22, x0 + dx + 24, y0 + 38], fill=(232, 190, 150))
        draw.rectangle([x0 + dx, y0 + 38, x0 + dx + 32, y0 + 56], fill=(70, 90, 140))
        draw.rectangle([x0 + dx - 4, y0 + 56, x0 + dx + 36, y0 + 62], fill=(150, 110, 70))
    # clock
    cx, cy = x1 - 22, y0 + 20
    draw.ellipse([cx - 12, cy - 12, cx + 12, cy + 12], fill=(255, 255, 255),
                 outline=NAVY, width=2)
    draw.line([cx, cy, cx, cy - 8], fill=NAVY, width=2)
    draw.line([cx, cy, cx + 6, cy + 2], fill=NAVY, width=2)
    f = font(F_SANS_B, 11)
    draw.text((x0 + 6, y0 + 3), "551,864", font=f, fill=NAVY)


def ill_somalia(draw, x0, y0, x1, y1):
    draw.rectangle([x0, y0, x1, y1], fill=(220, 232, 240))
    flag_so(draw, x0 + 10, y0 + 12, 40, 26)
    flag_ae(draw, x1 - 50, y0 + 12, 40, 26)
    # plane flying away
    px, py = x1 - 30, y0 + 52
    draw.polygon([(px - 22, py), (px + 14, py - 6), (px + 22, py - 2),
                  (px + 10, py + 4), (px - 8, py + 6)], fill=(60, 60, 60))
    draw.line([x0 + 52, y0 + 30, px - 22, py], fill=(150, 150, 150), width=1)
    f = font(F_SANS_B, 11)
    draw.text((x0 + 6, y1 - 16), "72 HRS", font=f, fill=RED)


def ill_bogota(draw, x0, y0, x1, y1):
    draw.rectangle([x0, y0, x1, y1], fill=(250, 240, 210))
    # crowd
    cols = [(200, 60, 60), (40, 100, 180), (220, 160, 40), (60, 160, 90), (140, 80, 160)]
    for i in range(9):
        cx = x0 + 10 + i * ((x1 - x0 - 20) // 9)
        cy = y0 + 44 + (i % 2) * 8
        draw.ellipse([cx - 5, cy - 10, cx + 5, cy], fill=(232, 190, 150))
        draw.rectangle([cx - 7, cy, cx + 7, cy + 16], fill=cols[i % 5])
    # banner
    draw.rectangle([x0 + 6, y0 + 6, x1 - 6, y0 + 24], fill=(255, 255, 255),
                   outline=NAVY)
    f = font(F_SANS_B, 9)
    t = "PARO NACIONAL"
    tw = draw.textlength(t, font=f)
    draw.text((x0 + (x1 - x0) // 2 - tw / 2, y0 + 9), t, font=f, fill=NAVY)
    flag_co(draw, x0 + 6, y1 - 20, 26, 14)


# ---------- content ----------
NUMBERS = [
    ("3", "presidents at one table"),
    ("9–6", "World Court genocide vote"),
    ("$81.3bn", "Anthropic's record IPO"),
    ("24.6m", "GTA VI copies, day one*"),
    ("200,000+", "evacuated ahead of Akvan"),
    ("4.9%", "Australian jobless rate"),
]

REGIONS = [("ASIA", 9), ("EUROPE", 11), ("MIDDLE EAST", 4), ("AFRICA", 6),
           ("AMERICAS", 6), ("OCEANIA", 5), ("GLOBAL", 3)]

# (n, place, topic, headline, body, source, tag, illustration)
MEDIUM = [
    (2, "THE HAGUE", "LAW", "World Court: Myanmar committed genocide",
     "Judges vote 9–6 in The Gambia's case over the Rohingya — the first time "
     "the court has found a state guilty of genocide.",
     "UN News · AFP", "REPORTED", ill_icj),
    (3, "ANTALYA", "CLIMATE", "COP31 draft drops fossil fuels and $120bn aid goal",
     "The slimmed text — 144 paragraphs cut to 80 — names no fuel and no figure "
     "for adaptation aid. Talks end Friday.",
     "Reuters · AFP", "REPORTED", ill_cop),
    (4, "NEW YORK", "MARKETS", "Anthropic debuts in the biggest IPO on record",
     "Priced at $83, ANT opened at $111.50 and closed up 17% at $97.17. The "
     "$81.3bn sale tops SpaceX's record.",
     "AP · CNBC", "REPORTED", ill_anthropic),
    (5, "WORLDWIDE", "GAMES", "GTA VI goes on sale after a 13-year wait",
     "Midnight launches, New Zealand first. Sensor Tower puts day one at 24.6m "
     "copies and $2.36bn — an entertainment record.",
     "BBC · Sensor Tower", "REPORTED", ill_gta),
]

# (n, place, topic, headline, body, source, tag, illustration)
SMALL = [
    (6, "ODISHA", "STORM", "Cyclone Akvan nears India",
     "Over 200,000 moved to safety; landfall due Friday.",
     "IMD", "FORECAST", ill_cyclone),
    (7, "CRIMEA", "WAR", "Kerch Bridge hit again",
     "Third strike in a week halts trains to Russia.",
     "Euronews", "REPORTED", ill_bridge),
    (8, "RIYADH", "WAR", "Saudis down Houthi missiles",
     "Debris fell on the capital; no casualties reported.",
     "Reuters", "REPORTED", ill_riyadh),
    (9, "GREENLAND", "SECURITY", "Denmark backs Arctic pact",
     "Parliament approves the Greenland security deal 109–0.",
     "AP", "REPORTED", ill_greenland),
    (10, "CANBERRA", "ECONOMY", "Australia jobless rate 4.9%",
     "Highest since 2021; 43,500 jobs lost in October.",
     "ABS", "REPORTED", ill_jobs),
    (11, "SEOUL", "EDUCATION", "551,864 sit Suneung exam",
     "Flights pause for the listening section.",
     "Yonhap", "REPORTED", ill_suneung),
    (12, "MOGADISHU", "DIPLOMACY", "Somalia expels UAE envoy",
     "72 hours to leave; Mogadishu cites 'open invasion'.",
     "Reuters", "REPORTED", ill_somalia),
    (13, "BOGOTÁ", "LABOUR", "Colombia unions strike",
     "Marches in three cities against a rescue law.",
     "InfoBae", "REPORTED", ill_bogota),
]

# (n, place, brief, source) — numbered 14..44
BRIEFS = [
    (14, "Seoul", "Top court clears ex-PM Han Duck-soo.", "AP"),
    (15, "Jakarta", "Asset-seizure law passes after 18 years.", "Kompas"),
    (16, "Hormuz", "Iran says mines set three tankers ablaze.", "Al Jazeera"),
    (17, "Gaza", "Israel says tank raid past truce line is over.", "BBC"),
    (18, "Kyiv", "Russian drones kill one, hit two embassies.", "Kyiv Independent"),
    (19, "Berlin", "Europe seeks a winter truce; 40+ partners meet.", "Euronews"),
    (20, "Washington", "Senate rejects curb on Trump Iran powers, 48–51.", "AP"),
    (21, "Florida", "Floods shut Broward schools; 15.3 in of rain.", "CBS"),
    (22, "Seoul", "Exports top $1 trillion, a first.", "Yonhap"),
    (23, "Johannesburg", "South Africa beat Bangladesh by nine wickets.", "AP"),
    (24, "Northland, NZ", "19 sperm whales die in mass stranding.", "RNZ"),
    (25, "Nairobi", "Marathon champion Jepchirchir banned three years.", "AP"),
    (26, "Paris", "Mélenchon splits left; Le Pen leads poll 68.5–31.5.", "Euronews"),
    (27, "Rome", "Author Corrado Augias dies at 91.", "Euronews"),
    (28, "Sudan", "Court sentences absent RSF chief to death.", "AP"),
    (29, "Pretoria", "Central bank holds rate at 7.25%.", "SABC"),
    (30, "Wellington", "Court: pay-equity cuts broke rights law.", "RNZ"),
    (31, "Tonga", "Drought emergency takes effect.", "RNZ"),
    (32, "Cook Islands", "Cyclone Xavier weakens to category 4.", "RNZ"),
    (33, "Dhaka", "Yunus home ablaze, two killed.", "Reuters"),
    (34, "Ulaanbaatar", "MPs accept president's resignation, 96–104.", "Reuters"),
    (35, "Mumbai", "Sensex up 990 points to 82,021.75.", "Reuters"),
    (36, "Paris", "IEA: Hormuz is 'the largest energy supply shock'.", "IEA"),
    (37, "Madrid", "Sánchez and Feijóo clash in only TV debate.", "Reuters"),
    (38, "Doha", "U-17 World Cup: France 3–1 Senegal.", "Reuters"),
    (39, "Minsk", "Russia and Georgia hold first talks since 2008.", "Reuters"),
    (40, "Brussels", "EU delays methane rules two years.", "Euronews"),
    (41, "Zurich", "Two rivals to challenge FIFA's Infantino.", "ABC"),
    (42, "Canaries", "Record 11,000 migrants in 15 days.", "Euronews"),
    (43, "El Salvador", "Bukele files to run for a third term.", "Reuters"),
    (44, "Haiti", "Police say 34 gang suspects killed in raid.", "AP"),
]

MAP_PINS = [
    (114.1, 22.5, 1), (4.3, 52.1, 2), (30.7, 36.9, 3), (-74.0, 40.7, 4),
    (85.8, 20.3, 6), (34.1, 45.0, 7), (46.7, 24.7, 8), (-42.0, 72.0, 9),
    (149.1, -35.3, 10), (127.0, 37.5, 11), (45.3, 2.0, 12), (-74.1, 4.7, 13),
]

DATE_CHECK = ("DATE CHECK — Left out on purpose, first reported on other days: "
              "EU's €45bn Ukraine loan plan (18 Nov) · Iran fires on Kuwait and Bahrain "
              "(18 Nov) · Nvidia results (17 Nov) · Jeffries named for US speaker (18 Nov) · "
              "Van Gogh's $190.4m sale (18 Nov) · Voyager 1 one light-day out (18 Nov) · "
              "Deutsche Bank–Epstein files (17 Nov) · $83 Anthropic IPO price (18 Nov) · "
              "COP31's close and Cyclone Akvan's landfall (20 Nov, not yet).")


def build():
    img = Image.new("RGB", (W, H), PAPER)
    d = ImageDraw.Draw(img)
    MX = 14  # side margin

    # ===== masthead band =====
    d.rectangle([0, 0, W, 102], fill=NAVY)
    f_kick = font(F_SANS_B, 13)
    d.text((MX, 10), "THE WORLD IN ONE DAY", font=f_kick, fill=(255, 255, 255))
    f_cnt = font(F_SANS_B, 12)
    cnt = "44 STORIES · 7 REGIONS · 13 DRAWN"
    d.text((W - MX - d.textlength(cnt, font=f_cnt), 11), cnt, font=f_cnt,
           fill=(255, 214, 120))
    # date — auto-fit
    date_txt = "Thursday 19 November 2026"
    size = 56
    while size > 30:
        f_date = font(F_SERIF_B, size)
        if d.textlength(date_txt, font=f_date) <= W - 2 * MX:
            break
        size -= 1
    d.text(((W - d.textlength(date_txt, font=f_date)) / 2, 34), date_txt,
           font=f_date, fill=(255, 255, 255))
    d.rectangle([0, 102, W, 106], fill=RED)

    # ===== sub-headline =====
    f_sub = font(F_SERIF_I, 17)
    sub = ("Trump, Xi and Putin share one table · The World Court finds genocide "
           "in Myanmar · A record IPO meets a record game launch")
    d.text(((W - d.textlength(sub, font=f_sub)) / 2, 112), sub, font=f_sub,
           fill=RED_DK)

    # ===== numbers strip =====
    y0, y1 = 136, 178
    d.line([(MX, y0), (W - MX, y0)], fill=GRAY_LT, width=1)
    d.line([(MX, y1), (W - MX, y1)], fill=GRAY_LT, width=1)
    cw = (W - 2 * MX) / len(NUMBERS)
    f_num = font(F_SERIF_B, 24)
    f_lab = font(F_SANS, 10)
    for i, (num, lab) in enumerate(NUMBERS):
        x = MX + i * cw
        d.text((x + 8, y0 + 3), num, font=f_num, fill=RED)
        d.text((x + 8, y0 + 28), lab, font=f_lab, fill=GRAY)
        if i:
            d.line([(x, y0 + 4), (x, y1 - 4)], fill=GRAY_LT, width=1)

    # ===== region bar =====
    y0, y1 = 182, 200
    total = sum(c for _, c in REGIONS)
    x = MX
    f_reg = font(F_SANS_B, 10)
    for name, count in REGIONS:
        wseg = (W - 2 * MX) * count / total
        d.rectangle([x, y0, x + wseg, y1], fill=REGION_COLORS[name])
        label = f"{name} {count}"
        tw = d.textlength(label, font=f_reg)
        d.text((x + (wseg - tw) / 2, y0 + 4), label, font=f_reg,
               fill=(255, 255, 255))
        x += wseg

    # ===== lead story (full width) =====
    y0, y1 = 206, 402
    d.rectangle([MX, y0, W - MX, y1], outline=NAVY, width=2)
    ill_w = 560
    ill_summit(d, MX + 2, y0 + 2, MX + 2 + ill_w, y1 - 2)
    d.line([(MX + 2 + ill_w, y0), (MX + 2 + ill_w, y1)], fill=NAVY, width=2)
    tx = MX + 2 + ill_w + 16
    tw = W - MX - tx - 10
    num_circle(d, tx + 9, y0 + 18, 1, r=10)
    f_kick2 = font(F_SANS_B, 11)
    d.text((tx + 26, y0 + 10), "SHENZHEN · SUMMIT", font=f_kick2, fill=RED)
    badge(d, tx + 26, y0 + 26, "REPORTED", (34, 120, 60))
    f_h1 = font(F_SERIF_B, 27)
    y = draw_text_block(d, tx, y0 + 46,
                        "Trump, Xi and Putin hold first three-way summit",
                        f_h1, tw, NAVY, leading=32, max_lines=3)
    f_b1 = font(F_SANS, 12)
    y = draw_text_block(d, tx, y + 8,
                        "The US, Chinese and Russian leaders met for 90 minutes and "
                        "issued a “Declaration on Peace” on nuclear risk and UN reform. "
                        "Ukraine was not on the agenda; Kyiv was not in the room.",
                        f_b1, tw, INK, leading=16, max_lines=5)
    f_src = font(F_SANS, 10)
    d.text((tx, y1 - 22), "— Reuters · AP · Xinhua", font=f_src, fill=GRAY)

    # ===== medium row: 4 cards =====
    y0, y1 = 408, 612
    gap = 8
    cw = (W - 2 * MX - 3 * gap) / 4
    f_k = font(F_SANS_B, 10)
    f_hm = font(F_SERIF_B, 15)
    f_bm = font(F_SANS, 10)
    for i, (n, place, topic, head, body, src, tag, ill) in enumerate(MEDIUM):
        x0 = MX + i * (cw + gap)
        x1 = x0 + cw
        d.rectangle([x0, y0, x1, y1], outline=NAVY, width=1)
        ill(d, x0 + 1, y0 + 1, x1 - 1, y0 + 90)
        d.line([(x0, y0 + 90), (x1, y0 + 90)], fill=NAVY, width=1)
        num_circle(d, x0 + 13, y0 + 102, n, r=9)
        d.text((x0 + 27, y0 + 94), f"{place} · {topic}", font=f_k, fill=RED)
        badge(d, x1 - 62, y0 + 94, tag, (34, 120, 60) if tag == "REPORTED" else (180, 120, 20))
        yy = draw_text_block(d, x0 + 8, y0 + 112, head, f_hm, cw - 16, NAVY,
                             leading=18, max_lines=2)
        yy = draw_text_block(d, x0 + 8, yy + 4, body, f_bm, cw - 16, INK,
                             leading=12, max_lines=3)
        d.text((x0 + 8, y1 - 15), "— " + src, font=font(F_SANS, 9), fill=GRAY)

    # ===== small rows: 8 cards, 2 x 4 =====
    f_hs = font(F_SERIF_B, 12)
    f_bs = font(F_SANS, 9)
    f_ks = font(F_SANS_B, 9)
    row_h = 88
    for row in range(2):
        y0 = 618 + row * (row_h + 6)
        y1 = y0 + row_h
        for col in range(4):
            n, place, topic, head, body, src, tag, ill = SMALL[row * 4 + col]
            x0 = MX + col * (cw + gap)
            x1 = x0 + cw
            d.rectangle([x0, y0, x1, y1], outline=NAVY, width=1)
            iw = 92
            ill(d, x0 + 1, y0 + 1, x0 + iw, y1 - 1)
            d.line([(x0 + iw, y0), (x0 + iw, y1)], fill=NAVY, width=1)
            tx = x0 + iw + 8
            tw = x1 - tx - 6
            num_circle(d, tx + 7, y0 + 12, n, r=8)
            d.text((tx + 18, y0 + 5), f"{place} · {topic}", font=f_ks, fill=RED)
            yy = draw_text_block(d, tx, y0 + 19, head, f_hs, tw, NAVY,
                                 leading=14, max_lines=2)
            draw_text_block(d, tx, yy + 2, body, f_bs, tw, INK, leading=11,
                            max_lines=2)
            d.text((tx, y1 - 12), "— " + src, font=font(F_SANS, 8), fill=GRAY)

    # ===== bottom: map + briefs =====
    y0, y1 = 806, 968
    map_w = 296
    d.rectangle([MX, y0, MX + map_w, y1], outline=NAVY, width=1)
    f_sec = font(F_SANS_B, 11)
    d.text((MX + 8, y0 + 5), "WHERE IT HAPPENED", font=f_sec, fill=NAVY)
    d.text((MX + 8, y0 + 20), "numbers match the stories · 5 = worldwide",
           font=font(F_SANS, 9), fill=GRAY)
    draw_map(d, (MX + 4, y0 + 36, MX + map_w - 4, y1 - 4), MAP_PINS)

    bx = MX + map_w + 10
    bw = W - MX - bx
    d.text((bx, y0 + 5), "ALSO ON THURSDAY 19 NOVEMBER — 31 MORE STORIES",
           font=f_sec, fill=RED)
    d.line([(bx, y0 + 20), (W - MX, y0 + 20)], fill=RED, width=1)
    f_br = font(F_SANS, 9)
    f_brb = font(F_SANS_B, 9)
    col_w = bw / 2 - 6
    row_h2 = 9.6
    for idx, (n, place, brief, src) in enumerate(BRIEFS):
        col = 0 if idx < 16 else 1
        r = idx if idx < 16 else idx - 16
        x = bx + col * (col_w + 12)
        yy = y0 + 25 + r * row_h2
        d.text((x, yy), f"{n}", font=f_brb, fill=RED)
        nw = d.textlength(f"{n} ", font=f_brb)
        line = f"{place} — {brief} {src}"
        # trim to fit
        while d.textlength(line, font=f_br) > col_w - nw and len(line) > 10:
            line = line[:-1]
        if len(line) < len(f"{place} — {brief} {src}"):
            line = line.rstrip(" .,") + "…"
        d.text((x + nw, yy), line, font=f_br, fill=INK)

    # ===== date check =====
    y0, y1 = 974, 1002
    d.rectangle([MX, y0, W - MX, y1], outline=RED, width=1)
    f_dc = font(F_SANS, 9)
    lines = wrap(d, DATE_CHECK, f_dc, W - 2 * MX - 16)
    yy = y0 + 3
    for ln in lines[:2]:
        d.text((MX + 8, yy), ln, font=f_dc, fill=INK)
        yy += 11

    # ===== footer =====
    f_ft = font(F_SANS, 8)
    ft = ("Every story here happened, or was first reported, on Thursday 19 November 2026 (any time zone). "
          "Claims are attributed, not stated as fact. *Sensor Tower estimate. Pictures and map: original, drawn in code. "
          "Sources: Reuters, AP, AFP, BBC, Al Jazeera, UN News, Euronews, ABC, RNZ, Xinhua, IMD, ABS, Yonhap, IEA.")
    flines = wrap(d, ft, f_ft, W - 2 * MX)
    yy = 1005
    for ln in flines[:2]:
        d.text((MX, yy), ln, font=f_ft, fill=GRAY)
        yy += 9

    return img


if __name__ == "__main__":
    out = os.path.join(HERE, "entry.png")
    img = build()
    img.save(out, optimize=True)
    print(out, img.size, os.path.getsize(out), "bytes")
