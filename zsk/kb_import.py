"""
MD 研报导入器。
混合策略：自动按标题层级提取 + 支持手动标注。
"""
from __future__ import annotations

import re
from pathlib import Path
from kb_core import KnowledgeNode
from kb_ontology import map_section_to_category, PREDEFINED_TAGS


# ── MD 解析 ──────────────────────────────────────────────

def _parse_headings(md_text: str) -> list[dict]:
    """
    解析 MD 文本，按标题拆分章节。
    返回列表，每项包含: level, title, content, annotations, line_start。
    """
    lines = md_text.split("\n")
    sections: list[dict] = []
    current_section: dict | None = None
    current_lines: list[str] = []
    ref_lines: list[str] = []         # 参考文献行
    in_references = False

    heading_re = re.compile(r"^(#{1,6})\s+(.+)$")
    fence_re = re.compile(r"^(`{3,}|~{3,})")

    in_fence = False       # 是否在代码块内
    fence_char = ""        # 代码块分隔符 (``` 或 ~~~)

    for lineno, line in enumerate(lines, 1):
        # 检测代码块边界（在 heading 检测之前）
        fm = fence_re.match(line)
        if fm:
            marker = fm.group(1)
            if not in_fence:
                in_fence = True
                fence_char = marker
                if current_section is not None:
                    current_lines.append(line)
                continue
            elif marker == fence_char:
                in_fence = False
                fence_char = ""
                if current_section is not None:
                    current_lines.append(line)
                continue

        if in_fence:
            # 代码块内的行不做 heading 解析，直接加入内容
            if current_section is not None:
                current_lines.append(line)
            continue

        m = heading_re.match(line)
        if m:
            # 保存上一个 section
            if current_section is not None:
                current_section["content"] = "\n".join(current_lines).strip()
                sections.append(current_section)

            level = len(m.group(1))
            title = m.group(2).strip()
            current_section = {
                "level": level,
                "title": title,
                "content": "",
                "annotations": {},
                "line_start": lineno,
            }
            current_lines = []

            # 检测是否为参考文献章节
            if "参考" in title and ("文献" in title or "资料" in title or "书目" in title):
                in_references = True
            else:
                in_references = False
        else:
            if in_references:
                ref_lines.append(line)
            elif current_section is not None:
                current_lines.append(line)
            # 如果还没有任何 section (前言部分), 跳过

    # 保存最后一个 section
    if current_section is not None:
        current_section["content"] = "\n".join(current_lines).strip()
        sections.append(current_section)

    # 解析每个 section 的 annotations
    for sec in sections:
        sec["annotations"] = _parse_kb_annotations(sec["content"])
        # 去掉 annotation 行
        sec["content"] = _strip_annotations(sec["content"])

    # 收集参考文献
    references = _parse_references(ref_lines)

    return sections, references


def _parse_kb_annotations(content: str) -> dict:
    """
    解析 <!-- kb: key=value key=value --> 格式的手动标注。
    示例: <!-- kb: priority=1 tags=react,planning parent=abc123 -->
    """
    annotations = {}
    pattern = re.compile(r"<!--\s*kb:\s*(.+?)\s*-->")
    for m in pattern.finditer(content):
        params = m.group(1).strip()
        # 按空格拆分 key=value
        for part in params.split():
            if "=" in part:
                k, v = part.split("=", 1)
                k = k.strip()
                v = v.strip()
                if k == "tags":
                    annotations[k] = [t.strip() for t in v.split(",")]
                elif k == "priority":
                    try:
                        annotations[k] = int(v)
                    except ValueError:
                        pass
                elif k in ("parent_id", "parent", "pid"):
                    annotations["parent_id"] = v
                elif k == "category":
                    annotations[k] = v
                elif k == "l2_category":
                    annotations[k] = v
                elif k == "abstract":
                    annotations[k] = v
    return annotations


def _strip_annotations(content: str) -> str:
    """移除 <!-- kb: ... --> 标注行。"""
    return re.sub(r"<!--\s*kb:\s*.+?\s*-->\n?", "", content)


def _parse_references(lines: list[str]) -> list[str]:
    """解析参考文献行。"""
    refs = []
    ref_pattern = re.compile(r"^\[(\d+)\]\s*(.+)$")
    for line in lines:
        line = line.strip()
        if not line:
            continue
        m = ref_pattern.match(line)
        if m:
            refs.append(f"[{m.group(1)}] {m.group(2)}")
        else:
            # 非编号引用行
            refs.append(line)
    return refs


