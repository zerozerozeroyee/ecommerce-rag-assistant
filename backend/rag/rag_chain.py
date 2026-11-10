from typing import Any, Dict, List

from backend.llm.qwen_client import QwenClient
from backend.rag.vector_store import ChromaVectorStore


class RAGChain:
    """RAG 核心问答链：检索知识并调用 Qwen 生成答案"""

    def __init__(
        self,
        vector_store: ChromaVectorStore,
        llm: QwenClient,
        top_k: int = 3,
        max_distance: float = 0.65
    ):
        self.vector_store = vector_store
        self.llm = llm
        self.top_k = top_k
        self.max_distance = max_distance

    def ask(self, question: str) -> Dict[str, Any]:
        """接收用户问题，检索知识并生成回答"""

        if not question or not question.strip():
            raise ValueError("用户问题不能为空")

        question = question.strip()

        # 1. 检查知识库是否有数据
        if self.vector_store.count() == 0:
            return {
                "answer": "知识库目前没有可用资料，暂时无法回答。",
                "sources": [],
                "retrieved_count": 0
            }

        # 2. 从 Chroma 检索相关知识
        search_results = self.vector_store.search(
            query=question,
            top_k=self.top_k
        )

        # 3. 根据余弦距离过滤低相关性结果
        relevant_results = [
            result
            for result in search_results
            if result["distance"] <= self.max_distance
        ]

        # 4. 如果没有足够相关的知识，不调用大模型
        if not relevant_results:
            return {
                "answer": (
                    "抱歉，当前商品知识库中没有找到足够相关的信息，"
                    "暂时无法准确回答这个问题。"
                ),
                "sources": [],
                "retrieved_count": 0
            }

        # 5. 整理检索到的知识，构建上下文
        context_parts = []

        for index, result in enumerate(relevant_results, start=1):
            metadata = result.get("metadata") or {}

            source = metadata.get("source", "未知来源")
            chunk_index = metadata.get("chunk_index", "未知")

            context_parts.append(
                f"""[资料 {index}]
来源：{source}
Chunk 编号：{chunk_index}
内容：
{result["content"]}
"""
            )

        context = "\n".join(context_parts)

        # 6. 构建 RAG Prompt
        prompt = f"""
请根据下面提供的商品知识库资料回答用户问题。

【商品知识库资料】
{context}

【用户问题】
{question}

【回答要求】
1. 只能依据商品知识库资料回答。
2. 不允许编造商品参数、价格、售后政策等信息。
3. 如果资料没有提供问题所需的信息，请明确说明资料中没有相关信息。
4. 回答使用自然、简洁的中文。
5. 如果涉及具体商品参数，请尽量保留原始数值和单位。
6. 不要把推测当作事实。
"""

        # 7. 调用 Qwen 生成答案
        answer = self.llm.chat(
            prompt=prompt,
            system_prompt=(
                "你是一个严谨的电商商品知识库客服助手。"
                "你必须以提供的知识库资料为依据，"
                "不能使用资料之外的信息编造答案。"
            )
        )

        # 8. 返回答案和来源信息
        return {
            "answer": answer,
            "sources": relevant_results,
            "retrieved_count": len(relevant_results)
        }