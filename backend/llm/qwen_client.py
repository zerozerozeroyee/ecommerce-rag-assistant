import os

from dotenv import load_dotenv
from openai import OpenAI


# 加载项目根目录下的 .env
load_dotenv()


class QwenClient:
    """千问 AI 大模型客户端"""

    def __init__(self):
        api_key = os.getenv("QWEN_API_KEY")
        base_url = os.getenv("QWEN_BASE_URL")
        self.model = os.getenv(
            "QWEN_MODEL",
            "qwen3.8-flash"
        )

        if not api_key:
            raise ValueError(
                "未配置 QWEN_API_KEY，请检查 .env 文件"
            )

        if not base_url:
            raise ValueError(
                "未配置 QWEN_BASE_URL，请检查 .env 文件"
            )

        self.client = OpenAI(
            api_key=api_key,
            base_url=base_url
        )

    def chat(
        self,
        prompt: str,
        system_prompt: str = "你是一个专业的电商商品客服助手。"
    ) -> str:
        """调用千问模型生成回答"""

        if not prompt.strip():
            raise ValueError("用户问题不能为空")

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": system_prompt
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.3
        )

        answer = response.choices[0].message.content

        return answer or ""