import base64
import os
import re

from mistralai import Mistral
from mistralai.models import OCRPageObject, OCRResponse


class MistralOCR:
    def __init__(self):
        self.client = Mistral(api_key=os.environ["MISTRAL_API_KEY"])

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
    mistral_ocr = MistralOCR()
    base64_image = mistral_ocr.encode_image("images/0.jpg")
    image_url = f"data:image/jpeg;base64,{base64_image}"
    markdown = mistral_ocr.ocr(image_url)
    print(markdown)
