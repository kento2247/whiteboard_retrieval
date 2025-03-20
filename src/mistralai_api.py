import base64
import json
import os

from mistralai import Mistral
from mistralai.models import OCRPageObject, OCRResponse
from pydantic import BaseModel


class ImageInfo(BaseModel):
    """英語での画像説明を表すクラス"""

    english_named_entity_list: list[str]  # 固有表現のリスト
    english_plain_text_description: str  # 画像の説明


class InstInfo(BaseModel):
    """英語での指示文を表すクラス"""

    english_instruction: str  # 英語の指示文
    english_proper_noun_list: list[str]


class MistralModel:
    def __init__(self):
        self.client = Mistral(api_key=os.environ["MISTRAL_API_KEY"])
        self.config = {
            "max_tokens": 512,
            "temperature": 0,
            "model": "mistral-small-latest",
        }

    def ocr(self, image_url: str) -> str:
        """OCRを実行し、結果を取得する"""
        pages: OCRResponse = self.client.ocr.process(
            model="mistral-ocr-latest",
            document={
                "type": "image_url",
                "image_url": image_url,
            },
        )
        page: OCRPageObject = pages.pages[0]
        return page.markdown

    def get_image_info(self, image_path: str) -> ImageInfo:
        """画像の説明を取得する"""
        base64_image = self.encode_image(image_path)
        image_url = f"data:image/jpeg;base64,{base64_image}"
        messages = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "Describe in detail the content written on the whiteboard.",
                    },
                    {"type": "image_url", "image_url": image_url},
                ],
            }
        ]
        config = self.config
        config["response_format"] = ImageInfo
        response = self.client.chat.parse(messages=messages, **config)
        response = response.choices[0].message.content
        response_dict = json.loads(response)
        return ImageInfo(**response_dict)

    def encode_image(self, image_path: str) -> str:
        """Encode the image to base64."""
        try:
            with open(image_path, "rb") as image_file:
                return base64.b64encode(image_file.read()).decode("utf-8")
        except FileNotFoundError:
            print(f"Error: The file {image_path} was not found.")
            return None
        except Exception as e:  # Added general exception handling
            print(f"Error: {e}")
            return None

    def get_inst_info(self, instruction: str) -> InstInfo:
        """指示文から固有表現を取得する"""
        prompt = (
            "Translate the following instruction into English and extract all proper nouns. "
            "Provide the translation and the list of proper nouns in English. "
            f"instruction: {instruction}"
        )
        prompt = [
            {
                "role": "user",
                "content": prompt,
            },
        ]
        config = self.config
        config["response_format"] = InstInfo
        res = self.client.chat.parse(messages=prompt, **config)
        response = res.choices[0].message.content
        response_dict = json.loads(response)
        return InstInfo(**response_dict)


if __name__ == "__main__":
    mistral_model = MistralModel()

    # inst
    instruction = "対照学習について数式で議論をしたホワイトボードを検索してください。"
    instinfo: InstInfo = mistral_model.get_inst_info(instruction)
    print(instinfo.english_instruction)
    print(instinfo.english_proper_noun_list)

    # image
    base64_image = mistral_model.encode_image("images/IMG_0569.jpg")
    image_url = f"data:image/jpeg;base64,{base64_image}"

    image_info: ImageInfo = mistral_model.get_image_info(image_url)
    english_named_entity_list = image_info.english_named_entity_list
    english_plain_text_description = image_info.english_plain_text_description
    print(english_named_entity_list)
    print(english_plain_text_description)
