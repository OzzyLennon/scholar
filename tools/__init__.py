# ==========================================
# 工具模块初始化
# ==========================================
from .literature_search import SemanticScholarAPI, CoreAPI, LiteratureSearchManager, Paper
from .metaso_search import MetasoMCPClient, ChinesePaper
from .vector_store import VectorStoreManager, ChromaDBStore, LocalVectorStore

__all__ = [
    # 文献检索
    "SemanticScholarAPI",
    "CoreAPI", 
    "LiteratureSearchManager",
    "Paper",
    
    # 秘塔搜索
    "MetasoMCPClient",
    "ChinesePaper",

    # 向量存储
    "VectorStoreManager",
    "ChromaDBStore",
    "LocalVectorStore",
]

try:
    from .sandbox import PythonSandbox, DataAnalyzer, ExecutionResult
    __all__.extend([
        # 数据分析
        "PythonSandbox",
        "DataAnalyzer",
        "ExecutionResult"
    ])
except ImportError:
    print("⚠️ Warning: tools.sandbox module not found, some features may be disabled.")
