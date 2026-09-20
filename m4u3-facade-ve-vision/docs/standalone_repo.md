# Lifting this into a standalone repository

The M4U3 deliverable is **self-contained**: it has its own `README.md`, `LICENSE`,
`NOTICE`, `requirements.txt`, `.gitignore`, notebooks, source, docs and results. Nothing in
it reaches outside this folder, and every path resolves from `src/config.py:REPO_ROOT`.

It currently lives as a subfolder of the Group 02 repository. If you want the submitted
link to contain nothing but this assignment, lift it out — the contents do not change.

## The three commands

Create an empty repository on GitHub first (**Public**, no README, no .gitignore, no
licence — this folder already has all three), then:

```bash
# 1. Extract the subfolder, keeping its commit history
git subtree split --prefix=m4u3-facade-ve-vision -b m4u3-standalone

# 2. Push that branch as the new repository's main
git push https://github.com/<YOU>/m4u3-facade-ve-vision.git m4u3-standalone:main

# 3. Clean up the temporary branch
git branch -D m4u3-standalone
```

`git subtree split` rewrites the subfolder's commits as if it had always been the
repository root, so the new repo keeps the history rather than arriving as one
"initial commit". A plain `cp -r` would lose that.

## The one thing you must change afterwards

Two places name the repository. Re-point both:

```bash
# from inside the new standalone repo
grep -rl 'ZIGURAT-AI-AECO-Masters_Group-2' . --include=*.md --include=*.ipynb |
  xargs sed -i 's#OmarEAbdelaal/ZIGURAT-AI-AECO-Masters_Group-2#<YOU>/m4u3-facade-ve-vision#g'

# the project is now at the repo root, so the notebooks must stop looking in a subfolder
grep -rl 'SUBDIR   = ' notebooks/*.ipynb |
  xargs sed -i 's#SUBDIR   = \\"m4u3-facade-ve-vision\\"#SUBDIR   = \\"\\"#'
```

Then open one notebook from the README badge and confirm it clones and runs. That check
takes two minutes and it is the whole point of the exercise — a badge that 404s is the
most visible possible failure of the Session 4 acceptance test.

## Checklist before you submit the link

- [ ] Repository is **Public**, not Private.
- [ ] All three Colab badges open and run.
- [ ] `best.pt` published as a **GitHub Release** asset, and its direct URL pasted into
      `WEIGHTS_URL` in `src/config.py`.
- [ ] Roboflow dataset version is linked and publicly accessible.
- [ ] `DATASET_SOURCE` set to `roboflow` for the real run, so the `VERIFICATION RUN`
      banners clear themselves.
- [ ] `results/` regenerated from that real run — the metrics and the error analysis are
      written by code, so this is one "Run all", not an editing job.
