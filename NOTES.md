# 开发笔记 / 变更记录（不属于技能本体）

> 这个文件不随技能复制。它记的是**为什么这么做**、以及踩过的坑，让后人（包括未来的我）知道哪些决定不能随便改。

## 0.1.0（2026-10-07，初始）

从零搭骨架：SKILL.md + 4 份 reference + bootstrap.py + latex_check.js + check_rigor_tutor.py（11 类断言 + 自检）。

### 设计时的关键取舍（别回退）

- **严谨性 = 过程，不是承诺。** 三条铁律（能算就算能查就查 / 分层讲解契约 / 支线栈）各自落成一份 reference，别处只引用。这是从 the-tutor 的"单一事实源"直接继承，但**加了它没有的东西**：机器计算核验 + KaTeX 渲染校验——因为答疑型比引导型更依赖"工具算的数"。
- **脚本预算与 the-tutor 相反**：the-tutor 反脚本膨胀（≤1），rigor-tutor 有真实执行需求，按需带 2 个脚本，用 SCRIPT-ALLOWLIST 锁死。判定标准一句话：**这个判断能不能由模型直接读文件/跑命令完成？能，就不加脚本。**
- **与 the-tutor 命名空间隔离**：the-tutor 写 `<主题>/学习地图.md`，rigor-tutor 写 `问答/<主题>/`，同库共存不互踩。

### 借鉴来源（想法，非照搬）

- `the-tutor`：单一事实源、版本可观测、frontmatter 规范键的坑、vault 永不写死、结构校验器骨架。
- `socratic-tutor`（通用版）：锚点三档、高危未核实主张清单、"能算就算能查就查"、退化标注的诚实纪律。

## 环境备忘

- 校验脚本 `check_rigor_tutor.py` 用极简 frontmatter 解析器，**不依赖 PyYAML**（Homebrew python3 没有它）。
- 计算/渲染依赖**不随仓库**：`.tooling/`（venv + node_modules）已 gitignore，换设备跑 `bootstrap.py` 重建。
- `latex_check.js` 靠 `findRepoRoot()` 从 `__dirname` 向上找到含 `.agents/skills/rigor-tutor` 的目录来定位 `.tooling/node_modules/katex`——**不写死任何绝对路径**。
- 本仓库 git 只在本机操作；别在别的设备上跑 git status（会刷新 .git/index 造成 churn）。
