from backend.llm.qwen_client import QwenClient
from backend.rag.vector_store import ChromaVectorStore
from backend.rag.rag_chain import RAGChain


def main():
    # 1. 初始化 Chroma 向量数据库
    vector_store = ChromaVectorStore(
        persist_directory="data/vector_db",
        collection_name="product_knowledge"
    )

    print(f"知识库当前 Chunk 数量：{vector_store.count()}")

    # 2. 初始化 Qwen 客户端
    qwen = QwenClient()

    # 3. 创建 RAG 问答链
    rag = RAGChain(
        vector_store=vector_store,
        llm=qwen,
        top_k=3,
        max_distance=0.65
    )

    # 4. 测试问题
    questions = [
        "这款耳机的续航时间有多久？",
        "这款耳机支持什么蓝牙版本？",
        "这款耳机的价格是多少？"
    ]

    # 5. 逐个提问
    for question in questions:
        print("\n" + "=" * 50)
        print(f"用户问题：{question}")

        result = rag.ask(question)

        print("\nQwen 回答：")
        print(result["answer"])

        print("\n检索到的相关知识数量：")
        print(result["retrieved_count"])

        print("\n参考资料：")

        for index, source in enumerate(
            result["sources"],
            start=1
        ):
            print(f"\n--- 资料 {index} ---")
            print(f"内容：{source['content']}")
            print(f"距离：{source['distance']:.4f}")
            print(f"来源：{source['metadata']}")

    print("\nRAG 问答测试完成！")


if __name__ == "__main__":
    main()