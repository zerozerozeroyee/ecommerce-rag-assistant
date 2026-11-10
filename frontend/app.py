# import os

# import requests
# import streamlit as st
# from dotenv import load_dotenv

# def get_knowledge_files():
#     """获取知识库文件列表"""

#     try:
#         response = requests.get(
#             f"{API_BASE_URL}/api/knowledge/files",
#             timeout=30
#         )

#         response.raise_for_status()

#         return response.json()

#     except requests.RequestException as e:
#         st.error(f"获取知识库文件失败：{e}")
#         return None


# def reindex_knowledge_file(filename):
#     """重新索引指定文件"""

#     try:
#         response = requests.post(
#             f"{API_BASE_URL}/api/knowledge/reindex/{filename}",
#             timeout=120
#         )

#         response.raise_for_status()

#         return response.json()

#     except requests.RequestException as e:
#         st.error(f"重新索引失败：{e}")
#         return None


# def delete_knowledge_file(filename):
#     """删除指定知识库文件"""

#     try:
#         response = requests.delete(
#             f"{API_BASE_URL}/api/knowledge/files/{filename}",
#             timeout=60
#         )

#         response.raise_for_status()

#         return response.json()

#     except requests.RequestException as e:
#         st.error(f"删除文件失败：{e}")
#         return None


# # 读取项目根目录的 .env 配置
# load_dotenv()

# API_BASE_URL = os.getenv(
#     "BACKEND_API_URL",
#     "http://127.0.0.1:8000"
# ).rstrip("/")


# # =========================
# # 页面基本配置
# # =========================

# st.set_page_config(
#     page_title="电商商品知识库智能客服",
#     page_icon="🛍️",
#     layout="wide"
# )


# # =========================
# # 初始化聊天记录
# # =========================

# if "messages" not in st.session_state:
#     st.session_state.messages = []


# # =========================
# # 页面标题
# # =========================

# st.title("🛍️ 电商商品知识库智能客服")

# st.caption(
#     "基于 RAG、BGE Embedding、Chroma 和 Qwen 构建的智能问答系统"
# )

# st.divider()


# # =========================
# # 侧边栏
# # =========================

# with st.sidebar:
#     st.header("系统信息")

#     st.write("**后端 API 地址**")
#     st.code(API_BASE_URL)

#     # 检查 FastAPI 是否正常
#     try:
#         health_response = requests.get(
#             f"{API_BASE_URL}/health",
#             timeout=3
#         )

#         if health_response.status_code == 200:
#             health_data = health_response.json()

#             if health_data.get("status") == "healthy":
#                 st.success("后端服务运行正常")
#                 st.metric(
#                     "知识库 Chunk 数量",
#                     health_data.get("knowledge_count", 0)
#                 )
#             else:
#                 st.warning("后端服务正在初始化")
#         else:
#             st.error("后端服务异常")

#     except requests.RequestException:
#         st.error("无法连接后端 API")

#     # =========================
#     # 知识库管理
#     # =========================

#     st.divider()

#     st.subheader("📚 知识库管理")

#     uploaded_file = st.file_uploader(
#         "上传商品知识文档",
#         type=["pdf", "docx", "xlsx", "txt"],
#         help="支持 PDF、Word、Excel 和 TXT，单个文件最大 10 MB"
#     )

#     if st.button(
#         "上传并更新知识库",
#         use_container_width=True,
#         disabled=uploaded_file is None
#     ):

#         with st.spinner("正在解析文档并更新知识库..."):

#             try:
#                 response = requests.post(
#                     f"{API_BASE_URL}/api/knowledge/upload",
#                     files={
#                         "file": (
#                             uploaded_file.name,
#                             uploaded_file.getvalue(),
#                             uploaded_file.type
#                         )
#                     },
#                     timeout=180
#                 )

#                 response.raise_for_status()

#                 result = response.json()

#                 st.success(result["message"])

#                 st.write(
#                     f"文件名称：{result['filename']}"
#                 )

#                 st.metric(
#                     "解析出的文档数量",
#                     result["parsed_documents"]
#                 )

#                 st.metric(
#                     "本次 Chunk 数量",
#                     result["chunk_count"]
#                 )

#                 st.metric(
#                     "知识库当前 Chunk 总数",
#                     result["knowledge_count"]
#                 )

