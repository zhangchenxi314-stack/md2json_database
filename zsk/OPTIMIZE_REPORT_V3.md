# 优化报告：标题归一化合并、空摘要填充、去重命令

## 一、优化背景

| 项目 | 说明 |
|------|------|
| 关联项目 | zsk — Agent 开发技术知识库 |
| 优化日期 | 2026-06-16 |
| 版本 | v1.2 |
| 触发场景 | 其他电脑上的多份研报导入后，因标题写法差异导致概念未合并；部分节点展开简介空白 |

### 问题详述

**问题 1 — 概念未合并到主干**

不同研报中描述同一概念的章节标题写法不一致，如：
- 报告 A：`## 工具调用技术`
- 报告 B：`## AI Agent 工具调用`
- 报告 C：`## Agent 工具调用技术`

旧版合并逻辑要求标题**完全一致**才能匹配，导致这些本质上相同的概念被创建为多个独立节点，树结构杂乱。

**问题 2 — 部分节点展开简介空白**

导入的研报章节正文丰富，但提取时未生成摘要（`abstract` 为空）。在 HTML 详情面板中，摘要区域显示为空，用户感知为"空白简介"。

---

## 二、方案设计

### 2.1 标题归一化

新增 `normalize_title()` 函数，对标题做标准化处理后再比较：

| 处理步骤 | 示例 |
|----------|------|
| 原始标题 | `AI Agent 工具调用技术` |
| → 小写 | `ai agent 工具调用技术` |
| → 去标点 | `ai agent 工具调用技术` |
| → 去空格 | `aiagent工具调用技术` |
| → 循环剥前缀 | `工具调用技术` |

前缀剥离循环处理（处理多前缀叠加）：
```
"aiagent工具调用技术" → 匹配 "aiagent" → "工具调用技术" → 无更多前缀 → 停止
"ai工具调用技术" → 匹配 "ai" → "工具调用技术"
```

6 组测试用例全部通过：

| 标题 A | 标题 B | 匹配 |
|--------|--------|:--:|
| Agent 记忆系统 | 记忆系统 | ✓ |
| AI Agent 工具调用 | 工具调用 | ✓ |
| RAG 检索增强生成 | rag检索增强生成 | ✓ |
| 记忆系统 | 记忆系统 | ✓ |
| Agent RAG 技术 | rag技术 | ✓ |
| AI Agent 工具调用技术 | 工具调用技术 | ✓ |

### 2.2 合并匹配升级

`find_by_title_category()` 改为归一化比较：

```python
# 旧：严格相等
if node.title.strip().lower() == title_lower and node.category == category:
    return node

# 新：归一化匹配
norm = normalize_title(title)
for node in self.nodes.values():
    if normalize_title(node.title) == norm and node.category == category:
        return node
```

### 2.3 空摘要填充

双层兜底：

| 层 | 位置 | 机制 |
|----|------|------|
| 数据层 | `KnowledgeBase.fill_empty_abstracts()` | 遍历所有节点，对 `abstract` 为空但 `content` 有内容的，取正文首段有效文本（跳过标题行、代码块、表格）作为摘要，截断 150 字符 |
| 导出版 | `kb_export._extract_first_sentence()` | HTML 构建节点时，若 `abstract` 为空，从 `content` 实时提取首句作为摘要 |

### 2.4 去重命令

新增 `KnowledgeBase.dedup_pass()` 方法，对归一化标题相同的节点执行事后合并（适用于已有 KB 中因历史原因残留的重复节点）。

合并逻辑与 `merge_node` 一致：正文追加、标签取并、优先级取最高、子节点转移、来源文件拼接。合并后删除重复节点并重建分类树。

---

## 三、实现细节

### 3.1 kb_core.py

**`normalize_title(title)`** — 模块级函数，18 行：

```python
def normalize_title(title: str) -> str:
    t = title.strip().lower()
    t = re.sub(r"[：:：（）()【】「」\"\"'']", "", t)
    t = re.sub(r"\s+", "", t)
    prefixes = ["agent", "aiagent", "ai"]
    changed = True
    while changed:
        changed = False
        for prefix in prefixes:
            if t.startswith(prefix) and len(t) > len(prefix):
                t = t[len(prefix):]
                changed = True
                break
    return t
```

**`fill_empty_abstracts()`** — 遍历节点，取正文首段有效文本填充空摘要。

**`dedup_pass()`** — 按 `category + normalize_title` 分组，对每组内 2+ 节点执行合并。

### 3.2 kb_export.py

**`_extract_first_sentence()`** — 从 Markdown 正文中提取第一句有意义的文本（跳过标题、代码块、表格，清除 Markdown 标记）。

**`_node_to_tree_item()`** — `abstract` 字段改用 `node.abstract or _extract_first_sentence(node.content)`。

### 3.3 kb.py & kb_import.py

- **`dedup` 命令**：`cmd_dedup` 依次调用 `fill_empty_abstracts → dedup_pass → ensure_category_tree`，输出统计信息
- **导入流程自动化**：所有导入路径（合并/独立/交互式/批量）末尾统一追加 `fill_empty_abstracts + dedup_pass` 调用

---

## 四、测试验证

### 4.1 归一化验证

```
$ python3 -c "from kb_core import normalize_title; ..."

✓ "Agent 记忆系统" ↔ "记忆系统"
✓ "AI Agent 工具调用" ↔ "工具调用"
✓ "RAG 检索增强生成" ↔ "rag检索增强生成"
✓ "记忆系统" ↔ "记忆系统"
✓ "Agent  RAG 技术" ↔ "rag技术"
✓ "AI Agent 工具调用技术" ↔ "工具调用技术"
```

### 4.2 导入+去重全流程

```
$ rm -f data/knowledge_base.json
$ python3 kb.py import reports/
$ python3 kb.py dedup

📄 agent-memory-rag-deep.md: 合并 0, 新增 11, 跳过 2
📄 agent-tech-2024.md:    合并 10, 新增 8, 跳过 2
✅ 未发现重复节点      ← 两份测试报告无重复标题，通过
```

### 4.3 CLI 命令清单

| 命令 | 功能 |
|------|------|
| `python3 kb.py import report.md` | 导入（自动合并+归类+补摘要+去重） |
| `python3 kb.py dedup` | 手动去重 + 补摘要 |
| `python3 kb.py reorganize` | 手动重建分类树 |
| `python3 kb.py export` | 导出 HTML |

---

## 五、影响范围

### 修改文件

| 文件 | 改动 | 行数变化 |
|------|------|----------|
| `kb_core.py` | 新增 `normalize_title` + `fill_empty_abstracts` + `dedup_pass`；`find_by_title_category` 改用归一化匹配 | +100 |
| `kb_export.py` | 新增 `_extract_first_sentence`；`_node_to_tree_item` 兜底摘要 | +17 |
| `kb_import.py` | 两处合并函数末尾追加 `fill_empty_abstracts + dedup_pass` | +4 |
| `kb.py` | 新增 `dedup` 命令 + 三条导入路径自动调用 | +20 |
| **总计** | | **+141** |

### 不兼容变更

无。归一化匹配向后兼容——原已匹配的标题归一化后仍然匹配。`dedup` 为新增命令，不影响已有流程。

### 项目总览

| 指标 | v1.0 | v1.2（当前） |
|------|------|-------------|
| 总行数 | 1530 | ~2350 |
| 外部依赖 | 1（markdown） | 1 |
| CLI 命令 | 11 | 13（+dedup +reorganize） |
| 导入自动步骤 | 3 | 5（+补摘要 +去重） |
