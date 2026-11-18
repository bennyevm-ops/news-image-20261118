#!/usr/bin/env python3
"""The Day In One Picture -- Wednesday 18 November 2026.

A make.fun "news-image" entry: the whole of one day's world news summed up
in a single 1024x1024 PNG, drawn as a newspaper front page.

The program uses ONLY the Python standard library.  It carries its own
PNG encoder (zlib + struct), its own tiny rasteriser (rects, circles,
lines, polygons), and its own 5x7 bitmap font, and it paints the page
pixel by pixel.  The output is fully deterministic: no clock, no
randomness, no network -- two runs produce byte-identical files.

Layout of the page
------------------
* Masthead: "THE DAY IN ONE PICTURE", then the day named in the largest
  type on the page: WEDNESDAY / 18 NOVEMBER 2026.
* One wide LEAD panel: Nvidia's blockbuster results ($115.8B revenue).
* A 2x2 grid: Anthropic's IPO pricing, the Fed minutes, Bank Indonesia's
  rate call with the rupiah at a record low, and Nvidia's $130B outlook.

Run it with:  python3 main.py
It writes entry.png into $MAKEFUN_OUTPUT_DIR (default /output).
"""

import os
import struct
import zlib

# ---------------------------------------------------------------------------
# Bitmap font: 5x7 glyphs, one tuple of 7 strings per character.
# '#' is a lit pixel, '.' is dark.  Authored for this entry; covers the
# uppercase alphabet, digits, and the punctuation the headlines need.
# ---------------------------------------------------------------------------

