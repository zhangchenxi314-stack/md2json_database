# zsk 知识库 — 全版本优化报告

## 项目信息

| 项目 | 说明 |
|------|------|
| 项目名称 | zsk — Agent 开发技术知识库 |
| 项目路径 | `/Users/zcx/project/zsk/` |
| 总行数 | ~2500 行 Python + 脚本 + 文档 |
| 外部依赖 | `markdown`（唯一，纯 Python） |
| CLI 命令 | 14 个 |
| Skills | `zsk-knowledge-base` + `zsk-build` |

---

## 一、优化历程总览

| 版本 | 日期 | 核心问题 | 解决方案 |
|------|------|----------|----------|
| v1.0 | 06-16 | 多份研报各自独立成树，相同概念分裂 | 合并导入：按 category+title 匹配合并 |
| v1.1 | 06-16 | 知识树太扁、无主根、空节点展开空白 | 四层分类树 + 空白引导提示 |
| v1.2 | 06-16 | 跨写法标题不匹配、空摘要 | 标题归一化 + 自动补摘要 + dedup 去重 |
| v1.3 | 06-17 | 规则匹配不准，需 agent 语义理解 | `build` 命令 + `zsk-build` skill |
| v1.4 | 06-17 | Windows agent 仍走规则模式，skill 未随项目移植 | import 封锁 + build.bat + skill 嵌入项目 + 格式模板 |

---

## 二、各版本详细说明

### v1.0 — 合并导入

**问题**：`reports/` 放多份研报 → HTML 按每份报告独立罗列，无法按概念统一展开。

**方案**：默认合并模式。导入时按 `category + title` 匹配已有节点：命中→合并，未命中→新增，H1 和"概述"→跳过。

**合并策略**：内容追加、标签取并、优先级取最高、子节点去重、来源文件拼接。

**效果**：两份研报（33 节点）→ 合并后 19 节点，节省 42%。

**涉及模块**：`kb_core.merge_node()`、`kb_import.import_and_merge()`。

---

### v1.1 — 四层分类树

**问题**：
1. 节点太多、深度仅 2 层（H2→H3）
2. 缺少最大一级节点
3. 分类容器节点点击展开显示"（无正文内容）"

**方案**：
- `ensure_category_tree()` 构建：主根 → 8 分类 → 概念 → 子概念（深度 2→4）
- HTML 空白节点按类型分级提示（主根/分类/容器/叶子）

**踩坑**：初版把 H3 子节点也剥离到分类下，导致概念子节点丢失。修复：只移动无父节点的 H2 概念。

**效果**：1 个主根 + 8 个分类节点，深度 4。子节点完整保留。

**涉及模块**：`kb_core.ensure_category_tree()`、`kb_export` selectNode 函数。

---

### v1.2 — 标题归一化 + 去重

**问题**：
1. `"AI Agent 工具调用技术"` vs `"工具调用技术"` 不匹配
2. 部分节点展开后简介空白

**方案**：
- `normalize_title()`：去标点→去空格→循环剥前缀（agent/ai/aiagent）
- `find_by_title_category()` 改用归一化比较
- `fill_empty_abstracts()` 从正文取首段自动补摘要
- `dedup_pass()` 遍历合并归一化相同的重复节点

**效果**：6 组跨写法标题测试全部通过。`dedup` 命令可事后清理。

**涉及模块**：`kb_core.normalize_title/fill_empty_abstracts/dedup_pass`。

---

### v1.3 — Agent 智能构建

**问题**：规则匹配本质上是关键词+正则，无法理解"Agent评测"属于`evaluation`分类、"LLM评测方法"和"Benchmark"是同一概念。

**方案**：双模架构。`import`（规则）保留但降级，新增 `build`（Agent 智能模式）：

- `kb.py build` 输出四段分析报告（KB 状态→本体论→研报章节→操作指令）
- Agent 阅读分析→语义理解每个概念→用 `add`/`edit` 精准构建
- `zsk-build` skill 定义完整工作流+语义合并规则

**涉及模块**：`kb.py cmd_build`（~120 行）、`zsk-build` skill。

---

### v1.4 — Windows 兼容 + import 封锁 + skill 嵌入

**问题**：移植到 Windows 后 agent 仍走 `import`（旧 skill 路由），生成杂乱树。`zsk-build` skill 在 `~/.hermes/` 里，未随项目移植。

**方案**：四重防线

| 防线 | 机制 |
|------|------|
| ① import 封锁 | `sys.stdin.isatty()` 检测，非交互终端自动拒绝 |
| ② skill 路由 | `zsk-knowledge-base` v2.0，导入场景全部路由到 `build` |
| ③ skill 嵌入 | `skills/` 目录随项目，`setup` 复制到 `~/.hermes/` 并替换路径占位符 |
| ④ 格式模板 | `reports/EXAMPLE.md` + `AI_COMMANDS.md` 6 场景参考 |

**新增文件**：`build.bat`（Win）、`AI_COMMAND.bat/.sh`、`AI_COMMANDS.md`、`README.md`。

---

## 三、架构演进

```
v1.0                     v1.4
─────                    ────
kb.py (11 cmd)           kb.py (14 cmd)
├── import (规则)         ├── import (封锁)
└── export               ├── build  (Agent 智能)
                         ├── dedup
                         ├── reorganize
                         ├── setup  (安装 skills/)
                         └── export

kb_core.py               kb_core.py
├── CRUD                  ├── CRUD
                          ├── merge_node
                          ├── ensure_category_tree
                          ├── normalize_title
                          ├── fill_empty_abstracts
                          └── dedup_pass

                          skills/
                          ├── zsk-knowledge-base/SKILL.md
                          └── zsk-build/SKILL.md

                          build.bat / build.sh
                          AI_COMMANDS.md
                          README.md
```

---

## 四、最终交付物

```
zsk/
├── kb.py                    # CLI 主入口 (14 命令)
├── kb_core.py               # 数据模型 + 合并 + 分类树 + 去重
├── kb_ontology.py           # 8 分类本体
├── kb_import.py             # 规则导入 + 合并导入
├── kb_export.py             # HTML 可视化
├── skills/                  # ★ skill 模板（随项目移植）
│   ├── zsk-knowledge-base/
│   │   └── SKILL.md         #   知识库操作 skill v2.0
│   └── zsk-build/
│       └── SKILL.md         #   智能构建 skill v1.0
├── build.bat                # Windows 一键构建
├── build.sh / build.command # macOS/Linux 一键构建
├── AI_COMMAND.bat/.sh       # 对 AI 说的话（复制粘贴）
├── AI_COMMANDS.md           # 6 场景命令参考
├── README.md                # 快速开始指南
├── reports/
│   └── EXAMPLE.md           # 研报格式模板
├── data/
│   └── knowledge_base.json
├── output/
│   └── knowledge_base.html
├── REQUIREMENTS.md
├── DEV_REPORT.md
└── OPTIMIZE_REPORT_V1-V5.md
```

---

## 五、移植到新机器（3 步）

```bash
# 1. 复制项目
cp -r zsk/ D:\tools\

# 2. 一键
双击 build.bat          # Windows
./build.sh              # macOS/Linux

# 3. 或手动
pip install markdown
python kb.py setup      # 安装 skills（路径自动适配）
# 对 Hermes 说 AI_COMMAND.bat 里的那句话
```
