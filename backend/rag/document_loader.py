from pathlib import Path
from typing import List

# import fitz
import pymupdf
import pymupdf
from docx import Document as DocxDocument
from openpyxl import load_workbook

from backend.rag.document import Document


class DocumentLoader:
    """负责解析不同格式的商品知识文档"""

    SUPPORTED_EXTENSIONS = {
        ".pdf",
        ".docx",
        ".xlsx",
        ".txt"
    }

    def load(self, file_path: str) -> List[Document]:
        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(f"文件不存在：{file_path}")

        suffix = path.suffix.lower()

        if suffix not in self.SUPPORTED_EXTENSIONS:
            raise ValueError(f"暂不支持的文件格式：{suffix}")

        if suffix == ".pdf":
            return self._load_pdf(path)

        if suffix == ".docx":
            return self._load_docx(path)

        if suffix == ".xlsx":
            return self._load_excel(path)

        if suffix == ".txt":
            return self._load_txt(path)

        return []

    def _load_pdf(self, path: Path) -> List[Document]:
        documents = []

        # with fitz.open(path) as pdf:
        with pymupdf.open(path) as pdf:
            for page_index, page in enumerate(pdf):
                text = page.get_text("text")

                if text.strip():
                    documents.append(
                        Document(
                            page_content=text,
                            metadata={
                                "source": path.name,
                                "file_type": "pdf",
                                "page": page_index + 1
                            }
                        )
                    )

        return documents

    def _load_docx(self, path: Path) -> List[Document]:
        doc = DocxDocument(path)

        contents = []

        # 提取普通段落
        for paragraph in doc.paragraphs:
            text = paragraph.text.strip()

            if text:
                contents.append(text)

        # 提取表格
        for table in doc.tables:
            for row in table.rows:
                values = [
                    cell.text.strip()
                    for cell in row.cells
                ]

                if any(values):
                    contents.append(" | ".join(values))

        text = "\n".join(contents)

        if not text.strip():
            return []

        return [
            Document(
                page_content=text,
                metadata={
                    "source": path.name,
                    "file_type": "docx"
                }
            )
        ]

    def _load_excel(self, path: Path) -> List[Document]:
        documents = []

        workbook = load_workbook(
            filename=path,
            read_only=True,
            data_only=True
        )

        try:
            for sheet in workbook.worksheets:
                rows = sheet.iter_rows(values_only=True)

                headers = next(rows, None)

                if not headers:
                    continue

                headers = [
                    str(value).strip() if value is not None else ""
                    for value in headers
                ]

                for row_index, row in enumerate(rows, start=2):
                    fields = []

                    for header, value in zip(headers, row):
                        if value is not None:
                            fields.append(
                                f"{header}：{value}"
                            )

                    if not fields:
                        continue

                    text = "\n".join(fields)

                    documents.append(
                        Document(
                            page_content=text,
                            metadata={
                                "source": path.name,
                                "file_type": "xlsx",
                                "sheet": sheet.title,
                                "row": row_index
                            }
                        )
                    )

        finally:
            workbook.close()

        return documents

    def _load_txt(self, path: Path) -> List[Document]:
        content = None

        for encoding in ("utf-8", "utf-8-sig", "gb18030"):
            try:
                content = path.read_text(encoding=encoding)
                break
            except UnicodeDecodeError:
                continue

        if content is None:
            raise ValueError(
                f"无法识别 TXT 文件编码：{path.name}"
            )

        if not content.strip():
            return []

        return [
            Document(
                page_content=content,
                metadata={
                    "source": path.name,
                    "file_type": "txt"
                }
            )
        ]