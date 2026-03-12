# ==========================================
# 核心 Agent 层 - 极致还原你的 500 行完整业务流
# 完美适配 V12 Config 解耦架构与 Auto-Healing
# ==========================================
import json
import re
import sys
import subprocess
import os
from typing import List, Dict, Any, Optional
from openai import OpenAI
import markdown
from xhtml2pdf import pisa

from config import config
from prompts.system_prompts import (
    LEAD_AUTHOR_PLANNING_PROMPT, 
    LEAD_AUTHOR_WRITING_PROMPT,
    LEAD_AUTHOR_EVALUATION_PROMPT,
    REVIEWER_GAP_ANALYSIS_PROMPT, 
    DATA_CRAWLER_PROMPT, 
    DATA_ANALYST_PROMPT
)

# ==========================================
# 1. 主控 Agent (Lead Author)
# ==========================================
class LeadAuthorAgent:
    def __init__(self):
        llm_config = config.get_agent_llm("lead_author")
        if llm_config and llm_config.is_available():
            self.client = OpenAI(api_key=llm_config.api_key, base_url=llm_config.base_url)
            self.model = llm_config.model
            self.temperature = llm_config.temperature 
        else:
            self.client = None

    def plan(self, idea: str) -> Dict:
        """根据课题进行顶层大纲规划 (严格返回 dict)"""
        if not self.client: 
            return {"outline": ["1. 引言", "2. 结论"], "search_queries": [idea], "needs_data_analysis": False}
        
        print("[🧠 主控] 正在进行顶层设计与学术大纲规划...")
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                temperature=self.temperature,
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": LEAD_AUTHOR_PLANNING_PROMPT},
                    {"role": "user", "content": f"请针对以下课题进行规划并返回JSON格式：\n{idea}"}
                ]
            )
            return json.loads(response.choices[0].message.content)
        except Exception as e:
            print(f"[⚠️ 主控] 规划失败: {e}")
            return {"outline": ["1. 引言", "2. 结论"], "search_queries": [idea], "needs_data_analysis": False}

    def evaluate_search_results(self, papers: List[Dict], queries: List[str]) -> Dict:
        """评估检索回来的文献质量"""
        if not self.client or not papers: 
            return {"approved": True, "feedback": "无评估反馈"}
            
        print("[🧠 主控] 正在评估检索文献的学术质量是否切题...")
        titles = [p.get("title", "") for p in papers[:10]]
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                temperature=self.temperature,
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": LEAD_AUTHOR_EVALUATION_PROMPT},
                    {"role": "user", "content": f"原始检索词：{queries}\n检索到的前10篇文献标题：\n{titles}"}
                ]
            )
            return json.loads(response.choices[0].message.content)
        except Exception as e:
            return {"approved": True, "feedback": f"评估异常默认通过: {e}"}
        
    def write(self, outline: List[str], context: Dict, data_results: Dict) -> str:
        """终极统稿：融合所有上下文撰写 Markdown 长文"""
        if not self.client: return "LLM 未配置，无法撰写最终学术报告。"
        
        print("[🧠 主控] 正在深度整合所有素材，撰写万字学术报告...")
        prompt = f"大纲结构：\n{json.dumps(outline, ensure_ascii=False)}\n\n"
        prompt += f"文献上下文与Gap分析：\n{json.dumps(context, ensure_ascii=False)}\n\n"
        
        if data_results:
            prompt += f"实证数据与图表结果：\n{json.dumps(data_results, ensure_ascii=False)}\n\n"
            
        prompt += "请严格按照上述要求撰写完整的学术论文(必须为结构化 Markdown 格式)："
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                temperature=self.temperature,
                messages=[
                    {"role": "system", "content": LEAD_AUTHOR_WRITING_PROMPT},
                    {"role": "user", "content": prompt}
                ]
            )
            content = response.choices[0].message.content
            
            # 🧹 强力清洗：去除可能的开场白 (Chatter Removal)
            # 匹配模式：开头直到第一个 Markdown 标题 (#) 之前的所有非标题文本
            # 如果开头就是标题，则不受影响
            match = re.search(r'^(.*?)(?=\n#)', content, re.DOTALL)
            if match:
                preamble = match.group(1).strip()
                # 如果前言包含 "Okay" "Here is" 等典型废话，则切除
                if any(x in preamble.lower() for x in ['okay', 'sure', 'here is', 'certainly', 'as a']):
                    content = content[len(match.group(1)):]
            
            return content.strip()
        except Exception as e:
            return f"撰写失败，异常信息: {e}"

