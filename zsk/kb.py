#!/usr/bin/env python3
"""
知识库 CLI 工具。
用法: python kb.py <command> [options]

命令:
  list       列出所有知识点
  search     全文搜索
  show       查看详情
  stats      统计信息
  add        手动添加知识点
  edit       编辑知识点
  delete     删除知识点
  import     从 MD 研报导入
  export     导出 HTML 可视化
"""
from __future__ import annotations

import sys
import argparse
from pathlib import Path
from kb_core import KnowledgeBase, KnowledgeNode
from kb_ontology import ONTOLOGY, PRIORITY_LEVELS, PREDEFINED_TAGS

# 项目根目录 — 始终是 kb.py 所在目录，无论从何处调用
PROJECT_DIR = Path(__file__).resolve().parent


def cmd_list(kb: KnowledgeBase, args):
    nodes = kb.list_all()
    if args.category:
        nodes = [n for n in nodes if n.category == args.category]
    if args.tag:
        nodes = [n for n in nodes if args.tag in n.tags]
    if args.priority:
        nodes = [n for n in nodes if n.priority == args.priority]
    if args.limit:
        nodes = nodes[:args.limit]

    if not nodes:
        print("（无知识点）")
        return

    for n in nodes:
        stars = "⭐" * n.priority
        cat = f"[{ONTOLOGY.get(n.category, {}).get('label', n.category)}]" if n.category else ""
        tags = ", ".join(n.tags[:3]) if n.tags else ""
        print(f"  {stars} {n.id:14s} {cat:8s} {n.title}")
        if args.verbose:
            print(f"       {n.abstract[:100]}")
            if tags:
                print(f"       🏷 {tags}")
            print()


def cmd_search(kb: KnowledgeBase, args):
    results = kb.search(args.keyword)
    if not results:
        print(f"未找到匹配 '{args.keyword}' 的知识点")
        return
    print(f"找到 {len(results)} 个结果：\n")
    for n in results:
        stars = "⭐" * n.priority
        cat = f"[{ONTOLOGY.get(n.category, {}).get('label', n.category)}]" if n.category else ""
        print(f"  {stars} {n.id:14s} {cat:8s} {n.title}")
        if n.abstract:
            print(f"       {n.abstract[:120]}")
        print()


def cmd_show(kb: KnowledgeBase, args):
    node = kb.get(args.id)
    if not node:
        print(f"未找到节点: {args.id}")
        return

    pri = PRIORITY_LEVELS.get(node.priority, PRIORITY_LEVELS[5])
    cat = ONTOLOGY.get(node.category, {}).get("label", node.category) if node.category else "-"

    print(f"{'=' * 60}")
    print(f"📌 {node.title}")
    print(f"{'=' * 60}")
    print(f"ID:       {node.id}")
    print(f"优先级:   {pri['label']} (P{node.priority})")
    print(f"分类:     {cat}  /  {node.l2_category or '-'}")
    print(f"来源:     {node.source_file}  § {node.source_section}")
    print(f"标签:     {', '.join(node.tags) if node.tags else '-'}")
    print(f"父节点:   {node.parent_id or '(根节点)'}")
    children = kb.get_children(node.id)
    print(f"子节点:   {', '.join(c.title for c in children) if children else '(无)'}")
    print(f"创建:     {node.created_at}")
    print(f"更新:     {node.updated_at}")
    if node.abstract:
        print(f"\n📝 摘要:")
        print(f"   {node.abstract}")
    if node.references:
        print(f"\n📚 参考文献:")
        for r in node.references:
            print(f"   {r}")
    print(f"\n{'─' * 60}")
    print(f"📄 正文 (Markdown):")
    print(f"{'─' * 60}")
    print(node.content if node.content else "（无内容）")
    print(f"{'─' * 60}")


def cmd_stats(kb: KnowledgeBase, args):
    s = kb.stats()
    print(f"{'=' * 40}")
    print(f"📊 知识库统计")
    print(f"{'=' * 40}")
    print(f"节点总数:   {s['node_count']}")
    print(f"最大深度:   {s['max_depth']}")
    print(f"\n按分类:")
    for cat, count in s["by_category"].items():
        label = ONTOLOGY.get(cat, {}).get("label", cat)
        bar = "█" * min(count, 40)
        print(f"  {label:12s} {count:3d}  {bar}")
    print(f"\n按优先级:")
    for level, count in s["by_priority"].items():
        label = PRIORITY_LEVELS.get(level, {}).get("label", f"P{level}")
        print(f"  P{level} {label:8s} {count:3d}")
    print(f"\n热门标签:")
    for tag, count in list(s["top_tags"].items())[:10]:
        print(f"  {tag:20s} {count:3d}")


