# Local Validation Scope

Local formal edition (2026-10-19). The user has authorized this local formal edition: canonical_written=true and formal_publication=false. This promotion verifies local release identities; it does not expand historical experimental or research validation.

## Four complete PDFs

The [English body](body/main.pdf), the [English Workbook](workbook/quant-course-workbook-en.pdf), and their Chinese counterparts cover all teaching content, exercises, and answers for Chapters 1–45, Projects 1–6, and the Capstone; each project follows its prerequisite chapters. The four PDFs passed two independent acceptance reviews: a content and rendering review (checked against the sources, with key numbers of new exercise answers recomputed) and a page-by-page contact-sheet review of every book. Table of contents, bookmarks, in-book jumps, and local file links were checked with a PDF parser; no link points into a build folder. Semantic boxes frame complete worked examples, from statement through every step to the conclusion, and continued boxes carry a continuation label. Every figure in the English body has English labels; the two shared figures that had Chinese labels (Chapter 10 cash-flow timeline, Project 1 dashboard) were redrawn from the same code and data with only the label text translated. Plot labels that Notebooks generate at run time may still be Chinese, as the [Notebook guide](NOTEBOOK_GUIDE.md) notes.

## Isolated cold start (actually run)

This package was copied into an empty directory outside the course working tree and the commands in the [entry page](README.md) were run as written:

- Environment: macOS arm64, CPython 3.14.7, a new `.venv`, `pip install -r requirements-macos-arm64-py314.lock` (network used only to install from public PyPI); the installed set matches the 75 locked packages exactly. After `ipykernel install --prefix .venv`, the Notebook kernel was confirmed to run the `.venv` interpreter.
- Offline tests: `PYTHONPATH=src .venv/bin/python -m pytest tests -q` — 197 passed, including the corrected regression and inference tests for Chapters 8 and 32.
- Notebooks: `run_notebook.py` executed all 54 Chinese and all 54 English language views, each in a fresh kernel — 108 of 108 PASS. Code cells are identical across languages; every run wrote to its own `runs/execution_*` and `runs/<name>_*` directories.
- Capstone: `capstone/check_portable.py` passed (fault injection, same-task recovery, idempotent replay). Running `run_offline.py` as in the [engineering guide](capstone/ENGINEERING_BASE.md): the fault run stops as intended; recovery with the same state-db, run key, and output-dir reconciles PASS with terminal NAV 9995.998; the replay is identical; reusing the key with another output directory is refused.
- After all runs, no file outside `.venv/` and `runs/` was added or changed.

## Not run and boundaries

Market-data branches (G01 rights unknown; G05 has not authorized A10-B), Docker, historical command lines outside the run matrix, and other platforms or Python versions were not run. Constructed results check methods and implementations; they are not market evidence. Links in documents that point to historical QA and audit records inside the course working tree (`qa/` and similar) are not distributed with this package; for chapter text, the PDFs are the reader route.

[Remaining work](REMAINING_ITEMS.md) · [Entry](README.md)


## This local formal promotion

On 2026-10-19 only release-status text and entry points were updated. The four PDFs, shared code, dependencies, configurations, exercises/answers and Notebooks retain accepted B4/C3 bytes. C3 freshly checked check_portable, fault/recovery/replay/key-reuse rejection and three entry Notebooks, with zero static changes. The 197 tests and 162-Notebook full run are inherited C2 evidence bound to unchanged files; they were not rerun for this promotion. No PDFs were rebuilt.


## Contents layout correction (BIL23B5, October 19, 2026)

After the initial formal promotion described above, the four PDFs received a contents-only correction: consistent chapter separators, wrapping at word boundaries, and a separate right-aligned page-number area. Text, 72 dpi rendering and link targets on body pages were compared against B4; the current project acceptance register records the results and independent reviews. Shared code, configuration, data and Notebooks are unchanged; applicable execution evidence is inherited, with no claim of a new full run.
