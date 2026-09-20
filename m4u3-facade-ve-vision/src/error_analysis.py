"""
Mine the validation set for the four AECO error types defined in Session 3.

    False Positive     the hallucination   — detected something that is not there
    False Negative     the miss            — failed to see something that is
    Class Confusion    the mix-up          — right object, wrong name
    Localization Error the drift           — right object, right name, sloppy box

Anecdotal error analysis ("I looked through some images and found a bad one")
is not reproducible and not auditable. This module ranks every error in the
validation split by confidence (for FPs) or by instance size (for FNs), crops
the worst offenders, and writes them out with the numbers attached, so
docs/error_analysis.md cites evidence instead of recollection.

LOCALIZATION ERROR is separated out deliberately. For a Value Engineering
read-out the quantity comes from box area, so a correctly-classified box at
IoU 0.55 is a 45 %-wrong quantity while mAP50 still counts it as a success.
That failure is invisible in the headline metric and expensive in the model.
"""

from __future__ import annotations

import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import config as C

LOC_ERROR_IOU = 0.75   # matched, correct class, but below this IoU = drift
MATCH_IOU     = 0.50   # below this there is no match at all


def _iou(a, b) -> float:
    ix0, iy0 = max(a[0], b[0]), max(a[1], b[1])
    ix1, iy1 = min(a[2], b[2]), min(a[3], b[3])
    iw, ih = max(0.0, ix1 - ix0), max(0.0, iy1 - iy0)
    inter = iw * ih
    if inter <= 0:
        return 0.0
    ua = (a[2] - a[0]) * (a[3] - a[1]) + (b[2] - b[0]) * (b[3] - b[1]) - inter
    return inter / ua if ua > 0 else 0.0


def _load_gt(label_path: Path, w: int, h: int):
    out = []
    if not label_path.exists():
        return out
    for line in label_path.read_text().splitlines():
        parts = line.split()
        if len(parts) < 5:
            continue
        cid, cx, cy, bw, bh = int(parts[0]), *map(float, parts[1:5])
        out.append((cid, [(cx - bw / 2) * w, (cy - bh / 2) * h,
                          (cx + bw / 2) * w, (cy + bh / 2) * h]))
    return out


