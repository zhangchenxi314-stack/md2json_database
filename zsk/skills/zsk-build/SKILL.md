---
name: zsk-build
description: "Use when the user asks to build/rebuild the Agent 技术知识库 from reports. Intelligent build mode — read reports with LLM understanding and map concepts to ontology, instead of rule-based import."
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [knowledge-base, ontology, agent-tech, build, semantic]
    related_skills: [zsk-knowledge-base]
---

# ZSK Intelligent Build

## Overview

`kb.py build` outputs a structured analysis of all MD reports + current KB state + ontology. As the agent, use your LLM understanding to read each section, determine its proper category/priority/tags, check for semantic overlap with existing concepts, and build the KB with precise `add`/`edit` commands.

This is fundamentally different from `kb.py import` — that uses regex and keyword matching. You use semantic understanding.

## When to Use

- User says: "构建知识库", "build kb", "rebuild", "重新构建", "导入研报"
- New reports added to `reports/`
- Existing KB has gaps or misclassified concepts
- User wants the most accurate knowledge tree

## Workflow

### Step 1: Run analysis

```bash
python {PROJECT_DIR}/kb.py build
```

Output: current KB state → ontology → per-report section analysis → agent instructions.

### Step 2: Plan concept map

Read EVERY section. For each:

1. **Category** — auto-suggest (`← 建议分类:`) is a HINT only. Use semantic judgment. "评测方法" → `evaluation`.
2. **Exists?** — `⚠ 已存在` means rough match found. Use `edit` to merge.
3. **Priority:** P1=core, P2=important, P3=general, P4=advanced, P5=optional.
4. **Tags:** 2-5 keywords.
5. **Abstract:** one sentence.

### Step 3: Execute

```bash
# New concept
python {PROJECT_DIR}/kb.py add --title "X" --category Y --priority Z --abstract "..." --content "..." --tags "a,b"

# Merge existing
python {PROJECT_DIR}/kb.py edit <id> --content "appended text"

# Set parent
python {PROJECT_DIR}/kb.py edit <child_id> --parent <parent_id>
```

### Step 4: Finalize

```bash
python {PROJECT_DIR}/kb.py reorganize
python {PROJECT_DIR}/kb.py dedup
python {PROJECT_DIR}/kb.py export
```

## Semantic Merging Rules

1. **Same concept, different names**: "Agent记忆系统" = "记忆系统" = "Memory System". Merge.
2. **Parent-child**: If report A has H2 "工具调用" and report B has H3 "Function Calling" under it, make child.
3. **New sub-concepts**: Create as children of existing parent concepts.
4. **Append, don't duplicate**: Merge content with `---` separator.
5. **Priority escalation**: If any report says P1, merged node is P1.

## Handling Non-Standard Reports

If reports lack heading structure (plain text, no H1/H2/H3), read the ENTIRE content and extract concepts semantically. Group related paragraphs into concepts, then map to ontology categories.
