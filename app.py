"""
Scholar - 6-Agent 学术工作流引擎 · Streamlit 前端 (Refactored)
"""
import sys
import threading
import queue
import time
import streamlit as st

# 导入 UI 模块 
from ui.state import init_state, STAGES
from ui.components import load_css, render_sidebar, render_hero, render_stage_bar, render_result_area
from ui.runner import run_workflow_thread

# ==========================================
# 页面基础配置
# ==========================================
st.set_page_config(
    page_title="Scholar · 6-Agent 学术引擎",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)

# 加载全局样式
load_css("assets/style.css")

# 初始化状态
init_state()

# 侧边栏及顶栏
render_sidebar()
render_hero()

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

# 结果展示区
with result_col:
    render_result_area()
