"""
Single source of truth for every parameter this project reports.

THIS IS THE ONLY FILE YOU NEED TO EDIT to point the pipeline at your own
Roboflow dataset and your own trained weights. The README, the notebooks,
the metrics tables and the evidence pack all read from here, so a value
changed here propagates everywhere and cannot go stale in one place only.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, asdict
from pathlib import Path

# --------------------------------------------------------------------------
# 1. WHERE THE DATASET COMES FROM
# --------------------------------------------------------------------------
# "roboflow"  -> your own Roboflow project (needs ROBOFLOW_API_KEY)
# "universe"  -> a public Roboflow Universe project you have forked
# "synthetic" -> the self-contained procedural dataset in synthetic_facades.py
#                No credentials, no network, no account. Always runs.
#                Use it to PROVE THE PIPELINE, never to claim a result.
DATASET_SOURCE = os.environ.get("DATASET_SOURCE", "synthetic")

# Fill these in from your Roboflow project URL:
#   https://app.roboflow.com/<WORKSPACE>/<PROJECT>/<VERSION>
ROBOFLOW_WORKSPACE = os.environ.get("ROBOFLOW_WORKSPACE", "")   # e.g. "group02-aeco"
ROBOFLOW_PROJECT   = os.environ.get("ROBOFLOW_PROJECT",   "")   # e.g. "facade-ve-elements"
ROBOFLOW_VERSION   = int(os.environ.get("ROBOFLOW_VERSION", "1"))
ROBOFLOW_FORMAT    = "yolov8"

# The API key is read from the environment or a Colab secret. It is NEVER
# written into a notebook cell, a config file or a commit.
#   Colab:  key icon in the left sidebar -> name it ROBOFLOW_API_KEY
#   Local:  export ROBOFLOW_API_KEY="..."
ROBOFLOW_API_KEY_ENV = "ROBOFLOW_API_KEY"

# Public, human-readable dataset reference quoted in the README and the report.
DATASET_PUBLIC_URL = os.environ.get("DATASET_PUBLIC_URL", "")   # Roboflow Universe link


# --------------------------------------------------------------------------
# 2. THE CLASS CONTRACT
# --------------------------------------------------------------------------
# Order is load-bearing: it is the class-id order in every .txt label file.
# Changing the order silently invalidates every existing label. Append only.
CLASSES: list[str] = [
    "window",        # 0 - discrete punched glazed opening in an opaque wall
    "curtain_wall",  # 1 - continuous glazed façade zone, no opaque interruption
    "door",          # 2 - ground-level pedestrian entrance / egress opening
    "balcony",       # 3 - projecting or recessed occupiable slab with balustrade
    "louvre_screen", # 4 - fixed slatted solar-shading or plant-screening element
]
NC = len(CLASSES)

# Cost weighting used by the VE read-out (indicative €/m² of element face area,
# design-stage order of magnitude only — see docs/problem_framing.md).
VE_UNIT_RATES_EUR_M2: dict[str, float] = {
    "window":        520.0,
    "curtain_wall":  780.0,
    "door":          640.0,
    "balcony":       410.0,
    "louvre_screen": 350.0,
}


# --------------------------------------------------------------------------
# 3. TRAINING CONTRACT  (quoted verbatim in the README reproducibility table)
# --------------------------------------------------------------------------
@dataclass(frozen=True)
class TrainConfig:
    model: str = "yolov8n.pt"   # n = nano. Session 3: start small, scale if mAP plateaus.
    epochs: int = 30            # >= 30 per the brief. < 30 underfits, > 100 overfits at this size.
    batch: int = 16             # Session 3 sweet spot for a free Colab T4.
    imgsz: int = 640            # Standard. Raise to 1280 only for hairline-scale targets.
    seed: int = 42              # Fixed so a re-run reproduces the same split shuffling.
    patience: int = 20          # Early stop on plateau; guards the "U-turn" overfit case.
    optimizer: str = "auto"
    cos_lr: bool = True
    deterministic: bool = True
    run_name: str = "facade_ve_v1"
    project_dir: str = "runs/detect"

    def as_kwargs(self) -> dict:
        d = asdict(self)
        d.pop("model")
        d["name"] = d.pop("run_name")
        d["project"] = d.pop("project_dir")
        return d


TRAIN = TrainConfig()


# --------------------------------------------------------------------------
# 4. INFERENCE CONTRACT
# --------------------------------------------------------------------------
# Value Engineering quantity take-off is driven by BOX AREA, so a loose box is
# a wrong cost. We therefore report mAP50-95 as the headline metric (it is
# IoU-strict and punishes sloppy boxes) rather than the friendlier mAP50, and
# we hold confidence a little high to keep phantom quantities out of the model.
CONF_THRESHOLD = 0.35
IOU_THRESHOLD  = 0.50
HEADLINE_METRIC = "mAP50-95"

# Where the trained weights live for a third party who does not want to train.
# Publish best.pt as a GitHub Release asset and paste the direct URL here.
WEIGHTS_URL = os.environ.get("WEIGHTS_URL", "")
WEIGHTS_LOCAL_FALLBACK = "results/weights/best.pt"


# --------------------------------------------------------------------------
# 5. PATHS  (repo-relative, resolved from this file — never absolute, never
#            a Desktop path. The "File Not Found" test in LS4 is graded.)
# --------------------------------------------------------------------------
REPO_ROOT       = Path(__file__).resolve().parent.parent
DATA_DIR        = REPO_ROOT / "data"
DATASET_DIR     = DATA_DIR / "dataset"          # gitignored: images never committed
DATA_YAML       = DATA_DIR / "data.yaml"
RESULTS_DIR     = REPO_ROOT / "results"
METRICS_DIR     = RESULTS_DIR / "metrics"
CURVES_DIR      = RESULTS_DIR / "curves"
EVIDENCE_DIR    = RESULTS_DIR / "evidence"
NEW_IMAGES_DIR  = DATA_DIR / "new_images"       # unseen photos for the honest demo
DOCS_DIR        = REPO_ROOT / "docs"


def api_key() -> str:
    """Fetch the Roboflow key from the environment or a Colab secret."""
    key = os.environ.get(ROBOFLOW_API_KEY_ENV, "")
    if key:
        return key
    try:  # Colab secret manager
        from google.colab import userdata  # type: ignore
        return userdata.get(ROBOFLOW_API_KEY_ENV) or ""
    except Exception:
        return ""


def summary() -> str:
    """One block a reader can paste into an issue when something disagrees."""
    import platform, sys
    try:
        import ultralytics, torch
        ul, tv = ultralytics.__version__, torch.__version__
        gpu = torch.cuda.get_device_name(0) if torch.cuda.is_available() else "CPU only"
    except Exception:
        ul = tv = gpu = "not installed"
    return "\n".join([
        f"dataset source   : {DATASET_SOURCE}",
        f"roboflow project : {ROBOFLOW_WORKSPACE}/{ROBOFLOW_PROJECT} v{ROBOFLOW_VERSION}"
                             if ROBOFLOW_WORKSPACE else "roboflow project : (not configured)",
        f"classes ({NC})     : {', '.join(CLASSES)}",
        f"model            : {TRAIN.model}",
        f"epochs/batch/imgsz: {TRAIN.epochs} / {TRAIN.batch} / {TRAIN.imgsz}",
        f"seed             : {TRAIN.seed}",
        f"conf / iou       : {CONF_THRESHOLD} / {IOU_THRESHOLD}",
        f"ultralytics      : {ul}",
        f"torch            : {tv}",
        f"device           : {gpu}",
        f"python           : {sys.version.split()[0]} on {platform.platform()}",
    ])


if __name__ == "__main__":
    print(summary())
