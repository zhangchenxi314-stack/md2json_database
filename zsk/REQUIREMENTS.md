# 需求分析报告：MD 研报 → JSON 知识库

## 一、项目定位

将已有的 Agent 开发技术 Markdown 研报，按本体论（Ontology）构建为本地 JSON 知识库。人可读、AI 可调、可查询、可维护、可可视化。

---

## 二、核心需求拆解

### 2.1 输入：MD 研报

- 数量：已有的多篇 Markdown 研究报告
- 主题域：Agent 开发相关技术（架构、规划、工具调用、记忆、多智能体、评估、安全对齐、RAG 等）
- 结构：假定每篇研报有标题层级（H1~H6），内容包含文本、代码块、表格等

### 2.2 本体论建模

按领域本体将知识组织为树状/图状结构，核心概念：

```
Agent 开发技术（根）
├── 架构设计
│   ├── 单 Agent 架构
│   ├── 多 Agent 架构
│   └── 混合架构
├── 规划与推理
│   ├── ReAct
│   ├── Plan-and-Execute
│   └── Tree-of-Thought
├── 工具调用
│   ├── Function Calling
│   ├── MCP 协议
│   └── 工具选择策略
├── 记忆系统
│   ├── 短期记忆
│   ├── 长期记忆
│   └── 向量检索
├── 多智能体协作
│   ├── 角色分工
│   ├── 消息传递
│   └── 任务编排
├── 评估与评测
│   ├── Benchmark
│   ├── 人工评估
│   └── LLM-as-Judge
├── RAG 与知识增强
│   ├── 检索策略
│   ├── 分块策略
│   └── 重排序
└── 安全与对齐
    ├── 护栏机制
    ├── RLHF/DPO
    └── 红队测试
```

### 2.3 JSON 数据模型设计

每个知识点为一个 Node：

```json
{
  "id": "uuid",
  "title": "ReAct 推理范式",
  "abstract": "ReAct 将推理与行动交替进行...",
  "content": "完整的知识点正文（Markdown）",
  "priority": 3,
  "tags": ["planning", "reasoning", "react"],
  "source_file": "研报-推理框架.md",
  "parent_id": "planning-reasoning",
  "children": ["react-loop", "react-tool-use"],
  "relations": [
    {"target": "tool-calling", "type": "depends_on"},
    {"target": "plan-and-execute", "type": "compared_with"}
  ],
  "created_at": "2026-06-16T00:00:00Z",
  "updated_at": "2026-06-16T00:00:00Z"
}
```

字段说明：

| 字段 | 类型 | 说明 |
|------|------|------|
| id | string | 唯一标识（UUID 或语义路径） |
| title | string | 知识点标题 |
| abstract | string | 一句话摘要（AI 检索用） |
| content | string | 完整正文（Markdown） |
| priority | int 1-5 | 优先级：1=基础必知，5=高级选读 |
| tags | string[] | 标签数组，支持多维度检索 |
| source_file | string | 来源研报文件名（溯源） |
| parent_id | string\|null | 父节点 ID（树结构） |
| children | string[] | 子节点 ID 列表（冗余但便于遍历） |
| relations | object[] | 跨树关系（依赖、对比、引用等） |
| created_at | ISO8601 | 创建时间 |
| updated_at | ISO8601 | 更新时间 |

### 2.4 可视化（HTML）

单文件 HTML，零依赖（纯 HTML + CSS + vanilla JS），具备：

- **树状展开/折叠**：点击节点展开子节点
- **优先级色标**：
  - 红色边框/标记 = P1 核心必读
  - 橙色 = P2 重要
  - 黄色 = P3 一般
  - 蓝色 = P4 进阶
  - 灰色 = P5 选读
- **搜索/过滤**：顶部搜索框，按标题/tag/content 实时过滤
- **节点详情面板**：点击节点显示完整 content（Markdown 渲染为 HTML）
- **统计概览**：顶部展示节点总数、优先级分布、标签云
- **导出功能**：JSON 数据嵌入 HTML（单文件即可离线使用）

