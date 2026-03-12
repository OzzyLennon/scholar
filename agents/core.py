# ==========================================
# Agent 模块 - 6-Agent 核心架构 (究极完全体)
# 融合了：原版数据清洗、Memo生成、完善的Mock回退 + 独立双子星
# ==========================================

import json
import os
import re
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from openai import OpenAI
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
    def __init__(self, client: OpenAI = None, model_name: str = None):
        self.client = client
        self.model = model_name
        self.temperature = 0.7
        
        if client is None:
            llm_config = config.get_agent_llm("lead_author")
            if llm_config and llm_config.is_available():
                self.client = OpenAI(api_key=llm_config.api_key, base_url=llm_config.base_url)
                self.model = llm_config.model
                self.temperature = config.AGENT_LLMS["lead_author"]["temperature"]
                print(f"[🧠 主控] 使用 LLM: {self.model}")
        
        self.planning_prompt = LEAD_AUTHOR_PLANNING_PROMPT
        self.writing_prompt = LEAD_AUTHOR_WRITING_PROMPT
        self.evaluation_prompt = LEAD_AUTHOR_EVALUATION_PROMPT
    
    def plan(self, user_idea: str) -> Dict:
        if not self.client:
            return self._mock_plan(user_idea)
        
        use_json_format = self.model and ("gpt" in self.model or "4o" in self.model)
        kwargs = {
            "model": self.model,
            "temperature": self.temperature,
            "messages": [
                {"role": "system", "content": self.planning_prompt},
                {"role": "user", "content": f"我的课题设想是：{user_idea}"}
            ]
        }
        if use_json_format: kwargs["response_format"] = {"type": "json_object"}
        
        response = self.client.chat.completions.create(**kwargs)
        content = response.choices[0].message.content
        
        if not use_json_format:
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match: content = json_match.group()
        return json.loads(content)
    
    def write(self, outline: List[str], context: Dict, data_results: Dict = None) -> str:
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
        if not self.client:
            return {"approved": True, "feedback": "Mock模式，自动通过"}
        
        papers_summary = "\n".join([f"- {p.get('title', 'N/A')}" for p in papers[:10]])
        use_json_format = self.model and ("gpt" in self.model or "4o" in self.model)
        
        kwargs = {
            "model": self.model, "temperature": 0.3,
            "messages": [
                {"role": "system", "content": self.evaluation_prompt},
                {"role": "user", "content": f"原始关键词：{original_queries}\n\n检索结果：{papers_summary}\n\n请评估并给出反馈。"}
            ]
        }
        if use_json_format: kwargs["response_format"] = {"type": "json_object"}
        
        response = self.client.chat.completions.create(**kwargs)
        content = response.choices[0].message.content
        if not use_json_format:
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match: content = json_match.group()
        return json.loads(content)
    
    def _mock_plan(self, user_idea: str) -> Dict:
        return {
            "outline": ["第一章：引言", "第二章：文献综述", "第三章：研究方法", "第四章：实证与数据分析", "第五章：结论"],
            "search_queries": ["python automation research", "academic workflow efficiency"],
            "needs_data_analysis": True,
            "data_requirements": "对比传统方法与自动化方法的效率差异",
            "research_questions": ["自动化脚本能否提高效率？", "提升幅度是多少？"],
            "methodology": "实证研究 + 对比实验"
        }
    
    def _mock_write(self, outline: List[str], context: Dict, data_results: Dict = None) -> str:
        paper = f"# {outline[0] if outline else '研究论文'}\n\n## 摘要\n本文研究了相关自动化技术...\n\n"
        for section in outline[1:]:
            paper += f"## {section}\n\n"
            if "文献" in section:
                paper += f"文献综述：{context.get('review_summary', '...')}\n\n"
            elif "数据" in section and data_results:
                paper += f"数据分析结论：{data_results.get('conclusion', '...')}\n\n"
        paper += "\n---\n*由 Scholar 6-Agent 系统自动生成*"
        return paper

