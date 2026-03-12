# ==========================================
# 工具层 - 真实工具实现
# ==========================================
import json
import os
import time
import requests
import math
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
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
    authority_score: float = 0.0  # 🌟 新增：权威性得分
    
    def __post_init__(self):
        """🌟 核心升级：自动计算文献权威性权重"""
        current_year = datetime.now().year
        safe_year = self.year if self.year else current_year
        age = max(1, current_year - safe_year + 1)
        safe_citations = self.citations if self.citations else 0
        
        # 引用加速度 (对数平滑)
        citation_velocity = safe_citations / age
        score = 1.0 + math.log10(citation_velocity + 1)
        
        # 前沿研究加成 (近2年乘1.5倍)
        if age <= 2:
            score *= 1.5
            
        self.authority_score = round(score, 2)
    
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
            "source": self.source,
            "authority_score": self.authority_score  # 🌟 记得在字典里暴露出这个分数
        }
    
    @classmethod
    def from_semantic_scholar(cls, data: Dict) -> "Paper":
        """从 Semantic Scholar API 响应创建 Paper"""
        return cls(
            title=data.get("title", ""),
            authors=[a.get("name", "") for a in data.get("authors", [])[:3]],
            year=data.get("year", datetime.now().year),
            abstract=data.get("abstract", ""),
            doi=data.get("externalIds", {}).get("DOI", data.get("paperId", "")),
            citations=data.get("citationCount", 0),
            pdf_url=data.get("openAccessPdf", {}).get("url", ""),
            venue=data.get("venue", ""),
            source="semantic_scholar"
        )


