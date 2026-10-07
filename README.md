# rigor-tutor

**严谨答疑技能**（问答型教学）。与引导型 `the-tutor` 互补：

| | the-tutor（引导型） | rigor-tutor（问答型） |
|---|---|---|
| 谁先开口 | 引导者提问，学习者**自己构建** | 学习者**主动问**，直接给答案 |
| 终点信号 | 每节点「无提示复现」闭环 | 每个数字有出处、每条表述有锚点、每条支线能弹栈回来 |
| 适用 | "从零讲起 / 引导我推导" | "帮我严谨解答 / 给我算一下 / 这个概念到底什么意思" |

## 三条铁律（严谨不是承诺，是机制）

1. **能算就算、能查就查**：符号用 SymPy、数值用 NumPy/SciPy，**每个数字带出处**，杜绝幻觉；逻辑走「锚点三档 + 高危未核实主张清单」。
2. **分层讲解契约**：严谨表述与直觉类比显式分开，类比必须能**回译**；用可实操场景降门槛但不变形。
3. **支线栈**：术语卡壳开递归支线（显式栈 + 弹栈重锚），栈落盘，理解后能递归回去。

重要问答落 Obsidian Markdown，**公式写前用 KaTeX 渲染校验**，保证能正确渲染。

## 环境要求

- Python ≥ 3.9
- Node ≥ 18（含 npm）

## 安装

```bash
git clone https://github.com/huanglianqi/rigor-tutor.git
cd rigor-tutor

# 1) 让 DSH 发现技能（二选一）
#    用户级：任何工作区可用
ln -s "$(pwd)/.agents/skills/rigor-tutor" ~/.agents/skills/rigor-tutor
#    项目级：某个工作区可用
#   ln -s "$(pwd)/.agents/skills/rigor-tutor" "<学习库>/.agents/skills/rigor-tutor"

# 2) 初始化工具链（建 venv + 装 sympy/numpy/scipy/matplotlib + npm 装 katex + 自检）
python3 .agents/skills/rigor-tutor/scripts/bootstrap.py
```

`bootstrap.py` 幂等，可重复跑；`--self-test` 只自检不重装。换设备就重跑一遍。

## 使用

在 DSH 里说：

- "帮我严谨解答：为什么期权定价要用风险中性测度？"
- "给我算一下这个积分 / 这个期望 / 这个概率"
- "这个概念到底什么意思？（它会自动开支线，讲完带你回去）"

重要部分说"记下来"即可落进 Obsidian 学习库（库位置每次会话由你指定/探测，不写死）。

## 校验

```bash
python3 tools/check_rigor_tutor.py              # 技能包结构断言
python3 tools/check_rigor_tutor.py --self-test  # 结构校验器自检
python3 .agents/skills/rigor-tutor/scripts/bootstrap.py --self-test  # 工具链自检
```

## 目录

```
.agents/skills/rigor-tutor/   技能本体（整份复制即可带走）
  SKILL.md                    入口：原则 + 流程 + references/scripts 索引
  references/                 4 份契约（严谨 / 计算核验 / 支线栈 / 落盘）
  scripts/                    bootstrap.py + latex_check.js（仅这两个）
tools/                        开发库专用：结构校验器（不随技能复制）
```

## License

[MIT](LICENSE)
