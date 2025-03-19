import numpy as np
from pydantic import BaseModel

from mistralai_api import ImageInfo, MistralModel, ProperNouns
from stella import StellaEmbedder


class ImageData(BaseModel):
    image_path: str
    description: str
    ocr: list[str]
    description_feats: np.ndarray


class InstructionData(BaseModel):
    instruction: str
    ocr: list[str]
    instruction_feats: np.ndarray


class Processer:
    def __init__(self):
        self.stella = StellaEmbedder()
        self.mistral = MistralModel()

    def process_image(self, image_path: str) -> ImageData:
        image_info: ImageInfo = self.mistral.describe_image(image_path)
        english_named_entity_list = image_info.english_named_entity_list
        english_plain_text_description = image_info.english_plain_text_description
        description_feats = self.stella.embed_text(english_plain_text_description)
        return ImageData(
            image_path=image_path,
            description=english_plain_text_description,
            ocr=english_named_entity_list,
            description_feats=description_feats,
        )

    def process_instruction(self, instruction: str) -> InstructionData:
        proper_nouns: ProperNouns = self.mistral.get_proper_nouns(instruction)
        english_proper_noun_list = proper_nouns.english_proper_noun_list
        instruction_feats = self.stella.embed_text(instruction)
        return InstructionData(
            instruction=instruction,
            ocr=english_proper_noun_list,
            instruction_feats=instruction_feats,
        )


if __name__ == "__main__":
    processer = Processer()
    image_path = "images/IMG_0569.jpg"
    instruction = (
        "対照学習の新規性について数式で議論をしたホワイトボードを検索してください。"
    )

    image_data = processer.process_image(image_path)
    instruction_data = processer.process_instruction(instruction)

    print(image_data)
    print(instruction_data)