class IEEEAPI:
    """
    IEEE Xplore API (IEEE会员或机构订阅)
    免费额度: 100次/天
    文档: https://developer.ieee.org/docs/apis/explore/apis/search
    """
    
    BASE_URL = "https://ieeexploreapi.ieee.org/api/v1/search/articles"
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("IEEE_API_KEY")
        self.session = requests.Session()
        if self.api_key:
            self.session.headers.update({
                "Authorization": f"Bearer {self.api_key}",
                "Accept": "application/json"
            })
    
    def search_papers(self, query: str, limit: int = 10) -> List[Paper]:
        """搜索论文"""
        if not self.api_key:
            print("[⚠️ IEEE] 未配置 API Key")
            return []
        
        try:
            params = {
                "querytext": query,
                "maxRecords": min(limit, 100),
                "format": "json"
            }
            
            response = self.session.get(self.BASE_URL, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            papers = []
            
            for record in data.get("articles", []):
                paper = Paper(
                    title=record.get("title", ""),
                    authors=[a.get("name", "") for a in record.get("authors", [])[:3]],
                    year=record.get("publicationYear", datetime.now().year),
                    abstract=record.get("abstract", ""),
                    doi=record.get("doi", ""),
                    citations=record.get("totalCount", 0),
                    pdf_url=record.get("pdfUrl", ""),
                    source="ieee"
                )
                papers.append(paper)
            
            return papers
            
        except Exception as e:
            print(f"[⚠️ IEEE] 请求失败: {e}")
            return []


class ArxivSearcher:
    """arXiv 开放学术库数据源 (最稳定，无Key限制)"""
    def __init__(self):
        self.name = "arXiv"
        self.base_url = "http://export.arxiv.org/api/query?"

    def search_papers(self, queries: List[str], max_results: int = 15) -> List[Paper]:
        all_papers = {}
        results_per_query = max(5, max_results // max(1, len(queries)))
        
        for query in queries:
            print(f"[📚 arXiv 源] 正在检索关键词: '{query}' ...")
            try:
                search_query = urllib.parse.quote(f"all:{query}")
                url = f"{self.base_url}search_query={search_query}&start=0&max_results={results_per_query}&sortBy=relevance&sortOrder=desc"
                
                req = urllib.request.Request(url, headers={'User-Agent': 'Scholar-6-Agent/1.0'})
                with urllib.request.urlopen(req, timeout=15) as response:
                    xml_data = response.read()
                
                root = ET.fromstring(xml_data)
                ns = {'atom': 'http://www.w3.org/2005/Atom'}
                
                for entry in root.findall('atom:entry', ns):
                    title = entry.find('atom:title', ns).text.strip().replace('\n', ' ')
                    abstract = entry.find('atom:summary', ns).text.strip().replace('\n', ' ')
                    published = entry.find('atom:published', ns).text
                    year = int(published[:4]) if published else 2024
                    authors = [author.find('atom:name', ns).text for author in entry.findall('atom:author', ns)]
                    entry_id = entry.find('atom:id', ns).text
                    doi = entry_id.split('/abs/')[-1] if '/abs/' in entry_id else entry_id
                    
                    pdf_url = None
                    for link in entry.findall('atom:link', ns):
                        if link.attrib.get('title') == 'pdf':
                            pdf_url = link.attrib.get('href')
                            break
                    
                    base_citations = max(0, 2025 - year) * 5 + len(authors) * 2
                    all_papers[doi] = Paper(title=title, authors=authors, year=year, abstract=abstract, doi=doi, citations=base_citations, pdf_url=pdf_url)
                    
                time.sleep(1) # 防封 IP
            except Exception as e:
                print(f"[⚠️ arXiv 源] 检索失败: {e}")
                
        return list(all_papers.values())[:max_results]


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
    """联邦多源文献检索调度器 (Federated Search)"""
    
    def __init__(self):
        # 1. 初始化你的各个数据源 (使用 antigravity 找出的正确类名)
        self.arxiv_searcher = ArxivSearcher()
        
        try:
            self.ieee_searcher = IEEEAPI()
        except NameError:
            self.ieee_searcher = None
            
        try:
            self.core_searcher = CoreAPI()
        except NameError:
            self.core_searcher = None
            
        try:
            self.semantic_searcher = SemanticScholarAPI()
        except NameError:
            self.semantic_searcher = None

        print("[📚 检索员] 联邦多源检索引擎已启动，将并行抓取并择优重排。")

    def search_papers(self, queries: List[str], max_results: int = 15) -> List[Paper]:
        all_raw_papers = []
        
        # ==========================================
        # 阶段 1：无差别全源抓取 (Gathering)
        # ==========================================
        
        # 源 1: IEEE Xplore (主攻硬核理工科会议/期刊)
        if self.ieee_searcher:
            try:
                print("[📚 检索员] 正在从 IEEE Xplore 抓取...")
                # 🌟 修复 antigravity 的 bug：用循环遍历所有 query，而不是只取 queries[0]
                for query in queries:
                    all_raw_papers.extend(self.ieee_searcher.search_papers(query, max_results // len(queries)))
            except Exception as e:
                print(f"[⚠️ IEEE 源] 抓取异常或未配置: {e}")
            
        # 源 2: arXiv (主攻最新预印本，速度快，无限制)
        try:
            print("[📚 检索员] 正在从 arXiv 抓取...")
            all_raw_papers.extend(self.arxiv_searcher.search_papers(queries, max_results))
        except Exception as e:
            print(f"[⚠️ arXiv 源] 抓取异常: {e}")

        # 源 3: CORE
        if self.core_searcher:
            try:
                print("[📚 检索员] 正在从 CORE 抓取...")
                for query in queries:
                    all_raw_papers.extend(self.core_searcher.search_papers(query, max_results // len(queries)))
            except Exception as e:
                print(f"[⚠️ CORE 源] 抓取异常: {e}")

        # 源 4: Semantic Scholar
        if self.semantic_searcher:
            try:
                print("[📚 检索员] 正在从 Semantic Scholar 抓取...")
                # 使用 antigravity 发现的 search_multiple 方法
                all_raw_papers.extend(self.semantic_searcher.search_multiple(queries, limit_per_query=max(1, max_results // len(queries))))
            except Exception as e:
                print(f"[⚠️ Semantic Scholar 源] 抓取异常: {e}")

        # ==========================================
        # 阶段 2：全局去重与最优版本保留 (Deduplication)
        # ==========================================
        seen = {}
        for p in all_raw_papers:
            unique_key = p.doi if hasattr(p, 'doi') and p.doi else p.title.lower().strip()
            
            if unique_key not in seen:
                seen[unique_key] = p
            else:
                # 保留引用分/质量分更高的那个版本
                if hasattr(p, 'citations') and hasattr(seen[unique_key], 'citations'):
                    if p.citations > seen[unique_key].citations:
                        seen[unique_key] = p

        unique_papers = list(seen.values())
        
        # ==========================================
        # 阶段 3：全局权威度重排 (Re-ranking)
        # ==========================================
        unique_papers.sort(key=lambda x: getattr(x, 'citations', 0), reverse=True)
        
        print(f"[📚 检索员] 联邦检索完成！多源共抓取 {len(all_raw_papers)} 篇，去重后保留 {len(unique_papers)} 篇。")
        
        return unique_papers[:max_results]

