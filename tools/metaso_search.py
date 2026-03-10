# ==========================================
# 工具层 - 秘塔中文文献搜索 (MCP)
# ==========================================
import json
import os
import requests
import time
from typing import List, Dict, Optional
from dataclasses import dataclass


@dataclass
class ChinesePaper:
    """中文论文数据结构"""
    title: str
    abstract: str
    authors: List[str]
    year: Optional[int]
    venue: str
    url: str
    source: str  # 来源：秘塔
    citation_count: int = 0
    
    def to_dict(self) -> Dict:
        return {
            "title": self.title,
            "abstract": self.abstract,
            "authors": self.authors,
            "year": self.year,
            "venue": self.venue,
            "url": self.url,
            "source": self.source,
            "citation_count": self.citation_count,
            "doi": None  # 中文文献通常没有DOI
        }


class MetasoMCPClient:
    """
    秘塔MCP客户端 - 中文文献搜索
    
    支持：
    - webpage: 网页搜索
    - document: 文档搜索
    - paper: 学术论文搜索
    """
    
    API_ENDPOINT = "https://metaso.cn/api/mcp"
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("METASO_API_KEY")
        if not self.api_key:
            raise ValueError("需要提供秘塔API Key")
        
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    def _call_tool(self, tool_name: str, arguments: Dict) -> Optional[Dict]:
        """调用MCP工具"""
        payload = {
            "method": "tools/call",
            "jsonrpc": "2.0",
            "params": {
                "name": tool_name,
                "arguments": arguments
            },
            "id": int(time.time() * 1000)
        }
        
        try:
            response = requests.post(
                self.API_ENDPOINT,
                json=payload,
                headers=self.headers,
                timeout=60
            )
            response.raise_for_status()
            
            result = response.json()
            
            if "error" in result:
                print(f"[⚠️ 秘塔MCP] 工具错误: {result['error']}")
                return None
            
            result_data = result.get("result", {})
            
            # 解析 content 中的 JSON 字符串
            content_list = result_data.get("content", [])
            if content_list and len(content_list) > 0:
                text_content = content_list[0].get("text", "")
                if text_content:
                    try:
                        parsed = json.loads(text_content)
                        return parsed
                    except json.JSONDecodeError:
                        # 如果不是JSON，直接返回原始结果
                        return result_data
            
            return result_data
            
        except requests.exceptions.RequestException as e:
            print(f"[⚠️ 秘塔MCP] 请求失败: {e}")
            return None
        except Exception as e:
            print(f"[⚠️ 秘塔MCP] 调用失败: {e}")
            return None
    
    def search_papers(self, query: str, limit: int = 10) -> List[ChinesePaper]:
        """
        搜索中文学术论文
        
        Args:
            query: 搜索关键词（中文）
            limit: 结果数量
        
        Returns:
            ChinesePaper 列表
        """
        arguments = {
            "q": query,
            "size": min(limit, 20),
            "scope": "paper",
            "includeSummary": True
        }
        
        result = self._call_tool("metaso_web_search", arguments)
        
        if not result:
            return []
        
        papers = []
        
        # 解析结果 - 秘塔返回的是 {webpages: [...], total: N}
        webpages = result.get("webpages", [])
        if isinstance(webpages, list):
            for item in webpages:
                paper = self._parse_paper_item(item)
                if paper:
                    papers.append(paper)
        
        print(f"[秘塔MCP] 找到 {len(papers)} 篇中文文献")
        return papers
    
    def search_documents(self, query: str, limit: int = 10) -> List[ChinesePaper]:
        """搜索中文文档"""
        arguments = {
            "q": query,
            "size": min(limit, 20),
            "scope": "document",
            "includeSummary": True
        }
        
        result = self._call_tool("metaso_web_search", arguments)
        
        if not result:
            return []
        
        papers = []
        
        # 解析结果 - 秘塔返回的是 {webpages: [...], total: N}
        webpages = result.get("webpages", [])
        if isinstance(webpages, list):
            for item in webpages:
                paper = self._parse_paper_item(item)
                if paper:
                    papers.append(paper)
        
        print(f"[秘塔MCP] 找到 {len(papers)} 篇中文文档")
        return papers
    
    def search_web(self, query: str, limit: int = 10) -> List[ChinesePaper]:
        """搜索中文网页"""
        arguments = {
            "q": query,
            "size": min(limit, 20),
            "scope": "webpage",
            "includeSummary": True
        }
        
        result = self._call_tool("metaso_web_search", arguments)
        
        if not result:
            return []
        
        papers = []
        
        if isinstance(result, dict):
            content = result.get("content", [])
            if isinstance(content, list):
                for item in content:
                    paper = self._parse_paper_item(item)
                    if paper:
                        papers.append(paper)
        
        print(f"[秘塔MCP] 找到 {len(papers)} 条中文网页")
        return papers
    
    def _parse_paper_item(self, item: Dict) -> Optional[ChinesePaper]:
        """解析搜索结果项 - 秘塔格式"""
        try:
            # 秘塔返回格式：title, snippet, link, date, docId, score
            title = item.get("title", "").strip()
            abstract = item.get("snippet", item.get("summary", ""))[:500]  # 摘要限制500字
            url = item.get("link", item.get("url", ""))
            
            # 解析作者（通常没有）
            authors = []
            
            # 解析年份
            year = None
            date_str = item.get("date", "")
            if date_str:
                try:
                    year = int(date_str[:4])
                except:
                    pass
            
            # 来源/期刊 - 使用link的域名
            venue = "网络资源"
            if url:
                if "bilibili.com" in url:
                    venue = "B站"
                elif "baidu.com" in url:
                    venue = "百度"
                elif "cloud.tencent.com" in url:
                    venue = "腾讯云"
                elif "zhihu.com" in url:
                    venue = "知乎"
            
            # 引用数（通常没有）
            citation_count = 0
            
            if title:  # 必须有标题
                return ChinesePaper(
                    title=title,
                    abstract=abstract,
                    authors=authors,
                    year=year,
                    venue=venue,
                    url=url,
                    source="秘塔MCP",
                    citation_count=citation_count
                )
        except Exception as e:
            print(f"[⚠️] 解析文献项失败: {e}")
        
        return None
    
    def search_multiple(self, queries: List[str], limit_per_query: int = 5) -> List[ChinesePaper]:
        """
        批量搜索多个关键词
        
        Args:
            queries: 搜索关键词列表
            limit_per_query: 每个关键词的结果数
        
        Returns:
            去重后的 ChinesePaper 列表
        """
        all_papers = []
        seen_titles = set()
        
        for query in queries:
            print(f"  [🔍 秘塔] 检索: '{query}'")
            
            # 优先搜索学术论文
            papers = self.search_papers(query, limit_per_query)
            
            # 如果论文不够，补充文档
            if len(papers) < limit_per_query:
                docs = self.search_documents(query, limit_per_query - len(papers))
                papers.extend(docs)
            
            # 去重
            for paper in papers:
                if paper.title not in seen_titles:
                    seen_titles.add(paper.title)
                    all_papers.append(paper)
            
            # 限速：每次请求间隔 1 秒
            time.sleep(1)
        
        print(f"[🔍 秘塔MCP] 共找到 {len(all_papers)} 篇中文文献\n")
        return all_papers


# 便捷函数
def create_metaso_client() -> Optional[MetasoMCPClient]:
    """创建秘塔客户端（如果配置了API Key）"""
    api_key = os.getenv("METASO_API_KEY")
    if api_key:
        try:
            return MetasoMCPClient(api_key)
        except Exception as e:
            print(f"[⚠️] 秘塔客户端初始化失败: {e}")
    return None
