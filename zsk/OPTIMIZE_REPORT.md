# 优化报告：多报告合并导入

## 一、优化背景

| 项目 | 说明 |
|------|------|
| 关联项目 | zsk — Agent 开发技术知识库 |
| 优化日期 | 2026-06-16 |
| 触发场景 | 在 `reports/` 放入多份相关研报后，HTML 和 JSON 按每份报告独立罗列，无法按概念统一展开 |

### 问题描述

知识库中已有多份 Agent 技术研报，它们的章节高度重叠。例如：

- 报告 A 有「记忆系统」章节（含短期记忆、长期记忆、记忆整合策略）
- 报告 B 也有「记忆系统」章节（含短期记忆、长期记忆、记忆整合策略 + 新内容）

旧版导入行为：每份报告独立成树，产生两棵并行的「记忆系统」子树。用户期望的是**按概念逐级展开**——两棵「记忆系统」合并为一棵，子节点去重聚合，内容叠加。

```
旧行为（独立模式）:              新行为（合并模式）:
                                
报告 A                          记忆系统（根节点）
├── 记忆系统                    ├── 短期记忆  ← A+B 合并
│   ├── 短期记忆                ├── 长期记忆  ← A+B 合并
│   ├── 长期记忆                └── 记忆整合策略 ← A+B 合并
│   └── 记忆整合策略            
                                RAG 检索增强生成（根节点）
报告 B                          ├── 分块策略    ← A+B 合并
├── 记忆系统                    ├── 检索与重排序 ← 来自 A
│   ├── 短期记忆                └── 检索策略    ← 来自 B，新增
│   ├── 长期记忆                
│   └── 记忆整合策略            
```

---

## 二、方案设计

### 2.1 核心思路

导入新研报时，对每个提取的知识节点执行**匹配 → 合并或新增**：

1. 按 `category + title` 在已有知识库中查找同概念节点
2. 找到 → 合并内容/标签/优先级/子节点/来源
3. 未找到 → 作为新节点加入
4. 报告标题（H1）和通用章节（如"概述"）→ 跳过

### 2.2 合并策略细则

| 字段 | 合并规则 |
|------|----------|
| `content` | 追加（`\n\n---\n\n` 分隔），不重复追加 |
| `abstract` | 新内容优先覆盖空摘要 |
| `priority` | 取数值更小（优先级更高）的一方 |
| `tags` | 并集去重 |
| `source_file` | 拼接（逗号分隔），不重复 |
| `children` | 并集去重 |
| `references` | 并集去重 |
| `l2_category` | 原来为空时用新的填充 |
| `updated_at` | 更新为当前时间 |

### 2.3 跳过规则

| 条件 | 原因 |
|------|------|
| H1 + 无分类 + 有子节点 | 报告标题，不是概念 |
| 无分类 + 无子节点 | 通用章节（如"概述"），不同报告含义不同不宜合并 |

---

## 三、实现细节

### 3.1 kb_core.py — 查找与合并

新增两个方法到 `KnowledgeBase` 类：

```python
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
        # ... 逐字段合并（content, abstract, priority, tags, source_file, children, references, l2_category）
        return existing.id
    else:
        # 新增
        self.nodes[incoming.id] = incoming
        return incoming.id
```

### 3.2 kb_import.py — 合并导入函数

新增三个函数：

**`import_and_merge(kb, filepath)`** — 核心函数：

1. 解析 MD → 提取节点（复用 `import_md`）
2. 对节点做拓扑排序（父节点先于子节点处理）
3. 遍历节点：
   - 跳过 H1 和无分类叶子节点
   - 重映射 `parent_id`（若父节点被跳过或合并到已有节点）
   - 调用 `kb.merge_node()` 执行合并或新增
4. 返回统计 `{"merged": N, "new": N, "skipped": N}`

**`import_directory_merge(kb, dirpath)`** — 批量合并，逐文件调用 `import_and_merge`。

