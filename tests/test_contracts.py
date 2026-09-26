import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.core.database import Base, get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.models.contract import Contract
from unittest.mock import patch, MagicMock
from app.schemas.contract import RiskReportResponse, NegotiationReportResponse
from io import BytesIO
import PyPDF2
import docx

# Setup in-memory DB
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_contracts.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

def override_get_current_user():
    return User(id=1, email="test@test.com")

app.dependency_overrides[get_db] = override_get_db
app.dependency_overrides[get_current_user] = override_get_current_user

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_database():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    user = User(id=1, email="test@test.com", hashed_password="hashed_password")
    db.add(user)
    db.commit()
    yield
    Base.metadata.drop_all(bind=engine)

def create_dummy_pdf():
    pdf = PyPDF2.PdfWriter()
    page = pdf.add_blank_page(width=72, height=72)
    # Adding text to PyPDF2 is complex, so we'll just create a blank pdf
    # Or mock the extract function instead
    pass

@patch('app.api.v1.endpoints.contracts.extract_text_from_pdf')
def test_upload_contract_pdf(mock_extract):
    mock_extract.return_value = "This is a dummy PDF contract."
    
    response = client.post(
        "/api/v1/contracts/upload",
        data={"title": "Test PDF Contract"},
        files={"file": ("test.pdf", b"%PDF-1.4...", "application/pdf")}
    )
    assert response.status_code == 200
    assert response.json()["title"] == "Test PDF Contract"
    assert response.json()["content"] == "This is a dummy PDF contract."

@patch('app.api.v1.endpoints.contracts.extract_text_from_docx')
def test_upload_contract_docx(mock_extract):
    mock_extract.return_value = "This is a dummy DOCX contract."
    
    response = client.post(
        "/api/v1/contracts/upload",
        data={"title": "Test DOCX Contract"},
        files={"file": ("test.docx", b"PK...", "application/vnd.openxmlformats-officedocument.wordprocessingml.document")}
    )
    assert response.status_code == 200
    assert response.json()["title"] == "Test DOCX Contract"
    assert response.json()["content"] == "This is a dummy DOCX contract."

@patch('app.api.v1.endpoints.contracts.review_agent.review_contract')
def test_review_contract(mock_review):
    mock_review.return_value = "Review complete. All good."
    
    # First create a contract
    db = TestingSessionLocal()
    contract = Contract(title="Review Test", content="Content", user_id=1)
    db.add(contract)
    db.commit()
    db.refresh(contract)
    
    response = client.post(f"/api/v1/contracts/review?contract_id={contract.id}")
    assert response.status_code == 200
    assert response.json()["review"] == "Review complete. All good."

@patch('app.api.v1.endpoints.contracts.risk_agent.analyze_risk')
def test_analyze_risk(mock_risk):
    mock_risk.return_value = RiskReportResponse(
        risk_score=50,
        risk_level="MEDIUM",
        issues=[{"clause": "Test clause", "issue": "Test issue", "category": "General", "severity": "MEDIUM", "reason": "Test reason"}]
    )
    
    db = TestingSessionLocal()
    contract = Contract(title="Risk Test", content="Content", user_id=1)
    db.add(contract)
    db.commit()
    db.refresh(contract)
    
    response = client.post(f"/api/v1/contracts/analyze-risk?contract_id={contract.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["risk_score"] == 50
    assert data["risk_level"] == "MEDIUM"

@patch('app.api.v1.endpoints.contracts.negotiation_agent.suggest_negotiations')
def test_negotiate_contract(mock_negotiate):
    mock_negotiate.return_value = NegotiationReportResponse(
        suggestions=[{"original_clause": "Clause A", "suggested_clause": "Clause B", "reasoning": "Safer"}]
    )
    
    db = TestingSessionLocal()
    contract = Contract(title="Negotiate Test", content="Content", user_id=1)
    db.add(contract)
    db.commit()
    db.refresh(contract)
    
    response = client.post(f"/api/v1/contracts/negotiate?contract_id={contract.id}")
    assert response.status_code == 200
    data = response.json()
    assert len(data["suggestions"]) == 1

@patch('app.api.v1.endpoints.contracts.explainability_agent.explain_clause')
def test_explain_clause(mock_explain):
    mock_explain.return_value = "This means X."
    
    response = client.post("/api/v1/contracts/explain?clause=Complex%20clause")
    assert response.status_code == 200
    assert response.json()["explanation"] == "This means X."