# ── 标题 → 节点提取 ──────────────────────────────────────

def _generate_id(title: str, category: str = "") -> str:
    """根据标题生成语义化 ID。"""
    import hashlib
    base = re.sub(r"[^\w\u4e00-\u9fff]", "-", title.lower()).strip("-")
    base = re.sub(r"-+", "-", base)
    if category:
        base = f"{category}-{base}"
    if len(base) > 40:
        h = hashlib.md5(base.encode()).hexdigest()[:8]
        base = f"{base[:30]}-{h}"
    return base


def _extract_abstract(content: str, max_len: int = 120) -> str:
    """从正文提取摘要：取第一段非空文本。"""
    for line in content.split("\n"):
        line = line.strip()
        # 跳过标题、代码块、表格
        if not line or line.startswith("#") or line.startswith("```") or line.startswith("|"):
            continue
        # 移除 markdown 格式
        clean = re.sub(r"[\*\_\`\>\-\+]", "", line).strip()
        if len(clean) > 10:
            if len(clean) > max_len:
                return clean[:max_len] + "…"
            return clean
    return ""


def _extract_tags(content: str, title: str, category: str) -> list[str]:
    """从内容和标题中提取标签。"""
    tags = []
    text = (title + " " + content[:500]).lower()

    # 关键词 → 标签映射
    keyword_map = {
        "react": "react",
        "plan and execute": "plan-execute",
        "plan-and-execute": "plan-execute",
        "cot": "cot",
        "chain of thought": "cot",
        "tree of thought": "tree-of-thought",
        "function call": "function-calling",
        "function calling": "function-calling",
        "tool call": "function-calling",
        "mcp": "mcp",
        "model context protocol": "mcp",
        "langchain": "langchain",
        "langgraph": "langgraph",
        "autogen": "autogen",
        "crewai": "crewai",
        "rag": "rag",
        "retrieval": "retrieval-strategy",
        "embedding": "embedding",
        "向量": "vector-retrieval",
        "记忆": "memory",
        "短期记忆": "short-term",
        "长期记忆": "long-term",
        "护栏": "guardrails",
        "guardrail": "guardrails",
        "rlhf": "rlhf-dpo",
        "dpo": "rlhf-dpo",
        "红队": "red-teaming",
        "prompt injection": "prompt-injection",
        "benchmark": "benchmark",
        "评测": "benchmark",
        "llm as judge": "llm-as-judge",
        "swarm": "swarm",
        "multi agent": "multi-agent",
        "multi-agent": "multi-agent",
        "多智能体": "multi-agent",
        "分块": "chunking",
        "chunking": "chunking",
        "重排序": "reranking",
        "rerank": "reranking",
    }
    for kw, tag in keyword_map.items():
        if kw in text and tag not in tags:
            tags.append(tag)

    # 难度推断
    if any(w in text for w in ["入门", "基础", "简介", "概述", "介绍"]):
        if "beginner" not in tags:
            tags.append("beginner")
    if any(w in text for w in ["进阶", "高级", "深入", "优化"]):
        if "advanced" not in tags:
            tags.append("advanced")

    # 按预定义标签过滤 + 去重
    valid = [t for t in tags if t in PREDEFINED_TAGS][:8]
    return valid


def _infer_priority(content: str, title: str, level: int) -> int:
    """根据标题层级和内容推断优先级。"""
    text = (title + " " + content[:300]).lower()
    # H1 = 高层概述 → P1/P2
    if level == 1:
        return 1 if any(w in text for w in ["概述", "简介", "架构", "核心"]) else 2
    # H2 = 核心章节 → P1/P2
    if level == 2:
        return 1 if any(w in text for w in ["核心", "原理", "基础"]) else 2
    # H3 = 具体技术 → P2/P3
    if level == 3:
        return 2 if any(w in text for w in ["核心", "重要", "常用"]) else 3
    # H4+ = 细节 → P3/P4
    if level >= 4:
        return 3 if any(w in text for w in ["配置", "实践", "示例"]) else 4
    return 3


