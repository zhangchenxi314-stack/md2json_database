# Agent 记忆与 RAG 深度研究报告

## 概述

本报告深入分析 Agent 记忆系统的实现方案和 RAG 检索增强生成的最新技术演进。

## 记忆系统

Agent 记忆系统是 2024-2025 年 Agent 技术栈中变化最快的领域之一。

### 短期记忆

短期记忆的核心挑战是上下文窗口的高效利用。最新研究提出了"滑动窗口+摘要压缩"
的混合策略，在长对话中保持关键信息的可及性。

<!-- kb: priority=1 tags=memory,short-term,context-window -->

关键技术点：
- 滑动窗口 + 重要性评分，动态保留关键信息
- 摘要模型（如 GPT-4 摘要能力）压缩历史上下文
- Mem0 等记忆中间件提供了开箱即用的短期记忆方案

### 长期记忆

长期记忆需要向量数据库（如 Pinecone、Milvus、Weaviate）作为存储后端。
关键是在海量记忆中快速检索相关信息。

<!-- kb: priority=2 tags=memory,long-term,vector-retrieval -->

2025 年趋势：记忆原生化。模型本身开始具备原生记忆能力（如 Gemini 的
Context Caching、Claude 的 Project Knowledge），减少对外部向量库的依赖。

### 记忆整合策略

记忆整合参考了人脑海马体的工作机制。从短期记忆中选择高重要性信息，
经过摘要压缩后存入长期记忆存储。

## RAG 检索增强生成

RAG 技术从 2023 年的基础检索方案演进到 2025 年的 Agentic RAG。

### 检索策略

除了传统的向量检索，近年出现了多种高级检索策略：
- **Self-RAG**: 模型自主判断是否需要检索、检索什么、如何利用检索结果
- **CRAG**: 检索后加入纠错机制，对检索结果进行质量评估
- **Agentic RAG**: 多步检索，Agent 根据中间结果动态调整检索计划

### 分块策略

最新的语义分块技术利用 embedding 模型的注意力权重来确定最佳切分点，
相比固定大小分块，召回率提升 15-30%。

## 工具调用技术

### Function Calling 基础

2025 年的 Function Calling 已支持：
- 并行工具调用：一次返回多个 tool_call，减少往返延迟
- 结构化输出：JSON Mode / Structured Outputs 确保返回格式可靠
- 工具调用流式：在 streaming 模式下逐步返回 tool_call 参数

### 工具选择策略

当工具数量超过 50 个时，需要高效的检索机制。常用方法包括：
- 基于语义相似度筛选相关工具（embedding + Top-K）
- 工具分组 + 层级选择
- 基于历史使用频率的动态排序

## 技术演进趋势总结

1. 记忆从外挂向量库向模型原生能力演进
2. RAG 从单步检索向多步自主检索演进
3. 工具调用从单次调用向并行+流式演进
4. 检索质量从粗排向精排+纠错演进

## 参考文献

[1] Mem0 Team, "Mem0: The Memory Layer for AI Agents", 2025
[2] Asai et al., "Self-RAG: Learning to Retrieve, Generate, and Critique", 2024
[3] Yan et al., "Corrective Retrieval Augmented Generation", 2024
[4] Google, "Gemini Context Caching Documentation", 2025