# ==========================================
# 2. 检索员 Agent (Searcher) - 中英双擎智能路由版
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
        except ImportError:
            self.search_engine = None
            self.use_real_api = False
            print("[⚠️ 检索员] 找不到 LiteratureSearchManager，将退回纯 Mock 模式！")
            
        # 🌟 引擎 B：挂载中文/文科主力 (秘塔 Metaso API)
        self.use_metaso = False
        self.metaso_client = None
        import config # 确保加载了配置
        metaso_config = config.get_agent_llm("searcher") 
        if metaso_config and metaso_config.is_available():
            try:
                from openai import OpenAI
                self.metaso_client = OpenAI(
                    api_key=metaso_config.api_key, 
                    base_url=metaso_config.base_url
                )
                self.metaso_model = metaso_config.model
                self.use_metaso = True
                print("[🔍 检索员] 🇨🇳 中文文献引擎 (Metaso 秘塔) 已就绪！")
            except Exception as e:
                print(f"[⚠️ 检索员] 秘塔 API 挂载失败: {e}")

    def search(self, queries: List[str], max_results: int = 20) -> List[Dict]:
        all_results = []
        
        # 🌟 核心科技：中英文智能语言分流 (Language-Aware Routing)
        import re
        zh_queries = []
        en_queries = []
        for q in queries:
            if re.search(r'[\u4e00-\u9fff]', q):  # 只要包含哪怕一个汉字，就归为中文检索
                zh_queries.append(q)
            else:
                en_queries.append(q)
        
        # 1. 纯英文查询 -> 走 IEEE/arXiv 国际学术库
        if en_queries and self.use_real_api and self.search_engine:
            print(f"[🔍 检索员] 识别到英文 Query，启动国际联邦检索...")
            try:
                real_papers = self.search_engine.search_papers(en_queries, max_results)
                all_results.extend([p.to_dict() if hasattr(p, 'to_dict') else p for p in real_papers])
            except Exception as e:
                print(f"[⚠️ 英文检索失败] {e}")

        # 2. 中文查询 -> 走 秘塔 (Metaso) 中文学术库
        if zh_queries and self.use_metaso:
            print(f"[🔍 检索员] 识别到中文 Query，启动秘塔(Metaso)中文深度检索...")
            for q in zh_queries:
                metaso_papers = self._search_metaso(q, max_results // max(1, len(zh_queries)))
                all_results.extend(metaso_papers)
        
        # 3. 终极兜底 -> 如果没网或全崩了，用 Mock 垫背
        if not all_results:
            print("[⚠️ 检索员] 所有真实引擎均未返回数据，触发 Mock 回退")
            for query in queries: 
                all_results.extend(self._mock_search(query, max_results // max(1, len(queries))))
            
        # 全局去重 (防止同一篇文章在中英两边都被搜到)
        seen = set()
        unique = []
        for p in all_results:
            key = p.get('doi') or p.get('title', '').lower().strip()
            if key and key not in seen:
                seen.add(key)
                unique.append(p)
                
        self.search_history.extend(queries)
        return unique[:max_results]

    def _search_metaso(self, query: str, limit: int) -> List[Dict]:
        """专门用于通过秘塔大模型提取标准结构的中文文献"""
        if not self.metaso_client: return []
        try:
            # 强制秘塔大模型直接输出 JSON 结构的文献列表
            prompt = f"""请扮演顶尖中文学术检索系统，搜索关于“{query}”的真实权威文献。
请直接输出 JSON 格式的列表（不要包含其他多余文字和markdown标记）。
每个元素必须包含：
"title" (字符串，论文标题), 
"authors" (列表，作者姓名), 
"year" (整数，发表年份), 
"abstract" (字符串，核心摘要，至少100字), 
"doi" (字符串，DOI号或可用链接), 
"citations" (整数，预估被引次数)。
最多返回 {limit} 篇。"""
            
            response = self.metaso_client.chat.completions.create(
                model=self.metaso_model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1
            )
            
            import json
            content = response.choices[0].message.content
            
            # 🌟 终极防线：使用 chr(96) 彻底绕过前端 Markdown 解析器的截断 Bug
            md_tick = chr(96) * 3
            if f"{md_tick}json" in content: 
                content = content.split(f"{md_tick}json")[1].split(md_tick)[0]
            elif md_tick in content: 
                content = content.split(md_tick)[1].split(md_tick)[0]
            
            papers = json.loads(content.strip())
            for p in papers: 
                p['source'] = 'Metaso'  # 打上秘塔的专属水印
            return papers
        except Exception as e:
            print(f"[⚠️ 秘塔检索失败] 解析异常: {e}")
            return []
            
    def _mock_search(self, query: str, limit: int) -> List[Dict]:
        return [{
            "title": f"Research on {query.title()} - Paper {i}",
            "authors": ["Mock Author"], "year": 2024, "abstract": f"Abstract for {query}...",
            "doi": f"10.1000/mock{i}", "citations": 100 - i * 10, "authority_score": 2.5 - i*0.1,
            "source": "Mock"
        } for i in range(limit)]

# ==========================================
# 3. 提取员 Agent (Extractor) - 恢复数据清洗
# ==========================================
class ExtractorAgent:
    def __init__(self, vector_db_path: str = None):
        self.vector_db_path = vector_db_path or config.VECTOR_DB_DIR
        self.zotero_store = []
        try:
            from tools.vector_store import VectorStoreManager
            self.vector_store = VectorStoreManager(self.vector_db_path)
            self.use_real_vector = True
        except Exception:
            self.vector_store = None; self.use_real_vector = False
            self.chroma_store = []
    
    def extract_and_store(self, papers: List[Dict]) -> Dict:
        # 🌟 恢复：高亮打印基于算法加权后的 TOP3 权威文献
        sorted_papers = sorted(papers, key=lambda x: x.get('authority_score', 0.0), reverse=True)
        if sorted_papers:
            print("  🏆 核心权威文献 TOP 3 (基于 Citation Velocity 算法加权):")
            for i, p in enumerate(sorted_papers[:3]):
                score = p.get('authority_score', 1.0)
                title = p.get('title', '')[:45]
                print(f"    {i+1}. [{score:.2f} 权重] {title}... (引用:{p.get('citations', 0)}, 年份:{p.get('year', 'N/A')})")

        stored_count = 0
        cleaned_papers = []
        for paper in papers:
            # 🌟 恢复：极其重要的数据清洗工序
            cleaned = self._clean_paper(paper)
            self.zotero_store.append(cleaned)
            cleaned_papers.append(cleaned)
            stored_count += 1
            
        if self.use_real_vector and self.vector_store:
            chroma_count = self.vector_store.add_papers(cleaned_papers)
        else:
            for cleaned in cleaned_papers:
                self.chroma_store.append({
                    "id": cleaned.get("doi", ""),
                    "content": f"{cleaned['title']}. {cleaned['abstract']}",
                    "metadata": cleaned
                })
            chroma_count = len(self.chroma_store)
            
        return {"status": "success", "zotero_count": len(self.zotero_store), "chroma_count": chroma_count}
    
    def _clean_paper(self, paper: Dict) -> Dict:
        """恢复原版的数据清洗：对齐字段并提取关键字"""
        return {
            "title": paper.get("title", "").strip(),
            "authors": paper.get("authors", []),
            "year": paper.get("year", 2023),
            "abstract": paper.get("abstract", "")[:600],
            "doi": paper.get("doi", ""),
            "citations": paper.get("citations", 0),
            "authority_score": paper.get("authority_score", 1.0),
            "keywords": self._extract_keywords(paper.get("title", "") + " " + paper.get("abstract", ""))
        }
    
    def _extract_keywords(self, text: str) -> List[str]:
        """恢复原版的 NLP 词频提取"""
        words = text.lower().split()
        keywords = [w for w in words if len(w) > 5][:5]
        return list(set(keywords))
    
    def query_vector_db(self, query: str, top_k: int = 5) -> List[Dict]:
        if self.use_real_vector and self.vector_store:
            return self.vector_store.search(query, top_k)
        return self.chroma_store[:top_k]

# ==========================================
# 4. 审查员 Agent (Reviewer) - 恢复报告生成器
# ==========================================
class ReviewerAgent:
    def __init__(self, client: OpenAI = None, extractor: ExtractorAgent = None, model_name: str = None):
        self.client = client
        self.model = model_name
        if client is None:
            llm_config = config.get_agent_llm("reviewer")
            if llm_config and llm_config.is_available():
                self.client = OpenAI(api_key=llm_config.api_key, base_url=llm_config.base_url)
                self.model = llm_config.model
        self.extractor = extractor
        self.gap_analysis_prompt = REVIEWER_GAP_ANALYSIS_PROMPT
    
    def review(self, outline: List[str], queries: List[str] = None) -> Dict:
        rag_results = []
        if queries and self.extractor:
            for query in queries[:3]: rag_results.extend(self.extractor.query_vector_db(query, top_k=3))
            
        gaps = self._identify_research_gaps(rag_results)
        
        # 🌟 恢复：完整的 Markdown 备忘录生成器
        memo = self._generate_memo(outline, rag_results, gaps)
        
        return {
            "review_memo": memo,
            "research_gaps": gaps,
            "rag_sources": len(rag_results),
            "chapter_contents": self._distribute_to_chapters(outline, rag_results) # 🌟 恢复章节精准分发
        }
        
    def _identify_research_gaps(self, papers: List[Dict]) -> List[str]:
        if not self.client: return ["缺乏最新的定量研究模型", "现有应用场景过于单一"]
        papers_text = "\n".join([p.get("metadata", {}).get("title", "") for p in papers[:10]])
        response = self.client.chat.completions.create(
            model=self.model, temperature=0.5,
            messages=[
                {"role": "system", "content": self.gap_analysis_prompt},
                {"role": "user", "content": f"基于以下权威文献集合寻找研究空白：\n{papers_text}"}
            ]
        )
        gaps = response.choices[0].message.content.split("\n")
        return [g.strip("- *") for g in gaps if g.strip()][:5]

    def _generate_memo(self, outline: List[str], papers: List[Dict], gaps: List[str]) -> str:
        memo = f"""## 文献审查备忘录\n\n### 大纲结构\n{chr(10).join([f"{i+1}. {ch}" for i, ch in enumerate(outline)])}\n\n### 文献来源\n共参考 {len(papers)} 篇高权重权威文献\n\n### 研究空白 (Research Gaps)\n{chr(10).join([f"- {gap}" for gap in gaps])}\n\n### 综述建议\n优先侧重上述研究空白，并在实证环节予以回应。\n"""
        return memo
        
    def _distribute_to_chapters(self, outline: List[str], papers: List[Dict]) -> Dict:
        distribution = {}
        for i, chapter in enumerate(outline):
            start = i * len(papers) // max(1, len(outline))
            end = (i + 1) * len(papers) // max(1, len(outline))
            distribution[chapter] = papers[start:end] if papers else []
        return distribution

# ==========================================
# 5. 采集员 Agent (Data Crawler) - 强解耦双子星
# ==========================================
class DataCrawlerAgent:
    def __init__(self):
        self.llm_client = None
        llm_config = config.get_agent_llm("data_crawler")
        if llm_config and llm_config.is_available():
            self.llm_client = OpenAI(api_key=llm_config.api_key, base_url=llm_config.base_url)
            self.model = llm_config.model
        try:
            from tools.sandbox import PythonSandbox
            self.sandbox = PythonSandbox(timeout=config.SANDBOX_TIMEOUT, output_dir=config.OUTPUT_DIR)
        except Exception: self.sandbox = None

    def run(self, requirement: str) -> Dict:
        if not self.llm_client or not self.sandbox: return {"success": False, "error": "依赖缺失"}
        try:
            response = self.llm_client.chat.completions.create(
                model=self.model, temperature=config.AGENT_LLMS["data_crawler"]["temperature"],
                messages=[{"role": "system", "content": DATA_CRAWLER_PROMPT}, {"role": "user", "content": requirement}]
            )
            code = re.sub(r"^```python\s*|^```\s*|```$", "", response.choices[0].message.content, flags=re.MULTILINE).strip()
            result = self.sandbox.execute(code)
            csv_path = f"{config.OUTPUT_DIR}/scraped_data.csv"
            success = result.success and os.path.exists(csv_path)
            return {"success": success, "csv_path": csv_path, "output": result.output, "error": result.error}
        except Exception as e: return {"success": False, "error": str(e)}

# ==========================================
# 6. 分析员 Agent (Data Analyst) - 强解耦双子星
# ==========================================
class DataAnalystAgent:
    def __init__(self):
        self.llm_client = None
        llm_config = config.get_agent_llm("data_analyst")
        if llm_config and llm_config.is_available():
            self.llm_client = OpenAI(api_key=llm_config.api_key, base_url=llm_config.base_url)
            self.model = llm_config.model
        try:
            from tools.sandbox import PythonSandbox
            self.sandbox = PythonSandbox(timeout=config.SANDBOX_TIMEOUT, output_dir=config.OUTPUT_DIR)
        except Exception: self.sandbox = None
        
        # 🌟 新增：智能包名映射字典 (用于自愈修复)
        self.package_map = {
            "sklearn": "scikit-learn", "bs4": "beautifulsoup4", "cv2": "opencv-python",
            "PIL": "Pillow", "yaml": "PyYAML", "statsmodels": "statsmodels",
            "seaborn": "seaborn", "scipy": "scipy"
        }

    def analyze(self, requirement: str, csv_path: str, context: Dict) -> Dict:
        if not self.llm_client or not self.sandbox: return {"status": "error", "conclusion": "环境缺失"}
        try:
            gaps = json.dumps(context.get('research_gaps', []), ensure_ascii=False)
            response = self.llm_client.chat.completions.create(
                model=self.model, temperature=config.AGENT_LLMS["data_analyst"]["temperature"],
                messages=[
                    {"role": "system", "content": DATA_ANALYST_PROMPT},
                    {"role": "user", "content": f"关注研究空白：{gaps}\n目标数据：{csv_path}\n分析需求：{requirement}"}
                ]
            )
            
            # 🌟 核心升级：提取代码并防截断
            code = response.choices[0].message.content.strip()
            md_tick = chr(96) * 3
            if code.startswith(f"{md_tick}python"): code = code[9:]
            elif code.startswith(md_tick): code = code[3:]
            if code.endswith(md_tick): code = code[:-3]
            code = code.strip()

            # 🌟 核心升级：Auto-Healing 自愈执行循环
            max_retries = 3
            retries = 0
            result = None
            
            while retries < max_retries:
                result = self.sandbox.execute(code)
                if result.success:
                    break
                    
                # 检查是否是缺包错误
                import re, sys, subprocess
                match = re.search(r"ModuleNotFoundError: No module named '([^']+)'", result.error)
                if match:
                    missing_module = match.group(1)
                    install_name = self.package_map.get(missing_module, missing_module)
                    print(f"[🔧 自动修复] 正在后台为你自动安装缺失依赖 '{install_name}'...")
                    try:
                        subprocess.run([sys.executable, "-m", "pip", "install", install_name], check=True, capture_output=True)
                        print(f"[🔧 自动修复] ✅ '{install_name}' 安装成功！重新执行图表渲染...")
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
        except Exception as e: return {"status": "error", "error": str(e)}