import hashlib
from pathlib import Path
from typing import List, Dict, Any

import chromadb

from backend.rag.document import Document
from backend.rag.embedding import BGEEmbedding


class ChromaVectorStore:
    """基于 Chroma 的向量数据库操作类"""

    def __init__(
        self,
        persist_directory: str = "data/vector_db",
        collection_name: str = "product_knowledge",
        embedding_model: str = "BAAI/bge-small-zh-v1.5"
    ):
        self.persist_directory = Path(persist_directory)
        self.persist_directory.mkdir(
            parents=True,
            exist_ok=True
        )

        self.embedding = BGEEmbedding(embedding_model)

        # 创建本地持久化数据库
        self.client = chromadb.PersistentClient(
            path=str(self.persist_directory)
        )

        # 创建或获取集合
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"}
        )

    @staticmethod
    def _generate_id(document: Document) -> str:
        """根据文档内容和来源生成稳定 ID"""

        raw_text = (
            str(document.metadata.get("source", ""))
            + str(document.metadata.get("chunk_index", ""))
            + document.page_content
        )

        return hashlib.md5(
            raw_text.encode("utf-8")
        ).hexdigest()

    def add_documents(
        self,
        documents: List[Document]
    ) -> int:
        """将文档向量化并写入 Chroma"""

        if not documents:
            return 0

        valid_documents = [
            doc for doc in documents
            if doc.page_content.strip()
        ]

        if not valid_documents:
            return 0

        texts = [
            doc.page_content
            for doc in valid_documents
        ]

        embeddings = self.embedding.embed_texts(texts)

        ids = [
            self._generate_id(doc)
            for doc in valid_documents
        ]

        metadatas = [
            doc.metadata
            for doc in valid_documents
        ]

        # upsert：相同 ID 更新，不同 ID 新增
        self.collection.upsert(
            ids=ids,
            documents=texts,
            embeddings=embeddings,
            metadatas=metadatas
        )

        return len(valid_documents)

    def search(
        self,
        query: str,
        top_k: int = 3
    ) -> List[Dict[str, Any]]:
        """根据用户问题检索相关文档"""

        if not query.strip():
            return []

        if top_k <= 0:
            raise ValueError("top_k 必须大于 0")

        query_embedding = self.embedding.embed_query(query)

        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=min(
                top_k,
                self.collection.count()
            ),
            include=[
                "documents",
                "metadatas",
                "distances"
            ]
        )

        search_results = []

        if not results["ids"]:
            return search_results

        for index, document_id in enumerate(results["ids"][0]):
            search_results.append({
                "id": document_id,
                "content": results["documents"][0][index],
                "metadata": results["metadatas"][0][index],
                "distance": results["distances"][0][index]
            })

        return search_results

    def count(self) -> int:
        """获取集合中的文档数量"""

        return self.collection.count()

    def get_source_files(self) -> List[Dict[str, Any]]:
        """获取向量数据库中已索引的文件及其 Chunk 数量"""

        results = self.collection.get(
            include=["metadatas"]
        )

        file_stats = {}

        for metadata in results.get("metadatas", []):
            if not metadata:
                continue

            source = metadata.get("source")

            if not source:
                continue

            if source not in file_stats:
                file_stats[source] = {
                    "filename": source,
                    "file_type": metadata.get("file_type", ""),
                    "chunk_count": 0
                }

            file_stats[source]["chunk_count"] += 1

        return list(file_stats.values())

    def count_by_source(self, source: str) -> int:
        """统计指定文件对应的向量数量"""

        results = self.collection.get(
            where={"source": source},
            include=["metadatas"]
        )

        return len(results.get("ids", []))

    def delete_by_source(self, source: str) -> int:
        """删除指定文件对应的全部向量数据"""

        results = self.collection.get(
            where={"source": source},
            include=["metadatas"]
        )

        ids = results.get("ids", [])

        if not ids:
            return 0

        self.collection.delete(ids=ids)

        return len(ids)

    def replace_documents(
        self,
        source: str,
        documents: List[Document]
    ) -> int:
        """
        重新索引指定文件。

        先写入新向量，再清理旧向量中不再使用的记录，
        避免新向量写入失败时直接丢失旧数据。
        """

        if not documents:
            raise ValueError("没有可用于重新索引的文档")

        # 确保所有新文档都关联到指定文件
        for document in documents:
            document.metadata["source"] = source

        # 获取该文件原有的向量 ID
        old_results = self.collection.get(
            where={"source": source},
            include=["metadatas"]
        )

        old_ids = set(old_results.get("ids", []))

        # 写入新向量
        inserted_count = self.add_documents(documents)

        # 计算新向量 ID
        new_ids = {
            self._generate_id(document)
            for document in documents
            if document.page_content.strip()
        }

        # 只删除新版本中已经不存在的旧向量
        stale_ids = list(old_ids - new_ids)

        if stale_ids:
            self.collection.delete(ids=stale_ids)

        return inserted_count