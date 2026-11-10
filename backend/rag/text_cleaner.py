import re
import unicodedata


class TextCleaner:
    """负责清洗文档中的无效字符和空白内容"""

    @staticmethod
    def clean(text: str) -> str:
        if not text:
            return ""

        # 统一 Unicode 字符形式
        text = unicodedata.normalize("NFKC", text)

        # 统一换行符
        text = text.replace("\r\n", "\n")
        text = text.replace("\r", "\n")

        # 删除空字符
        text = text.replace("\x00", "")

        # 统一特殊空格
        text = text.replace("\u00a0", " ")

        # 删除每行首尾空格
        lines = [
            line.strip()
            for line in text.split("\n")
        ]

        # 连续多个空行压缩成最多一个空行
        text = "\n".join(lines)
        text = re.sub(r"\n{3,}", "\n\n", text)

        # 删除文本首尾空白
        return text.strip()