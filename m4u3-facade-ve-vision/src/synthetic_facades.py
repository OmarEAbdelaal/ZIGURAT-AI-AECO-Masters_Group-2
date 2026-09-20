"""
Procedural façade elevations + exact YOLO labels, with no network and no account.

WHY THIS EXISTS
---------------
The M4U3 brief asks that a third party be able to open the repository and
reproduce the pipeline in Colab. A pipeline that only runs once the reader has
a Roboflow account, an API key and a private dataset is not reproducible by a
stranger; it is reproducible by us. So the repository ships a dataset it can
generate from nothing, and the notebooks default to it.

WHAT IT IS AND IS NOT
---------------------
It IS a controlled smoke test: it proves the loader, the data.yaml, the
training loop, the metric extraction, the evidence pack and the error-analysis
miner all work, end to end, on a machine that has never seen this project.

It IS NOT a result. Numbers from this dataset say nothing about real façade
detection performance — the geometry is axis-aligned, the lighting is
synthetic, and the domain gap to a real photograph is enormous (LS2 Q&A:
"models trained only on synthetic data often perform worse on real-world
inputs"). Every table produced from it is labelled VERIFICATION RUN.

DESIGN NOTE
-----------
Realism is deliberately imperfect but the FAILURE STRUCTURE is real. The
generator plants unlabelled decoys (spandrel panels that read as glazing,
signage that reads as a door) and hard positives (3-pixel clerestory windows,
glare-blown openings, occluded bays). That is what makes the confusion matrix
and the automatic FP/FN miner produce findings worth writing about instead of
a perfect diagonal.
"""

from __future__ import annotations

import random
from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

from config import CLASSES

W = H = 640
CID = {name: i for i, name in enumerate(CLASSES)}


@dataclass
class Box:
    cls: str
    x0: float
    y0: float
    x1: float
    y1: float

    def yolo(self, w: int = W, h: int = H) -> str:
        cx = (self.x0 + self.x1) / 2 / w
        cy = (self.y0 + self.y1) / 2 / h
        bw = (self.x1 - self.x0) / w
        bh = (self.y1 - self.y0) / h
        cx, cy = min(max(cx, 0.0), 1.0), min(max(cy, 0.0), 1.0)
        bw, bh = min(bw, 1.0), min(bh, 1.0)
        return f"{CID[self.cls]} {cx:.6f} {cy:.6f} {bw:.6f} {bh:.6f}"

    @property
    def area_px(self) -> float:
        return max(0.0, self.x1 - self.x0) * max(0.0, self.y1 - self.y0)


# ---------------------------------------------------------------- palettes --
WALL_TONES = [
    (206, 199, 188), (188, 176, 162), (166, 158, 150), (214, 208, 198),
    (150, 138, 128), (178, 168, 178), (196, 186, 170), (132, 126, 122),
]
GLASS_TONES = [
    (64, 84, 104), (48, 66, 86), (86, 104, 120), (40, 54, 70),
    (72, 96, 112), (56, 76, 96),
]
SKY_TOP = [(126, 162, 206), (150, 178, 210), (96, 132, 178), (176, 192, 206)]


def _sky(draw: ImageDraw.ImageDraw, rnd: random.Random) -> None:
    top = rnd.choice(SKY_TOP)
    bot = tuple(min(255, c + rnd.randint(40, 80)) for c in top)
    for y in range(H):
        t = y / H
        draw.line(
            [(0, y), (W, y)],
            fill=tuple(int(top[i] + (bot[i] - top[i]) * t) for i in range(3)),
        )