def cmd_add(kb: KnowledgeBase, args):
    node = KnowledgeNode(
        id=args.id or "",
        title=args.title,
        abstract=args.abstract or "",
        content=args.content or "",
        priority=args.priority or 3,
        tags=args.tags.split(",") if args.tags else [],
        category=args.category or "",
        l2_category=args.l2 or "",
        parent_id=args.parent or None,
        source_file=args.source or "",
        source_section=args.section or "",
    )
    nid = kb.add(node)
    print(f"✅ 已添加: {node.title}  (id={nid})")


def cmd_edit(kb: KnowledgeBase, args):
    updates = {}
    if args.title is not None:
        updates["title"] = args.title
    if args.abstract is not None:
        updates["abstract"] = args.abstract
    if args.content is not None:
        updates["content"] = args.content
    if args.priority is not None:
        updates["priority"] = args.priority
    if args.tags is not None:
        updates["tags"] = [t.strip() for t in args.tags.split(",")]
    if args.category is not None:
        updates["category"] = args.category
    if args.l2 is not None:
        updates["l2_category"] = args.l2
    if args.parent is not None:
        updates["parent_id"] = args.parent if args.parent != "none" else None
    if args.source is not None:
        updates["source_file"] = args.source
    if args.section is not None:
        updates["source_section"] = args.section

    if not updates:
        print("未提供任何更新字段")
        return

    ok = kb.update(args.id, **updates)
    if ok:
        print(f"✅ 已更新: {args.id}")
        cmd_show(kb, args)
    else:
        print(f"❌ 未找到节点: {args.id}")


def cmd_delete(kb: KnowledgeBase, args):
    node = kb.get(args.id)
    if not node:
        print(f"❌ 未找到节点: {args.id}")
        return
    ok = kb.delete(args.id, cascade=args.cascade)
    if ok:
        mode = "（级联删除子节点）" if args.cascade else "（子节点已提升为根节点）"
        print(f"🗑 已删除: {node.title} {mode}")
    else:
        print(f"❌ 删除失败: {args.id}")


def cmd_import(kb: KnowledgeBase, args):
    from kb_import import import_and_merge, import_directory_merge

    filepath = Path(args.path)

    if args.no_merge:
        # 旧模式：每份报告独立成树
        from kb_import import import_md, import_directory
        if filepath.is_dir():
            results = import_directory(filepath, default_category=args.category or "")
            total = 0
            for fname, nodes in results.items():
                if not args.dry_run:
                    for n in nodes:
                        kb.add(n)
                print(f"  📄 {fname}: {len(nodes)} 个知识点")
                total += len(nodes)
            if not args.dry_run:
                kb.ensure_category_tree()
            action = "将导入" if args.dry_run else "已导入"
            print(f"\n📦 {action} {len(results)} 个文件，共 {total} 个知识点（独立模式）")
        else:
            nodes = import_md(filepath, default_category=args.category or "")
            if not args.dry_run:
                for n in nodes:
                    kb.add(n)
                kb.ensure_category_tree()
            action = "将导入" if args.dry_run else "已导入"
            print(f"📄 {filepath.name}: {action} {len(nodes)} 个知识点（独立模式）\n")
            for n in nodes:
                cat = ONTOLOGY.get(n.category, {}).get("label", n.category) if n.category else "-"
                print(f"  {'⭐' * n.priority} [{cat}] {n.title}")
                print()
    else:
        # 默认：合并模式
        if args.dry_run:
            from kb_import import import_md
            if filepath.is_dir():
                for md_file in sorted(filepath.glob("*.md")):
                    nodes = import_md(md_file, default_category=args.category or "")
                    print(f"  📄 {md_file.name}: 预览 {len(nodes)} 个节点（将合并入已有知识树）")
            else:
                nodes = import_md(filepath, default_category=args.category or "")
                print(f"📄 {filepath.name}: 预览 {len(nodes)} 个节点（将合并入已有知识树）\n")
                # 获取章节层级以识别 H1
                from kb_import import _parse_headings
                sections, _ = _parse_headings(Path(filepath).read_text(encoding="utf-8"))
                title_to_level = {s["title"]: s["level"] for s in sections}
                for n in nodes:
                    cat = ONTOLOGY.get(n.category, {}).get("label", n.category) if n.category else "-"
                    sec_level = title_to_level.get(n.source_section, 0)
                    if sec_level == 1 and not n.category and n.children:
                        action = "跳过"
                    elif not n.category and not n.children:
                        action = "跳过"
                    elif n.category and kb.find_by_title_category(n.title, n.category):
                        action = "合并"
                    else:
                        action = "新增"
                    print(f"  {action:4s} {'⭐' * n.priority} [{cat:6s}] {n.title}")
                print()
            print("⚠ 试运行模式。去掉 --dry-run 确认导入。")
        else:
            if filepath.is_dir():
                stats = import_directory_merge(kb, filepath, default_category=args.category or "")
            else:
                stats = import_and_merge(kb, filepath, default_category=args.category or "")
                print(f"📄 {filepath.name}: 合并 {stats['merged']}, 新增 {stats['new']}, 跳过 {stats['skipped']}")
                print()

    if args.dry_run and not args.no_merge:
        print("⚠ 试运行模式，未实际写入。去掉 --dry-run 确认导入。")

    if not filepath.exists():
        print(f"❌ 路径不存在: {args.path}")


