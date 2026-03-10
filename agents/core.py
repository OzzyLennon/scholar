# ==========================================
# Agent 模块 - 5-Agent 核心架构
# ==========================================
# 未来重构：将各个 Agent 拆分到独立文件
# - lead_author.py
# - searcher.py
# - extractor.py
# - reviewer.py
# - data_researcher.py
# ==========================================

import json
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from openai import OpenAI
from config import config
from prompts.system_prompts import (
    LEAD_AUTHOR_PLANNING_PROMPT,
    LEAD_AUTHOR_WRITING_PROMPT,
    LEAD_AUTHOR_EVALUATION_PROMPT,
    REVIEWER_GAP_ANALYSIS_PROMPT,
    DATA_RESEARCHER_CODE_GENERATION_PROMPT
)


# ==========================================
# 1. 主控 Agent (Lead Author / Orchestrator)
# ==========================================
class LeadAuthorAgent:
    """
    核心大脑 - 整个系统的中枢
    职责：破题规划 + 方向把控 + 路径决策 + 最终统稿
    使用配置中的 lead_author LLM
    """
    
    def __init__(self, client: OpenAI = None, model_name: str = None):
        # 如果没有传入 client，尝试使用配置的 LLM
        self.client = client
        self.model = model_name
        self.temperature = 0.7
        
        if client is None:
            llm_config = config.get_agent_llm("lead_author")
            if llm_config and llm_config.is_available():
                self.client = OpenAI(api_key=llm_config.api_key, base_url=llm_config.base_url)
                self.model = llm_config.model
                self.temperature = 0.7
                print(f"[🧠 主控] 使用 LLM: {llm_config.model}")
        
        # Prompts 从外部模块加载
        self.planning_prompt = LEAD_AUTHOR_PLANNING_PROMPT
        self.writing_prompt = LEAD_AUTHOR_WRITING_PROMPT
        self.evaluation_prompt = LEAD_AUTHOR_EVALUATION_PROMPT
    
    def plan(self, user_idea: str) -> Dict:
        """破题规划"""
        if not self.client:
            return self._mock_plan(user_idea)
        
        # DeepSeek 不支持 response_format，只在 OpenAI 系列使用
        use_json_format = self.model and ("gpt" in self.model or "4o" in self.model)
        
        kwargs = {
            "model": self.model,
            "temperature": self.temperature,
            "messages": [
                {"role": "system", "content": self.planning_prompt},
                {"role": "user", "content": f"我的课题设想是：{user_idea}"}
            ]
        }
        
        if use_json_format:
            kwargs["response_format"] = {"type": "json_object"}
        
        response = self.client.chat.completions.create(**kwargs)
        
        content = response.choices[0].message.content
        # 如果不是 OpenAI 模型，尝试从文本中提取 JSON
        if not use_json_format:
            import re
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                content = json_match.group()
        
        return json.loads(content)
    
    def write(self, outline: List[str], context: Dict, data_results: Dict = None) -> str:
        """最终统稿"""
        if not self.client:
            return self._mock_write(outline, context, data_results)
        
        context_str = json.dumps(context, ensure_ascii=False, indent=2)
        
        response = self.client.chat.completions.create(
            model=self.model,
            temperature=self.temperature,
            messages=[
                {"role": "system", "content": self.writing_prompt},
                {"role": "user", "content": f"大纲：{outline}\n\n素材：{context_str}\n\n请撰写完整的学术论文。"}
            ]
        )
        return response.choices[0].message.content
    
    def evaluate_search_results(self, papers: List[Dict], original_queries: List[str]) -> Dict:
        """评估检索结果，决定是否打回重搜"""
        if not self.client:
            return {"approved": True, "feedback": "Mock模式，自动通过"}
        
        papers_summary = "\n".join([f"- {p.get('title', 'N/A')}" for p in papers[:10]])
        
        # DeepSeek 不支持 response_format
        use_json_format = self.model and ("gpt" in self.model or "4o" in self.model)
        
        kwargs = {
            "model": self.model,
            "temperature": 0.3,
            "messages": [
                {"role": "system", "content": self.evaluation_prompt},
                {"role": "user", "content": f"原始关键词：{original_queries}\n\n检索结果：{papers_summary}\n\n请评估并给出反馈。"}
            ]
        }
        
        if use_json_format:
            kwargs["response_format"] = {"type": "json_object"}
        
        response = self.client.chat.completions.create(**kwargs)
        
        content = response.choices[0].message.content
        # 如果不是 OpenAI 模型，尝试从文本中提取 JSON
        if not use_json_format:
            import re
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                content = json_match.group()
        
        return json.loads(content)
    
    def _mock_plan(self, user_idea: str) -> Dict:
        return {
            "outline": ["第一章：引言", "第二章：文献综述", "第三章：研究方法", "第四章：数据分析", "第五章：结论"],
            "search_queries": ["python automation research", "academic workflow efficiency", "literature review tools"],
            "needs_data_analysis": True,
            "data_requirements": "对比传统方法与自动化方法的效率差异",
            "research_questions": ["自动化脚本能否提高文献收集效率？", "提升幅度是多少？"],
            "methodology": "实证研究 + 对比实验"
        }
    
    def _mock_write(self, outline: List[str], context: Dict, data_results: Dict = None) -> str:
        paper = f"# {outline[0] if outline else '研究论文'}\n\n"
        paper += "## 摘要\n本文研究了...\n\n"
        for section in outline[1:]:
            paper += f"## {section}\n\n"
            if "文献" in section:
                paper += f"文献综述：{context.get('review_summary', '...')}\n\n"
                paper += f"研究空白：{context.get('research_gaps', '...')}\n\n"
            elif "数据" in section and data_results:
                paper += f"数据分析：{data_results.get('conclusion', '...')}\n\n"
        paper += "\n---\n*由 Scholar 5-Agent 系统自动生成*"
        return paper


