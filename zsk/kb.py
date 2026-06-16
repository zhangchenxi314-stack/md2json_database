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
    from kb_import import import_md, import_directory

    filepath = Path(args.path)
    if filepath.is_dir():
        results = import_directory(filepath, default_category=args.category or "")
        total = 0
        for fname, nodes in results.items():
            if not args.dry_run:
                for n in nodes:
                    kb.add(n)
            print(f"  📄 {fname}: {len(nodes)} 个知识点")
            total += len(nodes)
        action = "将导入" if args.dry_run else "已导入"
        print(f"\n📦 {action} {len(results)} 个文件，共 {total} 个知识点")
    elif filepath.is_file():
        nodes = import_md(filepath, default_category=args.category or "")
        if not args.dry_run:
            for n in nodes:
                kb.add(n)
        action = "将导入" if args.dry_run else "已导入"
        print(f"📄 {filepath.name}: {action} {len(nodes)} 个知识点\n")
        for n in nodes:
            cat = ONTOLOGY.get(n.category, {}).get("label", n.category) if n.category else "-"
            print(f"  {'⭐' * n.priority} [{cat}] {n.title}")
            if n.children:
                print(f"     └─ 子节点: {', '.join(n.children)}")
            print()
    else:
        print(f"❌ 路径不存在: {args.path}")

    if args.dry_run:
        print("\n⚠ 试运行模式，未实际写入。去掉 --dry-run 确认导入。")


def cmd_export(kb: KnowledgeBase, args):
    from kb_export import export_html

    output = Path(args.output or "output/knowledge_base.html")
    out_path = export_html(kb, output)
    print(f"✅ HTML 已导出: {out_path.resolve()}")
    print(f"   可在浏览器中打开查看")


def _interactive_import(kb: KnowledgeBase, args):
    """交互式导入：先预览，逐条确认。"""
    from kb_import import import_md

    filepath = Path(args.path)
    if not filepath.is_file():
        print(f"❌ 文件不存在: {args.path}")
        return

    nodes = import_md(filepath, default_category=args.category or "")
    if not nodes:
        print("未提取到知识点。")
        return

    print(f"\n📄 {filepath.name} → 提取到 {len(nodes)} 个知识点:\n")
    for i, n in enumerate(nodes, 1):
        cat = ONTOLOGY.get(n.category, {}).get("label", n.category) if n.category else "-"
        print(f"  [{i}] {'⭐' * n.priority} [{cat}] {n.title}")
        if n.abstract:
            print(f"      {n.abstract[:100]}")
        print()

    while True:
        resp = input("导入全部？[Y]es / [n]o 逐条选择 / [q]uit: ").strip().lower()
        if resp in ("", "y", "yes"):
            for n in nodes:
                kb.add(n)
            print(f"✅ 已导入 {len(nodes)} 个知识点")
            return
        elif resp in ("n", "no"):
            selected = []
            for i, n in enumerate(nodes, 1):
                ans = input(f"  导入 [{i}] {n.title}? [y/N]: ").strip().lower()
                if ans in ("y", "yes"):
                    selected.append(n)
            for n in selected:
                kb.add(n)
            print(f"✅ 已导入 {len(selected)}/{len(nodes)} 个知识点")
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
    p = sub.add_parser("import", help="从 MD 研报导入")
    p.add_argument("path", help="MD 文件或目录")
    p.add_argument("--category", "-c", help="默认分类")
    p.add_argument("--dry-run", action="store_true", help="试运行（不写入）")
    p.add_argument("--interactive", "-i", action="store_true", help="交互式逐条确认")

    # export
    p = sub.add_parser("export", help="导出 HTML")
    p.add_argument("--output", "-o", help="输出路径，默认 output/knowledge_base.html")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    # 项目根目录 = 脚本所在目录的父目录（如果脚本在 src/ 下则为脚本目录）
    script_dir = Path(__file__).resolve().parent

    kb = KnowledgeBase(script_dir / "data" / "knowledge_base.json")

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
    }

    if args.command in commands:
        if args.command == "import" and getattr(args, "interactive", False):
            _interactive_import(kb, args)
        else:
            commands[args.command](kb, args)


if __name__ == "__main__":
    main()
