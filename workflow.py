# ==========================================
# 6-Agent 学术工作流引擎 (强解耦完全体版)
# ==========================================
import os
import json
import re
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass, field
import markdown
from xhtml2pdf import pisa

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
                # 修复：传递正确的参数，确保 context 包含 'research_gaps'
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

    def _format_bibliography(self, papers: List[Dict]) -> str:
        """生成 APA 格式的参考文献列表，按首字母排序"""
        if not papers: return ""
        
        formatted_refs = []
        # 去重
        seen = set()
        unique_papers = []
        for p in papers:
            title = p.get('title', '').strip()
            if title and title not in seen:
                seen.add(title)
                unique_papers.append(p)
                
        # 排序：按第一作者姓氏排序，无作者则按标题
        def sort_key(p):
            authors = p.get('authors', [])
            if authors and isinstance(authors, list):
                return authors[0].strip().lower()
            return p.get('title', '').strip().lower()
            
        unique_papers.sort(key=sort_key)
        
        formatted_refs.append("## References")
        for p in unique_papers:
            # APA 格式: Author, A. A. (Year). Title. Source.
            authors = p.get('authors', ['Unknown'])
            if isinstance(authors, list):
                auth_str = ", ".join(authors[:3]) + (" et al." if len(authors) > 3 else "")
            else:
                auth_str = str(authors)
                
            year = p.get('year', 'n.d.')
            title = p.get('title', 'Untitled')
            source = p.get('source', '')
            
            # Markdown 格式列表
            ref_str = f"- {auth_str} ({year}). *{title}*. {source}"
            formatted_refs.append(ref_str)
            
        return "\n".join(formatted_refs)

    def _generate_pdf(self, md_content: str, output_path: str):
        """将 Markdown 转换为排版精美的 PDF"""
        try:
            # 1. MD -> HTML
            html_body = markdown.markdown(md_content, extensions=['tables', 'fenced_code'])
            
            # 2. CSS 样式 (适配 xhtml2pdf)
            css = """
            <style>
                @page {
                    size: A4;
                    margin: 2.5cm;
                    @frame header_frame {           /* Static Frame */
                        -pdf-frame-content: header_content;
                        top: 1cm;
                        margin-left: 1cm;
                        margin-right: 1cm;
                    }
                    @frame footer_frame {           /* Static Frame */
                        -pdf-frame-content: footer_content;
                        bottom: 1cm;
                        margin-left: 1cm;
                        margin-right: 1cm;
                    }
                }
                body {
                    font-family: Helvetica, Arial, sans-serif;
                    line-height: 1.5;
                    font-size: 11pt;
                }
                h1 { text-align: center; font-size: 24pt; color: #2c3e50; }
                h2 { border-bottom: 1px solid #2c3e50; padding-bottom: 5px; margin-top: 20px; font-size: 16pt; color: #2c3e50; }
                h3 { margin-top: 15px; font-size: 14pt; color: #34495e; }
                p { text-align: justify; }
                code { background-color: #f4f4f4; font-family: Courier; }
                pre { background-color: #f4f4f4; padding: 10px; border: 1px solid #ddd; }
                blockquote { border-left: 4px solid #ccc; padding-left: 10px; color: #666; font-style: italic; }
            </style>
            """
            
            # 3. 构造完整 HTML (包含页眉页脚)
            full_html = f"""
            <html>
            <head>{css}</head>
            <body>
                <div id="header_content" style="text-align: center; color: #888; font-size: 9pt;">Generated by Scholar 6-Agent System</div>
                <div id="footer_content" style="text-align: center; color: #888; font-size: 9pt;">Page <pdf:pagenumber> of <pdf:pagecount></div>
                {html_body}
            </body>
            </html>
            """
            
            # 3. HTML -> PDF
            with open(output_path, "wb") as f:
                pisa_status = pisa.CreatePDF(full_html, dest=f)
                
            if pisa_status.err:
                print(f"[⚠️ Workflow] PDF 生成出现错误: {pisa_status.err}")
        except Exception as e:
            print(f"[⚠️ Workflow] PDF 生成失败: {e}")

    def _save_paper(self, project: ResearchProject):
        """恢复原版的双轨存储：保存 Markdown 和完整的 JSON 日志，并生成 PDF"""
        os.makedirs(config.OUTPUT_DIR, exist_ok=True)
        
        # 1. 自动生成标准化的参考文献列表 (APA 格式 + 排序)
        bibliography = self._format_bibliography(project.papers)
        
        # 2. 拼接到 Markdown 末尾 (确保没有重复的 References 章节)
        # 先简单清理一下可能存在的 References 标题（以防 LLM 没听话）
        final_md = re.sub(r'\n#+\s*(References|参考文献).*$', '', project.final_paper, flags=re.DOTALL | re.IGNORECASE)
        final_md += f"\n\n{bibliography}"
        project.final_paper = final_md
        
        # 3. 保存 Markdown 论文
        md_path = f"{config.OUTPUT_DIR}/{project.id}.md"
        with open(md_path, 'w', encoding='utf-8') as f:
            f.write(project.final_paper)
        
        # 4. 生成 PDF
        pdf_path = f"{config.OUTPUT_DIR}/{project.id}.pdf"
        self._generate_pdf(project.final_paper, pdf_path)
        
        # 5. 保存极其详细的 JSON 工程日志 (供 Debug 和系统迭代使用)
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
        print(f"  📕 PDF已生成: {pdf_path}")
        print(f"  📋 运行志已保存: {log_path}")