**`_topo_sort(nodes)`** — 按节点深度排序，确保父节点总是先于子节点处理。这是因为合并时子节点的 `parent_id` 需要重映射到父节点合并后的真实 ID。

### 3.3 kb.py — CLI 改动

- 导入命令**默认走合并模式**
- `--dry-run` 预览时显示每节点的处理动作：`合并` / `新增` / `跳过`
- `--no-merge` 切回旧版独立模式
- `--interactive`（-i）也适配了合并模式

关键代码段：

```python
# 导入默认合并
if filepath.is_dir():
    stats = import_directory_merge(kb, filepath)
else:
    stats = import_and_merge(kb, filepath)
    print(f"合并 {stats['merged']}, 新增 {stats['new']}, 跳过 {stats['skipped']}")
```

---

## 四、测试验证

### 4.1 测试数据

| 报告 | 节点数 | 内容 |
|------|--------|------|
| `agent-tech-2024.md` | 20 | 架构、工具调用、RAG、记忆系统等 |
| `agent-memory-rag-deep.md` | 13 | 记忆系统深入、RAG 深入、工具调用补充 |

两份报告在以下概念上重叠：记忆系统、短期记忆、长期记忆、记忆整合策略、RAG 检索增强生成、分块策略、工具调用技术、Function Calling 基础、工具选择策略、技术演进趋势总结。

### 4.2 测试结果

```
第一份导入:
  合并 0, 新增 18, 跳过 2

第二份 dry-run:
  合并 10, 新增 1, 跳过 2    ← 预览标签正确

第二份正式导入:
  合并 10, 新增 1, 跳过 2

最终知识库:
  节点总数: 19
  最大深度: 2
  分类分布:
    架构设计           7
    工具调用           4
    RAG 与知识增强      4
    记忆系统           4
```

### 4.3 合并效果验证

```
$ python3 kb.py show rag-rag-检索增强生成

来源:     agent-tech-2024.md, agent-memory-rag-deep.md  ← 两份报告
子节点:   分块策略, 检索与重排序, 检索策略              ← 去重聚合

$ python3 kb.py show memory-记忆系统

来源:     agent-tech-2024.md, agent-memory-rag-deep.md  ← 两份报告
子节点:   短期记忆, 长期记忆, 记忆整合策略               ← 不重复
```

### 4.4 功能兼容性

| 命令 | 结果 |
|------|------|
| `python3 kb.py import report.md` | ✅ 默认合并 |
| `python3 kb.py import report.md --no-merge` | ✅ 独立模式可用 |
| `python3 kb.py import report.md --dry-run` | ✅ 预览标注 合并/新增/跳过 |
| `python3 kb.py import report.md -i` | ✅ 交互式合并可用 |
| `python3 kb.py search "检索策略"` | ✅ 可搜索到新增节点 |
| `python3 kb.py export` | ✅ HTML 正确渲染合并后的树 |

---

## 五、影响范围

### 修改的文件

| 文件 | 改动 | 行数变化 |
|------|------|----------|
| `kb_core.py` | 新增 `find_by_title_category` + `merge_node` | +59 |
| `kb_import.py` | 新增 `import_and_merge` + `import_directory_merge` + `_topo_sort` | +106 |
| `kb.py` | `cmd_import` 重写为合并模式，`_interactive_import` 适配合并 | +54 |
| `DEV_REPORT.md` | 新增 5.5 节、更新模块表/测试表 | +60 |
| `zsk-knowledge-base` skill | 更新导入说明 | 无行数变化 |

### 不兼容变更

无。旧版独立模式通过 `--no-merge` 保留。

---

## 六、附录：合并前后对比

### 独立模式（--no-merge）

```
两份报告 → 两棵独立树 → 37 个节点
概念分散，重复严重
```

### 合并模式（默认）

```
两份报告 → 一棵统一树 → 19 个节点
概念聚合，逐级展开
```

**空间节省：49%**（37 → 19），且随着报告增多，节省比例会更高——新增报告的增量仅为真正新概念的节点数，而非全部章节数。
