from src.mistralai_api import ImageInfo, MistralModel, ProperNouns
from src.stella import StellaEmbedder


class Embedder:
    def __init__(self):
        self.stella = StellaEmbedder()
        self.mistral = MistralModel()

    def embed_text(self, text):
        return self.stella.embed_text(text)

    def describe_image(self, image_url):
        image_info: ImageInfo = self.mistral.describe_image(image_url)
        english_named_entity_list = image_info.english_named_entity_list
        english_plain_text_description = image_info.english_plain_text_description

    def get_proper_nouns(self, instruction):
        proper_nouns: ProperNouns = self.mistral.get_proper_nouns(instruction)
        english_proper_noun_list = proper_nouns.english_proper_noun_list
