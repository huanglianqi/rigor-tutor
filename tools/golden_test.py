#!/usr/bin/env python3
"""rigor-tutor 端到端 golden test（开发库专用，不属于技能本体）。

验证整条管线，把"严谨=过程"变成可跑的断言：
  1. 机器算出 ground truth（SymPy 定积分 / NumPy 均值）；
  2. 断言工具给出的就是已知正确答案（工具本身没配错）；
  3. 把机器输出写进一篇样例答疑笔记（含 LaTeX + 出处）；
  4. 用 latex_check.js 渲染校验——好公式必须过；
  5. 反向控制：坏公式（\\frac{1}）必须被拒（证明校验器真在抓错，不是放水）。

退出码：0=通过；1=有失败；2=环境未就绪（先跑 bootstrap.py）。
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SKILL = REPO / ".agents" / "skills" / "rigor-tutor"
VPY = REPO / ".tooling" / "venv" / "bin" / "python"
LATEX_CHECK = SKILL / "scripts" / "latex_check.js"


def sh(cmd):
    return subprocess.run([str(c) for c in cmd], capture_output=True, text=True)


def main() -> int:
    if not VPY.is_file():
        print("[X] .tooling/venv 不存在，先跑 `python3 .agents/skills/rigor-tutor/scripts/bootstrap.py`")
        return 2

    # 1) 机器算 ground truth
    code = (
        'import json, sympy, numpy\n'
        'x = sympy.symbols("x")\n'
        'integral = sympy.integrate(x**2, (x, 0, 1))\n'
        'dice_mean = numpy.mean([1, 2, 3, 4, 5, 6])\n'
        'print(json.dumps({"integral": str(integral), "dice_mean": str(dice_mean)}))\n'
    )
    r = sh([VPY, "-c", code])
    if r.returncode != 0:
        print("[X] 计算失败：", r.stderr)
        return 1
    gt = json.loads(r.stdout.strip().splitlines()[-1])

    # 2) 断言工具给出的是已知正确答案
    fails = []
    if gt["integral"] != "1/3":
        fails.append(f"SymPy 定积分应为 '1/3'，实得 {gt['integral']!r}")
    if abs(float(gt["dice_mean"]) - 3.5) > 1e-12:
        fails.append(f"NumPy 骰子均值应为 3.5，实得 {gt['dice_mean']!r}")

    # 3) 用机器输出构造样例答疑笔记
    note = rf"""---
type: rigor-qa
topic: golden-test
date: 2026-10-07
tags: [问答, 自检]
---

# golden-test 答疑（端到端自检）

## 严谨表述（锚点：无——自检样例）
$$\int_0^1 x^2\,dx = \frac{{1}}{{3}}$$

## 算例（数值带出处）
骰子单次点数期望 $E[X] = {gt['dice_mean']}$（来源：`numpy.mean([1,2,3,4,5,6])` → `{gt['dice_mean']}`）。

定积分 $\int_0^1 x^2\,dx = {gt['integral']}$（来源：SymPy `integrate(x**2,(x,0,1))` → `{gt['integral']}`）。
"""
    if gt["integral"] not in note or gt["dice_mean"] not in note:
        fails.append("机器输出未能写进笔记")

    # 4) LaTeX 渲染校验：好公式必须过
    with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False, encoding="utf-8") as f:
        f.write(note)
        good_path = f.name
    r = sh(["node", LATEX_CHECK, good_path])
    if r.returncode != 0:
        fails.append("好笔记 LaTeX 校验未通过：\n" + r.stdout + r.stderr)

    # 5) 反向控制：坏公式必须被拒
    bad = "# 坏公式\n\n这是坏公式 $\\frac{1}$ 应被拒绝。\n"
    with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False, encoding="utf-8") as f:
        f.write(bad)
        bad_path = f.name
    r = sh(["node", LATEX_CHECK, bad_path])
    if r.returncode == 0:
        fails.append("坏公式 $\\frac{1}$ 未被拒绝（校验器放水）")

    for p in (good_path, bad_path):
        Path(p).unlink(missing_ok=True)

    if fails:
        print("[X] golden test 失败：")
        for msg in fails:
            print("   -", msg)
        return 1
    print("[OK] golden test 通过：工具算对 → 值落进笔记 → LaTeX 渲染通过，且坏公式被拒")
    return 0


if __name__ == "__main__":
    sys.exit(main())