def analyse(weights: Path, data_yaml: Path, conf: float | None = None, max_crops: int = 6):
    """Run the model over val, classify every error, crop the worst, write JSON+MD."""
    import yaml as _yaml
    from PIL import Image, ImageDraw
    from ultralytics import YOLO

    conf = C.CONF_THRESHOLD if conf is None else conf
    cfg = _yaml.safe_load(Path(data_yaml).read_text())
    root = Path(cfg.get("path", Path(data_yaml).parent))
    img_dir = root / cfg["val"]
    lbl_dir = img_dir.parent / "labels"
    images = sorted(p for p in img_dir.iterdir()
                    if p.suffix.lower() in (".jpg", ".jpeg", ".png", ".bmp", ".webp"))

    model = YOLO(str(weights))
    tally = Counter()
    fps, fns, confusions, drifts = [], [], [], []
    per_class_fn = defaultdict(int)
    per_class_fp = defaultdict(int)

    for img_path in images:
        im = Image.open(img_path).convert("RGB")
        w, h = im.size
        gt = _load_gt(lbl_dir / f"{img_path.stem}.txt", w, h)
        res = model.predict(str(img_path), conf=conf, iou=C.IOU_THRESHOLD, verbose=False)[0]

        preds = []
        for b in res.boxes:
            preds.append((int(b.cls.item()), [float(v) for v in b.xyxy[0].tolist()],
                          float(b.conf.item())))
        preds.sort(key=lambda p: -p[2])

        used = set()
        for pi, (pcls, pbox, pconf) in enumerate(preds):
            best_j, best_iou = -1, 0.0
            for j, (gcls, gbox) in enumerate(gt):
                if j in used:
                    continue
                v = _iou(pbox, gbox)
                if v > best_iou:
                    best_iou, best_j = v, j
            rec = {"image": img_path.name, "pred_class": C.CLASSES[pcls],
                   "conf": round(pconf, 3), "iou": round(best_iou, 3), "box": pbox}
            if best_iou < MATCH_IOU:
                tally["false_positive"] += 1
                per_class_fp[C.CLASSES[pcls]] += 1
                fps.append(rec)
                continue
            used.add(best_j)
            gcls = gt[best_j][0]
            rec["true_class"] = C.CLASSES[gcls]
            rec["gt_box"] = gt[best_j][1]
            if gcls != pcls:
                tally["class_confusion"] += 1
                confusions.append(rec)
            elif best_iou < LOC_ERROR_IOU:
                tally["localization_error"] += 1
                drifts.append(rec)
            else:
                tally["true_positive"] += 1

        for j, (gcls, gbox) in enumerate(gt):
            if j not in used:
                tally["false_negative"] += 1
                per_class_fn[C.CLASSES[gcls]] += 1
                area = (gbox[2] - gbox[0]) * (gbox[3] - gbox[1])
                fns.append({"image": img_path.name, "true_class": C.CLASSES[gcls],
                            "box": gbox, "area_px": round(area, 1),
                            "rel_area": round(area / (w * h), 5)})

    fps.sort(key=lambda r: -r["conf"])                 # most confident hallucinations first
    fns.sort(key=lambda r: r["area_px"])               # smallest misses first (scale story)
    confusions.sort(key=lambda r: -r["conf"])
    drifts.sort(key=lambda r: r["iou"])                # worst drift first

    out_dir = C.EVIDENCE_DIR / "errors"
    out_dir.mkdir(parents=True, exist_ok=True)
    for tag, rows in (("fp", fps), ("fn", fns), ("confusion", confusions), ("drift", drifts)):
        for k, r in enumerate(rows[:max_crops], 1):
            im = Image.open(img_dir / r["image"]).convert("RGB")
            d = ImageDraw.Draw(im)
            if "gt_box" in r:
                d.rectangle(r["gt_box"], outline=(65, 207, 151), width=3)   # truth = green
            if tag == "fn":
                d.rectangle(r["box"], outline=(221, 107, 32), width=3)      # missed = orange
            else:
                d.rectangle(r["box"], outline=(224, 49, 49), width=3)       # prediction = red
            x0, y0, x1, y1 = r["box"]
            pad = 64
            crop = im.crop((max(0, x0 - pad), max(0, y0 - pad),
                            min(im.width, x1 + pad), min(im.height, y1 + pad)))
            if min(crop.size) < 160:
                s = 160 / max(1, min(crop.size))
                crop = crop.resize((int(crop.width * s), int(crop.height * s)))
            crop.save(out_dir / f"{tag}_{k:02d}_{Path(r['image']).stem}.jpg", quality=92)

    total_err = sum(tally[k] for k in
                    ("false_positive", "false_negative", "class_confusion", "localization_error"))
    payload = {
        "weights": str(weights), "conf_threshold": conf,
        "match_iou": MATCH_IOU, "localization_error_iou": LOC_ERROR_IOU,
        "images_evaluated": len(images),
        "tally": dict(tally), "total_errors": total_err,
        "false_positives_by_class": dict(per_class_fp),
        "false_negatives_by_class": dict(per_class_fn),
        "worst_false_positives": fps[:max_crops],
        "worst_false_negatives": fns[:max_crops],
        "worst_class_confusions": confusions[:max_crops],
        "worst_localization_errors": drifts[:max_crops],
    }
    C.METRICS_DIR.mkdir(parents=True, exist_ok=True)
    (C.METRICS_DIR / "error_analysis.json").write_text(json.dumps(payload, indent=2))
    print(json.dumps({"tally": dict(tally), "total_errors": total_err}, indent=2))
    print(f"error crops -> {out_dir}")
    return payload


if __name__ == "__main__":
    from dataset import resolve_dataset
    w = C.RESULTS_DIR / "weights" / "best.pt"
    analyse(w, resolve_dataset())
