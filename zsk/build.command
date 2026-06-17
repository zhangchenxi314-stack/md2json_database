#!/bin/bash
# ============================================================
# zsk 知识库一键构建脚本
# 用法: 双击此文件，或在终端执行 ./build.sh
# 功能: 安装依赖 → 注册 skill → 启动 Hermes 构建知识库
# ============================================================
set -e

# 定位项目根目录（脚本所在目录）
DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$DIR"

echo "============================================"
echo "  📦 zsk 知识库一键构建"
echo "============================================"
echo ""

# ── 1. 安装依赖 ──
echo "📦 [1/3] 安装依赖..."
pip3 install markdown -q 2>/dev/null
echo "   ✅ markdown 就绪"

# ── 2. 注册 skill ──
echo "🔧 [2/3] 注册 skills 到 Hermes Agent..."
python3 "$DIR/kb.py" setup
echo ""

# ── 3. 启动构建 ──
echo "🚀 [3/3] 启动 Hermes Agent 智能构建..."
echo ""
echo "   Agent 将自动："
echo "   ① 读取 reports/ 下所有研报"
echo "   ② 语义理解每个概念 → 归类到 8 个本体分类"
echo "   ③ 合并相同概念、建立父子层级"
echo "   ④ 导出 HTML 知识树"
echo ""
echo "============================================"
echo ""

exec hermes -z "加载 zsk-build skill，然后构建知识库。" --skills zsk-build
