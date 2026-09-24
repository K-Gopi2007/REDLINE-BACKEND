from app.services.gemini import gemini_service

class DraftAgent:
    @staticmethod
    def draft_contract(prompt: str) -> str:
        system_instruction = (
            "You are an expert Legal Draft Agent. "
            "Your task is to generate a comprehensive, professional legal contract based on the user's natural language request. "
            "Ensure standard legal formatting, clear terms, and appropriate protective clauses for the party requesting it."
        )
        return gemini_service.generate_content(prompt, system_instruction=system_instruction)

draft_agent = DraftAgent()
