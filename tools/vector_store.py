# ==========================================
# 工具层 - 向量存储 (ChromaDB 新版本)
# ==========================================
import json
import os
from typing import List, Dict, Optional, Any
from datetime import datetime

# ChromaDB 依赖
try:
    import chromadb
    CHROMADB_AVAILABLE = True
except ImportError:
    CHROMADB_AVAILABLE = False
    print("[⚠️] ChromaDB 未安装，将使用本地存储。安装: pip install chromadb")


class VectorStore:
    """向量存储基类"""
    pass


class ChromaDBStore(VectorStore):
    """
    ChromaDB 向量存储 (新版本 API)
    """
    
    def __init__(self, persist_directory: str = "./vector_db", collection_name: str = "papers"):
        self.persist_directory = persist_directory
        os.makedirs(persist_directory, exist_ok=True)
        
        if not CHROMADB_AVAILABLE:
            raise RuntimeError("ChromaDB 未安装")
        
        # 新版 ChromaDB API
        self.client = chromadb.PersistentClient(path=persist_directory)
        
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"}
        )
    
    def add(self, ids: List[str], documents: List[str], metadatas: List[Dict] = None):
        """添加向量"""
        self.collection.add(
            ids=ids,
            documents=documents,
            metadatas=metadatas or [{}] * len(ids)
        )
    
    def query(self, query_texts: List[str], n_results: int = 5) -> List[Dict]:
        """查询向量"""
        results = self.collection.query(
            query_texts=query_texts,
            n_results=n_results
        )
        
        # 转换为统一格式
        documents = []
        for i in range(len(query_texts)):
            docs = []
            for j in range(len(results["ids"][i])):
                doc = {
                    "id": results["ids"][i][j],
                    "content": results["documents"][i][j],
                    "metadata": results["metadatas"][i][j] if results.get("metadatas") else {},
                    "distance": results["distances"][i][j] if results.get("distances") else 0
                }
                docs.append(doc)
            documents.append(docs)
        
        return documents
    
    def count(self) -> int:
        return self.collection.count()


class LocalVectorStore(VectorStore):
    """
    本地向量存储（fallback）
    """
    
    def __init__(self, persist_directory: str = "./vector_db"):
        self.persist_directory = persist_directory
        self.db_file = os.path.join(persist_directory, "local_store.json")
        self.data = self._load()
    
    def _load(self) -> Dict:
        if os.path.exists(self.db_file):
            with open(self.db_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {"documents": [], "index": {}}
    
    def _save(self):
        with open(self.db_file, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)
    
    def add(self, ids: List[str], documents: List[str], metadatas: List[Dict] = None):
        for i, doc_id in enumerate(ids):
            doc = {
                "id": doc_id,
                "content": documents[i],
                "metadata": metadatas[i] if metadatas and i < len(metadatas) else {}
            }
            self.data["documents"].append(doc)
            
            keywords = documents[i].lower().split()[:20]
            for kw in keywords:
                if kw not in self.data["index"]:
                    self.data["index"][kw] = []
                self.data["index"][kw].append(doc_id)
        
        self._save()
    
    def query(self, query_texts: List[str], n_results: int = 5) -> List[Dict]:
        results = []
        for query in query_texts:
            keywords = query.lower().split()
            scores = {}
            
            for kw in keywords:
                if kw in self.data["index"]:
                    for doc_id in self.data["index"][kw]:
                        scores[doc_id] = scores.get(doc_id, 0) + 1
            
            sorted_ids = sorted(scores.keys(), key=lambda x: scores[x], reverse=True)[:n_results]
            
            docs = []
            for doc_id in sorted_ids:
                for doc in self.data["documents"]:
                    if doc["id"] == doc_id:
                        docs.append(doc)
                        break
            
            results.append(docs)
        
        return results
    
    def count(self) -> int:
        return len(self.data["documents"])


class VectorStoreManager:
    """向量存储管理器"""
    
    def __init__(self, persist_directory: str = "./vector_db", prefer_chroma: bool = False):
        """
        默认使用本地存储（ChromaDB 需要下载 ~80MB 模型，太慢）
        """
        self.store: VectorStore = None
        
        if prefer_chroma and CHROMADB_AVAILABLE:
            try:
                self.store = ChromaDBStore(persist_directory)
                print("[✓] ChromaDB 向量存储已初始化")
            except Exception as e:
                print(f"[⚠️] ChromaDB 初始化失败: {e}")
        
        if not self.store:
            self.store = LocalVectorStore(persist_directory)
            print("[✓] 本地向量存储已初始化")
    
    def add_papers(self, papers: List[Any]) -> int:
        """批量添加论文到向量库"""
        ids = []
        documents = []
        metadatas = []
        
        for paper in papers:
            if isinstance(paper, dict):
                paper_id = paper.get('doi') or f"paper_{hash(paper.get('title', ''))}"
                title = paper.get('title', '')
                abstract = paper.get('abstract', '')
                authors = paper.get('authors', [])
                metadata = paper
            else:
                paper_id = paper.doi or f"paper_{hash(paper.title)}"
                title = paper.title
                abstract = paper.abstract
                authors = paper.authors if hasattr(paper, 'authors') else []
                metadata = paper.to_dict() if hasattr(paper, 'to_dict') else {}
            
            content = f"{title}\n\n{abstract}"
            if authors:
                content = f"{', '.join(authors)}\n{content}"
            
            ids.append(paper_id)
            documents.append(content)
            metadatas.append(metadata)
        
        self.store.add(ids, documents, metadatas)
        return len(ids)
    
    def search(self, query: str, n_results: int = 5) -> List[Dict]:
        """搜索相关文献"""
        results = self.store.query([query], n_results)
        return results[0] if results else []
    
    def count(self) -> int:
        return self.store.count()
