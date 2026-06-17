# zsk 知识库 — OKR 项目管理

**项目：** zsk — Agent 开发技术知识库  
**代码：** ~2500 行 Python  
**依赖：** markdown（唯一）  
**迭代：** v1.0 → v1.1 → v1.2 → v1.3 → v1.4（2026-06-16 ~ 2026-06-17）  
**CLI：** 14 命令  
**Skills：** zsk-knowledge-base + zsk-build  

---

## O1 [v1.0] 搭建研报→知识库的基础数据管道

| KR | 关键结果 | 度量 / 验证 | 状态 |
|----|---------|------------|------|
| KR1.1 | 完成需求分析与系统设计，对齐 6 项关键决策 | REQUIREMENTS.md：本体分类体系（8 大类 × 5~6 子类）、JSON 数据模型（12 字段 KnowledgeNode）、导入策略（混合模式）、优先级 P1~P5、零跨树关系、完整 Markdown 渲染。用户确认全部 6 项后开始编码。 | 已完成 |
| KR1.2 | 实现 MD 研报解析引擎：代码块安全处理 + 分类继承 | kb_import.py（550 行）。围栏检测跳过代码块内 `#`（误解析率 0）；H2→概念 / H3→子概念自动拆分；章节标题关键词映射 8 大分类；子节点自动继承父节点分类；三种导入模式：直接 / --dry-run / -i 交互式。 | 已完成 |
| KR1.3 | 构建 JSON 知识库核心数据模型 + CLI 工具 | kb_core.py（341 行）+ kb.py（564 行）。KnowledgeNode 数据类 + KnowledgeBase CRUD；CLI 初始 11 个命令；kb_ontology.py：8 分类 × 5~6 二级分类 + 标签规范 + 优先级色标。验证：两份测试研报导入 → 20+13 节点，分类/父子/继承全部正确。 | 已完成 |
| KR1.4 | 实现多报告合并导入，相同概念不分裂 | kb_core.merge_node()：按 category+title 匹配。命中→合并（内容追加、标签取并、优先级取最高、子节点去重、来源文件拼接）；未命中→新建。实测：2 份研报 33→19 节点，节省 42%。 | 已完成 |
| KR1.5 | 实现跨机器可移植性：路径自感知 + 一键注册 | PROJECT_DIR = Path(\_\_file\_\_).resolve().parent（路径自感知）；kb.py setup 生成 ~/.hermes/skills/ 下的 skill，路径自动适配当前机器；移植：cp → pip install markdown → python3 kb.py setup → 完成；验证：cd /tmp && python3 /path/to/kb.py stats，任意目录正常调用。 | 已完成 |

---

## O2 [v1.1] 四层知识树可视化：从 8 根平铺到 1 根 4 层

| KR | 关键结果 | 度量 / 验证 | 状态 |
|----|---------|------------|------|
| KR2.1 | 重构知识树层级：8 个平级根 → 1 个主根 + 8 个分类容器（深度 2→4） | 用户反馈三个问题：树太扁 / 缺主根 / 空节点无引导。kb_core.ensure_category_tree()（+91 行）：主根→分类容器→概念→子概念。踩坑：初版误移 H3 子节点导致父子断裂，加 parent_id 判断后修正。效果：根节点 8→1，最大深度 2→4。 | 已完成 |
| KR2.2 | HTML 空白节点分级引导提示 | kb_export.py selectNode 函数（+15 行）：主根→"AI Agent 开发技术全景知识体系…"；分类容器→"此节点为【分类名】分类容器…"；容器节点→"此节点包含 N 个子知识点…"；叶子节点→"（暂无详细内容）"。用户感知从"空白"变为有意义的导览。 | 已完成 |
| KR2.3 | HTML 可视化完整交付：搜索 / 色标 / 展开折叠 / Markdown / 响应式 | kb_export.py（468 行）单文件自包含：零外部 JS/CSS，JSON 内嵌 \<script\>，离线可用；vanilla JS：树渲染 + 实时搜索过滤 + 展开折叠；Python 侧 markdown 库预渲染 → HTML（代码高亮、表格）；移动端响应式布局。 | 已完成 |

---

## O3 [v1.2] 标题归一化合并 + 空摘要填充 + 去重命令

| KR | 关键结果 | 度量 / 验证 | 状态 |
|----|---------|------------|------|
| KR3.1 | 标题归一化：跨写法同一概念自动识别为相同节点 | 问题："AI Agent 工具调用技术" vs "工具调用技术" 不匹配。kb_core.normalize_title()（18 行）：小写→去标点→去空格→循环剥前缀（agent/ai/aiagent）。find_by_title_category() 改用归一化比较。6 组跨写法标题测试全部通过（含中英文混合场景）。 | 已完成 |
| KR3.2 | 空摘要自动填充 + 去重命令自动化 | kb_core.fill_empty_abstracts()：正文首段有效文本自动补摘要，截断 150 字符；kb_export._extract_first_sentence()：HTML 侧双层兜底；kb_core.dedup_pass()：按 category+normalize_title 合并重复节点；导入流程自动化：所有路径末尾追加 fill_empty_abstracts + dedup_pass。 | 已完成 |

---

## O4 [v1.3] Agent 智能语义构建：用 LLM 理解替代规则匹配

