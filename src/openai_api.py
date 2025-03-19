import os

from openai import OpenAI
from pydantic import BaseModel


class NamedEntities(BaseModel):
    """固有表現を表すクラス"""

    english_named_entity_list: list[str]


class ImageDescription(BaseModel):
    """英語での画像説明を表すクラス"""

    english_image_description: str


class OpenaiApiClient:
    """環境変数から設定を取得し、OpenAIにリクエストを送信するクライアント"""

    def __init__(
        self,
        model: str = "davinci",
        max_tokens: int = 512,
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

    def get_named_entities(self, instruction: str) -> NamedEntities:
        """指示文から固有表現を取得する"""
        prompt = (
            "Extract proper nouns from the following text. "
            "The output should be translated into English. "
            "Instruction: " + instruction
        )
        prompt = [
            {
                "role": "user",
                "content": prompt,
            },
        ]
        config = self.config
        config["response_format"] = NamedEntities
        res = self.client.beta.chat.completions.parse(messages=prompt, **config)
        response = res.choices[0].message.content
        return response

    def get_image_description(
        self, image_path: str, ocr_text_list: list[str]
    ) -> ImageDescription:
        """画像のパスとOCR結果から画像説明を取得する"""
        prompt = (
            "Describe the image in English. "
            "The output should be translated into English. "
            "Texts in the image: " + " ".join(ocr_text_list)
        )
        base64_image = open(image_path, "rb").read().encode("base64")
        prompt = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": prompt,
                    },
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/png;base64,{base64_image}"},
                    },
                ],
            }
        ]
        config = self.config
        config["response_format"] = ImageDescription

        res = self.client.beta.chat.completions.parse(messages=prompt, **config)
        response = res.choices[0].message.content
        return response


if __name__ == "__main__":
    client = OpenaiApiClient()
    print(client.client.api_key)
