# ==========================================
# 6-Agent 学术工作流引擎 (强解耦完全体版)
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
    DataCrawlerAgent,
    DataAnalystAgent
)
from config import config

@dataclass
class ResearchProject:
    """研究项目状态机"""
    id: str
    idea: str
    plan: Dict = field(default_factory=dict)
    papers: List = field(default_factory=list)
    stored_papers: Dict = field(default_factory=dict)
    review: Dict = field(default_factory=dict)
    data_results: Dict = field(default_factory=dict)
    final_paper: str = ""
    status: str = "created"
    logs: List[str] = field(default_factory=list)
    created_at: str = ""
    updated_at: str = ""
    
    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()
        self.updated_at = self.created_at
    
    def log(self, message: str):
        """记录时间戳日志"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.logs.append(f"[{timestamp}] {message}")


class SixAgentWorkflow:
    def __init__(self):
        # 初始化 6 大 Agent
        self.lead_author = LeadAuthorAgent()
        self.searcher = SearcherAgent()
        self.extractor = ExtractorAgent(config.OUTPUT_DIR)
        self.reviewer = ReviewerAgent(extractor=self.extractor)
        self.data_crawler = DataCrawlerAgent()
        self.data_analyst = DataAnalystAgent()
        
        self.current_project: Optional[ResearchProject] = None
        self.projects: Dict[str, ResearchProject] = {}
    
    def create_project(self, user_idea: str) -> ResearchProject:
        project_id = f"proj_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        project = ResearchProject(id=project_id, idea=user_idea)
        self.current_project = project
        self.projects[project_id] = project
        project.log("项目创建成功，6-Agent 引擎启动")
        return project
    
    def run(self, user_idea: str = None) -> ResearchProject:
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
        project.log("主控 Agent 开始深度思考并规划大纲...")
        
        project.plan = self.lead_author.plan(project.idea)
        print(f"  📋 大纲：{len(project.plan.get('outline', []))} 章")
        print(f"  🔍 检索词：{project.plan.get('search_queries', [])}")
        print(f"  ❓ 研究问题：{project.plan.get('research_questions', [])}")
        print(f"  📊 激活数据采集流：{project.plan.get('needs_data_analysis', False)}")
        project.log("破题规划完成")
        
        # ==========================================
        # 阶段 2: 检索员执行搜索
        # ==========================================
        self._print_header("🔍 阶段 2: 检索员 Agent 文献搜索")
        project.status = "searching"
        project.log("检索员 Agent 前往 Semantic Scholar/秘塔 执行检索")
        
        queries = project.plan.get('search_queries', [])
        project.papers = self.searcher.search(queries, max_results=config.MAX_SEARCH_RESULTS)
        
        print(f"  共检索到 {len(project.papers)} 篇文献")
        for i, paper in enumerate(project.papers[:3], 1):
            print(f"    {i}. {paper.get('title', 'N/A')[:50]}...")
            
        evaluation = self.lead_author.evaluate_search_results(project.papers, queries)
        print(f"  主控评估反馈: {evaluation.get('feedback', '通过')}")
        project.log(f"文献检索完成，获取 {len(project.papers)} 篇")
        
        # ==========================================
        # 阶段 3: 提取员计算权重与存储
        # ==========================================
        self._print_header("📦 阶段 3: 提取员 Agent 权威度计算与存储")
        project.status = "extracting"
        project.log("提取员 Agent 计算权威分并存入 ChromaDB")
        
        project.stored_papers = self.extractor.extract_and_store(project.papers)
        print(f"  Zotero 结构化存储：{project.stored_papers.get('zotero_count', 0)} 篇")
        print(f"  ChromaDB 向量入库：{project.stored_papers.get('chroma_count', 0)} 条")
        project.log("向量清洗与存储完成")
        
        # ==========================================
        # 阶段 4: 审查员 Hybrid RAG 审查
        # ==========================================
        self._print_header("📖 阶段 4: 审查员 Agent (Kimi) 混合检索与空白提炼")
        project.status = "reviewing"
        project.log("审查员 Agent 执行超长上下文阅读...")
        
        project.review = self.reviewer.review(project.plan.get('outline', []), queries)
        print(f"  RAG 检出权威文献块：{project.review.get('rag_sources', 0)} 条")
        print(f"  发现硬核研究空白：{len(project.review.get('research_gaps', []))} 个")
        for gap in project.review.get('research_gaps', [])[:3]:
            print(f"    • {gap}")
        project.log("文献审查与 Gap 分析完成")
        
        # ==========================================
        # 阶段 5: 数据双子星 (ETL 采集 -> DS 分析)
        # ==========================================
        needs_data = project.plan.get('needs_data_analysis', False)
        if needs_data:
            self._print_header("🚀 阶段 5: 数据双子星流水线 (Crawler -> Analyst)")
            project.status = "data_pipeline"
            data_req = project.plan.get('data_requirements', '')
            
            # 5.1 采集员出动
            project.log("🕷️ 采集员出动：编写爬虫并落地 CSV...")
            crawler_res = self.data_crawler.run(data_req)
            
            if crawler_res.get('success'):
                # 5.2 分析员出动
                project.log("📈 分析员接管：读取 CSV 进行数据科学绘图...")
                csv_path = crawler_res.get('csv_path')
                project.data_results = self.data_analyst.analyze(data_req, csv_path, project.review)
                
                print(f"  核心洞察：{project.data_results.get('conclusion', '')}")
                print(f"  生成高质图表：{len(project.data_results.get('charts', []))} 张")
                project.log("数据双子星任务圆满完成")
            else:
                project.log(f"⚠️ 采集员遇到障碍: {crawler_res.get('error')}, 跳过数据分析。")
        else:
            self._print_header("⏭️ 阶段 5: 纯理论综述，跳过实证流水线")
            project.log("主控判定无需实证，跳过数据采集")
        
        # ==========================================
        # 阶段 6: 主控最终统稿
        # ==========================================
        self._print_header("✍️ 阶段 6: 主控 Agent 最终学术统稿")
        project.status = "writing"
        project.log("主控 Agent 开始深度整合并撰写 Markdown 论文...")
        
        context = {
            "literature_references": project.papers,
            "research_gaps": project.review.get('research_gaps', []),
            "review_summary": project.review.get('review_memo', '')
        }
        
        project.final_paper = self.lead_author.write(project.plan.get('outline', []), context, project.data_results)
        
        self._save_paper(project)
        
        project.status = "completed"
        project.updated_at = datetime.now().isoformat()
        project.log("🎉 项目大功告成")
        
        self._print_header("✅ 6-Agent 工作流执行完毕")
        return project

    def _print_header(self, title: str):
        print("\n" + "="*70 + f"\n{title}\n" + "="*70)
        
    def _save_paper(self, project: ResearchProject):
        """恢复原版的双轨存储：保存 Markdown 和完整的 JSON 日志"""
        os.makedirs(config.OUTPUT_DIR, exist_ok=True)
        
        # 保存 Markdown 论文
        md_path = f"{config.OUTPUT_DIR}/{project.id}.md"
        with open(md_path, 'w', encoding='utf-8') as f:
            f.write(project.final_paper)
        
        # 保存极其详细的 JSON 工程日志 (供 Debug 和系统迭代使用)
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
            
        print(f"\n  📄 终稿已保存: {md_path}")
        print(f"  📋 运行志已保存: {log_path}")