### 2.5 查询与维护

**人工操作**（CLI 工具）：
- `python kb.py list` — 列出所有知识点
- `python kb.py search <keyword>` — 全文搜索
- `python kb.py show <id>` — 查看详情
- `python kb.py add --title ... --parent ...` — 手动添加
- `python kb.py edit <id>` — 编辑
- `python kb.py delete <id>` — 删除
- `python kb.py import <md_file>` — 从 MD 导入
- `python kb.py export --html` — 导出可视化
- `python kb.py stats` — 统计信息

**AI 调用**：
- JSON 文件可直接读取、grep、Python json 库加载
- 结构化字段（tags、relations）便于语义查询
- 可作为 RAG 的 knowledge source

---

## 三、技术方案

### 3.1 依赖分析（最小化原则）

| 依赖 | 用途 | 是否必需 |
|------|------|----------|
| Python 3.10+ | 运行环境 | ✅ 系统自带 |
| `json` | JSON 读写 | ✅ 标准库 |
| `uuid` | ID 生成 | ✅ 标准库 |
| `argparse` | CLI | ✅ 标准库 |
| `re` | Markdown 解析 | ✅ 标准库 |
| `datetime` | 时间戳 | ✅ 标准库 |
| `pathlib` | 文件操作 | ✅ 标准库 |
| `markdown` (可选) | HTML 渲染 | ⚠️ 可用正则替代 |

**结论：零外部依赖也可实现，核心功能全靠 Python 标准库。** 如果希望 HTML 可视化的 Markdown 渲染更好，可选装 `markdown` 库（纯 Python，无 C 扩展）。

### 3.2 项目结构

```
zsk/
├── kb.py                  # 主 CLI 入口
├── kb_core.py             # 核心数据模型 + CRUD
├── kb_import.py           # MD 研报 → 知识节点提取
├── kb_export.py           # JSON → HTML 可视化
├── kb_ontology.py         # 本体论定义（分类体系）
├── data/
│   └── knowledge_base.json  # 知识库主文件
├── reports/               # 原始 MD 研报存放处
└── output/
    └── knowledge_base.html  # 可视化输出
```

### 3.3 数据流

```
MD 研报 → kb_import.py → 本体分类 + 知识点提取
                              ↓
                       knowledge_base.json
                              ↓
                    ┌─────────┼─────────┐
                    ↓         ↓         ↓
               CLI 查询    AI 读取    HTML 可视化
```

---

## 四、待确认问题

在开始开发前，需要和你确认以下几点：

1. **本体论体系**：上面列出的 8 个一级分类是否覆盖你的研报主题？需要增减哪些？

2. **MD 研报位置**：现有研报放在哪里？是 `reports/` 目录还是其他路径？是否需要我先看看实际研报的内容来校准本体分类？

3. **导入策略**：MD 研报导入时——
   - **自动提取**：按标题层级（H1/H2/H3...）自动拆分为知识点
   - **手动标注**：在 MD 中用特殊标记（如 `<!-- kb: priority=2 tags=xxx -->`）标注
   - **混合模式**：先自动提取，再人工调整
   
   你倾向哪种？

4. **关系建模**：除了父子关系（树结构），是否需要跨树关系（如"ReAct 依赖 Function Calling"）？这会让数据模型从树变成图，复杂度增加。

5. **Markdown → HTML 渲染**：可视化中的 content 是否需要完整的 Markdown 渲染（代码高亮、表格、列表），还是纯文本即可？前者需要引入 `markdown` 库。

6. **优先级定义**：优先级 1-5 的具体含义是否需要调整？
   - P1 = 核心基础（必须掌握）
   - P2 = 重要常用
   - P3 = 一般了解
   - P4 = 进阶深入
   - P5 = 扩展选读

---

请过目，确认或调整后我立即开始编码。
