"""
Resolve DATASET_SOURCE to a data.yaml on disk.

Three sources, one return type. The notebooks never branch on the source —
they call resolve_dataset() and get a path. That is what lets the same
notebook serve a stranger with no credentials and the author with a private
Roboflow project.
"""

from __future__ import annotations

import shutil
from pathlib import Path

import config as C


def _rewrite_yaml_paths(yaml_path: Path) -> Path:
    """
    Roboflow writes absolute or ../ paths into data.yaml that break the moment
    the folder moves — the single most common cause of a notebook that ran on
    the author's machine and dies on the reader's. Pin `path:` to the real
    parent directory and make the split keys relative to it.
    """
    import yaml

    root = yaml_path.parent.resolve()
    cfg = yaml.safe_load(yaml_path.read_text()) or {}
    cfg["path"] = str(root)
    for split, default in (("train", "train/images"), ("val", "valid/images"), ("test", "test/images")):
        val = cfg.get(split)
        if not val:
            if (root / default).exists():
                cfg[split] = default
            continue
        name = Path(str(val).replace("\\", "/")).as_posix()
        for marker in ("train/", "valid/", "val/", "test/"):
            if marker in name:
                name = name[name.index(marker):]
                break
        cfg[split] = name
    cfg["nc"] = len(C.CLASSES)
    cfg["names"] = C.CLASSES
    yaml_path.write_text(yaml.safe_dump(cfg, sort_keys=False))
    return yaml_path


def _verify_class_contract(yaml_path: Path) -> None:
    """
    Fail loudly if the downloaded dataset's class order differs from
    config.CLASSES. Class ids are positional: a silently reordered list turns
    every 'window' label into 'curtain_wall' and the metrics will look fine.
    """
    import yaml

    names = (yaml.safe_load(yaml_path.read_text()) or {}).get("names", [])
    if isinstance(names, dict):
        names = [names[k] for k in sorted(names)]
    if list(names) != list(C.CLASSES):
        raise SystemExit(
            "CLASS CONTRACT MISMATCH — refusing to train.\n"
            f"  data.yaml   : {list(names)}\n"
            f"  config.py   : {list(C.CLASSES)}\n"
            "Class ids are positional. Fix the order in Roboflow or in "
            "src/config.py so the two agree, then re-run."
        )


def resolve_dataset(force_rebuild: bool = False) -> Path:
    """Return a path to a usable data.yaml for the configured source."""
    src = C.DATASET_SOURCE.lower()

    # ---------------------------------------------------------- synthetic ---
    if src == "synthetic":
        import synthetic_facades

        out = C.DATASET_DIR / "synthetic"
        yaml_path = out / "data.yaml"
        if force_rebuild and out.exists():
            shutil.rmtree(out)
        if not yaml_path.exists():
            synthetic_facades.build(out)
        else:
            print(f"synthetic dataset already present -> {out}")
        print("\n  NOTE: this is the VERIFICATION dataset. It proves the pipeline runs.\n"
              "        It is not evidence of real-world façade detection performance.\n")
        return yaml_path

    # ------------------------------------------------- roboflow / universe --
    if src in ("roboflow", "universe"):
        key = C.api_key()
        if not key:
            raise SystemExit(
                f"DATASET_SOURCE='{src}' but no API key found.\n"
                f"  Colab : sidebar key icon -> add secret named {C.ROBOFLOW_API_KEY_ENV}\n"
                f"  Local : export {C.ROBOFLOW_API_KEY_ENV}='...'\n"
                "Or set DATASET_SOURCE='synthetic' to run the pipeline without an account."
            )
        if not (C.ROBOFLOW_WORKSPACE and C.ROBOFLOW_PROJECT):
            raise SystemExit(
                "Set ROBOFLOW_WORKSPACE and ROBOFLOW_PROJECT in src/config.py.\n"
                "Read them straight off your project URL:\n"
                "  https://app.roboflow.com/<WORKSPACE>/<PROJECT>/<VERSION>"
            )
        from roboflow import Roboflow

        out = C.DATASET_DIR / f"{C.ROBOFLOW_PROJECT}-v{C.ROBOFLOW_VERSION}"
        if force_rebuild and out.exists():
            shutil.rmtree(out)
        if not (out / "data.yaml").exists():
            rf = Roboflow(api_key=key)
            ds = (rf.workspace(C.ROBOFLOW_WORKSPACE)
                    .project(C.ROBOFLOW_PROJECT)
                    .version(C.ROBOFLOW_VERSION)
                    .download(C.ROBOFLOW_FORMAT, location=str(out)))
            print(f"downloaded -> {ds.location}")
        else:
            print(f"dataset already present -> {out}")
        yaml_path = _rewrite_yaml_paths(out / "data.yaml")
        _verify_class_contract(yaml_path)
        return yaml_path

    raise SystemExit(
        f"Unknown DATASET_SOURCE={C.DATASET_SOURCE!r}. "
        "Use 'synthetic', 'roboflow' or 'universe'."
    )


def describe(yaml_path: Path) -> dict:
    """Count images and per-class instances — the dataset health check."""
    import yaml as _yaml
    from collections import Counter

    cfg = _yaml.safe_load(Path(yaml_path).read_text())
    root = Path(cfg.get("path", Path(yaml_path).parent))
    report = {"yaml": str(yaml_path), "splits": {}, "per_class": {}}
    total = Counter()

    for split in ("train", "val", "test"):
        rel = cfg.get(split)
        if not rel:
            continue
        img_dir = root / rel
        if not img_dir.exists():
            continue
        imgs = [p for p in img_dir.iterdir()
                if p.suffix.lower() in (".jpg", ".jpeg", ".png", ".bmp", ".webp")]
        lbl_dir = img_dir.parent / "labels"
        counts, empties = Counter(), 0
        for p in imgs:
            f = lbl_dir / f"{p.stem}.txt"
            if not f.exists() or not f.read_text().strip():
                empties += 1
                continue
            for line in f.read_text().splitlines():
                if line.strip():
                    counts[int(line.split()[0])] += 1
        report["splits"][split] = {
            "images": len(imgs), "instances": sum(counts.values()), "unlabelled_images": empties
        }
        total.update(counts)
        report["per_class"][split] = {C.CLASSES[i]: counts.get(i, 0) for i in range(len(C.CLASSES))}

    n = sum(s["images"] for s in report["splits"].values())
    report["split_ratio"] = {
        k: f"{v['images'] / n:.0%}" for k, v in report["splits"].items()
    } if n else {}
    report["per_class"]["TOTAL"] = {C.CLASSES[i]: total.get(i, 0) for i in range(len(C.CLASSES))}

    # Class imbalance is the single most useful number for the error analysis.
    vals = [v for v in report["per_class"]["TOTAL"].values() if v]
    report["imbalance_ratio"] = round(max(vals) / min(vals), 1) if len(vals) > 1 else 1.0
    return report


if __name__ == "__main__":
    import json
    print(json.dumps(describe(resolve_dataset()), indent=2))
