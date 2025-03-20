from typing import List

import numpy as np
from pydantic import BaseModel, ConfigDict

from mistralai_api import ImageInfo, InstInfo, MistralModel
from stella import StellaEmbedder


# Custom type for numpy arrays
class NumpyArrayType:
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if isinstance(v, np.ndarray):
            return v
        raise TypeError("numpy.ndarray required")


class ImageData(BaseModel):
    image_path: str
    description: str
    ocr: List[str]
    description_feats: np.ndarray
    model_config = ConfigDict(arbitrary_types_allowed=True)


class InstructionData(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    instruction: str
    ocr: List[str]
    instruction_feats: np.ndarray
    model_config = ConfigDict(arbitrary_types_allowed=True)


class Processer:
    def __init__(self):
        self.stella = StellaEmbedder()
        self.mistral = MistralModel()

    def process_image(self, image_path: str) -> ImageData:
        image_info: ImageInfo = self.mistral.get_image_info(image_path)
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
        inst_info: InstInfo = self.mistral.get_inst_info(instruction)
        english_instruction = inst_info.english_instruction
        english_proper_noun_list = inst_info.english_proper_noun_list
        instruction_feats = self.stella.embed_text(english_instruction)

        return InstructionData(
            instruction=english_instruction,
            ocr=english_proper_noun_list,
            instruction_feats=instruction_feats,
        )


if __name__ == "__main__":
    processer = Processer()
    image_path = "images/IMG_0569.jpg"
    instruction = "対照学習"

    image_data = processer.process_image(image_path)
    instruction_data = processer.process_instruction(instruction)

    print(image_data.description)
    print(instruction_data.instruction)
