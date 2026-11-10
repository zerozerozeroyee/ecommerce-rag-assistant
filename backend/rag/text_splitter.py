from typing import List

from langchain_text_splitters import RecursiveCharacterTextSplitter

from backend.rag.document import Document


class DocumentSplitter:
    """负责将长文档切分为多个 Chunk"""

    def __init__(
        self,
        chunk_size: int = 500,
        chunk_overlap: int = 100
    ):
        if chunk_size <= 0:
            raise ValueError("chunk_size 必须大于 0")

        if chunk_overlap < 0:
            raise ValueError("chunk_overlap 不能小于 0")

        if chunk_overlap >= chunk_size:
            raise ValueError(
                "chunk_overlap 必须小于 chunk_size"
            )

        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            separators=[
                "\n\n",
                "\n",
                "。",
                "！",
                "？",
                "；",
                "，",
                " ",
                ""
            ]
        )

    def split_documents(
        self,
        documents: List[Document]
    ) -> List[Document]:

        chunks = []

        for document in documents:
            text_chunks = self.splitter.split_text(
                document.page_content
            )

            for index, text in enumerate(text_chunks):
                metadata = document.metadata.copy()

                metadata.update({
                    "chunk_index": index,
                    "chunk_size": len(text)
                })

                chunks.append(
                    Document(
                        page_content=text,
                        metadata=metadata
                    )
                )

        return chunks