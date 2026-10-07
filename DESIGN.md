# rigor-tutor 架构设计稿（v0.1）

> 本文件是**设计稿**，不是技能本体。它只讨论"造什么、为什么、边界在哪"，不进技能包。

## 1. 一句话定位

**rigor-tutor 是一个问答型严谨答疑技能**：学习者提问，它直接给出**严谨、可核、可追溯**的答案，
并把重要问答落进 Obsidian。与 the-tutor（引导型）互补，不替代。

## 2. 核心洞察：严谨不是承诺，是过程

LLM 的幻觉集中在两处——"凭记忆报一个数"和"凭感觉下一个结论"。所以严谨性**不能在提示词里承诺**，
只能用机制把这两处换成"跑工具 / 查出处"：

| 需求 | 机制 | 落点 |
|---|---|---|
| 逻辑严谨、杜绝幻觉 | 锚点三档 + 高危未核实主张清单 + 能算就算能查就查 | `rigor-contract.md` |
| 数值必须计算机算 | 强制 SymPy/NumPy/SciPy + 每个数字带出处 | `computation-contract.md` |
| 降门槛不失严谨 | 分层讲解契约 + 回译检验 | `rigor-contract.md` §3 |
| 递归支线 | 显式栈 + 弹栈重锚 + 落盘 | `branch-stack.md` |
| 落 Obsidian + 严格 LaTeX | 写前 KaTeX 渲染校验 + 重要部分入选标准 | `vault-spec.md` |
| 工程化 | 单一事实源 + 版本可观测 + 结构校验器 + 工具链自检 | `check_rigor_tutor.py` / `bootstrap.py` |

**和 the-tutor 最大的区别**：the-tutor 反脚本膨胀（scripts ≤1），rigor-tutor **有真实的执行需求**——
计算核验和 LaTeX 渲染校验必须真跑，所以它**按需带 2 个脚本**（bootstrap.py + latex_check.js），
并用 SCRIPT-ALLOWLIST 机械锁死，防止膨胀。

## 3. 范围：v0.1 做什么、明确不做什么

**v0.1 做**：严谨分层讲解 + 机器计算核验 + 支线栈 + Obsidian 落盘（KaTeX 校验）+ 工具链 bootstrap + 结构校验器。

**v0.1 明确不做**（每一条都写"为什么"）：

| 不做 | 为什么 |
|---|---|
| 引导式无提示复现闭环 | 那是 the-tutor 的职责，本技能是"答疑"不是"引导" |
| 状态机 / 掌握度追踪 | 答疑是事件驱动的，不维护跨主题掌握状态 |
| 费曼考核 / 独立判定者 | the-tutor 的 v2 接口，与答疑正交 |
| Lean/Coq 机器可验证证明 | 对答疑场景是杀鸡用牛刀，会主导对话 |

## 4. 文件结构（同 the-tutor 的骨架，脚本预算不同）

```
.agents/skills/rigor-tutor/
  SKILL.md                入口 ≤~250 行：原则 + 流程 + references/scripts 索引
  references/             rigor-contract / computation-contract / branch-stack / vault-spec
  scripts/                bootstrap.py + latex_check.js（仅这两个）
tools/check_rigor_tutor.py  开发库专用结构校验器（照搬 the-tutor 的断言思路，改脚本预算）
```

## 5. 待拍板的记录（v0.1 后）

- 是否需要在答疑后接一个**轻量"你能不能用一句转述"确认**（区别于 the-tutor 的完整复现闭环）；
- golden test 是否固化成 `tools/golden_test.py`（当前是手工跑一次端到端）。

## 附：反负债清单

- [x] SKILL.md ≤250 行，changelog 不进正文
- [x] 四条契约各自唯一权威，别处只引用
- [x] scripts 只允许 bootstrap.py + latex_check.js（SCRIPT-ALLOWLIST 把关）
- [x] 技能本体内零本机路径 / 零解释器别名 / 零会漂移的数字快照；vault 永不写死
- [x] description ≤500 字符，触发词不与 the-tutor 冲突
- [x] 正文有可观测版本行，与 metadata.version 由 check 脚本断言一致