def cmd_export(kb: KnowledgeBase, args):
    from kb_export import export_html

    output = Path(args.output) if args.output else (PROJECT_DIR / "output" / "knowledge_base.html")
    out_path = export_html(kb, output)
    print(f"✅ HTML 已导出: {out_path.resolve()}")
    print(f"   可在浏览器中打开查看")


def cmd_reorganize(kb: KnowledgeBase, args):
    """重建分类树层级：主根 → 8 个分类 → 概念节点。"""
    root_id = kb.ensure_category_tree()
    root = kb.get(root_id)
    print(f"✅ 分类树已重建")
    print(f"   主根: {root.title if root else '?'}")
    cats = kb.get_children(root_id)
    print(f"   分类: {len(cats)} 个")
    for c in cats:
        sub = kb.get_children(c.id)
        print(f"     [{c.title}] → {len(sub)} 个概念节点")
    print()
    print(f"   💡 建议运行 python3 kb.py export 更新可视化")


def cmd_setup(kb: KnowledgeBase, args):
    """在新机器上注册此知识库到 Hermes Agent。"""
    skill_dir = Path.home() / ".hermes" / "skills" / "note-taking" / "zsk-knowledge-base"
    skill_dir.mkdir(parents=True, exist_ok=True)

    skill_content = f"""---
name: zsk-knowledge-base
description: "Use when the user asks to search, query, import, or manage the Agent 技术知识库 (zsk). A local Markdown-report → JSON knowledge base with CLI at {PROJECT_DIR}/kb.py."
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [knowledge-base, ontology, agent-tech, markdown, json]
    related_skills: [obsidian, llm-wiki]
---

# ZSK — Agent 开发技术知识库

## Overview

zsk is a local knowledge base built from Markdown research reports about Agent development technology.
Reports are parsed into structured JSON nodes organized by an 8-category ontology.

**Project directory**: `{PROJECT_DIR}`
**CLI entry**: `python3 {PROJECT_DIR}/kb.py`
**Data file**: `{PROJECT_DIR}/data/knowledge_base.json`
**Reports dir**: `{PROJECT_DIR}/reports/`
**HTML output**: `{PROJECT_DIR}/output/knowledge_base.html`

## When to Use

- User asks to search the knowledge base: "搜索知识库", "find xxx in kb"
- User wants to import new reports: "导入研报", "把这篇加到知识库"
- User wants stats or overview: "知识库有多少节点"
- User wants the HTML visualization: "导出可视化", "open the kb"
- User wants to add/edit/delete nodes: "加一个知识点", "修改 xxx"

## Key Commands

All commands use absolute paths — no `cd` needed.

```bash
python3 {PROJECT_DIR}/kb.py search "<keyword>"
python3 {PROJECT_DIR}/kb.py list
python3 {PROJECT_DIR}/kb.py list --category rag
python3 {PROJECT_DIR}/kb.py list --priority 1
python3 {PROJECT_DIR}/kb.py show <node_id>
python3 {PROJECT_DIR}/kb.py stats
```

### Import Reports

```bash
# Always dry-run first
python3 {PROJECT_DIR}/kb.py import <path/to/report.md> --dry-run

# Interactive (recommended)
python3 {PROJECT_DIR}/kb.py import <path/to/report.md> -i

# Direct import
python3 {PROJECT_DIR}/kb.py import <path/to/report.md>
```

### Export

```bash
python3 {PROJECT_DIR}/kb.py export
# Then open {PROJECT_DIR}/output/knowledge_base.html in browser
```

## Workflows

### User asks a knowledge question

1. `python3 {PROJECT_DIR}/kb.py search "<keywords>"`
2. If hits, show details with `python3 {PROJECT_DIR}/kb.py show <id>`
3. Synthesize answer from KB content
4. If no hits, tell user KB doesn't cover it

### User wants to import reports

1. `python3 {PROJECT_DIR}/kb.py stats` — check current state
2. `python3 {PROJECT_DIR}/kb.py import <path> --dry-run` — preview
3. Show user extracted nodes (categories, priorities, structure)
4. Only run real import after user confirms

### User wants visualization

1. `python3 {PROJECT_DIR}/kb.py export` — re-export latest
2. Tell user to open the HTML file in browser

## Common Pitfalls

1. **Use `python3`, not `python`.** macOS `python` may not exist.
2. **Always dry-run before import.** Preview extracted nodes first.
3. **Missing `markdown` dependency.** If export fails: `pip3 install markdown`.
4. **Importing same file twice creates duplicates.** Search first to check.
"""

    skill_md = skill_dir / "SKILL.md"
    skill_md.write_text(skill_content, encoding="utf-8")

    print(f"✅ Skill 已注册到: {skill_md}")
    print()
    print(f"   Hermes Agent 现在可以通过自然语言使用知识库。")
    print(f"   试试在新会话中说：「搜索知识库里有什么」")


