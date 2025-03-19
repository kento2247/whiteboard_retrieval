import os

from mistralai import Mistral


class MistralOCR:
    def __init__(self):
        self.client = Mistral(api_key=os.environ["MISTRAL_API_KEY"])

    def ocr(self, image_url: str):
        ocr_response = self.client.ocr.process(
            model="mistral-ocr-latest",
            document={
                "type": "image_url",
                "image_url": image_url,
            },
        )
        return ocr_response


if __name__ == "__main__":
    mistral_ocr = MistralOCR()
    ocr_response = mistral_ocr.ocr(
        "https://raw.githubusercontent.com/mistralai/cookbook/refs/heads/main/mistral/ocr/receipt.png"
    )
    print(ocr_response)
