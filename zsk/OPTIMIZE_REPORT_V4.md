# 优化报告：Agent 智能构建模式

## 一、优化背景

| 项目 | 说明 |
|------|------|
| 关联项目 | zsk — Agent 开发技术知识库 |
| 优化日期 | 2026-06-17 |
| 版本 | v1.3 |
| 触发场景 | 在其他电脑上，agent 用规则导入时概念分类不准、合并遗漏；用户需要 agent 用语义理解来做概念提取与合并 |

### 问题根因

`kb.py import` 是基于规则的：正则解析标题 → 关键词映射分类 → 归一化标题匹配合并。这套机制在以下场景失效：

| 场景 | 规则表现 | 期望 |
|------|----------|------|
| 章节标题 "Agent评测维度" | 关键词表无匹配 → 无分类 | 应归入 `evaluation` |
| 章节 "LLM评测方法" vs "Benchmark" | 标题不匹配 → 分成两个节点 | 应合并为同一概念 |
| 跨写法 "Memory System" vs "记忆系统" | 归一化未覆盖英文 | 应识别为同一概念 |

根本原因：**规则无法替代语义理解**。而 agent 本身就是一个 LLM，具备语义理解能力——应该让 agent 来做概念提取与合并。

---

## 二、方案设计

### 2.1 双模架构

```
┌─────────────────────────────────────────────────┐
│                   kb.py                          │
│                                                  │
│  import (规则模式)          build (Agent模式)      │
│  ┌─────────────────┐      ┌─────────────────┐    │
│  │ 正则解析标题      │      │ 输出全量分析报告   │    │
│  │ 关键词映射分类    │      │ ↓ Agent 阅读      │    │
│  │ 归一化标题合并    │      │ 语义理解每个概念   │    │
│  │ 快速、适合初导    │      │ 确定分类/优先级    │    │
│  └─────────────────┘      │ 合并相同概念      │    │
│                            │ 建立父子层级      │    │
│                            │ 准确、适合精建    │    │
│                            └─────────────────┘    │
└─────────────────────────────────────────────────┘
```

- `import` — 保留，适合首次快速导入或简单场景
- `build` — 新增，适合多报告、跨写法的精确构建

### 2.2 build 命令设计

`python3 kb.py build` 不执行任何修改，而是输出一份结构化分析报告，包含四段：

| 段落 | 内容 | 用途 |
|------|------|------|
| 📊 当前 KB 状态 | 每个分类下已有概念列表 | Agent 判断哪些概念已存在 |
| 📂 本体分类体系 | 8 个分类 + 描述 + 二级分类 | Agent 为每个概念选分类 |
| 📄 研报分析 | 每个章节的标题/层级/内容预览/自动分类建议/已存在标记 | Agent 做语义判断的依据 |
| 🤖 操作步骤 | add/edit 命令模板 + 收尾命令 | Agent 执行操作的指令 |

关键技术点：内容预览截断 100 字符，既给 agent 足够上下文又不撑爆 token。

### 2.3 Agent 工作流（zsk-build skill）

```
Step 1: python3 kb.py build
          ↓  获取全量分析报告
Step 2: 阅读每个章节 → 确定分类/优先级/标签/摘要
          ↓  语义判断（超越关键词匹配）
Step 3: python3 kb.py add/edit
          ↓  精确操作知识库
Step 4: reorganize → dedup → export
          ↓  收尾 + 导出 HTML
```

Skill 中包含的**语义合并规则**（Agent 需遵守）：

1. 同概念不同写法 → 合并（"Memory System" ≈ "记忆系统"）
2. 父子关系 → 建立层级（H2→H3→H4 保持）
3. 新子概念 → 创建子节点
4. 内容合并 → 追加，不重复
5. 优先级升级 → 任一报告视为核心则取核心

### 2.4 一键脚本

`build.sh` / `build.command`（macOS 双击）：

```bash
#!/bin/bash
set -e
DIR="$(cd "$(dirname "$0")" && pwd)"
pip3 install markdown -q
python3 "$DIR/kb.py" setup
exec hermes -z "加载 zsk-build skill，然后构建知识库。" --skills zsk-build
```

三步入魂：装依赖 → 注册 skill → 启动 agent 构建。

---

## 三、实现细节

### 3.1 kb.py — cmd_build()

核心函数，约 120 行。关键逻辑：

