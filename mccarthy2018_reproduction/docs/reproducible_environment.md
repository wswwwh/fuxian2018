# 可重建运行环境

## 环境文件

- `environment.yml`：跨平台环境意图，允许 conda-forge 解析兼容版本。
- `environment-lock.yml`：阶段 A 冻结时在 Windows/cislunar 环境中实测通过的核心版本快照。
- `pyproject.toml`：可安装 Python 项目的运行依赖；其中包含 DE421 路径实际使用的 `skyfield`。

锁文件记录的是核心直接依赖，不替代 conda 求解器产生的完整传递依赖清单。若精确版本在未来 channel 中不可用，应先保留失败日志，再在独立环境中验证兼容升级；不得直接修改审计阈值来迁就环境漂移。

## 本机权威解释器

```powershell
D:\miniconda3\envs\cislunar\python.exe
```

所有阶段 A/B 命令从项目根目录执行，并显式设置：

```powershell
$env:PYTHONDONTWRITEBYTECODE = '1'
$env:PYTHONPATH = 'src'
```

禁止依赖未核实的 `PATH` 解析结果。若使用 `conda run`，仍应检查最终解释器：

```powershell
conda run -n cislunar python -c "import sys; print(sys.executable)"
```

## 创建或复核环境

兼容环境：

```powershell
conda env create -f environment.yml
```

冻结版本环境：

```powershell
conda env create -f environment-lock.yml
```

直接依赖导入探针：

```powershell
$env:PYTHONDONTWRITEBYTECODE = '1'
$env:PYTHONPATH = 'src'
& 'D:\miniconda3\envs\cislunar\python.exe' -c "import fitz, matplotlib, numpy, pandas, PIL, pypdf, scipy, skyfield; import qp_orbits; print('IMPORT PASS')"
```

## 阶段 A 回归命令

```powershell
$env:PYTHONDONTWRITEBYTECODE = '1'
$env:PYTHONPATH = 'src'
& 'D:\miniconda3\envs\cislunar\python.exe' scripts\run_reproduction_baseline_freeze.py --check
& 'D:\miniconda3\envs\cislunar\python.exe' -m unittest discover -s tests -v
& 'D:\miniconda3\envs\cislunar\python.exe' scripts\build_reproduction_targets.py --check
& 'D:\miniconda3\envs\cislunar\python.exe' scripts\validate_reproduction_smoke.py
git diff --check
```

`run_reproduction_baseline_freeze.py` 只读取 canonical CSV、冻结锁和证据文件；默认模式仅重建派生的基线摘要、清单与 Markdown，`--check` 模式不写文件。
