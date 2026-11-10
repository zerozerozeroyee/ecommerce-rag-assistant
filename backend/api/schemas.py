from typing import Any, Dict, List

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """用户问答请求"""

    question: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="用户提出的商品问题"
    )


class SourceItem(BaseModel):
    """检索到的参考资料"""

    content: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    distance: float


class ChatResponse(BaseModel):
    """问答接口响应"""

    answer: str
    sources: List[SourceItem]
    retrieved_count: int


class UploadResponse(BaseModel):
    """知识库文件上传响应"""

    message: str
    filename: str
    parsed_documents: int
    chunk_count: int
    inserted_count: int
    knowledge_count: int