import numpy as np
import torch
from sentence_transformers import SentenceTransformer


class StellaEmbedder:
    def __init__(self):
        self.device = "cuda:0" if torch.cuda.is_available() else "cpu"
        self.model = SentenceTransformer(
            "dunzhang/stella_en_400M_v5", trust_remote_code=True
        ).to(self.device)

    def embed_text(self, text):
        result = self.model.encode(text)  ## stellaの出力は1024次元
        return np.array(result)


if __name__ == "__main__":
    embedder = StellaEmbedder()
    text = "I am a student."
    print(embedder.embed_text(text).shape)  ## (1024,)