def _build_tree(sections: list[dict]) -> list[dict]:
    """
    根据标题层级构建父子关系。
    返回带有 parent_title 字段的 sections 列表。
    """
    # 按层级维护最近的父节点标题
    parent_stack: list[str | None] = [None] * 7  # H1-H6

    for sec in sections:
        lv = sec["level"]
        # 找到最近的低层级标题作为 parent
        parent_title = None
        for p in range(lv - 1, 0, -1):
            if parent_stack[p] is not None:
                parent_title = parent_stack[p]
                break
        sec["_parent_title"] = parent_title
        # 更新当前层级的栈
        parent_stack[lv] = sec["title"]
        # 清空更深层级
        for d in range(lv + 1, 7):
            parent_stack[d] = None

    return sections


# ── 主入口 ──────────────────────────────────────────────

def import_md(
    filepath: str | Path,
    default_category: str = "",
    auto_priority: bool = True,
    auto_tags: bool = True,
) -> list[KnowledgeNode]:
    """
    导入单个 MD 研报，返回提取的知识节点列表。
    
    参数:
        filepath: MD 文件路径
        default_category: 默认一级分类（章节映射失败时使用）
        auto_priority: 是否自动推断优先级
        auto_tags: 是否自动提取标签
    """
    filepath = Path(filepath)
    md_text = filepath.read_text(encoding="utf-8")
    filename = filepath.name

    sections, references = _parse_headings(md_text)
    sections = _build_tree(sections)

    # 为每个 section 构建标题 → node_id 映射 (先分配 ID)
    title_to_id: dict[str, str] = {}
    nodes: list[KnowledgeNode] = []
    extracted_refs: list[str] = []  # 收集到的参考文献节点

    for sec in sections:
        title = sec["title"]
        ann = sec["annotations"]
        content = sec["content"]

        # 跳过参考文献章节（单独处理）
        if "参考" in title and ("文献" in title or "资料" in title or "书目" in title):
            continue

        # 确定分类
        if "category" in ann:
            category = ann["category"]
        else:
            category = map_section_to_category(title) or default_category

        # 如果 mapping 没有匹配且无默认分类 → 跳过该章节作为独立节点
        # （内容会作为父节点的 content 一部分）
        if not category and sec["level"] <= 2:
            # 顶层无分类节点 → 仍创建，category 留空供人工补充
            pass

        # 生成 ID
        node_id = ann.get("id") or _generate_id(title, category)
        # 处理标题冲突
        base_id = node_id
        counter = 1
        while node_id in title_to_id.values():
            node_id = f"{base_id}-{counter}"
            counter += 1
        title_to_id[title] = node_id

        # 优先级
        if "priority" in ann:
            priority = ann["priority"]
        elif auto_priority:
            priority = _infer_priority(content, title, sec["level"])
        else:
            priority = 3

        # 标签
        if "tags" in ann:
            tags = ann["tags"]
        elif auto_tags:
            tags = _extract_tags(content, title, category)
        else:
            tags = []

        # 摘要
        abstract = ann.get("abstract", "") or _extract_abstract(content)

        # 收集参考文献
        node_refs = _parse_references(content.split("\n"))

        node = KnowledgeNode(
            id=node_id,
            title=title,
            abstract=abstract,
            content=content,
            priority=priority,
            tags=tags,
            category=category,
            l2_category=ann.get("l2_category", ""),
            source_file=filename,
            source_section=title,
            references=node_refs,
        )
        nodes.append(node)

    # 第二轮：建立父子关系
    for sec in sections:
        if sec["title"] not in title_to_id:
            continue
        node_id = title_to_id[sec["title"]]
        parent_title = sec.get("_parent_title")
        if parent_title and parent_title in title_to_id:
            parent_id = title_to_id[parent_title]
            node = next(n for n in nodes if n.id == node_id)
            node.parent_id = parent_id
            # 把子节点加到父节点的 children
            parent_node = next(n for n in nodes if n.id == parent_id)
            if node_id not in parent_node.children:
                parent_node.children.append(node_id)

    # 第二轮加：子节点继承父节点的 category（如果自身未设置）
    for node in nodes:
        if not node.category and node.parent_id:
            parent = next((n for n in nodes if n.id == node.parent_id), None)
            if parent and parent.category:
                node.category = parent.category

    # 第三轮：如果文件有全局参考文献，附加到最后一个节点
    if references and nodes:
        # 找到最相关的顶层节点（H1）
        h1_nodes = [n for n in nodes
                    if any(s["title"] == n.source_section and s["level"] == 1
                           for s in sections)]
        target = h1_nodes[-1] if h1_nodes else nodes[-1]
        for ref in references:
            if ref not in target.references:
                target.references.append(ref)

    return nodes


