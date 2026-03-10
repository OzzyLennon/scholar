# ==========================================
# 5-Agent 学术工作流引擎
# ==========================================
import os
import json
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass, field

from agents import (
    LeadAuthorAgent,
    SearcherAgent,
    ExtractorAgent,
    ReviewerAgent,
    DataResearcherAgent
)
from config import config

@dataclass
class ResearchProject:
    """研究项目"""
    id: str
    idea: str
    
    # 主控输出
    plan: Dict = field(default_factory=dict)
    
    # 检索员输出
    papers: List = field(default_factory=list)
    
    # 提取员输出
    stored_papers: Dict = field(default_factory=dict)
    
    # 审查员输出
    review: Dict = field(default_factory=dict)
    
    # 数据研究员输出（动态生成）
    data_results: Dict = field(default_factory=dict)
    
    # 主控最终输出
    final_paper: str = ""
    
    # 状态跟踪
    status: str = "created"
    logs: List[str] = field(default_factory=list)
    created_at: str = ""
    updated_at: str = ""
    
    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()
        self.updated_at = self.created_at
    
    def log(self, message: str):
        """记录日志"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.logs.append(f"[{timestamp}] {message}")


class FiveAgentWorkflow:
    """
    5-Agent 学术工作流引擎
    
    架构：
    1. 主控 (Lead Author) - 中枢
    2. 检索员 (Searcher) - 文献搜索
    3. 提取员 (Extractor) - 数据清洗与存储
    4. 审查员 (Reviewer) - RAG + 研究空白
    5. 数据研究员 (Data Researcher) - 动态唤醒
    """
    
    def __init__(self, llm_client=None):
        self.client = llm_client
        
        # 初始化 5 个 Agent（每个 Agent 会自动使用自己的 LLM 配置）
        self.lead_author = LeadAuthorAgent()
        self.searcher = SearcherAgent()
        self.extractor = ExtractorAgent(config.OUTPUT_DIR)
        self.reviewer = ReviewerAgent(extractor=self.extractor)
        self.data_researcher = DataResearcherAgent()
        
        # 项目状态
        self.current_project: Optional[ResearchProject] = None
        self.projects: Dict[str, ResearchProject] = {}
    
    def create_project(self, user_idea: str) -> ResearchProject:
        """创建新项目"""
        project_id = f"proj_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        project = ResearchProject(id=project_id, idea=user_idea)
        self.current_project = project
        self.projects[project_id] = project
        project.log("项目创建成功")
        return project
    
    def run(self, user_idea: str = None) -> ResearchProject:
        """运行完整工作流"""
        if user_idea:
            self.create_project(user_idea)
        
        if not self.current_project:
            raise ValueError("请先创建项目")
        
        project = self.current_project
        
        # ==========================================
        # 阶段 1: 主控破题规划
        # ==========================================
        self._print_header("🧠 阶段 1: 主控 Agent 破题规划")
        
        project.status = "planning"
        project.log("主控 Agent 开始规划")
        
        project.plan = self.lead_author.plan(project.idea)
        
        print(f"  📋 大纲：{len(project.plan.get('outline', []))} 章")
        print(f"  🔍 检索词：{project.plan.get('search_queries', [])}")
        print(f"  ❓ 研究问题：{project.plan.get('research_questions', [])}")
        print(f"  📊 需要数据分析：{project.plan.get('needs_data_analysis', False)}")
        
        project.log("规划完成")
        
        # ==========================================
        # 阶段 2: 检索员执行搜索
        # ==========================================
        self._print_header("🔍 阶段 2: 检索员 Agent 文献搜索")
        
        project.status = "searching"
        project.log("检索员 Agent 开始工作")
        
        queries = project.plan.get('search_queries', [])
        project.papers = self.searcher.search(queries, max_results=config.MAX_SEARCH_RESULTS)
        
        print(f"  共检索到 {len(project.papers)} 篇文献")
        for i, paper in enumerate(project.papers[:3], 1):
            print(f"    {i}. {paper.get('title', 'N/A')[:50]}...")
        
        # 主控评估检索结果
        evaluation = self.lead_author.evaluate_search_results(project.papers, queries)
        print(f"  {evaluation.get('feedback', '通过')}")
        
        project.log(f"检索完成：{len(project.papers)} 篇")
        
        # ==========================================
        # 阶段 3: 提取员清洗存储
        # ==========================================
        self._print_header("📦 阶段 3: 提取员 Agent 数据清洗与存储")
        
        project.status = "extracting"
        project.log("提取员 Agent 开始工作")
        
        project.stored_papers = self.extractor.extract_and_store(project.papers)
        
        print(f"  Zotero 存储：{project.stored_papers.get('zotero_count', 0)} 篇")
        print(f"  ChromaDB 向量库：{project.stored_papers.get('chroma_count', 0)} 条")
        
        project.log("数据存储完成")
        
        # ==========================================
        # 阶段 4: 审查员 RAG 检索 + 研究空白
        # ==========================================
        self._print_header("📖 阶段 4: 审查员 Agent 文献综述")
        
        project.status = "reviewing"
        project.log("审查员 Agent 开始工作")
        
        outline = project.plan.get('outline', [])
        project.review = self.reviewer.review(
            outline=outline,
            queries=project.plan.get('search_queries', [])[:3]
        )
        
        print(f"  RAG 检索：{project.review.get('rag_sources', 0)} 条向量")
        print(f"  发现研究空白：{len(project.review.get('research_gaps', []))} 个")
        for gap in project.review.get('research_gaps', [])[:3]:
            print(f"    • {gap}")
        
        project.log("审查完成")
        
        # ==========================================
        # 阶段 5: 数据研究员（动态唤醒）
        # ==========================================
        needs_data = project.plan.get('needs_data_analysis', False)
        
        if needs_data:
            self._print_header("📊 阶段 5: 数据研究员 Agent 动态唤醒")
            
            project.status = "analyzing"
            project.log("数据研究员 Agent 被唤醒")
            
            data_req = project.plan.get('data_requirements', '')
            project.data_results = self.data_researcher.analyze(data_req, project.review)
            
            print(f"  任务：{data_req}")
            print(f"  结论：{project.data_results.get('conclusion', '')}")
            print(f"  图表：{len(project.data_results.get('charts', []))} 张")
            
            project.log("数据分析完成")
        else:
            self._print_header("⏭️ 阶段 5: 跳过（无需数据分析）")
            project.log("主控判定无需数据分析")
        
        # ==========================================
        # 阶段 6: 主控最终统稿
        # ==========================================
        self._print_header("✍️ 阶段 6: 主控 Agent 最终统稿")
        
        project.status = "writing"
        project.log("主控 Agent 开始统稿")
        
        # 分离文献引用和研究空白
        # 只传递真实学术论文作为参考文献
        context = {
            "literature_references": project.papers,  # 真实学术论文 - 用于参考文献
            "research_gaps": project.review.get('research_gaps', []),  # 研究空白 - 作为独立章节
            "review_summary": project.review.get('review_memo', ''),  # 文献综述摘要
            "chapter_contents": project.review.get('chapter_contents', {})
        }
        
        project.final_paper = self.lead_author.write(
            outline=project.plan.get('outline', []),
            context=context,
            data_results=project.data_results
        )
        
        # 保存论文
        self._save_paper(project)
        
        project.status = "completed"
        project.updated_at = datetime.now().isoformat()
        project.log("项目完成")
        
        # ==========================================
        # 完成
        # ==========================================
        self._print_header("✅ 5-Agent 工作流执行完毕")
        
        print(f"\n  项目ID: {project.id}")
        print(f"  状态: {project.status}")
        print(f"  文献: {len(project.papers)} 篇")
        print(f"  向量: {project.stored_papers.get('chroma_count', 0)} 条")
        print(f"  论文长度: {len(project.final_paper)} 字符")
        
        return project
    
    def _print_header(self, title: str):
        """打印分隔线"""
        print("\n" + "="*60)
        print(title)
        print("="*60)
    
    def _save_paper(self, project: ResearchProject):
        """保存论文"""
        os.makedirs(config.OUTPUT_DIR, exist_ok=True)
        
        # 保存 Markdown
        md_path = f"{config.OUTPUT_DIR}/{project.id}.md"
        with open(md_path, 'w', encoding='utf-8') as f:
            f.write(project.final_paper)
        
        # 保存 JSON 日志
        log_path = f"{config.OUTPUT_DIR}/{project.id}.json"
        with open(log_path, 'w', encoding='utf-8') as f:
            json.dump({
                "id": project.id,
                "idea": project.idea,
                "plan": project.plan,
                "review": project.review,
                "data_results": project.data_results,
                "logs": project.logs
            }, f, ensure_ascii=False, indent=2)
        
        print(f"\n  📄 论文已保存: {md_path}")
        print(f"  📋 日志已保存: {log_path}")