def _pane(draw: ImageDraw.ImageDraw, b: Box, glass, rnd: random.Random,
          frame: int = 3, mullions: bool = False) -> None:
    """Draw a glazed unit: frame, glass, sky reflection wedge, optional mullions."""
    # A clerestory box can be 4 px tall; a 3 px frame would invert it. Scale the
    # frame to the unit so the hard-positive small targets still render.
    frame = max(1.0, min(frame, (b.x1 - b.x0) / 3.0, (b.y1 - b.y0) / 3.0))
    draw.rectangle([b.x0, b.y0, b.x1, b.y1], fill=(92, 92, 96))
    draw.rectangle([b.x0 + frame, b.y0 + frame, b.x1 - frame, b.y1 - frame], fill=glass)
    # reflection wedge — the cue a model latches onto, and the cue that betrays it
    if rnd.random() < 0.7:
        h = (b.y1 - b.y0) * rnd.uniform(0.2, 0.5)
        draw.polygon(
            [(b.x0 + frame, b.y0 + frame), (b.x1 - frame, b.y0 + frame),
             (b.x1 - frame, b.y0 + frame + h * 0.4), (b.x0 + frame, b.y0 + frame + h)],
            fill=tuple(min(255, c + rnd.randint(45, 85)) for c in glass),
        )
    if mullions:
        n = max(1, int((b.x1 - b.x0) // 42))
        for k in range(1, n):
            x = b.x0 + (b.x1 - b.x0) * k / n
            draw.line([(x, b.y0 + frame), (x, b.y1 - frame)], fill=(108, 108, 112), width=2)


def _balustrade(draw: ImageDraw.ImageDraw, b: Box, rnd: random.Random) -> None:
    draw.rectangle([b.x0, b.y0, b.x1, b.y1], fill=(172, 176, 180))
    draw.rectangle([b.x0, b.y0, b.x1, b.y0 + 4], fill=(120, 124, 128))
    if rnd.random() < 0.5:                      # vertical balusters
        x = b.x0 + 4
        while x < b.x1 - 3:
            draw.line([(x, b.y0 + 5), (x, b.y1)], fill=(128, 132, 136), width=1)
            x += 7
    else:                                        # glass balustrade
        draw.rectangle([b.x0 + 2, b.y0 + 5, b.x1 - 2, b.y1], fill=(150, 168, 178))


def _louvres(draw: ImageDraw.ImageDraw, b: Box, rnd: random.Random) -> None:
    draw.rectangle([b.x0, b.y0, b.x1, b.y1], fill=(126, 124, 120))
    step = rnd.choice([6, 8, 10])
    y = b.y0 + 2
    while y < b.y1 - 2:
        draw.line([(b.x0 + 2, y), (b.x1 - 2, y)], fill=(176, 174, 168), width=2)
        y += step


def generate_image(seed: int) -> tuple[Image.Image, list[Box]]:
    """One elevation. Returns the image and only the boxes that are LABELLED."""
    rnd = random.Random(seed)
    img = Image.new("RGB", (W, H))
    d = ImageDraw.Draw(img)
    _sky(d, rnd)

    wall = rnd.choice(WALL_TONES)
    glass = rnd.choice(GLASS_TONES)

    # --- the building block -------------------------------------------------
    fx0 = rnd.randint(20, 70)
    fx1 = W - rnd.randint(20, 70)
    fy0 = rnd.randint(30, 110)
    fy1 = H - rnd.randint(30, 70)
    d.rectangle([fx0, fy0, fx1, fy1], fill=wall)
    # ground / pavement
    d.rectangle([0, fy1, W, H], fill=tuple(max(0, c - 55) for c in wall))
    # a shaded return face, so the model cannot assume one flat tone
    if rnd.random() < 0.55:
        rw = rnd.randint(24, 60)
        d.polygon([(fx1, fy0), (fx1 + rw, fy0 + rnd.randint(10, 30)),
                   (fx1 + rw, fy1), (fx1, fy1)],
                  fill=tuple(max(0, c - 40) for c in wall))

    boxes: list[Box] = []
    floors = rnd.randint(4, 7)
    bays = rnd.randint(3, 6)
    fh = (fy1 - fy0) / floors
    bw = (fx1 - fx0) / bays
    gm_x, gm_y = bw * rnd.uniform(0.16, 0.30), fh * rnd.uniform(0.20, 0.34)

    # Every elevation is one of three archetypes so the two glazing classes are
    # genuinely separable by geometry, not by colour.
    archetype = rnd.choices(["punched", "curtain_bays", "mixed"], weights=[5, 3, 3])[0]

    for r in range(floors):
        y0 = fy0 + r * fh
        ground = (r == floors - 1)
        top = (r == 0)
        bay_is_curtain = archetype == "curtain_bays" or (
            archetype == "mixed" and rnd.random() < 0.4
        )

        if bay_is_curtain and not ground:
            # continuous glazed band across the whole floor -> curtain_wall
            b = Box("curtain_wall", fx0 + gm_x * 0.5, y0 + gm_y * 0.55,
                    fx1 - gm_x * 0.5, y0 + fh - gm_y * 0.55)
            _pane(d, b, glass, rnd, frame=2, mullions=True)
            boxes.append(b)
            if rnd.random() < 0.35:                       # balcony in front of it
                bb = Box("balcony", b.x0 + rnd.uniform(0, 40), b.y1 - 18,
                         b.x0 + rnd.uniform(120, 220), b.y1 + 10)
                _balustrade(d, bb, rnd)
                boxes.append(bb)
            continue

        for c in range(bays):
            x0 = fx0 + c * bw
            if ground and c == bays // 2:
                # ---- entrance ------------------------------------------------
                dw, dh = bw * 0.46, fh * 0.80
                b = Box("door", x0 + (bw - dw) / 2, y0 + fh - dh,
                        x0 + (bw + dw) / 2, y0 + fh - 2)
                _pane(d, b, tuple(max(0, g - 14) for g in glass), rnd, frame=4)
                d.line([(b.x0, b.y0), (b.x1, b.y0)], fill=(70, 70, 74), width=4)
                boxes.append(b)
                continue

            wx0, wy0 = x0 + gm_x / 2, y0 + gm_y / 2
            wx1, wy1 = x0 + bw - gm_x / 2, y0 + fh - gm_y / 2

            # ---- HARD POSITIVE 1: clerestory. Real, labelled, ~4 px tall. ----
            if top and rnd.random() < 0.30:
                wy0, wy1 = y0 + fh * 0.30, y0 + fh * 0.30 + rnd.uniform(3, 7)

            # ---- DECOY: opaque spandrel with glazing-like sheen, UNLABELLED --
            if rnd.random() < 0.13:
                d.rectangle([wx0, wy0, wx1, wy1],
                            fill=tuple(min(255, c + 16) for c in wall))
                d.polygon([(wx0, wy0), (wx1, wy0), (wx1, wy0 + (wy1 - wy0) * 0.3),
                           (wx0, wy0 + (wy1 - wy0) * 0.6)],
                          fill=tuple(min(255, c + 48) for c in wall))
                d.rectangle([wx0, wy0, wx1, wy1], outline=(140, 138, 134), width=2)
                continue

            b = Box("window", wx0, wy0, wx1, wy1)
            _pane(d, b, glass, rnd)
            boxes.append(b)

            if rnd.random() < 0.22 and not ground:
                bb = Box("balcony", b.x0 - 5, b.y1 - 12, b.x1 + 5, b.y1 + 14)
                _balustrade(d, bb, rnd)
                boxes.append(bb)

            if rnd.random() < 0.14:
                lb = Box("louvre_screen", b.x0, b.y0 - rnd.uniform(10, 20),
                         b.x1, b.y0 - 2)
                if lb.y0 > fy0:
                    _louvres(d, lb, rnd)
                    boxes.append(lb)

    # ---- plant screen on the roof ------------------------------------------
    if rnd.random() < 0.40:
        lw = rnd.uniform(70, 170)
        lx = rnd.uniform(fx0 + 10, max(fx0 + 11, fx1 - lw - 10))
        lb = Box("louvre_screen", lx, fy0 - rnd.uniform(18, 34), lx + lw, fy0 - 2)
        if lb.y0 > 4:
            _louvres(d, lb, rnd)
            boxes.append(lb)

    # ---- DECOY: ground-level signage that reads as a door, UNLABELLED -------
    if rnd.random() < 0.28:
        sw, sh = rnd.uniform(34, 62), rnd.uniform(70, 110)
        sx = rnd.uniform(fx0 + 8, max(fx0 + 9, fx1 - sw - 8))
        d.rectangle([sx, fy1 - sh, sx + sw, fy1 - 4],
                    fill=tuple(max(0, c - 70) for c in wall), outline=(88, 88, 92), width=3)

    # ---- NUISANCE: hard scaffold/pole shadow across the wall ---------------
    if rnd.random() < 0.45:
        ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        od = ImageDraw.Draw(ov)
        sx = rnd.uniform(fx0, fx1)
        od.polygon([(sx, fy0), (sx + rnd.uniform(8, 22), fy0),
                    (sx + rnd.uniform(40, 110), fy1), (sx + rnd.uniform(20, 70), fy1)],
                   fill=(0, 0, 0, rnd.randint(55, 100)))
        img = Image.alpha_composite(img.convert("RGBA"), ov).convert("RGB")
        d = ImageDraw.Draw(img)

    # ---- HARD POSITIVE 2: glare blowout over part of the façade ------------
    if rnd.random() < 0.30:
        ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        od = ImageDraw.Draw(ov)
        cx, cy = rnd.uniform(fx0, fx1), rnd.uniform(fy0, fy1)
        rr = rnd.uniform(70, 150)
        for k in range(9, 0, -1):
            od.ellipse([cx - rr * k / 9, cy - rr * k / 9, cx + rr * k / 9, cy + rr * k / 9],
                       fill=(255, 252, 238, int(190 * (1 - k / 10))))
        img = Image.alpha_composite(img.convert("RGBA"), ov).convert("RGB")
        d = ImageDraw.Draw(img)

    # ---- HARD POSITIVE 3: foreground tree occluding a bay ------------------
    if rnd.random() < 0.32:
        tx = rnd.uniform(fx0, fx1)
        d.rectangle([tx - 6, fy1 - 150, tx + 6, fy1 + 10], fill=(74, 58, 44))
        for _ in range(34):
            ox, oy = rnd.gauss(0, 34), rnd.gauss(-70, 42)
            rr = rnd.uniform(11, 26)
            d.ellipse([tx + ox - rr, fy1 + oy - rr, tx + ox + rr, fy1 + oy + rr],
                      fill=(rnd.randint(40, 78), rnd.randint(84, 130), rnd.randint(38, 70)))

    if rnd.random() < 0.35:
        img = img.filter(ImageFilter.GaussianBlur(rnd.uniform(0.4, 1.1)))

    # Drop degenerate boxes — a 1-px label is a labelling error, not a hard case.
    boxes = [b for b in boxes if b.area_px >= 20 and (b.x1 - b.x0) >= 3 and (b.y1 - b.y0) >= 2]
    return img, boxes


def build(out_dir: Path, n_train: int = 96, n_val: int = 24, seed: int = 42) -> Path:
    """Write a YOLO-format dataset (80/20 train/val) and its data.yaml."""
    out_dir = Path(out_dir)
    for split, n in (("train", n_train), ("valid", n_val)):
        (out_dir / split / "images").mkdir(parents=True, exist_ok=True)
        (out_dir / split / "labels").mkdir(parents=True, exist_ok=True)

    counts: dict[str, int] = {c: 0 for c in CLASSES}
    idx = 0
    for split, n in (("train", n_train), ("valid", n_val)):
        for _ in range(n):
            idx += 1
            img, boxes = generate_image(seed * 10_000 + idx)
            stem = f"facade_{split}_{idx:04d}"
            img.save(out_dir / split / "images" / f"{stem}.jpg", quality=90)
            (out_dir / split / "labels" / f"{stem}.txt").write_text(
                "\n".join(b.yolo() for b in boxes) + ("\n" if boxes else "")
            )
            for b in boxes:
                counts[b.cls] += 1

    yaml_path = out_dir / "data.yaml"
    yaml_path.write_text(
        "# Generated by src/synthetic_facades.py — VERIFICATION dataset, not a result.\n"
        f"path: {out_dir.resolve()}\n"
        "train: train/images\n"
        "val: valid/images\n"
        f"nc: {len(CLASSES)}\n"
        f"names: {CLASSES}\n"
    )
    total = n_train + n_val
    print(f"synthetic dataset -> {out_dir}")
    print(f"  images : {n_train} train / {n_val} val  ({n_train/total:.0%}/{n_val/total:.0%})")
    print("  instances per class:")
    for c, k in counts.items():
        print(f"    {c:<14} {k:>5}")
    return yaml_path


if __name__ == "__main__":
    import sys
    sys.path.insert(0, str(Path(__file__).parent))
    from config import DATASET_DIR
    build(DATASET_DIR / "synthetic")


def build_new_images(out_dir: Path, n: int = 5, seed: int = 9_999) -> Path:
    """
    Held-out elevations for the new-image demo.

    Generated from a seed range disjoint from build()'s, so these are images
    the model has never seen in training OR validation. LS3: "Never show a
    client a training image. They will think you cheated."

    When you run on a real dataset, replace these with real photographs in
    data/new_images/ — the notebook prefers whatever is already in that folder.
    """
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    for i in range(1, n + 1):
        img, _ = generate_image(seed * 100 + i)
        img.save(out_dir / f"unseen_facade_{i:02d}.jpg", quality=92)
    print(f"{n} held-out images -> {out_dir}")
    return out_dir
