# AI Agent 技术研报：2024年核心能力与框架演进

## 概述

本研报系统梳理了2024年AI Agent开发的核心技术栈，涵盖能力要素、主流框架、
工具调用、RAG增强、记忆系统及基础设施演进趋势。面向Agent开发者提供全景技术视图。

<!-- kb: priority=1 tags=overview,llm -->

## AI Agent 核心能力要素

现代AI Agent系统需要具备以下核心能力：感知环境、规划推理、工具调用、
记忆管理、多模态交互等。这些能力要素共同构成了Agent的"操作系统"层。

### 感知与理解

Agent首先需要理解用户意图和上下文。这包括自然语言理解(NLU)、
意图识别、上下文窗口管理等。最新的大模型已经具备强大的上下文理解能力，
但在长对话和复杂任务中仍面临挑战。

### 规划与决策

规划能力是Agent区别于简单Chatbot的核心差异。主流范式包括ReAct、
Plan-and-Execute、以及更前沿的Tree-of-Thought。

<!-- kb: priority=2 tags=planning,react,plan-execute -->

ReAct(Reasoning + Acting)范式将推理和行动交替进行，每一轮推理后执行工具调用，
观察结果再继续推理。这种模式在LangChain和LangGraph中得到广泛应用。

### 工具使用

工具调用让Agent能够突破LLM的文本边界，与外部世界交互。

## 主流开发框架对比

当前主流Agent开发框架可分为轻量级编排库和全栈平台两类。

| 框架 | 类型 | 特点 | 适用场景 |
|------|------|------|----------|
| LangChain | 编排库 | 生态丰富，组件化 | 快速原型 |
| LangGraph | 状态机 | 有向图编排 | 复杂流程 |
| AutoGen | 多Agent | 对话驱动 | 多角色协作 |
| CrewAI | 多Agent | 角色扮演 | 团队协作 |
| Semantic Kernel | 企业级 | 微软生态 | 企业应用 |

LangGraph通过有向图(DAG)来编排Agent的执行流程，每个节点代表一个状态，
边代表状态转换。相比LangChain的链式调用，LangGraph更适合复杂的多步骤Agent。

## 工具调用技术

工具调用(原Function Calling)是Agent连接外部世界的桥梁。

### Function Calling 基础

<!-- kb: priority=1 tags=function-calling,openai -->

LLM通过Function Calling机制，可以根据用户输入自动选择并调用预定义的函数。
OpenAI在2023年6月首次推出，此后Anthropic、Google等厂商也相继支持。

典型流程：用户输入 → LLM解析意图 → 返回function_call JSON → 执行函数 → 
将结果返回LLM → 生成最终回复。

### MCP 协议

Model Context Protocol (MCP)由Anthropic于2024年底推出，旨在标准化
AI模型与外部工具的交互方式。MCP定义了统一的Client-Server架构。

```python
# MCP Client 示例
from mcp import Client

client = Client()
result = await client.call_tool("web_search", {"query": "AI trends 2024"})
```

### 工具选择策略

当Agent拥有大量工具时，需要高效的检索策略: 基于语义相似度、
基于分类目录、以及混合检索等方法。

## RAG 检索增强生成

RAG是解决LLM知识截止和幻觉问题的主流方案。

### 分块策略

文档分块(Chunking)直接影响检索质量。常用策略：

- **固定大小**: 512/1024 tokens，简单但可能切断语义
- **语义分块**: 基于句子边界和语义相似度动态切分
- **层级分块**: 保持文档结构（标题-段落），适合研报类文档

### 检索与重排序

<!-- kb: priority=2 tags=retrieval-strategy,reranking -->

两阶段检索已成标配：粗排(向量检索 Top-K) → 精排(Cross-encoder 重排序)。
Cohere Rerank和BGE-Reranker是主流选择。

## 记忆系统

Agent的记忆系统决定了其持续对话和个性化能力。

### 短期记忆

短期记忆即对话上下文窗口。128K tokens已成为主流模型标配，但长上下文
仍面临"迷失在中间"(Lost in the Middle)问题。

### 长期记忆

长期记忆通过持久化存储实现跨会话的信息保留。关键技术包括：
向量数据库(Milvus/Pinecone)、知识图谱、以及Mem0等记忆中间件。

<!-- kb: priority=1 tags=memory,long-term,vector-retrieval -->

### 记忆整合策略

从短期到长期记忆的整合需要：重要性评分 → 摘要压缩 → 向量存储。
核心思想是模拟人脑的海马体记忆巩固过程。

## 基础设施演进

Agent基础设施正从"拼凑式"向"平台化"演进。

- **2023**: 手工编排，LangChain链式调用
- **2024 H1**: 状态机编排，LangGraph/AutoGen
- **2024 H2**: MCP协议统一工具接口，标准化加速
- **2025**: Agent原生基础设施（AgentOS, Agent-native DB）

容器化部署、GPU资源调度、观测性(Observability)成为Agent基础设施的三大支柱。

## 技术演进趋势总结

1. **从CoT到Agentic Workflow**: 单次推理 → 多步自主执行
2. **工具标准化**: MCP协议推动工具生态统一
3. **记忆原生化**: 从外挂向量库到模型原生记忆能力
4. **多Agent协作**: 从单体Agent到Agent团队
5. **安全对齐**: RLHF/DPO + 护栏机制成为标配

## 参考文献

[1] Yao et al., "ReAct: Synergizing Reasoning and Acting in Language Models", ICLR 2023
[2] Anthropic, "Model Context Protocol Specification", 2024
[3] Lewis et al., "Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks", NeurIPS 2020
[4] Wang et al., "Plan-and-Solve Prompting: Improving Zero-Shot Chain-of-Thought", 2023
[5] Chase, H., "LangChain: Building Applications with LLMs through Composability", 2023
