# 开发报告：MD 研报 → JSON 知识库

## 一、项目信息

| 项目 | 说明 |
|------|------|
| 项目名称 | zsk — Agent 开发技术知识库 |
| 项目路径 | `/Users/zcx/project/zsk/` |
| 开发日期 | 2026-06-16 |
| Python 版本 | 3.9+ |
| 外部依赖 | 仅 `markdown` 一个（纯 Python，无 C 扩展） |

---

## 二、需求回顾

将已有的 Agent 开发技术 Markdown 研报，按本体论（Ontology）构建为本地 JSON 知识库。核心要求：

1. MD 研报 → 结构化 JSON 知识节点
2. 按本体论分类（8 个一级分类）
3. 人和 AI 都能查询、维护、调用
4. 可导出为 HTML 可视化页面（可展开树、优先级色标）
5. 依赖最少化

### 研报结构（用户提供）

研报为涉密内容，不可直接查看。已知章节结构为：

> 概述 → AI Agent 核心能力要素 → 主流开发框架对比 → 工具调用技术 → RAG 检索增强生成 → 记忆系统 → 基础设施演进 → 技术演进趋势总结 → 参考文献

### 需求对齐确认

| 问题 | 决策 |
|------|------|
| 本体分类 | 使用预设的 8 个一级分类 |
| 研报查看 | 不可查看实际研报，按章节结构映射 |
| 导入策略 | 混合模式（自动提取 + 手动标注支持） |
| 跨树关系 | 不需要，保持纯树结构 |
| Markdown 渲染 | 需要完整渲染（代码高亮、表格） |
| 优先级定义 | P1~P5 含义确认 |

---

## 三、系统架构

### 3.1 架构图

```
┌─────────────────────────────────────────────────────┐
│                     kb.py (CLI)                      │
│  list | search | show | stats | add | edit | delete  │
│              import | export                         │
├──────────┬──────────┬──────────┬────────────────────┤
│ kb_core  │kb_import │kb_export │  kb_ontology        │
│ 数据模型  │ MD 解析   │ HTML 生成 │  分类/标签/优先级    │
│ CRUD     │ 节点提取   │ 可视化    │  章节映射           │
├──────────┴──────────┴──────────┴────────────────────┤
│              data/knowledge_base.json                │
│              output/knowledge_base.html              │
└─────────────────────────────────────────────────────┘
```

### 3.2 模块职责

| 模块 | 职责 | 行数 |
|------|------|------|
| `kb_ontology.py` | 8 分类定义、优先级配置、标签规范、章节→分类映射 | ~180 |
| `kb_core.py` | KnowledgeNode 数据类、KnowledgeBase CRUD 管理器 | ~260 |
| `kb_import.py` | MD 解析（代码块安全）、自动分类/优先级/标签、混合模式 | ~410 |
| `kb_export.py` | 单文件 HTML 生成（CSS + vanilla JS，零外部 JS 依赖） | ~370 |
| `kb.py` | argparse CLI 入口，11 个子命令 | ~310 |
| **总计** | | **~1530** |

---

## 四、数据模型设计

### 4.1 JSON Schema

每个知识点是一个 KnowledgeNode：

```json
{
  "id": "memory-记忆系统",
  "title": "记忆系统",
  "abstract": "Agent的记忆系统决定了其持续对话和个性化能力。",
  "content": "## 短期记忆\n\n短期记忆即对话上下文窗口...",
  "priority": 2,
  "tags": [],
  "category": "memory",
  "l2_category": "",
  "source_file": "agent-tech-2024.md",
  "source_section": "记忆系统",
  "parent_id": "ai-agent-技术研报-2024年核心能力与框架演进",
  "children": ["短期记忆", "长期记忆", "记忆整合策略"],
  "references": ["[1] Lewis et al., RAG, NeurIPS 2020"],
  "created_at": "2026-06-16T09:40:53Z",
  "updated_at": "2026-06-16T09:40:53Z"
}
```

### 4.2 本体分类体系（8 个一级分类）

| ID | 标签 | 二级分类数 |
|----|------|-----------|
| `architecture` | 架构设计 | 6（单Agent、多Agent、混合、框架对比、核心能力、基础设施） |
| `planning` | 规划与推理 | 6（ReAct、Plan-Execute、ToT、CoT、反思、路由） |
| `tool-calling` | 工具调用 | 5（Function Calling、MCP、工具选择、编排、API集成） |
| `memory` | 记忆系统 | 5（短期、长期、向量检索、上下文窗口、记忆整合） |
| `multi-agent` | 多智能体协作 | 5（角色分工、通信、任务编排、辩论、群体智能） |
| `rag` | RAG 与知识增强 | 6（检索策略、分块、重排序、嵌入、索引、混合检索） |
| `evaluation` | 评估与评测 | 5（Benchmark、人工评估、LLM-as-Judge、度量、安全评估） |
| `safety` | 安全与对齐 | 5（护栏、RLHF/DPO、红队测试、提示注入、内容过滤） |

