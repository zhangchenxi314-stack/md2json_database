"""
知识库本体论定义。
定义 Agent 开发技术领域的分类体系、标签规范、优先级规则。
"""
from __future__ import annotations

# ── 本体分类树 ──────────────────────────────────────────────
# 一级分类 (L1) → 二级分类 (L2, 可选)
ONTOLOGY: dict[str, dict[str, list[str] | None]] = {
    "architecture": {
        "label": "架构设计",
        "description": "Agent 系统架构、核心能力要素、框架设计",
        "l2": [
            "single-agent",    # 单 Agent 架构
            "multi-agent",     # 多 Agent 架构
            "hybrid",          # 混合架构
            "framework-compare", # 主流框架对比
            "core-capabilities", # 核心能力要素
            "infrastructure",  # 基础设施演进
        ],
    },
    "planning": {
        "label": "规划与推理",
        "description": "Agent 的任务规划、推理链、决策策略",
        "l2": [
            "react",           # ReAct 范式
            "plan-execute",    # Plan-and-Execute
            "tree-of-thought", # Tree-of-Thought
            "cot",             # Chain-of-Thought
            "reflection",      # 自我反思
            "routing",         # 路由/分发
        ],
    },
    "tool-calling": {
        "label": "工具调用",
        "description": "Function Calling、MCP、工具选择与编排",
        "l2": [
            "function-calling", # Function Calling
            "mcp",              # MCP 协议
            "tool-selection",   # 工具选择策略
            "tool-orchestration", # 工具编排
            "api-integration",  # API 集成
        ],
    },
    "memory": {
        "label": "记忆系统",
        "description": "短期/长期记忆、向量检索、上下文管理",
        "l2": [
            "short-term",     # 短期记忆
            "long-term",      # 长期记忆
            "vector-retrieval", # 向量检索
            "context-window", # 上下文窗口管理
            "memory-consolidation", # 记忆整合
        ],
    },
    "multi-agent": {
        "label": "多智能体协作",
        "description": "多 Agent 角色分工、通信、编排",
        "l2": [
            "role-assignment",  # 角色分工
            "communication",    # 消息传递/通信协议
            "task-orchestration", # 任务编排
            "debate",           # 辩论/博弈
            "swarm",            # 群体智能
        ],
    },
    "rag": {
        "label": "RAG 与知识增强",
        "description": "检索增强生成、分块、重排序、索引",
        "l2": [
            "retrieval-strategy", # 检索策略
            "chunking",          # 分块策略
            "reranking",         # 重排序
            "embedding",         # 嵌入模型
            "indexing",          # 索引构建
            "hybrid-search",     # 混合检索
        ],
    },
    "evaluation": {
        "label": "评估与评测",
        "description": "Benchmark、评测方法、质量度量",
        "l2": [
            "benchmark",      # 基准测试
            "human-eval",     # 人工评估
            "llm-as-judge",   # LLM 评判
            "metrics",        # 度量指标
            "safety-eval",    # 安全评估
        ],
    },
    "safety": {
        "label": "安全与对齐",
        "description": "护栏、RLHF/DPO、红队测试",
        "l2": [
            "guardrails",     # 护栏机制
            "rlhf-dpo",       # RLHF / DPO
            "red-teaming",    # 红队测试
            "prompt-injection", # 提示注入防护
            "content-filtering", # 内容过滤
        ],
    },
}

# ── 标签规范 ──────────────────────────────────────────────
# 预定义标签（导入时建议从这些中选择，也允许自定义）
PREDEFINED_TAGS: list[str] = [
    # 技术栈
    "llm", "gpt", "claude", "gemini", "llama",
    "langchain", "langgraph", "autogen", "crewai", "semantic-kernel",
    "openai", "anthropic", "google",
    # 技术概念
    "prompt-engineering", "fine-tuning", "zero-shot", "few-shot",
    "streaming", "async", "state-machine", "dag",
    # 角色
    "beginner", "intermediate", "advanced",
    # 来源类型
    "tutorial", "paper", "benchmark", "case-study", "overview",
    "trend", "best-practice",
]

# ── 优先级定义 ──────────────────────────────────────────────
PRIORITY_LEVELS: dict[int, dict[str, str]] = {
    1: {"label": "核心基础", "color": "#d32f2f", "bg": "#ffebee",
        "description": "必须掌握的基础知识"},
    2: {"label": "重要常用", "color": "#f57c00", "bg": "#fff3e0",
        "description": "日常开发常用"},
    3: {"label": "一般了解", "color": "#fbc02d", "bg": "#fffde7",
        "description": "建议了解"},
    4: {"label": "进阶深入", "color": "#1976d2", "bg": "#e3f2fd",
        "description": "深入探索"},
    5: {"label": "扩展选读", "color": "#757575", "bg": "#f5f5f5",
        "description": "按需查阅"},
}

# ── 研报章节 → 本体分类映射 ─────────────────────────────────
# 用于导入时自动分类
SECTION_TO_CATEGORY: dict[str, str] = {
    "概述":                              None,               # 散布到各分类
    "ai agent核心能力要素":               "architecture",
    "aiagent核心能力要素":                "architecture",
    "agent核心能力要素":                  "architecture",
    "核心能力要素":                       "architecture",
    "主流开发框架对比":                   "architecture",
    "开发框架对比":                       "architecture",
    "工具调用技术":                       "tool-calling",
    "工具调用":                           "tool-calling",
    "rag检索增强生成":                    "rag",
    "rag":                                "rag",
    "检索增强生成":                       "rag",
    "记忆系统":                           "memory",
    "基础设施演进":                       "architecture",
    "技术演进趋势总结":                   "architecture",
    "技术趋势总结":                       "architecture",
    "参考文献":                           None,               # 作为元数据
}


def get_category(cat_id: str) -> dict | None:
    """根据分类 ID 获取分类信息。"""
    return ONTOLOGY.get(cat_id)


def get_l2_label(cat_id: str, l2_id: str) -> str:
    """获取二级分类的可读标签（首字母大写）。"""
    return l2_id.replace("-", " ").title()


def get_priority_info(level: int) -> dict:
    """获取优先级配置。"""
    return PRIORITY_LEVELS.get(level, PRIORITY_LEVELS[5])


def map_section_to_category(section_title: str) -> str | None:
    """
    将研报章节标题映射到本体分类 ID。
    返回 None 表示该章节不需要自动归类（如概述、参考文献）。
    """
    key = section_title.strip().lower().replace(" ", "").replace("_", "").replace("-", "")
    return SECTION_TO_CATEGORY.get(key)
