# JOSS Submission Checklist — pyoceanmap

Ordered steps from the current state to a submitted JOSS paper. Items marked
**(you)** require your accounts, personal content, or external services.

## 1. Finish paper content
- [x] Fill in the two research posters in `paper/paper.md` (Research Impact section).
- [ ] **(you)** Read `paper/paper.md` end-to-end once in your own voice — reviewers read it closely.

## 2. Commit and push the restructure
Currently everything is staged deletions + untracked new files, uncommitted.
```bash
git add -A
git commit   # message describing the JOSS packaging restructure
git push
```
- [ ] **(you)** Confirm **GitHub Actions CI goes green** — the CI badge must pass before submission.

## 3. Read the Docs
- [ ] **(you)** readthedocs.org → Import the `pyoceanmap` repo (config `.readthedocs.yaml` is ready).
- [ ] Confirm the docs build and the README docs badge goes live.

## 4. Zenodo archive + DOI (required by JOSS)
- [ ] **(you)** Enable the **Zenodo ↔ GitHub** integration for the repo (Zenodo → GitHub tab → toggle `pyoceanmap`).
- [ ] Cut the release:
  ```bash
  git tag v1.0.0
  git push --tags
  ```
  then create a **GitHub Release** from that tag — Zenodo auto-archives it and mints a DOI.
- [ ] Paste the DOI into **`CITATION.cff`** (`doi:` line) and the **README DOI badge**
      (both currently `10.5281/zenodo.XXXXXXX`), then commit.

## 5. Submit to JOSS
- [ ] Confirm requirements: OSI license (BSD-3 ✅), tests ✅, docs ✅, `paper.md` + `paper.bib` ✅.
- [ ] **(you)** Submit at **joss.theoj.org** → "Submit a paper": point at the repo, release
      version (`v1.0.0`), and the Zenodo DOI.
- [ ] Respond to reviewer issues on GitHub over the following weeks.

## Recommended before submitting
- [ ] **Southern Ocean / Argo case study** is described in the paper/README but not represented
      in `examples/` (only the Arctic demo is). Add a Southern Ocean example, or note in the docs
      how those figures are produced — JOSS values reproducibility.
- [ ] **`data/Behrendt-etal_2017.tab`** — confirm it is OK to redistribute (UDASH catalog
      reference). If unsure, remove it and link instead (same reasoning as the copyrighted PDF
      that was removed).

## Status of the 6 pre-submission must-fixes
1. Installable package (`pyproject.toml`, `pyoceanmap/` package) — **done**
2. Automated tests + GitHub Actions CI — **done** (21 tests; badge in README)
3. `paper.md` (Summary, Statement of Need, tool comparison, Research Impact) — **done**
4. Zenodo-archived tagged release with DOI — **needs step 4 above (you)**
5. API docs (docstrings + Sphinx docs page) — **done** (Read the Docs hosting = step 3)
6. AI-usage disclosure — **done** (in `paper.md` and `README.md`)
