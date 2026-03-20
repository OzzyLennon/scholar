# ==========================================
# 核心配置模块 - 支持多 LLM 动态路由与资源池
# ==========================================
import os
from dataclasses import dataclass
from typing import Dict, Optional
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

@dataclass
class LLMConfig:
    """单个大模型运行配置"""
    api_key: str
    base_url: str
    model: str
    temperature: float = 0.5
    
    def is_available(self) -> bool:
        return bool(self.api_key)

class ConfigManager:
    """全局配置与模型路由管理器"""
    
    def __init__(self):
        # ==========================================
        # 1. 基础系统配置
        # ==========================================
        self.OUTPUT_DIR = os.getenv("OUTPUT_DIR", "./output")
        self.VECTOR_DB_DIR = os.getenv("VECTOR_DB_DIR", "./vector_db")
        self.MAX_SEARCH_RESULTS = int(os.getenv("MAX_SEARCH_RESULTS", "20"))
        self.SANDBOX_TIMEOUT = int(os.getenv("SANDBOX_TIMEOUT", "120"))
        
        # 修复可能的目录嵌套问题（处理"./output/output"等重复路径）
        # 注意：如果环境变量错误地设置为"./output/output"，这里进行修正
        original_dir = self.OUTPUT_DIR
        if self.OUTPUT_DIR.endswith("/output/output"):
            # 移除多余的"/output"
            self.OUTPUT_DIR = self.OUTPUT_DIR[:-7]  # 移除最后的"/output"
            print(f"[Config] 修复输出目录路径: {original_dir} -> {self.OUTPUT_DIR}")
        elif self.OUTPUT_DIR == "./output/output":
            self.OUTPUT_DIR = "./output"
            print(f"[Config] 修复输出目录路径: {original_dir} -> {self.OUTPUT_DIR}")

        os.makedirs(self.OUTPUT_DIR, exist_ok=True)
            
        # ==========================================
        # 2. 学术数据库 API Keys
        # ==========================================
        self.IEEE_API_KEY = os.getenv("IEEE_API_KEY", "")
        self.SEMANTIC_SCHOLAR_API_KEY = os.getenv("SEMANTIC_SCHOLAR_API_KEY", "")
        self.CORE_API_KEY = os.getenv("CORE_API_KEY", "")
        
        # ==========================================
        # 3. 大模型资源池 (Provider Registry)
        # ==========================================
        self.providers = {
            "openai": {
                "key": os.getenv("OPENAI_API_KEY", ""),
                "url": os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
            },
            "deepseek": {
                "key": os.getenv("DEEPSEEK_KEY", ""),
                "url": "https://api.deepseek.com/v1"
            },
            "siliconflow": {
                "key": os.getenv("SILICONFLOW_KEY", ""),
                "url": "https://api.siliconflow.cn/v1"
            },
            "metaso": {
                "key": os.getenv("METASO_API_KEY", ""),
                "url": "https://api.metaso.cn/v1"
            }
        }
        
        # ==========================================
        # 4. Agent 路由表 (从 .env 动态读取)
        # ==========================================
        self.agent_routes = {
            "lead_author": {
                "provider": os.getenv("AGENT_LEAD_AUTHOR_PROVIDER", "deepseek"),
                "model": os.getenv("AGENT_LEAD_AUTHOR_MODEL", "deepseek-reasoner"),
                "temp": float(os.getenv("AGENT_LEAD_AUTHOR_TEMP", "0.7"))
            },
            "reviewer": {
                "provider": os.getenv("AGENT_REVIEWER_PROVIDER", "siliconflow"),
                "model": os.getenv("AGENT_REVIEWER_MODEL", "Pro/moonshotai/Kimi-K2.5"),
                "temp": float(os.getenv("AGENT_REVIEWER_TEMP", "0.5"))
            },
            "data_crawler": {
                "provider": os.getenv("AGENT_CRAWLER_PROVIDER", "deepseek"),
                "model": os.getenv("AGENT_CRAWLER_MODEL", "deepseek-chat"),
                "temp": float(os.getenv("AGENT_CRAWLER_TEMP", "0.1"))
            },
            "data_analyst": {
                "provider": os.getenv("AGENT_DATA_PROVIDER", "deepseek"),
                "model": os.getenv("AGENT_DATA_MODEL", "deepseek-chat"),
                "temp": float(os.getenv("AGENT_DATA_TEMP", "0.1"))
            },
            # 搜索员专属路由 (中英双擎中的中文主力)
            "searcher": {
                "provider": "metaso",  # 强绑定秘塔
                "model": "metaso-search",
                "temp": 0.1
            }
        }

    def get_agent_llm(self, agent_name: str) -> Optional[LLMConfig]:
        """核心装配厂：根据 Agent 名字，返回组装好的 LLM 配置"""
        route = self.agent_routes.get(agent_name)
        if not route:
            # 如果请求了未定义的 Agent，默认走 DeepSeek
            route = {"provider": "deepseek", "model": "deepseek-chat", "temp": 0.5}
            
        provider_name = route["provider"]
        provider_info = self.providers.get(provider_name)
        
        # 如果对应的外包服务商没有配 Key，直接返回 None，让业务层自己决定是否 Mock
        if not provider_info or not provider_info["key"]:
            return None
            
        return LLMConfig(
            api_key=provider_info["key"],
            base_url=provider_info["url"],
            model=route["model"],
            temperature=route["temp"]
        )
    
    def use_llm(self) -> bool:
        """检查资源池中是否有任意一家的 API Key 存活"""
        # 遍历所有的服务商，只要有一个配了 Key，就放行
        for provider_name, provider_info in self.providers.items():
            if provider_info.get("key"):
                return True
        return False

# 实例化全局单例
config = ConfigManager()