#!/usr/bin/env node
"use strict";
// rigor-tutor LaTeX 渲染校验器。
// 用法：node latex_check.js <笔记.md>   —— 校验该文件里每个 $...$ / $$...$$ 能否被 KaTeX 渲染
//       node latex_check.js --self-test —— 自检（好公式应过、坏公式应被拒）
// 退出码：0 = 全部渲染通过；1 = 有失败 / 未安装 KaTeX。
// 依赖：katex 装在 <repo>/.tooling/node_modules（由 bootstrap.py 安装）。

const fs = require("fs");
const path = require("path");

function findRepoRoot() {
  let dir = __dirname;
  for (let i = 0; i < 10; i++) {
    if (fs.existsSync(path.join(dir, ".agents", "skills", "rigor-tutor"))) return dir;
    const up = path.dirname(dir);
    if (up === dir) break;
    dir = up;
  }
  return null;
}

function loadKatex() {
  const repo = findRepoRoot();
  if (!repo) return null;
  const base = path.join(repo, ".tooling", "node_modules", "katex");
  for (const c of [base, path.join(base, "katex.js"), path.join(base, "dist", "katex.js")]) {
    try { return require(c); } catch (e) { /* try next */ }
  }
  return null;
}

function render(katex, tex, display) {
  try {
    katex.renderToString(tex, { throwOnError: true, displayMode: display });
    return null;
  } catch (e) {
    return e.message || String(e);
  }
}

function extractMath(md) {
  const blocks = [];
  const errors = [];
  const lines = md.split(/\r?\n/);
  let inFence = false;
  lines.forEach((line, idx) => {
    const lineNo = idx + 1;
    if (/^\s*(```|~~~)/.test(line)) { inFence = !inFence; return; }
    if (inFence) return;

    const withoutBlock = line.replace(/\$\$([\s\S]*?)\$\$/g, (all, tex) => {
      blocks.push({ tex: tex.trim(), display: true, line: lineNo });
      return "";
    });

    const inlineRe = /(?<!\\)\$([^$\n]+?)(?<!\\)\$/g;
    let m;
    while ((m = inlineRe.exec(withoutBlock)) !== null) {
      blocks.push({ tex: m[1].trim(), display: false, line: lineNo });
    }

    let dollars = 0;
    for (let i = 0; i < line.length; i++) {
      if (line[i] === "$" && (i === 0 || line[i - 1] !== "\\")) dollars++;
    }
    if (dollars % 2 === 1) errors.push(`line ${lineNo}: 未配对的 $（奇数个未转义 $）`);
  });
  return { blocks, errors };
}

function selfTest() {
  const katex = loadKatex();
  if (!katex) { console.error("未安装 KaTeX：先跑 `python3 scripts/bootstrap.py`"); return 1; }
  const good = ["x^2", "\\frac{1}{3}", "\\int_0^1 x^2\\,dx = \\frac{1}{3}",
    "\\sum_{i=1}^{n} i = \\frac{n(n+1)}{2}", "\\mathbb{E}[X] = \\mu", "\\sigma\\sqrt{n}"];
  const bad = ["\\frac{1}", "\\sqrt"];
  let fails = 0;
  for (const t of good) {
    const e = render(katex, t, false);
    if (e) { fails++; console.error(`[FAIL] 好公式未通过: ${t}\n       ${e.split("\n")[0]}`); }
    else console.log(`[OK]   ${t}`);
  }
  for (const t of bad) {
    const e = render(katex, t, false);
    if (!e) { fails++; console.error(`[FAIL] 坏公式居然通过: ${t}`); }
    else console.log(`[OK]   正确拒绝: ${t} -> ${e.split("\n")[0]}`);
  }
  console.log(fails === 0 ? "\n[OK] KaTeX 自检通过" : `\n[X] ${fails} 处失败`);
  return fails === 0 ? 0 : 1;
}

function main() {
  const args = process.argv.slice(2);
  if (args[0] === "--self-test") return selfTest();
  const file = args[0];
  if (!file) { console.error("用法: node latex_check.js <笔记.md>  或  node latex_check.js --self-test"); return 1; }
  if (!fs.existsSync(file)) { console.error(`找不到文件: ${file}`); return 1; }
  const katex = loadKatex();
  if (!katex) { console.error("未安装 KaTeX：先跑 `python3 scripts/bootstrap.py`"); return 1; }
  const { blocks, errors } = extractMath(fs.readFileSync(file, "utf8"));
  let fails = 0;
  for (const e of errors) { fails++; console.error("[不平衡] " + e); }
  for (const b of blocks) {
    const err = render(katex, b.tex, b.display);
    if (err) { fails++; console.error(`[FAIL] line ${b.line} ${b.display ? "display" : "inline"}: ${b.tex}\n       ${err.split("\n")[0]}`); }
    else console.log(`[OK]   line ${b.line} ${b.display ? "display" : "inline"}: ${b.tex.slice(0, 60)}`);
  }
  if (blocks.length === 0 && errors.length === 0) console.log("[OK] 未发现数学公式");
  console.log(fails === 0 ? "\n[OK] LaTeX 校验通过" : `\n[X] ${fails} 处失败`);
  return fails === 0 ? 0 : 1;
}

process.exit(main());
