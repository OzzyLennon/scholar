import streamlit as st

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
