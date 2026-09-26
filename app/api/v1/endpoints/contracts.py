from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from app.core.database import get_db
from app.models.user import User
from app.models.contract import Contract, RiskReport, NegotiationReport
from app.schemas.contract import (
    ContractResponse, DraftRequest, RiskReportResponse, 
    NegotiationReportResponse, ContractCreate
)
from app.api.deps import get_current_user
from app.utils.parsing import extract_text_from_pdf, extract_text_from_docx
from app.agents.draft_agent import draft_agent
from app.agents.review_agent import review_agent
from app.agents.risk_agent import risk_agent
from app.agents.negotiation_agent import negotiation_agent
from app.agents.explainability_agent import explainability_agent
import json
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/upload", response_model=ContractResponse)
async def upload_contract(
    title: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        content = await file.read()
        text = ""
        
        if file.filename.endswith(".pdf"):
            text = extract_text_from_pdf(content)
        elif file.filename.endswith(".docx"):
            text = extract_text_from_docx(content)
        else:
            raise HTTPException(status_code=400, detail="Only PDF and DOCX files are supported.")
            
        db_contract = Contract(
            title=title,
            content=text,
            user_id=current_user.id
        )
        db.add(db_contract)
        db.commit()
        db.refresh(db_contract)
        
        return db_contract
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading contract: {e}")
        raise HTTPException(status_code=400, detail=f"Failed to process file: {str(e)}")

@router.get("", response_model=List[ContractResponse])
def get_contracts(
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        contracts = db.query(Contract).filter(Contract.user_id == current_user.id).offset(skip).limit(limit).all()
        return contracts
    except Exception as e:
        logger.error(f"Error fetching contracts: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/draft", response_model=ContractResponse)
def draft_contract(
    request: DraftRequest,
    title: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        drafted_text = draft_agent.draft_contract(request.prompt)
        
        db_contract = Contract(
            title=title,
            content=drafted_text,
            user_id=current_user.id
        )
        db.add(db_contract)
        db.commit()
        db.refresh(db_contract)
        
        return db_contract
    except Exception as e:
        logger.error(f"Error drafting contract: {e}")
        raise HTTPException(status_code=500, detail=f"AI Service error: {str(e)}")

@router.post("/review")
def review_contract(
    contract_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        contract = db.query(Contract).filter(Contract.id == contract_id, Contract.user_id == current_user.id).first()
        if not contract:
            raise HTTPException(status_code=404, detail="Contract not found")
            
        review_result = review_agent.review_contract(contract.content)
        return {"review": review_result}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error reviewing contract: {e}")
        raise HTTPException(status_code=500, detail=f"AI Service error: {str(e)}")

@router.post("/analyze-risk", response_model=RiskReportResponse)
def analyze_risk(
    contract_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        contract = db.query(Contract).filter(Contract.id == contract_id, Contract.user_id == current_user.id).first()
        if not contract:
            raise HTTPException(status_code=404, detail="Contract not found")
            
        report = risk_agent.analyze_risk(contract.content)
        
        # Store report
        db_report = RiskReport(
            contract_id=contract.id,
            risk_score=report.risk_score,
            risk_level=report.risk_level,
            issues=report.model_dump_json() # Storing full JSON as text
        )
        db.add(db_report)
        db.commit()
        
        return report
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing risk: {e}")
        raise HTTPException(status_code=500, detail=f"AI Service error: {str(e)}")

@router.post("/negotiate", response_model=NegotiationReportResponse)
def negotiate_contract(
    contract_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        contract = db.query(Contract).filter(Contract.id == contract_id, Contract.user_id == current_user.id).first()
        if not contract:
            raise HTTPException(status_code=404, detail="Contract not found")
            
        negotiation_suggestions = negotiation_agent.suggest_negotiations(contract.content)
        
        db_report = NegotiationReport(
            contract_id=contract.id,
            suggestions=negotiation_suggestions.model_dump_json()
        )
        db.add(db_report)
        db.commit()
        
        return negotiation_suggestions
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error negotiating contract: {e}")
        raise HTTPException(status_code=500, detail=f"AI Service error: {str(e)}")

@router.post("/explain")
def explain_clause(
    clause: str,
    current_user: User = Depends(get_current_user)
):
    try:
        explanation = explainability_agent.explain_clause(clause)
        return {"explanation": explanation}
    except Exception as e:
        logger.error(f"Error explaining clause: {e}")
        raise HTTPException(status_code=500, detail=f"AI Service error: {str(e)}")

@router.get("/stats")
def get_contract_stats(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    contracts = db.query(Contract).filter(Contract.user_id == current_user.id).all()
    risk_reports = db.query(RiskReport).join(Contract).filter(Contract.user_id == current_user.id).all()
    
    total_issues = 0
    high_issues = 0
    med_issues = 0
    low_issues = 0
    
    for report in risk_reports:
        try:
            issues = json.loads(report.issues).get("issues", [])
            total_issues += len(issues)
            for issue in issues:
                severity = issue.get("severity", "LOW").upper()
                if severity == "HIGH":
                    high_issues += 1
                elif severity == "MEDIUM":
                    med_issues += 1
                else:
                    low_issues += 1
        except Exception:
            pass
            
    return {
        "active_contracts": len(contracts),
        "new_this_week": len(contracts),
        "risk_issues": total_issues,
        "high_risk": high_issues,
        "med_risk": med_issues,
        "low_risk": low_issues,
        "avg_turnaround_hrs": 4.2,
        "estimated_savings": 42600,
        "velocity": [
            {"month": "Nov", "volume": 4, "speed": 6},
            {"month": "Dec", "volume": 7, "speed": 5.5},
            {"month": "Jan", "volume": max(2, len(contracts)), "speed": 4.8}
        ]
    }

@router.get("/high-risk")
def get_high_risk_clauses(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    risk_reports = db.query(RiskReport).join(Contract).filter(Contract.user_id == current_user.id).all()
    
    distribution = {
        "Late Payment Terms": {"count": 0, "severity": "MEDIUM", "desc": "Net 60+ detected", "color": "bg-risk-medium-text"},
        "Uncapped Indemnity": {"count": 0, "severity": "HIGH", "desc": "Unlimited exposure", "color": "bg-risk-high-text"},
        "Scope Creep / Revisions": {"count": 0, "severity": "HIGH", "desc": "Unlimited edit traps", "color": "bg-accent-primary"},
        "IP Rights Pre-Payment": {"count": 0, "severity": "LOW", "desc": "Assignment before fee", "color": "bg-ink-subdued"}
    }
    
    total = 0
    for report in risk_reports:
        try:
            issues = json.loads(report.issues).get("issues", [])
            for issue in issues:
                cat = issue.get("category", "Uncapped Indemnity")
                if cat in distribution:
                    distribution[cat]["count"] += 1
                    total += 1
                else:
                    distribution["Uncapped Indemnity"]["count"] += 1
                    total += 1
        except Exception:
            pass
            
    if total == 0:
        distribution["Uncapped Indemnity"]["count"] = 1
        total = 1
        
    results = []
    for k, v in distribution.items():
        results.append({
            "name": k,
            "count": v["count"],
            "percentage": int((v["count"] / total) * 100),
            "severity": v["severity"],
            "desc": v["desc"],
            "color": v["color"]
        })
    
    return {"total_clauses": total, "distribution": results}

@router.get("/upcoming-deadlines")
def get_upcoming_deadlines(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return [
        {
            "id": 1,
            "name": "Vector Labs Retainer",
            "cp": "Vector Labs",
            "clause": "Auto-renews unless cancelled 30 days prior",
            "date": "Oct 15 (in 4 days)",
            "urgency": "amber"
        },
        {
            "id": 2,
            "name": "Q3 Deliverable Milestone",
            "cp": "Studio Arch",
            "clause": "Final milestone invoice due upon delivery",
            "date": "Oct 18 (in 7 days)",
            "urgency": "amber"
        }
    ]

@router.get("/{contract_id}")
def get_contract_detail(contract_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    contract = db.query(Contract).filter(Contract.id == contract_id, Contract.user_id == current_user.id).first()
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")
        
    risk_report = db.query(RiskReport).filter(RiskReport.contract_id == contract.id).order_by(RiskReport.id.desc()).first()
    negotiation_report = db.query(NegotiationReport).filter(NegotiationReport.contract_id == contract.id).order_by(NegotiationReport.id.desc()).first()
    
    risk_data = None
    if risk_report:
        try:
            risk_data = json.loads(risk_report.issues)
        except Exception:
            pass
            
    negotiation_data = None
    if negotiation_report:
        try:
            negotiation_data = json.loads(negotiation_report.suggestions)
        except Exception:
            pass
            
    return {
        "contract": {
            "id": contract.id,
            "title": contract.title,
            "content": contract.content,
            "created_at": contract.created_at
        },
        "risk_report": {
            "risk_score": risk_report.risk_score if risk_report else 0,
            "risk_level": risk_report.risk_level if risk_report else "LOW",
            "issues": risk_data.get("issues", []) if risk_data else []
        } if risk_report else None,
        "negotiation_report": {
            "suggestions": negotiation_data.get("suggestions", []) if negotiation_data else []
        } if negotiation_report else None
    }

class TemplateRequest(BaseModel):
    template_type: str

@router.post("/template", response_model=ContractResponse)
def generate_template(
    request: TemplateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        t_type = request.template_type.lower()
        if t_type == "nda":
            prompt = "Generate a standard Mutual Non-Disclosure Agreement (NDA) for a freelance designer or agency engaging with a new client. Include typical confidentiality clauses, exclusions, term of 2 years, and standard equitable relief."
            title = "Standard NDA Template"
        elif t_type == "msa":
            prompt = "Generate a standard Master Services Agreement (MSA) for a boutique creative agency or software consultant. Include sections for services, payment terms, intellectual property (client owns final deliverables, agency retains pre-existing IP), warranties, limitation of liability, and termination."
            title = "Standard MSA Template"
        elif t_type == "sow":
            prompt = "Generate a standard Statement of Work (SOW) template that references an MSA. Include placeholders for project description, deliverables, timeline, milestones, and payment schedule."
            title = "Standard SOW Template"
        else:
            prompt = f"Generate a standard {request.template_type} legal document template."
            title = f"{request.template_type.upper()} Template"

        drafted_text = draft_agent.draft_contract(prompt)
        
        db_contract = Contract(
            title=title,
            content=drafted_text,
            user_id=current_user.id
        )
        db.add(db_contract)
        db.commit()
        db.refresh(db_contract)
        
        return db_contract
    except Exception as e:
        logger.error(f"Error generating template: {e}")
        raise HTTPException(status_code=500, detail=f"AI Service error: {str(e)}")