| KR | 关键结果 | 度量 / 验证 | 状态 |
|----|---------|------------|------|
| KR4.1 | 新增 build 命令：输出结构化分析报告供 Agent 阅读 | 问题根因：规则 = 关键词 + 正则，"Agent评测维度"→无分类，"LLM评测" vs "Benchmark"→分两个节点。kb.py cmd_build()（~120 行）输出四段报告：① KB 状态（每分类已有概念）、② 本体分类体系、③ 逐章节分析（标题/层级/内容预览 100 字符/自动建议/已存在标记）、④ 操作指令模板。 | 已完成 |
| KR4.2 | 创建 zsk-build skill：定义 Agent 智能构建完整工作流 | Step 1: kb.py build 获取分析 → Step 2: LLM 语义理解每个章节 → Step 3: kb.py add/edit 逐节点构建 → Step 4: reorganize / dedup / export。5 条语义合并规则：同概念不同写法合并、父子保持、新子概念创建、内容追加不重复、优先级升级。 | 已完成 |
| KR4.3 | 一键构建脚本：build.sh / build.command | 三步入魂：pip install markdown → python3 kb.py setup → exec hermes -z "加载 zsk-build skill，然后构建知识库" --skills zsk-build。DIR="$(cd "$(dirname "$0")" && pwd)" 定位项目根；set -e 任一步失败即停止。 | 已完成 |

---

## O5 [v1.4] Windows 兼容 + import 封锁 + skill 嵌入项目

| KR | 关键结果 | 度量 / 验证 | 状态 |
|----|---------|------------|------|
| KR5.1 | Windows 一键构建脚本 + 跨平台命令统一 | 问题：Windows agent 用 python（非 python3），路径用 %DIR%（非 $DIR），中文乱码。build.bat：chcp 65001(UTF-8) → pip install markdown → python kb.py setup → hermes -z "加载 zsk-build skill，然后构建知识库" --skills zsk-build。AI_COMMAND.bat / .sh：6 场景命令，Windows / macOS 双份。 | 已完成 |
| KR5.2 | import 封锁 + skill 路由：四重防线防止退化到规则模式 | 问题链条：agent 说"导入"→skill 路由到 import→规则匹配→分类错/合并漏→树杂乱。防线①：skill 路由—zsk-knowledge-base v2.0，"导入"→触发 build 工作流；防线②：import 自封锁—cmd_import() 检测 stdin.isatty()，非交互终端（agent 管道）自动拒绝；防线③：build 分析输出，agent 阅读→语义分类→add/edit 精准构建；防线④：reports/EXAMPLE.md，研报格式模板 + 标注语法说明。 | 已完成 |
| KR5.3 | Skill 嵌入项目 + AI 命令参考文档 | skills/ 目录随项目移植，setup 复制到 ~/.hermes/ 并替换路径占位符；reports/EXAMPLE.md：研报格式模板（标题层级 / 标注语法 / 分类 ID 参考）；AI_COMMANDS.md：6 场景自然语言命令（构建 / 更新 / 不规范格式 / 搜索 / 导出 / 修复）；README.md：快速开始 + 对 Hermes 说的命令 + 格式要求 + 故障排查。 | 已完成 |

---

## O6 工程文档与交付物

| KR | 关键结果 | 度量 / 验证 | 状态 |
|----|---------|------------|------|
| KR6.1 | 每轮迭代输出独立优化报告（5 份） | OPTIMIZE_REPORT_V2 / V3 / V4 / V5 / FULL。每份报告结构：背景（触发场景 + 问题详述）→ 方案设计 → 实现细节 → 测试验证 → 影响范围（修改文件 + 不兼容变更）。 | 已完成 |
| KR6.2 | 完整工程文档体系（4 份） | REQUIREMENTS.md：项目定位 + 6 项待确认问题 + 技术方案选型；DEV_REPORT.md（448 行）：需求回顾→系统架构→数据模型→关键实现细节→测试验证（10 项全通过）→使用指南→待优化项；RISKS.md：5 类 14 项风险；FEATURES.md：11 项功能概要。 | 已完成 |
| KR6.3 | 系统架构图提示词 | ARCHITECTURE_DIAGRAM_PROMPT.md：4 层分层结构 + ASCII 框图 + 数据流标注 + 8 分类元数据 + Mermaid 版本 + 配色建议。可直接粘贴给 AI 绘图工具生成系统框图。 | 已完成 |

---

## 汇总

| Objective | 版本 | KR 数 | 完成 | 核心产出 |
|-----------|------|-------|------|---------|
| O1 基础数据管道 | v1.0 | 5 | 5/5 | MD解析 + JSON存储 + HTML可视化 + 合并导入 + 跨机器移植 |
| O2 四层知识树 | v1.1 | 3 | 3/3 | 深度2→4，空白节点分级引导，HTML交互完善 |
| O3 归一化与去重 | v1.2 | 2 | 2/2 | 6组跨写法测试通过，空摘要自动填充，去重自动化 |
| O4 Agent智能构建 | v1.3 | 3 | 3/3 | build命令 + zsk-build skill + 一键脚本 |
| O5 Windows+防护 | v1.4 | 3 | 3/3 | build.bat + import封锁 + skill嵌入 + AI命令参考 |
| O6 工程文档 | — | 3 | 3/3 | 5轮优化报告 + 4份工程文档 + 架构图提示词 |
| **合计** | **v1.0→v1.4** | **19** | **19/19** | **全部已完成** |
