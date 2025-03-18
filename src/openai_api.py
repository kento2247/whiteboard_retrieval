import os

from openai import OpenAI
from pydantic import BaseModel


class OpenaiApiClient:
    """環境変数から設定を取得し、OpenAIにリクエストを送信するクライアント"""

    def __init__(
        self,
        model: str = "davinci",
        max_tokens: int = 100,
        n: int = 1,
        stop: str = None,
    ):
        self.client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
        self.config = {
            "model": model,  # モデルを選択
            "max_tokens": max_tokens,  # 生成する文章の最大単語数
            "n": n,  # いくつの返答を生成するか
            "stop": stop,  # 指定した単語が出現した場合、文章生成を打ち切る
            "temperature": 0,  # 出力する単語のランダム性（0から2の範囲） 0であれば毎回返答内容固定
        }


if __name__ == "__main__":
    client = OpenaiApiClient()
    print(client.client.api_key)