### 4.3 优先级体系

| 级别 | 标签 | 颜色 | 含义 |
|------|------|------|------|
| P1 | 核心基础 | #d32f2f 红 | 必须掌握 |
| P2 | 重要常用 | #f57c00 橙 | 日常开发常用 |
| P3 | 一般了解 | #fbc02d 黄 | 建议了解 |
| P4 | 进阶深入 | #1976d2 蓝 | 深入探索 |
| P5 | 扩展选读 | #757575 灰 | 按需查阅 |

---

## 五、关键实现细节

### 5.1 MD 解析：代码块安全处理

**问题**：代码块内的 `#` 注释会被误识别为 Markdown 标题，破坏树结构。

**解决**：在标题正则匹配之前，先检测代码围栏（`` ``` `` 和 `~~~`），进入代码块后跳过标题检测，退出代码块后恢复。

```python
fence_re = re.compile(r"^(`{3,}|~{3,})")
in_fence = False

for line in lines:
    # 先检测围栏
    if fence_re.match(line):
        in_fence = not in_fence
        continue
    # 代码块内跳过标题检测
    if in_fence:
        continue
    # 正常标题检测
    if heading_re.match(line):
        ...
```

### 5.2 分类继承

**问题**：H2 章节（如"记忆系统"）通过章节标题映射到 `memory` 分类，但其 H3 子章节（如"短期记忆"）无法通过标题匹配到分类，导致 `category` 为空。

**解决**：在父子关系建立后，遍历所有节点——若节点自身无分类但父节点有，自动继承父节点分类。

```python
for node in nodes:
    if not node.category and node.parent_id:
        parent = next((n for n in nodes if n.id == node.parent_id), None)
        if parent and parent.category:
            node.category = parent.category
```

### 5.3 混合导入模式

支持三种粒度的导入控制：

| 模式 | 命令 | 说明 |
|------|------|------|
| 直接导入 | `python3 kb.py import report.md` | 全自动，立即写入 |
| 试运行 | `python3 kb.py import report.md --dry-run` | 预览提取结果，不写入 |
| 交互式 | `python3 kb.py import report.md -i` | 逐条确认，选择性导入 |

手动标注语法（嵌入 MD 中）：

```markdown
<!-- kb: priority=1 tags=react,planning category=planning -->
```

支持的标注字段：`priority`, `tags`, `category`, `l2_category`, `parent_id`, `abstract`, `id`。

### 5.4 HTML 可视化

单文件自包含设计：

- **零外部 JS/CSS 依赖**：所有样式和逻辑内嵌
- **JSON 数据内嵌**：`<script>const DATA = {...}</script>`，离线可用
- **vanilla JS**：树渲染、搜索过滤、展开折叠、详情展示全用原生 JS
- **Markdown 渲染**：Python 侧用 `markdown` 库预渲染为 HTML，嵌入页面
- **响应式**：移动端自动切换为上下布局

核心交互：

```
左侧树                    右侧详情
┌──────────────┐         ┌──────────────────────┐
│ 📂 知识树      │         │ 📌 记忆系统             │
│              │         │ ⭐⭐ P2 重要常用         │
│ ▶ 架构设计     │         │ [记忆系统]              │
│ ▼ 工具调用     │ 点击 →  │                        │
│   ● Function  │         │ Agent的记忆系统决定了... │
│   ● MCP 协议   │         │                        │
│   ● 工具选择   │         │ ## 短期记忆             │
│ ▶ RAG        │         │ 短期记忆即对话上下文...    │
│ ▼ 记忆系统     │         │                        │
│   ● 短期记忆   │         │ 📚 参考文献              │
│   ● 长期记忆   │         │ [1] Lewis et al. ...   │
└──────────────┘         └──────────────────────┘
```

---

## 六、测试验证

使用模拟研报 `reports/agent-tech-2024.md`（模拟用户研报结构）进行端到端测试。

### 6.1 导入结果

```
📄 agent-tech-2024.md: 已导入 20 个知识点

  分类分布:
    架构设计           7  ███████
    工具调用           4  ████
    记忆系统           4  ████
    RAG 与知识增强      3  ███

  优先级分布:
    P1 核心基础       6
    P2 重要常用       9
    P3 一般了解       5

  树深度: 3 层
