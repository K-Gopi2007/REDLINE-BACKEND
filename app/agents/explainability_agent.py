from app.services.gemini import gemini_service

class ExplainabilityAgent:
    @staticmethod
    def explain_clause(clause_content: str) -> str:
        system_instruction = (
            "You are an Explainability Agent. "
            "Your goal is to explain complex legal jargon and AI decisions in plain, simple English. "
            "Make it understandable for a non-lawyer without losing the core legal meaning."
        )
        return gemini_service.generate_content(
            prompt=f"Explain this legal text in plain English:\n\n{clause_content}",
            system_instruction=system_instruction
        )

explainability_agent = ExplainabilityAgent()
