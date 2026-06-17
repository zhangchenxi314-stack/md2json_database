"""
核心数据模型与 CRUD 操作。
KnowledgeBase 是 JSON 知识库的完整管理器。
"""
from __future__ import annotations

import json
import uuid
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
from dataclasses import dataclass, field, asdict

from kb_ontology import get_priority_info, ONTOLOGY, PRIORITY_LEVELS


# ── 数据模型 ──────────────────────────────────────────────

@dataclass
class KnowledgeNode:
    """知识节点。"""
    id: str
    title: str
    abstract: str = ""
    content: str = ""            # Markdown 正文
    priority: int = 3
    tags: list[str] = field(default_factory=list)
    category: str = ""           # 一级分类 ID (如 "architecture")
    l2_category: str = ""        # 二级分类 ID (如 "single-agent")
    source_file: str = ""        # 来源研报文件名
    source_section: str = ""     # 来源章节标题
    parent_id: Optional[str] = None
    children: list[str] = field(default_factory=list)
    references: list[str] = field(default_factory=list)  # 参考文献
    created_at: str = ""
    updated_at: str = ""

    def __post_init__(self):
        now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        if not self.id:
            self.id = uuid.uuid4().hex[:12]
        if not self.created_at:
            self.created_at = now
        if not self.updated_at:
            self.updated_at = now

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> KnowledgeNode:
        return cls(**{k: d.get(k, "") if k in ("abstract", "content", "source_file",
                                                 "source_section", "category", "l2_category")
                      else d.get(k, []) if k in ("tags", "children", "references")
                      else d.get(k, None) if k == "parent_id"
                      else d.get(k, 3) if k == "priority"
                      else d.get(k, "") for k in d})


# ── CRUD 管理器 ────────────────────────────────────────────

