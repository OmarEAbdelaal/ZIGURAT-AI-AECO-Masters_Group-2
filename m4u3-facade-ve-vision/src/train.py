"""Train the detector and persist everything the README claims."""

from __future__ import annotations

import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import config as C
from dataset import resolve_dataset, describe


def train(force_rebuild: bool = False, **overrides):
    from ultralytics import YOLO
    import torch

    data_yaml = resolve_dataset(force_rebuild=force_rebuild)
    health = describe(data_yaml)
    print(json.dumps(health, indent=2))

    kwargs = C.TRAIN.as_kwargs() | overrides
    kwargs["project"] = str(C.REPO_ROOT / kwargs["project"])
    device = 0 if torch.cuda.is_available() else "cpu"

    started = datetime.now(timezone.utc)
    print(f"\ntraining on {device} | {kwargs['epochs']} epochs | "
          f"imgsz={kwargs['imgsz']} | batch={kwargs['batch']}\n")

    model = YOLO(C.TRAIN.model)
    model.train(data=str(data_yaml), device=device, exist_ok=True, plots=True, **kwargs)
    elapsed = (datetime.now(timezone.utc) - started).total_seconds()

    run_dir = Path(model.trainer.save_dir)
    metrics = model.val(data=str(data_yaml), device=device, split="val",
                        conf=0.001, iou=C.IOU_THRESHOLD, plots=True)

    _persist(run_dir, metrics, health, elapsed, device, data_yaml)
    return run_dir, metrics


def _persist(run_dir: Path, metrics, health: dict, elapsed: float, device, data_yaml: Path) -> None:
    """Copy curves into results/ and write the metrics table the README quotes."""
    import ultralytics, torch

    C.CURVES_DIR.mkdir(parents=True, exist_ok=True)
    C.METRICS_DIR.mkdir(parents=True, exist_ok=True)
    (C.RESULTS_DIR / "weights").mkdir(parents=True, exist_ok=True)

    # Ultralytics renamed the curve plots between releases (PR_curve.png ->
    # BoxPR_curve.png in 8.4). Copy whatever the installed version produced and
    # normalise the name, so results/curves/ and the README agree on either.
    wanted = ("results.png", "confusion_matrix_normalized.png", "confusion_matrix.png",
              "labels.jpg", "results.csv")
    for name in wanted:
        src = run_dir / name
        if src.exists():
            shutil.copy2(src, C.CURVES_DIR / name)

    for stem in ("PR", "P", "R", "F1"):
        for candidate in (f"Box{stem}_curve.png", f"{stem}_curve.png"):
            src = run_dir / candidate
            if src.exists():
                shutil.copy2(src, C.CURVES_DIR / f"{stem}_curve.png")
                break

    best = run_dir / "weights" / "best.pt"
    if best.exists():
        shutil.copy2(best, C.RESULTS_DIR / "weights" / "best.pt")

    box = metrics.box
    per_class = []
    for i, ci in enumerate(box.ap_class_index):
        p, r, ap50, ap = box.class_result(i)
        per_class.append({
            "class": C.CLASSES[int(ci)],
            "instances": int(health["per_class"].get("val", {}).get(C.CLASSES[int(ci)], 0)),
            "precision": round(float(p), 4),
            "recall": round(float(r), 4),
            "mAP50": round(float(ap50), 4),
            "mAP50_95": round(float(ap), 4),
        })

    payload = {
        "run_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "dataset_source": C.DATASET_SOURCE,
        "is_verification_run": C.DATASET_SOURCE == "synthetic",
        "data_yaml": str(data_yaml),
        "dataset_health": health,
        "device": str(device),
        "gpu": torch.cuda.get_device_name(0) if torch.cuda.is_available() else "CPU only",
        "train_seconds": round(elapsed, 1),
        "ultralytics": ultralytics.__version__,
        "torch": torch.__version__,
        "config": {"model": C.TRAIN.model, **C.TRAIN.as_kwargs()},
        "overall": {
            "precision": round(float(box.mp), 4),
            "recall": round(float(box.mr), 4),
            "mAP50": round(float(box.map50), 4),
            "mAP50_95": round(float(box.map), 4),
        },
        "per_class": per_class,
    }
    (C.METRICS_DIR / "metrics.json").write_text(json.dumps(payload, indent=2))

    import csv
    with (C.METRICS_DIR / "metrics_per_class.csv").open("w", newline="") as fh:
        # lineterminator="\n": csv defaults to CRLF, which makes git flag the file
        # on every platform switch and shows the whole table as changed in a diff.
        w = csv.DictWriter(fh, lineterminator="\n",
                           fieldnames=["class", "instances", "precision", "recall", "mAP50", "mAP50_95"])
        w.writeheader()
        w.writerows(per_class)

    (C.METRICS_DIR / "metrics.md").write_text(_markdown(payload))
    print(f"\nmetrics -> {C.METRICS_DIR}\ncurves  -> {C.CURVES_DIR}")


def _markdown(p: dict) -> str:
    o = p["overall"]
    banner = (
        "> **VERIFICATION RUN — not a performance claim.** These numbers come from the "
        "procedural dataset in `src/synthetic_facades.py`, which exists to prove the pipeline "
        "executes end to end without credentials. Synthetic façades are axis-aligned and "
        "synthetically lit; the domain gap to a photograph is large. Replace with a "
        "`DATASET_SOURCE=\"roboflow\"` run before quoting any figure as a result.\n"
        if p["is_verification_run"] else
        "> Produced from the Roboflow dataset named in `src/config.py`.\n"
    )
    rows = "\n".join(
        f"| `{c['class']}` | {c['instances']} | {c['precision']:.3f} | {c['recall']:.3f} "
        f"| {c['mAP50']:.3f} | **{c['mAP50_95']:.3f}** |"
        for c in p["per_class"]
    )
    cfg = p["config"]
    return f"""# Metrics — {p['config']['model']} on `{p['dataset_source']}`

{banner}
Run (UTC): `{p['run_utc']}` · device: `{p['gpu']}` · train time: {p['train_seconds']:.0f}s
`ultralytics {p['ultralytics']}` · `torch {p['torch']}`

## Overall (validation split, IoU 0.50)

| Precision | Recall | mAP50 | mAP50-95 |
|---|---|---|---|
| {o['precision']:.3f} | {o['recall']:.3f} | {o['mAP50']:.3f} | **{o['mAP50_95']:.3f}** |

`mAP50-95` is the headline metric for this project. Value Engineering quantities are
derived from **box area**, so a box that is 20 % too large is a 20 % cost error even
though `mAP50` would still score it a hit. Only the IoU-strict metric penalises that.

## Per class

| Class | Val instances | Precision | Recall | mAP50 | mAP50-95 |
|---|---|---|---|---|---|
{rows}

## Reproduction parameters

| Parameter | Value |
|---|---|
| model | `{cfg['model']}` |
| epochs | {cfg['epochs']} |
| batch | {cfg['batch']} |
| imgsz | {cfg['imgsz']} |
| seed | {cfg['seed']} |
| patience | {cfg['patience']} |
| cos_lr | {cfg['cos_lr']} |
| ultralytics | `{p['ultralytics']}` |

<sub>Generated by `src/train.py`. Do not edit by hand — re-run the notebook instead.</sub>
"""


if __name__ == "__main__":
    train()
