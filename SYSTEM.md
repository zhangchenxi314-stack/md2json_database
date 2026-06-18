# zsk 系统说明文档

## 一、系统概述

zsk 是一个两阶段流水线系统，将华为内部技术网站的调研内容自动转化为结构化 Agent 技术知识库。

- **阶段 A**：`researching-and-reporting` skill 驱动 agent-browser 对 3ms、jx社区、w3、2012实验室四个网站进行自动抓取，生成 Markdown 研报
- **阶段 B**：`zsk-build` skill 驱动 LLM 语义理解研报内容，按 8 大本体分类逐节点写入 JSON 知识库，最终导出交互式 HTML 可视化页面和 CLI 查询接口

---

## 二、系统架构图

```
┌─────────────────────────────────────────────────┐
│                  ①  数据源                       │
│    3ms     jx社区      w3     2012实验室          │
└────────────┬────────────┬────────────┬───────────┘
             │            │            │
             └──────┬──────┴──────┬─────┘
                    ▼             ▼
┌─────────────────────────────────────────────────┐
│  ②  researching-and-reporting skill             │
│     ├─ agent-browser 自动抓取                    │
│     └─ 生成 Markdown 研报                        │
└──────────────────────┬──────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────┐
│  ③  zsk-build skill                             │
│     ├─ LLM 语义理解研报内容                       │
│     ├─ 逐节点写入知识库                           │
│     └─ 整理去重 + 导出                            │
└──────────────────────┬──────────────────────────┘
                       │
          ┌────────────┼────────────┐
          ▼            ▼            ▼
┌────────────┐ ┌────────────┐ ┌────────────┐
│  JSON 文件  │ │  HTML 页面  │ │  CLI 查询   │
└────────────┘ └────────────┘ └────────────┘
             ④  输出与使用
```

---

## 三、各层详细说明

### ① 数据源

**输入：** 无（外部系统）

**输出：** 四个网站的原始网页内容

| 网站 | 类型 | 说明 |
|------|------|------|
| 3ms | 技术文档 / 博客 | 内部技术文章与最佳实践 |
| jx社区 | 开发者社区 / 论坛 | 技术讨论与问答 |
| w3 | 内部 Wiki 知识库 | 结构化技术文档 |
| 2012实验室 | 论文 / 专利库 | 前沿研究与专利 |

---

### ② researching-and-reporting skill

**输入：** 四个网站的原始网页内容

**输出：** Markdown 研报文件（放入 `reports/` 目录）

#### 工作流

```
四个网站 URL
     │
     ▼
researching-and-reporting skill 触发
     │
     ▼
agent-browser CLI 自动抓取网页
     │  浏览器渲染 → DOM 解析 → 正文提取
     ▼
Markdown 研报生成
     │  按 H1 / H2 / H3 标题层级结构化输出
     │  支持可选标注：<!-- kb: priority=2 tags=xxx -->
     ▼
reports/*.md 研报文件
```

#### 依赖

| 依赖 | 用途 | 必需 |
|------|------|------|
| researching-and-reporting skill | 调研工作流编排 | ✅ |
| agent-browser CLI | 网页自动抓取与内容提取 | ✅ |
| 华为内网访问权限 | 访问四个内部网站 | ✅ |

---

### ③ zsk-build skill — 知识库构建引擎（核心）

**输入：** `reports/` 目录下的 Markdown 研报文件

**输出：** 结构化 JSON 知识库 (`data/knowledge_base.json`) + 交互式 HTML 页面 (`output/knowledge_base.html`)

#### 工作流

```
reports/*.md 研报
     │
     ▼
Step 1 — kb.py build（输出分析报告）
     │  当前 KB 状态 + 本体分类体系 + 每份研报逐章节分析 + 操作指令模板
     ▼
Step 2 — LLM 语义理解（Agent 核心）
     │  读取每篇研报完整内容
     │  判断归属分类（8 大本体分类之一）
     │  检查与已有概念的语义重叠（决定合并还是新建）
     │  确定优先级（P1~P5）和标签
     │  生成摘要（abstract）
     ▼
Step 3 — 逐节点写入（kb.py add / edit）
     │  add：创建新概念节点
     │  edit：合并到已有概念（追加内容，取最高优先级）
     │  edit --parent：建立父子层级
     ▼
Step 4 — 整理与导出
     │  reorganize：修复树结构（主根→8分类→概念→子概念）
     │  dedup：合并重复概念
     │  export：生成 HTML 可视化页面
     ▼
输出：JSON + HTML + CLI
```

