# 优化报告：Windows 兼容与 import 强制替换

## 一、优化背景

| 项目 | 说明 |
|------|------|
| 关联项目 | zsk — Agent 开发技术知识库 |
| 优化日期 | 2026-06-17 |
| 版本 | v1.4 |
| 触发场景 | 移植到 Windows 电脑后，agent 仍走 `import`（规则模式），生成杂乱文件树，未启用智能构建 |

### 问题链条

```
Windows agent 说"导入研报"
    ↓
zsk-knowledge-base skill 路由到 kb.py import
    ↓
import 用正则+关键词匹配（非语义）
    ↓
跨写法概念漏合并、分类错误
    ↓
HTML 知识树杂乱
```

根因：**skill 没有将"导入"场景路由到 `build`，`import` 命令没有自保护**。

---

## 二、方案设计

### 2.1 四重防线

```
用户/Agent 说"导入研报"
    ↓
┌─ 防线 ①: skill 路由 ──────────────────────────┐
│ zsk-knowledge-base v2.0                         │
│ "导入研报" → 触发 build 工作流                   │
│ import 标注为 deprecated / blocked              │
└────────────────────────────────────────────────┘
    ↓ (如果 agent 仍调用 import)
┌─ 防线 ②: import 自封锁 ────────────────────────┐
│ cmd_import() 检测 stdin.isatty()                │
│ 非交互终端 → 自动拒绝，输出 build 引导            │
│ 交互终端 → 弹确认，默认 N                        │
└────────────────────────────────────────────────┘
    ↓
┌─ 防线 ③: build 输出分析 ───────────────────────┐
│ agent 阅读分析报告 → 语义分类 → add/edit 精准构建 │
└────────────────────────────────────────────────┘
    ↓
┌─ 防线 ④: EXAMPLE.md 模板 ──────────────────────┐
│ 研报不规范时，agent 参考模板理解期望格式            │
│ 或无模板时直接做语义提取                          │
└────────────────────────────────────────────────┘
```

### 2.2 import 封锁逻辑

```python
def cmd_import(kb, args):
    print("⚠  import 是规则匹配模式，准确度有限")
    print("   💡 建议改用: python3 kb.py build")
    print("   继续使用 import？(规则模式)[y/N] ", end="")

    if not sys.stdin.isatty():
        # 非交互终端（agent 调用）→ 自动拒绝
        print("(非交互终端，自动跳过 import，请使用 build 命令)")
        return  # ← 直接退出，不做任何导入

    resp = input().strip().lower()
    if resp not in ("y", "yes"):
        print("已取消。请使用: python3 kb.py build")
        return
    # 只有人类明确输入 y 才继续
```

关键：`sys.stdin.isatty()` 区分人类终端和 agent 管道调用。

### 2.3 Windows 一键脚本

`build.bat` — 与 `build.sh` 功能对等：

```batch
@echo off
chcp 65001 >nul
cd /d "%~dp0"

:: 1. 装依赖
pip install markdown -q

:: 2. 注册 skill
python "%DIR%kb.py" setup

:: 3. 启动构建
hermes -z "加载 zsk-build skill，然后构建知识库。" --skills zsk-build
```

关键差异：`python`（非 `python3`）、`%DIR%`（非 `$DIR`）、`chcp 65001`（UTF-8）。

### 2.4 研报模板

`reports/EXAMPLE.md` — 其他电脑上的 agent 可参照此格式生成规范研报：

```markdown
# [报告标题]                  ← H1，不作节点
## [概念名]                   ← H2，顶层概念
### [子概念]                  ← H3，子知识点
<!-- kb: priority=2 tags=... -->  ← 可选标注
## 参考文献
```

---

## 三、实现细节

### 3.1 kb.py — import 封锁

改动位置：`cmd_import` 函数开头，26 行新增。

核心判断：
- `sys.stdin.isatty()` → True：人类终端，弹 y/N 确认
- `sys.stdin.isatty()` → False：agent 管道，直接拒绝并引导

### 3.2 build.bat

- `chcp 65001` — 启用 UTF-8 编码，防止中文乱码
- `cd /d "%~dp0"` — 无论从哪启动，定位到脚本目录
- `pip install` — Windows 上 pip 通常可直接调用
- `hermes -z` — 同 Linux，Hermes CLI 跨平台

### 3.3 reports/EXAMPLE.md

包含：
- HTML 注释中的完整格式说明（标题层级规则、标注语法、优先级和分类 ID 参考）
- 可替换的占位符 `[你的概念A]`、`[子概念A-1]`
- 实际标注示例 `<!-- kb: priority=2 tags=function-calling,openai -->`

### 3.4 skill 重写

`zsk-knowledge-base` v1.0 → v2.0：

| 字段 | v1.0 | v2.0 |
|------|------|------|
| description | "…import, or manage…" | "…ALWAYS use build mode, NEVER use import…" |
| 导入工作流 | `kb.py import --dry-run` → `kb.py import` | `kb.py build` → 阅读分析 → `kb.py add/edit` |
| 命令示例 | 仅 macOS 路径 | Windows(`python`) + macOS(`python3`) 双写 |
| 一键脚本 | 无 | 提及 `build.bat` / `build.sh` |
| 坑 | "Always dry-run before import" | "**NEVER use `kb.py import`**" |

---

## 四、测试验证

### 4.1 import 封锁验证

```
$ python3 kb.py import reports/

⚠  import 是规则匹配模式，准确度有限
   💡 建议改用智能构建模式
   继续使用 import？(规则模式)[y/N] (非交互终端，自动跳过 import，请使用 build 命令)
```

Agent 管道调用 → 被拦截 ✅

### 4.2 build 命令不受影响

```
$ python3 kb.py build
📊 当前知识库状态
...
```

`build` 独立运行 ✅

### 4.3 build.bat 语法验证

```
> build.bat
============================================
  zsk 知识库一键构建 (Windows)
============================================
[1/3] 安装依赖...
[2/3] 注册 skills...
[3/3] 启动 Hermes Agent 智能构建...
```

---

## 五、影响范围

### 修改文件

| 文件 | 改动 | 类型 |
|------|------|------|
| `kb.py` | `cmd_import` 加 `isatty` 封锁逻辑 | 修改 +26 行 |
| `build.bat` | Windows 一键构建脚本 | 新增 |
| `reports/EXAMPLE.md` | 研报格式模板 + 标注说明 | 新增 |
| `zsk-knowledge-base` skill | v1.0 → v2.0，import deprecated，双平台指令 | 重写 |

### 不兼容变更

- `kb.py import` 在非交互终端（agent 调用）中不再执行，直接拒绝
- 人类仍可通过交互终端输入 `y` 继续使用
- 其他命令无影响

### 项目版本演进

| 版本 | 核心能力 |
|------|----------|
| v1.0 | MD 解析 + JSON 存储 + HTML 可视化 |
| v1.1 | 合并导入 + 跨机器移植（setup） |
| v1.2 | 分类层级 + 归一化匹配 + 去重 |
| v1.3 | Agent 智能构建（build + zsk-build skill） |
| **v1.4** | **Windows 兼容 + import 强制替换（build.bat + EXAMPLE.md + skill v2.0）** |
