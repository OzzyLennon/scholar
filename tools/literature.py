# ==========================================
# 工具模块 - 文献检索
# ==========================================
import json
import time
from typing import List, Dict, Optional
from dataclasses import dataclass

@dataclass
class Paper:
    """论文数据结构"""
    title: str
    authors: List[str]
    year: int
    abstract: str
    doi: str
    citations: int = 0
    pdf_url: Optional[str] = None
    source: str = "mock"  # mock, semantic_scholar, core, crossref
    
    def to_dict(self) -> Dict:
        return {
            "title": self.title,
            "authors": self.authors,
            "year": self.year,
            "abstract": self.abstract[:200] + "..." if len(self.abstract) > 200 else self.abstract,
            "doi": self.doi,
            "citations": self.citations,
            "source": self.source
        }

class LiteratureSearcher:
    """文献检索工具"""
    
    def __init__(self):
        self.search_history = []
    
    def search(self, queries: List[str], max_results: int = 10) -> List[Paper]:
        """
        检索文献
        目前使用 mock 数据，后续可接入真实 API
        """
        print(f"\n[🔍 检索员] 正在检索 {len(queries)} 个关键词...")
        
        all_results = []
        for query in queries:
            print(f"  → 关键词: '{query}'")
            papers = self._mock_search(query, max_results // len(queries))
            all_results.extend(papers)
            time.sleep(0.5)  # 模拟网络延迟
        
        # 去重（基于 DOI）
        seen_dois = set()
        unique_results = []
        for paper in all_results:
            if paper.doi not in seen_dois:
                seen_dois.add(paper.doi)
                unique_results.append(paper)
        
        print(f"[🔍 检索员] 找到 {len(unique_results)} 篇相关文献\n")
        self.search_history.extend(queries)
        return unique_results[:max_results]
    
    def _mock_search(self, query: str, limit: int) -> List[Paper]:
        """模拟检索结果"""
        mock_papers = {
            "python": [
                Paper("Python for Data Analysis", ["Wes McKinney"], 2022, 
                      "This paper explores Python's capabilities in data analysis...", "10.1001/py001", 1500),
                Paper("Automating Research Workflows with Python", ["John Smith"], 2023,
                      "A comprehensive guide to automating academic workflows...", "10.1001/py002", 800),
            ],
            "automation": [
                Paper("Workflow Automation in Academic Research", ["Jane Doe"], 2023,
                      "This study examines the impact of automation on research productivity...", "10.1002/au001", 1200),
                Paper("Scripting for Scholars", ["Bob Wilson"], 2021,
                      "Best practices for academic scripting...", "10.1002/au002", 600),
            ],
            "literature": [
                Paper("Systematic Literature Review Methods", ["Alice Chen"], 2022,
                      "A systematic approach to conducting literature reviews...", "10.1003/li001", 2000),
                Paper("Digital Tools for Literature Management", ["David Lee"], 2023,
                      "An overview of modern literature management tools...", "10.1003/li002", 950),
            ],
            "efficiency": [
                Paper("Research Productivity Metrics", ["Sarah Johnson"], 2023,
                      "Measuring and improving research efficiency...", "10.1004/ef001", 1100),
                Paper("Time Management in Academia", ["Michael Brown"], 2022,
                      "Strategies for efficient academic work...", "10.1004/ef002", 750),
            ]
        }
        
        # 根据关键词返回模拟数据
        results = []
        for key, papers in mock_papers.items():
            if key in query.lower():
                results.extend(papers)
        
        # 如果没有匹配，返回通用结果
        if not results:
            results = [
                Paper(f"Research on {query.title()}", ["Various Authors"], 2023,
                      f"A study related to {query}...", f"10.9999/{hash(query) % 10000}", 500)
            ]
        
        return results[:limit]
    
    def get_search_history(self) -> List[str]:
        return self.search_history

class LiteratureAnalyzer:
    """文献分析工具"""
    
    def analyze_gaps(self, papers: List[Paper], topic: str) -> Dict:
        """分析研究空白"""
        print("[📊 分析工具] 正在分析研究空白...")
        
        years = [p.year for p in papers]
        avg_year = sum(years) / len(years) if years else 0
        
        # 统计各年份文献数量
        year_dist = {}
        for y in years:
            year_dist[y] = year_dist.get(y, 0) + 1
        
        analysis = {
            "total_papers": len(papers),
            "year_range": f"{min(years)}-{max(years)}" if years else "N/A",
            "avg_year": round(avg_year, 1),
            "year_distribution": year_dist,
            "avg_citations": round(sum(p.citations for p in papers) / len(papers), 1) if papers else 0,
            "suggested_gap": "现有研究主要集中在理论层面，缺乏大规模实证数据支持"
        }
        
        return analysis
    
    def extract_themes(self, papers: List[Paper]) -> List[str]:
        """提取研究主题"""
        print("[📊 分析工具] 正在提取研究主题...")
        
        # 简化的主题提取（基于标题关键词）
        themes = set()
        for paper in papers:
            words = paper.title.lower().split()
            themes.update([w for w in words if len(w) > 4])
        
        return list(themes)[:10]
