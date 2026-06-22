# zsk — Agent 技术知识库

将 Agent 开发技术的 Markdown 研报，按 8 大本体分类构建为结构化 JSON 知识库——人可读、AI 可调、可查询、可维护、可可视化。

## 项目概述

zsk 是一个两阶段流水线系统，将华为内部技术网站的调研内容自动转化为结构化 Agent 技术知识库。

| 阶段 | 做什么 | 谁做的 |
|------|--------|--------|
| **阶段 A — 调研** | 自动抓取 3ms、jx社区、w3、2012实验室四个网站，生成 Markdown 研报 | `researching-and-reporting` skill + agent-browser |
| **阶段 B — 构建** | LLM 语义理解研报内容，按 8 大本体分类逐节点写入 JSON 知识库，导出 HTML 可视化 | `zsk-build` skill + kb.py |

## 核心功能

- **研报解析** — 按标题层级（H1/H2/H3）自动提取知识点
- **本体分类** — 每个知识点归入 8 大分类（架构/规划/工具调用/记忆/多Agent/RAG/评估/安全）
- **LLM 语义构建** — 由 LLM 理解研报内容，判断合并/新建、确定优先级和分类，超越规则匹配
- **四层知识树** — 主根 → 8 分类 → 概念 → 子概念
- **交互式 HTML** — 浏览器打开，展开/折叠、搜索过滤、优先级色标、Markdown 渲染
- **CLI 命令** — 搜索、增删改查、统计、导出，14 个命令
- **跨平台** — Windows（双击 bat）和 macOS/Linux（sh 脚本）一键运行
- **可移植** — 复制项目到任意电脑，`python3 kb.py setup` 即可接入 Hermes Agent

## 8 大本体分类

| 分类 ID | 标签 | 涵盖内容 |
|---------|------|---------|
| `architecture` | 架构设计 | 单Agent、多Agent、混合架构、框架对比 |
| `planning` | 规划与推理 | ReAct、Plan-Execute、ToT、CoT、反思、路由 |
| `tool-calling` | 工具调用 | Function Calling、MCP、工具选择、编排 |
| `memory` | 记忆系统 | 短期/长期记忆、向量检索、上下文窗口 |
| `multi-agent` | 多智能体协作 | 角色分工、通信、任务编排、辩论 |
| `rag` | RAG 与知识增强 | 检索策略、分块、重排序、嵌入、混合检索 |
| `evaluation` | 评估与评测 | Benchmark、LLM-as-Judge、度量 |
| `safety` | 安全与对齐 | 护栏、RLHF/DPO、红队测试、提示注入 |

## 快速开始

### 1. 安装

```bash
# macOS / Linux
pip3 install markdown
python3 kb.py setup

# Windows — 双击 install.bat
```

### 2. 放入研报

将 Markdown 研报文件放入 `reports/` 目录。研报格式要求：

- `#` 标题 = 报告名称（不作为知识节点）
- `##` 标题 = 一级概念（归入某个本体分类）
- `###` 标题 = 二级概念（挂在对应 H2 概念下）
- 可选标注：`<!-- kb: priority=2 tags=tag1,tag2 -->`

详见 `reports/EXAMPLE.md`。

### 3. 构建知识库

对 Hermes Agent 说：

> 加载 zsk-build skill，然后构建知识库。

或使用一键脚本：

```bash
# macOS / Linux
./build.sh

# Windows — 双击 build.bat
```

### 4. 查看结果

- **HTML 可视化**：浏览器打开 `output/knowledge_base.html`
- **CLI 查询**：`python3 kb.py search "MCP"`
- **JSON 源文件**：`data/knowledge_base.json`（可作 RAG 知识源）

## CLI 命令参考

