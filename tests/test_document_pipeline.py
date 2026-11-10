from pathlib import Path

from backend.rag.document_loader import DocumentLoader
from backend.rag.text_cleaner import TextCleaner
from backend.rag.text_splitter import DocumentSplitter


def main():
    # 1. 获取测试文件
    file_path = Path("data/documents/product_faq.txt")

    # 2. 解析文档
    loader = DocumentLoader()
    documents = loader.load(str(file_path))

    print("\n========== 文档解析结果 ==========")
    print(f"解析出的文档数量：{len(documents)}")

    # 3. 文本清洗
    for document in documents:
        document.page_content = TextCleaner.clean(
            document.page_content
        )

    print("\n========== 文本清洗结果 ==========")

    if documents:
        print(documents[0].page_content[:200])

    # 4. 文本分块
    splitter = DocumentSplitter(
        chunk_size=200,
        chunk_overlap=40
    )

    chunks = splitter.split_documents(documents)

    print("\n========== Chunk 分块结果 ==========")
    print(f"Chunk 数量：{len(chunks)}")

    # 5. 查看每个 Chunk
    for index, chunk in enumerate(chunks):
        print(f"\n--- Chunk {index + 1} ---")

        print("内容：")
        print(chunk.page_content)

        print("Metadata：")
        print(chunk.metadata)


if __name__ == "__main__":
    main()