# 包内文件结构

本地正式版（2026-10-19）。包根共842个文件；下表按目录统计。代码、数据、配置与运行器在包根两语共用；`editions/zh`与`editions/en`只放各语言的入口文档、读者资源、Notebook语言视图和完整PDF。项目与Capstone的中文文档在包根对应目录，英文文档在`editions/en/`下同名路径；章节教学源（中文`part0*/`、英文`editions/en/chapters/`）随包提供，读者路线以PDF为准。逐文件来源与SHA-256见批次清单。

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

[入口](README.md)
