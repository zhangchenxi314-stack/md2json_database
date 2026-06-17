"""
HTML 可视化导出。
将知识库导出为单文件交互式 HTML 页面。
需要: pip install markdown （纯 Python，无 C 扩展）
"""
from __future__ import annotations

import json
from pathlib import Path
from kb_core import KnowledgeBase
from kb_ontology import ONTOLOGY, PRIORITY_LEVELS


def _md_to_html(md_text: str) -> str:
    """Markdown → HTML，带代码块 CSS class。"""
    try:
        import markdown
        return markdown.markdown(
            md_text,
            extensions=["fenced_code", "tables", "codehilite", "toc"],
        )
    except ImportError:
        import html
        return "<pre>" + html.escape(md_text) + "</pre>"


def _extract_first_sentence(text: str, max_len: int = 120) -> str:
    """从正文取第一句有意义的话作为摘要。"""
    if not text:
        return ""
    for line in text.split("\n"):
        line = line.strip()
        if not line or line.startswith("#") or line.startswith("```") or line.startswith("|"):
            continue
        import re
        clean = re.sub(r"[\*\`\[\]\(\)\>\-\+]", "", line).strip()
        if len(clean) > 8:
            return clean[:max_len] + ("…" if len(clean) > max_len else "")
    return ""


def _node_to_tree_item(node, kb: KnowledgeBase) -> dict:
    """递归构建树节点。"""
    children = kb.get_children(node.id)
    pri_info = PRIORITY_LEVELS.get(node.priority, PRIORITY_LEVELS[5])
    cat_label = ""
    if node.category and node.category in ONTOLOGY:
        cat_label = ONTOLOGY[node.category]["label"]

    return {
        "id": node.id,
        "title": node.title,
        "abstract": node.abstract or _extract_first_sentence(node.content),
        "content_html": _md_to_html(node.content),
        "priority": node.priority,
        "priority_label": pri_info["label"],
        "priority_color": pri_info["color"],
        "priority_bg": pri_info["bg"],
        "tags": node.tags,
        "category": node.category,
        "category_label": cat_label,
        "l2_category": node.l2_category,
        "source_file": node.source_file,
        "source_section": node.source_section,
        "references": node.references,
        "children": [_node_to_tree_item(c, kb) for c in children],
    }


def export_html(kb: KnowledgeBase, output_path: str | Path):
    """导出知识库为交互式 HTML。"""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # 构建树数据
    roots = kb.get_roots()
    tree_data = [_node_to_tree_item(r, kb) for r in roots]
    stats = kb.stats()

    # 构建本体分类信息
    ontology_info = {
        cat_id: {"label": v["label"], "description": v["description"]}
        for cat_id, v in ONTOLOGY.items()
    }

    data_json = json.dumps({
        "tree": tree_data,
        "stats": stats,
        "ontology": ontology_info,
        "priorities": {
            str(k): v for k, v in PRIORITY_LEVELS.items()
        },
    }, ensure_ascii=False)

    html = _build_html(data_json)
    output_path.write_text(html, encoding="utf-8")
    return output_path


def _build_html(data_json: str) -> str:
    """构建完整 HTML 页面。"""
    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Agent 开发技术知识库</title>
<style>
/* ── 全局 ──────────────────────────────────────── */
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC",
                 "Microsoft YaHei", sans-serif;
    background: #f8f9fa; color: #333; line-height: 1.6;
    display: flex; flex-direction: column; height: 100vh;
}}

/* ── 顶栏 ──────────────────────────────────────── */
#toolbar {{
    background: #fff; border-bottom: 1px solid #e0e0e0;
    padding: 12px 20px; display: flex; gap: 12px; align-items: center;
    flex-shrink: 0; flex-wrap: wrap;
}}
#toolbar h1 {{ font-size: 18px; color: #1a73e8; margin-right: 16px; white-space: nowrap; }}
#search {{ flex: 1; min-width: 200px; max-width: 400px;
    padding: 8px 14px; border: 1px solid #ddd; border-radius: 20px;
    font-size: 14px; outline: none; transition: border .2s;
}}
#search:focus {{ border-color: #1a73e8; }}
.stats-badge {{
    font-size: 12px; padding: 4px 10px; border-radius: 12px;
    background: #e8f0fe; color: #1a73e8; white-space: nowrap;
}}
#priority-legend {{
    display: flex; gap: 8px; align-items: center; font-size: 12px; flex-wrap: wrap;
}}
.legend-dot {{
    width: 10px; height: 10px; border-radius: 50%; display: inline-block;
    margin-right: 3px;
}}

/* ── 主体布局 ────────────────────────────────────── */
#main {{ display: flex; flex: 1; overflow: hidden; }}
#sidebar {{
    width: 360px; min-width: 280px; background: #fff;
    border-right: 1px solid #e0e0e0; overflow-y: auto;
    display: flex; flex-direction: column;
}}
#detail {{
    flex: 1; overflow-y: auto; padding: 24px 32px; background: #fafbfc;
}}

