# Package File Structure

Local formal edition (2026-10-19). The package root holds 842 files; the table counts them by directory. Code, data, configuration, and the runner at the root are shared by both languages; `editions/zh` and `editions/en` hold only each language’s entry documents, reader resources, Notebook language views, and complete PDFs. Chinese project and Capstone documents sit in the root directories; English documents use the same paths under `editions/en/`. Chapter teaching sources (Chinese `part0*/`, English `editions/en/chapters/`) are included; the PDFs are the reader route. Per-file origins and SHA-256 are in the batch manifest.

```text
  ENVIRONMENT.json                                1
  README.md                                       1
  capstone                                       15
  code                                           42
  data                                            4
  editions                                       17
  editions/en/body                                1
  editions/en/capstone                           10
  editions/en/chapters                           45
  editions/en/figures                             1
  editions/en/loom                                1
  editions/en/notebooks                          45
  editions/en/projects                           63
  editions/en/resources                           9
  editions/zh/body                                1
  editions/zh/loom                                1
  editions/zh/notebooks                          45
  editions/zh/projects                            9
  editions/zh/resources                           9
  figures                                       105
  fixtures                                       27
  notebooks                                      45
  part00                                          2
  part01                                         16
  part02                                          8
  part03                                         16
  part04                                         14
  part05                                         10
  part06                                         13
  part07                                         71
  print_examples                                  8
  projects                                        2
  projects/project01                             12
  projects/project02                             15
  projects/project03                             15
  projects/project04                             27
  projects/project05                             31
  projects/project06                             26
  pyproject.toml                                  1
  qa                                              2
  references.md                                   1
  requirements-macos-arm64-py314.lock             1
  run_notebook.py                                 1
  src                                            43
  tests                                          10
```

[Entry](README.md)
