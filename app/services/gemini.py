from google import genai
from google.genai import types
from app.core.config import settings
from typing import Type, Any, Optional
from pydantic import BaseModel

class GeminiService:
    def __init__(self):
        self.client = genai.Client(api_key=settings.GEMINI_API_KEY)
        self.model_id = 'gemini-3.8-flash'

    def generate_content(self, prompt: str, system_instruction: Optional[str] = None, response_schema: Optional[Any] = None) -> str:
        config_kwargs = {}
        if system_instruction:
            config_kwargs["system_instruction"] = system_instruction
            
        if response_schema:
            config_kwargs["response_mime_type"] = "application/json"
            config_kwargs["response_schema"] = response_schema
            
        config = types.GenerateContentConfig(**config_kwargs)

        response = self.client.models.generate_content(
            model=self.model_id,
            contents=prompt,
            config=config
        )
        return response.text

    def generate_structured(self, prompt: str, response_schema: Type[BaseModel], system_instruction: Optional[str] = None) -> BaseModel:
        response_text = self.generate_content(prompt, system_instruction, response_schema)
        return response_schema.model_validate_json(response_text)

gemini_service = GeminiService()