/* ── 侧栏树 ──────────────────────────────────────── */
#tree-header {{
    padding: 10px 16px; font-size: 13px; color: #666;
    border-bottom: 1px solid #f0f0f0; display: flex; justify-content: space-between;
}}
#tree {{ padding: 4px 0; }}

.tree-node {{ user-select: none; }}
.tree-row {{
    display: flex; align-items: center; padding: 6px 12px 6px 4px;
    cursor: pointer; border-left: 3px solid transparent;
    transition: background .15s, border-color .15s;
}}
.tree-row:hover {{ background: #f0f4ff; }}
.tree-row.active {{ background: #e8f0fe; border-left-color: #1a73e8; }}
.tree-row.hidden {{ display: none; }}

.toggle {{
    width: 20px; height: 20px; display: inline-flex; align-items: center;
    justify-content: center; font-size: 10px; color: #999; flex-shrink: 0;
    cursor: pointer; border-radius: 4px; transition: background .15s;
}}
.toggle:hover {{ background: #e0e0e0; }}
.toggle.leaf {{ visibility: hidden; }}

.priority-dot {{
    width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0;
    margin: 0 6px 0 2px;
}}
.node-title {{ font-size: 13px; flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }}
.node-tags {{ display: flex; gap: 4px; margin-left: 6px; flex-shrink: 0; }}
.node-tag {{
    font-size: 10px; padding: 1px 6px; border-radius: 8px;
    background: #f0f0f0; color: #888; white-space: nowrap;
}}

/* ── 详情面板 ──────────────────────────────────────── */
#detail-empty {{
    display: flex; flex-direction: column; align-items: center;
    justify-content: center; height: 100%; color: #bbb;
}}
#detail-empty .icon {{ font-size: 64px; margin-bottom: 16px; }}

#detail-content {{ display: none; }}
#detail-content.show {{ display: block; }}

.detail-header {{ margin-bottom: 20px; padding-bottom: 16px; border-bottom: 1px solid #eee; }}
.detail-header h2 {{ font-size: 22px; margin-bottom: 8px; }}
.detail-meta {{
    display: flex; gap: 16px; flex-wrap: wrap; font-size: 13px; color: #888;
    align-items: center;
}}
.detail-meta .badge {{
    padding: 2px 10px; border-radius: 10px; font-size: 12px; font-weight: 500;
}}
.detail-abstract {{
    background: #f0f7ff; border-left: 3px solid #1a73e8;
    padding: 12px 16px; margin-bottom: 20px; border-radius: 0 6px 6px 0;
    font-size: 14px; color: #555;
}}

/* ── Markdown 渲染 ─────────────────────────────────── */
.md-content {{ font-size: 15px; }}
.md-content h1 {{ font-size: 24px; margin: 24px 0 12px; color: #222; }}
.md-content h2 {{ font-size: 20px; margin: 20px 0 10px; color: #333; border-bottom: 1px solid #eee; padding-bottom: 6px; }}
.md-content h3 {{ font-size: 17px; margin: 16px 0 8px; color: #444; }}
.md-content h4, .md-content h5, .md-content h6 {{ font-size: 15px; margin: 12px 0 6px; color: #555; }}
.md-content p {{ margin: 8px 0; }}
.md-content ul, .md-content ol {{ margin: 8px 0; padding-left: 24px; }}
.md-content li {{ margin: 4px 0; }}
.md-content code {{
    background: #f0f0f0; padding: 2px 6px; border-radius: 3px;
    font-family: "SF Mono", "Fira Code", "Consolas", monospace; font-size: 13px;
}}
.md-content pre {{
    background: #1e1e1e; color: #d4d4d4; padding: 16px; border-radius: 8px;
    overflow-x: auto; margin: 12px 0; font-size: 13px; line-height: 1.5;
}}
.md-content pre code {{
    background: none; padding: 0; color: inherit; font-size: inherit;
}}
.md-content table {{
    border-collapse: collapse; width: 100%; margin: 12px 0; font-size: 14px;
}}
.md-content th, .md-content td {{
    border: 1px solid #ddd; padding: 8px 12px; text-align: left;
}}
.md-content th {{ background: #f5f7fa; font-weight: 600; }}
.md-content tr:hover {{ background: #fafbfc; }}
.md-content blockquote {{
    border-left: 4px solid #ddd; padding: 8px 16px; margin: 12px 0;
    color: #666; background: #f9f9f9; border-radius: 0 6px 6px 0;
}}
.md-content a {{ color: #1a73e8; text-decoration: none; }}
.md-content a:hover {{ text-decoration: underline; }}
.md-content hr {{ border: none; border-top: 1px solid #eee; margin: 20px 0; }}
.md-content img {{ max-width: 100%; border-radius: 6px; }}

/* ── 引用列表 ──────────────────────────────────────── */
.refs-section {{ margin-top: 24px; padding-top: 16px; border-top: 1px solid #eee; }}
.refs-section h4 {{ font-size: 14px; color: #888; margin-bottom: 8px; }}
.ref-item {{ font-size: 13px; color: #777; margin: 4px 0; padding-left: 12px; border-left: 2px solid #eee; }}

/* ── 响应式 ────────────────────────────────────────── */
@media (max-width: 768px) {{
    #main {{ flex-direction: column; }}
    #sidebar {{ width: 100%; max-height: 40vh; border-right: none; border-bottom: 1px solid #e0e0e0; }}
}}
</style>
</head>
<body>

<!-- 顶栏 -->
<div id="toolbar">
    <h1>🧠 Agent 开发技术知识库</h1>
    <input id="search" type="text" placeholder="搜索知识点…" oninput="filterTree()">
    <span class="stats-badge" id="stats-count"></span>
    <span class="stats-badge" id="stats-depth"></span>
    <div id="priority-legend"></div>
</div>

<!-- 主体 -->
<div id="main">
    <div id="sidebar">
        <div id="tree-header">
            <span>📂 知识树</span>
            <span style="cursor:pointer" onclick="collapseAll()" title="全部折叠">⊟</span>
        </div>
        <div id="tree"></div>
    </div>
    <div id="detail">
        <div id="detail-empty">
            <div class="icon">📖</div>
            <p>点击左侧知识点查看详情</p>
        </div>
        <div id="detail-content"></div>
    </div>
</div>

<script>
// ── 数据 ───────────────────────────────────────────
const DATA = {data_json};

// ── 渲染函数 ───────────────────────────────────────
function buildTree(nodes, container, depth) {{
    nodes.forEach(node => {{
        const div = document.createElement('div');
        div.className = 'tree-node';
        div.dataset.id = node.id;
        div.dataset.title = node.title.toLowerCase();
        div.dataset.tags = (node.tags || []).join(' ').toLowerCase();
        div.dataset.content = (node.abstract || '') + ' ' + (node.category_label || '');
        div.dataset.priority = node.priority;

        const row = document.createElement('div');
        row.className = 'tree-row';
        row.style.paddingLeft = (8 + depth * 16) + 'px';
        row.onclick = (e) => {{ e.stopPropagation(); selectNode(node); }};

        // toggle
        const toggle = document.createElement('span');
        toggle.className = 'toggle' + (node.children.length === 0 ? ' leaf' : '');
        toggle.textContent = '▶';
        if (node.children.length > 0) {{
            toggle.onclick = (e) => {{
                e.stopPropagation();
                toggleNode(div, toggle);
            }};
        }}
        row.appendChild(toggle);

        // priority dot
        const dot = document.createElement('span');
        dot.className = 'priority-dot';
        dot.style.background = node.priority_color;
        dot.title = node.priority_label;
        row.appendChild(dot);

        // title
        const titleEl = document.createElement('span');
        titleEl.className = 'node-title';
        titleEl.textContent = node.title;
        row.appendChild(titleEl);

        // tags
        if (node.tags && node.tags.length > 0) {{
            const tagsDiv = document.createElement('span');
            tagsDiv.className = 'node-tags';
            node.tags.slice(0, 3).forEach(t => {{
                const tEl = document.createElement('span');
                tEl.className = 'node-tag';
                tEl.textContent = t;
                tagsDiv.appendChild(tEl);
            }});
            row.appendChild(tagsDiv);
        }}

        div.appendChild(row);

        // children container
        if (node.children.length > 0) {{
            const childContainer = document.createElement('div');
            childContainer.className = 'tree-children';
            childContainer.style.display = 'none';
            buildTree(node.children, childContainer, depth + 1);
            div.appendChild(childContainer);
        }}

        container.appendChild(div);
        window._nodeMap[node.id] = node;
    }});
}}

function toggleNode(div, toggle) {{
    const childContainer = div.querySelector('.tree-children');
    if (!childContainer) return;
    if (childContainer.style.display === 'none') {{
        childContainer.style.display = 'block';
        toggle.textContent = '▼';
    }} else {{
        childContainer.style.display = 'none';
        toggle.textContent = '▶';
    }}
}}

function collapseAll() {{
    document.querySelectorAll('.tree-children').forEach(c => c.style.display = 'none');
    document.querySelectorAll('.toggle:not(.leaf)').forEach(t => t.textContent = '▶');
}}

function selectNode(node) {{
    // highlight
    document.querySelectorAll('.tree-row').forEach(r => r.classList.remove('active'));
    const row = document.querySelector(`[data-id="${{node.id}}"] .tree-row`);
    if (row) row.classList.add('active');

    // show detail
    document.getElementById('detail-empty').style.display = 'none';
    const dc = document.getElementById('detail-content');
    dc.className = 'show';

    let tagsHtml = (node.tags || []).map(t =>
        `<span class="node-tag">${{t}}</span>`).join('');

    let refsHtml = '';
    if (node.references && node.references.length > 0) {{
        refsHtml = `<div class="refs-section">
            <h4>📚 参考文献</h4>
            ${{node.references.map(r => `<div class="ref-item">${{r}}</div>`).join('')}}
        </div>`;
    }}

    // 内容区域：为空时给友好提示
    let contentHtml = node.content_html;
    if (!contentHtml || contentHtml.trim() === '') {{
        if (node.id === 'kb-root') {{
            contentHtml = '<p style="color:#666">📖 AI Agent 开发技术全景知识体系。点击左侧分类节点逐步展开查看各领域知识点。</p>';
        }} else if (node.id.startsWith('cat-')) {{
            contentHtml = `<p style="color:#666">📂 此节点为<b>${{node.title}}</b>分类容器，点击左侧展开箭头查看该分类下的所有知识点。</p>`;
        }} else if (node.children && node.children.length > 0) {{
            contentHtml = `<p style="color:#666">📂 此节点包含 ${{node.children.length}} 个子知识点，点击左侧展开箭头查看详情。</p>`;
        }} else {{
            contentHtml = '<p><em>（暂无详细内容）</em></p>';
        }}
    }}

    dc.innerHTML = `
        <div class="detail-header">
            <h2>${{node.title}}</h2>
            <div class="detail-meta">
                <span class="badge" style="background:${{node.priority_bg}};color:${{node.priority_color}}">
                    ${{'⭐'.repeat(node.priority)}} P${{node.priority}} ${{node.priority_label}}
                </span>
                ${{node.category_label ? `<span>${{node.category_label}}</span>` : ''}}
                ${{node.l2_category ? `<span>· ${{node.l2_category}}</span>` : ''}}
                ${{node.source_file ? `<span>📄 ${{node.source_file}}</span>` : ''}}
                ${{node.source_section ? `<span>§ ${{node.source_section}}</span>` : ''}}
            </div>
        </div>
        ${{node.abstract ? `<div class="detail-abstract">${{node.abstract}}</div>` : ''}}
        <div class="md-content">${{contentHtml}}</div>
        ${{tagsHtml ? `<div style="margin-top:16px;display:flex;gap:6px;flex-wrap:wrap">${{tagsHtml}}</div>` : ''}}
        ${{refsHtml}}
    `;
}}

function filterTree() {{
    const q = document.getElementById('search').value.toLowerCase().trim();
    document.querySelectorAll('.tree-node').forEach(div => {{
        if (!q) {{
            div.querySelector('.tree-row').classList.remove('hidden');
            return;
        }}
        const text = div.dataset.title + ' ' + div.dataset.tags + ' ' + div.dataset.content;
        const match = text.toLowerCase().includes(q);
        div.querySelector('.tree-row').classList.toggle('hidden', !match);
        // 如果匹配，展开父节点
        if (match) {{
            let parent = div.parentElement;
            while (parent) {{
                if (parent.classList.contains('tree-children')) {{
                    parent.style.display = 'block';
                    const siblingToggle = parent.parentElement.querySelector('.toggle');
                    if (siblingToggle) siblingToggle.textContent = '▼';
                }}
                parent = parent.parentElement;
            }}
        }}
    }});
}}

// ── 统计 ───────────────────────────────────────────
function renderStats() {{
    const s = DATA.stats;
    document.getElementById('stats-count').textContent =
        `节点: ${{s.node_count}}`;
    document.getElementById('stats-depth').textContent =
        `最大深度: ${{s.max_depth}}`;

    // priority legend
    const legend = document.getElementById('priority-legend');
    const pri = DATA.priorities;
    legend.innerHTML = Object.entries(pri).map(([k, v]) =>
        `<span><span class="legend-dot" style="background:${{v.color}}"></span>P${{k}} ${{s.by_priority[k] || 0}}</span>`
    ).join('');
}}

// ── 初始化 ─────────────────────────────────────────
window._nodeMap = {{}};
const treeContainer = document.getElementById('tree');
buildTree(DATA.tree, treeContainer, 0);

// 默认展开第一层
document.querySelectorAll('#tree > .tree-node > .tree-children').forEach(c => {{
    c.style.display = 'block';
}});
document.querySelectorAll('#tree > .tree-node > .tree-row > .toggle:not(.leaf)').forEach(t => {{
    t.textContent = '▼';
}});

renderStats();
</script>
</body>
</html>"""