# ==========================================
# 2. 检索员 Agent (Searcher) - 中英双擎智能路由
# ==========================================
class SearcherAgent:
    def __init__(self):
        self.search_history = []
        
        # 🌟 引擎 A：挂载英文/理工科主力 (联邦引擎: arXiv + IEEE)
        try:
            from tools.literature_search import LiteratureSearchManager
            self.search_engine = LiteratureSearchManager()
            self.use_real_api = True
            print("[🔍 检索员] 🌐 国际前沿引擎 (arXiv+IEEE) 已就绪！")
        except ImportError as e:
            print(f"[⚠️ 检索员] 真实引擎初始化失败，将回退到 Mock 模式。错误详情: {e}")
            self.search_engine = None
            self.use_real_api = False
            
        # 🌟 引擎 B：挂载中文/文科主力 (秘塔 Metaso API)
        self.use_metaso = False
        self.metaso_client = None
        try:
            from tools.metaso_search import MetasoMCPClient
            self.metaso_client = MetasoMCPClient()
            self.use_metaso = True
            print("[🔍 检索员] 🇨🇳 中文文献引擎 (Metaso 秘塔) 已就绪！")
        except Exception as e:
            print(f"[⚠️ 检索员] Metaso 客户端初始化失败: {e}")

    def search(self, queries: List[str], max_results: int = 20) -> List[Dict]:
        all_results = []
        
        # 🌟 策略升级：不再区分中英文，全量执行双源检索 (Maximizing Recall)
        # 无论是中文还是英文查询，都同时丢给“联邦引擎”和“秘塔引擎”
        # 这样能确保：
        # 1. 英文查询也能利用秘塔检索到国内的高质量综述或翻译
        # 2. 中文查询也能尝试在国际库中碰运气（虽然概率低）
        # 3. 最重要的是，完全避免了语言判断失误导致的漏搜
        
        # 1. 启动国际联邦检索 (arXiv/IEEE/Semantic Scholar)
        if self.use_real_api and self.search_engine:
            print(f"[🔍 检索员] 启动国际联邦检索 (Federated Search)...")
            try:
                # 联邦引擎内部已经处理了多源并发
                real_papers = self.search_engine.search_papers(queries, max_results)
                all_results.extend([p.to_dict() if hasattr(p, 'to_dict') else p for p in real_papers])
            except Exception as e:
                print(f"[⚠️ 检索员] 国际联邦检索异常: {e}")

        # 2. 启动秘塔中文检索 (Metaso)
        if self.use_metaso and self.metaso_client:
            print(f"[🔍 检索员] 启动秘塔深度检索 (Metaso Search)...")
            for q in queries:
                # 秘塔对单个查询的并发限制较小，但为了稳妥还是逐个搜
                metaso_papers = self._search_metaso(q, max_results // max(1, len(queries)))
                all_results.extend(metaso_papers)
        elif self.use_metaso and not self.metaso_client:
             print("[⚠️ 检索员] 秘塔引擎已启用但客户端未就绪 (可能是 Key 错误)，跳过。")
        
        # 3. 全面兜底 (Mock)
        if not all_results:
            print("[⚠️ 检索员] 所有真实引擎均未返回数据，触发 Mock 回退")
            for query in queries: 
                all_results.extend(self._mock_search(query, max_results // max(1, len(queries))))
            
        # 4. 全局去重
        seen = set()
        unique = []
        for p in all_results:
            # 优先使用 DOI，其次使用标题 (归一化)
            key = p.get('doi') or p.get('title', '').lower().strip()
            # 移除无效 key
            if not key or key == "none" or key == "":
                # 如果没有 DOI 也没有标题，这数据废了，跳过
                continue
                
            if key not in seen:
                seen.add(key)
                unique.append(p)
                
        self.search_history.extend(queries)
        print(f"[🔍 检索员] 双源检索汇总: 共 {len(all_results)} 条 -> 去重后 {len(unique)} 条")
        return unique[:max_results]

    def _search_metaso(self, query: str, limit: int) -> List[Dict]:
        if not self.metaso_client: return []
        try:
            papers = self.metaso_client.search_papers(query, limit)
            return [p.to_dict() for p in papers]
        except Exception as e:
            print(f"[⚠️ 检索员] Metaso 搜索失败: {e}")
            return []
            
    def _mock_search(self, query: str, limit: int) -> List[Dict]:
        return [{"title": f"Mock Paper on {query} {i}", "authors": ["Mock Author"], "year": 2024, "abstract": "Mock Data...", "doi": f"mock{i}", "citations": 10, "source": "Mock"} for i in range(limit)]

# ==========================================
# 3. 提取员 Agent (Extractor)
# ==========================================
class ExtractorAgent:
    def __init__(self, output_dir: str = "./output"):
        self.output_dir = output_dir
        
        if not getattr(config, 'SKIP_VECTOR_DB', False):
            try:
                from tools.vector_store import VectorStoreManager
                # 挂载真正的向量库引擎
                self.vector_store = VectorStoreManager(persist_directory=config.VECTOR_DB_DIR)
            except Exception as e:
                print(f"[⚠️ 提取员] 向量库初始化失败: {e}")
                self.vector_store = None
        else:
            self.vector_store = None

    def extract_and_store(self, papers: List[Dict]) -> Dict:
        """核心入库流：清洗并注入 ChromaDB"""
        print(f"[📥 提取员] 正在处理 {len(papers)} 篇文献的权威分与入库操作...")
        chroma_count = 0
        if self.vector_store:
            try:
                chroma_count = self.vector_store.add_papers(papers)
            except Exception as e:
                print(f"[⚠️ 提取员] 向量入库错误: {e}")
                
        return {
            "zotero_count": len(papers),  # 保留用于向 workflow 兼容汇报
            "chroma_count": chroma_count
        }

# ==========================================
# 4. 审查员 Agent (Reviewer) - 混合 RAG 版
# ==========================================
class ReviewerAgent:
    def __init__(self, extractor=None):
        # 接收外部传入的 extractor 以调用其内部的 vector_store
        self.extractor = extractor
        llm_config = config.get_agent_llm("reviewer")
        if llm_config and llm_config.is_available():
            self.client = OpenAI(api_key=llm_config.api_key, base_url=llm_config.base_url)
            self.model = llm_config.model
            self.temperature = llm_config.temperature
        else:
            self.client = None

    def review(self, outline: List[str], queries: List[str]) -> Dict:
        """从 ChromaDB 中调取上下文，进行超长文本的 Gap 分析"""
        if not self.client: 
            return {"research_gaps": [], "review_memo": "LLM 不可用", "rag_sources": 0}
            
        print("[🧐 审查员] 正在执行混合检索与系统性文献审查...")
        
        # 1. 向 ChromaDB 执行 RAG 检索
        docs = []
        if self.extractor and self.extractor.vector_store:
            for q in queries:
                results = self.extractor.vector_store.search(q, n_results=5)
                docs.extend(results)
                
        # 2. 对召回结果去重
        seen_ids = set()
        unique_docs = []
        for d in docs:
            doc_id = d.get('id')
            if doc_id not in seen_ids:
                seen_ids.add(doc_id)
                unique_docs.append(d)
        
        # 3. 拼接 RAG 上下文
        context = ""
        for i, d in enumerate(unique_docs[:15]):
            context += f"【文献{i+1}】\n{d.get('content', '')}\n\n"
            
        # 4. 丢给大模型深读
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                temperature=self.temperature,
                messages=[
                    {"role": "system", "content": REVIEWER_GAP_ANALYSIS_PROMPT},
                    {"role": "user", "content": f"当前大纲规划：{outline}\n\n参考内容：\n{context}"}
                ]
            )
            gaps_text = response.choices[0].message.content
            gaps = [g.strip() for g in gaps_text.split('\n') if g.strip() and len(g) > 5]
            
            return {
                "research_gaps": gaps,
                "review_memo": gaps_text,
                "rag_sources": len(unique_docs)
            }
        except Exception as e:
            print(f"[⚠️ 审查员] 审查失败: {e}")
            return {"research_gaps": [], "review_memo": f"Error: {e}", "rag_sources": len(unique_docs)}

# ==========================================
# 5. 采集员 Agent (Data Crawler)
# ==========================================
class DataCrawlerAgent:
    def __init__(self):
        llm_config = config.get_agent_llm("data_crawler")
        if llm_config and llm_config.is_available():
            self.client = OpenAI(api_key=llm_config.api_key, base_url=llm_config.base_url)
            self.model = llm_config.model
            self.temperature = llm_config.temperature 
        else:
            self.client = None
            
        try:
            from tools.sandbox import PythonSandbox
            self.sandbox = PythonSandbox(timeout=config.SANDBOX_TIMEOUT, output_dir=config.OUTPUT_DIR)
        except Exception: 
            self.sandbox = None

    def run(self, requirement: str) -> Dict:
        """主入口：生成代码并在沙箱中拉取数据落地 CSV"""
        if not self.client or not self.sandbox: 
            return {"success": False, "error": "LLM或沙箱引擎未配置，无法爬取"}
            
        print("[🕷️ 采集员] 正在评估抓取需求并编写 Jina 爬虫...")
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                temperature=self.temperature,
                messages=[
                    {"role": "system", "content": DATA_CRAWLER_PROMPT},
                    {"role": "user", "content": f"需求：{requirement}"}
                ]
            )
            code = response.choices[0].message.content.strip()
            
            # 代码防截断处理
            md_tick = chr(96) * 3
            if code.startswith(f"{md_tick}python"): code = code[9:]
            elif code.startswith(md_tick): code = code[3:]
            if code.endswith(md_tick): code = code[:-3]
            code = code.strip()
            
            print("[🕷️ 采集员] 爬虫已就绪，正在沙箱中静默执行网络抓取...")
            result = self.sandbox.execute(code)
            csv_path = os.path.join(config.OUTPUT_DIR, "scraped_data.csv")
            
            # 严格校验是否生成了 CSV 数据资产
            if result.success and os.path.exists(csv_path):
                return {"success": True, "csv_path": csv_path, "error": ""}
            else:
                return {"success": False, "csv_path": "", "error": result.error or "代码成功执行，但未能落地为 CSV 文件"}
                
        except Exception as e:
            return {"success": False, "error": f"网络爬取链异常: {e}"}

# ==========================================
# 6. 分析员 Agent (Data Analyst) - 满血自愈版
# ==========================================
class DataAnalystAgent:
    def __init__(self):
        self.llm_client = None
        llm_config = config.get_agent_llm("data_analyst")
        if llm_config and llm_config.is_available():
            self.llm_client = OpenAI(api_key=llm_config.api_key, base_url=llm_config.base_url)
            self.model = llm_config.model
            self.temperature = llm_config.temperature
            
        try:
            from tools.sandbox import PythonSandbox
            self.sandbox = PythonSandbox(timeout=config.SANDBOX_TIMEOUT, output_dir=config.OUTPUT_DIR)
        except Exception: 
            self.sandbox = None
        
        # 智能包名映射字典 (用于缺包拦截与自愈修复)
        self.package_map = {
            "sklearn": "scikit-learn", "bs4": "beautifulsoup4", "cv2": "opencv-python",
            "PIL": "Pillow", "yaml": "PyYAML", "statsmodels": "statsmodels",
            "seaborn": "seaborn", "scipy": "scipy"
        }

    def analyze(self, requirement: str, csv_path: str, context: Dict) -> Dict:
        """主入口：基于 CSV 执行统计检验、画图，并做错误自愈"""
        if not self.llm_client or not self.sandbox: 
            return {"status": "error", "conclusion": "分析环境缺失"}
            
        try:
            gaps = json.dumps(context.get('research_gaps', []), ensure_ascii=False)
            response = self.llm_client.chat.completions.create(
                model=self.model, 
                temperature=self.temperature, 
                messages=[
                    {"role": "system", "content": DATA_ANALYST_PROMPT},
                    {"role": "user", "content": f"关注研究空白：{gaps}\n目标数据：{csv_path}\n分析需求：{requirement}"}
                ]
            )
            
            code = response.choices[0].message.content.strip()
            md_tick = chr(96) * 3
            if code.startswith(f"{md_tick}python"): code = code[9:]
            elif code.startswith(md_tick): code = code[3:]
            if code.endswith(md_tick): code = code[:-3]
            code = code.strip()

            # 🌟 核心：Auto-Healing 自愈执行循环
            max_retries = 3
            retries = 0
            result = None
            
            while retries < max_retries:
                result = self.sandbox.execute(code)
                if result.success:
                    break
                    
                match = re.search(r"ModuleNotFoundError: No module named '([^']+)'", result.error)
                if match:
                    missing_module = match.group(1)
                    install_name = self.package_map.get(missing_module, missing_module)
                    print(f"[🔧 自动修复] 正在后台为你自动安装缺失依赖 '{install_name}'...")
                    try:
                        subprocess.run([sys.executable, "-m", "pip", "install", install_name], check=True, capture_output=True)
                        print(f"[🔧 自动修复] ✅ '{install_name}' 安装成功！重新执行沙箱代码...")
                        retries += 1
                        continue
                    except Exception as e:
                        print(f"[⚠️ 自动修复失败] 无法安装 {install_name}: {e}")
                        break
                else:
                    print(f"[⚠️ 数据研究员] 代码执行遇到非依赖错误:\n{result.error[:300]}")
                    break

            insights = [line.strip() for line in result.output.split('\n') if line.strip()] if result and result.success else []
            
            return {
                "status": "success" if (result and result.success) else "error",
                "conclusion": insights[-1] if insights else "数据科学分析完毕，详见附图。",
                "charts": result.figures if result else [],
                "error": result.error if result else "未知错误"
            }
        except Exception as e: 
            return {"status": "error", "error": str(e), "conclusion": "执行期崩溃"}