#             except requests.HTTPError as error:
#                 try:
#                     detail = error.response.json().get(
#                         "detail",
#                         "文件上传失败"
#                     )
#                 except ValueError:
#                     detail = "文件上传失败"

#                 st.error(detail)

#             except requests.Timeout:
#                 st.error("文件处理超时，请稍后重试。")

#             except requests.RequestException:
#                 st.error("无法连接后端，请检查 FastAPI 是否正常运行。")

#     if st.button("🔄 刷新文件列表", use_container_width=True):

#         st.session_state["refresh_knowledge_files"] = True

#     if (
#         "refresh_knowledge_files" not in st.session_state
#         or st.session_state["refresh_knowledge_files"]
#     ):
#         file_data = get_knowledge_files()
#         st.session_state["refresh_knowledge_files"] = False
#     else:
#         file_data = get_knowledge_files()

#     if file_data:

#         files = file_data.get("files", [])

#         st.caption(
#             f"共 {file_data.get('total', 0)} 个文件"
#         )

#         if not files:
#             st.info("知识库中暂无文件")

#         for index, file in enumerate(files):

#             filename = file["filename"]

#             with st.expander(filename):

#                 st.write(
#                     f"文件类型：{file['file_type']}"
#                 )

#                 st.write(
#                     f"文件大小：{file['file_size']} Bytes"
#                 )

#                 st.write(
#                     f"Chunk 数量：{file['chunk_count']}"
#                 )

#                 if file["indexed"]:
#                     st.success("已建立向量索引")
#                 else:
#                     st.warning("尚未建立向量索引")

#                 if not file["exists_on_disk"]:
#                     st.error("原始文件不存在，无法重新索引")

#                 # 重新索引
#                 if st.button(
#                     "🔄 重新索引",
#                     key=f"reindex_{index}",
#                     disabled=not file["exists_on_disk"],
#                     use_container_width=True
#                 ):

#                     with st.spinner("正在重新索引..."):

#                         result = reindex_knowledge_file(filename)

#                     if result:
#                         st.success(result["message"])
#                         st.rerun()

#                 # 删除文件
#                 if st.button(
#                     "🗑️ 删除文件",
#                     key=f"delete_{index}",
#                     use_container_width=True
#                 ):

#                     st.session_state[
#                         f"confirm_delete_{index}"
#                     ] = True

#                 if st.session_state.get(
#                     f"confirm_delete_{index}",
#                     False
#                 ):

#                     st.warning(
#                         f"确定删除 {filename} 吗？此操作不可直接恢复。"
#                     )

#                     col1, col2 = st.columns(2)

#                     with col1:

#                         if st.button(
#                             "确认删除",
#                             key=f"confirm_{index}",
#                             type="primary"
#                         ):

#                             result = delete_knowledge_file(filename)

#                             if result:
#                                 st.success("文件删除成功")
#                                 st.session_state[
#                                     f"confirm_delete_{index}"
#                                 ] = False
#                                 st.rerun()

#                     with col2:

#                         if st.button(
#                             "取消",
#                             key=f"cancel_{index}"
#                         ):

#                             st.session_state[
#                                 f"confirm_delete_{index}"
#                             ] = False

#                             st.rerun()

#     st.divider()

#     st.subheader("功能说明")

#     st.write(
#         """
#         - 商品参数查询
#         - 商品功能咨询
#         - 售后政策查询
#         - 商品知识库语义检索
#         - 参考资料展示
#         """
#     )

#     st.divider()

#     if st.button("清空聊天记录", use_container_width=True):
#         st.session_state.messages = []
#         st.rerun()


# # =========================
# # 欢迎界面
# # =========================

# if not st.session_state.messages:
#     st.info(
#         "你好！我是电商商品智能客服，请输入你想了解的商品问题。"
#     )

#     st.subheader("你可以试着问我")

#     example_questions = [
#         "这款耳机的续航时间有多久？",
#         "这款耳机支持什么蓝牙版本？",
#         "这款耳机可以防水吗？",
#         "商品出现质量问题应该怎么办？"
#     ]

#     for question in example_questions:
#         st.markdown(f"- {question}")


# # =========================
# # 展示历史聊天记录
# # =========================

# for message in st.session_state.messages:

#     with st.chat_message(message["role"]):

#         st.markdown(message["content"])

