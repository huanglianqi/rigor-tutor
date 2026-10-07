#!/usr/bin/env python3
"""rigor-tutor 工具链初始化 + 自检。

职责（幂等，可重复跑）：
  1. 在仓库根建 `.tooling/venv`（若不存在）并装 sympy/numpy/scipy/matplotlib；
  2. 用 npm 把 katex 装进 `.tooling/node_modules`（LaTeX 渲染校验用）；
  3. 自检：venv 里真的能算（sympy 积分 / numpy / scipy），katex 真的能渲染。

`.tooling/` 已 gitignore，**不可移植**——换设备就重跑本脚本。

退出码：0 = 全部就绪；1 = 有失败。
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

PY_DEPS = ["sympy", "numpy", "scipy", "matplotlib"]

# 自检用的 Python 片段：三个库各验一次真实计算
PY_SELF = (
    "import sympy, numpy, scipy.stats as st; "
    "x = sympy.symbols('x'); "
    "print('sympy  integral(x**2,0..1) =', sympy.integrate(x**2, (x, 0, 1))); "
    "print('numpy  mean([1,2,3])         =', numpy.mean([1.0, 2.0, 3.0])); "
    "print('scipy  norm.cdf(0)           =', st.norm.cdf(0.0))"
)


def repo_root() -> Path:
    here = Path(__file__).resolve()
    for p in [here, *here.parents]:
        if (p / ".agents" / "skills" / "rigor-tutor" / "scripts" / "bootstrap.py").resolve() == here:
            return p
    sys.exit("找不到仓库根：本脚本应位于 <repo>/.agents/skills/rigor-tutor/scripts/bootstrap.py")


REPO = repo_root()
SKILL = REPO / ".agents" / "skills" / "rigor-tutor"
TOOLING = REPO / ".tooling"
VENV = TOOLING / "venv"
VPY = VENV / "bin" / "python"


def run(cmd, **kw):
    print("  +", " ".join(str(c) for c in cmd), flush=True)
    return subprocess.run([str(c) for c in cmd], **kw)


def ensure_venv() -> bool:
    if VPY.is_file():
        print("[venv] 已存在，跳过创建")
        return True
    print(f"[1/3] 创建虚拟环境 {VENV}")
    if run([sys.executable, "-m", "venv", str(VENV)]).returncode != 0:
        print("!! venv 创建失败")
        return False
    print(f"[2/3] 安装 Python 依赖：{' '.join(PY_DEPS)}")
    if run([str(VPY), "-m", "pip", "install", "--disable-pip-version-check", *PY_DEPS]).returncode != 0:
        print("!! pip install 失败")
        return False
    return True


def ensure_katex() -> bool:
    if (TOOLING / "node_modules" / "katex").is_dir():
        print("[katex] 已存在，跳过安装")
        return True
    if shutil.which("node") is None or shutil.which("npm") is None:
        print("!! 未找到 node/npm，跳过 KaTeX（LaTeX 渲染校验将不可用）")
        return False
    print("[3/3] 用 npm 安装 KaTeX（缓存隔离到 .tooling/npm-cache，不触碰 ~/.npm）")
    return run(["npm", "install", "--prefix", str(TOOLING),
                "--cache", str(TOOLING / "npm-cache"), "katex"]).returncode == 0


def self_test() -> int:
    ok = True
    if VPY.is_file():
        if run([str(VPY), "-c", PY_SELF]).returncode != 0:
            ok = False
    else:
        print("!! venv 不存在，无法自检 Python 计算（先跑一次不带 --self-test 的本脚本）")
        ok = False
    if shutil.which("node"):
        if run(["node", str(SKILL / "scripts" / "latex_check.js"), "--self-test"]).returncode != 0:
            ok = False
    else:
        print("!! 未找到 node，无法自检 KaTeX")
        ok = False
    print("\n[OK] 自检通过" if ok else "\n[X] 自检未通过")
    return 0 if ok else 1


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="rigor-tutor 工具链初始化 + 自检")
    ap.add_argument("--self-test", action="store_true", help="只跑自检，不创建/安装")
    args = ap.parse_args(argv)
    if args.self_test:
        return self_test()
    a = ensure_venv()
    b = ensure_katex()
    if not (a and b):
        print("\n[X] 初始化未完全成功（见上面 !! 行）")
        return 1
    return self_test()


if __name__ == "__main__":
    sys.exit(main())
