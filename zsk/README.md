# zsk — Agent 开发技术知识库

## 快速开始

### Windows（推荐：双击）

```
双击 build.bat → 全自动完成
```

脚本自动：装依赖 → 注册 skill → 启动 Hermes 构建。

### macOS / Linux

```bash
./build.sh
```

### 手动（如果自动脚本不可用）

```bash
# 1. 装依赖
pip install markdown        # Windows
pip3 install markdown       # macOS/Linux

# 2. 注册 skill
python kb.py setup          # Windows
python3 kb.py setup         # macOS/Linux

# 3. 对 Hermes 说（复制下面这句话）
```

---

## 对 Hermes 说的命令

**完整构建（推荐，适用于首次或重建）：**

> 加载 zsk-build skill，然后构建知识库。

**仅更新（已有知识库，新增了研报）：**

> 加载 zsk-build skill。运行 kb.py build 获取分析，只新增不存在的新概念，已有概念用 edit 追加内容。最后 reorganize、dedup、export。

**仅查询：**

> 搜索知识库里关于 MCP 的内容
> 知识库有多少节点
> 导出知识库可视化

---

## 研报格式要求

放入 `reports/` 目录的 Markdown 文件请遵循以下结构（详见 `reports/EXAMPLE.md`）：

```markdown
# 报告标题

## 概念A（一级知识点）

概念的正文描述。这里写详细内容。

### 子概念A-1（二级知识点）

子概念的正文描述。

<!-- kb: priority=2 tags=tag1,tag2 -->
可选标注，覆盖自动分类。

## 概念B

...

## 参考文献

[1] 引用1
[2] 引用2
```

**规则：**
- `#` H1 = 报告标题（不作为知识节点）
- `##` H2 = 一级概念（归入某个本体分类）
- `###` H3 = 二级概念（挂在 H2 概念下）
- `<!-- kb: priority=N tags=... -->` = 可选标注

**如果研报格式不标准**（如纯文本、无标题层级），agent 仍可通过 `build` 模式的语义理解提取概念，在命令中加一句：

> 研报格式不标准，请直接阅读内容做语义提取和分类。

---

## 故障排查

| 现象 | 解决 |
|------|------|
| Hermes 说找不到 kb.py | 检查路径，或用 `python kb.py setup` 重新注册 skill |
| HTML 树结构杂乱 | 对 Hermes 说「重建分类树」或手动 `python kb.py reorganize` |
| 概念未合并 | 对 Hermes 说「去重合并」或手动 `python kb.py dedup` |
| pip 找不到 | 确认 Python 已安装并加入 PATH |
| 中文乱码 | Windows: 用 `chcp 65001` 后再运行命令 |