| 命令 | 用途 | 示例 |
|------|------|------|
| `build` | 输出分析报告，供 Agent 语义构建 | `python3 kb.py build` |
| `search` | 全文搜索 | `python3 kb.py search "MCP"` |
| `list` | 列出知识点（可按分类/标签/优先级过滤） | `python3 kb.py list --category memory` |
| `show` | 查看节点详情 | `python3 kb.py show <id>` |
| `stats` | 知识库统计 | `python3 kb.py stats` |
| `add` | 手动添加知识点 | `python3 kb.py add --title "MCP协议" --category tool-calling --priority 2` |
| `edit` | 编辑已有节点 | `python3 kb.py edit <id> --content "追加内容"` |
| `delete` | 删除节点 | `python3 kb.py delete <id> --cascade` |
| `import` | 规则导入（非交互终端自动跳过，请用 build） | `python3 kb.py import reports/` |
| `export` | 导出 HTML 可视化 | `python3 kb.py export` |
| `reorganize` | 重建分类树 | `python3 kb.py reorganize` |
| `dedup` | 去重合并 | `python3 kb.py dedup` |
| `setup` | 注册 skill 到 Hermes Agent（新机器首次） | `python3 kb.py setup` |

> `python3` 或 `python` 取决于系统；Windows 上通常用 `python`。

## 项目结构

```
zsk/
├── kb.py                    # CLI 入口（14 个命令）
├── kb_core.py               # 数据模型 + CRUD + 合并 + 分类树 + 去重
├── kb_ontology.py           # 8 分类定义 + 优先级 + 标签映射
├── kb_import.py             # MD 研报解析 + 合并导入
├── kb_export.py             # HTML 可视化生成
├── skills/                  # Skill 模板（随项目移植）
│   ├── zsk-knowledge-base/  # 知识库查询/管理 skill
│   └── zsk-build/           # Agent 智能构建 skill
├── reports/                 # 研报存放目录
│   └── EXAMPLE.md           # 研报格式模板
├── data/
│   └── knowledge_base.json  # JSON 知识库（构建产物）
├── output/
│   └── knowledge_base.html  # HTML 可视化（构建产物）
├── build.sh / build.bat     # 一键构建脚本
├── install.bat              # Windows 一键安装
├── uninstall.bat            # Windows 一键卸载
├── AI_COMMANDS.md           # 常用对话命令参考
├── SYSTEM.md                # 系统架构文档
├── REQUIREMENTS.md          # 需求分析报告
├── DEV_REPORT.md            # 开发报告
├── FEATURES.md              # 功能概要
├── RISKS.md                 # 风险分析
└── README.md                # 本文档
```

## 依赖

**运行环境：**

| 依赖 | 版本 | 说明 |
|------|------|------|
| Python | 3.9+ | 标准库即可运行 |
| `markdown` 库 | — | MD → HTML 渲染 `pip3 install markdown` |

其余全部使用 Python 标准库（`json`、`re`、`argparse`、`pathlib`、`uuid`、`datetime`）。

**外部系统：**

| 依赖 | 用途 | 必需 |
|------|------|------|
| Hermes Agent | 运行 skill，执行 LLM 语义构建 | ✅ |
| agent-browser CLI | 阶段 A 网页抓取 | ✅（阶段 A） |
| 华为内网权限 | 访问内部四个网站 | ✅（阶段 A） |

## 卸载

```bash
# macOS / Linux
rm -rf ~/.hermes/skills/note-taking/zsk-knowledge-base
rm -rf ~/.hermes/skills/note-taking/zsk-build
pip3 uninstall markdown -y
cd .. && rm -rf zsk

# Windows — 双击 uninstall.bat
```

## 故障排查

| 现象 | 解决 |
|------|------|
| Hermes 找不到 kb.py | `python3 kb.py setup` 重新注册 skill |
| HTML 树结构杂乱 | `python3 kb.py reorganize` 重建分类树 |
| 概念未合并 | `python3 kb.py dedup` 去重，或让 Agent 重新构建 |
| `import` 命令被封锁 | 非交互终端自动跳过，请用 `build` 命令代替 |
| 中文乱码（Windows） | 先执行 `chcp 65001` |

## 已知限制

- Agent 构建质量依赖 LLM 模型能力，弱模型可能导致分类错误或合并遗漏
- 标题归一化仅剥离 `agent/ai` 前缀，其他语言变体可能未覆盖
- 8 个分类硬编码，新领域无处归类
- 全量 JSON 读写，节点上千时性能下降
- 无版本控制，修改后无法回滚