#### 核心模块

| 模块 | 职责 | 行数 |
|------|------|------|
| `kb_ontology.py` | 8 大分类定义、5 级优先级配置、标签规范、章节标题→分类映射 | 178 |
| `kb_core.py` | KnowledgeNode 数据类、KnowledgeBase CRUD、标题归一化、节点合并、去重、分类树构建 | 523 |
| `kb_import.py` | MD 解析（代码块安全处理）、自动分类/标签/优先级、合并导入 | 550 |
| `kb_export.py` | 单文件 HTML 生成（CSS + vanilla JS，零外部 JS 依赖） | 468 |
| `kb.py` | CLI 入口，14 个命令 | 687 |

#### 依赖

| 依赖 | 用途 | 必需 |
|------|------|------|
| Python 3.9+ | 运行环境 | ✅ |
| `markdown` 库 | MD → HTML 渲染（`pip3 install markdown`） | ✅ |
| Hermes Agent | 运行 zsk-build / zsk-knowledge-base skill | ✅ |
| zsk-build skill | Agent 智能构建工作流定义 | ✅ |
| zsk-knowledge-base skill | 知识库查询与管理接口 | ✅ |
| kb.py | CLI 工具（14 个命令） | ✅ |

---

### ④ 输出与使用

**输入：** 知识库引擎的构建结果

**输出：** 三种使用形态

| 输出 | 格式 | 用途 |
|------|------|------|
| `data/knowledge_base.json` | JSON 文件 | 结构化知识存储，人 + AI 可读，可作 RAG 知识源 |
| `output/knowledge_base.html` | HTML 页面 | 浏览器打开，交互式知识树（展开折叠、搜索、优先级色标、Markdown 渲染） |
| CLI 命令查询 | 终端 | `kb.py search/list/stats/show` 命令行查询 |

---

## 四、数据模型

每个知识点为一个 `KnowledgeNode`，JSON 结构：

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | string | 唯一标识 |
| `title` | string | 知识点标题 |
| `abstract` | string | 一句话摘要（AI 检索用） |
| `content` | string | 完整正文（Markdown） |
| `priority` | int 1-5 | P1=核心基础，P2=重要常用，P3=一般了解，P4=进阶深入，P5=扩展选读 |
| `tags` | string[] | 标签数组 |
| `category` | string | 本体分类 ID |
| `parent_id` | string | 父节点 ID（树结构） |
| `children` | string[] | 子节点 ID 列表 |
| `source_file` | string | 来源研报文件名（溯源） |
| `created_at` | ISO8601 | 创建时间 |
| `updated_at` | ISO8601 | 更新时间 |

### 8 大本体分类

| ID | 标签 | 二级分类 |
|----|------|---------|
| `architecture` | 架构设计 | 单Agent、多Agent、混合、框架对比、核心能力、基础设施 |
| `planning` | 规划与推理 | ReAct、Plan-Execute、ToT、CoT、反思、路由 |
| `tool-calling` | 工具调用 | Function Calling、MCP、工具选择、编排、API集成 |
| `memory` | 记忆系统 | 短期、长期、向量检索、上下文窗口、记忆整合 |
| `multi-agent` | 多智能体协作 | 角色分工、通信、任务编排、辩论、群体智能 |
| `rag` | RAG 与知识增强 | 检索策略、分块、重排序、嵌入、索引、混合检索 |
| `evaluation` | 评估与评测 | Benchmark、人工评估、LLM-as-Judge、度量、安全评估 |
| `safety` | 安全与对齐 | 护栏、RLHF/DPO、红队测试、提示注入、内容过滤 |

### 优先级色标

| 级别 | 标签 | 颜色 | 
|------|------|------|
| P1 | 核心基础 | 红 #d32f2f |
| P2 | 重要常用 | 橙 #f57c00 |
| P3 | 一般了解 | 黄 #fbc02d |
| P4 | 进阶深入 | 蓝 #1976d2 |
| P5 | 扩展选读 | 灰 #757575 |

---

## 五、CLI 命令参考

