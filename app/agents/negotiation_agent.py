from app.services.gemini import gemini_service
from app.schemas.contract import NegotiationReportResponse

class NegotiationAgent:
    @staticmethod
    def suggest_negotiations(contract_content: str) -> NegotiationReportResponse:
        system_instruction = (
            "You are an expert Legal Negotiation Agent. "
            "Review the contract and identify clauses that are unfavorable or risky. "
            "Provide the original clause, a suggested safer clause, and reasoning for the change."
        )
        return gemini_service.generate_structured(
            prompt=f"Provide negotiation recommendations for this contract:\n\n{contract_content}",
            response_schema=NegotiationReportResponse,
            system_instruction=system_instruction
        )

negotiation_agent = NegotiationAgent()
