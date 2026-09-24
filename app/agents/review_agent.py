from app.services.gemini import gemini_service

class ReviewAgent:
    @staticmethod
    def review_contract(contract_content: str) -> str:
        system_instruction = (
            "You are an expert Legal Review Agent. "
            "Review the provided contract structure, identify any missing standard clauses, "
            "and suggest overall structural improvements."
        )
        return gemini_service.generate_content(
            prompt=f"Review this contract:\n\n{contract_content}", 
            system_instruction=system_instruction
        )

review_agent = ReviewAgent()
