# from fastapi import FastAPI

# app = FastAPI(
#     title="Ecommerce RAG Assistant",
#     description="基于 RAG 的电商商品知识库智能问答系统",
#     version="1.0.0"
# )


# @app.get("/")
# async def root():
#     return {
#         "message": "Ecommerce RAG Assistant is running!",
#         "status": "success"
#     }


# @app.get("/health")
# async def health_check():
#     return {
#         "status": "healthy"
#     }

from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI

from backend.api.routes import router
from backend.llm.qwen_client import QwenClient
from backend.rag.rag_chain import RAGChain
from backend.rag.vector_store import ChromaVectorStore


logging.basicConfig(level=logging.INFO)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用启动时初始化 RAG 服务"""

    logging.info("正在初始化 RAG 服务...")

    # 初始化 Chroma 向量数据库
    vector_store = ChromaVectorStore(
        persist_directory="data/vector_db",
        collection_name="product_knowledge"
    )

    # 将向量数据库保存到应用状态
    app.state.vector_store = vector_store

    # 初始化 Qwen 客户端
    qwen = QwenClient()

    # 创建 RAG 问答链
    app.state.rag_chain = RAGChain(
        vector_store=vector_store,
        llm=qwen,
        top_k=3,
        max_distance=0.65
    )

    logging.info(
        "RAG 服务初始化完成，知识库 Chunk 数量：%s",
        vector_store.count()
    )

    yield

    logging.info("RAG 服务已关闭")


app = FastAPI(
    title="电商商品知识库智能问答系统",
    description="基于 BGE、Chroma 和 Qwen 的 RAG 智能问答系统",
    version="1.0.0",
    lifespan=lifespan
)

# 注册问答路由
app.include_router(router)


@app.get("/", tags=["系统"])
def root():
    return {
        "message": "电商商品知识库智能问答系统运行中",
        "docs": "/docs"
    }


@app.get("/health", tags=["系统"])
def health():
    rag_chain = getattr(
        app.state,
        "rag_chain",
        None
    )

    if rag_chain is None:
        return {
            "status": "initializing"
        }

    return {
        "status": "healthy",
        "knowledge_count": rag_chain.vector_store.count()
    }