#!/usr/bin/env python3
"""rigor-tutor 技能包结构校验（开发库专用，不属于技能本体）。

补的洞：手工检查抓不到的损坏——同一规则多处副本漂移、跨文件引用指空、版本两处不一致、
脚本清单被破坏。

断言清单
────────
  FM-*          frontmatter 可解析、name/description 齐备、旧式驼峰键会让整技能被静默丢弃
  DESC-LEN      description ≤ 500 字符（模型目录上限，超了末尾触发词先被砍）
  VERSION       metadata.version 与正文版本行一致
  REF-MISSING   SKILL.md 提到的 references/x.md 必须真实存在
  REF-ORPHAN    references/ 下每个文件都必须在 SKILL.md 里被提到
  HEADING-DUP   同一文件不得有重复小节编号
  CITE-MISSING  跨文件 `references/x.md §N` 引用必须指向真实存在的小节
  SCRIPT-*      scripts/ 只允许核心脚本（bootstrap.py、latex_check.js），且两者都在

退出码：0=通过；1=有 FAIL；2=跑不起来（环境问题≠规范问题）。
"""

from __future__ import annotations

import re
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_SKILL = REPO_ROOT / ".agents" / "skills" / "rigor-tutor"

CATALOG_DESCRIPTION_MAX = 500
LEGACY_INVOCATION_KEYS = ("disableModelInvocation", "modelInvocable", "userInvocable")
REF_RE = re.compile(r"(references/[\w\-.]+\.md|SKILL\.md)")
HEADING_RE = re.compile(r"^#{1,6}\s+(\d+(?:\.\d+)*)\s*[.、]?\s*(.*)$", re.M)
BODY_VERSION_RE = re.compile(r"技能版本[^\n]*?(\d+\.\d+\.\d+(?:-dev\.\d+)?)")
SEMVER_RE = re.compile(r"^\d+\.\d+\.\d+(?:-dev\.\d+)?$")
ADJ_SEC_RE = re.compile(r"references/([\w\-.]+)\.md`?\s*§\s*(\d+(?:\.\d+)*)")

ALLOWED_SCRIPTS = {"bootstrap.py", "latex_check.js"}


class Finding:
    __slots__ = ("level", "code", "where", "message")

    def __init__(self, level, code, where, message):
        self.level, self.code, self.where, self.message = level, code, where, message

    def __str__(self):
        return f"[{self.level}] {self.code}  {self.where}\n        {self.message}"


def split_frontmatter(text):
    problems = []
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}, text, ["首行不是 `---`：没有 frontmatter"]
    close = None
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            close = i
            break
    if close is None:
        return {}, text, ["frontmatter 未闭合"]
    data, current = {}, None
    for raw in lines[1:close]:
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        if ":" not in raw:
            problems.append(f"无法解析的行：{raw.strip()[:60]}")
            continue
        indent = len(raw) - len(raw.lstrip(" "))
        key, _, value = raw.strip().partition(":")
        key, value = key.strip(), value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]
        if indent == 0:
            if value == "":
                current, data[key] = key, {}
            else:
                current, data[key] = None, value
        elif current is not None:
            data[current][key] = value
    return data, "\n".join(lines[close + 1:]), problems


def headings(text):
    return [(m.group(1), m.group(2).strip(), text[: m.start()].count("\n") + 1)
            for m in HEADING_RE.finditer(text)]


def check_frontmatter(text):
    data, body, problems = split_frontmatter(text)
    findings = [Finding("FAIL", "FM-PARSE", "SKILL.md", p) for p in problems]
    for key in LEGACY_INVOCATION_KEYS:
        if key in data:
            findings.append(Finding("FAIL", "FM-LEGACY", f"SKILL.md（{key}）",
                "旧式驼峰键会让加载器丢掉整份技能；改用 disable-model-invocation / user-invocable"))
    if not isinstance(data.get("name"), str):
        findings.append(Finding("FAIL", "FM-PARSE", "SKILL.md", "缺少 name"))
    desc = data.get("description")
    if not isinstance(desc, str) or not desc.strip():
        findings.append(Finding("FAIL", "FM-PARSE", "SKILL.md", "缺少 description"))
    elif len(desc) > CATALOG_DESCRIPTION_MAX:
        findings.append(Finding("FAIL", "DESC-LEN", "SKILL.md（description）",
            f"{len(desc)} 字符 > {CATALOG_DESCRIPTION_MAX}；超出的会被截断，触发词通常写在末尾"))
    if str(data.get("disable-model-invocation", "")).lower() == "true" \
            and str(data.get("user-invocable", "")).lower() == "false":
        findings.append(Finding("FAIL", "FM-UNREACHABLE", "SKILL.md", "模型调不动、用户也点不了"))
    return data, body, findings


