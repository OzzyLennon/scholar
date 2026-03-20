# ==========================================
# 工具层 - 向量存储引擎 (究极完全体)
# 融合：ChromaDB 支持 + 纯本地倒排索引兜底 + Hybrid RAG 权威性重排 + Metadata 净化
# ==========================================
import json
import os
import math
import re
from typing import List, Dict, Optional, Any
from datetime import datetime

# 尝试导入 ChromaDB，如果失败则优雅降级到本地存储
try:
    import chromadb
    CHROMADB_AVAILABLE = True
except ImportError:
    CHROMADB_AVAILABLE = False
    print("[⚠️] ChromaDB 未安装，系统将自动降级使用纯本地倒排索引存储。")

class VectorStore:
    """向量数据库抽象基类"""
    def add(self, ids: List[str], documents: List[str], metadatas: List[Dict] = None):
        pass
    def query(self, query_texts: List[str], n_results: int = 5) -> List[List[Dict]]:
        pass
    def count(self) -> int:
        pass

# ==========================================
# 1. ChromaDB 官方实现 (工业级)
# ==========================================
class ChromaDBStore(VectorStore):
    def __init__(self, persist_directory: str = "./vector_db", collection_name: str = "papers"):
        self.persist_directory = persist_directory
        os.makedirs(persist_directory, exist_ok=True)
        if not CHROMADB_AVAILABLE:
            raise RuntimeError("ChromaDB 未安装")
        
        self.client = chromadb.PersistentClient(path=persist_directory)
        # 强制使用余弦相似度 (Cosine Similarity) 更有利于文本匹配
        self.collection = self.client.get_or_create_collection(
            name=collection_name, 
            metadata={"hnsw:space": "cosine"}
        )
    
    def add(self, ids: List[str], documents: List[str], metadatas: List[Dict] = None):
        # 分批次写入防止内存溢出
        batch_size = 100
        for i in range(0, len(ids), batch_size):
            self.collection.add(
                ids=ids[i:i+batch_size], 
                documents=documents[i:i+batch_size], 
                metadatas=metadatas[i:i+batch_size] if metadatas else [{}] * len(ids[i:i+batch_size])
            )
    
    def query(self, query_texts: List[str], n_results: int = 5) -> List[List[Dict]]:
        # 如果库里的文档数量少于请求数量，动态调整 n_results
        actual_n = min(n_results, max(1, self.count()))
        if actual_n == 0:
            return [[] for _ in query_texts]
            
        results = self.collection.query(query_texts=query_texts, n_results=actual_n)
        
        # 统一返回结构
        formatted_results = []
        for i in range(len(query_texts)):
            docs = []
            if results["ids"] and len(results["ids"]) > i:
                for j in range(len(results["ids"][i])):
                    doc = {
                        "id": results["ids"][i][j],
                        "content": results["documents"][i][j],
                        "metadata": results["metadatas"][i][j] if results.get("metadatas") else {},
                        "distance": results["distances"][i][j] if results.get("distances") else 0.0
                    }
                    docs.append(doc)
            formatted_results.append(docs)
        return formatted_results
    
    def count(self) -> int: 
        return self.collection.count()

# ==========================================
# 2. 本地倒排索引兜底实现 (恢复原版的精妙设计)
# ==========================================
class LocalVectorStore(VectorStore):
    def __init__(self, persist_directory: str = "./vector_db"):
        self.db_file = os.path.join(persist_directory, "local_store.json")
        self.data = self._load()
        
    def _load(self) -> Dict:
        if os.path.exists(self.db_file):
            try:
                with open(self.db_file, 'r', encoding='utf-8') as f: 
                    return json.load(f)
            except Exception:
                pass
        return {"documents": [], "index": {}}
        
    def _save(self):
        os.makedirs(os.path.dirname(self.db_file), exist_ok=True)
        with open(self.db_file, 'w', encoding='utf-8') as f: 
            json.dump(self.data, f, ensure_ascii=False, indent=2)
            
    def _tokenize(self, text: str) -> List[str]:
        """简单的分词器 (英文按空格，中文按单字/词组)"""
        text = text.lower()
        words = re.findall(r'\b\w+\b', text)
        return [w for w in words if len(w) > 2] # 过滤掉太短的停用词
        
    def add(self, ids: List[str], documents: List[str], metadatas: List[Dict] = None):
        """添加文档并更新倒排索引"""
        for i, doc_id in enumerate(ids):
            # 1. 存入文档主表
            doc_obj = {
                "id": doc_id, 
                "content": documents[i], 
                "metadata": metadatas[i] if metadatas else {}
            }
            # 去重逻辑
            existing_idx = next((index for (index, d) in enumerate(self.data["documents"]) if d["id"] == doc_id), None)
            if existing_idx is not None:
                self.data["documents"][existing_idx] = doc_obj
            else:
                self.data["documents"].append(doc_obj)
                
            # 2. 建立精妙的倒排索引 (Inverted Index)
            words = self._tokenize(documents[i])
            word_counts = {}
            for w in words:
                word_counts[w] = word_counts.get(w, 0) + 1
                
            # 只取频率最高的 Top 20 关键词存入索引，极大节省空间
            top_words = sorted(word_counts.items(), key=lambda x: x[1], reverse=True)[:20]
            for word, count in top_words:
                if word not in self.data["index"]:
                    self.data["index"][word] = {}
                self.data["index"][word][doc_id] = count
                
        self._save()
        
    def query(self, query_texts: List[str], n_results: int = 5) -> List[List[Dict]]:
        """基于词频的 TF-IDF Lite 倒排检索"""
        all_results = []
        doc_map = {d["id"]: d for d in self.data["documents"]}
        
        for query_text in query_texts:
            query_words = self._tokenize(query_text)
            scores = {}
            
            for word in query_words:
                if word in self.data["index"]:
                    doc_freqs = self.data["index"][word]
                    # 简单的 TF 打分累加
                    for doc_id, freq in doc_freqs.items():
                        scores[doc_id] = scores.get(doc_id, 0) + freq
            
            # 排序：得分越高的排越前
            sorted_doc_ids = sorted(scores.items(), key=lambda x: x[1], reverse=True)
            
            docs = []
            for doc_id, score in sorted_doc_ids[:n_results]:
                if doc_id in doc_map:
                    doc = doc_map[doc_id].copy()
                    # 模拟 ChromaDB 的 distance (得分越高，distance 越小)
                    doc["distance"] = 1.0 / (score + 1.0) 
                    docs.append(doc)
                    
            all_results.append(docs)
            
        return all_results
        
    def count(self) -> int: 
        return len(self.data["documents"])