```

### 6.2 树结构验证

```
AI Agent 技术研报 (H1)
├── 概述 (H2)
├── AI Agent 核心能力要素 [架构设计] (H2)
│   ├── 感知与理解 [架构设计] (H3)        ← 分类继承生效
│   ├── 规划与决策 [架构设计] (H3)
│   └── 工具使用 [架构设计] (H3)
├── 主流开发框架对比 [架构设计] (H2)
├── 工具调用技术 [工具调用] (H2)
│   ├── Function Calling 基础 [工具调用] (H3)
│   ├── MCP 协议 [工具调用] (H3)
│   └── 工具选择策略 [工具调用] (H3)
├── RAG 检索增强生成 [RAG] (H2)
│   ├── 分块策略 [RAG] (H3)
│   └── 检索与重排序 [RAG] (H3)
├── 记忆系统 [记忆系统] (H2)
│   ├── 短期记忆 [记忆系统] (H3)
│   ├── 长期记忆 [记忆系统] (H3)
│   └── 记忆整合策略 [记忆系统] (H3)
├── 基础设施演进 [架构设计] (H2)
└── 技术演进趋势总结 [架构设计] (H2)
```

✅ 所有节点正确归类  
✅ 父子关系正确  
✅ 分类继承生效  
✅ 参考文献章节正确排除  
✅ 代码块内注释未被误解析  

### 6.3 CLI 功能验证

| 命令 | 结果 |
|------|------|
| `python3 kb.py list` | ✅ 列出 20 个节点 |
| `python3 kb.py list --category memory` | ✅ 筛选 4 个节点 |
| `python3 kb.py search "ReAct"` | ✅ 命中"规划与决策" |
| `python3 kb.py show memory-记忆系统` | ✅ 完整展示详情 |
| `python3 kb.py stats` | ✅ 统计面板正确 |
| `python3 kb.py export` | ✅ HTML 生成成功 |

---

## 七、使用指南

### 7.1 首次使用

```bash
cd /Users/zcx/project/zsk

# 1. 安装唯一依赖
pip3 install markdown

# 2. 放入研报到 reports/ 目录
cp /path/to/your/report.md reports/

# 3. 试运行导入（先看效果）
python3 kb.py import reports/ --dry-run

# 4. 确认后正式导入
python3 kb.py import reports/

# 5. 查看统计
python3 kb.py stats

# 6. 导出可视化
python3 kb.py export

# 7. 在浏览器中打开
open output/knowledge_base.html
```

### 7.2 日常维护

```bash
# 搜索
python3 kb.py search "MCP"

# 手动添加节点
python3 kb.py add --title "新知识点" --category tool-calling --priority 2

# 编辑节点
python3 kb.py edit <id> --priority 1 --tags "mcp,anthropic"

# 删除节点（级联删除子节点）
python3 kb.py delete <id> --cascade

# 重新导出 HTML
python3 kb.py export
```

### 7.3 手动标注增强

在 MD 研报中插入标注以覆盖自动识别：

```markdown
## 我的自定义章节

<!-- kb: priority=1 tags=mcp,function-calling category=tool-calling l2=mcp -->

这里的内容不会被自动分类影响，将使用手动指定的分类和优先级。
```

---

## 八、待优化项

| 项 | 优先级 | 说明 |
|----|--------|------|
| 标签自动提取增强 | P2 | 当前基于关键词匹配，可扩展为 TF-IDF 或 LLM 辅助提取 |
| 跨文件去重 | P2 | 多次导入同名文件时自动去重（或提示覆盖） |
| JSON 增量更新 | P3 | 当前是全量读写，大数据量时考虑增量写入 |
| 全文搜索索引 | P3 | 当前为 O(n) 遍历，大数据量时可加倒排索引 |
| 导出为 Markdown | P3 | 支持将知识库反导出为结构化 MD 文档 |
| Web 服务模式 | P4 | `python3 kb.py serve` 启动本地 Web 服务器 |

---

## 九、附录

### A. 文件清单

```
/Users/zcx/project/zsk/
├── kb.py
├── kb_core.py
├── kb_ontology.py
├── kb_import.py
├── kb_export.py
├── REQUIREMENTS.md
├── DEV_REPORT.md              ← 本报告
├── data/
│   └── knowledge_base.json
├── reports/
│   └── agent-tech-2024.md
└── output/
    └── knowledge_base.html
```

### B. 依赖清单

```
Python 3.9+ 标准库:
  json, uuid, re, argparse, datetime, pathlib, hashlib, dataclasses

唯一外部依赖:
  markdown (纯 Python, pip install markdown)
```
