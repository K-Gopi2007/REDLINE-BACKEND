from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
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