def check_version(data, body):
    findings = []
    meta = data.get("metadata") if isinstance(data.get("metadata"), dict) else {}
    version = meta.get("version")
    if not isinstance(version, str) or not version:
        findings.append(Finding("FAIL", "VERSION", "SKILL.md（metadata.version）", "缺少版本号"))
        return findings
    if not SEMVER_RE.match(version):
        findings.append(Finding("FAIL", "VERSION", "SKILL.md", f"`{version}` 不是 X.Y.Z 或 X.Y.Z-dev.N"))
    m = BODY_VERSION_RE.search(body)
    if m is None:
        findings.append(Finding("FAIL", "VERSION", "SKILL.md（正文）",
            "frontmatter 不随正文加载，正文要有一行 `> **技能版本 `X.Y.Z`**`"))
    elif m.group(1) != version:
        findings.append(Finding("FAIL", "VERSION", "SKILL.md", f"正文 {m.group(1)} ≠ frontmatter {version}"))
    return findings


def check_references(skill, skill_text):
    findings = []
    ref_dir = skill / "references"
    actual = {p.name for p in ref_dir.glob("*.md")} if ref_dir.is_dir() else set()
    mentioned = {Path(m).name for m in REF_RE.findall(skill_text) if m.startswith("references/")}
    for name in sorted(mentioned - actual):
        findings.append(Finding("FAIL", "REF-MISSING", "SKILL.md", f"提到 references/{name} 但不存在"))
    for name in sorted(actual - mentioned):
        findings.append(Finding("FAIL", "REF-ORPHAN", f"references/{name}", "文件存在但 SKILL.md 没提到"))
    return findings


def check_headings(files):
    findings = []
    for name, text in files.items():
        seen = {}
        for num, _title, line in headings(text):
            if num in seen:
                findings.append(Finding("FAIL", "HEADING-DUP", f"{name}:{line}",
                    f"小节 §{num} 重复（上次在第 {seen[num]} 行）"))
            else:
                seen[num] = line
    return findings


def check_citations(files):
    heads = {name: {num for num, _t, _l in headings(text)} for name, text in files.items()}
    findings = []
    for name, text in files.items():
        for m in ADJ_SEC_RE.finditer(text):
            target, sec = m.group(1), m.group(2)
            if target != name and sec not in heads.get(f"{target}.md", set()):
                findings.append(Finding("FAIL", "CITE-MISSING", f"{name}",
                    f"引用 references/{target}.md §{sec}，但该小节不存在"))
    return findings


def check_scripts(skill):
    findings = []
    scripts = skill / "scripts"
    if not scripts.is_dir():
        findings.append(Finding("FAIL", "SCRIPT-DIR", "scripts/", "scripts/ 目录缺失"))
        return findings
    files = {p.name for p in scripts.iterdir() if p.is_file() and p.name != ".gitkeep"}
    for name in sorted(files - ALLOWED_SCRIPTS):
        findings.append(Finding("FAIL", "SCRIPT-ALLOWLIST", f"scripts/{name}",
            f"未在允许清单 {sorted(ALLOWED_SCRIPTS)} 中；加脚本先过三问（见 AGENTS.md）"))
    for name in sorted(ALLOWED_SCRIPTS - files):
        findings.append(Finding("FAIL", "SCRIPT-MISSING", "scripts/", f"核心脚本 {name} 缺失"))
    return findings


def check_skill(skill):
    findings = []
    skill_md = skill / "SKILL.md"
    if not skill_md.is_file():
        raise FileNotFoundError(f"找不到 {skill_md}")
    text = skill_md.read_text(encoding="utf-8")
    data, body, f = check_frontmatter(text)
    findings += f
    findings += check_version(data, body)
    findings += check_references(skill, text)
    files = {"SKILL.md": text}
    ref_dir = skill / "references"
    if ref_dir.is_dir():
        for p in sorted(ref_dir.glob("*.md")):
            files[p.name] = p.read_text(encoding="utf-8")
    findings += check_headings(files)
    findings += check_citations(files)
    findings += check_scripts(skill)
    return findings