FONT = {
    "A": (".###.", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"),
    "B": ("####.", "#...#", "#...#", "####.", "#...#", "#...#", "####."),
    "C": (".####", "#....", "#....", "#....", "#....", "#....", ".####"),
    "D": ("####.", "#...#", "#...#", "#...#", "#...#", "#...#", "####."),
    "E": ("#####", "#....", "#....", "####.", "#....", "#....", "#####"),
    "F": ("#####", "#....", "#....", "####.", "#....", "#....", "#...."),
    "G": (".####", "#....", "#....", "#.###", "#...#", "#...#", ".###."),
    "H": ("#...#", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"),
    "I": ("#####", "..#..", "..#..", "..#..", "..#..", "..#..", "#####"),
    "J": ("..###", "...#.", "...#.", "...#.", "...#.", "#..#.", ".##.."),
    "K": ("#...#", "#..#.", "#.#..", "##...", "#.#..", "#..#.", "#...#"),
    "L": ("#....", "#....", "#....", "#....", "#....", "#....", "#####"),
    "M": ("#...#", "##.##", "#.#.#", "#.#.#", "#...#", "#...#", "#...#"),
    "N": ("#...#", "##..#", "##..#", "#.#.#", "#..##", "#..##", "#...#"),
    "O": (".###.", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."),
    "P": ("####.", "#...#", "#...#", "####.", "#....", "#....", "#...."),
    "Q": (".###.", "#...#", "#...#", "#...#", "#.#.#", "#..#.", ".##.#"),
    "R": ("####.", "#...#", "#...#", "####.", "#.#..", "#..#.", "#...#"),
    "S": (".####", "#....", "#....", ".###.", "....#", "....#", "####."),
    "T": ("#####", "..#..", "..#..", "..#..", "..#..", "..#..", "..#.."),
    "U": ("#...#", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."),
    "V": ("#...#", "#...#", "#...#", "#...#", "#...#", ".#.#.", "..#.."),
    "W": ("#...#", "#...#", "#...#", "#.#.#", "#.#.#", "##.##", "#...#"),
    "X": ("#...#", ".#.#.", "..#..", "..#..", "..#..", ".#.#.", "#...#"),
    "Y": ("#...#", "#...#", ".#.#.", "..#..", "..#..", "..#..", "..#.."),
    "Z": ("#####", "....#", "...#.", "..#..", ".#...", "#....", "#####"),
    "0": (".###.", "#..##", "#.#.#", "##..#", "#...#", "#...#", ".###."),
    "1": ("..#..", ".##..", "..#..", "..#..", "..#..", "..#..", ".###."),
    "2": (".###.", "#...#", "....#", "...#.", "..#..", ".#...", "#####"),
    "3": ("#####", "...#.", "..#..", "...#.", "....#", "#...#", ".###."),
    "4": ("...#.", "..##.", ".#.#.", "#..#.", "#####", "...#.", "...#."),
    "5": ("#####", "#....", "####.", "....#", "....#", "#...#", ".###."),
    "6": (".###.", "#....", "#....", "####.", "#...#", "#...#", ".###."),
    "7": ("#####", "....#", "...#.", "..#..", ".#...", ".#...", ".#..."),
    "8": (".###.", "#...#", "#...#", ".###.", "#...#", "#...#", ".###."),
    "9": (".###.", "#...#", "#...#", ".####", "....#", "....#", ".###."),
    " ": (".....", ".....", ".....", ".....", ".....", ".....", "....."),
    ".": (".....", ".....", ".....", ".....", ".....", ".##..", ".##.."),
    ",": (".....", ".....", ".....", ".....", ".##..", ".##..", ".#..."),
    "'": (".##..", ".##..", ".#...", ".....", ".....", ".....", "....."),
    "!": ("..#..", "..#..", "..#..", "..#..", "..#..", ".....", "..#.."),
    "-": (".....", ".....", ".....", "#####", ".....", ".....", "....."),
    ":": (".....", ".##..", ".##..", ".....", ".##..", ".##..", "....."),
    "/": ("....#", "....#", "...#.", "..#..", ".#...", "#....", "#...."),
    "+": (".....", "..#..", "..#..", "#####", "..#..", "..#..", "....."),
    "$": ("..#..", ".####", "#.#..", ".###.", "..#.#", "####.", "..#.."),
    "%": ("##..#", "##.#.", "....#", "...#.", "..#..", ".#.##", "#..##"),
}

GLYPH_W = 5
GLYPH_H = 7
GLYPH_ADVANCE = 6  # 5 px of glyph + 1 px of tracking, in glyph units


def text_width(text, scale):
    """Pixel width of a string rendered at the given integer scale."""
    if not text:
        return 0
    return len(text) * GLYPH_ADVANCE * scale - scale


# ---------------------------------------------------------------------------
# Canvas: a plain RGB pixel buffer plus the drawing primitives.
# ---------------------------------------------------------------------------

class Canvas:
    def __init__(self, width, height, bg):
        self.width = width
        self.height = height
        self.pixels = bytearray(bg) * (width * height)

    def set_px(self, x, y, color):
        if 0 <= x < self.width and 0 <= y < self.height:
            i = (y * self.width + x) * 3
            self.pixels[i] = color[0]
            self.pixels[i + 1] = color[1]
            self.pixels[i + 2] = color[2]

    def fill_rect(self, x, y, w, h, color):
        x0 = max(0, x)
        y0 = max(0, y)
        x1 = min(self.width, x + w)
        y1 = min(self.height, y + h)
        if x1 <= x0 or y1 <= y0:
            return
        row = bytes(color) * (x1 - x0)
        for yy in range(y0, y1):
            i = (yy * self.width + x0) * 3
            self.pixels[i:i + len(row)] = row

    def stroke_rect(self, x, y, w, h, thickness, color):
        self.fill_rect(x, y, w, thickness, color)
        self.fill_rect(x, y + h - thickness, w, thickness, color)
        self.fill_rect(x, y, thickness, h, color)
        self.fill_rect(x + w - thickness, y, thickness, h, color)

    def fill_circle(self, cx, cy, r, color):
        r2 = r * r
        for yy in range(cy - r, cy + r + 1):
            dy = yy - cy
            span2 = r2 - dy * dy
            if span2 < 0:
                continue
            span = int(span2 ** 0.5)
            self.fill_rect(cx - span, yy, 2 * span + 1, 1, color)

    def draw_line(self, x0, y0, x1, y1, thickness, color):
        """Thick line: Bresenham walk stamping filled circles."""
        dx = abs(x1 - x0)
        dy = -abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx + dy
        r = max(0, thickness // 2)
        x, y = x0, y0
        while True:
            if r:
                self.fill_circle(x, y, r, color)
            else:
                self.set_px(x, y, color)
            if x == x1 and y == y1:
                break
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x += sx
            if e2 <= dx:
                err += dx
                y += sy

    def fill_polygon(self, points, color):
        """Scanline even-odd polygon fill (integer vertices)."""
        ys = [p[1] for p in points]
        y_min = max(0, min(ys))
        y_max = min(self.height - 1, max(ys))
        n = len(points)
        for yy in range(y_min, y_max + 1):
            scan = yy + 0.5
            crossings = []
            for i in range(n):
                x0, y0 = points[i]
                x1, y1 = points[(i + 1) % n]
                if y0 == y1:
                    continue
                if (y0 <= scan < y1) or (y1 <= scan < y0):
                    t = (scan - y0) / (y1 - y0)
                    crossings.append(x0 + t * (x1 - x0))
            crossings.sort()
            for i in range(0, len(crossings) - 1, 2):
                xa = int(round(crossings[i]))
                xb = int(round(crossings[i + 1]))
                self.fill_rect(xa, yy, max(0, xb - xa), 1, color)

    # -- text ---------------------------------------------------------------

    def draw_text(self, x, y, text, scale, color):
        """Draw text with its top-left corner at (x, y). Returns width."""
        cursor = x
        for ch in text:
            glyph = FONT.get(ch)
            if glyph is None:
                glyph = FONT[" "]
            for row_i, row in enumerate(glyph):
                for col_i, cell in enumerate(row):
                    if cell == "#":
                        self.fill_rect(cursor + col_i * scale,
                                       y + row_i * scale,
                                       scale, scale, color)
            cursor += GLYPH_ADVANCE * scale
        return cursor - scale - x if text else 0

    def draw_text_centered(self, cx, y, text, scale, color):
        w = text_width(text, scale)
        return self.draw_text(cx - w // 2, y, text, scale, color)


# ---------------------------------------------------------------------------
# PNG encoding (zlib + struct only): 8-bit RGB, filter 0 scanlines.
# ---------------------------------------------------------------------------

def _chunk(tag, data):
    chunk = struct.pack(">I", len(data)) + tag + data
    chunk += struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)
    return chunk


def encode_png(canvas):
    raw = bytearray()
    stride = canvas.width * 3
    for yy in range(canvas.height):
        raw.append(0)  # filter type 0 (None) for every scanline
        start = yy * stride
        raw += canvas.pixels[start:start + stride]
    ihdr = struct.pack(">IIBBBBB", canvas.width, canvas.height,
                       8, 2, 0, 0, 0)  # 8-bit, colour type 2 (RGB)
    return (b"\x89PNG\r\n\x1a\n"
            + _chunk(b"IHDR", ihdr)
            + _chunk(b"IDAT", zlib.compress(bytes(raw), 9))
            + _chunk(b"IEND", b""))


# ---------------------------------------------------------------------------
# Pictograms: each story gets one big, simple picture built from shapes.
# ---------------------------------------------------------------------------

def draw_chip(cv, cx, cy, size, body, core, pin):
    """A computer chip: square body, bright core, pins on all four sides."""
    half = size // 2
    x0, y0 = cx - half, cy - half
    pin_len = size // 5
    pin_w = max(3, size // 16)
    step = size // 4
    for i in range(3):
        off = step * (i + 1) - pin_w // 2 - size // 8 + size // 16
        # top and bottom pins
        cv.fill_rect(x0 + off, y0 - pin_len, pin_w, pin_len, pin)
        cv.fill_rect(x0 + off, y0 + size, pin_w, pin_len, pin)
        # left and right pins
        cv.fill_rect(x0 - pin_len, y0 + off, pin_len, pin_w, pin)
        cv.fill_rect(x0 + size, y0 + off, pin_len, pin_w, pin)
    cv.fill_rect(x0, y0, size, size, body)
    inner = size // 2
    cv.fill_rect(cx - inner // 2, cy - inner // 2, inner, inner, core)


def draw_robot(cv, cx, cy, w, h, body, face, accent):
    """A simple robot head: dome head, antenna, two eyes, a mouth grille."""
    x0 = cx - w // 2
    y0 = cy - h // 2
    # antenna
    cv.draw_line(cx, y0, cx, y0 - h // 5, max(3, w // 14), accent)
    cv.fill_circle(cx, y0 - h // 5 - w // 12, w // 11, accent)
    # ears
    ear_w = max(4, w // 9)
    cv.fill_rect(x0 - ear_w, cy - h // 8, ear_w, h // 4, accent)
    cv.fill_rect(x0 + w, cy - h // 8, ear_w, h // 4, accent)
    # head
    cv.fill_rect(x0, y0, w, h, body)
    # eyes
    eye_r = max(3, w // 10)
    cv.fill_circle(cx - w // 5, cy - h // 10, eye_r, face)
    cv.fill_circle(cx + w // 5, cy - h // 10, eye_r, face)
    # mouth grille: three short vertical bars
    bar_w = max(3, w // 16)
    for i in (-1, 0, 1):
        cv.fill_rect(cx + i * w // 6 - bar_w // 2, cy + h // 6,
                     bar_w, h // 6, face)


def draw_bank(cv, cx, cy, w, h, color):
    """A bank / central-bank building: pediment, columns, steps."""
    x0 = cx - w // 2
    y0 = cy - h // 2
    ped_h = h // 4
    # pediment (triangle) + its base beam
    cv.fill_polygon([(x0 - w // 16, y0 + ped_h),
                     (x0 + w + w // 16, y0 + ped_h),
                     (cx, y0)], color)
    cv.fill_rect(x0, y0 + ped_h, w, h // 12, color)
    # columns
    col_top = y0 + ped_h + h // 8
    col_h = h - ped_h - h // 8 - h // 7
    col_w = max(4, w // 11)
    for i in range(4):
        col_x = x0 + w // 12 + i * (w - w // 6 - col_w) // 3
        cv.fill_rect(col_x, col_top, col_w, col_h, color)
    # base + step
    base_y = col_top + col_h
    cv.fill_rect(x0, base_y, w, h // 14, color)
    cv.fill_rect(x0 - w // 16, base_y + h // 14, w + w // 8, h // 14, color)


def draw_coin(cv, cx, cy, r, rim, face, ink):
    """A coin: gold disc with a rim, lettered 'RP' for the rupiah."""
    cv.fill_circle(cx, cy, r, rim)
    cv.fill_circle(cx, cy, r - max(3, r // 8), face)
    scale = max(2, (2 * r) // 22)
    w = text_width("RP", scale)
    cv.draw_text(cx - w // 2, cy - (GLYPH_H * scale) // 2, "RP", scale, ink)


def draw_rising_bars(cv, cx, cy, w, h, bar_color, arrow_color):
    """Ascending bar chart with a bold arrow climbing over it."""
    base = cy + h // 2
    n = 4
    bar_w = w // (n * 2 - 1)
    heights = [h // 3, h // 2, (3 * h) // 4, h]
    tops = []
    for i in range(n):
        bx = cx - w // 2 + i * 2 * bar_w
        bh = heights[i]
        cv.fill_rect(bx, base - bh, bar_w, bh, bar_color)
        tops.append((bx + bar_w // 2, base - bh))
    # arrow shaft through the bar tops, then a triangular head
    thick = max(4, w // 18)
    for i in range(n - 1):
        cv.draw_line(tops[i][0], tops[i][1] - h // 10,
                     tops[i + 1][0], tops[i + 1][1] - h // 10,
                     thick, arrow_color)
    tx, ty = tops[-1]
    ty -= h // 10
    head = w // 7
    cv.fill_polygon([(tx - head // 3, ty - head),
                     (tx + head, ty + head // 3),
                     (tx - head, ty - head // 3)], arrow_color)
    cv.fill_circle(tx, ty, thick // 2, arrow_color)


# ---------------------------------------------------------------------------
# The page: a newspaper front page for Wednesday 18 November 2026.
# ---------------------------------------------------------------------------

PAPER = (247, 243, 232)
INK = (20, 20, 20)

LEAD_BG = (13, 43, 30)
LEAD_TEXT = (245, 245, 238)
LEAD_SUB = (190, 215, 190)
CHIP_BODY = (224, 232, 220)
CHIP_CORE = (118, 185, 0)
CHIP_PIN = (160, 180, 160)

WHITE = (255, 252, 245)


def draw_panel(cv, x, y, w, h, bg, headline, sublines, sub_color, picto):
    """One grid panel: pictogram on top, headline, then a short subline."""
    cv.fill_rect(x, y, w, h, bg)
    picto(cv, x + w // 2, y + 50)
    for i, line in enumerate(headline):
        cv.draw_text_centered(x + w // 2, y + 94 + i * 46, line, 6, WHITE)
    for i, line in enumerate(sublines):
        cv.draw_text_centered(x + w // 2, y + 190 + i * 25, line, 3, sub_color)


def build_image():
    cv = Canvas(1024, 1024, PAPER)

    # Page frame.
    cv.stroke_rect(10, 10, 1004, 1004, 4, INK)

    # -- Masthead: the day, named in the largest type on the page. --------
    cv.draw_text_centered(512, 30, "THE DAY IN ONE PICTURE", 3, INK)
    cv.fill_rect(24, 58, 976, 3, INK)
    cv.draw_text_centered(512, 70, "WEDNESDAY", 11, INK)
    cv.draw_text_centered(512, 154, "18 NOVEMBER 2026", 6, INK)
    cv.fill_rect(24, 202, 976, 4, INK)
    cv.fill_rect(24, 210, 976, 2, INK)

    # -- Lead: the world digests Nvidia's blockbuster results. -----------
    cv.fill_rect(24, 222, 976, 256, LEAD_BG)
    draw_chip(cv, 158, 350, 108, CHIP_BODY, CHIP_CORE, CHIP_PIN)
    cv.draw_text(286, 242, "NVIDIA'S", 9, LEAD_TEXT)
    cv.draw_text(286, 312, "$115.8B", 9, LEAD_TEXT)
    cv.draw_text(286, 382, "BEAT", 9, LEAD_TEXT)
    cv.draw_text(286, 446, "WORLD DIGESTS THE AI GIANT'S RESULTS", 3, LEAD_SUB)

    # -- Grid of four. ----------------------------------------------------
    grid_y = (494, 752)
    grid_x = (24, 518)
    panel_w, panel_h = 482, 242

    # Anthropic prices its IPO today.
    draw_panel(
        cv, grid_x[0], grid_y[0], panel_w, panel_h, (180, 83, 9),
        ("ANTHROPIC", "PRICES IPO"),
        ("$1.5 TRILLION AI", "LISTING SET TODAY"),
        (255, 224, 178),
        lambda c, cx, cy: draw_robot(c, cx, cy, 62, 50,
                                     (252, 243, 226), (146, 64, 14),
                                     (255, 211, 106)),
    )

    # The Fed publishes its October minutes tonight.
    draw_panel(
        cv, grid_x[1], grid_y[0], panel_w, panel_h, (30, 58, 95),
        ("FED MINUTES", "TONIGHT"),
        ("CLUES ON A DECEMBER", "RATE HIKE"),
        (171, 203, 238),
        lambda c, cx, cy: draw_bank(c, cx, cy, 116, 72, (226, 236, 248)),
    )

    # Bank Indonesia's rate call, rupiah at a record low.
    draw_panel(
        cv, grid_x[0], grid_y[1], panel_w, panel_h, (153, 27, 27),
        ("JAKARTA'S", "RATE CALL"),
        ("RUPIAH AT RECORD LOW", "DECISION TODAY"),
        (254, 205, 205),
        lambda c, cx, cy: draw_coin(c, cx, cy, 35,
                                    (217, 160, 32), (245, 197, 66),
                                    (120, 20, 20)),
    )

    # Nvidia's $130B outlook, with zero China sales assumed.
    draw_panel(
        cv, grid_x[1], grid_y[1], panel_w, panel_h, (67, 56, 202),
        ("THE $130B", "OUTLOOK"),
        ("GUIDANCE BEATS - WITH", "ZERO CHINA SALES"),
        (199, 210, 254),
        lambda c, cx, cy: draw_rising_bars(c, cx, cy, 118, 70,
                                           (199, 210, 254), (250, 204, 21)),
    )

    return cv


def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out_dir, exist_ok=True)
    png = encode_png(build_image())
    out_path = os.path.join(out_dir, "entry.png")
    with open(out_path, "wb") as fh:
        fh.write(png)
    return out_path


if __name__ == "__main__":
    main()