def _interactive_import(kb: KnowledgeBase, args):
    """交互式导入：先预览，逐条确认（默认合并模式）。"""
    from kb_import import import_md, import_and_merge

    filepath = Path(args.path)
    if not filepath.is_file():
        print(f"❌ 文件不存在: {args.path}")
        return

    nodes = import_md(filepath, default_category=args.category or "")
    if not nodes:
        print("未提取到知识点。")
        return

    print(f"\n📄 {filepath.name} → 提取到 {len(nodes)} 个节点（将合并入已有知识树）:\n")
    for i, n in enumerate(nodes, 1):
        cat = ONTOLOGY.get(n.category, {}).get("label", n.category) if n.category else "-"
        existing = kb.find_by_title_category(n.title, n.category) if n.category else None
        action = "合并" if existing else "新增"
        print(f"  [{i}] {action:4s} {'⭐' * n.priority} [{cat}] {n.title}")
        if n.abstract:
            print(f"      {n.abstract[:100]}")
        print()

    while True:
        resp = input("导入全部（合并模式）？[Y]es / [n]o 逐条选择 / [q]uit: ").strip().lower()
        if resp in ("", "y", "yes"):
            stats = import_and_merge(kb, filepath, default_category=args.category or "")
            print(f"✅ 合并 {stats['merged']}, 新增 {stats['new']}, 跳过 {stats['skipped']}")
            return
        elif resp in ("n", "no"):
            selected_ids = []
            for i, n in enumerate(nodes, 1):
                ans = input(f"  导入 [{i}] {n.title}? [y/N]: ").strip().lower()
                if ans in ("y", "yes"):
                    selected_ids.append(n.id)
            # 只合并选中的节点
            for n in nodes:
                if n.id not in selected_ids:
                    continue
                existing = kb.find_by_title_category(n.title, n.category) if n.category else None
                if existing:
                    kb.merge_node(n)
                    print(f"  已合并: {n.title}")
                else:
                    kb.nodes[n.id] = n
                    if n.parent_id and n.parent_id in kb.nodes:
                        if n.id not in kb.nodes[n.parent_id].children:
                            kb.nodes[n.parent_id].children.append(n.id)
                    print(f"  已新增: {n.title}")
            kb._save()
            print(f"✅ 完成")
            return
        elif resp in ("q", "quit"):
            print("已取消")
            return
        else:
            print("请输入 y / n / q")