```python
def cmd_build(kb, args):
    # 1. 输出当前 KB 状态（遍历 kb-root 下 8 个分类节点）
    root = kb.get("kb-root")
    for cid in root.children:
        cat = kb.get(cid)
        concepts = kb.get_children(cid)
        print(f"  [{cat.title}] {len(concepts)} 个概念: ...")

    # 2. 输出本体论
    for cat_id, cat_info in ONTOLOGY.items():
        print(f"  {cat_id:20s} {cat_info['label']}")
        print(f"  {'':20s} {cat_info['description']}")

    # 3. 解析每份研报，输出章节结构 + 内容预览 + 分类建议
    from kb_import import _parse_headings
    for md_file in md_files:
        sections, refs = _parse_headings(md_file.read_text())
        for sec in sections:
            auto_cat = map_section_to_category(sec["title"])
            exists = kb.find_by_title_category(title, auto_cat)
            print(f"{'#' * sec['level']} {title}"
                  f"{' ← 建议分类: ' + cat_label if auto_cat else ''}"
                  f"{' ⚠ 已存在' if exists else ''}")
            print(f"   📝 {content[:100]}…")

    # 4. 输出 Agent 操作指令模板
    print("新增: python3 kb.py add --title ... --category ...")
    print("更新: python3 kb.py edit <id> --content ...")
```

### 3.2 zsk-build skill

存放在 `~/.hermes/skills/note-taking/zsk-build/SKILL.md`。描述以 "Use when" 开头，触发词覆盖中英文：

> "构建知识库", "build the knowledge base", "rebuild kb", "重新构建"

与 `zsk-knowledge-base` 形成关联（`related_skills`），agent 可在两个 skill 间切换。

### 3.3 build.sh

- `set -e` — 任何步骤失败立即停止
- `DIR="$(cd "$(dirname "$0")" && pwd)"` — 无论从哪执行，准确定位项目根
- `exec hermes -z "..." --skills zsk-build` — exec 替换当前进程，不残留 shell

### 3.4 Hermes CLI 集成

验证了 `hermes -z PROMPT` 可用：

```
$ hermes -z "echo test" --skills zsk-build
test
```

`-z` 为 one-shot 模式，`--skills` 预加载 skill。

---

## 四、测试验证

### 4.1 build 命令输出验证

```
$ python3 kb.py build | head -20

📊 当前知识库状态
节点: 28    最大深度: 4
  [架构设计] 4 个概念: 技术演进趋势总结, AI Agent 核心能力要素...
  [工具调用] 1 个概念: 工具调用技术
  ...

📂 本体分类体系（8 个一级分类）
  architecture         架构设计
  evaluation           评估与评测
  ...

📄 研报分析（2 份）
──────────────────────────────────
📄 agent-memory-rag-deep.md
# Agent 记忆与 RAG 深度研究报告
  ## 概述
     📝 本报告深入分析 Agent 记忆系统的实现方案...
  ## 记忆系统  ← 建议分类: 记忆系统 ⚠ 已存在(将合并)
     📝 Agent 记忆系统是 2024-2025 年 Agent 技术栈中...
```

### 4.2 一键脚本语法验证

```
$ bash -n build.sh
语法 OK

$ ls -la build.sh build.command
-rwx--x--x  build.sh
-rwx--x--x  build.command
```

### 4.3 Hermes 集成验证

```
$ hermes -z "echo test" --skills zsk-build
test
```

---

## 五、影响范围

### 修改文件

| 文件 | 改动 | 行数变化 |
|------|------|----------|
| `kb.py` | 新增 `cmd_build` 函数 + subparser + commands 注册 | +125 |
| `zsk-build` skill | 新建 `~/.hermes/skills/note-taking/zsk-build/SKILL.md` | 新增 |
| `build.sh` | 一键构建脚本 | 新增 |
| `build.command` | macOS 双击版本 | 新增（build.sh 副本） |

### CLI 命令清单（当前共 14 个）

| 命令 | 模式 | 用途 |
|------|------|------|
| `list` | 查询 | 列出知识点 |
| `search` | 查询 | 全文搜索 |
| `show` | 查询 | 查看详情 |
| `stats` | 查询 | 统计信息 |
| `add` | 写入 | 手动添加节点 |
| `edit` | 写入 | 编辑节点 |
| `delete` | 写入 | 删除节点 |
| `import` | 规则 | 自动导入 MD 研报 |
| **`build`** | **Agent** | **输出分析供 Agent 智能构建** |
| `export` | 输出 | 导出 HTML 可视化 |
| `setup` | 配置 | 注册 skill 到 Hermes |
| `reorganize` | 维护 | 重建分类树层级 |
| `dedup` | 维护 | 去重合并 |

### 不兼容变更

无。`import` 和 `build` 是两个独立命令，互不影响。

### 项目版本演进

| 版本 | 核心能力 | 关键新增 |
|------|----------|----------|
| v1.0 | MD 解析 + JSON 存储 + HTML 可视化 | kb_core, kb_import, kb_export |
| v1.1 | 合并导入 + 跨机器移植 | merge_node, import_and_merge, setup |
| v1.2 | 分类层级 + 归一化匹配 + 去重 | ensure_category_tree, normalize_title, dedup |
| **v1.3** | **Agent 智能构建 + 一键脚本** | **cmd_build, zsk-build skill, build.sh** |
