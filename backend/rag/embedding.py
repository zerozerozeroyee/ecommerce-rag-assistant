from typing import List

import numpy as np
from sentence_transformers import SentenceTransformer


class BGEEmbedding:
    """使用 BGE 模型将文本转换为向量"""

    def __init__(
        self,
        model_name: str = "BAAI/bge-small-zh-v1.5"
    ):
        self.model = SentenceTransformer(model_name)

    def embed_texts(
        self,
        texts: List[str]
    ) -> List[List[float]]:
        """将多个文本转换为向量"""

        if not texts:
            return []

        embeddings = self.model.encode(
            texts,
            normalize_embeddings=True,
            convert_to_numpy=True,
            show_progress_bar=True
        )

        return embeddings.astype(np.float32).tolist()

    def embed_query(self, text: str) -> List[float]:
        """将用户问题转换为向量"""

        embeddings = self.model.encode(
            [text],
            normalize_embeddings=True,
            convert_to_numpy=True
        )

        return embeddings[0].astype(np.float32).tolist()