class KnowledgeBase:
    """JSON 知识库管理器。"""

    def __init__(self, path: str | Path = "data/knowledge_base.json"):
        self.path = Path(path)
        self.nodes: dict[str, KnowledgeNode] = {}
        self._load()

    # ── 持久化 ──────────────────────────────────────────

    def _load(self):
        """从 JSON 文件加载。"""
        if self.path.exists():
            data = json.loads(self.path.read_text(encoding="utf-8"))
            self.nodes = {
                nid: KnowledgeNode.from_dict(nd)
                for nid, nd in data.get("nodes", {}).items()
            }
        else:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            self._save()

    def _save(self):
        """保存到 JSON 文件。"""
        data = {
            "meta": {
                "title": "Agent 开发技术知识库",
                "version": "1.0",
                "updated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                "node_count": len(self.nodes),
            },
            "nodes": {nid: n.to_dict() for nid, n in self.nodes.items()},
        }
        self.path.write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    # ── 查询 ────────────────────────────────────────────

    def get(self, node_id: str) -> KnowledgeNode | None:
        return self.nodes.get(node_id)

    def list_all(self) -> list[KnowledgeNode]:
        return sorted(self.nodes.values(), key=lambda n: (n.priority, n.title))

    def search(self, keyword: str) -> list[KnowledgeNode]:
        """全文搜索：标题、摘要、内容、标签。"""
        kw = keyword.lower()
        results = []
        for node in self.nodes.values():
            if (kw in node.title.lower()
                or kw in node.abstract.lower()
                or kw in node.content.lower()
                or any(kw in t.lower() for t in node.tags)):
                results.append(node)
        return sorted(results, key=lambda n: (n.priority, n.title))

    def filter_by_tag(self, tag: str) -> list[KnowledgeNode]:
        tag_lower = tag.lower()
        return [n for n in self.nodes.values()
                if any(tag_lower in t.lower() for t in n.tags)]

    def filter_by_category(self, cat_id: str) -> list[KnowledgeNode]:
        return [n for n in self.nodes.values() if n.category == cat_id]

    def find_by_title_category(self, title: str, category: str) -> KnowledgeNode | None:
        """按标题+分类查找已有节点（用于合并去重）。"""
        title_lower = title.strip().lower()
        for node in self.nodes.values():
            if node.title.strip().lower() == title_lower and node.category == category:
                return node
        return None

    def merge_node(self, incoming: KnowledgeNode) -> str:
        """
        合并节点：如果 KB 中已有同 category + title 的节点，则合并内容；
        否则直接新增。返回最终的 node_id。
        """
        existing = self.find_by_title_category(incoming.title, incoming.category)
        if existing:
            # ── 合并到已有节点 ──
            if incoming.content and incoming.content not in existing.content:
                existing.content += f"\n\n---\n\n{incoming.content}"

            existing.abstract = incoming.abstract or existing.abstract

            # 取更高优先级（数字越小越高）
            if incoming.priority < existing.priority:
                existing.priority = incoming.priority

            # 合并标签（去重）
            for t in incoming.tags:
                if t not in existing.tags:
                    existing.tags.append(t)

            # 合并来源文件
            if incoming.source_file and incoming.source_file not in existing.source_file:
                existing.source_file += f", {incoming.source_file}"

            # 合并参考文献（去重）
            for r in incoming.references:
                if r not in existing.references:
                    existing.references.append(r)

            # 合并子节点
            for child_id in incoming.children:
                if child_id not in existing.children:
                    existing.children.append(child_id)

            # 更新 L2 分类（如果原来没有）
            if not existing.l2_category and incoming.l2_category:
                existing.l2_category = incoming.l2_category

            existing.updated_at = incoming.updated_at
            return existing.id
        else:
            # ── 全新节点 ──
            self.nodes[incoming.id] = incoming
            if incoming.parent_id and incoming.parent_id in self.nodes:
                parent = self.nodes[incoming.parent_id]
                if incoming.id not in parent.children:
                    parent.children.append(incoming.id)
            return incoming.id

    def ensure_category_tree(self) -> str:
        """
        确保分类层级存在：主根 → 8个分类节点。
        将现有无分类根节点挂到对应分类下。
        返回主根节点 ID。
        """
        ROOT_ID = "kb-root"
        now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

        # 1. 确保主根节点存在
        if ROOT_ID not in self.nodes:
            root = KnowledgeNode(
                id=ROOT_ID,
                title="Agent 开发技术知识库",
                abstract="AI Agent 开发技术全景知识体系，按本体分类组织。",
                content="",
                priority=1,
                tags=["overview"],
                source_file="system",
                source_section="",
                created_at=now,
                updated_at=now,
            )
            self.nodes[ROOT_ID] = root

        # 2. 确保 8 个分类节点存在
        cat_ids: dict[str, str] = {}
        for cat_key, cat_info in ONTOLOGY.items():
            cat_node_id = f"cat-{cat_key}"
            cat_ids[cat_key] = cat_node_id

            if cat_node_id not in self.nodes:
                cat_node = KnowledgeNode(
                    id=cat_node_id,
                    title=cat_info["label"],
                    abstract=cat_info["description"],
                    content="",
                    priority=1,
                    tags=["category"],
                    category=cat_key,
                    source_file="system",
                    source_section="",
                    parent_id=ROOT_ID,
                    created_at=now,
                    updated_at=now,
                )
                self.nodes[cat_node_id] = cat_node
                # 加到主根的子节点
                self.nodes[ROOT_ID].children.append(cat_node_id)

        # 3. 将无父节点的概念节点（原 H2 根节点）挂到对应分类下
        for node in list(self.nodes.values()):
            if node.id == ROOT_ID or node.id.startswith("cat-"):
                continue
            # 只处理没有父节点、或父节点不在 KB 中的（即原来的根节点）
            if node.parent_id and node.parent_id in self.nodes:
                continue
            # 子节点保留原有父子关系不动
            
            if node.category and node.category in cat_ids:
                cat_node_id = cat_ids[node.category]
                node.parent_id = cat_node_id
                if node.id not in self.nodes[cat_node_id].children:
                    self.nodes[cat_node_id].children.append(node.id)

        # 4. 清理：移除分类节点的 children 中已不存在的引用
        for cat_node_id in cat_ids.values():
            if cat_node_id in self.nodes:
                cat_node = self.nodes[cat_node_id]
                cat_node.children = [c for c in cat_node.children if c in self.nodes]

        self._save()
        return ROOT_ID

    def filter_by_priority(self, level: int) -> list[KnowledgeNode]:
        return [n for n in self.nodes.values() if n.priority == level]

    def get_roots(self) -> list[KnowledgeNode]:
        """获取所有根节点（无 parent 的节点）。"""
        return [n for n in self.nodes.values() if not n.parent_id]

    def get_children(self, node_id: str) -> list[KnowledgeNode]:
        """获取某节点的直接子节点。"""
        node = self.nodes.get(node_id)
        if not node:
            return []
        return [self.nodes[c] for c in node.children if c in self.nodes]

    def get_descendants(self, node_id: str) -> list[KnowledgeNode]:
        """递归获取所有子孙节点。"""
        result = []
        for child in self.get_children(node_id):
            result.append(child)
            result.extend(self.get_descendants(child.id))
        return result

    def get_siblings(self, node_id: str) -> list[KnowledgeNode]:
        """获取同级节点。"""
        node = self.nodes.get(node_id)
        if not node or not node.parent_id:
            return self.get_roots()
        parent = self.nodes.get(node.parent_id)
        if not parent:
            return []
        return [self.nodes[c] for c in parent.children
                if c in self.nodes and c != node_id]

    # ── 增删改 ──────────────────────────────────────────

    def add(self, node: KnowledgeNode) -> str:
        """添加节点，自动维护父子关系。返回 node_id。"""
        self.nodes[node.id] = node
        if node.parent_id and node.parent_id in self.nodes:
            parent = self.nodes[node.parent_id]
            if node.id not in parent.children:
                parent.children.append(node.id)
        self._save()
        return node.id

    def update(self, node_id: str, **kwargs) -> bool:
        """更新节点字段。"""
        node = self.nodes.get(node_id)
        if not node:
            return False

        # 处理 parent 变更
        old_parent = node.parent_id
        new_parent = kwargs.get("parent_id", old_parent)

        for k, v in kwargs.items():
            if hasattr(node, k):
                setattr(node, k, v)
        node.updated_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

        # 从旧 parent 的 children 中移除
        if old_parent != new_parent:
            if old_parent and old_parent in self.nodes:
                old = self.nodes[old_parent]
                if node_id in old.children:
                    old.children.remove(node_id)
            if new_parent and new_parent in self.nodes:
                new = self.nodes[new_parent]
                if node_id not in new.children:
                    new.children.append(node_id)

        self._save()
        return True

    def delete(self, node_id: str, cascade: bool = False) -> bool:
        """
        删除节点。
        cascade=True: 级联删除所有子节点。
        cascade=False: 子节点的 parent 置空。
        """
        node = self.nodes.get(node_id)
        if not node:
            return False

        children = list(node.children)

        if cascade:
            for cid in children:
                self.delete(cid, cascade=True)
        else:
            for cid in children:
                if cid in self.nodes:
                    self.nodes[cid].parent_id = None

        # 从 parent 移除
        if node.parent_id and node.parent_id in self.nodes:
            parent = self.nodes[node.parent_id]
            if node_id in parent.children:
                parent.children.remove(node_id)

        del self.nodes[node_id]
        self._save()
        return True

    def reorder_children(self, parent_id: str, child_ids: list[str]):
        """重新排序子节点。"""
        parent = self.nodes.get(parent_id)
        if not parent:
            return
        valid = [cid for cid in child_ids if cid in self.nodes]
        parent.children = valid
        self._save()

    # ── 统计 ────────────────────────────────────────────

    def stats(self) -> dict:
        """返回统计信息。"""
        nodes = list(self.nodes.values())
        cats: dict[str, int] = {}
        tags: dict[str, int] = {}
        pri: dict[int, int] = {}
        for n in nodes:
            if n.category:
                cats[n.category] = cats.get(n.category, 0) + 1
            for t in n.tags:
                tags[t] = tags.get(t, 0) + 1
            pri[n.priority] = pri.get(n.priority, 0) + 1
        return {
            "node_count": len(nodes),
            "max_depth": self._max_depth(),
            "by_category": dict(sorted(cats.items(), key=lambda x: -x[1])),
            "by_priority": dict(sorted(pri.items())),
            "top_tags": dict(sorted(tags.items(), key=lambda x: -x[1])[:20]),
        }

    def _max_depth(self) -> int:
        """计算树的最大深度。"""
        roots = self.get_roots()

        def depth(node_id, visited=None):
            if visited is None:
                visited = set()
            if node_id in visited:
                return 0
            visited.add(node_id)
            node = self.nodes.get(node_id)
            if not node or not node.children:
                return 1
            return 1 + max(
                (depth(c, visited.copy()) for c in node.children if c in self.nodes),
                default=0,
            )

        return max((depth(r.id) for r in roots), default=0)
