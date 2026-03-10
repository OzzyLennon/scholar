# ==========================================
# 配置管理 - 支持多LLM
# ==========================================
import os
from dataclasses import dataclass
from typing import Dict, Optional
from dotenv import load_dotenv

# 加载 .env 文件
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
    
    # ===== 主LLM配置（兼容旧版）=====
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_BASE_URL: str = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
    MODEL_NAME: str = os.getenv("MODEL_NAME", "gpt-4o")
    
    # DeepSeek（从 signal_config.yaml 发现）
    DEEPSEEK_API_KEY: str = os.getenv("DEEPSEEK_API_KEY", "")
    DEEPSEEK_BASE_URL: str = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
    
    # ===== 多LLM配置（不同Agent用不同模型）=====
    
    # DeepSeek (主配置)
    DEEPSEEK_KEY: str = os.getenv("DEEPSEEK_KEY", "")
    DEEPSEEK_URL: str = "https://api.deepseek.com/v1"
    
    # SiliconFlow (DeepSeek V3.2)
    SILICONFLOW_KEY: str = os.getenv("SILICONFLOW_KEY", "")
    SILICONFLOW_URL: str = "https://api.siliconflow.cn/v1"
    
    # ARK (豆包/火山引擎)
    ARK_KEY: str = os.getenv("ARK_KEY", "")
    ARK_URL: str = "https://ark.cn-beijing.volces.com/api/coding"
    
    # Tencent Coding
    TENCENT_KEY: str = os.getenv("TENCENT_KEY", "")
    TENCENT_URL: str = "https://api.lkeap.cloud.tencent.com/coding/v3"
    
    # ===== 学术搜索配置 =====
    SEMANTIC_SCHOLAR_API_KEY: str = os.getenv("SEMANTIC_SCHOLAR_API_KEY", "")
    CORE_API_KEY: str = os.getenv("CORE_API_KEY", "")
    
    # ===== 秘塔MCP配置（中文文献） =====
    METASO_API_KEY: str = os.getenv("METASO_API_KEY", "")
    
    # ===== 输出配置 =====
    OUTPUT_DIR: str = os.getenv("OUTPUT_DIR", "./output")
    VECTOR_DB_DIR: str = os.getenv("VECTOR_DB_DIR", "./vector_db")
    
    # 修复目录嵌套问题
    if OUTPUT_DIR == "./output/output":
        OUTPUT_DIR = "./output"
    
    # ===== 搜索配置 =====
    MAX_SEARCH_RESULTS: int = int(os.getenv("MAX_SEARCH_RESULTS", "20"))
    
    # ===== Agent LLM分配配置 =====
    # 不同Agent可以配置不同的LLM
    AGENT_LLMS: Dict[str, str] = None
    
    def __post_init__(self):
        # Agent-LLM 映射配置（从环境变量读取）
        self.AGENT_LLMS = {
            # 主控(LeadAuthor)：规划+决策
            "lead_author": {
                "provider": os.getenv("AGENT_LEAD_AUTHOR_PROVIDER", "deepseek"),
                "model": os.getenv("AGENT_LEAD_AUTHOR_MODEL", "deepseek-reasoner"),
                "temperature": float(os.getenv("AGENT_LEAD_AUTHOR_TEMP", "0.7"))
            },
            # 审查员(Reviewer)：文献综述+Gap分析
            "reviewer": {
                "provider": os.getenv("AGENT_REVIEWER_PROVIDER", "deepseek"),
                "model": os.getenv("AGENT_REVIEWER_MODEL", "deepseek-reasoner"),
                "temperature": float(os.getenv("AGENT_REVIEWER_TEMP", "0.5"))
            },
            # 数据研究员(DataResearcher)：代码生成
            "data_researcher": {
                "provider": os.getenv("AGENT_DATA_PROVIDER", "tencent"),
                "model": os.getenv("AGENT_DATA_MODEL", "doubao-seed-2.0-code"),
                "temperature": float(os.getenv("AGENT_DATA_TEMP", "0.3"))
            }
        }
    
    # ===== 沙箱配置 =====
    SANDBOX_TIMEOUT: int = int(os.getenv("SANDBOX_TIMEOUT", "120"))
    
    # ===== 便捷方法 =====
    def use_llm(self) -> bool:
        """检查是否配置了任意 LLM"""
        return bool(self.OPENAI_API_KEY or self.DEEPSEEK_API_KEY or 
                   self.DEEPSEEK_KEY or self.SILICONFLOW_KEY or 
                   self.ARK_KEY or self.TENCENT_KEY)
    
    def get_llm_config(self, provider: str = None) -> Optional[LLMConfig]:
        """获取指定Provider的LLM配置"""
        configs = {
            "openai": LLMConfig(
                api_key=self.OPENAI_API_KEY,
                base_url=self.OPENAI_BASE_URL,
                model=self.MODEL_NAME
            ),
            "deepseek": LLMConfig(
                api_key=self.DEEPSEEK_KEY or self.DEEPSEEK_API_KEY,
                base_url=self.DEEPSEEK_URL,
                model="deepseek-chat"
            ),
            "deepseek-reasoner": LLMConfig(
                api_key=self.DEEPSEEK_KEY or self.DEEPSEEK_API_KEY,
                base_url=self.DEEPSEEK_URL,
                model="deepseek-reasoner"
            ),
            "siliconflow": LLMConfig(
                api_key=self.SILICONFLOW_KEY,
                base_url=self.SILICONFLOW_URL,
                model="deepseek-ai/DeepSeek-V3.2"
            ),
            "ark": LLMConfig(
                api_key=self.ARK_KEY,
                base_url=self.ARK_URL,
                model="doubao-seed-2.0-code"
            ),
            "tencent": LLMConfig(
                api_key=self.TENCENT_KEY,
                base_url=self.TENCENT_URL,
                model="doubao-seed-2.0-code"
            ),
            "kimi": LLMConfig(
                api_key=self.ARK_KEY,
                base_url=self.ARK_URL,
                model="kimi-k2.5"
            ),
            "glm": LLMConfig(
                api_key=self.ARK_KEY,
                base_url=self.ARK_URL,
                model="glm-4.7"
            )
        }
        
        if provider and provider in configs:
            return configs[provider]
        
        # 默认返回 DeepSeek
        return configs.get("deepseek")
    
    def get_agent_llm(self, agent_name: str) -> Optional[LLMConfig]:
        """获取指定Agent应该使用的LLM配置"""
        if agent_name not in self.AGENT_LLMS:
            return self.get_llm_config("deepseek")
        
        agent_config = self.AGENT_LLMS[agent_name]
        provider = agent_config.get("provider", "deepseek")
        
        # 特殊处理模型名
        model = agent_config.get("model", "deepseek-chat")
        
        # 根据provider返回对应配置
        configs = {
            "deepseek": self.get_llm_config("deepseek-reasoner") if "reasoner" in model else self.get_llm_config("deepseek"),
            "siliconflow": self.get_llm_config("siliconflow"),
            "ark": LLMConfig(
                api_key=self.ARK_KEY,
                base_url=self.ARK_URL,
                model=model
            ),
            "tencent": LLMConfig(
                api_key=self.TENCENT_KEY,
                base_url=self.TENCENT_URL,
                model=model
            )
        }
        
        return configs.get(provider, self.get_llm_config("deepseek"))


# 创建全局配置实例
config = Config()
