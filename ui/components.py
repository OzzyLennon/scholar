import streamlit as st
from pathlib import Path
import json
import os
from .state import STAGES

def load_css(file_path: str):
    with open(file_path, "r", encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

def render_sidebar():
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
            from config import config
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

def render_hero():
    st.markdown("""
    <div class="hero-card">
      <div class="hero-title">🎓 Scholar · 6-Agent 学术引擎</div>
      <div class="hero-subtitle">
        输入你的研究课题，6 个 AI Agent 将协同完成文献检索 → 研究空白提炼 → 数据分析 → 论文生成的完整流程
      </div>
    </div>
    """, unsafe_allow_html=True)

def render_stage_bar(stage_status: dict):
    html_pills = '<div class="stage-bar">'
    for icon, name, sid in STAGES:
        status = stage_status.get(sid, "pending")
        css = f"stage-{status}"
        prefix = "✓ " if status == "done" else ("⟳ " if status == "running" else "")
        html_pills += f'<span class="stage-pill {css}">{icon} {prefix}{name}</span>'
    html_pills += "</div>"
    st.markdown(html_pills, unsafe_allow_html=True)

def render_result_area():
    project = st.session_state.project

    if project is None and not st.session_state.running:
        # 空态引导界面
        st.markdown("""
        <div class="result-card" style="text-align:center; padding: 4rem 2rem;">
            <div style="font-size: 3.5rem; margin-bottom: 1.5rem; animation: float 3s ease-in-out infinite;">🧪</div>
            <div style="color: #94a3b8; font-size: 1.1rem; line-height: 1.8; margin-bottom: 2rem;">
                在左侧输入研究课题并点击启动，<br>
                <span style="color: #e2e8f0; font-weight: 500;">6 个 AI Agent</span> 将协同为您生成完整的学术论文。
            </div>
            <div style="display: flex; justify-content: center; gap: 16px; flex-wrap: wrap;">
                <span class="tech-badge badge-blue">🔍 Semantic Scholar</span>
                <span class="tech-badge badge-purple">🤖 DeepSeek R1</span>
                <span class="tech-badge badge-green">📦 ChromaDB RAG</span>
                <span class="tech-badge badge-yellow">🕷️ 智能爬虫</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

    elif st.session_state.running:
        st.markdown("""
        <div class="result-card loading-card" style="text-align:center; padding: 4rem 2rem;">
            <div style="font-size: 3.5rem; margin-bottom:1.5rem; animation: spin 2s linear infinite;">⚙️</div>
            <div style="color: #fbbf24; font-size: 1.2rem; font-weight: 600; margin-bottom: 0.5rem;">Agent 正在深度思考中...</div>
            <div style="color: #64748b; font-size:0.95rem;">请稍候，研究成果将在完成后自动展现</div>
            <div class="loading-bar"></div>
        </div>
        """, unsafe_allow_html=True)

    elif project is not None:
        render_project_results(project)

def render_project_results(project):
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
                st.markdown(f'''
                <div class="result-card outline-item" style="padding: 1rem 1.5rem; margin-bottom: 0.8rem;">
                    <span style="color:#6366f1; font-weight:700; margin-right:12px; font-size: 1.1rem;">Ch.{i}</span>
                    <span style="color:#e2e8f0; font-size: 1.05rem;">{ch}</span>
                </div>
                ''', unsafe_allow_html=True)
        
        queries = plan.get("search_queries", [])
        if queries:
            st.markdown('<div class="section-title">🔍 使用的检索词</div>', unsafe_allow_html=True)
            st.markdown(" ".join([f'`{q}`' for q in queries]))
        
        methodology = plan.get("methodology", "")
        if methodology:
            st.markdown('<div class="section-title" style="margin-top: 1.5rem;">📐 研究方法</div>', unsafe_allow_html=True)
            st.markdown(methodology)

    # Tab 3: 研究空白
    with tab_gaps:
        gaps = review.get("research_gaps", [])
        memo = review.get("review_memo", "")
        if gaps:
            st.markdown('<div class="section-title">发现的核心研究空白：</div>', unsafe_allow_html=True)
            for gap in gaps:
                if gap.strip():
                    st.markdown(f'''
                    <div class="result-card gap-card">
                        <span style="color:#fb7185; margin-right: 8px;">🔭</span>
                        <span style="color:#e2e8f0;">{gap}</span>
                    </div>
                    ''', unsafe_allow_html=True)
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
                
                st.markdown(f'''
                <div class="paper-item hover-effect">
                    <div class="title">{title}</div>
                    <div class="meta">{author_str} · <span style="color: #a78bfa">{year}</span> · 引用: <span style="color: #34d399">{citations}</span>{score_str}</div>
                </div>
                ''', unsafe_allow_html=True)
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