def main():
    parser = argparse.ArgumentParser(
        description="Agent 开发技术知识库 CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python kb.py list                              # 列出所有知识点
  python kb.py list --category architecture      # 按分类筛选
  python kb.py search "ReAct"                    # 搜索
  python kb.py show abc123                       # 查看详情
  python kb.py stats                             # 统计
  python kb.py import reports/agent-技术研报.md   # 导入研报
  python kb.py import reports/agent-技术研报.md --interactive  # 交互式导入
  python kb.py import reports/ --dry-run         # 试运行文件夹导入
  python kb.py export                            # 导出 HTML
  python kb.py add --title "新知识点" --category architecture --priority 2
  python kb.py edit abc123 --priority 1
  python kb.py delete abc123
        """,
    )
    sub = parser.add_subparsers(dest="command")

    # list
    p = sub.add_parser("list", help="列出知识点")
    p.add_argument("--category", "-c")
    p.add_argument("--tag", "-t")
    p.add_argument("--priority", "-p", type=int, choices=[1, 2, 3, 4, 5])
    p.add_argument("--limit", "-n", type=int)
    p.add_argument("--verbose", "-v", action="store_true")

    # search
    p = sub.add_parser("search", help="全文搜索")
    p.add_argument("keyword")

    # show
    p = sub.add_parser("show", help="查看详情")
    p.add_argument("id")

    # stats
    sub.add_parser("stats", help="统计信息")

    # add
    p = sub.add_parser("add", help="手动添加知识点")
    p.add_argument("--id")
    p.add_argument("--title", required=True)
    p.add_argument("--abstract")
    p.add_argument("--content")
    p.add_argument("--priority", type=int, choices=[1, 2, 3, 4, 5])
    p.add_argument("--tags")
    p.add_argument("--category")
    p.add_argument("--l2")
    p.add_argument("--parent")
    p.add_argument("--source")
    p.add_argument("--section")

    # edit
    p = sub.add_parser("edit", help="编辑知识点")
    p.add_argument("id")
    p.add_argument("--title")
    p.add_argument("--abstract")
    p.add_argument("--content")
    p.add_argument("--priority", type=int, choices=[1, 2, 3, 4, 5])
    p.add_argument("--tags")
    p.add_argument("--category")
    p.add_argument("--l2")
    p.add_argument("--parent")
    p.add_argument("--source")
    p.add_argument("--section")

    # delete
    p = sub.add_parser("delete", help="删除知识点")
    p.add_argument("id")
    p.add_argument("--cascade", action="store_true", help="级联删除子节点")

    # import
    p = sub.add_parser("import", help="从 MD 研报导入（默认合并模式）")
    p.add_argument("path", help="MD 文件或目录")
    p.add_argument("--category", "-c", help="默认分类")
    p.add_argument("--dry-run", action="store_true", help="试运行（不写入）")
    p.add_argument("--interactive", "-i", action="store_true", help="交互式逐条确认")
    p.add_argument("--no-merge", action="store_true", help="禁用合并：每份报告独立成树")

    # export
    p = sub.add_parser("export", help="导出 HTML")
    p.add_argument("--output", "-o", help="输出路径，默认 output/knowledge_base.html")

    # setup
    sub.add_parser("setup", help="在新机器上注册此知识库到 Hermes Agent")

    # reorganize
    sub.add_parser("reorganize", help="重建分类树层级：主根 → 分类 → 概念")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    kb = KnowledgeBase(PROJECT_DIR / "data" / "knowledge_base.json")

    commands = {
        "list": cmd_list,
        "search": cmd_search,
        "show": cmd_show,
        "stats": cmd_stats,
        "add": cmd_add,
        "edit": cmd_edit,
        "delete": cmd_delete,
        "import": cmd_import,
        "export": cmd_export,
        "setup": cmd_setup,
        "reorganize": cmd_reorganize,
    }

    if args.command in commands:
        if args.command == "import" and getattr(args, "interactive", False):
            _interactive_import(kb, args)
        else:
            commands[args.command](kb, args)


if __name__ == "__main__":
    main()
