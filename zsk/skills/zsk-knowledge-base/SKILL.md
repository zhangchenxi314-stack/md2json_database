---
name: zsk-knowledge-base
description: "Use when the user asks to search, query, build, or manage the Agent 技术知识库 (zsk). ALWAYS use build mode for importing, NEVER use import. The import command is deprecated and blocked in non-interactive mode."
version: 2.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [knowledge-base, ontology, agent-tech, markdown, json]
    related_skills: [zsk-build]
---

# ZSK — Agent 开发技术知识库

## Overview

zsk is a local knowledge base built from Markdown research reports about Agent development technology.
The knowledge tree has 4 levels: master root → 8 category nodes → concepts (H2) → sub-concepts (H3+).

**CRITICAL: For importing reports, ALWAYS use `kb.py build` (intelligent mode). NEVER use `kb.py import` — it is deprecated and blocked.**

## When to Use

- User asks to search: "搜索知识库", "find xxx in kb"
- User wants to build/import: "构建知识库", "导入研报", "build kb"
- User wants stats: "知识库有多少节点"
- User wants HTML: "导出可视化", "open the kb"

## Key Commands

On Windows use `python`, on macOS/Linux use `python3`.

### Search & Info
```bash
python {PROJECT_DIR}/kb.py search "<keyword>"
python {PROJECT_DIR}/kb.py list --category rag
python {PROJECT_DIR}/kb.py show <node_id>
python {PROJECT_DIR}/kb.py stats
```

### Build Knowledge Base (REQUIRED — use this, not import)

**Step 1: Get analysis**
```bash
python {PROJECT_DIR}/kb.py build
```

**Step 2:** Read output. For each section: category, priority, tags, merge-or-new.

**Step 3: Add new concepts**
```bash
python {PROJECT_DIR}/kb.py add --title "概念名" --category tool-calling --priority 2 --abstract "摘要" --content "正文" --tags "tag1,tag2"
```

**Step 4: Merge existing (marked ⚠已存在)**
```bash
python {PROJECT_DIR}/kb.py edit <id> --content "追加内容"
```

**Step 5: Parent-child hierarchy**
```bash
python {PROJECT_DIR}/kb.py edit <child_id> --parent <parent_id>
```

**Step 6: Finalize**
```bash
python {PROJECT_DIR}/kb.py reorganize
python {PROJECT_DIR}/kb.py dedup
python {PROJECT_DIR}/kb.py export
```

### One-click Build
- Windows: double-click `build.bat`
- macOS/Linux: `./build.sh`

## 8 Ontology Categories

| ID | Label |
|----|-------|
| `architecture` | 架构设计 |
| `planning` | 规划与推理 |
| `tool-calling` | 工具调用 |
| `memory` | 记忆系统 |
| `multi-agent` | 多智能体协作 |
| `rag` | RAG 与知识增强 |
| `evaluation` | 评估与评测 |
| `safety` | 安全与对齐 |

## Common Pitfalls

1. **NEVER use `kb.py import`.** Blocked in non-interactive mode. Always use `kb.py build`.
2. **Windows: `python`, macOS/Linux: `python3`.**
3. **Missing `markdown`:** `pip install markdown`.
4. **Flat tree:** `kb.py reorganize`.
5. **Duplicates:** `kb.py dedup`.
6. **Semantic judgment over keyword hints.** "评测方法" → `evaluation` even if auto-suggest says otherwise.