| 命令 | 用途 | 示例 |
|------|------|------|
| `build` | 输出分析报告供 Agent 语义构建 | `python3 kb.py build` |
| `add` | 手动添加概念节点 | `python3 kb.py add --title "MCP协议" --category tool-calling --priority 2` |
| `edit` | 编辑已有节点 | `python3 kb.py edit <id> --content "追加内容"` |
| `delete` | 删除节点 | `python3 kb.py delete <id> --cascade` |
| `search` | 全文搜索 | `python3 kb.py search "MCP"` |
| `list` | 列出节点 | `python3 kb.py list --category memory` |
| `show` | 查看节点详情 | `python3 kb.py show <id>` |
| `stats` | 统计信息 | `python3 kb.py stats` |
| `import` | 规则导入（已封锁，仅人类可用） | `python3 kb.py import reports/` |
| `export` | 导出 HTML 可视化 | `python3 kb.py export` |
| `setup` | 注册 skill 到 Hermes Agent | `python3 kb.py setup` |
| `reorganize` | 重建四层分类树 | `python3 kb.py reorganize` |
| `dedup` | 去重合并 | `python3 kb.py dedup` |

---

## 六、项目文件结构

```
zsk/
├── kb.py                    # CLI 入口（14 命令）
├── kb_core.py               # 数据模型 + 合并 + 分类树 + 去重
├── kb_ontology.py           # 8 分类本体 + 优先级 + 标签
├── kb_import.py             # MD 解析 + 合并导入
├── kb_export.py             # HTML 可视化
├── skills/                  # Skill 模板（随项目移植）
│   ├── zsk-knowledge-base/SKILL.md
│   └── zsk-build/SKILL.md
├── build.sh / build.bat     # 一键构建脚本（macOS / Windows）
├── AI_COMMAND.sh / .bat     # 对 AI 说的命令（复制粘贴）
├── AI_COMMANDS.md           # 6 场景命令参考
├── README.md                # 快速开始
├── reports/                 # 研报存放目录
│   └── EXAMPLE.md           # 格式模板
├── data/
│   └── knowledge_base.json  # JSON 知识库
├── output/
│   └── knowledge_base.html  # HTML 可视化输出
├── REQUIREMENTS.md          # 需求分析
├── DEV_REPORT.md            # 开发报告
├── FEATURES.md              # 功能概要
├── RISKS.md                 # 风险分析
├── SYSTEM.md                # 本文档
└── ARCHITECTURE_DIAGRAM_PROMPT.md  # 系统框图提示词
```

---

## 七、完整依赖清单

### 运行环境

| 依赖 | 版本要求 | 说明 |
|------|---------|------|
| Python | 3.9+ | 标准库即可运行 |
| pip | 任意 | 安装 markdown 库 |

### Python 库

| 库 | 安装命令 | 用途 | 必需 |
|----|---------|------|------|
| `markdown` | `pip3 install markdown` | MD → HTML 渲染（代码高亮、表格） | ✅ |

其余全部使用 Python 标准库：`json`、`re`、`argparse`、`pathlib`、`uuid`、`datetime`、`dataclasses`、`hashlib`。

### 外部系统

| 依赖 | 用途 | 必需 |
|------|------|------|
| Hermes Agent | 运行 zsk-build / zsk-knowledge-base skill | ✅ |
| agent-browser CLI | 网页自动抓取（阶段 A） | ✅ |
| researching-and-reporting skill | 调研工作流编排（阶段 A） | ✅ |
| 华为内网访问权限 | 访问 3ms / jx社区 / w3 / 2012实验室 | ✅ |

---

## 八、快速开始

```bash
# 1. 安装依赖
pip3 install markdown

# 2. 注册 skill
python3 kb.py setup

# 3. 放入研报到 reports/ 目录

# 4. 对 Hermes Agent 说：
#    "加载 zsk-build skill，然后构建知识库。"
```

或直接运行一键脚本：`./build.sh`（macOS）/ 双击 `build.bat`（Windows）

---

## 九、已知限制

- Agent 构建质量依赖 LLM 模型能力，弱模型可能导致分类错误或合并遗漏
- 标题归一化目前仅剥离 `agent/ai` 前缀，其他语言变体可能未覆盖
- 8 个分类硬编码，新领域无处归类
- 全量 JSON 读写，节点上千时性能下降
- 无版本控制，修改后无法回滚