#         # 如果是助手回答，展示参考资料
#         if message["role"] == "assistant":

#             sources = message.get("sources", [])

#             if sources:
#                 with st.expander(
#                     f"查看参考资料（{len(sources)} 条）"
#                 ):
#                     for index, source in enumerate(
#                         sources,
#                         start=1
#                     ):
#                         st.markdown(f"**参考资料 {index}**")

#                         st.write(source.get("content", ""))

#                         metadata = source.get("metadata", {})
#                         st.caption(
#                             f"来源：{metadata.get('source', '未知')} | "
#                             f"距离：{source.get('distance', 0):.4f}"
#                         )

#                         if index < len(sources):
#                             st.divider()


# # =========================
# # 用户输入
# # =========================

# question = st.chat_input("请输入你的商品问题...")


# if question:

#     # 1. 保存并显示用户问题
#     st.session_state.messages.append({
#         "role": "user",
#         "content": question
#     })

#     with st.chat_message("user"):
#         st.markdown(question)

#     # 2. 调用后端 RAG API
#     with st.chat_message("assistant"):

#         with st.spinner("正在检索商品知识并生成回答..."):

#             try:
#                 response = requests.post(
#                     f"{API_BASE_URL}/api/chat",
#                     json={
#                         "question": question
#                     },
#                     timeout=120
#                 )

#                 response.raise_for_status()

#                 result = response.json()

#                 answer = result.get(
#                     "answer",
#                     "暂时无法生成回答。"
#                 )

#                 sources = result.get("sources", [])

#                 # 3. 显示回答
#                 st.markdown(answer)

#                 # 4. 显示参考资料
#                 if sources:
#                     with st.expander(
#                         f"查看参考资料（{len(sources)} 条）"
#                     ):
#                         for index, source in enumerate(
#                             sources,
#                             start=1
#                         ):
#                             st.markdown(f"**参考资料 {index}**")

#                             st.write(source.get("content", ""))

#                             metadata = source.get("metadata", {})

#                             st.caption(
#                                 f"来源：{metadata.get('source', '未知')} | "
#                                 f"距离：{source.get('distance', 0):.4f}"
#                             )

#                             if index < len(sources):
#                                 st.divider()

#                 # 5. 保存助手回答
#                 st.session_state.messages.append({
#                     "role": "assistant",
#                     "content": answer,
#                     "sources": sources
#                 })

#             except requests.Timeout:
#                 error_message = "请求超时，请稍后重试。"

#                 st.error(error_message)

#                 st.session_state.messages.append({
#                     "role": "assistant",
#                     "content": error_message,
#                     "sources": []
#                 })

#             except requests.RequestException as error:
#                 error_message = (
#                     "暂时无法连接问答服务，请检查 FastAPI 是否正常运行。"
#                 )

#                 st.error(error_message)

#                 st.session_state.messages.append({
#                     "role": "assistant",
#                     "content": error_message,
#                     "sources": []
#                 })

#             except ValueError:
#                 error_message = "后端返回的数据格式异常，请检查 API 服务。"

#                 st.error(error_message)

#                 st.session_state.messages.append({
#                     "role": "assistant",
#                     "content": error_message,
#                     "sources": []
#                 })


import os
from urllib.parse import quote

import requests
import streamlit as st
from dotenv import load_dotenv


# =========================
# 环境配置
# =========================

load_dotenv()

API_BASE_URL = os.getenv(
    "BACKEND_API_URL",
    "http://127.0.0.1:8000"
).rstrip("/")


# =========================
# 页面基本配置
# =========================

st.set_page_config(
    page_title="电商商品知识库智能客服",
    page_icon="🛍️",
    layout="wide"
)


# =========================
# API 请求辅助函数
# =========================

def get_error_detail(error):
    """提取后端返回的错误信息"""

    try:
        return error.response.json().get(
            "detail",
            str(error)
        )
    except (ValueError, AttributeError):
        return str(error)


def get_knowledge_files():
    """获取知识库文件列表"""

    try:
        response = requests.get(
            f"{API_BASE_URL}/api/knowledge/files",
            timeout=30
        )

        response.raise_for_status()

        return response.json()

    except requests.HTTPError as error:
        st.error(
            f"获取文件列表失败：{get_error_detail(error)}"
        )

    except requests.Timeout:
        st.error("获取文件列表超时，请稍后重试。")

    except requests.RequestException:
        st.error("无法连接后端，请检查 FastAPI 是否正常运行。")

    return None


