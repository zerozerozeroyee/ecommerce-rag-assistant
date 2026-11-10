from pathlib import Path

from backend.rag.document_loader import DocumentLoader
from backend.rag.text_cleaner import TextCleaner
from backend.rag.text_splitter import DocumentSplitter
from backend.rag.vector_store import ChromaVectorStore


def main():
    # 1. 解析文档
    file_path = Path("data/documents/product_faq.txt")

    loader = DocumentLoader()
    documents = loader.load(str(file_path))

    # 2. 清洗文本
    for document in documents:
        document.page_content = TextCleaner.clean(
            document.page_content
        )

    # 3. 文档分块
    splitter = DocumentSplitter(
        chunk_size=200,
        chunk_overlap=40
    )

    chunks = splitter.split_documents(documents)

    print(f"文档分块数量：{len(chunks)}")

    # 4. 初始化向量数据库
    vector_store = ChromaVectorStore(
        persist_directory="data/vector_db",
        collection_name="product_knowledge"
    )

    # 5. 写入向量数据库
    inserted_count = vector_store.add_documents(chunks)

    print(f"本次写入 Chunk 数量：{inserted_count}")
    print(f"数据库当前 Chunk 数量：{vector_store.count()}")

    # 6. 测试语义检索
    query = "这款耳机的续航时间有多久？"

    print(f"\n用户问题：{query}")
    print("\n========== 检索结果 ==========")

    results = vector_store.search(
        query=query,
        top_k=3
    )

    for index, result in enumerate(results, start=1):
        print(f"\n--- 结果 {index} ---")
        print(f"内容：{result['content']}")
        print(f"距离：{result['distance']:.4f}")
        print(f"Metadata：{result['metadata']}")


if __name__ == "__main__":
    main()