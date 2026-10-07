# 本工作区给 DSH 的指令

这个目录是**问答型严谨答疑技能 `rigor-tutor` 的开发库**——不是知识库、不是 Obsidian 仓库、不是代码仓库（只是带 git 历史的技能开发目录）。

## 这里有什么

```
~/Projects/rigor-tutor/                      ← 本仓库：技能开发库（git 在这）
  AGENTS.md                                 本文件（不随技能复制）
  NOTES.md                                  开发笔记 / 变更记录（不随技能复制）
  DESIGN.md                                 架构设计稿（不随技能复制）
  README.md                                 面向 GitHub 使用者（不随技能复制）
  LICENSE                                   MIT（整库适用）
  .agents/skills/rigor-tutor/               技能本体（整份复制即可带走）
    SKILL.md                                严谨答疑教学法全文（唯一规范源）
    references/rigor-contract.md            严谨性契约【唯一权威】
    references/computation-contract.md      计算核验契约【唯一权威】
    references/branch-stack.md              支线栈契约【唯一权威】
    references/vault-spec.md                落盘契约【唯一权威】
    scripts/bootstrap.py                    工具链初始化 + 自检
    scripts/latex_check.js                  LaTeX 渲染校验
  tools/check_rigor_tutor.py                结构校验 + 自检（不随技能复制）
```

## 三条硬规矩（从 the-tutor 的教训里立下的，别破）

1. **单一事实源。** 任何规则、判定表、模板，**只允许有一份权威落点，别处只放指针**。
   严谨性 = `rigor-contract.md`；计算核验 = `computation-contract.md`；支线栈 = `branch-stack.md`；
   落盘 = `vault-spec.md`。别的文件引用它们的名字，**不得重述定义**。
2. **版本可观测。** frontmatter 会被加载器剥掉，模型问不到 `metadata.version`。所以正文顶部
   必须有一行 `> **技能版本 X.Y.Z**`，由 `check_rigor_tutor.py` 断言它与 `metadata.version` 一致。
3. **技能本体内不出现只在本机成立的路径/解释器别名/会漂移的数字快照。** 判定标准一句话：
   **别的项目的读者看到它，会不会被误导去做错一件事？** 那类内容写进本文件或 NOTES.md。
   特别注意：**vault 绝对路径永不写进技能本体或记录文件**（跨设备必错，见 `vault-spec.md` §2）。

## 改完必跑

```bash
python3 tools/check_rigor_tutor.py              # 结构断言（FM/VERSION/REF/HEADING/CITE/SCRIPT）
python3 tools/check_rigor_tutor.py --self-test  # 改动本脚本后必跑（11 个当场造夹具的用例）
python3 .agents/skills/rigor-tutor/scripts/bootstrap.py --self-test  # 改动 bootstrap/latex_check 后必跑
python3 .agents/skills/rigor-tutor/scripts/latex_check.js --self-test # 改动 latex_check.js 后必跑
```

版本号约定：语义化 `X.Y.Z`。严重度按"旧东西是否还能通过"判：
- **MAJOR**：改变既有行为契约（删必填动作、改输出格式）；
- **MINOR**：新增能力不破坏旧行为（新增一节、一份 reference、一个字段）；
- **PATCH**：措辞、举例、澄清。

## frontmatter 的调用策略（这里写错过会整份技能消失）

- DSH 加载器只认两个规范键：`disable-model-invocation`（true 则模型调不动）、`user-invocable`（false 则用户点不了）。
- ⚠️ **旧式驼峰键 `disableModelInvocation` / `modelInvocable` / `userInvocable` 会让整份技能被静默丢弃**，不是忽略那个键。改完 frontmatter 务必确认技能还在。
- `description` 进模型目录（≤500 字符，超了末尾触发词先被砍）；`whenToUse` 进界面目录，不参与模型侧触发。
- 本技能 `disable-model-invocation: false`（模型可主动调用）。
- **触发边界**（别和 the-tutor 打架）：本技能吃"帮我严谨解答 / 给我算一下 / 这个公式为什么对 / 这个概念到底什么意思"；the-tutor 吃"教我学 / 从零讲起 / 引导我推导"。改 description 时守住这条。

## scripts 允许清单（别破）

`scripts/` **只允许** `bootstrap.py` + `latex_check.js` 两个（由 `check_rigor_tutor.py` 的 SCRIPT-ALLOWLIST 机械把关）。想加脚本先过三问：

1. 这个判断能不能由模型直接读文件/跑命令完成？
2. 它是否依赖本机路径/解释器别名？
3. 是否已有机械校验能替代？

三问都过不了"不加"，才准加，并同步改 `check_rigor_tutor.py` 的 `ALLOWED_SCRIPTS`。

## 通道：Obsidian MCP 首选

rigor-tutor 读写学习库时，**首选 Obsidian MCP**（etag 版本守卫、backlink 自动一致、破坏性操作可恢复），
无 MCP 时退文件 I/O 并明说无并发守卫。细则在 `vault-spec.md` §1，**不要在正文别处重述**。

## 与 the-tutor 的命名空间隔离

同库共存时，the-tutor 写 `<主题>/学习地图.md`，rigor-tutor 写 `问答/<主题>/`，**互不踩文件**；
可以 wikilink 互指。细则见 `vault-spec.md` §3。

## 怎么安装 / 使用

- **迭代技能**：cwd = `~/Projects/rigor-tutor`，`.agents/skills/rigor-tutor/` 自动被发现。
- **在别的库 / 设备用**：见 `README.md`——clone + symlink + `bootstrap.py`。目录软链 DSH 加载器支持（`isSymbolicLink()` 后 `stat` 跟随）。

## 提交纪律

- 提交只暂存本次改动：`git add <具体路径>`，不要 `git add -A`。
- 本机路径、数字快照、设备专属配置只写 NOTES.md，不写技能本体。
- `.tooling/`、`node_modules/`、`__pycache__/` 已被 `.gitignore` 排除，**不要 force-add 进去**。