def reindex_knowledge_file(filename):
    """重新索引指定文件"""

    encoded_filename = quote(filename, safe="")

    try:
        response = requests.post(
            f"{API_BASE_URL}/api/knowledge/reindex/{encoded_filename}",
            timeout=180
        )

        response.raise_for_status()

        return response.json()

    except requests.HTTPError as error:
        st.error(
            f"重新索引失败：{get_error_detail(error)}"
        )

    except requests.Timeout:
        st.error("重新索引超时，请检查后端处理状态。")

    except requests.RequestException:
        st.error("无法连接后端，请检查 FastAPI 是否正常运行。")

    return None


def delete_knowledge_file(filename):
    """删除指定知识库文件"""

    encoded_filename = quote(filename, safe="")

    try:
        response = requests.delete(
            f"{API_BASE_URL}/api/knowledge/files/{encoded_filename}",
            timeout=60
        )

        response.raise_for_status()

        return response.json()

    except requests.HTTPError as error:
        st.error(
            f"删除文件失败：{get_error_detail(error)}"
        )

    except requests.Timeout:
        st.error("删除文件超时，请检查后端处理状态。")

    except requests.RequestException:
        st.error("无法连接后端，请检查 FastAPI 是否正常运行。")

    return None


def format_file_size(size):
    """格式化文件大小"""

    if size < 1024:
        return f"{size} B"

    if size < 1024 * 1024:
        return f"{size / 1024:.2f} KB"

    return f"{size / (1024 * 1024):.2f} MB"


# =========================
# 初始化 Session State
# =========================

if "messages" not in st.session_state:
    st.session_state.messages = []

if "knowledge_notice" not in st.session_state:
    st.session_state.knowledge_notice = None


# =========================
# 页面标题
# =========================

st.title("🛍️ 电商商品知识库智能客服")

st.caption(
    "基于 RAG、BGE Embedding、Chroma 和 Qwen 构建的智能问答系统"
)

st.divider()


# =========================
# 侧边栏
# =========================

