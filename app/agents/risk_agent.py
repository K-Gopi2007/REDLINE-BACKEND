from app.services.gemini import gemini_service
from app.schemas.contract import RiskReportResponse

class RiskAgent:
    @staticmethod
    def analyze_risk(contract_content: str) -> RiskReportResponse:
        system_instruction = (
            "You are an expert Legal Risk Analysis Agent. "
            "Analyze the contract for the following risks: Payment Risk, Liability Risk, Termination Risk, Confidentiality Risk, Intellectual Property Risk. "
            "Calculate a risk_score from 0 to 100. "
            "Determine risk_level as LOW, MEDIUM, or HIGH. "
            "Identify specific issues, map them to a severity (LOW/MEDIUM/HIGH), and explain the reason."
        )
        return gemini_service.generate_structured(
            prompt=f"Analyze this contract for risks:\n\n{contract_content}",
            response_schema=RiskReportResponse,
            system_instruction=system_instruction
        )

risk_agent = RiskAgent()
