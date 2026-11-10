import logging
from pathlib import Path

from fastapi import APIRouter, HTTPException, Request, UploadFile, File

from backend.api.schemas import (
    ChatRequest,
    ChatResponse,
    UploadResponse
)
from backend.rag.document_loader import DocumentLoader
from backend.rag.text_cleaner import TextCleaner
from backend.rag.text_splitter import DocumentSplitter


logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api",
    tags=["RAG 智能问答与知识库管理"]
)

# 上传文件保存目录
DOCUMENT_DIR = Path("data/documents")

# 允许上传的文件格式
ALLOWED_EXTENSIONS = {
    ".pdf",
    ".docx",
    ".xlsx",
    ".txt"
}

# 单个文件最大限制：10 MB
MAX_FILE_SIZE = 10 * 1024 * 1024


@router.post(
    "/chat",
    response_model=ChatResponse,
    summary="商品知识库智能问答"
)
def chat(
    request: ChatRequest,
    http_request: Request
):
    """调用 RAG 问答链回答用户问题"""

    rag_chain = getattr(
        http_request.app.state,
        "rag_chain",
        None
    )

    if rag_chain is None:
        raise HTTPException(
            status_code=503,
            detail="RAG 问答服务尚未初始化"
        )

    try:
        result = rag_chain.ask(request.question)

        return ChatResponse(
            answer=result["answer"],
            sources=result["sources"],
            retrieved_count=result["retrieved_count"]
        )

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error)
        )

    except Exception:
        logger.exception("RAG 问答处理失败")

        raise HTTPException(
            status_code=502,
            detail="问答服务暂时不可用，请稍后重试"
        )


@router.post(
    "/knowledge/upload",
    response_model=UploadResponse,
    summary="上传商品知识文档"
)
async def upload_knowledge(
    http_request: Request,
    file: UploadFile = File(...)
):
    """上传文档，自动解析、清洗、分块并写入向量数据库"""

    # 1. 检查向量数据库服务
    vector_store = getattr(
        http_request.app.state,
        "vector_store",
        None
    )

    if vector_store is None:
        raise HTTPException(
            status_code=503,
            detail="知识库服务尚未初始化"
        )

    # 2. 检查文件名和扩展名
    filename = Path(file.filename or "").name

    if not filename:
        raise HTTPException(
            status_code=400,
            detail="文件名不能为空"
        )

    suffix = Path(filename).suffix.lower()

    if suffix not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail="不支持的文件格式，仅支持 PDF、DOCX、XLSX、TXT"
        )

    # 3. 读取文件并限制大小
    content = await file.read()

    if not content:
        raise HTTPException(
            status_code=400,
            detail="上传文件不能为空"
        )

    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail="文件大小不能超过 10 MB"
        )

    # 4. 保存上传文件
    DOCUMENT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    file_path = DOCUMENT_DIR / filename

    try:
        file_path.write_bytes(content)

        # 5. 解析文档
        loader = DocumentLoader()
        documents = loader.load(str(file_path))

        if not documents:
            raise ValueError("文件中没有提取到有效文本")

        # 6. 清洗文本
        for document in documents:
            document.page_content = TextCleaner.clean(
                document.page_content
            )

        documents = [
            document
            for document in documents
            if document.page_content
        ]

        if not documents:
            raise ValueError("清洗后没有可用文本")

        # 7. 文档分块
        splitter = DocumentSplitter(
            chunk_size=200,
            chunk_overlap=40
        )

        chunks = splitter.split_documents(documents)

        if not chunks:
            raise ValueError("文档分块后没有可用内容")

        # 8. 写入 Chroma
        inserted_count = vector_store.add_documents(chunks)

        # 9. 返回结果
        return UploadResponse(
            message="知识文档上传并入库成功",
            filename=filename,
            parsed_documents=len(documents),
            chunk_count=len(chunks),
            inserted_count=inserted_count,
            knowledge_count=vector_store.count()
        )

    except (ValueError, FileNotFoundError) as error:
        logger.warning("文档处理失败：%s", error)

        raise HTTPException(
            status_code=400,
            detail=str(error)
        )

    except Exception:
        logger.exception("知识文档处理失败")

        raise HTTPException(
            status_code=500,
            detail="文档处理失败，请检查文件内容和服务日志"
        )

    finally:
        await file.close()


def _validate_filename(filename: str) -> str:
    """校验文件名，避免路径穿越"""

    if (
        not filename
        or filename in {".", ".."}
        or "/" in filename
        or "\\" in filename
        or Path(filename).name != filename
    ):
        raise HTTPException(
            status_code=400,
            detail="文件名不合法"
        )

    if Path(filename).suffix.lower() not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail="不支持的文件格式"
        )

    return filename