with st.sidebar:

    st.header("系统信息")

    st.write("**后端 API 地址**")
    st.code(API_BASE_URL)

    # -------------------------
    # 后端健康检查
    # -------------------------

    try:
        health_response = requests.get(
            f"{API_BASE_URL}/health",
            timeout=3
        )

        if health_response.status_code == 200:

            health_data = health_response.json()

            if health_data.get("status") == "healthy":

                st.success("后端服务运行正常")

                st.metric(
                    "知识库 Chunk 数量",
                    health_data.get("knowledge_count", 0)
                )

            else:
                st.warning("后端服务正在初始化")

        else:
            st.error("后端服务异常")

    except requests.RequestException:
        st.error("无法连接后端 API")

    # -------------------------
    # 操作结果提示
    # -------------------------

    notice = st.session_state.knowledge_notice

    if notice:

        if notice["type"] == "success":
            st.success(notice["message"])

        elif notice["type"] == "error":
            st.error(notice["message"])

        st.session_state.knowledge_notice = None

    # =========================
    # 知识库管理
    # =========================

    st.divider()

    st.subheader("📚 知识库管理")

    # -------------------------
    # 文件上传
    # -------------------------

    uploaded_file = st.file_uploader(
        "上传商品知识文档",
        type=["pdf", "docx", "xlsx", "txt"],
        help="支持 PDF、Word、Excel 和 TXT，单个文件最大 10 MB"
    )

    if st.button(
        "上传并更新知识库",
        use_container_width=True,
        disabled=uploaded_file is None
    ):

        with st.spinner("正在解析文档并更新知识库..."):

            try:
                response = requests.post(
                    f"{API_BASE_URL}/api/knowledge/upload",
                    files={
                        "file": (
                            uploaded_file.name,
                            uploaded_file.getvalue(),
                            uploaded_file.type
                        )
                    },
                    timeout=180
                )

                response.raise_for_status()

                result = response.json()

                st.success(result["message"])

                st.write(
                    f"文件名称：{result['filename']}"
                )

                col1, col2 = st.columns(2)

                with col1:
                    st.metric(
                        "解析出的文档数量",
                        result["parsed_documents"]
                    )

                with col2:
                    st.metric(
                        "本次 Chunk 数量",
                        result["chunk_count"]
                    )

                st.metric(
                    "知识库当前 Chunk 总数",
                    result["knowledge_count"]
                )

                # 上传完成后，下面的文件列表会重新请求后端

            except requests.HTTPError as error:

                st.error(
                    f"文件上传失败：{get_error_detail(error)}"
                )

            except requests.Timeout:
                st.error("文件处理超时，请稍后重试。")

            except requests.RequestException:
                st.error(
                    "无法连接后端，请检查 FastAPI 是否正常运行。"
                )

            except (KeyError, ValueError):
                st.error("后端返回的数据格式异常。")

    # -------------------------
    # 文件列表
    # -------------------------

    st.divider()

    st.subheader("📂 已上传文件")

    st.button(
        "🔄 刷新文件列表",
        use_container_width=True,
        key="refresh_file_list"
    )

    # 每次 Streamlit 页面运行都会重新获取文件列表
    file_data = get_knowledge_files()

    if file_data is not None:

        files = file_data.get("files", [])

        total_files = file_data.get("total", 0)

        indexed_count = sum(
            1 for file in files
            if file.get("indexed", False)
        )

        col1, col2 = st.columns(2)

        with col1:
            st.metric(
                "文件总数",
                total_files
            )

        with col2:
            st.metric(
                "已索引文件",
                indexed_count
            )

        if not files:

            st.info("知识库中暂无文件")

        else:

            for file in files:

                filename = file["filename"]

                # 使用编码后的文件名生成稳定的组件 Key
                file_key = quote(filename, safe="")

                with st.expander(filename):

                    st.write(
                        f"文件类型：{file.get('file_type', '未知')}"
                    )

                    st.write(
                        "文件大小："
                        + format_file_size(
                            file.get("file_size", 0)
                        )
                    )

                    st.write(
                        f"Chunk 数量：{file.get('chunk_count', 0)}"
                    )

                    if file.get("indexed", False):
                        st.success("已建立向量索引")
                    else:
                        st.warning("尚未建立向量索引")

                    if not file.get("exists_on_disk", False):
                        st.error("原始文件不存在，无法重新索引")

                    # -------------------------
                    # 重新索引
                    # -------------------------

                    if st.button(
                        "🔄 重新索引",
                        key=f"reindex_{file_key}",
                        disabled=not file.get("exists_on_disk", False),
                        use_container_width=True
                    ):

                        with st.spinner(
                            f"正在重新索引 {filename}..."
                        ):

                            result = reindex_knowledge_file(filename)

                        if result:

                            st.session_state.knowledge_notice = {
                                "type": "success",
                                "message": (
                                    f"{filename} 重新索引成功，"
                                    f"本次处理 {result['chunk_count']} 个 Chunk。"
                                )
                            }

                            st.rerun()

                    # -------------------------
                    # 删除文件
                    # -------------------------

                    if st.button(
                        "🗑️ 删除文件",
                        key=f"delete_{file_key}",
                        use_container_width=True
                    ):

                        st.session_state[
                            f"confirm_delete_{file_key}"
                        ] = True

                    # -------------------------
                    # 删除二次确认
                    # -------------------------

                    if st.session_state.get(
                        f"confirm_delete_{file_key}",
                        False
                    ):

                        st.warning(
                            f"确定删除 {filename} 吗？"
                            "这将同时删除原始文件和对应的向量数据。"
                        )

                        col1, col2 = st.columns(2)

                        with col1:

                            if st.button(
                                "确认删除",
                                key=f"confirm_{file_key}",
                                type="primary",
                                use_container_width=True
                            ):

                                result = delete_knowledge_file(filename)

                                if result:

                                    st.session_state[
                                        f"confirm_delete_{file_key}"
                                    ] = False

                                    st.session_state.knowledge_notice = {
                                        "type": "success",
                                        "message": (
                                            f"{filename} 删除成功，"
                                            f"共删除 {result['deleted_chunks']} 个 Chunk。"
                                        )
                                    }

                                    st.rerun()

                        with col2:

                            if st.button(
                                "取消",
                                key=f"cancel_{file_key}",
                                use_container_width=True
                            ):

                                st.session_state[
                                    f"confirm_delete_{file_key}"
                                ] = False

                                st.rerun()

    # =========================
    # 功能说明
    # =========================

    st.divider()

    st.subheader("功能说明")

    st.write(
        """
        - 商品参数查询
        - 商品功能咨询
        - 售后政策查询
        - 商品知识库语义检索
        - 参考资料展示
        - 知识库文件管理
        """
    )

    st.divider()

    # -------------------------
    # 清空聊天记录
    # -------------------------

    if st.button(
        "清空聊天记录",
        use_container_width=True
    ):

        st.session_state.messages = []

        st.rerun()


