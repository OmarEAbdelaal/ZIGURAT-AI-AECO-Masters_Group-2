# Reproducibility Proof

> Session 4's acceptance test: *"A stranger should be able to open your GitHub link and
> reproduce your results in Google Colab without asking you a single question."*
> This page records that it was actually done, by whom, on what, and how long it took.

---

## Last successful end-to-end run

| | |
|---|---|
| **Date / time (UTC)** | **2026-09-20 19:57:07** |
| **What ran** | `02_train_and_evaluate.ipynb` → `03_inference_and_evidence.ipynb`, restart-and-run-all, from a clean checkout |
| **Dataset** | `DATASET_SOURCE="synthetic"` — 96 train / 24 val (80/20), 2 578 instances |
| **Hardware** | **CPU only** — Intel Xeon @ 2.10 GHz, no GPU present |
| **Training time** | **499 s (8 min 19 s)** for 30 epochs, ≈ 16.6 s/epoch |
| **Evidence pack** | ≈ 90 s |
| **ultralytics** | `8.4.157` |
| **torch** | `2.14.0+cu130` |
| **Python** | `3.11.15` on Linux |
| **Result** | P **0.975** · R **0.946** · mAP50 **0.948** · mAP50-95 **0.879** |
| **Outcome** | ✅ Completed with no manual intervention and no edits to any cell |

Full machine-readable record: [`results/metrics/metrics.json`](../results/metrics/metrics.json).

### Independent confirmation run

The run above was produced by `src/train.py`. To check that the *notebook* reproduces it
rather than merely claiming to, `02_train_and_evaluate.ipynb` was then executed
headlessly, restart-and-run-all, on the same machine:

| | first run (`src/train.py`) | second run (notebook 02) |
|---|---|---|
| Started (UTC) | 19:57:07 | 20:19:20 |
| Precision | 0.9754 | **0.9754** |
| Recall | 0.9459 | **0.9459** |
| mAP50 | 0.9475 | **0.9475** |
| mAP50-95 | 0.8794 | **0.8794** |
| Training time | 499 s | 489 s |

**All four metrics reproduced exactly, to four decimal places**, and every generated curve
(`results.png`, both confusion matrices, the P/R/F1/PR curves) was byte-identical between
the two runs. Only the wall-clock time and the recorded timestamp differ.

That is `seed=42` with `deterministic=True` doing its job on a fixed device, and it is the
difference between a reproducibility claim and a reproducibility *result*. Note the caveat
in "Known reproducibility limits" below: this holds on the same hardware. Across different
GPUs or CUDA builds, expect ±0.01–0.02 mAP even with the seed fixed.

## Expected runtime range

| Configuration | Dataset | 30 epochs | Notes |
|---|---|---|---|
| Colab **T4 GPU** | synthetic (120 img) | **2–4 min** | the normal path |
| Colab **T4 GPU** | Roboflow, ~500 img | **12–25 min** | scales roughly linearly with image count |
| Colab **CPU** | synthetic (120 img) | **8–12 min** | measured above at 8 min 19 s |
| Colab **CPU** | Roboflow, ~500 img | **45–90 min** | tolerable but unpleasant; prefer the verification run |
| `imgsz=1280` | any | **≈ 4×** the above | Session 3: doubling resolution quadruples training time |

Notebook `01` is ~2 min anywhere. Notebook `03` is ~1–3 min: it loads weights, it does not
train.

## About this being a CPU run

The brief allows a short verification run where GPU is unavailable, documented clearly.
This run went further than the allowance: **it is the full 30-epoch contract, not a
shortened one** — the same `epochs`, `batch`, `imgsz` and `seed` the README quotes. The
only concession to having no GPU was the dataset: 120 procedural images rather than a
larger photographic set.

So what is proven and what is not:

- ✅ **Proven** — the pipeline runs end to end, unattended, from a clean checkout on a
  machine with no GPU, no Roboflow account and no API key. Every number in
  `results/metrics/` and every image in `results/evidence/` was produced by that run.
