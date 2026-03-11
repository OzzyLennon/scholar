# ==========================================
# 配置管理 - 支持多LLM (大满贯完全体版)
# 保留了全平台接口，同时支持 6-Agent 动态路由
# ==========================================
import os
from dataclasses import dataclass
from typing import Dict, Optional
from dotenv import load_dotenv

load_dotenv()

@dataclass
class LLMConfig:
    """单个LLM配置"""
    api_key: str
    base_url: str
    model: str
    def is_available(self) -> bool:
        return bool(self.api_key)

@dataclass
class Config:
    """项目配置"""
    
    # ===== LLM API Keys (全平台火力保留) =====
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_BASE_URL: str = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
    MODEL_NAME: str = os.getenv("MODEL_NAME", "gpt-4o")
    
    DEEPSEEK_API_KEY: str = os.getenv("DEEPSEEK_API_KEY", "")
    DEEPSEEK_BASE_URL: str = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
    DEEPSEEK_KEY: str = os.getenv("DEEPSEEK_KEY", "")
    DEEPSEEK_URL: str = os.getenv("DEEPSEEK_URL", "https://api.deepseek.com/v1")
    
    SILICONFLOW_KEY: str = os.getenv("SILICONFLOW_KEY", "")
    SILICONFLOW_URL: str = os.getenv("SILICONFLOW_URL", "https://api.siliconflow.cn/v1")
    
    ARK_KEY: str = os.getenv("ARK_KEY", "")
    ARK_URL: str = os.getenv("ARK_URL", "https://ark.cn-beijing.volces.com/api/coding")
    
    TENCENT_KEY: str = os.getenv("TENCENT_KEY", "")
    TENCENT_URL: str = os.getenv("TENCENT_URL", "https://api.lkeap.cloud.tencent.com/coding/v3")
    
    # ===== 学术搜索与工具配置 =====
    SEMANTIC_SCHOLAR_API_KEY: str = os.getenv("SEMANTIC_SCHOLAR_API_KEY", "")
    CORE_API_KEY: str = os.getenv("CORE_API_KEY", "")
    METASO_API_KEY: str = os.getenv("METASO_API_KEY", "")
    
    OUTPUT_DIR: str = os.getenv("OUTPUT_DIR", "./output")
    VECTOR_DB_DIR: str = os.getenv("VECTOR_DB_DIR", "./vector_db")
    
    # 修复目录嵌套问题
    if OUTPUT_DIR == "./output/output":
        OUTPUT_DIR = "./output"
    
    MAX_SEARCH_RESULTS: int = int(os.getenv("MAX_SEARCH_RESULTS", "20"))
    SANDBOX_TIMEOUT: int = int(os.getenv("SANDBOX_TIMEOUT", "120"))
    
    AGENT_LLMS: Dict[str, dict] = None
    
    def __post_init__(self):
        # 🌟 6-Agent 动态路由分配表 (从环境变量读取，完美保留你的原版设计)
        self.AGENT_LLMS = {
            "lead_author": {
                "provider": os.getenv("AGENT_LEAD_AUTHOR_PROVIDER", "deepseek"),
                "model": os.getenv("AGENT_LEAD_AUTHOR_MODEL", "deepseek-reasoner"),
                "temperature": float(os.getenv("AGENT_LEAD_AUTHOR_TEMP", "0.7"))
            },
            "reviewer": {
                "provider": os.getenv("AGENT_REVIEWER_PROVIDER", "siliconflow"),
                "model": os.getenv("AGENT_REVIEWER_MODEL", "Pro/moonshotai/Kimi-K2.5"),
                "temperature": float(os.getenv("AGENT_REVIEWER_TEMP", "0.5"))
            },
            "data_crawler": {
                "provider": os.getenv("AGENT_CRAWLER_PROVIDER", "siliconflow"),
                "model": os.getenv("AGENT_CRAWLER_MODEL", "deepseek-ai/DeepSeek-V3.2"),
                "temperature": float(os.getenv("AGENT_CRAWLER_TEMP", "0.1"))
            },
            "data_analyst": {
                "provider": os.getenv("AGENT_ANALYST_PROVIDER", "siliconflow"),
                "model": os.getenv("AGENT_ANALYST_MODEL", "deepseek-ai/DeepSeek-V3.2"),
                "temperature": float(os.getenv("AGENT_ANALYST_TEMP", "0.1"))
            }
        }
    
    def use_llm(self) -> bool:
        """检查是否有任意平台的 API Key 存活"""
        return bool(self.OPENAI_API_KEY or self.DEEPSEEK_API_KEY or 
                   self.DEEPSEEK_KEY or self.SILICONFLOW_KEY or 
                   self.ARK_KEY or self.TENCENT_KEY)
    
    def get_llm_config(self, provider: str = None, target_model: str = None) -> Optional[LLMConfig]:
        """大满贯装配车间：支持市面上几乎所有主流平台的动态装配"""
        configs = {
            "openai": LLMConfig(
                api_key=self.OPENAI_API_KEY, 
                base_url=self.OPENAI_BASE_URL, 
                model=target_model or self.MODEL_NAME
            ),
            "deepseek": LLMConfig(
                api_key=self.DEEPSEEK_KEY or self.DEEPSEEK_API_KEY, 
                base_url=self.DEEPSEEK_BASE_URL or self.DEEPSEEK_URL, 
                model=target_model or "deepseek-chat"
            ),
            "deepseek-reasoner": LLMConfig(
                api_key=self.DEEPSEEK_KEY or self.DEEPSEEK_API_KEY, 
                base_url=self.DEEPSEEK_BASE_URL or self.DEEPSEEK_URL, 
                model=target_model or "deepseek-reasoner"
            ),
            "siliconflow": LLMConfig(
                api_key=self.SILICONFLOW_KEY, 
                base_url=self.SILICONFLOW_URL, 
                model=target_model or "deepseek-ai/DeepSeek-V3.2"
            ),
            "ark": LLMConfig(
                api_key=self.ARK_KEY, 
                base_url=self.ARK_URL, 
                model=target_model or "doubao-seed-2.0-code"
            ),
            "tencent": LLMConfig(
                api_key=self.TENCENT_KEY, 
                base_url=self.TENCENT_URL, 
                model=target_model or "doubao-seed-2.0-code"
            ),
            # 保留你原版中定义的其它特定平台预设
            "kimi": LLMConfig(
                api_key=self.ARK_KEY, 
                base_url=self.ARK_URL, 
                model=target_model or "kimi-k2.5"
            ),
            "glm": LLMConfig(
                api_key=self.ARK_KEY, 
                base_url=self.ARK_URL, 
                model=target_model or "glm-4.7"
            )
        }
        return configs.get(provider, configs.get("deepseek"))
    
    def get_agent_llm(self, agent_name: str) -> Optional[LLMConfig]:
        """为具体的 Agent 提供动态模型分发"""
        if agent_name not in self.AGENT_LLMS:
            return self.get_llm_config("deepseek")
            
        agent_config = self.AGENT_LLMS[agent_name]
        provider = agent_config.get("provider", "deepseek")
        model = agent_config.get("model", "deepseek-chat")
        
        # 兼容深思官方 R1 模型的特殊判断逻辑
        if provider == "deepseek" and "reasoner" in model:
            return self.get_llm_config(provider="deepseek-reasoner", target_model=model)
            
        # 将环境变量中的 provider 和 model 精准传递给底层装配厂
        return self.get_llm_config(provider=provider, target_model=model)

config = Config()