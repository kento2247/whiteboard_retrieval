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
    text1 = "The whiteboard contains detailed notes and diagrams related to machine learning concepts, specifically focusing on adaptive soft contrastive learning. Key terms and formulas are written in both English and another language, likely Korean. The board includes diagrams illustrating processes and relationships between different components such as cosine similarity, softmax, and entropy. There are references to models like ViLBERT and methods like MLM (Masked Language Modeling). Additionally, there are mathematical expressions and annotations explaining the adaptive soft labeling process, including the use of exponential functions and minimizations. The board also mentions other related techniques and models like SimCLR, MoCo, and Barlow Twins. Overall, the content appears to be a detailed explanation of advanced machine learning techniques and their mathematical foundations...."
    text2 = "apple"

    emb1 = embedder.embed_text(text1)
    emb2 = embedder.embed_text(text2)

    sim = np.dot(emb1, emb2) / (np.linalg.norm(emb1) * np.linalg.norm(emb2))
    print(sim)
