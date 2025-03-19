import base64
import json
import os

from mistralai import Mistral
from mistralai.models import OCRPageObject, OCRResponse
from pydantic import BaseModel


class DescribedImage(BaseModel):
    """英語での画像説明を表すクラス"""

    english_named_entity_list: list[str]  # 固有表現のリスト
    english_plain_text_description: str  # 画像の説明


class MistralModel:
    def __init__(self):
        self.client = Mistral(api_key=os.environ["MISTRAL_API_KEY"])
        self.config = {
            "max_tokens": 512,
            "temperature": 0,
            "model": "mistral-small-latest",
        }

    def ocr(self, image_url: str):
        pages: OCRResponse = self.client.ocr.process(
            model="mistral-ocr-latest",
            document={
                "type": "image_url",
                "image_url": image_url,
            },
        )
        page: OCRPageObject = pages.pages[0]
        return page.markdown

    def describe_image(self, image_url: str) -> DescribedImage:
        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "Describe the image in English."},
                    {"type": "image_url", "image_url": image_url},
                ],
            }
        ]
        response = self.client.chat.parse(
            messages=messages, **self.config, response_format=DescribedImage
        )
        response = response.choices[0].message.content
        response_dict = json.loads(response)
        return DescribedImage(**response_dict)

    def encode_image(self, image_path):
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


if __name__ == "__main__":
    mistral_model = MistralModel()
    base64_image = mistral_model.encode_image("images/IMG_0569.jpg")
    image_url = f"data:image/jpeg;base64,{base64_image}"

    description = mistral_model.describe_image(image_url)
    english_named_entity_list = description.english_named_entity_list
    english_plain_text_description = description.english_plain_text_description
    print(english_named_entity_list)
    print(english_plain_text_description)