def report(skill, findings):
    fails = [f for f in findings if f.level == "FAIL"]
    print(f"[技能包] {skill}")
    if not findings:
        print("  [OK] 全部断言通过")
    else:
        for f in findings:
            print(f"  {f}")
        print(f"\n  共 {len(fails)} 个 FAIL")
    return 1 if fails else 0


GOOD_SKILL = """---
name: demo
description: 演示技能。
disable-model-invocation: false
user-invocable: true
metadata:
  version: 1.0.0
---
# 演示

> **技能版本 `1.0.0`**。

## 1. 一节

细则见 `references/detail.md` §1。

## 5. references

- `references/detail.md`：细则。
"""
GOOD_REF = "# 细则\n\n## 1. 一节\n\n内容。\n"


def build_fixture(root):
    skill = root / "demo"
    (skill / "references").mkdir(parents=True)
    (skill / "scripts").mkdir(parents=True)
    (skill / "SKILL.md").write_text(GOOD_SKILL, encoding="utf-8")
    (skill / "references" / "detail.md").write_text(GOOD_REF, encoding="utf-8")
    (skill / "scripts" / "bootstrap.py").write_text("# placeholder\n", encoding="utf-8")
    (skill / "scripts" / "latex_check.js").write_text("// placeholder\n", encoding="utf-8")
    return skill


def self_test():
    cases = {
        "干净技能包": ({}, set()),
        "旧式驼峰键": ({"skill_md": GOOD_SKILL.replace("disable-model-invocation: false", "modelInvocable: true")}, {"FM-LEGACY"}),
        "版本不一致": ({"skill_md": GOOD_SKILL.replace("version: 1.0.0", "version: 1.2.3")}, {"VERSION"}),
        "缺正文版本行": ({"skill_md": GOOD_SKILL.replace("> **技能版本 `1.0.0`**。\n", "")}, {"VERSION"}),
        "提到不存在的 reference": ({"skill_md": GOOD_SKILL + "\n- `references/ghost.md`：不存在。\n"}, {"REF-MISSING"}),
        "孤儿 reference": ({"orphan": True}, {"REF-ORPHAN"}),
        "description 超限": ({"skill_md": GOOD_SKILL.replace("description: 演示技能。", "description: " + "长。" * 300)}, {"DESC-LEN"}),
        "小节编号重复": ({"detail": GOOD_REF + "\n## 1. 又一个一节\n\n内容。\n"}, {"HEADING-DUP"}),
        "跨文件引用指向不存在的小节": ({"skill_md": GOOD_SKILL.replace("§1。", "§9。")}, {"CITE-MISSING"}),
        "非法脚本名": ({"extra_script": True}, {"SCRIPT-ALLOWLIST"}),
        "缺核心脚本": ({"drop_script": True}, {"SCRIPT-MISSING"}),
    }
    failures = []
    for name, (patches, expected) in cases.items():
        with tempfile.TemporaryDirectory() as tmp:
            skill = build_fixture(Path(tmp))
            if "skill_md" in patches:
                (skill / "SKILL.md").write_text(patches["skill_md"], encoding="utf-8")
            if "detail" in patches:
                (skill / "references" / "detail.md").write_text(patches["detail"], encoding="utf-8")
            if patches.get("orphan"):
                (skill / "references" / "orphan.md").write_text("# 没人提到我\n", encoding="utf-8")
            if patches.get("extra_script"):
                (skill / "scripts" / "context_pressure.py").write_text("# stray\n", encoding="utf-8")
            if patches.get("drop_script"):
                (skill / "scripts" / "latex_check.js").unlink()
            got = {f.code for f in check_skill(skill)}
            ok = expected <= got
            print(f"{'PASS' if ok else 'FAIL'}  {name}" + ("" if ok else f"   期望⊇{sorted(expected)} 实得{sorted(got)}"))
            if not ok:
                failures.append(name)
    print(f"\n{'[OK] 自检全部通过' if not failures else '[X] 自检失败：' + '、'.join(failures)}（{len(cases)} 个用例）")
    return 1 if failures else 0


def run(argv=None):
    import argparse
    ap = argparse.ArgumentParser(description="rigor-tutor 技能包结构校验")
    ap.add_argument("--skill", type=Path, default=DEFAULT_SKILL)
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args(argv)
    if args.self_test:
        return self_test()
    try:
        return report(args.skill, check_skill(args.skill))
    except Exception:
        import traceback
        traceback.print_exc()
        print("\n[X] 校验无法完成 —— 退出码 2，不是「规范有问题」。", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(run())
