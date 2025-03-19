import numpy as np
from pydantic import BaseModel

from src.mistralai_api import ImageInfo, MistralModel, ProperNouns
from src.stella import StellaEmbedder


class ImageData(BaseModel):
    image_url: str
    description: str
    named_entity_list: list[str]
    description_feats: np.ndarray


class InstructionData(BaseModel):
    instruction: str
    proper_nouns: list[str]
    instruction_feats: np.ndarray


class Embedder:
    def __init__(self):
        self.stella = StellaEmbedder()
        self.mistral = MistralModel()

    def process_image(self, image_url) -> ImageData:
        image_info: ImageInfo = self.mistral.describe_image(image_url)
        english_named_entity_list = image_info.english_named_entity_list
        english_plain_text_description = image_info.english_plain_text_description
        description_feats = self.stella.embed_text(english_plain_text_description)
        return ImageData(
            image_url=image_url,
            description=english_plain_text_description,
            named_entity_list=english_named_entity_list,
            description_feats=description_feats,
        )

    def process_instruction(self, instruction) -> InstructionData:
        proper_nouns: ProperNouns = self.mistral.get_proper_nouns(instruction)
        english_proper_noun_list = proper_nouns.english_proper_noun_list
        instruction_feats = self.stella.embed_text(instruction)
        return InstructionData(
            instruction=instruction,
            proper_nouns=english_proper_noun_list,
            instruction_feats=instruction_feats,
        )
