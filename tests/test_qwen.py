from backend.llm.qwen_client import QwenClient


def main():
    # 1. 初始化 Qwen 客户端
    qwen = QwenClient()

    # 2. 测试问题
    prompt = "你好，请简单介绍一下你自己。"

    # 3. 调用模型
    print("正在调用千问 AI API...")

    answer = qwen.chat(prompt)

    # 4. 输出回答
    print("\n========== Qwen 回答 ==========")
    print(answer)


if __name__ == "__main__":
    main()