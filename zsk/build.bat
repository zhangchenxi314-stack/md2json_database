@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

:: ============================================================
:: zsk 知识库一键构建脚本 (Windows)
:: 用法: 双击此文件
:: 功能: 安装依赖 → 注册 skill → 启动 Hermes 构建知识库
:: ============================================================

cd /d "%~dp0"
set "DIR=%~dp0"

echo ============================================
echo   zsk 知识库一键构建 (Windows^)
echo ============================================
echo.

:: ── 1. 安装依赖 ──
echo [1/3] 安装依赖...
pip install markdown -q 2>nul
echo    markdown 就绪

:: ── 2. 注册 skill ──
echo [2/3] 注册 skills 到 Hermes Agent...
python "%DIR%kb.py" setup
echo.

:: ── 3. 启动构建 ──
echo [3/3] 启动 Hermes Agent 智能构建...
echo.
echo    Agent 将自动：
echo    1. 读取 reports\ 下所有研报
echo    2. 语义理解每个概念 → 归类到 8 个本体分类
echo    3. 合并相同概念、建立父子层级
echo    4. 导出 HTML 知识树
echo.
echo ============================================
echo.

hermes -z "加载 zsk-build skill，然后构建知识库。" --skills zsk-build