def import_directory(
    dirpath: str | Path,
    default_category: str = "",
) -> dict[str, list[KnowledgeNode]]:
    """
    批量导入目录中所有 MD 文件。
    返回 {filename: [nodes]} 映射。
    """
    dirpath = Path(dirpath)
    results: dict[str, list[KnowledgeNode]] = {}
    for md_file in sorted(dirpath.glob("*.md")):
        nodes = import_md(md_file, default_category=default_category)
        results[md_file.name] = nodes
    return results


# ── 合并导入：多报告整合为统一知识树 ─────────────────────

def import_and_merge(kb, filepath: str | Path,
                     default_category: str = "") -> dict:
    """
    导入 MD 研报并合并到已有知识库。
    相同 category + title 的节点会合并内容，而非重复创建。
    报告标题（H1）不作为节点，H2 章节直接成为顶层概念。
    
    返回 {"merged": N, "new": N, "skipped": N}
    """
    # 用原始 parse 获取章节层级（用于识别 H1 报告标题）
    filepath = Path(filepath)
    md_text = filepath.read_text(encoding="utf-8")
    sections, _ = _parse_headings(md_text)
    title_to_level: dict[str, int] = {}
    for sec in sections:
        title_to_level[sec["title"]] = sec["level"]

    # 提取所有节点
    nodes = import_md(filepath, default_category=default_category)

    # 拓扑排序：父节点先于子节点处理
    ordered = _topo_sort(nodes)

    # ID 映射：incoming_id → final_id（merge 后可能是已有节点的 id）
    id_map: dict[str, str | None] = {}
    stats = {"merged": 0, "new": 0, "skipped": 0}

    for node in ordered:
        # 跳过报告标题（H1、无分类、有子节点）
        sec_level = title_to_level.get(node.source_section, 0)
        if sec_level == 1 and not node.category and node.children:
            stats["skipped"] += 1
            id_map[node.id] = None
            continue

        # 跳过无分类叶子节点（如"概述"等通用章节）
        if not node.category and not node.children:
            stats["skipped"] += 1
            id_map[node.id] = None
            continue

        # 重映射 parent_id
        if node.parent_id and node.parent_id in id_map:
            mapped = id_map[node.parent_id]
            if mapped is None:
                node.parent_id = None
            else:
                node.parent_id = mapped

        # 尝试合并
        existing = kb.find_by_title_category(node.title, node.category) if node.category else None
        if existing:
            final_id = kb.merge_node(node)
            id_map[node.id] = final_id
            stats["merged"] += 1
        else:
            # 全新节点：直接加入 KB
            kb.nodes[node.id] = node
            if node.parent_id and node.parent_id in kb.nodes:
                parent = kb.nodes[node.parent_id]
                if node.id not in parent.children:
                    parent.children.append(node.id)
            id_map[node.id] = node.id
            stats["new"] += 1

    kb._save()
    # 重建分类层级（主根 → 分类 → 概念）
    kb.ensure_category_tree()
    # 自动补摘要 + 去重
    kb.fill_empty_abstracts()
    kb.dedup_pass()
    return stats


def import_directory_merge(kb, dirpath: str | Path,
                           default_category: str = "") -> dict:
    """
    批量合并导入目录中所有 MD 文件。
    返回全局统计 {"merged": N, "new": N, "skipped": N}。
    """
    dirpath = Path(dirpath)
    total = {"merged": 0, "new": 0, "skipped": 0}
    for md_file in sorted(dirpath.glob("*.md")):
        s = import_and_merge(kb, md_file, default_category=default_category)
        print(f"  📄 {md_file.name}: 合并 {s['merged']}, 新增 {s['new']}, 跳过 {s['skipped']}")
        for k in total:
            total[k] += s[k]
    kb.ensure_category_tree()
    kb.fill_empty_abstracts()
    kb.dedup_pass()
    return total


def _topo_sort(nodes: list) -> list:
    """按深度排序节点（父节点在前）。"""
    id_set = {n.id for n in nodes}

    def depth(n):
        d = 0
        current = n
        while current.parent_id and current.parent_id in id_set:
            d += 1
            # 找父节点
            parent = next((x for x in nodes if x.id == current.parent_id), None)
            if not parent:
                break
            current = parent
        return d

    return sorted(nodes, key=depth)
