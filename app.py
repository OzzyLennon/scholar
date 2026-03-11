"""
Scholar - 6-Agent 学术工作流引擎 · Streamlit 前端
"""
import sys
import threading
import queue
import json
import time
import os
from datetime import datetime
from pathlib import Path

import streamlit as st

# ==========================================
# 页面基础配置
# ==========================================
st.set_page_config(
    page_title="Scholar · 6-Agent 学术引擎",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ==========================================
# 全局样式
# ==========================================
st.markdown("""
<style>
/* 全局字体与背景 */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

/* 主背景渐变 */
.stApp {
    background: linear-gradient(135deg, #0f0f1a 0%, #1a1a2e 50%, #16213e 100%);
    min-height: 100vh;
}

/* 主标题卡片 */
.hero-card {
    background: linear-gradient(135deg, rgba(99,102,241,0.15) 0%, rgba(139,92,246,0.1) 100%);
    border: 1px solid rgba(99,102,241,0.3);
    border-radius: 20px;
    padding: 2rem 2.5rem;
    margin-bottom: 1.5rem;
    backdrop-filter: blur(10px);
}

.hero-title {
    font-size: 2.4rem;
    font-weight: 700;
    background: linear-gradient(90deg, #818cf8, #a78bfa, #c084fc);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    margin: 0;
    line-height: 1.2;
}

.hero-subtitle {
    color: rgba(148, 163, 184, 0.9);
    font-size: 1rem;
    margin-top: 0.5rem;
}

/* 阶段进度条 */
.stage-bar {
    display: flex;
    gap: 8px;
    margin: 1rem 0;
    flex-wrap: wrap;
}

.stage-pill {
    padding: 6px 14px;
    border-radius: 20px;
    font-size: 0.78rem;
    font-weight: 500;
    border: 1px solid rgba(255,255,255,0.1);
    transition: all 0.3s ease;
}

.stage-pending  { background: rgba(71,85,105,0.4); color: #94a3b8; }
.stage-running  { background: rgba(251,191,36,0.2); color: #fbbf24; border-color: rgba(251,191,36,0.5); animation: pulse 1.5s infinite; }
.stage-done     { background: rgba(52,211,153,0.15); color: #34d399; border-color: rgba(52,211,153,0.4); }
.stage-error    { background: rgba(239,68,68,0.15); color: #f87171; border-color: rgba(239,68,68,0.4); }

@keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.6; }
}

/* 日志框 */
.log-box {
    background: rgba(0,0,0,0.4);
    border: 1px solid rgba(99,102,241,0.2);
    border-radius: 12px;
    padding: 1rem;
    font-family: 'Courier New', monospace;
    font-size: 0.82rem;
    color: #94a3b8;
    max-height: 280px;
    overflow-y: auto;
    line-height: 1.7;
}

/* 结果卡片 */
.result-card {
    background: rgba(15,15,30,0.6);
    border: 1px solid rgba(99,102,241,0.25);
    border-radius: 16px;
    padding: 1.4rem;
    margin-bottom: 1rem;
    backdrop-filter: blur(8px);
}

.result-card h4 {
    color: #a78bfa;
    font-size: 0.85rem;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    margin-bottom: 0.8rem;
}

/* Gap 标签 */
.gap-tag {
    display: inline-block;
    background: rgba(251,113,133,0.15);
    color: #fb7185;
    border: 1px solid rgba(251,113,133,0.3);
    border-radius: 8px;
    padding: 4px 10px;
    font-size: 0.82rem;
    margin: 3px;
}

/* 文献条目 */
.paper-item {
    background: rgba(30,30,50,0.5);
    border-left: 3px solid #818cf8;
    padding: 10px 14px;
    border-radius: 0 8px 8px 0;
    margin-bottom: 8px;
    font-size: 0.88rem;
}

.paper-item .title { color: #e2e8f0; font-weight: 500; }
.paper-item .meta  { color: #64748b; font-size: 0.78rem; margin-top: 2px; }

/* 侧边栏 */
[data-testid="stSidebar"] {
    background: rgba(15,15,26,0.95);
    border-right: 1px solid rgba(99,102,241,0.2);
}

[data-testid="stSidebar"] .stMarkdown h3 {
    color: #a78bfa;
    font-size: 0.82rem;
    text-transform: uppercase;
    letter-spacing: 0.1em;
}

/* 输入框 */
.stTextArea textarea {
    background: rgba(15,15,30,0.8) !important;
    border: 1px solid rgba(99,102,241,0.3) !important;
    border-radius: 12px !important;
    color: #e2e8f0 !important;
    font-size: 0.95rem !important;
}

.stTextArea textarea:focus {
    border-color: rgba(99,102,241,0.7) !important;
    box-shadow: 0 0 0 3px rgba(99,102,241,0.15) !important;
}

/* 主按钮 */
.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #6366f1, #8b5cf6) !important;
    border: none !important;
    border-radius: 12px !important;
    padding: 0.6rem 2rem !important;
    font-weight: 600 !important;
    font-size: 1rem !important;
    transition: all 0.2s ease !important;
    width: 100%;
}

.stButton > button[kind="primary"]:hover {
    transform: translateY(-1px) !important;
    box-shadow: 0 8px 25px rgba(99,102,241,0.4) !important;
}

/* 分隔线 */
hr { border-color: rgba(99,102,241,0.15) !important; }

/* 下载按钮 */
.stDownloadButton button {
    background: rgba(52,211,153,0.1) !important;
    border: 1px solid rgba(52,211,153,0.3) !important;
    color: #34d399 !important;
    border-radius: 10px !important;
    font-weight: 500 !important;
}

/* Tab 样式 */
.stTabs [data-baseweb="tab-list"] {
    background: rgba(15,15,30,0.5);
    border-radius: 12px;
    padding: 4px;
    gap: 4px;
}

.stTabs [data-baseweb="tab"] {
    border-radius: 8px;
    color: #94a3b8 !important;
    font-weight: 500;
}

.stTabs [aria-selected="true"] {
    background: rgba(99,102,241,0.3) !important;
    color: #a78bfa !important;
}

/* Metrics */
[data-testid="metric-container"] {
    background: rgba(15,15,30,0.6);
    border: 1px solid rgba(99,102,241,0.2);
    border-radius: 12px;
    padding: 0.8rem 1rem;
}

[data-testid="metric-container"] label { color: #64748b !important; }
[data-testid="metric-container"] [data-testid="stMetricValue"] { 
    color: #a78bfa !important; font-weight: 700 !important; 
}
</style>
""", unsafe_allow_html=True)

# ==========================================
# 状态初始化
# ==========================================
STAGES = [
    ("🧠", "破题规划", "planning"),
    ("🔍", "文献检索", "searching"),
    ("📦", "提取存储", "extracting"),
    ("📖", "审查分析", "reviewing"),
    ("📊", "数据流水线", "data_pipeline"),
    ("✍️",  "最终统稿", "writing"),
]

def init_state():
    defaults = {
        "running": False,
        "stage_status": {s[2]: "pending" for s in STAGES},
        "logs": [],
        "project": None,
        "error": None,
        "log_queue": None,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_state()

# ==========================================
# 工作流执行（后台线程 + 队列通信）
# ==========================================
def run_workflow_thread(idea: str, log_q: queue.Queue):
    """在独立线程中运行工作流，通过队列回传状态"""
    try:
        # 动态 patch：把 print 重定向到队列
        import builtins
        _orig_print = builtins.print
        def _q_print(*args, **kwargs):
            msg = " ".join(str(a) for a in args)
            log_q.put(("log", msg))
            _orig_print(*args, **kwargs)
        builtins.print = _q_print

        from workflow import SixAgentWorkflow
        wf = SixAgentWorkflow()

        # 阶段钩子：在工作流类里直接 monkey-patch _print_header
        _orig_header = wf._print_header
        stage_map = {
            "阶段 1": "planning",
            "阶段 2": "searching",
            "阶段 3": "extracting",
            "阶段 4": "reviewing",
            "阶段 5": "data_pipeline",
            "阶段 6": "writing",
        }
        def _q_header(title: str):
            for key, sid in stage_map.items():
                if key in title:
                    log_q.put(("stage", sid))
                    break
            _orig_header(title)
        wf._print_header = _q_header

        project = wf.run(idea)
        log_q.put(("done", project))

    except Exception as e:
        import traceback
        log_q.put(("error", f"{e}\n{traceback.format_exc()}"))
    finally:
        builtins.print = _orig_print  # type: ignore


# ==========================================
# 侧边栏
# ==========================================
with st.sidebar:
    st.markdown("### 🎓 Scholar")
    st.markdown("6-Agent 学术工作流引擎")
    st.markdown("---")

    st.markdown("### ⚙️ Agent LLM 路由")

    try:
        from config import config
        agent_llms = config.AGENT_LLMS or {}
        rows = {
            "🧠 主控":  agent_llms.get("lead_author", {}),
            "📖 审查员": agent_llms.get("reviewer", {}),
            "🕷️ 采集员": agent_llms.get("data_crawler", {}),
            "📈 分析员": agent_llms.get("data_analyst", {}),
        }
        for label, cfg in rows.items():
            provider = cfg.get("provider", "—")
            model = cfg.get("model", "—")
            short_model = model.split("/")[-1] if "/" in model else model
            st.markdown(f"**{label}**  \n`{provider}` · `{short_model}`")
    except Exception:
        st.warning("⚠️ 无法读取配置")

    st.markdown("---")
    st.markdown("### 🔑 API Key 状态")
    try:
        has_key = config.use_llm()
        if has_key:
            st.success("✅ 已配置，将使用真实 LLM")
        else:
            st.warning("⚠️ 未配置，将使用 Mock 模式")
    except Exception:
        st.error("❌ 配置读取失败")

    st.markdown("---")
    st.markdown("### 📂 历史产出")
    output_dir = Path("./output")
    if output_dir.exists():
        md_files = sorted(output_dir.glob("proj_*.md"), reverse=True)[:5]
        if md_files:
            for f in md_files:
                st.markdown(f"📄 `{f.stem}`")
        else:
            st.caption("暂无历史记录")
    else:
        st.caption("output 目录尚未创建")

    st.markdown("---")
    st.caption("Made with ❤️ · Scholar Project")


# ==========================================
# 主区域 - Hero Header
# ==========================================
st.markdown("""
<div class="hero-card">
  <div class="hero-title">🎓 Scholar · 6-Agent 学术引擎</div>
  <div class="hero-subtitle">
    输入你的研究课题，6 个 AI Agent 将协同完成文献检索 → 研究空白提炼 → 数据分析 → 论文生成的完整流程
  </div>
</div>
""", unsafe_allow_html=True)

# ==========================================
# 阶段状态展示函数
# ==========================================
def render_stage_bar(stage_status: dict):
    html_pills = '<div class="stage-bar">'
    for icon, name, sid in STAGES:
        status = stage_status.get(sid, "pending")
        css = f"stage-{status}"
        prefix = "✓ " if status == "done" else ("⟳ " if status == "running" else "")
        html_pills += f'<span class="stage-pill {css}">{icon} {prefix}{name}</span>'
    html_pills += "</div>"
    st.markdown(html_pills, unsafe_allow_html=True)


# ==========================================
# 主分区：输入 / 运行 / 结果
# ==========================================
main_col, result_col = st.columns([1, 1.3], gap="large")

with main_col:
    st.markdown("#### 💡 研究课题")
    
    idea_examples = [
        "请帮我研究 GitHub Trending 上 AI Agent 框架的发展热度，分析各框架的Star增长趋势。",
        "研究大型语言模型在学术翻译领域的应用现状与未来挑战。",
        "分析近年来 Transformer 架构在计算机视觉领域的发展与突破。",
    ]
    
    selected_example = st.selectbox(
        "📋 快速选择示例课题（或在下方自由输入）",
        options=["自定义输入..."] + idea_examples,
        index=0,
        label_visibility="collapsed"
    )
    
    default_text = "" if selected_example == "自定义输入..." else selected_example
    
    research_idea = st.text_area(
        "研究课题输入",
        value=default_text,
        placeholder="描述你的研究课题或设想，越具体越好...\n\n例如：我想研究目前 GitHub 上人工智能 Agent 框架的发展热度，\n请帮我爬取 GitHub Trending 页面并做可视化分析。",
        height=160,
        label_visibility="collapsed",
    )
    
    run_btn = st.button(
        "🚀  启动 6-Agent 研究流程",
        type="primary",
        disabled=st.session_state.running,
    )
    
    if run_btn and research_idea.strip():
        # 重置状态
        st.session_state.running = True
        st.session_state.stage_status = {s[2]: "pending" for s in STAGES}
        st.session_state.logs = []
        st.session_state.project = None
        st.session_state.error = None
        st.session_state.log_queue = queue.Queue()
        # 启动后台线程
        t = threading.Thread(
            target=run_workflow_thread,
            args=(research_idea.strip(), st.session_state.log_queue),
            daemon=True,
        )
        t.start()
        st.rerun()

    elif run_btn and not research_idea.strip():
        st.warning("⚠️ 请输入研究课题")

    # 运行中：拉取队列消息
    if st.session_state.running and st.session_state.log_queue:
        st.markdown("---")
        st.markdown("#### ⚡ 实时进度")
        
        stage_placeholder = st.empty()
        log_placeholder = st.empty()
        
        # 标记当前活跃阶段
        active_stages = [s[2] for s in STAGES if st.session_state.stage_status.get(s[2]) == "running"]
        
        # 轮询队列（最多读取一批消息）
        q = st.session_state.log_queue
        finished = False
        for _ in range(30):  # 最多读取 30 条/轮
            try:
                msg_type, payload = q.get_nowait()
                if msg_type == "log":
                    st.session_state.logs.append(payload)
                elif msg_type == "stage":
                    # 标记上一个 running 的为 done
                    for sid, status in st.session_state.stage_status.items():
                        if status == "running":
                            st.session_state.stage_status[sid] = "done"
                    st.session_state.stage_status[payload] = "running"
                elif msg_type == "done":
                    st.session_state.project = payload
                    # 标记最后阶段 done
                    for sid in st.session_state.stage_status:
                        if st.session_state.stage_status[sid] == "running":
                            st.session_state.stage_status[sid] = "done"
                    st.session_state.running = False
                    finished = True
                elif msg_type == "error":
                    st.session_state.error = payload
                    st.session_state.running = False
                    finished = True
            except queue.Empty:
                break
        
        # 渲染阶段条
        with stage_placeholder:
            render_stage_bar(st.session_state.stage_status)
        
        # 日志区
        log_text = "\n".join(st.session_state.logs[-60:])
        with log_placeholder:
            st.markdown(f'<div class="log-box">{log_text.replace(chr(10), "<br>")}</div>', unsafe_allow_html=True)
        
        if not finished:
            time.sleep(0.8)
            st.rerun()
        else:
            st.rerun()

    elif not st.session_state.running and st.session_state.stage_status.get("planning") != "pending":
        # 已完成过一次，展示阶段结果
        st.markdown("---")
        st.markdown("#### 📊 执行阶段")
        render_stage_bar(st.session_state.stage_status)
        
        if st.session_state.logs:
            with st.expander("🗒️ 查看完整运行日志", expanded=False):
                log_text = "\n".join(st.session_state.logs)
                st.markdown(f'<div class="log-box">{log_text.replace(chr(10), "<br>")}</div>', unsafe_allow_html=True)
        
        if st.session_state.error:
            st.error(f"❌ 运行失败：{st.session_state.error[:500]}")


# ==========================================
# 结果展示区
# ==========================================
with result_col:
    project = st.session_state.project

    if project is None and not st.session_state.running:
        # 空态引导界面
        st.markdown("""
        <div class="result-card" style="text-align:center; padding: 3rem 2rem;">
            <div style="font-size: 3rem; margin-bottom: 1rem;">🧪</div>
            <div style="color: #94a3b8; font-size: 0.95rem; line-height: 1.8;">
                在左侧输入研究课题并点击启动，<br>
                6 个 AI Agent 将协同为你生成完整的学术论文。
            </div>
            <br>
            <div style="display: flex; justify-content: center; gap: 12px; flex-wrap: wrap;">
                <span style="background:rgba(99,102,241,0.1); color:#818cf8; border:1px solid rgba(99,102,241,0.3); padding:6px 12px; border-radius:8px; font-size:0.8rem;">🔍 Semantic Scholar</span>
                <span style="background:rgba(139,92,246,0.1); color:#a78bfa; border:1px solid rgba(139,92,246,0.3); padding:6px 12px; border-radius:8px; font-size:0.8rem;">🤖 DeepSeek R1</span>
                <span style="background:rgba(52,211,153,0.1); color:#34d399; border:1px solid rgba(52,211,153,0.3); padding:6px 12px; border-radius:8px; font-size:0.8rem;">📦 ChromaDB RAG</span>
                <span style="background:rgba(251,191,36,0.1); color:#fbbf24; border:1px solid rgba(251,191,36,0.3); padding:6px 12px; border-radius:8px; font-size:0.8rem;">🕷️ 智能爬虫</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

    elif st.session_state.running:
        st.markdown("""
        <div class="result-card" style="text-align:center; padding: 2.5rem;">
            <div style="font-size: 2.5rem; margin-bottom:1rem; animation: pulse 1.5s infinite;">⚙️</div>
            <div style="color: #fbbf24; font-size: 1rem; font-weight: 500;">Agent 正在运行中...</div>
            <div style="color: #64748b; font-size:0.85rem; margin-top: 0.5rem;">请稍候，结果将在完成后自动显示</div>
        </div>
        """, unsafe_allow_html=True)

    elif project is not None:
        # ---- 统计指标 ----
        plan = getattr(project, "plan", {}) or {}
        review = getattr(project, "review", {}) or {}
        stored = getattr(project, "stored_papers", {}) or {}
        data_r = getattr(project, "data_results", {}) or {}
        paper = getattr(project, "final_paper", "") or ""

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("📋 大纲章节", len(plan.get("outline", [])))
        m2.metric("📚 入库文献", stored.get("zotero_count", 0))
        m3.metric("🔬 研究空白", len(review.get("research_gaps", [])))
        m4.metric("📊 数据图表", len(data_r.get("charts", [])))

        st.markdown("---")

        # ---- Tabs ----
        tab_paper, tab_outline, tab_gaps, tab_papers, tab_charts = st.tabs([
            "📄 论文全文", "📋 大纲", "🔬 研究空白", "📚 文献列表", "📈 图表"
        ])

        # Tab 1: 论文
        with tab_paper:
            if paper:
                st.markdown(paper)
                st.markdown("---")
                col_dl1, col_dl2 = st.columns(2)
                with col_dl1:
                    st.download_button(
                        label="⬇️ 下载 Markdown 论文",
                        data=paper,
                        file_name=f"{project.id}.md",
                        mime="text/markdown",
                    )
                with col_dl2:
                    log_json = json.dumps({
                        "id": project.id,
                        "idea": project.idea,
                        "plan": project.plan,
                        "review": project.review,
                        "data_results": project.data_results,
                        "logs": project.logs,
                    }, ensure_ascii=False, indent=2)
                    st.download_button(
                        label="⬇️ 下载运行日志 JSON",
                        data=log_json,
                        file_name=f"{project.id}.json",
                        mime="application/json",
                    )
            else:
                st.info("论文尚未生成")

        # Tab 2: 大纲
        with tab_outline:
            outline = plan.get("outline", [])
            if outline:
                for i, ch in enumerate(outline, 1):
                    st.markdown(f"""
                    <div class="result-card" style="padding: 0.8rem 1.2rem; margin-bottom: 0.6rem;">
                        <span style="color:#6366f1; font-weight:700; margin-right:10px;">Ch.{i}</span>
                        <span style="color:#e2e8f0;">{ch}</span>
                    </div>
                    """, unsafe_allow_html=True)
            
            queries = plan.get("search_queries", [])
            if queries:
                st.markdown("**🔍 使用的检索词**")
                st.markdown(" ".join([f'`{q}`' for q in queries]))
            
            methodology = plan.get("methodology", "")
            if methodology:
                st.markdown(f"**📐 研究方法**  \n{methodology}")

        # Tab 3: 研究空白
        with tab_gaps:
            gaps = review.get("research_gaps", [])
            memo = review.get("review_memo", "")
            if gaps:
                st.markdown("**发现的核心研究空白：**")
                for gap in gaps:
                    if gap.strip():
                        st.markdown(f"""
                        <div class="result-card" style="border-left: 3px solid #fb7185; padding: 0.8rem 1.2rem;">
                            <span style="color:#e2e8f0;">🔭 {gap}</span>
                        </div>
                        """, unsafe_allow_html=True)
            if memo:
                with st.expander("📋 查看完整审查备忘录"):
                    st.markdown(memo)

        # Tab 4: 文献列表
        with tab_papers:
            papers = getattr(project, "papers", []) or []
            if papers:
                st.markdown(f"**共检索到 {len(papers)} 篇文献：**")
                for p in papers[:30]:
                    title = p.get("title", "N/A")
                    authors = p.get("authors", [])
                    year = p.get("year", "N/A")
                    doi = p.get("doi", "")
                    citations = p.get("citations", 0)
                    auth_score = p.get("authority_score", None)
                    
                    author_str = ", ".join(authors[:3]) if authors else "—"
                    if len(authors) > 3:
                        author_str += " et al."
                    score_str = f" · ⭐ {auth_score:.2f}" if auth_score else ""
                    
                    st.markdown(f"""
                    <div class="paper-item">
                        <div class="title">{title}</div>
                        <div class="meta">{author_str} · {year} · 引用: {citations}{score_str}</div>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.info("暂无文献数据")

        # Tab 5: 图表
        with tab_charts:
            charts = data_r.get("charts", [])
            if charts:
                conclusion = data_r.get("conclusion", "")
                if conclusion:
                    st.success(f"🔑 核心结论：{conclusion}")
                for chart_path in charts:
                    if os.path.exists(chart_path):
                        st.image(chart_path, use_column_width=True)
                    else:
                        st.warning(f"图表文件不存在：{chart_path}")
            else:
                needs_data = plan.get("needs_data_analysis", False)
                if needs_data:
                    st.info("ℹ️ 数据流水线已触发，但暂无图表产出（可能为 Mock 模式）")
                else:
                    st.info("📋 本次课题为纯文献综述，未激活数据分析流水线")