- ❌ **Not proven** — real-world façade detection performance. mAP50-95 0.879 on
  procedurally generated elevations is a statement about the *pipeline*, not the *problem*.
  Synthetic façades are axis-aligned, synthetically lit and free of the perspective,
  weather, material variation and clutter of a photograph. Expect materially lower numbers
  on real data; that is the domain gap, not a regression.

Every artefact from this run carries a `VERIFICATION RUN` banner. When you re-run against
a real Roboflow dataset the banner disappears automatically —
`src/train.py` keys it off `DATASET_SOURCE`, so it cannot be left on by accident or
removed by hand.

## Reproducibility checklist

- [x] **Dataset version / link** — `src/config.py` → `ROBOFLOW_WORKSPACE`,
      `ROBOFLOW_PROJECT`, `ROBOFLOW_VERSION`; public link in `DATASET_PUBLIC_URL`. The
      synthetic fallback is deterministic from `seed=42`.
- [x] **Split** — 80 / 20 train / validation, split in Roboflow (recorded against the
      dataset version, therefore reproducible), verified at run time by
      `dataset.describe()` and printed in the notebook.
- [x] **Model variant** — `yolov8n.pt`, transfer learning from COCO.
- [x] **Epochs / batch / imgsz** — 30 / 16 / 640, declared in `src/config.py:TrainConfig`
      and read from there by the notebook. There is no second place to change them.
- [x] **Seed** — 42, with `deterministic=True`.
- [x] **Confidence / IoU at inference** — 0.35 / 0.50, from the same config.
- [x] **ultralytics version** — pinned `==8.4.157` in `requirements.txt`; recorded in
      every metrics file by `config.summary()`.
- [x] **Environment snapshot** — `pip freeze` cell in notebook 02; `config.summary()`
      prints ultralytics, torch, Python, OS and device in one block.
- [x] **Weights provenance** — `best.pt` (never `last.pt`), copied into
      `results/weights/` by `src/train.py`, published as a GitHub Release asset and
      linked from `WEIGHTS_URL`.
- [x] **No absolute paths** — every path resolves from `config.REPO_ROOT`. Roboflow's
      `data.yaml` is rewritten by `dataset._rewrite_yaml_paths()` because its emitted
      paths break on any machine but the one that downloaded it.
- [x] **No secrets in the repo** — the Roboflow key is read from an environment variable
      or a Colab secret; `.gitignore` excludes `.env`, `*.key` and `secrets.*`.
- [x] **Class contract enforced** — `dataset._verify_class_contract()` aborts training if
      the downloaded class order disagrees with `config.CLASSES`, because class ids are
      positional and a silent reorder still produces plausible metrics.
- [x] **Results regenerate, never hand-edited** — `results/metrics/*.md` is written by
      `src/train.py`. Nothing in this repository claims a number that was typed.

## How to verify this yourself

1. Open `02_train_and_evaluate.ipynb` in Colab from the README badge.
2. **Runtime → Restart session and run all.** Change nothing.
3. Expect: a dataset health report, a labelled sample grid, a training log, a metrics
   table, three curve images, and `best.pt` on disk.
4. Open `03_inference_and_evidence.ipynb`, run all. Expect the evidence pack and the error
   tally.

If step 2 fails on a clean runtime, that is a bug in this repository, not in your setup —
open an issue with the output of `config.summary()`.

## Known reproducibility limits

- **Exact metric reproduction is not guaranteed** across different GPUs, CUDA versions or
  cuDNN builds, even with a fixed seed. Expect ±0.01–0.02 mAP. `deterministic=True`
  narrows this at a small speed cost; it does not eliminate it.
- **Ultralytics auto-selects the optimiser** (`optimizer="auto"`), which resolved to
  AdamW at lr ≈ 0.00111 for this run. A different dataset size changes that choice. It is
  recorded in the training log and in `results/curves/results.csv`.
- **Roboflow dataset versions are immutable, projects are not.** Always cite a version
  number. A bare project link will silently point at different data next month.
- **The validation set does double duty** as early-stopping signal and reported metric, so
  the figures are mildly optimistic. See [`data/README.md`](../data/README.md); the
  new-image pack in `results/evidence/new_images/` is the mitigation.