def _load_and_split_file(file_path: Path):
    """解析、清洗和分块"""

    loader = DocumentLoader()
    documents = loader.load(str(file_path))

    if not documents:
        raise ValueError("文件中没有提取到有效文本")

    for document in documents:
        document.page_content = TextCleaner.clean(
            document.page_content
        )

    documents = [
        document
        for document in documents
        if document.page_content.strip()
    ]

    if not documents:
        raise ValueError("清洗后没有可用文本")

    splitter = DocumentSplitter(
        chunk_size=200,
        chunk_overlap=40
    )

    chunks = splitter.split_documents(documents)

    if not chunks:
        raise ValueError("文档分块后没有可用内容")

    return documents, chunks


@router.get(
    "/knowledge/files",
    summary="获取知识库文件列表"
)
def list_knowledge_files(request: Request):
    """获取磁盘文件和向量索引文件"""

    vector_store = getattr(
        request.app.state,
        "vector_store",
        None
    )

    if vector_store is None:
        raise HTTPException(
            status_code=503,
            detail="知识库服务尚未初始化"
        )

    try:
        DOCUMENT_DIR.mkdir(
            parents=True,
            exist_ok=True
        )

        indexed_files = vector_store.get_source_files()

        indexed_map = {
            item["filename"]: item
            for item in indexed_files
        }

        disk_files = {}

        for file_path in DOCUMENT_DIR.iterdir():
            if (
                file_path.is_file()
                and file_path.suffix.lower() in ALLOWED_EXTENSIONS
            ):
                disk_files[file_path.name] = file_path

        all_filenames = set(disk_files) | set(indexed_map)

        files = []

        for filename in sorted(all_filenames):
            file_path = disk_files.get(filename)
            indexed_info = indexed_map.get(filename)

            files.append({
                "filename": filename,
                "file_type": (
                    file_path.suffix.lower().lstrip(".")
                    if file_path
                    else indexed_info.get("file_type", "")
                ),
                "file_size": (
                    file_path.stat().st_size
                    if file_path
                    else 0
                ),
                "chunk_count": (
                    indexed_info["chunk_count"]
                    if indexed_info
                    else 0
                ),
                "indexed": indexed_info is not None,
                "exists_on_disk": file_path is not None
            })

        return {
            "total": len(files),
            "files": files
        }

    except Exception:
        logger.exception("获取知识库文件列表失败")

        raise HTTPException(
            status_code=500,
            detail="获取文件列表失败"
        )


@router.delete(
    "/knowledge/files/{filename}",
    summary="删除知识库文件"
)
def delete_knowledge_file(
    filename: str,
    request: Request
):
    """删除原始文件及其对应的向量数据"""

    filename = _validate_filename(filename)

    vector_store = getattr(
        request.app.state,
        "vector_store",
        None
    )

    if vector_store is None:
        raise HTTPException(
            status_code=503,
            detail="知识库服务尚未初始化"
        )

    file_path = DOCUMENT_DIR / filename

    try:
        chunk_count = vector_store.count_by_source(filename)

        if not file_path.is_file() and chunk_count == 0:
            raise HTTPException(
                status_code=404,
                detail="文件不存在，且没有对应的索引记录"
            )

        deleted_count = vector_store.delete_by_source(filename)

        if file_path.is_file():
            file_path.unlink()

        return {
            "message": "文件及其向量数据删除成功",
            "filename": filename,
            "deleted_chunks": deleted_count
        }

    except HTTPException:
        raise

    except Exception:
        logger.exception("删除知识库文件失败：%s", filename)

        raise HTTPException(
            status_code=500,
            detail="删除文件失败，请检查服务日志"
        )


@router.post(
    "/knowledge/reindex/{filename}",
    summary="重新索引知识库文件"
)
def reindex_knowledge_file(
    filename: str,
    request: Request
):
    """重新解析文件并更新向量索引"""

    filename = _validate_filename(filename)

    vector_store = getattr(
        request.app.state,
        "vector_store",
        None
    )

    if vector_store is None:
        raise HTTPException(
            status_code=503,
            detail="知识库服务尚未初始化"
        )

    file_path = DOCUMENT_DIR / filename

    if not file_path.is_file():
        raise HTTPException(
            status_code=404,
            detail="原始文件不存在，无法重新索引"
        )

    try:
        documents, chunks = _load_and_split_file(file_path)

        inserted_count = vector_store.replace_documents(
            source=filename,
            documents=chunks
        )

        return {
            "message": "文件重新索引成功",
            "filename": filename,
            "parsed_documents": len(documents),
            "chunk_count": len(chunks),
            "inserted_count": inserted_count,
            "knowledge_count": vector_store.count()
        }

    except ValueError as error:
        logger.warning(
            "重新索引失败：%s，原因：%s",
            filename,
            error
        )

        raise HTTPException(
            status_code=400,
            detail=str(error)
        )

    except Exception:
        logger.exception("重新索引失败：%s", filename)

        raise HTTPException(
            status_code=500,
            detail="重新索引失败，请检查服务日志"
        )