"""
Build the evidence pack the brief asks for, as files rather than screenshots.

    results/evidence/annotations/   3-5 ground-truth annotation examples
    results/evidence/validation/    10 validation predictions
    results/evidence/new_images/    5 predictions on images the model never saw
    results/evidence/errors/        worst FP / FN / confusion / drift  (error_analysis.py)

Screenshots are acceptable to the brief, but they are lossy, undated and
impossible to regenerate. Everything here is produced by code from the
committed weights, so `Run all` refreshes the whole pack and a reviewer can
tell exactly which run produced which picture.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import config as C

PALETTE = {                      # Group 02 design-system series colours
    "window":        (28, 96, 243),
    "curtain_wall":  (65, 207, 151),
    "door":          (123, 79, 224),
    "balcony":       (221, 107, 32),
    "louvre_screen": (23, 162, 184),
}


def _font(size: int = 15):
    from PIL import ImageFont
    for p in ("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
              "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"):
        if Path(p).exists():
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                pass
    return ImageFont.load_default()


def _draw(im, boxes, title: str):
    """boxes: [(class_name, [x0,y0,x1,y1], label_or_None)]"""
    from PIL import ImageDraw
    d = ImageDraw.Draw(im)
    f, ft = _font(15), _font(17)
    for cls, box, label in boxes:
        col = PALETTE.get(cls, (74, 85, 104))
        d.rectangle(box, outline=col, width=3)
        if label:
            tw = d.textlength(label, font=f)
            ty = max(0, box[1] - 19)
            d.rectangle([box[0], ty, box[0] + tw + 8, ty + 19], fill=col)
            d.text((box[0] + 4, ty + 2), label, fill=(255, 255, 255), font=f)
    d.rectangle([0, 0, im.width, 28], fill=(27, 31, 35))
    d.text((8, 5), title, fill=(255, 255, 255), font=ft)
    return im


def annotation_examples(data_yaml: Path, n: int = 5):
    """Render ground-truth labels — proof the annotation contract was applied."""
    import yaml as _yaml
    from PIL import Image
    from error_analysis import _load_gt

    cfg = _yaml.safe_load(Path(data_yaml).read_text())
    root = Path(cfg.get("path", Path(data_yaml).parent))
    img_dir = root / cfg["train"]
    lbl_dir = img_dir.parent / "labels"
    out = C.EVIDENCE_DIR / "annotations"
    out.mkdir(parents=True, exist_ok=True)

    imgs = sorted(p for p in img_dir.iterdir()
                  if p.suffix.lower() in (".jpg", ".jpeg", ".png"))
    picked, k = [], 0
    for p in imgs:
        gt = _load_gt(lbl_dir / f"{p.stem}.txt", *Image.open(p).size)
        if len({c for c, _ in gt}) < 2:          # prefer multi-class examples
            continue
        k += 1
        im = Image.open(p).convert("RGB")
        _draw(im, [(C.CLASSES[c], b, C.CLASSES[c]) for c, b in gt],
              f"GROUND TRUTH  ·  {p.name}  ·  {len(gt)} instances")
        dst = out / f"annotation_{k:02d}_{p.stem}.jpg"
        im.save(dst, quality=92)
        picked.append(dst.name)
        if k >= n:
            break
    print(f"{len(picked)} annotation examples -> {out}")
    return picked


def predictions(weights: Path, image_paths: list[Path], out_dir: Path,
                tag: str, conf: float | None = None):
    """Render model predictions with class, confidence and a VE quantity read-out."""
    from PIL import Image
    from ultralytics import YOLO

    conf = C.CONF_THRESHOLD if conf is None else conf
    out_dir.mkdir(parents=True, exist_ok=True)
    model = YOLO(str(weights))
    manifest = []

    for k, p in enumerate(sorted(image_paths), 1):
        res = model.predict(str(p), conf=conf, iou=C.IOU_THRESHOLD, verbose=False)[0]
        im = Image.open(p).convert("RGB")
        boxes, dets = [], []
        for b in res.boxes:
            cls = C.CLASSES[int(b.cls.item())]
            xy = [float(v) for v in b.xyxy[0].tolist()]
            cf = float(b.conf.item())
            boxes.append((cls, xy, f"{cls} {cf:.2f}"))
            dets.append({"class": cls, "conf": round(cf, 3),
                         "box": [round(v, 1) for v in xy]})
        _draw(im, boxes, f"{tag.upper()}  ·  {p.name}  ·  {len(dets)} det @ conf≥{conf}")
        dst = out_dir / f"{tag}_{k:02d}_{p.stem}.jpg"
        im.save(dst, quality=92)
        manifest.append({"file": dst.name, "source": p.name,
                         "detections": dets, "ve": ve_readout(dets, im.size)})

    (out_dir / "manifest.json").write_text(json.dumps(manifest, indent=2))
    print(f"{len(manifest)} {tag} predictions -> {out_dir}")
    return manifest


def ve_readout(detections: list[dict], image_size) -> dict:
    """
    Turn raw detections into the two numbers the FMP's VE assistant consumes.

    This is the whole point of the detector. A bounding box is not a
    deliverable; a Window-to-Wall Ratio and an indicative envelope cost are.

    HEALTH WARNING, stated here and in the report: these are PIXEL-DOMAIN
    figures from an uncalibrated single image. Without a known scale, a camera
    pose or a reference dimension they are a relative screening signal for
    comparing design options, never a quantity take-off. LS1 Q&A is explicit
    that dimensional inference from raw pixels with no scale is unsolved.
    """
    w, h = image_size
    frame_area = float(w * h)
    by_class: dict[str, dict] = {}
    for d in detections:
        x0, y0, x1, y1 = d["box"]
        a = max(0.0, x1 - x0) * max(0.0, y1 - y0)
        e = by_class.setdefault(d["class"], {"count": 0, "px_area": 0.0})
        e["count"] += 1
        e["px_area"] += a

    glazed = sum(v["px_area"] for k, v in by_class.items() if k in ("window", "curtain_wall"))
    wwr = glazed / frame_area if frame_area else 0.0
    cost_index = sum(
        v["px_area"] / frame_area * C.VE_UNIT_RATES_EUR_M2.get(k, 0.0)
        for k, v in by_class.items()
    )
    return {
        "glazed_fraction_of_frame": round(wwr, 4),
        "envelope_cost_index": round(cost_index, 1),
        "counts": {k: v["count"] for k, v in by_class.items()},
        "basis": "uncalibrated pixel areas — relative screening signal, not a take-off",
    }


def build_all(weights: Path, data_yaml: Path, n_val: int = 10, n_new: int = 5):
    import yaml as _yaml

    annotation_examples(data_yaml, n=5)

    cfg = _yaml.safe_load(Path(data_yaml).read_text())
    root = Path(cfg.get("path", Path(data_yaml).parent))
    val_imgs = sorted(p for p in (root / cfg["val"]).iterdir()
                      if p.suffix.lower() in (".jpg", ".jpeg", ".png"))[:n_val]
    predictions(weights, val_imgs, C.EVIDENCE_DIR / "validation", "val")

    new_dir = C.NEW_IMAGES_DIR
    new_imgs = sorted(p for p in new_dir.iterdir()
                      if p.suffix.lower() in (".jpg", ".jpeg", ".png")) if new_dir.exists() else []
    if new_imgs:
        predictions(weights, new_imgs[:n_new], C.EVIDENCE_DIR / "new_images", "new")
    else:
        print(f"no images in {new_dir} — add unseen photographs there for the new-image pack")

    from error_analysis import analyse
    analyse(weights, data_yaml)


if __name__ == "__main__":
    from dataset import resolve_dataset
    build_all(C.RESULTS_DIR / "weights" / "best.pt", resolve_dataset())