# ==========================================
# 2. 检索员 Agent (Searcher)
# ==========================================
class SearcherAgent:
    """
    基础后勤组 - 文献搜索
    只听令于主控，按指定的 Search Queries 执行检索
    支持：Semantic Scholar（英文） + 秘塔MCP（中文）
    """
    
    def __init__(self):
        self.search_history = []
        
        # 激活：Semantic Scholar API（英文文献）
        try:
            from tools.literature_search import SemanticScholarAPI
            self.search_api = SemanticScholarAPI()
            self.use_real_api = True
            print("[🔍 检索员] Semantic Scholar API 已激活")
        except Exception as e:
            print(f"[⚠️ 检索员] Semantic Scholar API 激活失败: {e}")
            self.search_api = None
            self.use_real_api = False
        
        # 激活：秘塔MCP（中文文献）
        self.metaso_client = None
        self.use_metaso = False
        try:
            from tools.metaso_search import MetasoMCPClient
            if config.METASO_API_KEY:
                self.metaso_client = MetasoMCPClient(config.METASO_API_KEY)
                self.use_metaso = True
                print("[🔍 检索员] 秘塔MCP 已激活（中文文献）")
            else:
                print("[⚠️ 检索员] 秘塔MCP 未配置 API Key")
        except Exception as e:
            print(f"[⚠️ 检索员] 秘塔MCP 激活失败: {e}")
    
    def search(self, queries: List[str], max_results: int = 20) -> List[Dict]:
        """执行文献检索（英文 + 中文）"""
        print(f"\n[🔍 检索员] 收到主控指令，检索以下关键词：{queries}")
        
        all_results = []
        
        # ========== 英文文献搜索（Semantic Scholar） ==========
        if self.use_real_api and self.search_api:
            try:
                results = self.search_api.search_multiple(queries, max_results)
                if results:
                    english_papers = [p.to_dict() for p in results]
                    all_results.extend(english_papers)
                    print(f"[🔍 检索员] 英文文献: {len(english_papers)} 篇")
            except Exception as e:
                print(f"[⚠️ 检索员] Semantic Scholar 检索失败: {e}")
        
        # ========== 中文文献搜索（秘塔MCP） ==========
        if self.use_metaso and self.metaso_client:
            try:
                # 转换查询为中文（简单处理：保留原查询，但让秘塔处理中文）
                chinese_results = self.metaso_client.search_multiple(queries, max_results // 3)
                if chinese_results:
                    chinese_papers = [p.to_dict() for p in chinese_results]
                    all_results.extend(chinese_papers)
                    print(f"[🔍 检索员] 中文文献: {len(chinese_papers)} 篇")
            except Exception as e:
                print(f"[⚠️ 检索员] 秘塔MCP 检索失败: {e}")
        
        # ========== Mock 回退 ==========
        if not all_results:
            print("[🔍 检索员] 使用 Mock 数据")
            for query in queries:
                papers = self._mock_search(query, max_results // len(queries))
                all_results.extend(papers)
        
        # 去重（基于 DOI 或 title）
        seen = set()
        unique = []
        for p in all_results:
            key = p.get('doi') or p.get('title', '')
            if key and key not in seen:
                seen.add(key)
                unique.append(p)
        
        print(f"[🔍 检索员] 检索完成，共 {len(unique)} 篇文献（去重后）")
        self.search_history.extend(queries)
        return unique
    
    def _mock_search(self, query: str, limit: int) -> List[Dict]:
        return [
            {
                "title": f"Research on {query.title()} - Paper {i}",
                "authors": ["Author A", "Author B"],
                "year": 2023 - i % 3,
                "abstract": f"Abstract for {query}...",
                "doi": f"10.1000/{hash(query + str(i)) % 10000}",
                "citations": 100 - i * 10,
                "url": f"https://example.com/paper/{i}"
            }
            for i in range(limit)
        ]


# ==========================================
# 3. 提取员 Agent (Extractor)
# ==========================================
class ExtractorAgent:
    """
    基础后勤组 - 数据提取与存储
    负责将检索到的文献清洗后存入 Zotero 和 ChromaDB 向量库
    """
    
    def __init__(self, vector_db_path: str = None):
        self.vector_db_path = vector_db_path or config.VECTOR_DB_DIR
        self.zotero_store = []  # 模拟 Zotero 存储
        
        # 激活：ChromaDB 向量库
        try:
            from tools.vector_store import VectorStoreManager
            self.vector_store = VectorStoreManager(self.vector_db_path)
            self.use_real_vector = True
            print("[📦 提取员] ChromaDB 向量库已激活")
        except Exception as e:
            print(f"[⚠️ 提取员] ChromaDB 激活失败: {e}")
            self.vector_store = None
            self.use_real_vector = False
            self.chroma_store = []   # 模拟存储
    
    def extract_and_store(self, papers: List[Dict]) -> Dict:
        """提取文献数据并存储到 Zotero 和 ChromaDB"""
        print(f"\n[📦 提取员] 收到 {len(papers)} 篇文献，开始提取与存储...")
        
        stored_count = 0
        for paper in papers:
            # 1. 清洗数据
            cleaned = self._clean_paper(paper)
            
            # 2. 存入 Zotero（模拟）
            self.zotero_store.append(cleaned)
            stored_count += 1
        
        # 3. 存入 ChromaDB 向量库
        if self.use_real_vector and self.vector_store:
            chroma_count = self.vector_store.add_papers(papers)
        else:
            # 模拟存储
            for paper in papers:
                cleaned = self._clean_paper(paper)
                self.chroma_store.append({
                    "id": cleaned["doi"],
                    "content": f"{cleaned['title']}. {cleaned['abstract']}",
                    "metadata": cleaned
                })
            chroma_count = len(self.chroma_store)
        
        print(f"[📦 提取员] 存储完成：Zotero {len(self.zotero_store)} 篇，ChromaDB {chroma_count} 条向量")
        
        return {
            "status": "success",
            "zotero_count": len(self.zotero_store),
            "chroma_count": chroma_count,
            "last_paper": self.zotero_store[-1] if self.zotero_store else None
        }
    
    def _clean_paper(self, paper: Dict) -> Dict:
        """清洗文献数据"""
        return {
            "title": paper.get("title", "").strip(),
            "authors": paper.get("authors", []),
            "year": paper.get("year", 2023),
            "abstract": paper.get("abstract", "")[:500],
            "doi": paper.get("doi", ""),
            "citations": paper.get("citations", 0),
            "url": paper.get("url", ""),
            "keywords": self._extract_keywords(paper.get("title", "") + " " + paper.get("abstract", ""))
        }
    
    def _extract_keywords(self, text: str) -> List[str]:
        """提取关键词"""
        words = text.lower().split()
        keywords = [w for w in words if len(w) > 5][:5]
        return list(set(keywords))
    
    def query_vector_db(self, query: str, top_k: int = 5) -> List[Dict]:
        """查询向量库（供审查员使用）"""
        print(f"\n[📦 提取员] 收到审查员查询：'{query}'")
        
        # 使用真实向量库
        if self.use_real_vector and self.vector_store:
            results = self.vector_store.search(query, top_k)
        else:
            # 模拟返回最近的向量
            results = self.chroma_store[:top_k]
        
        print(f"[📦 提取员] 返回 {len(results)} 条相关向量")
        return results


# ==========================================
# 4. 审查员 Agent (Reviewer)
# ==========================================
class ReviewerAgent:
    """
    文献参谋 - RAG 检索 + 研究空白分析
    在本地向量库中做 RAG，把文献填入大纲，提炼 Research Gap
    使用配置的 reviewer LLM (kimi-k2.5)
    """
    
    def __init__(self, client: OpenAI = None, extractor: ExtractorAgent = None, model_name: str = None):
        # 如果没有传入 client，尝试使用配置的 LLM
        self.client = client
        self.model = model_name
        self.temperature = 0.5
        
        if client is None:
            llm_config = config.get_agent_llm("reviewer")
            if llm_config and llm_config.is_available():
                self.client = OpenAI(api_key=llm_config.api_key, base_url=llm_config.base_url)
                self.model = llm_config.model
                self.temperature = 0.5
                print(f"[📖 审查员] 使用 LLM: {llm_config.model}")
        
        self.extractor = extractor  # 用于查询向量库
        self.gap_analysis_prompt = REVIEWER_GAP_ANALYSIS_PROMPT
    
    def review(self, outline: List[str], queries: List[str] = None) -> Dict:
        """执行文献审查"""
        print(f"\n[📖 审查员] 收到主控大纲，共 {len(outline)} 章")
        
        # 1. RAG 检索（从向量库中查询相关文献）
        rag_results = []
        if queries and self.extractor:
            for query in queries[:3]:
                results = self.extractor.query_vector_db(query, top_k=3)
                rag_results.extend(results)
        
        # 2. 分析研究空白
        gaps = self._identify_research_gaps(rag_results)
        
        # 3. 生成审查备忘录
        memo = self._generate_memo(outline, rag_results, gaps)
        
        print(f"[📖 审查员] 审查完成，发现 {len(gaps)} 个研究空白")
        
        return {
            "review_memo": memo,
            "research_gaps": gaps,
            "rag_sources": len(rag_results),
            "chapter_contents": self._distribute_to_chapters(outline, rag_results)
        }
    
    def _identify_research_gaps(self, papers: List[Dict]) -> List[str]:
        """提炼研究空白"""
        if not self.client:
            return [
                "缺乏大规模实证数据支持",
                "现有研究多为定性分析，缺乏定量研究",
                "Python 自动化工具在学术场景的应用研究较少"
            ]
        
        papers_text = "\n".join([p.get("metadata", {}).get("title", "") for p in papers[:10]])
        
        response = self.client.chat.completions.create(
            model=self.model,
            temperature=0.5,
            messages=[
                {"role": "system", "content": self.gap_analysis_prompt},
                {"role": "user", "content": papers_text}
            ]
        )
        
        gaps = response.choices[0].message.content.split("\n")
        return [g.strip("- ") for g in gaps if g.strip()][:5]
    
    def _generate_memo(self, outline: List[str], papers: List[Dict], gaps: List[str]) -> str:
        """生成审查备忘录"""
        memo = f"""## 文献审查备忘录

### 大纲结构
{chr(10).join([f"{i+1}. {ch}" for i, ch in enumerate(outline)])}

### 文献来源
共参考 {len(papers)} 篇相关文献

### 研究空白
{chr(10).join([f"- {gap}" for gap in gaps])}

### 建议
1. 重点关注研究空白中的方向
2. 结合实证数据增强说服力
"""
        return memo
    
    def _distribute_to_chapters(self, outline: List[str], papers: List[Dict]) -> Dict:
        """将文献分配到各章节"""
        distribution = {}
        for i, chapter in enumerate(outline):
            start = i * len(papers) // len(outline)
            end = (i + 1) * len(papers) // len(outline)
            distribution[chapter] = papers[start:end] if papers else []
        return distribution


# ==========================================
# 5. 数据研究员 Agent (Data Researcher)
# ==========================================
class DataResearcherAgent:
    """
    核心执行 - 动态唤醒的数据研究员
    只有当主控判定需要实证分析时才会被激活
    配备 Python 代码执行能力
    使用配置的 data_researcher LLM (doubao-seed-2.0-code)
    """
    
    def __init__(self):
        self.execution_history = []
        self.code_generation_prompt = DATA_RESEARCHER_CODE_GENERATION_PROMPT
        
        # 激活：Python 沙箱
        try:
            from tools.sandbox import DataAnalyzer
            
            # 获取配置的 LLM
            llm_client = None
            llm_config = config.get_agent_llm("data_researcher")
            if llm_config and llm_config.is_available():
                llm_client = OpenAI(api_key=llm_config.api_key, base_url=llm_config.base_url)
                print(f"[📊 数据研究员] 使用 LLM: {llm_config.model}")
            
            self.analyzer = DataAnalyzer(llm_client=llm_client)
            self.use_sandbox = True
            print("[📊 数据研究员] Python 沙箱已激活")
        except Exception as e:
            print(f"[⚠️ 数据研究员] 沙箱激活失败: {e}")
            self.analyzer = None
            self.use_sandbox = False
    
    def analyze(self, requirement: str, context: Dict = None) -> Dict:
        """执行数据分析任务"""
        print(f"\n[📊 数据研究员] 被主控唤醒！")
        print(f"[📊 数据研究员] 任务需求：{requirement}")
        
        # 使用真实沙箱
        if self.use_sandbox and self.analyzer:
            result = self.analyzer.analyze(requirement, context)
            # 格式化结果
            formatted = {
                "status": result.get('status', 'success'),
                "output": result.get('output', ''),
                "conclusion": result.get('insights', [''])[0] if result.get('insights') else '分析完成',
                "statistics": result.get('statistics', {}),
                "charts": result.get('figures', []),
                "insights": result.get('insights', [])
            }
        else:
            # Mock 结果
            formatted = {
                "status": "success",
                "requirement": requirement,
                "conclusion": "数据分析完成：自动化方法相比传统方法效率提升约 40%",
                "statistics": {
                    "sample_size": 1000,
                    "mean_improvement": 0.4,
                    "p_value": 0.001,
                    "correlation": 0.78
                },
                "charts": [],
                "insights": [
                    "自动化脚本显著提高文献收集效率",
                    "随着文献数量增加，效率提升幅度增大",
                    "建议采用混合方法（自动+人工审核）"
                ]
            }
        
        self.execution_history.append(formatted)
        print(f"[📊 数据研究员] 分析完成，生成 {len(formatted.get('charts', []))} 张图表")
        
        return formatted
    
    def _generate_mock_code(self, requirement: str) -> str:
        """生成模拟的 Python 代码"""
        return f"""# Python 数据分析代码
import pandas as pd
import matplotlib.pyplot as plt
from scipy import stats

# 加载数据
data = pd.read_csv('./data/research_data.csv')

# 数据清洗
cleaned = data.dropna()

# 统计分析
correlation = cleaned['automation_level'].corr(cleaned['efficiency'])
t_stat, p_value = stats.ttest_ind(group_a, group_b)

# 可视化
plt.figure(figsize=(10, 6))
plt.plot(x, y)
plt.savefig('./output/efficiency_comparison.png')
"""
