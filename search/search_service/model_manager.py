import torch
from transformers import CLIPModel, CLIPProcessor
from django.conf import settings


class CLIPModelManager:
    _instance = None
    _model = None
    _processor = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def load_model(self):
        if self._model is None or self._processor is None:
            self._model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
            self._processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")

            # Используем GPU если доступен
            if torch.cuda.is_available():
                self._model = self._model.cuda()
                print("gpu on")

            # Переводим в режим оценки
            self._model.eval()
            print("CLIP model loaded successfully")

    def get_embedding(self, image):
        if self._model is None:
            self.load_model()

        inputs = self._processor(images=image, return_tensors="pt")

        # Перемещаем на GPU если доступно
        if torch.cuda.is_available():
            inputs = {k: v.cuda() for k, v in inputs.items()}

        with torch.no_grad():
            image_features = self._model.get_image_features(**inputs)
            embedding = image_features.cpu().numpy()[0].tolist()

        return embedding


# Глобальный экземпляр менеджера моделей
clip_manager = CLIPModelManager()
