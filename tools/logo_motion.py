"""STOP AT NOTHING — logo motion renderer (Pillow + ffmpeg)."""
import os, sys, subprocess, math
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

W = H = 1080
FPS = 30
NF = 150
OUT = os.environ.get("MOTION_FRAMES", "/tmp/stop-at-nothing-frames")
os.makedirs(OUT, exist_ok=True)
SRC = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", "stop-at-nothing-logo.png")

# ---------------------------------------------------------------- assets
base = Image.open(SRC).convert("L").resize((W, H), Image.LANCZOS)
# lift the source's near-black background to true black so crops composite cleanly
base = base.point(lambda v: 0 if v <= 11 else min(255, int((v - 11) * 255 / 244)))

def band(y0, y1):  # crop a horizontal strip, returns L image
    return base.crop((0, y0, W, y1))

MARK = band(236, 490)     # 254 tall
RULE = band(528, 552)     # 24 tall
L1 = band(596, 722)       # 126 tall
L2 = band(724, 850)

# metal-only mask for the shine sweep
markmask = MARK.point(lambda v: 255 if v > 46 else 0).filter(ImageFilter.GaussianBlur(4))
markmask = markmask.point(lambda v: min(255, int(v * 1.9)))

# soft diagonal highlight band, wide enough to sweep the whole lockup
SHINE_W, SHINE_H = 2200, 420
def make_shine():
    # horizontal gradient black->white->black
    g = np.zeros((SHINE_H, SHINE_W), dtype=np.float32)
    xs = np.arange(SHINE_W, dtype=np.float32)
    c = SHINE_W / 2
    halfw = 175.0
    prof = np.clip(1 - np.abs(xs - c) / halfw, 0, 1) ** 1.5
    g[:, :] = prof[None, :]
    img = Image.fromarray((g * 255).astype(np.uint8), "L")
    img = img.rotate(18, resample=Image.BICUBIC, expand=False)
    return img
SHINE = make_shine()

# ---------------------------------------------------------------- easing
def clamp(x, a=0.0, b=1.0): return max(a, min(b, x))
def seg(f, a, b):
    if f <= a: return 0.0
    if f >= b: return 1.0
    return (f - a) / (b - a)
def ease_out(x): return 1 - (1 - x) ** 3
def ease_io(x): return 3 * x * x - 2 * x * x * x

def add(dst, layer, pos):
    dst.paste(layer, pos, layer) if layer.mode == "L" else None

def screen_add(dst, layer, pos):
    """screen-composite a grayscale layer at pos onto RGB canvas"""
    x0, y0 = pos
    lw, lh = layer.size
    cx0, cy0 = max(0, x0), max(0, y0)
    cx1, cy1 = min(W, x0 + lw), min(H, y0 + lh)
    if cx1 <= cx0 or cy1 <= cy0:
        return
    src = layer.crop((cx0 - x0, cy0 - y0, cx1 - x0, cy1 - y0))
    reg = dst.crop((cx0, cy0, cx1, cy1))
    a = np.asarray(reg.convert("L"), dtype=np.uint16)
    b = np.asarray(src, dtype=np.uint16)
    out = 255 - ((255 - a) * (255 - b) // 255)
    dst.paste(Image.fromarray(out.astype(np.uint8), "L").convert("RGB"), (cx0, cy0))

def opacity(layer, op):
    if op >= 0.999: return layer
    return layer.point(lambda v: int(v * op))

def render(f):
    canvas = Image.new("RGB", (W, H), (0, 0, 0))

    # ---- 1. mark: settle in with a slow scale ----
    pm = ease_out(seg(f, 0, 26))
    op = clamp(seg(f, 0, 15))
    s = 0.93 + 0.07 * pm
    mw, mh = int(W * s), int(MARK.size[1] * s)
    m = MARK.resize((mw, mh), Image.LANCZOS)
    m = opacity(m, op)
    mx = (W - mw) // 2
    my = 363 - mh // 2

    # ---- 2. hairline rule: draws from the centre out ----
    rp = ease_io(seg(f, 10, 34))
    half = int(277 * rp)
    rule = Image.new("L", (max(1, half * 2), 3), 255)
    rule = rule.point(lambda v: int(v * (0.35 + 0.65 * rp)))

    # ---- 3. wordmark: fade with a short upward drift ----
    def line(layer, f0, f1, ytop):
        q = ease_out(seg(f, f0, f1))
        dy = int(round(26 * (1 - q)))
        return opacity(layer, clamp(q * 1.1)), ytop + dy

    a1, y1 = line(L1, 24, 54, 596)
    a2, y2 = line(L2, 32, 62, 724)

    # ---- 4. chrome sweep across the metal ----
    shine = None
    if 62 <= f <= 112:
        p = ease_io(seg(f, 62, 112))
        sx = int(-560 + 1500 * p)
        bandimg = Image.new("L", (W, MARK.size[1]), 0)
        tmp = Image.new("L", (W, MARK.size[1]), 0)
        tmp.paste(SHINE, (sx - SHINE_W // 2 + W // 2, -60))
        bandimg = Image.composite(tmp, Image.new("L", tmp.size, 0), markmask)
        shine = bandimg.point(lambda v: min(255, int(v * 1.05)))

    # ---- composite ----
    screen_add(canvas, m, (mx, my))
    screen_add(canvas, rule, ((W - rule.size[0]) // 2, 537))
    screen_add(canvas, a1, (0, y1))
    screen_add(canvas, a2, (0, y2))
    if shine is not None:
        screen_add(canvas, shine, (0, 236))

    canvas = canvas.filter(ImageFilter.GaussianBlur(0.25))
    canvas.save(f"{OUT}/f{f:04d}.png", compress_level=1)

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        for ff in [int(x) for x in sys.argv[2:]]:
            render(ff)
        sys.exit()
    a, b = int(sys.argv[1]), int(sys.argv[2])
    for f in range(a, b):
        render(f)
    print("rendered", a, b)