# =========================
# 欢迎界面
# =========================

if not st.session_state.messages:

    st.info(
        "你好！我是电商商品智能客服，请输入你想了解的商品问题。"
    )

    st.subheader("你可以试着问我")

    example_questions = [
        "这款耳机的续航时间有多久？",
        "这款耳机支持什么蓝牙版本？",
        "这款耳机可以防水吗？",
        "商品出现质量问题应该怎么办？"
    ]

    for question in example_questions:
        st.markdown(f"- {question}")


# =========================
# 展示历史聊天记录
# =========================

for message in st.session_state.messages:

    with st.chat_message(message["role"]):

        st.markdown(message["content"])

        # 如果是助手回答，展示参考资料
        if message["role"] == "assistant":

            sources = message.get("sources", [])

            if sources:

                with st.expander(
                    f"查看参考资料（{len(sources)} 条）"
                ):

                    for index, source in enumerate(
                        sources,
                        start=1
                    ):

                        st.markdown(
                            f"**参考资料 {index}**"
                        )

                        st.write(
                            source.get("content", "")
                        )

                        metadata = source.get("metadata", {})

                        st.caption(
                            f"来源：{metadata.get('source', '未知')} | "
                            f"距离：{source.get('distance', 0):.4f}"
                        )

                        if index < len(sources):
                            st.divider()


# =========================
# 用户输入
# =========================

question = st.chat_input("请输入你的商品问题...")


if question:

    # 1. 保存并显示用户问题
    st.session_state.messages.append({
        "role": "user",
        "content": question
    })

    with st.chat_message("user"):
        st.markdown(question)

    # 2. 调用后端 RAG API
    with st.chat_message("assistant"):

        with st.spinner("正在检索商品知识并生成回答..."):

            try:
                response = requests.post(
                    f"{API_BASE_URL}/api/chat",
                    json={
                        "question": question
                    },
                    timeout=120
                )

                response.raise_for_status()

                result = response.json()

                answer = result.get(
                    "answer",
                    "暂时无法生成回答。"
                )

                sources = result.get("sources", [])

                # 3. 显示回答
                st.markdown(answer)

                # 4. 显示参考资料
                if sources:

                    with st.expander(
                        f"查看参考资料（{len(sources)} 条）"
                    ):

                        for index, source in enumerate(
                            sources,
                            start=1
                        ):

                            st.markdown(
                                f"**参考资料 {index}**"
                            )

                            st.write(
                                source.get("content", "")
                            )

                            metadata = source.get("metadata", {})

                            st.caption(
                                f"来源：{metadata.get('source', '未知')} | "
                                f"距离：{source.get('distance', 0):.4f}"
                            )

                            if index < len(sources):
                                st.divider()

                # 5. 保存助手回答
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": answer,
                    "sources": sources
                })

            except requests.Timeout:

                error_message = "请求超时，请稍后重试。"

                st.error(error_message)

                st.session_state.messages.append({
                    "role": "assistant",
                    "content": error_message,
                    "sources": []
                })

            except requests.HTTPError as error:

                error_message = (
                    f"问答请求失败：{get_error_detail(error)}"
                )

                st.error(error_message)

                st.session_state.messages.append({
                    "role": "assistant",
                    "content": error_message,
                    "sources": []
                })

            except requests.RequestException:

                error_message = (
                    "暂时无法连接问答服务，请检查 FastAPI 是否正常运行。"
                )

                st.error(error_message)

                st.session_state.messages.append({
                    "role": "assistant",
                    "content": error_message,
                    "sources": []
                })

            except ValueError:

                error_message = (
                    "后端返回的数据格式异常，请检查 API 服务。"
                )

                st.error(error_message)

                st.session_state.messages.append({
                    "role": "assistant",
                    "content": error_message,
                    "sources": []
                })