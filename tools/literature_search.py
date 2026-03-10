# ==========================================
# 工具层 - 真实工具实现
# ==========================================
import json
import os
import time
import requests
from typing import List, Dict, Optional
from dataclasses import dataclass
from datetime import datetime

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
    venue: str = ""
    source: str = "semantic_scholar"
    
    def to_dict(self) -> Dict:
        abstract = self.abstract or ""
        return {
            "title": self.title or "Untitled",
            "authors": self.authors or [],
            "year": self.year or 2024,
            "abstract": (abstract[:300] + "..." if len(abstract) > 300 else abstract) if abstract else "",
            "doi": self.doi or "",
            "citations": self.citations or 0,
            "venue": self.venue or "",
            "source": self.source
        }
    
    @classmethod
    def from_semantic_scholar(cls, data: Dict) -> "Paper":
        """从 Semantic Scholar API 响应创建 Paper"""
        return cls(
            title=data.get("title", ""),
            authors=[a.get("name", "") for a in data.get("authors", [])[:3]],  # 取前3作者
            year=data.get("year", datetime.now().year),
            abstract=data.get("abstract", ""),
            doi=data.get("externalIds", {}).get("DOI", data.get("paperId", "")),
            citations=data.get("citationCount", 0),
            pdf_url=data.get("openAccessPdf", {}).get("url", ""),
            venue=data.get("venue", ""),
            source="semantic_scholar"
        )


class SemanticScholarAPI:
    """
    Semantic Scholar 文献检索 API
    免费，无需 API Key，限制：100次/5分钟
    文档: https://api.semanticscholar.org/
    """
    
    BASE_URL = "https://api.semanticscholar.org/graph/v1"
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "Accept": "application/json",
            "User-Agent": "Scholar-Agent/1.0"
        })
    
    def search_papers(self, query: str, limit: int = 10, year_range: str = None) -> List[Paper]:
        """
        搜索论文
        
        Args:
            query: 搜索关键词
            limit: 返回数量 (1-100)
            year_range: 年份范围，如 "2020-2024"
        
        Returns:
            List[Paper]
        """
        try:
            url = f"{self.BASE_URL}/paper/search"
            
            params = {
                "query": query,
                "limit": min(limit, 100),
                "fields": "title,abstract,year,authors,citationCount,externalIds,venue,openAccessPdf"
            }
            
            if year_range:
                params["publicationDateOrYear"] = year_range
            
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            papers = [Paper.from_semantic_scholar(p) for p in data.get("data", [])]
            
            return papers
            
        except requests.exceptions.RequestException as e:
            print(f"[⚠️ Semantic Scholar] 请求失败: {e}")
            return []
        except Exception as e:
            print(f"[⚠️ Semantic Scholar] 解析失败: {e}")
            return []
    
    def search_multiple(self, queries: List[str], limit_per_query: int = 5) -> List[Paper]:
        """
        批量搜索多个关键词
        Semantic Scholar 限制：100次/5分钟 ≈ 1次/3秒
        """
        all_papers = []
        seen_dois = set()
        
        for i, query in enumerate(queries):
            print(f"  [🔍] 检索: '{query}'")
            
            try:
                papers = self.search_papers(query, limit=limit_per_query)
                
                for paper in papers:
                    if paper.doi not in seen_dois:
                        seen_dois.add(paper.doi)
                        all_papers.append(paper)
                
                # 限速：每次请求间隔 3 秒（跳过最后一个）
                if i < len(queries) - 1:
                    time.sleep(3)
                    
            except Exception as e:
                print(f"  [⚠️] 检索失败: {e}")
                continue
        
        return all_papers
    
    def get_paper_details(self, paper_id: str) -> Optional[Paper]:
        """
        获取单篇论文详情
        """
        try:
            url = f"{self.BASE_URL}/paper/{paper_id}"
            params = {
                "fields": "title,abstract,year,authors,citationCount,externalIds,venue,openAccessPdf"
            }
            
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            return Paper.from_semantic_scholar(data)
            
        except Exception as e:
            print(f"[⚠️] 获取论文详情失败: {e}")
            return None


class CoreAPI:
    """
    CORE API (开源学术论文聚合)
    免费额度: 100,000次/月
    需要注册获取 API Key
    文档: https://core.ac.uk/services/api/
    """
    
    BASE_URL = "https://api.core.ac.uk/v3"
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("CORE_API_KEY")
        self.session = requests.Session()
        if self.api_key:
            self.session.headers.update({
                "Authorization": f"Bearer {self.api_key}",
                "Accept": "application/json"
            })
    
    def search_papers(self, query: str, limit: int = 10) -> List[Paper]:
        """搜索论文"""
        if not self.api_key:
            print("[⚠️ CORE] 未配置 API Key")
            return []
        
        try:
            url = f"{self.BASE_URL}/search/works"
            params = {
                "q": query,
                "limit": min(limit, 100),
                "scroll": "true"
            }
            
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            papers = []
            
            for work in data.get("results", []):
                paper = Paper(
                    title=work.get("title", ""),
                    authors=[a.get("name", "") for a in work.get("authors", [])[:3]],
                    year=work.get("yearPublished", datetime.now().year),
                    abstract=work.get("abstract", ""),
                    doi=work.get("doi", work.get("id", "")),
                    citations=work.get("citationCount", 0),
                    pdf_url=work.get("downloadUrl", ""),
                    source="core"
                )
                papers.append(paper)
            
            return papers
            
        except Exception as e:
            print(f"[⚠️ CORE] 请求失败: {e}")
            return []


class LiteratureSearchManager:
    """
    文献检索管理器
    整合多个数据源
    """
    
    def __init__(self, use_semantic_scholar: bool = True, use_core: bool = False, core_api_key: str = None):
        self.ss_api = SemanticScholarAPI() if use_semantic_scholar else None
        self.core_api = CoreAPI(core_api_key) if use_core else None
    
    def search(self, queries: List[str], max_results: int = 20) -> List[Paper]:
        """
        多源检索
        """
        all_papers = []
        
        # 优先使用 Semantic Scholar
        if self.ss_api:
            print(f"\n[📚 Semantic Scholar] 检索 {len(queries)} 个关键词...")
            papers = self.ss_api.search_multiple(queries, limit_per_query=max(3, max_results // len(queries)))
            all_papers.extend(papers)
            print(f"  ✓ 找到 {len(papers)} 篇")
        
        # 如果结果不够，补充 CORE
        if self.core_api and len(all_papers) < max_results:
            print(f"[📚 CORE] 补充检索...")
            for query in queries[:2]:
                papers = self.core_api.search_papers(query, limit=5)
                all_papers.extend(papers)
            print(f"  ✓ 补充 {len(all_papers)} 篇")
        
        # 去重并排序（按引用量）
        seen = {}
        for p in all_papers:
            if p.doi not in seen or p.citations > seen[p.doi].citations:
                seen[p.doi] = p
        
        unique_papers = list(seen.values())
        unique_papers.sort(key=lambda x: x.citations, reverse=True)
        
        return unique_papers[:max_results]