# ==========================================
# 3. 统一调度层 (负责 Hybrid RAG 权威重排)
# ==========================================
class VectorStoreManager:
    # 常量定义
    CANDIDATE_EXPANSION_FACTOR = 3  # 候选集扩展倍数，用于混合检索

    # 🌟 核心修改：重新把 prefer_chroma 改回 True，激活高性能向量库！
    def __init__(self, persist_directory: str = "./vector_db", prefer_chroma: bool = True):
        self.store = None
        
        # 优先尝试 ChromaDB
        if prefer_chroma and CHROMADB_AVAILABLE:
            try: 
                self.store = ChromaDBStore(persist_directory)
                print("[📦 向量库] 成功挂载 ChromaDB 高性能引擎")
            except Exception as e: 
                print(f"[⚠️] ChromaDB 挂载失败 ({e})，回退到本地存储。")
                
        # 降级兜底方案
        if not self.store: 
            self.store = LocalVectorStore(persist_directory)
            print("[📦 向量库] 成功挂载 Local 倒排索引引擎")
    
    def add_papers(self, papers: List[Any]) -> int:
        """适配清洗后的论文数据结构，并执行入库"""
        ids, documents, metadatas = [], [], []
        
        for paper in papers:
            # 兼容字典和 Paper 对象
            if isinstance(paper, dict):
                p_id = paper.get('doi') or f"p_{hash(paper.get('title'))}"
                title = paper.get('title', '')
                abstract = paper.get('abstract', '')
                raw_meta = paper
            else:
                p_id = paper.doi or f"p_{hash(paper.title)}"
                title = paper.title
                abstract = paper.abstract
                raw_meta = paper.to_dict() if hasattr(paper, 'to_dict') else {}
            
            # 构建嵌入用的核心文本 (Title + Abstract)
            content = f"【标题】{title}\n\n【摘要】{abstract}"
            ids.append(str(p_id))
            documents.append(content)
            
            # 🌟 核心防御：Metadata 净化器 (确保 ChromaDB 不会因为 List 或 None 报错)
            clean_meta = {}
            for k, v in raw_meta.items():
                if v is None:
                    clean_meta[k] = ""
                elif isinstance(v, list):
                    clean_meta[k] = ", ".join([str(x) for x in v])
                elif isinstance(v, (str, int, float, bool)):
                    clean_meta[k] = v
                else:
                    clean_meta[k] = str(v)
            
            metadatas.append(clean_meta)
        
        if ids:
            try:
                self.store.add(ids, documents, metadatas)
            except Exception as e:
                print(f"[⚠️ 向量库入库错误] {e}")
        return len(ids)
    
    def search(self, query: str, n_results: int = 5) -> List[Dict]:
        """基于权威性的混合检索 (Hybrid RAG Re-ranking)"""
        
        # 1. 扩大底层召回范围 (取 3 倍候选集)
        candidates_count = n_results * self.CANDIDATE_EXPANSION_FACTOR
        results = self.store.query([query], candidates_count)
        
        if not results or not results[0]: 
            return []
            
        docs = results[0]
        if not docs:
            return []
            
        # 2. 对召回的候选集进行权威性二次打分
        # 提取当前召回集中的最大 distance 用于归一化 (防除零)
        max_dist = max([d.get('distance', 1.0) for d in docs] + [0.001])
        if max_dist == 0: 
            max_dist = 0.001
            
        for i, doc in enumerate(docs):
            # a. 基础检索相关性得分
            distance_score = 1.0 - (doc.get('distance', max_dist) / max_dist)
            rank_score = 1.0 - (i / len(docs)) * 0.5
            semantic_score = (distance_score + rank_score) / 2.0
            
            # b. 权威性得分
            auth_score = float(doc.get('metadata', {}).get('authority_score', 1.0))
            
            # c. 平滑与混合打分 (60% 语义相关性 + 40% 权威性)
            normalized_auth = min(1.0, math.log1p(auth_score) / 2.0)
            doc['combined_score'] = (semantic_score * 0.6) + (normalized_auth * 0.4)
            
        # 3. 终极重排 (根据混合得分降序)
        docs.sort(key=lambda x: x.get('combined_score', 0), reverse=True)
        
        return docs[:n_results]
    
    def count(self) -> int: 
        return self.store.count()
